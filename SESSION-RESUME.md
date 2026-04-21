# Session Resume — Morpheus-the-Dreamer

Last session ended: 2026-04-20. Corpus state frozen at 332 papers / 291 PDFs / 587 markdowns; v0 design spec landed.

## What's done

| Phase | Status | Evidence |
|---|---|---|
| Scaffold + initial index (332 papers) | done | `d35eabc` |
| Cross-source dedup + unified index | done | `58a27b4` |
| ArXiv PDF download (291/291) | done | `a856052` |
| Prior session resume checkpoint | done | `aedcd6c` |
| Reorg `indexes/`+`scraped/` → `corpus/`; source-ref cleanup; enrichment; docling batch start | done | `3205cf6` |
| Docling conversion progress 256/291 | done | `7121843` |
| Docling conversion complete 291/291 | done | `abd0755` |
| SQLite index (`corpus/morpheus.db`) populated: 332 papers / 2,616 authors / 46 tags / 4,477 paper-tags / 3,327 paper-authors | done | `build_index_db.py` + `enrich_and_tag_db.py` + `tag_from_bodies.py` |
| Scripts consolidated under `scripts/` | done | `fetch_arxiv_metadata`, `build_index_db`, `enrich_and_tag_db`, `convert_pdfs_to_markdown`, `postprocess_markdowns`, `tag_from_bodies`, `weekly_arxiv_refresh`, `install_weekly_cron` |
| arxiv MCP server installed + `.mcp.json` at project root | done | `uvx arxiv-mcp-server`, storage rooted at `papers/arxiv/` |
| Analysis docs | done | `docs/analysis/corpus-overview.md`, `docs/analysis/morpheus-top-papers.md`, `docs/analysis/tagger-recall-fix.md` |
| Design docs | done | `docs/design/recipe-cards.md`, `docs/design/morpheus-v0-spec.md`, `docs/design/morpheus-open-questions.md` |
| Weekly refresh run (staged only) | done | 247 new papers in `corpus/staging-new.jsonl` (2026-04-01 → 04-21) |

All commits are on `main` at `github.com/ArtemisAI/Morpheus-the-Dreamer`.

## What's in flight

Nothing. Session is wrapping up clean.

## Known pending work

1. **Promote 247 staged papers.** `corpus/staging-new.jsonl` → DB rows + PDFs + markdowns. Recipe:
   ```bash
   python3 scripts/fetch_arxiv_metadata.py --input corpus/staging-new.jsonl --merge corpus/metadata-enriched.jsonl
   python3 scripts/build_index_db.py                 # rebuilds morpheus.db
   python3 scripts/enrich_and_tag_db.py
   python3 scripts/convert_pdfs_to_markdown.py       # docling, CUDA
   python3 scripts/postprocess_markdowns.py
   python3 scripts/tag_from_bodies.py
   ```
   Clear `corpus/staging-new.jsonl` after successful ingest.
2. **Install weekly cron.** The cron installed in-session was **cancelled / session-only**. To re-enable locally, review then run `scripts/install_weekly_cron.sh` and `crontab -e`.
3. **Validate v0 hypothesis.**
   - *Question 1*: run a SQL check on the `claude-mem` DB for ≥10k `(observation, outcome)` pairs (threshold for RL data sufficiency noted in `docs/design/morpheus-v0-spec.md`).
   - *Question 3*: train a logistic-regression baseline on the same pairs; compare against the binary-reward head before committing to the RL head.
4. **Reconcile with parent claude-mem.** Update `~/tools/tools-for-agents/claude-mem/docs/morpheus-rl-design.md` to reflect the **binary-reward decision** made in the v0 spec. Disagreement with the parent design is explicitly noted in `docs/design/morpheus-v0-spec.md` — the parent still needs to be amended.
5. **Identity reattribution (carry-over).** Commits on this repo are authored as `ArtemisAI`. The `claude-code-swe` bot token at `~/.config/gh/tokens/claude-code-swe.token` is still the intended identity. Decision pending: rewrite history + force-push vs. switch going forward only. See prior resume for context.

## Resume recipe (next session)

```bash
cd ~/tools/tools-for-agents/Morpheus-the-Dreamer
git status                                         # expect clean
git log --oneline -5                               # most recent: abd0755 or later
ls papers/arxiv/*.pdf | wc -l                      # 291
ls papers/markdown/ | wc -l                        # 587
wc -l corpus/unified.jsonl corpus/staging-new.jsonl
python3 -c "import sqlite3; c=sqlite3.connect('corpus/morpheus.db'); \
  print({k: c.execute(f'SELECT COUNT(*) FROM {k}').fetchone()[0] \
    for k in ['papers','authors','tags','paper_tags','paper_authors']})"
# expected: {'papers': 332, 'authors': 2616, 'tags': 46, 'paper_tags': 4477, 'paper_authors': 3327}
```

If promoting staged papers next, start at "Known pending work #1".

## Parent project links

- Parent repo: `~/tools/tools-for-agents/claude-mem`, branch `feat/morpheus`, in sync with private `ArtemisAI/pi-mem-dev/feat/morpheus`.
- Parent design doc: `docs/morpheus-rl-design.md` (needs binary-reward update — see pending #4).
- Research plan / Project Morpheus: https://github.com/ArtemisAI/pi-mem-dev/issues/28 (private).

## Memory / identity notes

- `reference_claude_code_swe_identity.md` — bot token path + `~/.bashrc` helpers `use-claude-code-swe` / `use-artemisai`.
- Bot-token reattribution for existing commits is still **pending** (see Known pending work #5).

## Known warnings

- Early commits were direct pushes to `main` on an unprotected repo. If the repo becomes collaboration-facing, enable branch protection and route work through PRs.
- PDFs (~1.0 GB) remain on `/dev/nvme0n1p6`. Google Drive migration via rclone was planned in the prior session and is still outstanding but no longer blocking — disk pressure has eased.
