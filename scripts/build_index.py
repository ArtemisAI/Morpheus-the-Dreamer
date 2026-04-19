#!/usr/bin/env python3
"""Build a unified cross-source index over Morpheus-the-Dreamer scraped papers.

Inputs: five per-source papers.jsonl files under scraped/<slug>/papers.jsonl.
Outputs: unified.jsonl + several human-readable .md files under indexes/.

Dedup primary key: normalized arxiv_id. Secondary: normalized title.
"""
from __future__ import annotations

import json
import re
import string
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path.home() / "tools/tools-for-agents/Morpheus-the-Dreamer"
SCRAPED = ROOT / "scraped"
OUT = ROOT / "indexes"
OUT.mkdir(exist_ok=True, parents=True)

SOURCES = {
    "necolizer": SCRAPED / "necolizer-awesome-rl-for-agents/papers.jsonl",
    "0russwest0": SCRAPED / "0russwest0-awesome-agent-rl/papers.jsonl",
    "tongjingqi": SCRAPED / "tongjingqi-awesome-agent-rl/papers.jsonl",
    "ventr1c": SCRAPED / "ventr1c-awesome-rl-agentic-search/papers.jsonl",
    # aitfind: skip — single wrapper entry pointing at 0russwest0 awesome-list
}

TODAY = date(2026, 4, 19)


# ---------- normalization helpers ----------

ARXIV_RE = re.compile(r"^(?:arxiv:)?\s*(\d{4}\.\d{4,6})(v\d+)?\s*$", re.IGNORECASE)
PUNCT_TBL = str.maketrans({c: " " for c in string.punctuation})


def norm_arxiv(raw: str | None) -> str | None:
    if not raw:
        return None
    m = ARXIV_RE.match(raw.strip())
    if not m:
        # still accept if it looks like a plain YYMM.NNNNN
        s = raw.strip().lower().replace("arxiv:", "").strip()
        s = re.sub(r"v\d+$", "", s)
        if re.match(r"^\d{4}\.\d{4,6}$", s):
            return s
        return None
    return m.group(1).lower()


def norm_title(t: str | None) -> str:
    if not t:
        return ""
    return " ".join(t.lower().translate(PUNCT_TBL).split())


def is_suspicious_arxiv(aid: str | None) -> tuple[bool, str]:
    if not aid:
        return False, ""
    m = re.match(r"^(\d{2})(\d{2})\.(\d{4,6})$", aid)
    if not m:
        return True, "malformed arxiv id"
    yy = int(m.group(1))
    mm = int(m.group(2))
    seq = int(m.group(3))
    if mm == 0 or mm > 12:
        return True, f"month={mm:02d} invalid"
    # arXiv yy is 2-digit since 2007; assume 20yy. "26" is already now; anything > current is future.
    cur_yy, cur_mm = TODAY.year % 100, TODAY.month
    if (yy, mm) > (cur_yy, cur_mm):
        return True, f"future date 20{yy}.{mm:02d} > {TODAY.isoformat()}"
    # implausible submission-sequence number. Single-month arXiv volume is ~15-20k,
    # so a 5-digit seq > 20000 is not realistic for a given month.
    if seq > 20000:
        return True, f"sequence number {seq} implausibly large (>20000)"
    return False, ""


# ---------- load ----------

def load_all() -> list[dict]:
    rows = []
    for slug, path in SOURCES.items():
        if not path.exists():
            print(f"WARN: missing {path}")
            continue
        with path.open() as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"WARN: {slug}:{i} json error: {e}")
                    continue
                obj["_source_slug"] = slug
                rows.append(obj)
    return rows


# ---------- merge ----------

def pick_year(a, b):
    def asint(x):
        try:
            return int(str(x)[:4])
        except Exception:
            return None
    ia, ib = asint(a), asint(b)
    if ia is None:
        return b
    if ib is None:
        return a
    return a if ia <= ib else b


