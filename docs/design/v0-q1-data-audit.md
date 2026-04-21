# v0 Q1 Data Audit — Do we have >=10k same-bucket (retained, dropped) pairs?

**Answer: No.** v0 cannot proceed as written. The binary preference signal (retained vs. dropped) is not persisted — claude-mem logs which observations were retained but never logs which observations were *candidates* that lost. Pair count today: **0**.

---

## What exists today

Source of truth: `~/.claude-mem/claude-mem.db` (prod) and `~/.claude-mem-dev/claude-mem.db` (dev).
Code owner of the signal: `src/services/feedback/FeedbackRecorder.ts` + call sites in `ObservationCompiler.ts`, `ObservationPipeline.ts`, `consolidation-service.ts`, `prune-superseded.ts`.

| DB         | observations | observation_feedback present? | rows | signal breakdown                 |
| ---------- | ------------ | ----------------------------- | ---- | -------------------------------- |
| prod       | 1,221        | **No** (migration 24 not run) | n/a  | n/a                              |
| dev        | 1,221        | Yes                           | 50   | `retained_in_context` x50, rest 0 |

Schema that does exist (migration 24, runner.ts:891):
```sql
CREATE TABLE observation_feedback (
  id INTEGER PK, observation_id INTEGER, signal_type TEXT,
  session_db_id INTEGER, created_at_epoch INTEGER, metadata TEXT
);
```
`FeedbackSignalType` union defines six values: `retrieved`, `retained_in_context`, `tool_adjacent`, `merged_into`, `superseded`, `consolidated_into`.

## What is missing

1. **`retrieved` is defined but never emitted.** Grepping `src/services` finds zero call sites that record `signal_type='retrieved'`. This is the *candidate-set* signal — without it there is no way to recover "these N observations competed for the same slot; K were kept, N-K were dropped".
2. **No bucket_key persisted.** The v0 spec and `morpheus-rl-design.md` §4 define a bucket as `"{type}|{concept}|{file_prefix}"`. It is a derivable view over `observations`, but the *retrieval event* that groups candidates (the query, session, or prompt_number that produced them together) is not stored.
3. **Negative signals are empty.** Even in the dev DB with feedback wired, there are zero `superseded`, `merged_into`, or `consolidated_into` rows — those recorders exist in code but no pruning/consolidation job has run against a corpus with dupes/contradictions in this environment.
4. **Prod DB is behind schema.** `schema_versions` lists 24 as applied but the table is absent (noted in runner.ts as a known cross-machine sync hazard; the migration self-heals on next boot).

Net: the claim in `morpheus-rl-design.md` §4 that "a scan of the current brain DB estimates ~8,000 distinct buckets across 1.2M observations" does not match this machine's corpus (1.2k obs, not 1.2M) and in any case buckets alone are not pairs — pairs need contention-set membership that is not recorded.

## Pair count by bucket
0 same-bucket (retained, dropped) pairs in either DB. Cannot clear 10k; we are 4 orders of magnitude short.

## Integration point in claude-mem (where `retrieved` must fire)

`src/services/context/ObservationCompiler.ts` — the compiler already iterates a ranked candidate list and picks a top-K to inject. It currently calls `recorder.recordBatch` only for the **kept** items (lines ~96-108 and ~204+ for the multi-project path). The same function has the full candidate list in scope one step earlier (the SQL query result before slicing to the injection budget). A single added loop there — log `retrieved` for every candidate, with a shared `retrieval_event_id` — would reconstitute the dropped-vs-kept contrast.

## Minimal schema proposal (required preceding PR)

```sql
-- New table: one row per candidate seen during a single compile call.
CREATE TABLE observation_retrieval_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  retrieval_event_id TEXT NOT NULL,        -- uuid per compile call
  session_db_id INTEGER NOT NULL,
  project TEXT NOT NULL,
  query_prompt_number INTEGER,
  observation_id INTEGER NOT NULL,
  rank INTEGER NOT NULL,                    -- pre-truncation rank
  relevance_score REAL,
  was_retained INTEGER NOT NULL,            -- 0 = dropped at truncation, 1 = injected
  bucket_key TEXT NOT NULL,                 -- type|concept|file_prefix, computed at write
  created_at_epoch INTEGER NOT NULL,
  FOREIGN KEY (observation_id) REFERENCES observations(id) ON DELETE CASCADE
);
CREATE INDEX idx_orc_event ON observation_retrieval_candidates(retrieval_event_id);
CREATE INDEX idx_orc_bucket ON observation_retrieval_candidates(bucket_key, was_retained);
-- Pairs query:
-- SELECT a.observation_id AS pos, b.observation_id AS neg
-- FROM observation_retrieval_candidates a
-- JOIN observation_retrieval_candidates b
--   ON a.retrieval_event_id = b.retrieval_event_id
--  AND a.bucket_key        = b.bucket_key
-- WHERE a.was_retained = 1 AND b.was_retained = 0;
```

Emit site: `ObservationCompiler.compile()` just before the top-K slice. One `INSERT` per candidate, wrapped in the existing transaction. Back-of-envelope: ~20 candidates per compile x ~50 compiles/day per active user = 1k rows/day/user. To hit 10k *pairs* we need ~30 active-user-days after instrumentation lands (pairs grow ~N*(K)*(N-K) per event; at N=20,K=5 that is ~75 pairs/event).

## Recommendation

**v0 needs a preceding instrumentation PR to claude-mem before the DPO training loop can be built.** Two-week timeline is viable only if the PR lands in week 1:

- Week 1: ship `observation_retrieval_candidates` table + emit site in `ObservationCompiler`, backfill `bucket_key` computation, enable on 1-3 heavy-usage dogfood brains. Target: 10k pairs in 5-7 days of real usage.
- Week 2: run v0 DPO training on whatever has accumulated; if <10k pairs, fall back to cross-bucket pairs (Q1's stated pivot) or synthetic augmentation.

Do not start v0 model work until the emit site is merged and writing rows. Everything else downstream is blocked on this one signal.
