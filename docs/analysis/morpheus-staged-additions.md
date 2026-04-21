# Morpheus — Staged-New Additions (247 papers, 2026-04-20 drop)

> Filter pass over `corpus/staging-new.jsonl` through the Morpheus lens
> (memory ops on sequences + RL/preference training of retention / summarization
> / retrieval policies, per `docs/design/morpheus-v0-spec.md` and
> `docs/analysis/morpheus-top-papers.md`). Title+abstract only; no PDFs read.

---

## Tier-S additions (direct structural priors — ≤5)

### NS1. `2604.18002` — Neural Garbage Collection: Learning to Forget while Learning to Reason (2026-04-20)

- Model *learns* which KV entries to evict mid-reasoning, trained **end-to-end from outcome reward alone** — the exact architecture shape of Morpheus's "learn keep/drop from terminal retention" v0 hypothesis, transposed to token-level memory.
- Treats eviction as a discrete RL action inside a chain-of-thought — the cleanest published analog to Morpheus's `retained / superseded / merged` four-signal table, collapsed to a single binary keep/drop decision trained from task reward.
- > "the model reasons, it periodically pauses, decides which KV cache entries to evict, and continues to reason conditioned on the remaining cache ... trained end-to-end from outcome-based task reward alone."

### NS2. `2604.18349` — HiGMem: Hierarchical and LLM-Guided Memory System for Long-Term Conversational Agents (2026-04-20)

- Two-level event/turn memory where an LLM **predicts which turns are worth reading** using event summaries as anchors — directly maps to Morpheus's observation + consolidated_digest two-level store and to the planned policy scoring `is_consolidated_digest = 1` rows.
- Motivated by exactly Morpheus's failure mode: vector similarity alone "produces bloated evidence sets ... lowers retrieval precision, increases answer-stage context cost." Morpheus's `relevance_score × policy_weight` blend is the quantitative response to this; HiGMem is the architectural validation.
- > "a two-level event-turn memory system that allows LLMs to use event summaries as semantic anchors to predict which related turns are worth reading."

### NS3. `2604.18478` — WorldDB: A Vector Graph-of-Worlds Memory Engine with Ontology-Aware Write-Time Reconciliation (2026-04-20)

- First published system that **treats supersession and contradiction as first-class write-time operations** on persistent agent memory — exactly Morpheus's `superseded_by` / `consolidated_into` pointers, with content-addressed immutability for audit trails.
- Extends flat bitemporal KG memory (Graphiti/Memento/Hydra DB) with recursive node composition — a strong architectural prior for how Morpheus's bucket namespace could evolve once the weight table is shipped.
- > "Persistent memory is the bottleneck separating stateless chatbots from long-running agentic systems ... no first-class notion of supersession or contradiction."

### NS4. `2604.18401` — StepPO: Step-Aligned Policy Optimization for Agentic RL (2026-04-20)

- Directly attacks the **delayed/sparse reward + long variable context** regime that Morpheus faces. Positions itself as post-token-level Agentic RL — the escalation path beyond MT-GRPO/MT-PPO (Tier-S S7) for when per-turn credit is needed across bucket keys.
- "Step-aligned" = reward aligned with agentic step boundaries; this is the correct credit-assignment unit for Morpheus (one observation = one step) and a cleaner abstraction than token-level PPO clipping.
- > "Agentic RL targets multi-turn interactive settings ... optimize core agentic capabilities ... addressing new challenges including delayed and sparse rewards, as well as long and variable context."

### NS5. `2604.17892` — LEPO: Latent Reasoning Policy Optimization (2026-04-20)

- RL applied directly on **continuous latent representations**, with Gumbel-Softmax injecting stochasticity to recover rollout diversity — the Dreamer-adjacent framing the project name invokes, and the algorithm Morpheus would need if it ever moves from a classifier over raw text to a latent-state scorer.
- > "LEPO, a novel framework that applies RL directly to continuous latent representations ... in rollout stage, LEPO maintains stochasticity to enable diverse trajectory sampling."

---

## Tier-A additions (strong secondary relevance — ≤15)

