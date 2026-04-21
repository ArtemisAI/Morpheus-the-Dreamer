#!/usr/bin/env python3
"""Close the tagger recall gap by scanning markdown bodies.

Reuses the rule set from `scripts/enrich_and_tag_db.py`. For each paper whose
arxiv_id matches a converted `.md` file in `papers/markdown/`, apply the same
regex rules against the body text (skipping the first 20 lines which usually
hold authors/abstract, overlapping with title+abstract tagging) and insert
additional `paper_tags` rows with `confidence=0.7`.

Safety:
- INSERT OR IGNORE — never overwrites a higher-confidence existing tag.
- Skips files that look incomplete (mtime newer than 10s, or size <= 2KB).
- Uses a single BEGIN IMMEDIATE transaction to avoid colliding with other
  writers (e.g. cron-driven monitoring agents).
- Does NOT modify markdown files, does NOT touch `papers/arxiv/`, does NOT
  kill the docling PID at `papers/markdown/convert.pid`.

Idempotent — safe to rerun.
"""
from __future__ import annotations

import re
import sqlite3
import sys
import time
from pathlib import Path

# Reuse rule tables from the existing tagger
sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_and_tag_db import (  # type: ignore
    AREA_RULES,
    METHOD_LITERAL,
    METHOD_REGEX,
    SUBJECT_RULES,
    ARTIFACT_REGEX,
    GUI_BODY_RX,
    GUI_TITLE_RX,
    MULTIMODAL_TITLE_RX,
)

REPO = Path(__file__).resolve().parent.parent
DB_PATH = REPO / "corpus" / "morpheus.db"
MD_DIR = REPO / "papers" / "markdown"

MIN_SIZE_BYTES = 2 * 1024
MIN_AGE_SECONDS = 10
SKIP_LEADING_LINES = 20
BODY_CONFIDENCE = 0.7


def apply_body_rules(body_text: str, title: str, primary_cat: str,
                     categories: list[str]) -> list[tuple[str, str]]:
    """Apply the same regex rules but against the markdown body.

    The original apply_rules() operates on title+abstract. Here `text` is
    the body only; we still consult title/categories for the GUI and
    multimodal side-conditions (so body-only signals don't over-fire).
    """
    text = f"{body_text}\n{primary_cat}".lower()
    raw = body_text  # preserve case for literal uppercase tokens

    tags: list[tuple[str, str]] = []

    # Area
    for name, rx in AREA_RULES:
        if rx.search(text):
            tags.append(("area", name))
    if GUI_BODY_RX.search(text) and (
        "cs.HC" in (categories or []) or GUI_TITLE_RX.search(title or "")
    ):
        tags.append(("area", "gui"))
    if primary_cat == "cs.CV" or MULTIMODAL_TITLE_RX.search(title or ""):
        tags.append(("area", "multimodal"))

    # Method (case-sensitive uppercase literal match in raw body)
    for tok in METHOD_LITERAL:
        if re.search(rf"\b{tok}\b", raw):
            tags.append(("method", tok.lower()))
    for name, rx in METHOD_REGEX:
        if rx.search(text):
            tags.append(("method", name))

    # Subject
    for name, rx in SUBJECT_RULES:
        if rx.search(text):
            tags.append(("subject", name))

    # Artifact
    area_names = {n for (k, n) in tags if k == "area"}
    if "benchmarks" in area_names:
        tags.append(("artifact", "benchmark"))
    for name, rx in ARTIFACT_REGEX:
        if rx.search(text):
            tags.append(("artifact", name))
    if "surveys" in area_names:
        tags.append(("artifact", "survey"))
    # NB: training-code / github_url is title-stage only, skip here.

    seen = set()
    out = []
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def ensure_confidence_column(conn: sqlite3.Connection) -> None:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(paper_tags)").fetchall()]
    if "confidence" not in cols:
        conn.execute(
            "ALTER TABLE paper_tags ADD COLUMN confidence REAL DEFAULT 1.0"
        )


