# papers/

Paper artifacts for the 291 arXiv-identified entries in the Morpheus corpus.

## Layout

- **`arxiv/`** — downloaded arXiv PDFs. Gitignored (see repo `.gitignore`);
  the canonical list of what's local is `arxiv/MANIFEST.jsonl`. 291/291
  PDFs downloaded per the last pass. See `arxiv/README.md` for details
  on the download strategy.
- **`markdown/`** — docling-converted Markdown of the PDFs. Currently empty
  (only `.gitkeep`). A sibling agent (see `scripts/pdf_to_markdown_plan.md`)
  is responsible for populating this directory. Filenames mirror the arXiv
  ID of the source PDF.

## Storage strategy

PDFs are local-only and will be mirrored to Google Drive for durability
(decision pending). Do not commit PDFs to git — the `.gitignore` excludes
`papers/**/*.pdf`. The `MANIFEST.jsonl` is committed and acts as the source
of truth for what should be available locally.
