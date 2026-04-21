#!/usr/bin/env python3
"""Batch-convert arXiv PDFs to Markdown via docling CLI.

Serial, idempotent, with thermal/VRAM watchdog. Writes:
  papers/markdown/<arxiv_id>.md
  papers/markdown/<arxiv_id>.meta.json
  papers/markdown/conversion.log      (tab-separated)
  papers/markdown/MANIFEST.jsonl      (merged on rerun)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "papers" / "arxiv"
MD_DIR = ROOT / "papers" / "markdown"
LOG_PATH = MD_DIR / "conversion.log"
MANIFEST_PATH = MD_DIR / "MANIFEST.jsonl"
DOCLING = "/home/artemisai/.local/bin/docling"

PER_DOC_TIMEOUT_S = 600  # 10 min
SLEEP_BETWEEN_S = 2
WATCHDOG_TEMP_C = 80
WATCHDOG_FREE_MB = 2000
WATCHDOG_MAX_RETRIES = 10
WATCHDOG_SLEEP_S = 30


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gpu_status() -> tuple[int | None, int | None]:
    """Return (temp_c, free_mb) or (None, None) if unavailable."""
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        ).strip()
        parts = [p.strip() for p in out.splitlines()[0].split(",")]
        return int(parts[0]), int(parts[1])
    except Exception:
        return None, None


def watchdog() -> None:
    for i in range(WATCHDOG_MAX_RETRIES):
        temp, free = gpu_status()
        if temp is None:
            return
        if temp < WATCHDOG_TEMP_C and free >= WATCHDOG_FREE_MB:
            return
        print(
            f"[watchdog] temp={temp}C free={free}MB — retry {i+1}/{WATCHDOG_MAX_RETRIES}"
            f" after {WATCHDOG_SLEEP_S}s",
            flush=True,
        )
        time.sleep(WATCHDOG_SLEEP_S)
    print("[watchdog] max retries reached; proceeding anyway", flush=True)


def load_manifest() -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    rows[rec["arxiv_id"]] = rec
                except Exception:
                    pass
    return rows


def write_manifest(rows: dict[str, dict]) -> None:
    tmp = MANIFEST_PATH.with_suffix(".jsonl.tmp")
    with tmp.open("w") as f:
        for aid in sorted(rows):
            f.write(json.dumps(rows[aid], sort_keys=True) + "\n")
    tmp.replace(MANIFEST_PATH)


def log_line(arxiv_id: str, status: str, seconds: float, out_bytes: int, error: str) -> None:
    with LOG_PATH.open("a") as f:
        err = error.replace("\t", " ").replace("\n", " ")[:500]
        f.write(f"{now_iso()}\t{arxiv_id}\t{status}\t{seconds:.2f}\t{out_bytes}\t{err}\n")


def inspect_markdown(md_path: Path) -> tuple[int, bool, bool]:
    """Return (approx_pages, has_tables, has_images). Pages heuristic: count form-feeds or fallback 0."""
    try:
        text = md_path.read_text(errors="ignore")
    except Exception:
        return 0, False, False
    has_tables = "|" in text and re.search(r"^\s*\|.*\|\s*$", text, re.M) is not None
    has_images = "![" in text or "<img" in text
    # docling doesn't always mark page breaks; leave pages=0 if unknown
    pages = 0
    return pages, bool(has_tables), has_images


def convert_one(pdf: Path, force: bool) -> dict:
    arxiv_id = pdf.stem
    md_out = MD_DIR / f"{arxiv_id}.md"
    meta_out = MD_DIR / f"{arxiv_id}.meta.json"

    if md_out.exists() and md_out.stat().st_size > 0 and not force:
        rec = {
            "arxiv_id": arxiv_id,
            "status": "skipped",
            "seconds": 0.0,
            "md_bytes": md_out.stat().st_size,
            "pages": 0,
            "has_tables": False,
            "has_images": False,
            "error": "",
        }
        log_line(arxiv_id, "skipped", 0.0, md_out.stat().st_size, "")
        return rec

    watchdog()

    cmd = [
        DOCLING,
        str(pdf),
        "--to",
        "md",
        "--output",
        str(MD_DIR),
        "--device",
        "cuda",
        "--no-ocr",
        "--num-threads",
        "4",
        "--document-timeout",
        str(PER_DOC_TIMEOUT_S),
        "--image-export-mode",
        "placeholder",
    ]

    start = time.time()
    error = ""
    status = "ok"
    try:
        proc = subprocess.run(
            cmd,
            timeout=PER_DOC_TIMEOUT_S + 60,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            status = "failed"
            error = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:]
            error = error[0] if error else f"exit={proc.returncode}"
    except subprocess.TimeoutExpired:
        status = "timeout"
        error = f"timeout>{PER_DOC_TIMEOUT_S + 60}s"
    except Exception as e:
        status = "failed"
        error = f"{type(e).__name__}: {e}"
    seconds = time.time() - start

    md_bytes = md_out.stat().st_size if md_out.exists() else 0
    if status == "ok" and md_bytes == 0:
        status = "failed"
        error = error or "empty output"

    pages, has_tables, has_images = (0, False, False)
    if md_out.exists() and md_bytes > 0:
        pages, has_tables, has_images = inspect_markdown(md_out)
        meta = {
            "arxiv_id": arxiv_id,
            "source_pdf": str(pdf.relative_to(ROOT)),
            "source_bytes": pdf.stat().st_size,
            "md_bytes": md_bytes,
            "duration_s": round(seconds, 2),
            "ocr_engine": "none",
            "device": "cuda",
            "docling_cli": DOCLING,
            "converted_at": now_iso(),
            "has_tables": has_tables,
            "has_images": has_images,
        }
        meta_out.write_text(json.dumps(meta, indent=2, sort_keys=True))

    log_line(arxiv_id, status, seconds, md_bytes, error)
    return {
        "arxiv_id": arxiv_id,
        "status": status,
        "seconds": round(seconds, 2),
        "md_bytes": md_bytes,
        "pages": pages,
        "has_tables": has_tables,
        "has_images": has_images,
        "error": error,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="Process all PDFs in papers/arxiv/")
    ap.add_argument("--files", nargs="*", default=[], help="Specific arxiv IDs or pdf paths to process")
    ap.add_argument("--force", action="store_true", help="Re-convert even if .md exists")
    ap.add_argument("--limit", type=int, default=0, help="Stop after N PDFs (0=all)")
    args = ap.parse_args()

    MD_DIR.mkdir(parents=True, exist_ok=True)

    if args.files:
        pdfs: list[Path] = []
        for f in args.files:
            p = Path(f)
            if not p.is_absolute():
                # try as arxiv id
                candidate = PDF_DIR / (p.name if p.suffix == ".pdf" else f"{f}.pdf")
                if candidate.exists():
                    p = candidate
                else:
                    p = (ROOT / f).resolve()
            pdfs.append(p)
    elif args.all:
        pdfs = sorted(PDF_DIR.glob("*.pdf"))
    else:
        print("ERROR: pass --all or --files ...", file=sys.stderr)
        return 2

    if args.limit:
        pdfs = pdfs[: args.limit]

    if not shutil.which(DOCLING) and not Path(DOCLING).exists():
        print(f"ERROR: docling not found at {DOCLING}", file=sys.stderr)
        return 3

    total = len(pdfs)
    print(f"[start] {now_iso()} pdfs={total} force={args.force}", flush=True)

    manifest = load_manifest()
    run_start = time.time()

    for idx, pdf in enumerate(pdfs, 1):
        if not pdf.exists() or pdf.suffix.lower() != ".pdf":
            print(f"[skip] {pdf} (missing or not a pdf)", flush=True)
            continue
        t0 = time.time()
        rec = convert_one(pdf, force=args.force)
        manifest[rec["arxiv_id"]] = rec
        # flush manifest every doc so crashes don't lose progress
        write_manifest(manifest)

        dt = time.time() - t0
        print(
            f"[{idx}/{total}] {rec['arxiv_id']} status={rec['status']} "
            f"t={dt:.1f}s md_kb={rec['md_bytes']/1024:.1f} err={rec['error'][:80]}",
            flush=True,
        )

        if idx % 10 == 0:
            elapsed = time.time() - run_start
            rate = idx / (elapsed / 60) if elapsed > 0 else 0
            eta_min = (total - idx) / rate if rate > 0 else 0
            print(
                f"[progress {idx}/{total}] elapsed={elapsed/60:.1f}m "
                f"rate={rate:.2f}/min eta={eta_min:.0f}m",
                flush=True,
            )

        if idx < total:
            time.sleep(SLEEP_BETWEEN_S)

    elapsed = time.time() - run_start
    print(f"[done] {now_iso()} elapsed={elapsed/60:.1f}m processed={len(pdfs)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
