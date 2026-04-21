#!/usr/bin/env python3
"""Cosmetic postprocessor for docling-converted markdowns in the Morpheus corpus.

Fixes two known defects emitted by docling:
  1. Paper titles are emitted as H2 (`## `) rather than H1 (`# `).
  2. Some files start with a leading `<!-- image -->` cover-page artifact.

Additional normalization:
  - Strips leading blank lines and leading HTML comment lines.
  - Collapses runs of 3+ blank lines to 2.

Idempotent: running twice is a no-op.

Usage:
    python scripts/postprocess_markdowns.py --dry-run
    python scripts/postprocess_markdowns.py
    python scripts/postprocess_markdowns.py --files 'papers/markdown/2509*.md'
    python scripts/postprocess_markdowns.py --skip-incomplete
"""
from __future__ import annotations

import argparse
import difflib
import glob
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GLOB = "papers/markdown/*.md"

HTML_COMMENT_RE = re.compile(r"^\s*<!--.*?-->\s*$")
H1_RE = re.compile(r"^#\s+\S")
H2_RE = re.compile(r"^##\s+\S")
MULTI_BLANK_RE = re.compile(r"\n{4,}")  # 3+ blank lines = 4+ newlines


def transform(text: str) -> tuple[str, list[str]]:
    """Apply fixes. Returns (new_text, list_of_action_labels)."""
    actions: list[str] = []
    lines = text.splitlines(keepends=False)

    # 1. Strip leading blank lines and leading HTML comment lines.
    stripped_any = False
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            i += 1
            stripped_any = True
            continue
        if HTML_COMMENT_RE.match(ln):
            i += 1
            stripped_any = True
            actions.append(f"stripped leading comment: {ln.strip()!r}")
            continue
        break
    if i > 0:
        lines = lines[i:]
        if stripped_any and not any(a.startswith("stripped leading comment") for a in actions):
            # only blank lines stripped; do not log as an action (trivial)
            pass

    # 2. If no H1 anywhere, promote first H2 to H1.
    has_h1 = any(H1_RE.match(ln) for ln in lines)
    if not has_h1:
        for idx, ln in enumerate(lines):
            if H2_RE.match(ln):
                new = "# " + ln[3:]  # replace leading "## " with "# "
                lines[idx] = new
                actions.append(f"promoted H2->H1 at line {idx + 1}: {new.strip()[:80]!r}")
                break

    # 3. Collapse 3+ consecutive blank lines to 2.
    new_text = "\n".join(lines)
    # preserve trailing newline if original had one
    if text.endswith("\n"):
        new_text += "\n"

    collapsed = MULTI_BLANK_RE.sub("\n\n\n", new_text)
    if collapsed != new_text:
        actions.append("collapsed 3+ blank lines to 2")
    new_text = collapsed

    return new_text, actions


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def process_file(path: Path, dry_run: bool) -> bool:
    """Return True if the file would change / did change."""
    original = path.read_text(encoding="utf-8")
    new_text, actions = transform(original)
    if new_text == original:
        return False

    rel = path.relative_to(REPO_ROOT) if path.is_absolute() else path
    print(f"\n=== {rel} ===")
    for a in actions:
        print(f"  - {a}")

    if dry_run:
        diff = difflib.unified_diff(
            original.splitlines(keepends=False)[:40],
            new_text.splitlines(keepends=False)[:40],
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            lineterm="",
            n=2,
        )
        print("\n".join(diff))
    else:
        atomic_write(path, new_text)
        print("  [written]")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Show actions without writing.")
    ap.add_argument("--files", default=DEFAULT_GLOB,
                    help=f"Glob of files to process (default: {DEFAULT_GLOB}).")
    ap.add_argument("--skip-incomplete", action="store_true",
                    help="Skip files modified in the last 10 seconds (docling may still be writing).")
    args = ap.parse_args()

    pattern = args.files
    if not os.path.isabs(pattern):
        pattern = str(REPO_ROOT / pattern)
    paths = sorted(Path(p) for p in glob.glob(pattern))
    if not paths:
        print(f"No files matched: {pattern}", file=sys.stderr)
        return 1

    now = time.time()
    changed = 0
    skipped = 0
    scanned = 0
    for p in paths:
        if not p.is_file():
            continue
        if args.skip_incomplete:
            try:
                if now - p.stat().st_mtime < 10:
                    skipped += 1
                    continue
            except OSError:
                skipped += 1
                continue
        scanned += 1
        if process_file(p, args.dry_run):
            changed += 1

    print(f"\nScanned: {scanned}  Changed: {changed}  Skipped(incomplete): {skipped}  "
          f"Mode: {'dry-run' if args.dry_run else 'write'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
