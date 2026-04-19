# SUMMARY — tongjingqi/Awesome-Agent-RL

**Source:** https://github.com/tongjingqi/Awesome-Agent-RL

**Actual Title:** Awesome-Agent-Reward-Construction

## Scope

Curated list focused specifically on **reward construction for AI agents**. Covers designing and collecting reward signals that guide agents toward desired behaviors. The repo frames itself around two ideas: *The Second Half* (Shunyu Yao) and *Era of Experience* (Silver/Sutton, DeepMind).

## Totals

- Papers: **78**
- Categories (leaf): **19**
- Date range (YYMM): **2305 – 2508**

## Top-level Taxonomy (5 areas)

1. **Synthesizing Verifiable Task** — build verifiable gyms (puzzles, games, multi-modal, curriculum)
2. **Real-World Task Reward Construction** — web search, GUI, VLA/embodied, world models
3. **Unsupervised Reward Construction** — proposer/solver, internal signals (entropy, confidence)
4. **Reward Model Construction** — generative RMs, RM pretraining, multi-modal RMs, process supervision
5. **Evaluation and Benchmarks** — reward-model benches, game gyms, web-search & computer-use evals

## Venues

- Arxiv: 46
- ICLR: 8
- ACL: 8
- ICML: 5
- COLM: 4
- NeurIPS: 4
- NAACL: 1
- CVPR: 1

## Themes & Notable Sub-areas

- **Verifiable task synthesis**: Code2Logic, SynLogic, Enigmata, InternBootcamp — synthetic puzzles/games to give RLVR more ground truth.
- **Web-search agents (Alibaba Tongyi WebAgent family)**: WebDancer, WebSailor, WebShaper, WebWatcher — heavy representation; Search-R1, WebRL, WebThinker, ASearcher round it out.
- **GUI/computer-use RL**: AgentCPM-GUI, ARPO, GUI-R1, OS-Genesis, AgentSynth.
- **VLA / embodied**: VLA-RL, iRe-VLA, RL4VLA, RIPT-VLA.
- **World models as reward sources**: Genie 3, Matrix-Game 2.0, GPT-simulator.
- **Self-play / zero-data RL**: Absolute Zero, R-Zero, SQLM, SPIRAL.
- **Unsupervised / internal-signal rewards**: TTRL, Intuitor, EMPO, Spurious Rewards, entropy-mechanism analyses.
- **Process reward models**: Math-Shepherd, Let's Verify Step by Step (PRM800K), DG-PRM, PRMBench, ProcessBench.
- **Generative / pretrained RMs**: SPCT, GenRM (SynthLabs + DeepMind), WorldPM, POLAR.
- **Benchmarks**: RewardBench, VL-RewardBench, tau-bench, OSWorld, WorkArena, TheAgentCompany, BrowseComp/-ZH, GAIA, BALROG, GTBench, GameArena, GameBench, ScienceBoard.

## Distinctive Coverage vs. other Awesome-Agent-RL

This repo is *not* a general agent-RL survey — it is specifically **reward-construction-centric**. Distinctive emphases likely absent (or thinner) elsewhere:

- Dedicated section on **Unsupervised Reward Construction** (entropy minimization, self-certainty, test-time RL).
- Explicit **Reward Model pretraining** sub-area (WorldPM, POLAR).
- Treatment of **World Models as future reward sources** as a first-class category.
- Framing around *The Second Half* / *Era of Experience* philosophy.
- Heavy Alibaba Tongyi WebAgent concentration (4 consecutive WebX papers).

## Extraction Issues

- Only one source file (`README.md`, 294 lines); no nested `.md`s to walk.
- Some entries use `[YYMM]` as the arXiv posting date (not full year); captured as `date_code` separately.
- A few entries have no arXiv id (e.g., Genie 3 blog post) — captured `project_url` instead.
- Duplicates across categories: **VeriFree** (2505.21493) appears twice under different sub-headings; **BrowseComp** (2504.12516) appears in both 'Web Search Evaluation' and 'Computer Use Evaluation'. Preserved as distinct rows (per-category context); cross-source dedup happens later.
- Authors field is the parenthesized *affiliations* list in the source, not person names — the README stores institutions in parens after titles. Preserved verbatim.
- Category heading 'Converting General Tasks to Verifiable Tasks' is referenced in TOC as 'Converting Open-Domain Tasks to Verifiable Tasks' — using the in-body heading.