| # | arxiv_id | Title | One-line why |
|---|----------|-------|-------------|
| NA1 | `2604.17935` | How Much Cache Does Reasoning Need? Depth-Cache Tradeoffs | Theoretical depth/cache lower bounds — quantitative grounding for Morpheus's context-size caps and compression claims. |
| NA2 | `2604.17886` | Latent Preference Modeling for Cross-Session Personalized Tool Calling | Cross-session latent preferences, memory-as-evolving-hypothesis, 1.24% tokens vs full-history — validates per-user/per-project policy split (v0 §10 q3). |
| NA3 | `2604.18235` | Negative Advantage Is a Double-Edged Sword: Calibrating Advantage in GRPO for Deep Search | GRPO advantage-calibration under intermediate-step / terminal-reward mismatch — exact symptom Morpheus will hit with four-signal process rewards. |
| NA4 | `2604.18206` | A Control Architecture for Training-Free Memory Use | Applicability control (when to trigger memory, when to trust) + evidence-based bank governance — training-free baseline for Morpheus's serve path. |
| NA5 | `2604.17948` | RAVEN: Retrieval-Augmented Vulnerability Exploration Network | Multi-agent RAG with explicit knowledge curation from fixed authoritative bank — reference architecture for Morpheus's consolidated-digest bank. |
| NA6 | `2604.18327` | PARM: Pipeline-Adapted Reward Model | DPO-aligned RM that fixes RM-vs-pipeline inconsistency in multi-stage pipelines — directly relevant if Morpheus's serving weight diverges from training signal. |
| NA7 | `2604.17931` | LiteResearcher: Scalable Agentic RL Training for Deep Research | Lite virtual-world RL training recipe; cheap substitute for real rollouts — template for batch-offline Morpheus if we ever need counterfactuals. |
| NA8 | `2604.18530` | OGER: Robust Offline-Guided Exploration Reward for Hybrid RL | Offline teacher + online RL hybrid — the exact regime Morpheus lives in (historical feedback as teacher, no online rollouts). |
| NA9 | `2604.18574` | When Can LLMs Learn to Reason with Weak Supervision? | Systematic study of RLVR under scarce / noisy / proxy rewards — Morpheus's `retained_in_context` is a weak-supervision signal; this paper sets expectations. |
| NA10 | `2604.17866` | Latent Abstraction for Retrieval-Augmented Generation (LAnR) | Unified retriever+generator in one model's latent space; adaptive stop — upgrade path if Morpheus's scorer becomes a latent module. |
| NA11 | `2604.18419` | Knowing When to Quit: Dynamic Abstention in LLM Reasoning | Reframes mid-generation abstention as an RL action with a reward parameter — formally identical to Morpheus's "drop this observation" action. |
| NA12 | `2604.17912` | Learning to Correct: Calibrated RL for Multi-Attempt CoT (CAL-GRPO) | Unbiased-gradient weighting for per-attempt rewards; the math pattern Morpheus needs for weighting across bucket observations. |
| NA13 | `2604.18567` | Latent Phase-Shift Rollback: KV-Cache Steering | Inference-time rollback and KV-cache steering as a control action — an alternative to supersession; interesting negative prior for whether Morpheus needs to rewrite vs. reweight. |
| NA14 | `2604.18131` | Training LLM Agents for Spontaneous, Reward-Free Self-Evolution | Outcome-reward trains agent to *summarize* world knowledge — validates the consolidation-digest-as-trainable-artifact angle Morpheus currently leaves prompt-driven. |
| NA15 | `2604.18489` | Aligning LMs with Rule-Based Constraints via DPO + KTO | Rule-based preference generation + DPO→KTO sequential alignment — exact recipe Morpheus-v0 could copy if it swaps DPO for KTO on unpaired negatives. |

---

## Rejected but interesting (≤10)