def run() -> None:
    if not DB_PATH.exists():
        print(f"ERROR: db missing at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    now = time.time()
    md_files = sorted(MD_DIR.glob("*.md"))
    stable: list[Path] = []
    skipped = 0
    for p in md_files:
        if p.name.endswith(".meta.json"):
            continue
        try:
            st = p.stat()
        except FileNotFoundError:
            skipped += 1
            continue
        if st.st_size < MIN_SIZE_BYTES or (now - st.st_mtime) < MIN_AGE_SECONDS:
            skipped += 1
            continue
        stable.append(p)

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        ensure_confidence_column(conn)
        cur = conn.cursor()

        (before_count,) = cur.execute(
            "SELECT COUNT(*) FROM paper_tags"
        ).fetchone()

        # Map arxiv_id -> (paper_id, title, primary_category)
        paper_rows = cur.execute(
            "SELECT arxiv_id, paper_id, title, primary_category "
            "FROM papers WHERE arxiv_id IS NOT NULL"
        ).fetchall()
        by_arxiv = {r[0]: (r[1], r[2] or "", r[3] or "") for r in paper_rows}

        # Pre-load existing tags per paper to suppress duplicates cheaply
        existing: dict[int, set[tuple[str, str]]] = {}
        for pid, kind, name in cur.execute(
            "SELECT pt.paper_id, t.kind, t.name FROM paper_tags pt "
            "JOIN tags t USING(tag_id)"
        ):
            existing.setdefault(pid, set()).add((kind, name))

        def ensure_tag(kind: str, name: str) -> int:
            cur.execute(
                "INSERT OR IGNORE INTO tags(kind, name) VALUES(?, ?)",
                (kind, name),
            )
            (tid,) = cur.execute(
                "SELECT tag_id FROM tags WHERE kind=? AND name=?",
                (kind, name),
            ).fetchone()
            return tid

        # Single transaction for all writes
        cur.execute("BEGIN IMMEDIATE")

        per_kind_added: dict[str, int] = {}
        per_tag_added: dict[tuple[str, str], int] = {}
        scanned = 0
        no_match = 0

        for path in stable:
            arxiv_id = path.stem  # filename stem (e.g. 2305.20050)
            meta = by_arxiv.get(arxiv_id)
            if not meta:
                no_match += 1
                continue
            paper_id, title, primary_cat = meta
            try:
                raw = path.read_text(errors="replace")
            except OSError:
                continue
            lines = raw.splitlines()
            if len(lines) <= SKIP_LEADING_LINES:
                continue
            body = "\n".join(lines[SKIP_LEADING_LINES:])
            scanned += 1

            have = existing.get(paper_id, set())
            fired = apply_body_rules(body, title, primary_cat, [])
            for kind, name in fired:
                if (kind, name) in have:
                    continue  # title/abstract pass already covered it
                tid = ensure_tag(kind, name)
                cur.execute(
                    "INSERT OR IGNORE INTO paper_tags(paper_id, tag_id, confidence) "
                    "VALUES(?,?,?)",
                    (paper_id, tid, BODY_CONFIDENCE),
                )
                if cur.rowcount:
                    per_kind_added[kind] = per_kind_added.get(kind, 0) + 1
                    per_tag_added[(kind, name)] = per_tag_added.get((kind, name), 0) + 1
                    have.add((kind, name))
            existing[paper_id] = have

        conn.commit()

        (after_count,) = cur.execute(
            "SELECT COUNT(*) FROM paper_tags"
        ).fetchone()
    finally:
        conn.close()

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    print("=== tag_from_bodies report ===")
    print(f"files scanned:       {scanned}")
    print(f"files skipped:       {skipped} (incomplete / <2KB / mtime<10s)")
    print(f"files w/o db match:  {no_match}")
    print()
    print("additions by kind:")
    for kind in sorted(per_kind_added):
        print(f"  {kind:<10} {per_kind_added[kind]}")
    print()
    print("top-10 newly-tagged (kind, name, added_count):")
    top = sorted(per_tag_added.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    for (kind, name), n in top:
        print(f"  {n:>4}  {kind:<9} {name}")
    print()
    print(f"paper_tags rows: before={before_count}  after={after_count}  "
          f"delta={after_count - before_count}")
    print("rerun-safe: yes (INSERT OR IGNORE + existence set suppresses dupes)")


if __name__ == "__main__":
    run()
