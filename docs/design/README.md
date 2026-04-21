# Morpheus Design

Opinionated v0 design — paper-grounded, implementable in 2 weeks.

Read in this order:

1. **[recipe-cards.md](./recipe-cards.md)** — one ≤30-line card per Tier-S paper
   (MEM1, MemAgent, MemSearcher, GiGPO, StepSearch, ReasonRAG, MT-GRPO/MT-PPO,
   ReSum) with exact reward, data, update rule, and hyperparameters extracted
   verbatim. Final table picks one option per design axis.
2. **[morpheus-v0-spec.md](./morpheus-v0-spec.md)** — the v0 spec. One-sentence
   problem, falsifiable 2-week hypothesis, explicit non-goals, data pipeline,
   policy architecture (Qwen2.5-3B-Instruct + DPO), training pseudocode,
   evaluation metric, file layout, and the disagreements we have with
   `claude-mem/docs/morpheus-rl-design.md`.
3. **[morpheus-open-questions.md](./morpheus-open-questions.md)** — 10
   value/cost-ranked open questions with the cheapest experiment that answers
   each. Q1, Q2, and Q10 should be answered **before** any training run.

Upstream references (read-only):
- `claude-mem/docs/morpheus-rl-design.md` — prior Phase E design
- `claude-mem/docs/morpheus-architecture.md` — Kairos-comparison roadmap
- `docs/analysis/morpheus-top-papers.md` — Tier-S ranking this design draws on
