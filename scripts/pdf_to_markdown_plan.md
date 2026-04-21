# PDF → Markdown Conversion Plan (291 arXiv PDFs)

_Date: 2026-04-20 · Author: scouting agent_

## 1. Environment findings

### Docling installs discovered
| Path | Python | docling | torch/CUDA |
|------|--------|---------|-----------|
| `/home/artemisai/.local/bin/docling` (system, `#!/usr/bin/python3` → 3.14.3) | 3.14.3 | **2.84.0** (core 2.71.0, ibm-models 3.13.0, parse 5.7.0) | torch **2.11.0+cu128**, `cuda.is_available=True`, CUDA 12.8 |
| `~/.claude/skills/docling/` (skill dir) | — | not yet materialized (`.venv/` absent) | would be built with `--system-site-packages` → inherits system CUDA torch |
| Other hits (`~/sys_admin/docling`, `~/services/data/docling`, `~/projects/docling-*`) | service/API clones, not conversion venvs | — | — |

**Chosen env:** the docling **skill** at `~/.claude/skills/docling/` is the intended entrypoint (`python scripts/run.py convert.py ...`). On first run it will create `~/.claude/skills/docling/.venv/` with `--system-site-packages`, inheriting the working torch+CUDA already installed in system Python. No install action required now — the skill bootstraps itself.

Fallback / direct: we can also invoke `/home/artemisai/.local/bin/docling` directly (it works today), but the skill wrapper gives us unified CLI flags (`--ocr easyocr`, `--threads`, `--lang`), logging under `data/`, and a known-good invocation contract.

### GPU inventory
- **GPU:** NVIDIA GeForce RTX 3060 (desktop, 12 GB)
- **VRAM:** 12288 MiB total · **11131 MiB free** · ~777 MiB in use (Xorg/KDE only)
- **Temp:** 43 °C idle · **Power cap:** 170 W · currently 11 W @ P8
- **Driver:** 580.126.18 · **CUDA runtime:** 13.0 (torch built against 12.8 — compatible)

This is *not* the 5.6 GB RTX 4050 in the skill's perf notes — we have **2× the VRAM headroom**, so OOM risk is low even on 500-page PDFs.

### Corpus profile (`papers/arxiv/`)
- **Count:** 291 PDFs · **Total size:** 1012 MB (~3.5 MB avg)
- **Largest:** `2508.13009.pdf` 35.7 MB · `2404.07972.pdf` 35.2 MB · `2508.21475.pdf` 26.9 MB
- **Smallest:** `2504.12516.pdf` 0.17 MB · `2505.20282.pdf` 0.36 MB · `2510.10448.pdf` 0.43 MB
- Vast majority are arXiv preprints (text-layer PDFs, 10–30 pages) — OCR rarely needed.

## 2. Skill invocation pattern (from `~/.claude/skills/docling/SKILL.md`)

- Always go through `python ~/.claude/skills/docling/scripts/run.py convert.py --input <pdf>`.
- `check_gpu.py` first — emits recommended OCR engine.
- Key knobs:
  - `--ocr easyocr|rapidocr|none` (use **easyocr** on GPU; **none** for text-layer arXiv PDFs — huge speedup)
  - `--no-ocr` — safe default for arXiv since they carry a text layer
  - `--no-tables` — off (we want tables)
  - `--threads N` — accelerator threads (default 4); lower under thermal pressure
  - `--lang fr,en` — set to `en` for arXiv
- **Batch mode:** not native. We drive it with our own outer loop (bash/python) that calls `run.py` once per PDF. Docling itself does not ship a `--rate-limit` or `--vram-guard` flag.
- **CPU fallback:** yes — RapidOCR path is CPU-only; `--ocr rapidocr` or unsetting `CUDA_VISIBLE_DEVICES=` forces CPU. Also `--no-ocr` on text PDFs needs only layout model (still GPU by default, small footprint).
- **Known OOM advice:** reduce `--threads`, process in page ranges.

## 3. Recommended strategy

### Environment
- **Venv:** `~/.claude/skills/docling/.venv/` (auto-created by `run.py` on first call). No manual install.
- **Device:** **CUDA** — RTX 3060 12 GB is plenty. Fallback to `--ocr rapidocr` only if thermals spike.