- `2604.18137` **AQPIM** — PIM-friendly KV quant; hardware path for Morpheus's cache but no policy learning.
- `2604.18103` **DASH: Delta Attention Selective Halting** — training-free token halting on stability; closest non-RL analog to "forget stabilized content."
- `2604.17979` **Architecture Matters More Than Scale (Financial QA)** — retrieval vs memory augmentation under compute constraints; useful for Morpheus's SME-style deployment story.
- `2604.18362` **ArbGraph: Conflict-Aware Evidence Arbitration** — pre-generation arbitration of contradictory evidence; conceptually adjacent to `superseded` resolution.
- `2604.18566` **Benchmarking Cloud vs. Local LLMs on CLD Extraction** — documents memory limits in long-context local models; motivates Morpheus's compression focus.
- `2604.18473` **BAR: Train Separately, Merge Together (MoE post-training)** — modular domain experts; intriguing if Morpheus ever wants per-project policy heads.
- `2604.18424` **Context-Aware Search Under Token Erasure** — IR analysis under partial query preservation; theoretical support for importance-weighted compression.
- `2604.18464` **Semantic Step Prediction (STP at step boundaries)** — latent trajectory regularization at reasoning-step boundaries; potential feature extractor for bucket keys.
- `2604.18239` **Disentangled Preference Optimization Dynamics** — unified decomposition of DPO-family objectives + likelihood-displacement diagnostics; useful when tuning Morpheus-v0 DPO.
- `2604.17928` **HEAL: Entropy Collapse in Few-Shot RLVR** — entropy-dynamics alignment under low-data RL; relevant because Morpheus will train on small per-bucket samples.

---

## Summary (5 lines)

1. Prioritize **NS1 2604.18002 (NGC)**, **NS2 2604.18349 (HiGMem)**, **NS3 2604.18478 (WorldDB)** for immediate PDF download + docling — these three are the clearest 2026-04 structural analogs to Morpheus and should be cited in the v0 design's related-work.
2. Second priority: **NS4 2604.18401 (StepPO)** and **NS5 2604.17892 (LEPO)** — required reading for any escalation past the tabular/DPO v0.
3. Of the 15 Tier-A picks, the high-leverage five for docling are `2604.17935`, `2604.18235`, `2604.18206`, `2604.18530`, `2604.18574` — they cover cache theory, GRPO calibration, training-free baseline, offline-guided hybrid RL, and weak-supervision limits respectively.
4. The remaining 10 Tier-A and 10 "rejected-but-interesting" can stay abstract-only until the v0 hypothesis resolves.
5. Total new: **5 Tier-S + 15 Tier-A + 10 skim** = 30 of 247 staged papers worth any further attention; the other 217 are off-lens (biomedical, hardware, multimodal, safety-only, domain benchmarks).

---

## Suggested edit to `docs/analysis/morpheus-top-papers.md` (not applied)

The existing "New picks (from staging-new.jsonl)" subsection at line ~290 already previews these picks. Concrete fold-in:

1. Promote **`2604.18002` (NGC)** from the "New picks" subsection into the main **Tier S** block as `S9` — it deserves equal billing with MEM1/MemAgent/MemSearcher given the compiler-style end-to-end forget-from-outcome framing (closest to Morpheus's training signal in the entire corpus).
2. Promote **`2604.18349` (HiGMem)** from "New picks" into **Tier S** as `S10` — two-level memory + LLM-guided retention prediction is the architectural validation Morpheus needs to cite.
3. Add **`2604.18478` (WorldDB)** to **Tier A** as `A16` — write-time reconciliation of supersession/contradiction is a novel and directly-applicable write-path primitive not covered elsewhere in the current Tier-A list.
4. Add **`2604.18401` (StepPO)** to **Tier A** as `A17`, bridging MT-GRPO (S7) and the Agentic-RL escalation path.
5. Keep **`2604.17892` (LEPO)**, **`2604.17886`**, **`2604.17935`** where they are (Tier S's "New picks" subsection) pending docling conversion — no immediate main-body move; they are speculative upgrade paths rather than structural priors.
6. Retire the freestanding "New picks" subsection once items 1–4 are folded in, replacing it with a one-line pointer to this file (`morpheus-staged-additions.md`) for future staged drops.
