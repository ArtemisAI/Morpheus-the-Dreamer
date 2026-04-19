# Morpheus-the-Dreamer

Research knowledge base for **Project Morpheus** — the reinforcement-learning observation-scoring system being built into [`claude-mem`](https://github.com/thedotmack/claude-mem) (development happens on the private `ArtemisAI/pi-mem-dev` fork, branch `feat/morpheus`, design spec at `docs/morpheus-rl-design.md`). This repo is the reading index and scratchpad for the RL / agent-RL / agentic-search literature that feeds Phase E of the Morpheus roadmap (reward modeling, observation scoring, feedback-loop training). It aggregates public awesome-lists into a normalized, cross-source corpus so the Morpheus design work can cite, dedupe, and prioritize papers without re-scraping.

## Directory layout

```
sources/       cloned awesome-list repos (gitignored; see sources/MANIFEST.md for remotes + SHAs)
scraped/       structured extractions per source (papers.jsonl, papers.md, categories.md)
papers/        (future) downloaded PDFs — gitignored for now pending storage decision
indexes/       (future) merged cross-source indexes (dedup, canonical IDs, topic tags)
docs/          (future) synthesis notes, reading queues, Morpheus-specific annotations
```

## Sources ingested

| Source | Entries | URL | Notes |
|---|---:|---|---|
| `necolizer-awesome-rl-for-agents` | 108 papers / 18 categories | https://github.com/Necolizer/awesome-rl-for-agents | RL training pipelines for LLM / MLLM agents |
| `0russwest0-awesome-agent-rl` | 20 papers | https://github.com/0russwest0/Awesome-Agent-RL | Recent 2025-03 to 2025-08 R1-wave agentic-RL, code-first |
| `tongjingqi-awesome-agent-rl` | 78 papers / 19 leaf categories (5 top areas) | https://github.com/tongjingqi/Awesome-Agent-RL | Reward-construction-centric |
| `ventr1c-awesome-rl-agentic-search` | 168 unique (332 rows, multi-slice) | https://github.com/ventr1c/Awesome-RL-based-Agentic-Search-Papers | RL-based agentic search specifically |
| `aitfind-morpheus-project` | redundant wrapper around `0russwest0` | — | Kept for provenance only |

Approximately ~375 paper-rows indexed across sources (pre-dedup).

## Status

**Research-ingestion phase.** Scraping of the five sources is complete and committed under `scraped/`. This is *not* a polished survey yet. Next steps, roughly in order:

1. Cross-source aggregation into `indexes/` (canonical paper IDs via arXiv ID / DOI / title hash).
2. Deduplication and category reconciliation across the five source taxonomies.
3. PDF pass — decide on storage strategy (local only vs. tracked) and populate `papers/`.
4. Synthesis docs under `docs/` keyed to Morpheus design questions (reward shape, observation granularity, credit assignment over tool-call sequences, feedback-loop sampling).

## License

This repository is a **content aggregation of public awesome-lists**. Every paper, repository, and external artifact referenced retains its own license as set by its original authors — nothing here relicenses upstream work. The organizational scaffolding contributed by this repo (scrape scripts, index structure, README, synthesis notes) is released under the **MIT License**. If a scraped file preserves upstream text verbatim, the upstream license continues to govern that text.

## Contributing / scope

This is a **reading index for Morpheus RL research**, not a general-purpose awesome-list. Scope is intentionally narrow:

- Reinforcement learning for LLM / MLLM agents (training, reward modeling, credit assignment).
- Agentic search and tool-use RL (relevant to claude-mem's observation stream).
- Observation scoring, memory relevance, and feedback-loop training signals.

PRs that broaden scope beyond those axes will probably be declined. PRs that add a missed paper within scope, fix a miscategorization, or contribute a synthesis note are welcome. Please include the upstream source and (if applicable) arXiv ID.
