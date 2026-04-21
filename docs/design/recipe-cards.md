# Tier-S Recipe Cards

One card per paper. Formulas in plain text. "For Morpheus" is the one thing we steal.

---

## 2506.15841 — MEM1

**Core move:** Agent rewrites a single compact `<IS>` (internal state) each turn; only agent-generated tokens are credited.

**Reward:** terminal F1 vs. ground-truth answer. Multi-objective tasks = sum of per-sub-question F1. Equation not captured in md — check PDF for exact binding.

**Data:** `(question, tool-interleaved trajectory [IS_1, A_1, O_1, ..., IS_T, answer], gold_answer)`. Single reward at terminal.

**Update:** PPO-style with masked trajectory policy optimization — gradient only on agent-generated tokens; retrieved tokens are loss-masked. Framework: veRL.

**Key hyperparams:** 4×H100/H200; batch=mini-batch=64; actor LR 1e-6, critic LR 1e-5, 50-step linear warmup; temperature 1.0 train / 0.01 eval.

**For Morpheus:** masked-token gradient is the *rule* — never credit tokens the compiler injected; only credit the policy's keep/drop decisions.

---

## 2507.02259 — MemAgent

**Core move:** Overwrite a fixed-size memory token span at each chunk; train end-to-end with Multi-Conv DAPO (GRPO variant) where the final-conversation reward is broadcast to all prior conversations.

**Reward (rule-based verifier):**
- Single-gold: `R = 1 if gold ∈ answer else 0` (scaled by format).
- Multi-gold: `R = |{y_i ∈ answer}| / |Y|`.

**Data:** `(long_doc, question, K read-write episodes [m_{k-1}, chunk_k → m_k], final_answer, gold)`. One reward at end; advantage broadcast.

**Update:** GRPO with clipped objective + KL penalty; loss-masking over retrieved tokens; Multi-Conv variant treats each read-write loop as an independent optimization target sharing the trajectory advantage.

**Key hyperparams:** KL 1e-3; entropy loss disabled; AdamW LR 1e-6, constant with linear warmup; rollout batch 128 (7B) / 256 (14B); group size G=16; sample-to-backprop ratio 16:1. Base: DeepSeek-R1-Distill-Qwen, Qwen2.5-Instruct-1M, QwenLong-L1.

**For Morpheus:** the broadcast-advantage trick — one terminal reward credits every historical write decision in the trajectory. Maps directly to "did this chunk get retained later → reward all prior keep/drop ops in the same session."

---

## 2511.02805 — MemSearcher

**Core move:** Every turn, LLM emits a new memory `m_i` that replaces `m_{i-1}`, scoped to what's needed for the final answer. Trained with multi-context GRPO.

**Reward:**
```
R = 1.0 · f_format · F1(a_pred, a_gold)
```
Format reward = tag correctness + `\boxed{}` presence; answer reward = token-level F1.

**Data:** `(q, [m_0=∅, t_1, a_1, o_1, m_1, t_2, a_2, o_2, m_2, ...], a_gold)`. Context per turn = only `(q, m_{i-1}, current turn)` — never full history.

**Update:** Multi-context GRPO. Compute one reward `R_i` per trajectory; normalize within group to get `A_i`; broadcast `A_i` to every conversation `T_{i,j}` in the trajectory; optimize each conversation as independent target. Loss-mask retrieval tokens.

**Key hyperparams:** LR 1e-6; train batch 256; 1 epoch; rollouts/group G=5; rollout temp 1.0; KL 0.001; clip 0.2; context 8K; memory ≤1024 tokens. Base: Qwen2.5-3B-Instruct (wins at 3B vs. 7B baselines).

**For Morpheus:** this is the closest behavioral twin — the overwrite/retain decision is *the* learned action. Steal the memory-size cap (1024 tokens) and the terminal-F1 reward shape.

---

## 2505.10978 — GiGPO

**Core move:** Two-level advantage: episode-level (trajectory mean) + step-level (anchor-state group mean). Anchor = environment-state hash; grouping is an offline hashmap pass, no extra rollouts.

**Reward:** `R_t^(i)` per-step (sparse ok); discounted return `R_t^(i) = Σ γ^k r_{t+k}` for step advantage.

**Data:** `(x, trajectory [s_t, a_t, r_t]_{t=1..T}, outcome)`. Each state hashed to anchor key ~s; group across trajectories sharing ~s.

**Update:** GRPO-clipped objective with combined advantage `A = A_E(τ) + ω · A_S(a_t)`, β controls KL. F_norm = std (default) or 1 (ablation — std introduces difficulty bias).

