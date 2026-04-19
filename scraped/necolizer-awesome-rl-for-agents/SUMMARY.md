# SUMMARY — Necolizer/awesome-rl-for-agents

**Source:** https://github.com/Necolizer/awesome-rl-for-agents
**Single file:** README.md (no sub-files)
**Total entries extracted:** 108
**Entries with arXiv IDs:** 72
**Entries with GitHub repos:** 82
**Year range (parsed from venue tags):** 2024–2026

## Scope
A curated, personal list of RL for LLM/MLLM agent work. Emphasis on research-driven,
computer-using, and tool-integrated agent behaviors. Includes non-paper items
(benchmarks, demos/projects, toolkits, blogs, related awesome-lists).

## Dominant themes
- RL for deep research / search agents (largest bucket)
- RL for computer-using / GUI agents (UI-TARS-2, OpenCUA, InfiGUI-R1, etc.)
- RL for tool-using problem solvers (ToolRL, ReTool, TORL, VerlTool)
- RL scaling for LLM reasoning (DAPO, DeepSeek-R1, Kimi k1.5, VAPO, LIMR)
- Self-playing agents (Agent0, Search Self-play)
- Multi-modal thinking-with-images (DeepEyes, MMSearch-R1)
- Agent memory RL (MemAgent, MEM1)
- Benchmarks for browsing/computer-use/deep research
- Toolkits (verl, rLLM, slime, ROLL) and RL-based agent tuning demos (RAGEN, SkyRL, Agent-R1)

## Distinctive vs generic RL-for-agents coverage
- Heavy curator bias toward Chinese-lab + Bytedance/Alibaba/Tencent work and 2025 preprints
- Includes forward-dated 2026 ICLR/Preprint entries (ArenaRL, OmniGAIA, etc.) — curator
  treats announced/arxiv-2601.* IDs as valid. Some arxiv IDs in "'26" entries look malformed
  (e.g. 2602.xxxxx) — likely placeholder / pre-assignment IDs and should be verified.
- Unlike generic RL-for-agents lists this one focuses narrowly on RL *training* pipelines
  (not prompting, planning, or architecture-only agent papers).
- Includes non-paper artifacts (blogs, platforms, toolkits), which inflates counts beyond
  pure paper lists.

## Extraction issues
- Source has no authors listed anywhere — `authors` is null for every entry.
- "'26" arxiv IDs (2601.xxxxx / 2602.xxxxx) are suspicious: these IDs don't exist yet
  at time of extraction. Captured as-is; downstream pass should validate.
- A few entries are toolkits / demos with no paper (e.g. Seed-1.8, mcp-agent, OpenManus-RL) —
  they still appear in JSONL with arxiv_id=null.
- "Marco Search Agent" entry lists TWO arxiv preprints; our extractor keeps the first one.
