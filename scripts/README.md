# scripts/

Pipelines for building and enriching the Morpheus corpus. All scripts are
idempotent and read/write paths relative to the repo root.

## Scripts

- **`build_index_db.py`** — Reads `corpus/unified.jsonl` + `papers/arxiv/MANIFEST.jsonl`
  and writes `corpus/morpheus.db` (the SQLite index used by sibling agents).
  Idempotent; pass `--rebuild` to drop and recreate.
- **`fetch_arxiv_metadata.py`** — Fetches canonical arXiv metadata for every
  `arxiv_id` in `corpus/unified.jsonl`. Writes `corpus/metadata-enriched.jsonl`
  and `corpus/authors.jsonl`. Rate-limited; reproducible.
- **`enrich_and_tag_db.py`** — Reads the enriched metadata + authors JSONL and
  populates `corpus/morpheus.db` with abstracts, primary_category, authors,
  and rule-based tags (kind in {category, area, method, subject, artifact}).
  Idempotent — safe to rerun.
- **`convert_pdfs_to_markdown.py`** — Converts the PDFs under `papers/arxiv/`
  into clean Markdown under `papers/markdown/` via docling.

## Runbooks

- **`refresh_arxiv.md`** — How to pull new arXiv papers matching the Morpheus
  topic filter and ingest them into the corpus.
- **`pdf_to_markdown_plan.md`** — Plan for the docling conversion pipeline.

## Re-running the index pipeline

```bash
python3 scripts/fetch_arxiv_metadata.py    # corpus/metadata-enriched.jsonl + corpus/authors.jsonl
python3 scripts/build_index_db.py --rebuild
python3 scripts/enrich_and_tag_db.py       # fill abstracts, authors, tags
```
