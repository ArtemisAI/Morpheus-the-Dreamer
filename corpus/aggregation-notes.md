# Aggregation Notes

## Dedup keys

- **Primary:** normalized `arxiv_id` — stripped `arXiv:` prefix, stripped `vN` version suffix, lowercased.
- **Secondary (only when arxiv_id is missing):** normalized title (lowercase, punctuation → space, collapsed whitespace).

## Merge rules on collision

- Title: keep the longest string.
- Year: keep the earliest parsable 4-digit year (paper provenance preference).
- Venue / authors / project_url: first non-empty wins (authors: longest).
- Categories: union.
- github_urls: union (list).

## Suspicious-id flag

- An arXiv id is flagged when its `YYMM` prefix has month 00 or >12, or when the implied date is in the future.
- Flagged rows are kept in the index but marked so humans can sanity-check.

## Bucket classification

- Heuristic keyword match against concatenation of title + `categories` list.
- A paper can land in multiple buckets. Everything unmatched falls to `Other`.
- Buckets are approximations — they are a reading aid, not a taxonomy.

## Hand decisions / edge cases

- Rows without a title AND without an arxiv_id are dropped (unusable).
- 2026-dated arXiv IDs are plausible (we're in April 2026); only invalid `YYMM` prefixes are suspicious.

## Totals

- **332** unique papers.
- **43** flagged suspicious (likely hallucinated arXiv ids).
- **185** have at least one github URL; **41** have no arXiv id.