def merge_into(dst: dict, src: dict) -> None:
    # longest title
    if len(str(src.get("title") or "")) > len(str(dst.get("title") or "")):
        dst["title"] = src.get("title")
    # earliest year
    dst["year"] = pick_year(dst.get("year"), src.get("year"))
    # union of categories with provenance
    cat = src.get("category")
    if cat:
        dst.setdefault("categories", [])
        entry = f"{src['_source_slug']}:{cat}"
        if entry not in dst["categories"]:
            dst["categories"].append(entry)
    # union of github_urls
    gh = src.get("github_url")
    if gh:
        dst.setdefault("github_urls", [])
        if gh not in dst["github_urls"]:
            dst["github_urls"].append(gh)
    # project url — keep first non-empty
    if not dst.get("project_url") and src.get("project_url"):
        dst["project_url"] = src.get("project_url")
    # venue — keep first non-empty
    if not dst.get("venue") and src.get("venue"):
        dst["venue"] = src.get("venue")
    # authors — keep longest
    if len(str(src.get("authors") or "")) > len(str(dst.get("authors") or "")):
        dst["authors"] = src.get("authors")
    # sources list
    dst.setdefault("sources", [])
    if src["_source_slug"] not in dst["sources"]:
        dst["sources"].append(src["_source_slug"])


def build_unified(rows: list[dict]) -> list[dict]:
    by_arxiv: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    unified: list[dict] = []

    for r in rows:
        aid_raw = r.get("arxiv_id")
        aid = norm_arxiv(aid_raw) if aid_raw else None
        if aid:
            if aid in by_arxiv:
                merge_into(by_arxiv[aid], r)
                continue
            entry = {
                "arxiv_id": aid,
                "title": r.get("title"),
                "authors": r.get("authors"),
                "venue": r.get("venue"),
                "year": r.get("year"),
                "project_url": r.get("project_url") or None,
                "categories": [],
                "github_urls": [],
                "sources": [],
            }
            merge_into(entry, r)
            by_arxiv[aid] = entry
            unified.append(entry)
        else:
            tkey = norm_title(r.get("title"))
            if not tkey:
                # unusable row; skip
                continue
            if tkey in by_title:
                merge_into(by_title[tkey], r)
                continue
            entry = {
                "arxiv_id": None,
                "title": r.get("title"),
                "authors": r.get("authors"),
                "venue": r.get("venue"),
                "year": r.get("year"),
                "project_url": r.get("project_url") or None,
                "categories": [],
                "github_urls": [],
                "sources": [],
            }
            merge_into(entry, r)
            by_title[tkey] = entry
            unified.append(entry)

    # suspicious flag
    for e in unified:
        sus, why = is_suspicious_arxiv(e.get("arxiv_id"))
        if sus:
            e["suspicious"] = True
            e["suspicious_reason"] = why
    return unified


# ---------- bucket classification ----------

BUCKETS_ORDER = [
    "Agentic Search",
    "Tool Use / Tool-Integrated RL",
    "Memory & Long Context",
    "Reward Construction (Verifiable)",
    "Reward Construction (Unsupervised)",
    "Reward Models",
    "Multimodal / Vision-Language Agents",
    "GUI / Computer Use",
    "Embodied / Robotics / VLA",
    "Multi-Agent / Collaboration",
    "Algorithms / PPO-GRPO Variants",
    "Benchmarks & Evaluation",
    "Surveys",
    "Self-Play / Self-Evolution",
    "Process Supervision / Step-Level Rewards",
    "Other",
]

