# postprocess_markdowns — runbook

Cosmetic fixes for docling-converted markdowns in `papers/markdown/`.

## What it does

1. Strips leading blank lines and leading `<!-- ... -->` HTML comment lines
   (removes the `<!-- image -->` cover-page artifact docling sometimes emits).
2. If the file has no `# ` H1 heading anywhere, promotes the first `## ` H2 to `# `
   (docling emits paper titles as H2).
3. Collapses runs of 3+ consecutive blank lines to 2.

The script is idempotent: running it twice is a no-op.

## When to run

Run **after** the docling batch has completed. Check:

```bash
# Confirm docling is no longer running
kill -0 "$(cat papers/markdown/convert.pid)" 2>/dev/null \
  && echo "still running" || echo "done"
```

If the batch might still be writing, you can run with `--skip-incomplete` to
skip files modified in the last 10 seconds.

## How to run

```bash
# 1. Dry-run on everything (no writes)
python scripts/postprocess_markdowns.py --dry-run

# 2. Dry-run on a subset
python scripts/postprocess_markdowns.py --dry-run --files 'papers/markdown/2509*.md'

# 3. Apply for real
python scripts/postprocess_markdowns.py

# 4. Apply safely while docling might still be wrapping up
python scripts/postprocess_markdowns.py --skip-incomplete
```

## How to verify

```bash
# Every file should now have exactly one H1
for f in papers/markdown/*.md; do
  n=$(grep -c '^# [^#]' "$f")
  [ "$n" -eq 1 ] || echo "BAD ($n H1s): $f"
done

# No file should start with an HTML comment
grep -l '^<!--' papers/markdown/*.md && echo "still has leading comments" || echo "clean"

# Re-run dry-run; it should report 0 changes (idempotency)
python scripts/postprocess_markdowns.py --dry-run
```

## How to revert

All markdowns are tracked in git. To revert:

```bash
# Revert everything
git checkout -- papers/markdown/

# Revert a single file
git checkout -- papers/markdown/2509.02544.md
```

## Flags

- `--dry-run` — show per-file actions and a unified diff preview without writing.
- `--files <glob>` — limit to a subset (default: `papers/markdown/*.md`).
- `--skip-incomplete` — skip files modified in the last 10 seconds.
