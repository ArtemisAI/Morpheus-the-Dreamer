# Docling conversion quality notes

Sampled 5 files 2026-04-21T04:02Z. Content quality is GOOD: sizes 90–117 KB, 3+ section headers each, pipe tables render cleanly, no error strings, math equations intact.

**Cosmetic defect (consistent across all 5):**

1. Paper titles are emitted as `## ` (H2) rather than `# ` (H1). No top-level heading on the documents.
2. One file (`2509.02544.md`) starts with a stray `<!-- image -->` comment before the title.

**Proposed fix (post-process, cheap — no reconversion needed):**

```python
# For each .md file: if no line starts with '# ' but a '## ' line exists,
# promote the FIRST '## ' to '# '. Also strip leading lines matching /^<!-- image -->/.
```

This is safe to run after the full batch completes. **Do not auto-apply** — wait for user review.

**Reconversion NOT needed.** Body content, tables, and math are intact.
