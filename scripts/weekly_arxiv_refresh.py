#!/usr/bin/env python3
"""Weekly arXiv refresh for the Morpheus corpus.

Queries the arXiv HTTP API for new papers in the Morpheus topic buckets
(see scripts/refresh_arxiv.md), dedupes against `corpus/morpheus.db`.papers,
and writes new records to `corpus/staging-new.jsonl` for manual review.

Designed to be run weekly via cron. Idempotent: running twice on the same
day produces the same staging file (new IDs are merged with any existing
rows keyed by arxiv_id).

Default behavior: STAGING ONLY (no DB writes, no PDF downloads).
Use --commit to insert new rows into morpheus.db (still no PDFs — the
docling pipeline picks those up separately via --promote).

Usage:
    python3 scripts/weekly_arxiv_refresh.py
    python3 scripts/weekly_arxiv_refresh.py --date-from 2026-04-18 --date-to 2026-04-20
    python3 scripts/weekly_arxiv_refresh.py --no-commit          # default
    python3 scripts/weekly_arxiv_refresh.py --commit             # write to DB
    python3 scripts/weekly_arxiv_refresh.py --promote            # stage + DB + queue PDFs
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import traceback
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "corpus" / "morpheus.db"
STAGING = ROOT / "corpus" / "staging-new.jsonl"
REFRESH_LOG = ROOT / "corpus" / "refresh-log.jsonl"
PDF_QUEUE = ROOT / "corpus" / "pdf-download-queue.jsonl"

ARXIV_API = "https://export.arxiv.org/api/query"
SLEEP_SECS = 3.0  # arXiv ToS: 1 request / 3 seconds
DEFAULT_MAX_RESULTS = 50
USER_AGENT = "Morpheus-the-Dreamer/0.1 (mailto:cardenalito@gmail.com)"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}

# Query set mirrors scripts/refresh_arxiv.md §3.
# Each bucket: (name, keyword query, categories, bucket_tag)
QUERY_SET = [
    ("agentic-search",
     "agentic search OR retrieval agent OR search agent reinforcement learning",
     ["cs.CL", "cs.AI", "cs.IR"], "agentic-search"),
    ("tool-use",
     "tool use LLM reinforcement learning OR tool-integrated reasoning",
     ["cs.CL", "cs.AI"], "tool-use"),
    ("ppo-grpo-dpo",
     "GRPO OR PPO OR DPO language model OR policy optimization LLM",
     ["cs.LG", "cs.CL"], "algorithms-ppo-grpo"),
    ("reward-models",
     "reward model LLM OR preference model RLHF",
     ["cs.LG", "cs.CL"], "reward-models"),
    ("process-supervision",
     "process reward model OR step-level reward OR PRM reasoning",
     ["cs.LG", "cs.CL"], "process-supervision"),
    ("memory-long-context",
     "agent memory OR long-context retrieval reinforcement learning",
     ["cs.CL", "cs.AI"], "memory"),
    ("self-play",
     "self-play LLM OR self-evolution agent OR self-improving reasoning",
     ["cs.LG", "cs.AI"], "self-play"),
    ("gui-computer-use",
     "GUI agent OR computer use agent OR screen agent reinforcement learning",
     ["cs.HC", "cs.AI", "cs.CL"], "gui-agents"),
    ("multimodal-reasoning",
     "multimodal reasoning reinforcement learning OR vision language agent",
     ["cs.CV", "cs.CL", "cs.AI"], "multimodal"),
    ("benchmarks",
     "agent benchmark OR tool-use benchmark OR agentic evaluation",
     ["cs.AI", "cs.CL", "cs.LG"], "benchmarks"),
    ("multi-agent",
     "multi-agent LLM OR cooperative agents reinforcement learning",
     ["cs.MA", "cs.AI"], "multi-agent"),
]


# ---------- arxiv API helpers ----------

def build_query(keywords: str, categories: list[str],
                date_from: str, date_to: str) -> str:
    """Build an arXiv API `search_query` string.

    Dates are YYYY-MM-DD; arXiv expects YYYYMMDDHHMM in submittedDate.
    """
    df = date_from.replace("-", "") + "0000"
    dt = date_to.replace("-", "") + "2359"
    cat_clause = " OR ".join(f"cat:{c}" for c in categories)
    # all: picks up title + abstract. Quote nothing — keywords already use OR.
    kw_clause = f"all:({keywords})"
    return (
        f"({kw_clause}) AND ({cat_clause}) "
        f"AND submittedDate:[{df} TO {dt}]"
    )


def fetch_query(search_query: str, max_results: int,
                max_retries: int = 3) -> str:
    params = {
        "search_query": search_query,
        "max_results": str(max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    backoff = SLEEP_SECS * 4
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            last_err = e
            # 429 / 503 => back off and retry
            if e.code in (429, 503) and attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    assert last_err is not None
    raise last_err


def _collapse(s):
    if not s:
        return s
    return re.sub(r"\s+", " ", s).strip()


_VERSION_RE = re.compile(r"v\d+$")


def _norm_arxiv_id(raw: str) -> str:
    # http://arxiv.org/abs/2404.01234v2  ->  2404.01234
    aid = raw.rsplit("/", 1)[-1]
    return _VERSION_RE.sub("", aid)


def parse_feed(xml_str: str) -> list[dict]:
    root = ET.fromstring(xml_str)
    rows = []
    for entry in root.findall("atom:entry", NS):
        aid_raw = _collapse(entry.findtext("atom:id", default="", namespaces=NS))
        if not aid_raw:
            continue
        arxiv_id = _norm_arxiv_id(aid_raw)
        title = _collapse(entry.findtext("atom:title", default="", namespaces=NS))
        summary = _collapse(entry.findtext("atom:summary", default="", namespaces=NS))
        published = _collapse(entry.findtext("atom:published", default="", namespaces=NS))
        updated = _collapse(entry.findtext("atom:updated", default="", namespaces=NS))
        authors = []
        for a in entry.findall("atom:author", NS):
            name = _collapse(a.findtext("atom:name", default="", namespaces=NS))
            if name:
                authors.append(name)
        primary_cat_el = entry.find("arxiv:primary_category", NS)
        primary_category = (
            primary_cat_el.get("term") if primary_cat_el is not None else None
        )
        categories = [
            c.get("term") for c in entry.findall("atom:category", NS)
            if c.get("term")
        ]
        pdf_url = None
        for link in entry.findall("atom:link", NS):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
        year = None
        if published:
            try:
                year = int(published[:4])
            except ValueError:
                year = None
        rows.append({
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": summary,
            "authors": authors,
            "primary_category": primary_category,
            "categories": categories,
            "published": published,
            "updated": updated,
            "year": year,
            "pdf_url": pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
            "url": f"https://arxiv.org/abs/{arxiv_id}",
        })
    return rows


# ---------- state management ----------

def existing_arxiv_ids(db_path: Path) -> set[str]:
    if not db_path.exists():
        return set()
    con = sqlite3.connect(str(db_path))
    try:
        cur = con.execute(
            "SELECT arxiv_id FROM papers WHERE arxiv_id IS NOT NULL AND arxiv_id <> ''"
        )
        return {_norm_arxiv_id(r[0]) for r in cur.fetchall()}
    finally:
        con.close()


def last_run_date(log_path: Path) -> str | None:
    if not log_path.exists():
        return None
    last = None
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    if last and "date" in last:
        return last["date"]
    return None


def load_staging(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            aid = row.get("arxiv_id")
            if aid:
                out[aid] = row
    return out


def write_staging(path: Path, rows: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for aid in sorted(rows.keys()):
            f.write(json.dumps(rows[aid], ensure_ascii=False) + "\n")


# ---------- commit / promote ----------

def commit_to_db(db_path: Path, new_rows: list[dict]) -> int:
    """Insert new papers into morpheus.db. Returns rows inserted."""
    if not db_path.exists():
        print(f"[warn] {db_path} missing; skipping --commit", file=sys.stderr)
        return 0
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys=ON")
    inserted = 0
    try:
        for row in new_rows:
            try:
                con.execute(
                    """INSERT OR IGNORE INTO papers
                       (arxiv_id, title, year, abstract, primary_category, suspicious, created_at)
                       VALUES (?, ?, ?, ?, ?, 0, ?)""",
                    (
                        row["arxiv_id"],
                        row["title"],
                        row.get("year"),
                        row.get("abstract") or "",
                        row.get("primary_category") or "",
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                if con.total_changes:
                    inserted += 1
            except sqlite3.Error as e:
                print(f"[warn] insert failed for {row['arxiv_id']}: {e}", file=sys.stderr)
        con.commit()
    finally:
        con.close()
    return inserted


def queue_pdfs(queue_path: Path, new_rows: list[dict]) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a") as f:
        for row in new_rows:
            f.write(json.dumps({
                "arxiv_id": row["arxiv_id"],
                "pdf_url": row["pdf_url"],
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }) + "\n")


# ---------- main ----------

def run_refresh(date_from: str, date_to: str, max_results: int,
                commit: bool, promote: bool, dry_run: bool) -> int:
    started = time.time()
    existing = existing_arxiv_ids(DB)
    staging = load_staging(STAGING)

    raw_count = 0
    new_rows: dict[str, dict] = {}
    errors: list[str] = []
    retrieved_at = datetime.now(timezone.utc).isoformat()

    for i, (name, kw, cats, bucket_tag) in enumerate(QUERY_SET):
        sq = build_query(kw, cats, date_from, date_to)
        try:
            if i > 0:
                time.sleep(SLEEP_SECS)
            xml_str = fetch_query(sq, max_results)
            rows = parse_feed(xml_str)
        except (urllib.error.URLError, urllib.error.HTTPError,
                ET.ParseError, TimeoutError) as e:
            err = f"bucket={name}: {type(e).__name__}: {e}"
            errors.append(err)
            print(f"[error] {err}", file=sys.stderr)
            continue
        raw_count += len(rows)
        for r in rows:
            aid = r["arxiv_id"]
            if aid in existing:
                continue
            if aid in new_rows:
                # merge bucket tag
                if bucket_tag not in new_rows[aid]["buckets"]:
                    new_rows[aid]["buckets"].append(bucket_tag)
                continue
            r["buckets"] = [bucket_tag]
            r["sources"] = ["arxiv-weekly-refresh"]
            r["retrieved_at"] = retrieved_at
            new_rows[aid] = r
        print(
            f"[bucket {i+1:02d}/{len(QUERY_SET)}] {name}: {len(rows)} hits, "
            f"{len(new_rows)} cum. new after dedup",
            file=sys.stderr,
        )

    # Merge into staging (keyed by arxiv_id)
    for aid, row in new_rows.items():
        if aid in staging:
            # preserve earlier retrieved_at, merge buckets
            existing_row = staging[aid]
            merged_buckets = sorted(set(existing_row.get("buckets", [])) | set(row["buckets"]))
            existing_row["buckets"] = merged_buckets
            staging[aid] = existing_row
        else:
            staging[aid] = row

    duration = round(time.time() - started, 2)

    if not dry_run:
        write_staging(STAGING, staging)

    db_inserts = 0
    if (commit or promote) and not dry_run:
        db_inserts = commit_to_db(DB, list(new_rows.values()))
    if promote and not dry_run:
        queue_pdfs(PDF_QUEUE, list(new_rows.values()))

    log_entry = {
        "date": date_to,
        "window": {"from": date_from, "to": date_to},
        "query_count": len(QUERY_SET),
        "results_returned": raw_count,
        "new_after_dedup": len(new_rows),
        "db_inserts": db_inserts,
        "duration_seconds": duration,
        "errors": errors,
        "commit": bool(commit or promote),
        "promote": bool(promote),
        "dry_run": bool(dry_run),
    }
    if not dry_run:
        REFRESH_LOG.parent.mkdir(parents=True, exist_ok=True)
        with REFRESH_LOG.open("a") as f:
            f.write(json.dumps(log_entry) + "\n")

    print(json.dumps(log_entry, indent=2))
    return len(new_rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--date-from", help="YYYY-MM-DD (default: last run date or 7 days ago)")
    p.add_argument("--date-to", help="YYYY-MM-DD (default: today UTC)")
    p.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS,
                   help=f"per-bucket max (default {DEFAULT_MAX_RESULTS})")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--commit", action="store_true",
                   help="insert new rows into morpheus.db (default: staging only)")
    g.add_argument("--no-commit", action="store_true",
                   help="explicit no-op: staging only (the default)")
    g.add_argument("--promote", action="store_true",
                   help="commit to DB AND queue PDFs for download")
    p.add_argument("--dry-run", action="store_true",
                   help="fetch + parse but do not write staging, log, or DB")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    today = datetime.now(timezone.utc).date()
    date_to = args.date_to or today.isoformat()
    if args.date_from:
        date_from = args.date_from
    else:
        last = last_run_date(REFRESH_LOG)
        if last:
            date_from = last
        else:
            date_from = (today - timedelta(days=7)).isoformat()
    try:
        run_refresh(
            date_from=date_from,
            date_to=date_to,
            max_results=args.max_results,
            commit=args.commit,
            promote=args.promote,
            dry_run=args.dry_run,
        )
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"[fatal] {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
