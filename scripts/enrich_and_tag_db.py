#!/usr/bin/env python3
"""Enrich corpus/morpheus.db: fill abstracts, primary_category, authors, and
apply rule-based tags. Idempotent — safe to rerun.

Inputs
------
- corpus/metadata-enriched.jsonl : arXiv metadata for 291 papers
- corpus/authors.jsonl           : 2583 unique author records

Writes
------
- papers.abstract, papers.primary_category
- tags / paper_tags (kind in {category, area, method, subject, artifact})
- authors / paper_authors

Use:
    python3 scripts/enrich_and_tag_db.py
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
DB_PATH = REPO / "corpus" / "morpheus.db"
META_PATH = REPO / "corpus" / "metadata-enriched.jsonl"
AUTHORS_PATH = REPO / "corpus" / "authors.jsonl"
SCHEMA_MD = REPO / "corpus" / "SCHEMA.md"

# ---------------------------------------------------------------------------
# Rule tables — ordered dict of (kind, name) -> compiled regex, plus optional
# extra predicate that receives (text, primary_cat, github_url, title)
# ---------------------------------------------------------------------------

_FLAGS = re.IGNORECASE


def _rx(pattern: str, flags: int = _FLAGS) -> re.Pattern:
    return re.compile(pattern, flags)


# Area rules (kind='area')
AREA_RULES = [
    ("agentic-search", _rx(r"\b(agent|agentic|search agent|web agent|browsing|deep research|retrieval.{0,20}agent)\b")),
    ("tool-use", _rx(r"\btool[- ]?(use|using|call|calling|augmented)\b|\bfunction call")),
    ("benchmarks", _rx(r"\b(benchmark|evaluation suite|eval(uation)? framework|leaderboard)\b")),
    ("algorithms-ppo-grpo", _rx(r"\b(PPO|GRPO|DPO|RLHF|RLAIF|policy gradient|advantage estimation|KL penalty|reward shaping)\b")),
    ("reward-models", _rx(r"\breward model|preference model|verifier|reward hack")),
    ("process-supervision", _rx(r"\bprocess (reward|supervision)|step[- ]?level|step[- ]?wise reward|PRM\b")),
    ("memory", _rx(r"\bmemory (augment|module|bank|replay)|long[- ]?term memory|episodic memory\b")),
    ("self-play", _rx(r"\bself[- ]?play|self[- ]?improv|self[- ]?generat(e|ion)|auto-curricul")),
    # gui handled specially
    # multimodal handled specially
    ("surveys", _rx(r"\b(survey|systematic review|taxonomy)\b.*\b(agent|reinforcement|LLM|reasoning)\b|^A Survey")),
    ("multi-agent", _rx(r"\bmulti[- ]?agent|cooperation|coordination|negotiation between agents\b")),
]

METHOD_LITERAL = ["PPO", "GRPO", "DPO", "RLHF", "RLAIF"]  # uppercase literal match

METHOD_REGEX = [
    ("sft", _rx(r"supervised fine[- ]?tun")),
    ("distillation", _rx(r"\bdistill")),
    ("rejection-sampling", _rx(r"\brejection sampl")),
    ("mcts", _rx(r"\bMCTS|monte.{0,5}carlo tree")),
    ("self-consistency", _rx(r"\bself[- ]?consistenc")),
    ("cot", _rx(r"\bchain[- ]?of[- ]?thought|CoT\b")),
    ("tool-learning", _rx(r"\btool learn")),
]

SUBJECT_RULES = [
    ("web-agents", _rx(r"\bweb (agent|browsing|navigation)")),
    ("code-agents", _rx(r"\bcode (agent|generation|synthesis)|SWE[- ]?bench|programming agent")),
    ("math-reasoning", _rx(r"\b(math|theorem|olympiad|GSM8K|MATH dataset)\b")),
    ("embodied", _rx(r"\b(robot|embodied|manipulation|navigation task)\b")),
    ("retrieval", _rx(r"\b(RAG|retrieval[- ]?augmented|dense retrieval)\b")),
    ("planning", _rx(r"\b(planning|plan generation|hierarchical plan)\b")),
    ("safety", _rx(r"\b(safety|jailbreak|adversarial|red[- ]?team)\b")),
    ("alignment", _rx(r"\b(alignment|helpful|harmless|HHH|constitutional)\b")),
]

# Artifact rules using regex on text
ARTIFACT_REGEX = [
    ("dataset", _rx(r"\b(dataset|corpus).{0,30}(release|introduce|present)|we (release|introduce|present) .{0,20}dataset")),
    ("model-weights", _rx(r"\b(release|open[- ]?source).{0,30}(model|weights|checkpoint)\b")),
    ("eval-harness", _rx(r"\beval(uation)? (harness|framework|suite)")),
]

# Special helpers
GUI_TITLE_RX = _rx(r"\b(screen|UI|GUI)\b")
GUI_BODY_RX = _rx(r"\b(GUI|screen|click|mobile UI|desktop agent|OS agent|mouse|keyboard)\b")
MULTIMODAL_TITLE_RX = _rx(r"\b(vision|visual|multimodal|image|video)\b")
SURVEY_TITLE_PREFIX_RX = _rx(r"^A Survey")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_name(name: str) -> str:
    """Lowercase + strip diacritics; collapse whitespace."""
    if not name:
        return ""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.lower().split())


def load_jsonl(path: Path) -> Iterable[dict]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def ensure_tag(cur: sqlite3.Cursor, kind: str, name: str) -> int:
    cur.execute("INSERT OR IGNORE INTO tags(kind, name) VALUES(?, ?)", (kind, name))
    row = cur.execute(
        "SELECT tag_id FROM tags WHERE kind=? AND name=?", (kind, name)
    ).fetchone()
    return row[0]


def link_tag(cur: sqlite3.Cursor, paper_id: int, tag_id: int, confidence: float = 1.0):
    cur.execute(
        "INSERT OR IGNORE INTO paper_tags(paper_id, tag_id, confidence) VALUES(?,?,?)",
        (paper_id, tag_id, confidence),
    )


def apply_rules(title: str, abstract: str | None, primary_cat: str,
                categories: list[str], github_url: str | None) -> list[tuple[str, str]]:
    title = title or ""
    abstract = abstract or ""
    text = f"{title}\n{abstract}\n{primary_cat}".lower()
    # For literal (case-sensitive) uppercase checks use original
    raw = f"{title}\n{abstract}"

    tags: list[tuple[str, str]] = []

    # --- Area ---
    for name, rx in AREA_RULES:
        if rx.search(text):
            tags.append(("area", name))
    # gui: special — (GUI|screen|click|mobile UI|desktop agent|OS agent|mouse|keyboard)
    # AND (cs.HC in categories OR title mentions screen/UI/GUI)
    if GUI_BODY_RX.search(text) and (
        "cs.HC" in (categories or []) or GUI_TITLE_RX.search(title)
    ):
        tags.append(("area", "gui"))
    # multimodal: primary_category==cs.CV or title contains vision/visual/multimodal/image/video
    if primary_cat == "cs.CV" or MULTIMODAL_TITLE_RX.search(title):
        tags.append(("area", "multimodal"))

    # --- Method literal (case-sensitive uppercase in raw text)
    for tok in METHOD_LITERAL:
        if re.search(rf"\b{tok}\b", raw):
            tags.append(("method", tok.lower()))
    for name, rx in METHOD_REGEX:
        if rx.search(text):
            tags.append(("method", name))

    # --- Subject ---
    for name, rx in SUBJECT_RULES:
        if rx.search(text):
            tags.append(("subject", name))

    # --- Artifact ---
    area_names = {n for (k, n) in tags if k == "area"}
    if "benchmarks" in area_names:
        tags.append(("artifact", "benchmark"))
    for name, rx in ARTIFACT_REGEX:
        if rx.search(text):
            tags.append(("artifact", name))
    if github_url:
        tags.append(("artifact", "training-code"))
    if "surveys" in area_names:
        tags.append(("artifact", "survey"))

    # Dedup while preserving order
    seen = set()
    out = []
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


# ---------------------------------------------------------------------------
# Main enrichment
# ---------------------------------------------------------------------------

def run():
    if not DB_PATH.exists():
        print(f"ERROR: db missing at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # Step B (pre): insert all authors from authors.jsonl
    # ------------------------------------------------------------------
    print("[authors] inserting unique authors...")
    n_authors = 0
    cur.execute("BEGIN")
    for a in load_jsonl(AUTHORS_PATH):
        name = (a.get("name") or "").strip()
        norm = (a.get("normalized_name") or normalize_name(name)).strip()
        if not name or not norm:
            continue
        cur.execute(
            "INSERT OR IGNORE INTO authors(name, name_normalized) VALUES(?,?)",
            (name, norm),
        )
        n_authors += 1
    conn.commit()
    print(f"[authors] processed {n_authors} records")

    # ------------------------------------------------------------------
    # Steps A, B (link), C: per paper
    # ------------------------------------------------------------------
    print("[papers] enriching per-paper data...")
    n_papers_seen = 0
    n_papers_matched = 0
    for rec in load_jsonl(META_PATH):
        arxiv_id = rec.get("arxiv_id")
        if not arxiv_id:
            continue
        n_papers_seen += 1
        row = cur.execute(
            "SELECT paper_id, title, github_url FROM papers WHERE arxiv_id=?",
            (arxiv_id,),
        ).fetchone()
        if not row:
            continue
        paper_id, title, github_url = row
        n_papers_matched += 1
        abstract = rec.get("abstract") or None
        primary_cat = rec.get("primary_category") or None
        categories = rec.get("categories") or []
        authors = rec.get("authors") or []

        cur.execute("BEGIN")

        # Step A: update abstract + primary_category
        cur.execute(
            "UPDATE papers SET abstract=COALESCE(?, abstract), "
            "primary_category=COALESCE(?, primary_category) WHERE paper_id=?",
            (abstract, primary_cat, paper_id),
        )

        # Category tag
        if primary_cat:
            tid = ensure_tag(cur, "category", primary_cat)
            link_tag(cur, paper_id, tid, 1.0)

        # Step B: link authors
        for pos, author in enumerate(authors):
            name = (author.get("name") or "").strip()
            if not name:
                continue
            norm = normalize_name(name)
            cur.execute(
                "INSERT OR IGNORE INTO authors(name, name_normalized) VALUES(?,?)",
                (name, norm),
            )
            arow = cur.execute(
                "SELECT author_id FROM authors WHERE name_normalized=?", (norm,)
            ).fetchone()
            if not arow:
                continue
            author_id = arow[0]
            cur.execute(
                "INSERT OR IGNORE INTO paper_authors(paper_id, author_id, position) "
                "VALUES(?,?,?)",
                (paper_id, author_id, pos),
            )

        # Step C: rule tags
        for kind, name in apply_rules(title, abstract, primary_cat or "",
                                       categories, github_url):
            tid = ensure_tag(cur, kind, name)
            link_tag(cur, paper_id, tid, 1.0)

        conn.commit()

    print(f"[papers] seen={n_papers_seen} matched={n_papers_matched}")

    # ------------------------------------------------------------------
    # Step C also for non-arxiv papers: tag by title only
    # ------------------------------------------------------------------
    print("[non-arxiv] tagging papers without arxiv_id by title...")
    for row in cur.execute(
        "SELECT paper_id, title, github_url FROM papers WHERE arxiv_id IS NULL"
    ).fetchall():
        paper_id, title, github_url = row
        cur.execute("BEGIN")
        for kind, name in apply_rules(title, None, "", [], github_url):
            tid = ensure_tag(cur, kind, name)
            link_tag(cur, paper_id, tid, 1.0)
        conn.commit()

    # ------------------------------------------------------------------
    # Step D: smoke test
    # ------------------------------------------------------------------
    print("\n=== SMOKE TEST ===")
    (n_a,) = cur.execute("SELECT COUNT(*) FROM authors").fetchone()
    (n_pa,) = cur.execute("SELECT COUNT(*) FROM paper_authors").fetchone()
    (n_abs,) = cur.execute(
        "SELECT COUNT(*) FROM papers WHERE abstract IS NOT NULL AND abstract <> ''"
    ).fetchone()
    print(f"authors rows:        {n_a}")
    print(f"paper_authors rows:  {n_pa}")
    print(f"papers w/ abstract:  {n_abs}")

    print("\n-- tags by kind --")
    rows = cur.execute(
        "SELECT kind, COUNT(DISTINCT t.tag_id) AS tag_count, COUNT(pt.paper_id) AS assignments "
        "FROM tags t LEFT JOIN paper_tags pt USING(tag_id) GROUP BY kind ORDER BY kind"
    ).fetchall()
    kind_summary = []
    for kind, tc, ac in rows:
        print(f"  {kind:<10} tags={tc:<4} assignments={ac}")
        kind_summary.append((kind, tc, ac))

    print("\n-- top 10 tags per kind --")
    top_by_kind: dict[str, list[tuple[str, int]]] = {}
    for (kind,) in cur.execute("SELECT DISTINCT kind FROM tags").fetchall():
        top = cur.execute(
            "SELECT t.name, COUNT(pt.paper_id) AS n "
            "FROM tags t LEFT JOIN paper_tags pt USING(tag_id) "
            "WHERE t.kind=? GROUP BY t.tag_id ORDER BY n DESC, t.name LIMIT 10",
            (kind,),
        ).fetchall()
        print(f"  [{kind}]")
        for name, n in top:
            print(f"    {n:>4}  {name}")
        top_by_kind[kind] = top

    print("\n-- tag-count distribution per paper --")
    (n_ge5,) = cur.execute(
        "SELECT COUNT(*) FROM (SELECT paper_id, COUNT(*) c FROM paper_tags GROUP BY paper_id HAVING c>=5)"
    ).fetchone()
    (n_le1,) = cur.execute(
        "SELECT COUNT(*) FROM (SELECT paper_id, COUNT(*) c FROM paper_tags GROUP BY paper_id HAVING c<=1)"
    ).fetchone()
    (n_papers,) = cur.execute("SELECT COUNT(*) FROM papers").fetchone()
    (n_untagged,) = cur.execute(
        "SELECT COUNT(*) FROM papers p WHERE NOT EXISTS (SELECT 1 FROM paper_tags pt WHERE pt.paper_id=p.paper_id)"
    ).fetchone()
    print(f"  papers with >=5 tags: {n_ge5}")
    print(f"  papers with <=1 tag:  {n_le1}")
    print(f"  papers with 0 tags:   {n_untagged}")
    print(f"  total papers:         {n_papers}")

    conn.close()

    # ------------------------------------------------------------------
    # Update SCHEMA.md with Populated state section (idempotent)
    # ------------------------------------------------------------------
    update_schema_md(n_a, n_pa, n_abs, n_papers, kind_summary, top_by_kind,
                     n_ge5, n_le1, n_untagged)


def update_schema_md(n_authors, n_paper_authors, n_abs, n_papers,
                     kind_summary, top_by_kind, n_ge5, n_le1, n_untagged):
    marker = "## Populated state"
    existing = SCHEMA_MD.read_text() if SCHEMA_MD.exists() else ""
    head = existing.split(marker)[0].rstrip() + "\n\n"

    lines = [marker, "",
             "_Generated by `scripts/enrich_and_tag_db.py` — numbers reflect the last run._",
             "",
             "### Row counts", ""]
    lines.append(f"- `papers`: {n_papers}")
    lines.append(f"- `papers.abstract` populated: {n_abs}")
    lines.append(f"- `authors`: {n_authors}")
    lines.append(f"- `paper_authors`: {n_paper_authors}")
    lines.append("")
    lines.append("### Tag vocabulary in use")
    lines.append("")
    lines.append("| kind | distinct tags | total assignments |")
    lines.append("| ---- | ------------: | ----------------: |")
    for kind, tc, ac in kind_summary:
        lines.append(f"| `{kind}` | {tc} | {ac} |")
    lines.append("")
    lines.append("### Top tags per kind")
    for kind, top in top_by_kind.items():
        lines.append("")
        lines.append(f"**{kind}**")
        lines.append("")
        for name, n in top:
            lines.append(f"- `{name}` — {n}")
    lines.append("")
    lines.append("### Paper tag-count distribution")
    lines.append("")
    lines.append(f"- papers with >=5 tags: {n_ge5}")
    lines.append(f"- papers with <=1 tag: {n_le1}")
    lines.append(f"- papers with 0 tags: {n_untagged}")
    lines.append("")

    SCHEMA_MD.write_text(head + "\n".join(lines))


if __name__ == "__main__":
    run()
