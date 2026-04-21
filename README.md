# Morpheus-the-Dreamer

Research knowledge base for **Project Morpheus** — the reinforcement-learning observation-scoring system being built into [`claude-mem`](https://github.com/thedotmack/claude-mem) (development happens on the private `ArtemisAI/pi-mem-dev` fork, branch `feat/morpheus`, design spec at `docs/morpheus-rl-design.md`). This repo is the reading index and scratchpad for the RL / agent-RL / agentic-search literature that feeds Phase E of the Morpheus roadmap (reward modeling, observation scoring, feedback-loop training).

It is a **332-paper curated corpus on agentic RL for LLMs**: a normalized, deduplicated, enriched index with arXiv metadata, author records, and rule-based tags so the Morpheus design work can cite and prioritize papers without re-scraping.

## Directory layout

```
corpus/           machine-readable corpus artifacts (unified.jsonl, morpheus.db, SCHEMA.md, STATS.md)
corpus/views/     flat human-readable views (by-arxiv-id, by-year, by-method)
papers/arxiv/     downloaded arXiv PDFs (gitignored) + MANIFEST.jsonl
papers/markdown/  docling-converted markdowns
scripts/          index + enrichment + refresh pipelines
docs/             synthesis notes, reading queues, Morpheus-specific annotations (WIP)
```

## Corpus at a glance

- **332** unique papers, **291** with arXiv IDs and locally-downloaded PDFs.
- SQLite index at `corpus/morpheus.db` with `papers`, `authors`, `paper_authors`,
  `tags`, `paper_tags`, `downloads`, and `fulltext` (FTS5) tables. See
  `corpus/SCHEMA.md` for populated-state counts.
- JSONL artifacts: `corpus/unified.jsonl` (canonical per-paper rows),
  `corpus/metadata-enriched.jsonl` (arXiv metadata + abstracts),
  `corpus/authors.jsonl` (2.5k+ author records).

## Scope

- Reinforcement learning for LLM / MLLM agents (training, reward modeling, credit assignment).
- Agentic search and tool-use RL (relevant to claude-mem's observation stream).
- Observation scoring, memory relevance, and feedback-loop training signals.

## License

This repository is a **content aggregation of public research**. Every paper, repository, and external artifact referenced retains its own license as set by its original authors — nothing here relicenses upstream work. The organizational scaffolding contributed by this repo (index scripts, schema, README, synthesis notes) is released under the **MIT License**.

## Contributing / scope

This is a **reading index for Morpheus RL research**, not a general-purpose awesome-list. PRs that broaden scope beyond the axes above will probably be declined. PRs that add a missed paper within scope, fix a miscategorization, or contribute a synthesis note are welcome. Please include the arXiv ID when applicable.
