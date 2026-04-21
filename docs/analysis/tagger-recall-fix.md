# Tagger Recall Fix — Body-Pass

_Run: 2026-04-20. Script: `scripts/tag_from_bodies.py`._

## 1. The recall gap

Rule-based tags in `corpus/morpheus.db` (kinds `area` / `method` / `subject` / `artifact`) were originally derived by `scripts/enrich_and_tag_db.py`, which applies regex rules to **title + abstract + primary_category only**. That pass has high precision but obvious recall gaps — the concept is often introduced only in §3 or §5 of the paper. Quick counts over `papers/markdown/*.md` bodies (measured against 238 stable conversions) showed:

| token | tagged (title+abs) | mentioned in body |
| ----- | -----------------: | ----------------: |
| GRPO  | 18                 | 102               |
| SFT   | 26                 | 112               |
| PPO   | ~same              | ~same             |
| CoT   | ~40                | 143               |

Roughly 5× under-assignment on the core RL/reasoning vocabulary. Downstream Morpheus queries that filter `method=grpo` would miss ~80 % of the relevant papers.

## 2. What the body pass added

`scripts/tag_from_bodies.py` reuses the exact rule tables from `enrich_and_tag_db.py` (imported, not duplicated), skips the first 20 lines (authors / abstract — already covered), filters files whose mtime is <10 s old or size <2 KB (docling is still writing), and inserts new `paper_tags` rows with `confidence=0.7` under a single `BEGIN IMMEDIATE` transaction. `INSERT OR IGNORE` plus an in-memory `(paper_id, kind, name)` set suppresses duplicates.

Results over 238 scanned files, 1 skipped:

| kind      | added |
| --------- | ----: |
| `area`    |   942 |
| `method`  |   899 |
| `subject` |   797 |
| `artifact`|   379 |
| **total** | **3017** |

`paper_tags` grew from **1 424 → 4 441** rows (+212 %). Top new assignments: `subject/alignment` (+171), `area/benchmarks` (+165), `method/cot` (+160), `area/algorithms-ppo-grpo` (+152), `area/reward-models` (+143), `method/sft` (+120), `method/grpo` (+116), `method/ppo` (+115). A second run added only 11 rows — those came from `.md` files docling finalized between the two invocations. Full rerun-safety confirmed.

Split by confidence post-run: **1 424 @ 1.0** (title-derived, authoritative) and **3 028 @ 0.7** (body-derived, supporting). Queries can therefore distinguish strong vs. supporting signals via `paper_tags.confidence`.

## 3. Remaining gaps

No regex-derived tag now has <5 assignments. The only sub-5 tags are arxiv-category labels (`category/cs.SE`, `eess.AS`, `cs.RO`) which reflect the actual corpus composition, not a rule miss. `method/distillation`, `subject/math-reasoning`, `subject/retrieval`, `artifact/eval-harness`, `area/tool-use` each sit at low-double-digit assignment counts — plausibly correct for a corpus skewed toward RL-for-LLM-agents. Still worth a manual spot-check on 10 random papers per low tag before trusting it in routing.

Docling conversion was at 238/291 completed at run time. When the remaining ~50 PDFs finalize, rerun `python3 scripts/tag_from_bodies.py` — it is safe and incremental.

## 4. Next pass recommendation

1. Re-run after docling finishes (expect ~600 more body-pass tags).
2. Add a **negation-aware** rule layer for methods (e.g. "unlike PPO, we ..." should not tag `ppo`). Current regex is a pure `\b...\b` match; false positives on background-only mentions are the main precision risk at `confidence=0.7`.
3. Introduce a `venue` or `year-bucket` tag kind to let Morpheus weight recent RL-agent work higher.
4. Consider sentence-embedding-based tag suggestion for long-tail tags (`self-play`, `memory`, `process-supervision`) that the regex fires on rarely but may be conceptually present.
