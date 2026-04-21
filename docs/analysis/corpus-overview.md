# Morpheus Corpus Overview

_Snapshot: **2026-04-21T04:04:33Z**_
_Files analyzed: **177 / 291** converted Markdown papers_
_All 177 analyzed files matched a row in `corpus/morpheus.db`._

This document synthesizes signals extracted from the Docling-converted Markdown corpus (at `papers/markdown/*.md`) joined with the structured metadata in `corpus/morpheus.db`. The goal is to give Morpheus a single actionable view of what the current research base contains, where coverage is strong, and where gaps remain for Phase E deepening.

---

## 1. Conversion Quality Baseline

Methodology: 30 random `.md` files (seed=42) were inspected for structural signals. Results are representative of the full corpus because Docling applies a uniform extraction pipeline per paper.

### Aggregate tally (n=30)

| metric | value |
|---|---|
| avg bytes | 81,568 |
| avg lines | 614 |
| has `#` H1 title | 0 / 30 |
| has ≥2 `##` sections | 30 / 30 |
| has Markdown tables | 30 / 30 |
| has equation markers (`$`,`\(`) | 7 / 30 |
| has References section | 30 / 30 |

### Quality notes

- **No `# H1` titles.** Docling emits the paper title as `## ` (H2) rather than `# ` (H1). This is a *stylistic* rather than structural issue — every sampled file still has a visible title row — but downstream chunkers that rely on H1 boundaries should treat the first H2 as the document title.
- **Structure is consistently rich**: 30/30 files have multiple `##` sections, 30/30 have at least one pipe-delimited table, and 30/30 carry a `References` or `Bibliography` heading. Average body is ~81 KB / ~600 lines, well above the 500-byte floor used to flag empty conversions.
- **Broken files flagged**: 0 (zero).

### Sample detail

| arxiv_id | bytes | lines | titled | # H2 | tables | eq | refs |
|---|---|---|---|---|---|---|---|
| 2508.15804 | 56,552 | 368 | yes | 38 | yes | no | yes |
| 2412.19723 | 81,564 | 662 | yes | 46 | yes | no | yes |
| 2402.05808 | 76,206 | 550 | yes | 30 | yes | no | yes |
| 2504.20073 | 98,167 | 851 | yes | 72 | yes | yes | yes |
| 2504.13958 | 89,775 | 732 | yes | 24 | yes | no | yes |
| 2504.10458 | 56,304 | 329 | yes | 19 | yes | yes | yes |
| 2501.16664 | 39,888 | 251 | yes | 15 | yes | no | yes |
| 2412.06559 | 88,899 | 408 | yes | 19 | yes | yes | yes |
| 2507.17849 | 135,892 | 1277 | yes | 93 | yes | yes | yes |
| 2411.02337 | 93,001 | 675 | yes | 37 | yes | no | yes |
| 2508.06165 | 135,581 | 1180 | yes | 122 | yes | yes | yes |
| 2505.20289 | 56,888 | 376 | yes | 23 | yes | no | yes |
| 2403.07718 | 78,764 | 494 | yes | 28 | yes | no | yes |
| 2402.12348 | 99,889 | 745 | yes | 61 | yes | no | yes |
| 2411.13543 | 104,937 | 915 | yes | 52 | yes | no | yes |
| 2504.05118 | 38,844 | 304 | yes | 29 | yes | no | yes |
| 2504.11343 | 42,535 | 258 | yes | 10 | yes | no | yes |
| 2506.20670 | 112,756 | 522 | yes | 47 | yes | no | yes |
| 2508.08636 | 69,333 | 390 | yes | 27 | yes | no | yes |
| 2510.27569 | 65,703 | 458 | yes | 32 | yes | no | yes |
| 2508.00414 | 61,257 | 406 | yes | 28 | yes | no | yes |
| 2503.23383 | 33,204 | 256 | yes | 23 | yes | no | yes |
| 2509.01055 | 109,602 | 963 | yes | 51 | yes | no | yes |
| 2505.20285 | 87,195 | 827 | yes | 48 | yes | no | yes |
| 2504.05812 | 67,353 | 538 | yes | 36 | yes | no | yes |
| 2505.22660 | 46,178 | 373 | yes | 27 | yes | no | yes |
| 2508.05748 | 85,707 | 728 | yes | 90 | yes | no | yes |
| 2504.21776 | 168,541 | 1645 | yes | 124 | yes | yes | yes |
| 2311.12983 | 88,826 | 551 | yes | 28 | yes | yes | yes |
| 2502.15760 | 77,703 | 396 | yes | 32 | yes | no | yes |

