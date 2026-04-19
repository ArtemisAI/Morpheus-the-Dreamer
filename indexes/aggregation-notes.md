# Aggregation Notes

## Inputs

- Four scraped awesome-list sources (necolizer, 0russwest0, tongjingqi, ventr1c).
- `aitfind-morpheus-project` was skipped: single wrapper entry pointing back at 0russwest0's list, no paper payload.
- `ventr1c` publishes many duplicate rows (same paper under multiple taxonomies); dedup collapses them.

## Dedup keys

- **Primary:** normalized `arxiv_id` — stripped `arXiv:` prefix, stripped `vN` version suffix, lowercased.
- **Secondary (only when arxiv_id is missing):** normalized title (lowercase, punctuation → space, collapsed whitespace).

## Merge rules on collision

- Title: keep the longest string.
- Year: keep the earliest parsable 4-digit year (paper provenance preference).
- Venue / authors / project_url: first non-empty wins (authors: longest).
- Categories: union, preserved as `source_slug:category` so provenance stays inspectable.
- github_urls: union (list).
- sources: union (list of slugs that contributed the paper).

## Suspicious-id flag

- An arXiv id is flagged when its `YYMM` prefix has month 00 or >12, or when the implied date is after today (2026-04-19).
- Known offenders in ventr1c source: `2602.*`, `2601.06487`, etc. — these look hallucinated by whatever generated the source README. Kept in the index but flagged so humans can sanity-check.

## Bucket classification

- Heuristic keyword match against concatenation of title + `categories` list.
- A paper can land in multiple buckets. Everything unmatched falls to `Other`.
- Buckets are approximations — they are a reading aid, not a taxonomy.

## Hand decisions / edge cases

- Rows without a title AND without an arxiv_id are dropped (unusable).
- `tongjingqi` rows include a `paper_url` field distinct from `arxiv_id` — we rely on the `arxiv_id` field, which is already populated for those rows.
- Several ventr1c rows use `year: 2026` which is plausible (we're in April 2026), so 2026 by itself is NOT suspicious; only the invalid `YYMM` prefix is.
- `source:category` entries preserve the original taxonomy of each source so downstream reviewers can trace where a tag came from.

## Totals

- **332** unique papers across 4 sources.
- **43** flagged suspicious (likely hallucinated arXiv ids).
- **185** have at least one github URL; **41** have no arXiv id.

## Overlap highlight

- Largest source overlap: `necolizer` ∩ `ventr1c` = **18** papers.