BUCKET_RULES: list[tuple[str, list[str]]] = [
    ("Surveys", ["survey", "review"]),
    ("Benchmarks & Evaluation", ["benchmark", "evaluation", "evaluating", "eval "]),
    ("Agentic Search", ["search", "retrieval", "rag", "deep research", "web agent", "browsing", "information seeking"]),
    ("Tool Use / Tool-Integrated RL", ["tool use", "tool-use", "tool integrat", "function call", "tool-integrated", "tool learning", "tool "]),
    ("Memory & Long Context", ["memory", "long context", "long-context", "long horizon", "long-horizon"]),
    ("Reward Construction (Verifiable)", ["verifiable", "rlvr", "synthesizing verifiable", "verifiable reward", "verifiable task"]),
    ("Reward Construction (Unsupervised)", ["unsupervised reward", "self-supervis", "unlabeled", "reward-free", "reward free", "without reward"]),
    ("Reward Models", ["reward model", "rm ", "process reward", "preference model", "judge model"]),
    ("Process Supervision / Step-Level Rewards", ["process supervis", "step-level", "step level", "step-wise", "stepwise reward"]),
    ("Multimodal / Vision-Language Agents", ["vlm", "vision-language", "vision language", "multimodal", "multi-modal", "image", "video"]),
    ("GUI / Computer Use", ["gui", "computer use", "computer-use", "ui agent", "screen", "desktop", "mobile agent", "android"]),
    ("Embodied / Robotics / VLA", ["embodied", "robot", "manipulation", "vla", "navigation"]),
    ("Multi-Agent / Collaboration", ["multi-agent", "multi agent", "multiagent", "collaborat", "cooperat", "debate"]),
    ("Algorithms / PPO-GRPO Variants", ["ppo", "grpo", "dpo", "reinforce", "policy optimization", "algorithm", "actor-critic", "trust region"]),
    ("Self-Play / Self-Evolution", ["self-play", "self play", "self-evolv", "self evolv", "self-improv", "self improv"]),
]


def bucketize(paper: dict) -> list[str]:
    haystack = " ".join(
        [paper.get("title") or ""]
        + list(paper.get("categories") or [])
    ).lower()
    hits: list[str] = []
    for bucket, needles in BUCKET_RULES:
        if any(n in haystack for n in needles):
            hits.append(bucket)
    if not hits:
        hits.append("Other")
    return hits


# ---------- writers ----------