**Key hyperparams:** ω balances episode vs. step (paper's default implied); γ discount factor; β KL coefficient; tested on Qwen2.5-{1.5B, 7B}-Instruct; verl-agent framework (https://github.com/langfengQ/verl-agent).

**For Morpheus:** bucket key = anchor-state hash. Our "shrinkage toward global mean" *is* the step-level relative advantage. This is the natural escalation path from tabular weights.

---

## 2505.15107 — StepSearch (StePPO)

**Core move:** PPO with token-level dense rewards = information-gain + redundancy-penalty, plus terminal F1 + keyword-hit rate.

**Reward:**
- Global (last token): `R_global = F1(a_pred, a_gold) + γ_key · keyword_hit_rate`.
- Step (last token of each round): `r_t^step = G_t − P_t` where `G_t` = avg information gain over n golden docs this round, `P_t` = fraction of retrieved docs in round t that were already in H_{t-1}`.

**Data:** `(q, [thought_t, search_t, retrieved_t]_{t=1..T}, a_gold, golden_docs)`. Needs gold-document annotation per step — MuSiQue pipeline.

**Update:** PPO with GAE; loss-mask retrieved tokens; clip ε=0.2.

**Key hyperparams:** KL β=1e-3; clip 0.2; rollout temp 1.0; top_p 1.0. Base: Qwen-2.5-{3B,7B}-{Base,Instruct}. Framework: verl. Ablation: StePPO > PPO > GRPO (GRPO prone to reward collapse at higher LR).

**For Morpheus:** information-gain-minus-redundancy is the *right* shape for our signal table — `retained_in_context` ≈ IG, `merged_into` ≈ redundancy. But we don't have gold docs, so **we won't use this as v0**; revisit for v1.

---

## 2505.14069 — ReasonRAG

**Core move:** Use MCTS to assign process-level rewards via Shortest Path Reward Estimation (SPRE), then train with DPO on preference pairs.

**Reward (SPRE per state y_{1:t}):**
```
r(y_{1:t}) = max_i [ α^{step(rollout_i)} · v(rollout_i) ]
```
where `v` = F1 to gold, `α ∈ (0,1]` decays long trajectories, max taken across MCTS rollouts.

**Data:** Preference tuples `(x, y_<t, y_w, y_l)` where y_w/y_l are the MCTS-ranked next-step pair at each branching state.

**Update:** DPO objective — `L = -E log σ(β (log π(y_w) − log π_ref(y_w)) − β (log π(y_l) − log π_ref(y_l)))`.

**Key hyperparams:** β KL constraint (DPO); retriever BGE top-3; base Qwen2.5-7B-Instruct; FlashRAG/Wikidump 2018. Beats Search-R1 at 34.4% EM / 42.3% F1.

**For Morpheus:** DPO is a cheap, on-laptop alternative to PPO/GRPO. If we have pairs of (kept observation, dropped observation) on the same bucket, DPO works without a critic.

---

## 2505.11821 — MT-GRPO / MT-PPO

**Core move:** Formal multi-turn MDP treatment. MT-PPO wins because MT-GRPO needs exponential rollouts for per-turn advantages.

**Reward:**
- Outcome: `R^O = 1·f_em + 0.1·f_format` (correct), `−1·(1−f_format)` (format penalty).
- Intermediate per turn k: `R_k^I = R_k^{retrieval} + R_k^{format} − λ_s · n_search_k` (search-count penalty).

**Data:** `(x, [l_1, f_1, ..., l_K, f_K], R^I_{1..K}, R^O)`. Per-turn rewards required.

**Update:** MT-PPO = PPO with GAE over token-level rewards `r_t = 1{end-of-turn-k} · R_k^I + 1{final} · R^O`. Critic provides value function. MT-GRPO = GRPO with per-turn advantage `A_k^i = (R_k^i − mean) / std` — exponential rollouts.

**Key hyperparams:** λ_s for search penalty; GAE γ, λ; PPO clip. Built on Search-R1 codebase.

**For Morpheus:** if we ever escalate beyond tabular, **MT-PPO is simpler than MT-GRPO** for credit assignment over our 4 signals. Turn-level verifiable rewards = our 4 signals. Trajectory-only reward → "unstable training and suboptimal performance."

---

## 2509.13313 — ReSum / ReSum-GRPO

**Core move:** Periodic external-tool summarization resets context; agent resumes from `(q, summary)`. Train with ReSum-GRPO = broadcast trajectory advantage to all K+1 segments.

**Reward:** terminal trajectory reward (Pass@k / F1 / exact-match) normalized within group.

**Data:** One ReSum trajectory = K+1 segments separated by summarization events; all segments share one outcome reward.

**Update:** GRPO with segment-broadcast advantage. Summary tool is frozen (ReSumTool-30B, distilled from a larger teacher).

**Key hyperparams:** Base = WebSailor-{3B,7B,30B}; summary tool = Qwen3-30B-A3B-Thinking-2507 fine-tuned. +8.2% avg vs. GRPO-ReAct baseline.

**For Morpheus:** our consolidation digest = their summary tool. **We won't train the summarizer in v0** — keep it prompt-driven; train only the retain/drop scorer.

---

## Where papers disagree — and what we pick

| Dimension | Options | Morpheus v0 pick | Why |
|---|---|---|---|
| RL algo | PPO (StepSearch, MT-PPO), GRPO (MemAgent, MemSearcher, ReSum), DPO (ReasonRAG) | **DPO** | No critic, no rollouts, works offline on historical pairs. Matches our "no online gradient" constraint. |
| Reward density | Terminal only (MEM1, MemAgent, MemSearcher, ReSum) vs. per-step (StepSearch, MT-PPO, ReasonRAG) | **Terminal** | We only have the compiler's retention decision. Per-step IG needs gold docs we don't have. |
| Credit assignment | Broadcast (MemAgent, MemSearcher, ReSum) vs. per-turn (MT-PPO, GiGPO) | **Broadcast** | Simpler, no critic; matches DPO. |
| Memory update | Overwrite (all) vs. append | **Keep/drop on append** | v0 scope = scoring existing append-only observations. Overwrite is v2. |
| Base model | Qwen2.5-3B-Instruct (MemSearcher), 7B (most), 14B+ | **Qwen2.5-3B-Instruct** | MemSearcher shows 3B beats 7B baselines on this task family; fits one 24GB GPU. |