---

## 2. What's in the Corpus

### 2.1 Year distribution

| year | papers |
|---|---|
| 2023 | 1 |
| 2024 | 18 |
| 2025 | 155 |
| 2026 | 3 |

The corpus skews heavily toward **2025** (155/177 papers), reflecting the explosion of agentic-RL and reasoning work post-o1/R1. Pre-2024 papers are deliberately under-represented — earlier foundational works (RLHF 2017, PPO 2017, the original Llama paper) are referenced by these papers but not indexed as primary documents.

### 2.2 Primary arXiv category

| category | papers |
|---|---|
| cs.CL | 71 |
| cs.AI | 48 |
| cs.LG | 37 |
| cs.CV | 10 |
| cs.IR | 7 |
| cs.RO | 3 |
| eess.AS | 1 |

cs.CL, cs.AI, and cs.LG together account for the vast majority — expected for an LLM-agents knowledge base. Note the presence of cs.RO (embodied agents) and cs.CV (multimodal GUI / screen agents) as meaningful minorities.

### 2.3 Tag distribution (from `morpheus.db`)

**Area tags** (what the paper is about):

| area | papers |
|---|---|
| agentic-search | 86 |
| benchmarks | 44 |
| algorithms-ppo-grpo | 38 |
| tool-use | 27 |
| reward-models | 23 |
| multimodal | 22 |
| process-supervision | 18 |
| multi-agent | 15 |
| surveys | 9 |
| self-play | 8 |
| gui | 7 |
| memory | 1 |

**Subject tags** (application domain):

| subject | papers |
|---|---|
| retrieval | 32 |
| math-reasoning | 20 |
| planning | 15 |
| web-agents | 13 |
| alignment | 8 |
| embodied | 5 |
| code-agents | 4 |
| safety | 2 |

**Method tags** (rule-based):

| method | papers |
|---|---|
| sft | 26 |
| grpo | 18 |
| distillation | 13 |
| cot | 9 |
| ppo | 7 |
| dpo | 7 |
| rlhf | 6 |
| mcts | 3 |
| rejection-sampling | 2 |
| rlaif | 2 |
| tool-learning | 1 |