def write_unified_jsonl(unified: list[dict]) -> None:
    with (OUT / "unified.jsonl").open("w") as f:
        for e in unified:
            out = {
                "arxiv_id": e.get("arxiv_id"),
                "title": e.get("title"),
                "authors": e.get("authors"),
                "venue": e.get("venue"),
                "year": e.get("year"),
                "project_url": e.get("project_url"),
                "github_urls": e.get("github_urls", []),
                "categories": e.get("categories", []),
                "sources": e.get("sources", []),
                "buckets": bucketize(e),
                "suspicious": e.get("suspicious", False),
                "suspicious_reason": e.get("suspicious_reason", ""),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")


def _arxiv_url(aid: str | None) -> str:
    return f"https://arxiv.org/abs/{aid}" if aid else ""


def _fmt_entry_line(e: dict) -> str:
    title = e.get("title") or "(untitled)"
    aid = e.get("arxiv_id")
    year = e.get("year") or "?"
    src = ",".join(e.get("sources") or [])
    sus = " **[SUSPICIOUS]**" if e.get("suspicious") else ""
    link = f"[arXiv:{aid}]({_arxiv_url(aid)})" if aid else "(no arxiv)"
    gh = ""
    if e.get("github_urls"):
        gh = " — code: " + ", ".join(f"[{i+1}]({u})" for i, u in enumerate(e["github_urls"][:3]))
    return f"- **{title}** — {year} — {link} — sources: `{src}`{gh}{sus}"


def write_by_arxiv(unified: list[dict]) -> None:
    withid = [e for e in unified if e.get("arxiv_id")]
    withid.sort(key=lambda e: e["arxiv_id"])
    noid = [e for e in unified if not e.get("arxiv_id")]
    noid.sort(key=lambda e: (e.get("title") or "").lower())
    lines = ["# Papers by arXiv ID", "", f"_{len(withid)} with arXiv id, {len(noid)} without._", ""]
    for e in withid:
        lines.append(_fmt_entry_line(e))
    lines += ["", "## Without arXiv ID", ""]
    for e in noid:
        lines.append(_fmt_entry_line(e))
    (OUT / "by-arxiv-id.md").write_text("\n".join(lines) + "\n")


def write_by_year(unified: list[dict]) -> None:
    by_year: dict[str, list[dict]] = defaultdict(list)
    for e in unified:
        y = str(e.get("year") or "unknown")[:4]
        by_year[y].append(e)
    years = sorted(by_year.keys(), key=lambda y: (y != "unknown", y), reverse=True)
    lines = ["# Papers by Year", ""]
    for y in years:
        ents = by_year[y]
        lines.append(f"## {y} ({len(ents)})")
        lines.append("")
        # group by first category (primary source's category)
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for e in ents:
            cats = e.get("categories") or []
            primary = cats[0].split(":", 1)[-1] if cats else "(uncategorized)"
            by_cat[primary].append(e)
        for cat in sorted(by_cat.keys()):
            lines.append(f"### {cat}")
            lines.append("")
            for e in sorted(by_cat[cat], key=lambda x: (x.get("title") or "").lower()):
                lines.append(_fmt_entry_line(e))
            lines.append("")
    (OUT / "by-year.md").write_text("\n".join(lines) + "\n")


def write_source_coverage(unified: list[dict]) -> None:
    slugs = list(SOURCES.keys())
    per_source = Counter()
    membership: dict[str, set[str]] = {s: set() for s in slugs}
    for i, e in enumerate(unified):
        key = e.get("arxiv_id") or norm_title(e.get("title"))
        for s in e.get("sources") or []:
            per_source[s] += 1
            membership[s].add(key)
    lines = ["# Source Coverage", "", "## Unique paper count per source", "",
             "| source | unique papers contributed |", "|---|---|"]
    for s in slugs:
        lines.append(f"| `{s}` | {per_source[s]} |")
    lines += ["", "## Overlap matrix (papers shared between each source pair)", "",
              "| | " + " | ".join(f"`{s}`" for s in slugs) + " |",
              "|" + "|".join(["---"] * (len(slugs) + 1)) + "|"]
    for a in slugs:
        row = [f"`{a}`"]
        for b in slugs:
            if a == b:
                row.append(str(len(membership[a])))
            else:
                row.append(str(len(membership[a] & membership[b])))
        lines.append("| " + " | ".join(row) + " |")

    # top pair
    pairs = []
    for i, a in enumerate(slugs):
        for b in slugs[i+1:]:
            pairs.append((a, b, len(membership[a] & membership[b])))
    pairs.sort(key=lambda x: -x[2])
    lines += ["", "## Top overlapping pairs", ""]
    for a, b, n in pairs:
        lines.append(f"- `{a}` ∩ `{b}` = **{n}**")
    (OUT / "by-source-coverage.md").write_text("\n".join(lines) + "\n")
    return pairs


def write_by_method(unified: list[dict]) -> None:
    buckets: dict[str, list[dict]] = {b: [] for b in BUCKETS_ORDER}
    for e in unified:
        for b in bucketize(e):
            buckets[b].append(e)
    lines = ["# Papers by Method / Theme", "",
             "Best-effort thematic grouping. A paper may appear in multiple buckets.", ""]
    for b in BUCKETS_ORDER:
        ents = buckets[b]
        lines.append(f"## {b} ({len(ents)})")
        lines.append("")
        for e in sorted(ents, key=lambda x: (str(x.get("year") or "0"), x.get("title") or ""), reverse=True):
            lines.append(_fmt_entry_line(e))
        lines.append("")
    (OUT / "by-method.md").write_text("\n".join(lines) + "\n")
    return {b: len(v) for b, v in buckets.items()}


def write_stats(unified: list[dict], bucket_counts: dict[str, int]) -> dict:
    total = len(unified)
    per_source = Counter()
    for e in unified:
        for s in e.get("sources") or []:
            per_source[s] += 1
    per_year = Counter(str(e.get("year") or "unknown")[:4] for e in unified)
    suspicious = sum(1 for e in unified if e.get("suspicious"))
    with_gh = sum(1 for e in unified if e.get("github_urls"))
    no_arxiv = sum(1 for e in unified if not e.get("arxiv_id"))

    lines = ["# Stats", "",
             f"- **Unique papers:** {total}",
             f"- **With github url:** {with_gh}",
             f"- **Without arXiv id:** {no_arxiv}",
             f"- **Flagged suspicious:** {suspicious}",
             "",
             "## Per source (appearances in unified set)", ""]
    for s in SOURCES:
        lines.append(f"- `{s}`: {per_source[s]}")
    lines += ["", "## Per year", ""]
    for y, n in sorted(per_year.items(), key=lambda x: x[0], reverse=True):
        lines.append(f"- {y}: {n}")
    lines += ["", "## Per bucket", ""]
    for b in BUCKETS_ORDER:
        lines.append(f"- {b}: {bucket_counts.get(b, 0)}")
    (OUT / "STATS.md").write_text("\n".join(lines) + "\n")
    return {"total": total, "per_source": per_source, "per_year": per_year,
            "suspicious": suspicious, "with_gh": with_gh, "no_arxiv": no_arxiv}


def write_notes(stats: dict, pairs: list[tuple[str, str, int]]) -> None:
    top = pairs[0] if pairs else None
    lines = [
        "# Aggregation Notes",
        "",
        "## Inputs",
        "",
        "- Four scraped awesome-list sources (necolizer, 0russwest0, tongjingqi, ventr1c).",
        "- `aitfind-morpheus-project` was skipped: single wrapper entry pointing back at 0russwest0's list, no paper payload.",
        "- `ventr1c` publishes many duplicate rows (same paper under multiple taxonomies); dedup collapses them.",
        "",
        "## Dedup keys",
        "",
        "- **Primary:** normalized `arxiv_id` — stripped `arXiv:` prefix, stripped `vN` version suffix, lowercased.",
        "- **Secondary (only when arxiv_id is missing):** normalized title (lowercase, punctuation → space, collapsed whitespace).",
        "",
        "## Merge rules on collision",
        "",
        "- Title: keep the longest string.",
        "- Year: keep the earliest parsable 4-digit year (paper provenance preference).",
        "- Venue / authors / project_url: first non-empty wins (authors: longest).",
        "- Categories: union, preserved as `source_slug:category` so provenance stays inspectable.",
        "- github_urls: union (list).",
        "- sources: union (list of slugs that contributed the paper).",
        "",
        "## Suspicious-id flag",
        "",
        "- An arXiv id is flagged when its `YYMM` prefix has month 00 or >12, or when the implied date is after today ({today}).".format(today=TODAY.isoformat()),
        "- Known offenders in ventr1c source: `2602.*`, `2601.06487`, etc. — these look hallucinated by whatever generated the source README. Kept in the index but flagged so humans can sanity-check.",
        "",
        "## Bucket classification",
        "",
        "- Heuristic keyword match against concatenation of title + `categories` list.",
        "- A paper can land in multiple buckets. Everything unmatched falls to `Other`.",
        "- Buckets are approximations — they are a reading aid, not a taxonomy.",
        "",
        "## Hand decisions / edge cases",
        "",
        "- Rows without a title AND without an arxiv_id are dropped (unusable).",
        "- `tongjingqi` rows include a `paper_url` field distinct from `arxiv_id` — we rely on the `arxiv_id` field, which is already populated for those rows.",
        "- Several ventr1c rows use `year: 2026` which is plausible (we're in April 2026), so 2026 by itself is NOT suspicious; only the invalid `YYMM` prefix is.",
        "- `source:category` entries preserve the original taxonomy of each source so downstream reviewers can trace where a tag came from.",
        "",
        "## Totals",
        "",
        f"- **{stats['total']}** unique papers across 4 sources.",
        f"- **{stats['suspicious']}** flagged suspicious (likely hallucinated arXiv ids).",
        f"- **{stats['with_gh']}** have at least one github URL; **{stats['no_arxiv']}** have no arXiv id.",
    ]
    if top:
        lines += ["", "## Overlap highlight", "",
                  f"- Largest source overlap: `{top[0]}` ∩ `{top[1]}` = **{top[2]}** papers."]
    (OUT / "aggregation-notes.md").write_text("\n".join(lines) + "\n")


# ---------- main ----------

def main() -> None:
    rows = load_all()
    print(f"loaded {len(rows)} raw rows")
    unified = build_unified(rows)
    print(f"unified: {len(unified)} unique papers")
    write_unified_jsonl(unified)
    write_by_arxiv(unified)
    write_by_year(unified)
    pairs = write_source_coverage(unified)
    bucket_counts = write_by_method(unified)
    stats = write_stats(unified, bucket_counts)
    write_notes(stats, pairs)
    # summary to stdout
    top = pairs[0] if pairs else None
    print(f"suspicious={stats['suspicious']} with_gh={stats['with_gh']} no_arxiv={stats['no_arxiv']}")
    if top:
        print(f"top overlap: {top[0]} ∩ {top[1]} = {top[2]}")


if __name__ == "__main__":
    main()
