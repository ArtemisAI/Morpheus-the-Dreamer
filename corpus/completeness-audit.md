# Corpus Completeness Audit

Date: 2026-04-20
Scope: Verifies every PDF-eligible paper from the 4 source scrapes landed in
`papers/arxiv/MANIFEST.jsonl`, and confirms the unified index is in sync.

## Methodology

For each `corpus/sources/<source>/papers.jsonl`, an arxiv ID was extracted per record
using:

1. The `arxiv_id` field (normalized to `YYMM.NNNNN`).
2. Fallback regex `arxiv\.org/(abs|pdf)/(\d{4}\.\d{4,5})` against
   `paper_url`, `github_url`, `project_url`, and `raw_line`.

Records without an extractable arxiv ID (code repos, blogs, awesome-list index
entries) were excluded per the note in the task brief. The union of extracted
IDs across all sources was then compared to:

- `papers/arxiv/MANIFEST.jsonl` (291 records, all `status: downloaded`)
- `corpus/unified.jsonl` (332 records; 291 with an `arxiv_id`)

## Headline Numbers

| Metric                               | Count |
|--------------------------------------|------:|
| Source union (unique arxiv IDs)      |   291 |
| Manifest arxiv IDs                   |   291 |
| Unified records with arxiv_id        |   291 |
| In sources but NOT in manifest       | **0** |
| In manifest but NOT in sources       | **0** |
| Unified IDs not in manifest          | **0** |
| Manifest entries tagged `pre_existing` |  93 |

Result: full round-trip integrity. Every source-contributed arxiv ID was
preserved through dedup/merge into the unified index AND downloaded into the
manifest. No silent drops.

## Per-Source Table

| Source                                  | JSONL lines | Unique arxiv IDs | Landed in manifest | Missing |
|-----------------------------------------|------------:|-----------------:|-------------------:|--------:|
| 0russwest0-awesome-agent-rl             |          20 |               17 |                 17 |       0 |
| aitfind-morpheus-project                |           1 |                0 |                  0 |       0 |
| necolizer-awesome-rl-for-agents         |         108 |               72 |                 72 |       0 |
| tongjingqi-awesome-agent-rl             |          78 |               74 |                 74 |       0 |
| ventr1c-awesome-rl-agentic-search       |         332 |              166 |                166 |       0 |
| **Union (dedup across sources)**        |           — |          **291** |            **291** |   **0** |

Notes:
- `aitfind-morpheus-project` contributes a single awesome-list landing-page
  record with no arxiv ID — expected, not a drop.
- `0russwest0`: 20 JSONL lines, 3 have no arxiv ID (code-only entries). 17 IDs,
  all landed.
- `necolizer`: 108 lines, 72 unique arxiv IDs (remainder are code repos,
  duplicate listings, or section headers with URL-only refs).
- `tongjingqi`: 78 lines, 74 unique arxiv IDs.
- `ventr1c`: 332 lines, 166 unique arxiv IDs (heavy intra-source duplication
  across survey categories).

## Drops to Investigate

None. `IN_SOURCES_NOT_IN_MANIFEST` is empty.

## Unexpected Manifest Entries

None. `IN_MANIFEST_NOT_IN_SOURCES` is empty. (93 manifest rows are tagged
`source: "pre_existing"`, meaning they were PDFs present on disk before the
arxiv download pass; all 93 are ALSO present in the union of source scrapes,
so nothing is orphaned.)

## Unified Index Cross-Check

Every one of the 291 `arxiv_id`-bearing rows in `corpus/unified.jsonl` is
present in `papers/arxiv/MANIFEST.jsonl`. Confirmed: 0 drift.

The remaining 41 unified rows (332 − 291) are code-repo / blog / awesome-list
entries with `arxiv_id: null`, legitimately excluded from PDF download per the
task brief.

## Conclusion

Corpus is complete. Dedup/merge preserved every source-contributed arxiv ID,
manifest fully covers the unified index, and no pre-existing PDFs are
orphaned from the source scrapes.
