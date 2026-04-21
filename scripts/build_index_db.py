#!/usr/bin/env python3
"""Build SQLite index for the Morpheus paper corpus.

Reads:
  corpus/unified.jsonl      - canonical list of 332 papers
  papers/arxiv/MANIFEST.jsonl - PDF download status (291 records)

Writes:
  corpus/morpheus.db

Usage:
  python3 scripts/build_index_db.py [--rebuild]

Idempotent: without --rebuild, existing DB is kept and script exits.
Authors and fulltext tables are left empty for later enrichment passes.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIFIED = ROOT / "corpus" / "unified.jsonl"
MANIFEST = ROOT / "papers" / "arxiv" / "MANIFEST.jsonl"
DB_PATH = ROOT / "corpus" / "morpheus.db"

SCHEMA = """
CREATE TABLE papers (
  paper_id INTEGER PRIMARY KEY,
  arxiv_id TEXT UNIQUE,
  title TEXT NOT NULL,
  year INTEGER,
  abstract TEXT,
  primary_category TEXT,
  github_url TEXT,
  suspicious INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE authors (
  author_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  name_normalized TEXT UNIQUE NOT NULL
);
CREATE TABLE paper_authors (
  paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
  author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE,
  position INTEGER NOT NULL,
  PRIMARY KEY (paper_id, author_id)
);
CREATE TABLE tags (
  tag_id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL,
  name TEXT NOT NULL,
  UNIQUE(kind, name)
);
CREATE TABLE paper_tags (
  paper_id INTEGER NOT NULL REFERENCES papers(paper_id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
  confidence REAL DEFAULT 1.0,
  PRIMARY KEY (paper_id, tag_id)
);
CREATE TABLE downloads (
  paper_id INTEGER PRIMARY KEY REFERENCES papers(paper_id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  bytes INTEGER,
  path TEXT,
  downloaded_at TEXT
);
CREATE VIRTUAL TABLE fulltext USING fts5(
  paper_id UNINDEXED,
  title,
  abstract,
  body,
  content=''
);
CREATE INDEX idx_papers_year ON papers(year);
CREATE INDEX idx_papers_arxiv ON papers(arxiv_id);
CREATE INDEX idx_tags_kind ON tags(kind);
"""


def parse_year(val):
    if val is None:
        return None
    try:
        return int(str(val)[:4])
    except (ValueError, TypeError):
        return None


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def load_papers(conn: sqlite3.Connection) -> dict[str, int]:
    """Load unified.jsonl. Returns arxiv_id -> paper_id map (keys include None proxies via title)."""
    title_to_id: dict[tuple, int] = {}
    arxiv_to_id: dict[str, int] = {}

    with UNIFIED.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            arxiv_id = rec.get("arxiv_id") or None
            title = rec.get("title") or "(untitled)"
            year = parse_year(rec.get("year"))
            github_urls = rec.get("github_urls") or []
            github_url = github_urls[0] if github_urls else None
            suspicious = 1 if rec.get("suspicious") else 0
            primary_category = rec.get("primary_category")  # not in current schema; null-safe
            abstract = rec.get("abstract")

            cur = conn.execute(
                """INSERT INTO papers(arxiv_id, title, year, abstract,
                       primary_category, github_url, suspicious)
                   VALUES(?,?,?,?,?,?,?)""",
                (arxiv_id, title, year, abstract, primary_category, github_url, suspicious),
            )
            paper_id = cur.lastrowid
            if arxiv_id:
                arxiv_to_id[arxiv_id] = paper_id
            title_to_id[(title, year)] = paper_id

            # primary_category -> category tag (if present)
            if primary_category:
                conn.execute(
                    "INSERT OR IGNORE INTO tags(kind, name) VALUES('category', ?)",
                    (primary_category,),
                )
                tid = conn.execute(
                    "SELECT tag_id FROM tags WHERE kind='category' AND name=?",
                    (primary_category,),
                ).fetchone()[0]
                conn.execute(
                    "INSERT OR IGNORE INTO paper_tags(paper_id, tag_id) VALUES(?,?)",
                    (paper_id, tid),
                )

    return arxiv_to_id


def load_downloads(conn: sqlite3.Connection, arxiv_to_id: dict[str, int]) -> int:
    n = 0
    skipped = 0
    with MANIFEST.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            arxiv_id = rec.get("arxiv_id")
            pid = arxiv_to_id.get(arxiv_id)
            if pid is None:
                skipped += 1
                continue
            status = rec.get("status") or "missing"
            # manifest uses status='downloaded' or 'pre_existing' — treat both as downloaded
            if status in ("downloaded", "pre_existing"):
                norm_status = "downloaded"
            else:
                norm_status = status
            path = f"papers/arxiv/{arxiv_id}.pdf"
            conn.execute(
                """INSERT INTO downloads(paper_id, status, bytes, path, downloaded_at)
                   VALUES(?,?,?,?, datetime('now'))
                   ON CONFLICT(paper_id) DO UPDATE SET
                     status=excluded.status,
                     bytes=excluded.bytes,
                     path=excluded.path""",
                (pid, norm_status, rec.get("bytes"), path),
            )
            n += 1
    if skipped:
        print(f"[warn] {skipped} manifest entries had no matching paper in unified.jsonl",
              file=sys.stderr)
    return n


def smoke_test(conn: sqlite3.Connection) -> None:
    print("\n=== SMOKE TESTS ===")
    q = lambda s, *a: conn.execute(s, a).fetchall()
    print(f"papers total:              {q('SELECT COUNT(*) FROM papers')[0][0]}  (expect 332)")
    print(f"papers with arxiv_id:      "
          f"{q('SELECT COUNT(*) FROM papers WHERE arxiv_id IS NOT NULL')[0][0]}  (expect 291)")
    dl = q("SELECT COUNT(*) FROM downloads WHERE status='downloaded'")[0][0]
    print(f"downloads status=downloaded: {dl}  (expect 291)")

    print("\n-- papers per year --")
    rows = q(
        "SELECT year, COUNT(*) FROM papers GROUP BY year ORDER BY year"
    )
    for y, c in rows:
        print(f"  {y!s:10s} {c}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true", help="drop and recreate the DB")
    args = ap.parse_args()

    if DB_PATH.exists():
        if args.rebuild:
            DB_PATH.unlink()
        else:
            print(f"{DB_PATH} already exists. Use --rebuild to recreate. Running smoke test only.")
            with sqlite3.connect(DB_PATH) as conn:
                smoke_test(conn)
            return 0

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        create_schema(conn)
        arxiv_to_id = load_papers(conn)
        print(f"loaded {len(arxiv_to_id)} papers with arxiv_id "
              f"(total {conn.execute('SELECT COUNT(*) FROM papers').fetchone()[0]})")
        nd = load_downloads(conn, arxiv_to_id)
        print(f"loaded {nd} download records")
        conn.commit()
        smoke_test(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
