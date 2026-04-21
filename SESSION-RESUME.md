# Session Resume — Morpheus-the-Dreamer

Last session ended: 2026-04-19 (reboot pending disk/GDrive setup).

## What's done

| Phase | Status | Evidence |
|---|---|---|
| Scaffold + README + .gitignore | ✅ | commit `d35eabc` |
| Scrape 5 sources → structured metadata | ✅ | `corpus/sources/*/papers.jsonl` + `papers.md` + `categories.md` |
| Cross-source dedup + unified index | ✅ | commit `58a27b4` — `indexes/unified.jsonl` (332 unique papers), `by-arxiv-id.md`, `by-year.md`, `by-source-coverage.md`, `by-method.md`, `STATS.md`, `aggregation-notes.md` |
| ArXiv PDF download (291/291) | ✅ | commit `a856052` — `papers/arxiv/MANIFEST.jsonl` tracked; PDFs gitignored (local-only, ~1.0 GB) |

All commits on `main`, pushed to `origin` (https://github.com/ArtemisAI/Morpheus-the-Dreamer).

## Corpus at a glance

- **332 unique papers** across 4 substantive sources (+1 redundant wrapper).
- Bucket distribution (papers land in multiple): Agentic Search 238, Benchmarks & Evaluation 130, Algorithms/PPO-GRPO 114, Tool Use 44, Multimodal 39, GUI 21, Reward Models 21, Process Supervision 20, Memory 11, Self-Play 10, Surveys 13.
- 185 have github_url, 41 have no arxiv_id (code-only / blog posts).
- 43 flagged `suspicious: true` (implausible YYMM — placeholder arXiv IDs, kept but marked).
- Year span: 2023 – 2026, 2025 dominant (193 papers).
- PDFs: 291 `.pdf` files in `papers/arxiv/` locally (1.0 GB). Not committed — gitignored. Manifest tracks file-by-file status.

## What's NOT done / blocked on reboot + GDrive setup

1. **Storage migration.** Root partition was at 100% during download (recovered to ~6.8 GB free after auto-cleanup). PDFs need to move off `/dev/nvme0n1p6` before the corpus grows. User intends to set up Google Drive via rclone post-reboot; PDFs will migrate there.
2. **Identity reattribution.** Three commits on this repo (`d35eabc`, `58a27b4`, `a856052`) are authored as `ArtemisAI`. The user has since provided a `claude-code-swe` GitHub PAT (stored at `~/.config/gh/tokens/claude-code-swe.token`) and wants bot-like commits under that identity. Decision pending: **rewrite history + force-push** (safe — repo is public but new, no external clones known) **vs. switch identity going forward only**.
3. **Research synthesis.** `docs/` is empty. Next step is thematic survey docs pulling from `indexes/unified.jsonl` and the PDFs, targeted at Project Morpheus Phase E needs (reward function design, bucketing granularity, policy update math, serving blend). Tracked in `ArtemisAI/pi-mem-dev` issue #28.
4. **No full-text indexing yet.** PDFs sit on disk but aren't extracted / chunked / embedded. Decisions pending: text extraction tool (pdfplumber / pymupdf / grobid), whether to push text to `claude-mem` Chroma or a separate corpus, whether to generate BibTeX.

## Resume recipe (after reboot + GDrive mounted)

1. **Verify corpus state.**
   ```bash
   cd ~/tools/tools-for-agents/Morpheus-the-Dreamer
   ls papers/arxiv/*.pdf | wc -l          # should be 291
   git status                              # should be clean
   git log --oneline -5                    # last commit: a856052 (or a reattributed SHA)
   wc -l indexes/unified.jsonl             # 332
   ```
2. **Migrate PDFs to Google Drive.** Example once rclone is configured (remote name `gdrive`):
   ```bash
   rclone copy papers/arxiv/ gdrive:Morpheus-the-Dreamer/papers/arxiv/ --progress
   # then either:
   # (a) delete local PDFs and symlink from rclone mount; or
   # (b) keep local and push gdrive copy as canonical
   ```
   Update `papers/arxiv/README.md` to point at the gdrive location.
3. **Decide identity policy.** Either:
   ```bash
   # Option A: rewrite history under claude-code-swe
   git filter-repo --commit-callback '…'   # or git rebase -i + exec
   git push --force-with-lease origin main
   # Option B: switch only for future commits
   source ~/.bashrc && use-claude-code-swe
   ```
4. **Kick off synthesis docs** per `ArtemisAI/pi-mem-dev` issue #28 research plan.

## Parent project link

- Parent: `~/tools/tools-for-agents/claude-mem`, branch `feat/morpheus`, in sync with `pi-mem-dev/feat/morpheus` (0 ahead, 0 behind).
- Design doc: `docs/morpheus-rl-design.md` at commit `e80beebf`.
- Research plan: https://github.com/ArtemisAI/pi-mem-dev/issues/28 (private).

## Memory notes added this session

- `reference_claude_code_swe_identity.md` — where the bot token lives, activation helpers in `~/.bashrc` (`use-claude-code-swe`, `use-artemisai`).

## Known warnings

- Sub-agents emitted SECURITY WARNINGs for direct pushes to `main` on an unprotected empty repo. Acceptable for this initialisation pass. If repo becomes collaboration-facing, enable branch protection on `main` and route future work through PRs.