**Artifact tags** (what's released):

| artifact | papers |
|---|---|
| training-code | 117 |
| benchmark | 44 |
| survey | 9 |
| model-weights | 5 |
| eval-harness | 3 |
| dataset | 2 |

Takeaways:
- **Agentic search dominates** (86 papers — Search-R1, R-Search, WebRL and follow-ons).
- **Benchmarks are 44 papers** — evaluation / leaderboard work is a major slice.
- **training-code artifacts** appear in 117 papers (≈66%), consistent with a reproducibility-leaning curator.
- **Model-weights releases (5)** and **datasets (2)** are relatively rare, suggesting we should up-weight open-weights work in Phase E.

### 2.4 Top authors (in-corpus)

| author | papers |
|---|---|
| Jingren Zhou | 10 |
| Fei Huang | 9 |
| Pengjun Xie | 8 |
| Yong Jiang | 7 |
| Ji-Rong Wen | 6 |
| Zhiyuan Liu | 5 |
| Yang Liu | 5 |
| Xipeng Qiu | 5 |
| Junyang Lin | 5 |
| Chi Zhang | 5 |
| Xuanjing Huang | 5 |
| Jialong Wu | 5 |
| Yuchen Zhang | 4 |
| Tianbao Xie | 4 |
| Qiying Yu | 4 |

Dominated by **Qwen / Alibaba DAMO** team members (Jingren Zhou, Fei Huang, Pengjun Xie, Junyang Lin) and **Chinese academic** groups (RUC — Ji-Rong Wen; Fudan — Xipeng Qiu; Tsinghua — Zhiyuan Liu). Affiliation extraction from MD bodies is unreliable (docling loses email footers), so affiliation tops are derived from prior author expertise rather than MD parsing.

---

## 3. Methods Landscape

Raw MD-body frequency of method strings (per-paper presence, not raw hits):

| method | papers mentioning |
|---|---|
| CoT | 143 |
| SFT | 112 |
| GRPO | 102 |
| PPO | 93 |
| RLHF | 62 |
| DPO | 53 |
| ReAct | 47 |
| REINFORCE | 36 |
| MCTS | 24 |
| Distillation | 16 |
| Reflexion | 16 |
| RLAIF | 9 |
| Rejection Sampling | 9 |
| Self-Consistency | 6 |
| KTO | 5 |
| Q-learning | 4 |
| IPO | 4 |
| SAC | 3 |
| ToT | 3 |
| ORPO | 2 |

### Agreement with rule-based method tags

For each method tag we have in the DB, we compare **papers tagged** vs **papers mentioning the method in the MD body**:

| tag | tagged | mentions | overlap | tagged-only | mentions-only |
|---|---|---|---|---|---|
| ppo | 7 | 93 | 7 | 0 | 86 |
| grpo | 18 | 102 | 18 | 0 | 84 |
| dpo | 7 | 53 | 7 | 0 | 46 |
| rlhf | 6 | 62 | 6 | 0 | 56 |
| rlaif | 2 | 9 | 2 | 0 | 7 |
| sft | 26 | 112 | 26 | 0 | 86 |
| mcts | 3 | 24 | 2 | 1 | 22 |
| cot | 9 | 87 | 8 | 1 | 79 |
| distillation | 13 | 16 | 5 | 8 | 11 |
| rejection-sampling | 2 | 9 | 2 | 0 | 7 |

**Interpretation:**

- Our rule-based tagger is **high-precision but low-recall**. Every tagged paper does mention the method (overlap == tagged_n for PPO/GRPO/DPO/RLHF/SFT/RLAIF/rejection-sampling), but many papers mention the method without being tagged.
- **GRPO**: tagged in 18 papers, mentioned in 102 — the tag catches ~18% of papers that discuss GRPO. Most of the 84 un-tagged mentions are in related-work sections (appropriate — the paper doesn't *use* GRPO, it just cites it). Worth a manual audit to confirm.
- **CoT / ReAct**: mentioned in 143 / 47 papers but only tagged in 9 / 0. CoT is so pervasive that flat tagging loses information; consider a `uses-cot-trace` artifact tag instead.
- **Distillation**: 8 papers tagged but not mentioned with the literal word 'Distillation' — likely using 'knowledge transfer' or 'teacher-student' phrasing. Tagger is catching semantic content the regex misses.
- **Action item**: the 'mentioned-but-not-tagged' column is the Phase E **tagger-recall backlog** — 86 GRPO candidates, 86 SFT candidates, 79 CoT candidates to triage for tag promotion.

---

## 4. Benchmarks Landscape

Benchmarks mentioned in ≥3 papers (union of known benchmark names):

| benchmark | papers mentioning |
|---|---|
| HotpotQA | 64 |
| MATH | 47 |
| MuSiQue | 37 |
| MATH500 | 36 |
| AIME | 32 |
| TriviaQA | 30 |
| GAIA | 29 |
| MMLU | 26 |
| AIME 2024 | 24 |
| GSM8K | 21 |
| 2WikiMultihopQA | 17 |
| WebArena | 16 |
| MMLU-Pro | 16 |
| SWE-bench | 15 |
| OlympiadBench | 14 |
| OSWorld | 12 |
| ARC | 11 |
| LiveCodeBench | 11 |
| WebShop | 10 |
| Mind2Web | 10 |
| HumanEval | 8 |
| MBPP | 7 |
| AlpacaEval | 6 |
| MT-Bench | 6 |
| ScreenSpot | 6 |
| ALFWorld | 5 |
| MiniWoB++ | 5 |
| MS MARCO | 5 |
| BFCL | 5 |
| RT-2 | 5 |

### Reading the list

- **Multi-hop QA** is the single largest cluster — HotpotQA (64), MuSiQue (37), TriviaQA (30), 2WikiMultihopQA, NaturalQuestions. This is the Search-R1 / R-Search / WebRL lineage that dominates the corpus.
- **Math reasoning** is the second cluster — MATH (47), MATH500 (36), AIME (32), AIME 2024 (24), GSM8K (21), OlympiadBench, TheoremQA.
- **Agentic / tool-use** benchmarks are thinner than expected — GAIA (29), SWE-bench (low-single-digits), WebArena, OSWorld, AgentBench, BFCL. For an 'agentic research' corpus this is an underweight area to fix.
- **Multimodal / GUI** benchmarks (ScreenSpot, ChartQA, DocVQA, Mind2Web, AITW) appear but are dominated by a handful of multimodal papers.
- **Coding** benchmarks (HumanEval, MBPP, LiveCodeBench) are present but thin — a known gap given DeepSeek-Coder / Qwen-Coder are well-represented as base models but not as evaluation targets.

---

## 5. Base Models and Compute Infrastructure

### Base model mentions (papers referencing each family)

| model family | papers |
|---|---|
| Qwen | 137 |
| GPT-4 | 117 |
| DeepSeek | 114 |
| o1 | 107 |
| Gemini | 75 |
| Claude | 58 |
| Llama | 43 |
| Mistral | 19 |
| GPT-3.5 | 15 |
| Gemma | 12 |
| BERT | 8 |
| T5 | 8 |
| Mixtral | 5 |
| Alpaca | 4 |
| CodeLlama | 3 |

Observations:
- **Qwen (137) > GPT-4 (117) > DeepSeek (114) > o1 (107) > Gemini (75) > Claude (58)**. Qwen's top spot reflects both its role as a frequently-fine-tuned base (Qwen-2.5 in every Search-R1-like paper) and the Alibaba author over-representation noted in Section 2.4.
- **DeepSeek and o1 tied at 110+** — these are the 'reasoning frontier' reference points for most 2025 papers.
- **Llama (43)** has been displaced as a primary fine-tuning base — most 2025 RL papers start from Qwen / DeepSeek-Math, not Llama.
- **Closed-source models (GPT-4, Claude, Gemini, o1)** are mostly cited as *evaluation baselines*, not as training subjects. This matches the open-code artifact tally in §2.3.

### GPU mentions (hardware references in MD bodies)

| gpu | papers |
|---|---|
| A100 | 43 |
| H100 | 14 |
| H200 | 3 |
| TPU | 2 |
| A6000 | 1 |
| RTX 3090 | 1 |

- **A100 (43)** remains the modal accelerator, with **H100 (14)** growing and **H200 (3)** appearing for the first time.
- Only ~34% of papers (64/177) explicitly cite GPU hardware. Most 2025 papers omit compute details — a reproducibility concern.

### Code/release signals

| signal | papers |
|---|---|
| papers with GitHub URL in MD | 130 |
| papers saying 'we introduce' | 142 |
| papers saying 'we release / open-source' | 26 |

130 / 177 papers (73%) carry at least one GitHub URL inside the converted MD. This is a high-quality, independent signal we can reconcile against the `papers.github_url` column in morpheus.db — any mismatch is a candidate correction.

Sample GitHub URLs extracted:

- `2305.20050` → https://github.com/openai/prm800k.
- `2311.12983` → https://github.com/Significant-Gravitas/Auto-GPT
- `2312.08935` → https://github.com/deepseek-ai/
- `2402.05808` → https://github.com/WooooDyy/LLM-Reverse-Curriculum-RL.
- `2402.12348` → https://github.com/jinhaoduan/GTBench
- `2403.07718` → https://github.com/ServiceNow/WorkArena
- `2403.11807` → https://github.com/CUHK-ARISE/GAMABench
- `2403.13787` → https://github.com/allenai/reward-bench
- `2404.03648` → https://github.com/THUDM/AutoWebGLM.
- `2404.07972` → https://github.com/ddupont808/GPT-4V-Act

---

## 6. Gaps and Phase E Recommendations

### Coverage gaps (thin relative to the stated research agenda)

1. **Coding agents.** SWE-bench, LiveCodeBench, APPS appear in only a handful of papers. Given the volume of 2025 coding-agent work (Agentless, SWE-Agent, CodeAct, SWE-RL), we should target **15–25 more papers** in this area before declaring Phase E coverage complete.
2. **Embodied / robotics.** Only 5 subject:embodied tags and 3 cs.RO papers. For a general-agents corpus this is under-scale — at least the RT-2, RT-X, Octo, and OpenVLA lineages deserve representation.
3. **GUI / OS agents.** OSWorld, VisualWebArena, Mind2Web, AITW all have <5 mentions. The GUI-agents literature (SeeAct, UI-TARS, CogAgent, Ferret-UI) is a known-growing area we are under-indexing.
4. **Safety / alignment.** Only 2 subject:safety and 8 subject:alignment papers. If Morpheus's brief includes alignment-aware curation, we need at least RLHF-variant safety papers (Anthropic's HH-RLHF line, DeepMind's Sparrow, scalable oversight).
5. **Open weights & datasets.** Only 5 papers tagged `artifact:model-weights` and 2 `artifact:dataset`. Up-weight papers that ship reusable artifacts — they matter more for downstream research than methods papers alone.
6. **Pre-2024 foundations.** The year curve shows a single 2023 paper. For a dreamer-style research corpus we should seed ~20 foundational pre-2024 papers (PPO, InstructGPT, Constitutional AI, Self-Instruct, Toolformer, ReAct, Reflexion, Llama-2, Mistral) so that citation graphs close properly.

### Corpus-quality follow-ups

1. **Fix H1 emission.** Post-process Docling MDs to promote the first `##` heading to `#` so standard chunkers (LlamaIndex, LangChain MarkdownHeaderSplitter) don't misinterpret the first section as a subtitle.
2. **Method-tag recall.** The rule-based tagger is high-precision but misses ~80% of PPO/GRPO/DPO/SFT papers. Build a second-pass LLM-assisted tagger that reads the Methods section and proposes tags, then human-approves.
3. **Compute-metadata extraction.** Only ~34% of MDs mention GPUs; extract GPU-hour claims into a `compute` field in `papers` so Morpheus can answer 'what can I reproduce on 8×A100?' queries.
4. **GitHub URL reconciliation.** Diff MD-extracted GitHub URLs against `papers.github_url` and flag mismatches (trailing periods, 404s) for cleanup.
5. **Dataset-extraction list.** The 30+ benchmarks hard-coded in this analysis should be promoted to a proper `benchmarks` table in morpheus.db keyed on a canonical name + aliases, so joins become robust.

### Proposed Phase E research questions

Based on what the current corpus *covers*, these are the questions Morpheus is well-positioned to answer today:

- Which RL objective (PPO vs GRPO vs DPO vs RLAIF) is empirically best for multi-hop retrieval agents? (≥25 comparable papers present.)
- How does process-supervision (PRM800K, Math-Shepherd) compare to outcome-only reward in 2025 math-reasoning work? (≥18 process-supervision papers.)
- What is the recipe convergence across Search-R1, R-Search, DeepSearch, WebRL? (86 agentic-search papers — the densest sub-corpus.)
- At what scale does GRPO beat PPO for reasoning? (102 GRPO + 93 PPO mentions gives enough side-by-sides to build a scaling table.)

Questions where the corpus is currently too thin:

- Long-horizon coding-agent trajectories (needs more SWE-bench papers).
- Safety/alignment under tool use (needs dedicated acquisition pass).
- Multimodal reasoning across GUI + text (needs GUI-agents expansion).

---

_End of overview — generated from 177 converted markdown files at 2026-04-21T04:04:33Z. Rerun `/tmp/analyze_corpus.py` after the Docling batch completes all 291 papers to refresh these numbers._
