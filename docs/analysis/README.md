# Morpheus Corpus Analysis

This directory holds corpus-wide syntheses of the Morpheus knowledge base.

Primary artifacts:

- **[morpheus-top-papers.md](./morpheus-top-papers.md)** — Morpheus-lens ranking
  of the corpus against the `claude-mem/docs/morpheus-rl-design.md` scope.
  Tier S / A / B, new-picks from `corpus/staging-new.jsonl`, cross-cutting themes,
  literature gaps, and a 6-paper reading order for a new Morpheus engineer.
- **[corpus-overview.md](./corpus-overview.md)** — corpus-wide quality baseline,
  tag / method / benchmark / base-model / compute landscape, and a list of
  Phase E gaps and follow-ups. Based on **177 / 291** Docling-converted papers as
  of **2026-04-21T04:04:33Z** (the Docling batch is still running; rerun
  `/tmp/analyze_corpus.py` after it completes to refresh the numbers).

## Next step

The Tier-S analysis feeds directly into the v0 implementation design in
**[../design/](../design/)** — start with `recipe-cards.md`, then the spec.
