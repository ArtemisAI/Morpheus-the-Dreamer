# Morpheus-the-Dreamer

Morpheus-the-Dreamer is a curated 332-paper research corpus on agentic reinforcement learning and memory for LLMs. It exists to anchor **Phase E of [claude-mem](https://github.com/thedotmack/claude-mem)** — the RL-based observation-scoring system tracked as *Project Morpheus* ([pi-mem-dev issue #28](https://github.com/ArtemisAI/pi-mem-dev/issues/28)). The repo ships a normalized SQLite index, per-paper JSONL records, locally-downloaded PDFs, docling-converted markdowns, and the synthesis / design notes that feed the v0 spec.

## Quickstart

```bash
git clone https://github.com/ArtemisAI/Morpheus-the-Dreamer.git
cd Morpheus-the-Dreamer
python3 scripts/build_index_db.py            # rebuilds corpus/morpheus.db from JSONL
```

Query examples (via `sqlite3` or Python):

```sql
SELECT arxiv_id, title FROM papers WHERE year = 2025 LIMIT 10;
SELECT p.arxiv_id, p.title FROM papers p
  JOIN paper_tags pt ON pt.paper_id = p.id
  JOIN tags t ON t.id = pt.tag_id
  WHERE t.name = 'reward-modeling';
SELECT snippet(fulltext, -1, '[', ']', '…', 10) FROM fulltext
  WHERE fulltext MATCH 'GRPO' LIMIT 5;
```

## Directory layout

```
Morpheus-the-Dreamer/
├── corpus/                canonical corpus artifacts
│   ├── morpheus.db        SQLite index (papers, authors, tags, fulltext FTS5)
│   ├── unified.jsonl      332 canonical per-paper rows
│   ├── metadata-enriched.jsonl  arXiv metadata + abstracts
│   ├── authors.jsonl      2,616 author records
│   ├── staging-new.jsonl  247 papers staged by weekly refresh (not yet ingested)
│   ├── refresh-log.jsonl  history of weekly_arxiv_refresh runs
│   ├── SCHEMA.md / STATS.md / aggregation-notes.md / completeness-audit.md
├── papers/
│   ├── arxiv/             291 downloaded PDFs (+ MANIFEST.jsonl; PDFs gitignored)
│   └── markdown/          587 docling-converted markdown files
├── scripts/               build + enrich + refresh pipelines
├── docs/
│   ├── analysis/          corpus-overview, morpheus-top-papers, tagger-recall-fix
│   └── design/            recipe-cards, morpheus-v0-spec, morpheus-open-questions
├── .mcp.json              arxiv MCP server config (storage rooted at papers/arxiv/)
└── SESSION-RESUME.md      handoff notes for the next session
```

## Key artifacts

| Artifact | Path | Shape |
|---|---|---|
| SQLite index | `corpus/morpheus.db` | 332 papers / 2,616 authors / 46 tags / 4,477 paper-tags / 3,327 paper-authors |
| Canonical rows | `corpus/unified.jsonl` | 332 lines |
| Enriched metadata | `corpus/metadata-enriched.jsonl` | arXiv abstracts + categories |
| Authors | `corpus/authors.jsonl` | 2,616 records |
| PDFs | `papers/arxiv/*.pdf` | 291 files (gitignored, ~1.0 GB) |
| Markdowns | `papers/markdown/` | 587 files (docling, CUDA) |
| Corpus analysis | `docs/analysis/corpus-overview.md` | distribution, gaps, outliers |
| Top-papers reading list | `docs/analysis/morpheus-top-papers.md` | prioritized for Phase E |
| Tagger audit | `docs/analysis/tagger-recall-fix.md` | false-negative recovery |
| Recipe cards | `docs/design/recipe-cards.md` | reusable training patterns |
| v0 spec | `docs/design/morpheus-v0-spec.md` | binary-reward design |
| Open questions | `docs/design/morpheus-open-questions.md` | unresolved design calls |

## Refreshing the corpus

Run `python3 scripts/weekly_arxiv_refresh.py` to pull new arXiv papers matching Morpheus scope into `corpus/staging-new.jsonl` (deduped against the DB). The helper talks to the arXiv MCP server configured in `.mcp.json`. Promotion into `corpus/morpheus.db` + PDF download + markdown conversion is a manual step (see `scripts/README.md`). `scripts/install_weekly_cron.sh` writes a user crontab entry — **run only if you want the refresh to recur locally**. The cron installed during session 2026-04-20 was session-only and has been cancelled.

## Status

- 332 papers indexed, enriched, tagged.
- 291/291 in-scope PDFs downloaded and markdown-converted.
- 247 new papers staged by the weekly refresh (2026-04-01 → 04-21), **not yet ingested**.
- Morpheus v0 spec committed; open questions tracked for the next session.

## Links

- Parent: [`claude-mem`](https://github.com/thedotmack/claude-mem) — dev on private fork `ArtemisAI/pi-mem-dev`, branch `feat/morpheus`.
- Design doc in parent: `docs/morpheus-rl-design.md`.
- Research plan / Project Morpheus: [pi-mem-dev issue #28](https://github.com/ArtemisAI/pi-mem-dev/issues/28) (private).

## License

Content aggregation of public research: every paper retains its original license. The scaffolding (scripts, schema, synthesis notes) is MIT.
