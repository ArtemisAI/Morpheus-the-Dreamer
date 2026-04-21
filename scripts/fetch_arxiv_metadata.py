#!/usr/bin/env python3
"""Fetch canonical arXiv metadata for every arxiv_id in corpus/unified.jsonl.

Writes:
  - corpus/metadata-enriched.jsonl  (one row per arxiv_id)
  - corpus/authors.jsonl            (one row per unique author)

Reproducible: python3 scripts/fetch_arxiv_metadata.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIFIED = ROOT / "corpus" / "unified.jsonl"
OUT_META = ROOT / "corpus" / "metadata-enriched.jsonl"
OUT_AUTHORS = ROOT / "corpus" / "authors.jsonl"

ARXIV_API = "https://export.arxiv.org/api/query"
BATCH_SIZE = 100
SLEEP_SECS = 3.0

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
}


def load_arxiv_ids(path: Path) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            aid = (row.get("arxiv_id") or "").strip()
            if aid and aid not in seen:
                seen.add(aid)
                ids.append(aid)
    return ids


def fetch_batch(ids: list[str]) -> str:
    q = "id_list=" + ",".join(ids) + "&max_results=" + str(len(ids))
    url = f"{ARXIV_API}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "Morpheus-the-Dreamer/0.1 (mailto:cardenalito@gmail.com)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def _text(el, default=None):
    if el is None:
        return default
    t = el.text
    return t.strip() if t else default


def _collapse(s: str | None) -> str | None:
    if s is None:
        return None
    return re.sub(r"\s+", " ", s).strip()


def parse_feed(xml_str: str) -> dict[str, dict]:
    """Return {arxiv_id: metadata_dict} for every entry in the feed."""
    root = ET.fromstring(xml_str)
    out: dict[str, dict] = {}
    for entry in root.findall("atom:entry", NS):
        atom_id = _text(entry.find("atom:id", NS), "")
        # id like http://arxiv.org/abs/2509.02547v1
        m = re.search(r"arxiv\.org/abs/(.+?)(?:v\d+)?$", atom_id or "")
        arxiv_id = m.group(1) if m else atom_id

        title = _collapse(_text(entry.find("atom:title", NS)))
        abstract = _collapse(_text(entry.find("atom:summary", NS)))
        published = _text(entry.find("atom:published", NS))
        updated = _text(entry.find("atom:updated", NS))

        authors = []
        for a in entry.findall("atom:author", NS):
            name = _text(a.find("atom:name", NS), "")
            aff = _text(a.find("arxiv:affiliation", NS), "") or ""
            if name:
                authors.append({"name": name, "affiliation": aff})

        primary_el = entry.find("arxiv:primary_category", NS)
        primary_category = primary_el.get("term") if primary_el is not None else None
        categories = [c.get("term") for c in entry.findall("atom:category", NS) if c.get("term")]

        doi = _text(entry.find("arxiv:doi", NS))
        journal_ref = _collapse(_text(entry.find("arxiv:journal_ref", NS)))
        comment = _collapse(_text(entry.find("arxiv:comment", NS)))

        out[arxiv_id] = {
            "arxiv_id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "primary_category": primary_category,
            "categories": categories,
            "published": published,
            "updated": updated,
            "doi": doi,
            "journal_ref": journal_ref,
            "comment": comment,
            "status": "ok",
        }
    return out


def slugify(name: str) -> str:
    # normalize accents, lowercase, strip periods, collapse whitespace/non-alnum to '-'
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace(".", " ")
    n = re.sub(r"[^a-z0-9]+", "-", n).strip("-")
    return n or "unknown"


def normalize_name(name: str) -> str:
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace(".", "")
    n = re.sub(r"\s+", " ", n).strip()
    return n


def main() -> int:
    ids = load_arxiv_ids(UNIFIED)
    print(f"[info] {len(ids)} unique arxiv_ids to fetch", file=sys.stderr)

    results: dict[str, dict] = {}
    batches = [ids[i : i + BATCH_SIZE] for i in range(0, len(ids), BATCH_SIZE)]
    for i, batch in enumerate(batches, 1):
        print(f"[fetch] batch {i}/{len(batches)} ({len(batch)} ids)", file=sys.stderr)
        try:
            xml_str = fetch_batch(batch)
            parsed = parse_feed(xml_str)
        except (urllib.error.URLError, ET.ParseError) as e:
            print(f"[error] batch {i} failed: {e}; retrying once after 10s", file=sys.stderr)
            time.sleep(10)
            try:
                xml_str = fetch_batch(batch)
                parsed = parse_feed(xml_str)
            except Exception as e2:
                print(f"[error] batch {i} failed twice: {e2}", file=sys.stderr)
                parsed = {}
        results.update(parsed)
        if i < len(batches):
            time.sleep(SLEEP_SECS)

    # Write enriched metadata in input order
    ok = 0
    not_found = 0
    with OUT_META.open("w") as f:
        for aid in ids:
            row = results.get(aid)
            if row is None:
                f.write(
                    json.dumps(
                        {
                            "arxiv_id": aid,
                            "title": None,
                            "abstract": None,
                            "authors": [],
                            "primary_category": None,
                            "categories": [],
                            "published": None,
                            "updated": None,
                            "doi": None,
                            "journal_ref": None,
                            "comment": None,
                            "status": "not_found",
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                not_found += 1
            else:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                ok += 1

    # Build authors index
    by_key: dict[str, dict] = {}
    for aid in ids:
        row = results.get(aid)
        if not row:
            continue
        for a in row["authors"]:
            name = a["name"]
            key = normalize_name(name)
            if not key:
                continue
            entry = by_key.setdefault(
                key,
                {
                    "author_id": slugify(name),
                    "name": name,
                    "normalized_name": key,
                    "paper_count": 0,
                    "arxiv_ids": [],
                },
            )
            if aid not in entry["arxiv_ids"]:
                entry["arxiv_ids"].append(aid)
                entry["paper_count"] += 1

    # Ensure unique author_id slugs (append suffix on collision)
    used_ids: set[str] = set()
    for key, entry in by_key.items():
        base = entry["author_id"]
        candidate = base
        n = 2
        while candidate in used_ids:
            candidate = f"{base}-{n}"
            n += 1
        entry["author_id"] = candidate
        used_ids.add(candidate)

    authors_sorted = sorted(by_key.values(), key=lambda e: (-e["paper_count"], e["normalized_name"]))
    with OUT_AUTHORS.open("w") as f:
        for e in authors_sorted:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Summary
    print("")
    print("=" * 60)
    print(f"Total arxiv_ids:   {len(ids)}")
    print(f"Fetched ok:        {ok}")
    print(f"Not found:         {not_found}")
    print(f"Unique authors:    {len(authors_sorted)}")
    print("Top 10 authors by paper_count:")
    for e in authors_sorted[:10]:
        print(f"  {e['paper_count']:3d}  {e['name']}  ({e['author_id']})")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