### Concurrency & batch
- **Serial, 1 PDF per process.** Docling layout + EasyOCR already saturate ~1 GPU; parallel processes will fight over VRAM and hurt throughput.
- **Outer driver:** a Python script (`scripts/convert_arxiv_pdfs.py`, to be written in a later pass) iterating `papers/arxiv/*.pdf` in deterministic order, resumable (skip if `<id>.md` exists).
- **Batch window:** 20 PDFs per logical batch, 30–90 s cooldown between batches — simple throttling.
- **Per-doc default args:** `--ocr none --threads 4 --lang en` (arXiv has text layer). Retry any file whose output is <1 KB with `--ocr easyocr` as OCR fallback.

### Thermal / VRAM guard
- **Sleep:** 2 s between documents (lets the VRAM allocator recycle, smooths thermals).
- **Watchdog:** before each PDF, query `nvidia-smi --query-gpu=temperature.gpu,memory.free --format=csv,noheader,nounits`. If `temperature.gpu >= 80 °C` → sleep 60 s. If `memory.free < 2048 MiB` → sleep 30 s and retry.
- **Hard cap:** optional `nvidia-smi -pl 140` to reduce power envelope from 170 W → 140 W during the run (reversed afterwards). Not strictly needed on an RTX 3060.
- **Pause/resume:** signal trap to write progress to `papers/markdown/.progress.json` after every file.

### Output layout
```
papers/
  markdown/
    <arxiv_id>.md            # docling's markdown (docling writes alongside input by default; we redirect with --output)
    <arxiv_id>.meta.json     # sidecar with { source_pdf, bytes, pages, ocr_engine, docling_version, duration_s, sha256 }
    .progress.json           # resumable queue state
    .failures.log
```

Note: upstream docling's `convert.py` wrapper emits `.md` only; the `.meta.json` sidecar is written by **our** driver (not by docling itself). Plan doc updated to reflect that — do not assume docling emits both.

### Ingestion into `corpus/morpheus.db`
1. **Schema migration (separate PR):**
   - Add `conversion_status` column to the `papers` master table: `TEXT CHECK(conversion_status IN ('pending','ok','failed','skipped')) DEFAULT 'pending'`.
   - Add `conversion_error TEXT`, `markdown_path TEXT`, `markdown_bytes INTEGER`, `converted_at TEXT`.
   - Create FTS5 table `fulltext` if not present:
     ```sql
     CREATE VIRTUAL TABLE fulltext USING fts5(
         arxiv_id UNINDEXED, title, body,
         content='', tokenize='porter unicode61'
     );
     ```
2. **After each successful conversion:** upsert `papers` row (status=ok, paths, bytes, timestamp); `INSERT INTO fulltext(arxiv_id, title, body) VALUES (?, ?, readfile(md_path))`.
3. **On failure:** status=failed, log to `.failures.log`, append error to `conversion_error`.
4. Do this in a separate `scripts/ingest_markdown_to_db.py` step so conversion and ingestion can be re-run independently. DB writes wrapped in a transaction per batch of 20.

### Throughput estimate
Skill doc's reference: 526-page PDF ≈ 28 min on an RTX 4050 (5.6 GB, slower GPU). Our RTX 3060 is ~1.3× faster on tensor throughput and has 2× VRAM, so expect **~15–25 s per average arXiv PDF (12 pages, text-layer, `--no-ocr`)** and **3–6 min for the largest (35 MB, many figures)**.

- **Low bound** (all text-layer, `--no-ocr`, happy path):
  291 × 20 s ≈ **~1.6 h** + cooldowns (≈ 10 min) ≈ **~1 h 50 min**
- **High bound** (30 % need EasyOCR fallback, larger median, thermal throttling):
  291 × 90 s ≈ **~7.3 h** ≈ **~7–8 h**

Recommend launching the run overnight with resumable checkpointing; realistic outcome lands around **3–4 hours**.

### Explicit non-goals (this plan)
- No installs performed.
- No conversion executed.
- `corpus/morpheus.db` untouched — migration + ingestion are separate, follow-up steps.
