# ArXiv PDF Cache

Local cache of arXiv PDFs referenced across the Morpheus-the-Dreamer scraped index
(`scraped/*/papers.jsonl`).

## Naming convention

- Each file is named by its normalized arXiv ID with a `.pdf` suffix:
  - New-style: `2305.20050.pdf`
  - Old-style (archive/NNNNNNN): slash replaced with underscore, e.g. `cs.LG_0123456.pdf`
- Version suffix (`vN`) is stripped before download — this fetches the **latest**
  version from arxiv.org (`https://arxiv.org/pdf/<id>.pdf`).
- No metadata is embedded in the PDF filename or content. For author, title,
  venue, year, or cross-source provenance, look the arxiv_id up in the unified
  index under `indexes/` (or the per-source rows in `scraped/*/papers.jsonl`).

## Download convention

- User-Agent: `Morpheus-the-Dreamer research index (ArtemisAI; contact cardenalito@gmail.com)`
- Rate limit: 3 seconds between requests (arXiv courtesy limit). **Do not
  parallelize** additional downloads against this cache.
- Retry: on HTTP 429 or 5xx, one retry after 30 s; on 404 logged as `missing`.
- Resumable: re-runs skip any file that already exists with non-zero size.

## Gitignore

PDFs are **not** committed to the repo (`papers/*.pdf` and `papers/**/*.pdf`
rules in the root `.gitignore`). Only `MANIFEST.jsonl` and this README live in
git. Re-run the download script to rehydrate the cache on a fresh clone.

## Manifest

`MANIFEST.jsonl` has one row per unique arxiv_id from the unified index with fields:

- `arxiv_id` — normalized ID (no version suffix, lowercased)
- `title` — paper title from the unified index (may be null)
- `year` — publication year from the unified index (may be null)
- `status` — `downloaded` | `skipped` | `failed` | `missing`
- `bytes` — file size in bytes (present when `status == "downloaded"`)
- `source` — `pre_existing` (was already on disk) or `downloaded` (fetched this run)
- `reason` — present for non-`downloaded` rows; e.g. `suspicious_id`, `http_404`, `not_a_pdf`

Suspicious IDs (YYMM with month > 12, or year > current month at run time)
are flagged as `status: "skipped"` / `reason: "suspicious_id"` and are
candidates for manual review / correction in the scraped index.
