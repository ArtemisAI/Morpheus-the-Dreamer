# Runbook: Weekly arXiv Refresh (Automated)

Companion to `scripts/refresh_arxiv.md` (the manual monthly runbook).
This one is the lightweight, cron-driven weekly sweep.

## What the cron does

Every Monday 06:00 local time, `scripts/weekly_arxiv_refresh.py` runs the
11-bucket query set from the manual runbook against the arXiv HTTP API,
windowed to *(last successful run date)* → *today*. Results are deduped
against `corpus/morpheus.db`.`papers` and appended to
`corpus/staging-new.jsonl` (keyed by `arxiv_id`, so reruns are idempotent).

The script **does not** touch the DB, `papers/arxiv/`, or the docling
pipeline by default — staging only. That keeps the cron safe to run while
the docling batch is chewing on `papers/markdown/`.

## Files

| path | purpose |
|---|---|
| `scripts/weekly_arxiv_refresh.py` | the sweep script |
| `scripts/install_weekly_cron.sh`  | prints the cron line + install instructions |
| `corpus/staging-new.jsonl`        | candidate new papers awaiting review |
| `corpus/refresh-log.jsonl`        | one JSON row per run (window, counts, errors) |
| `corpus/refresh-log.out`          | raw stdout/stderr tail from cron |
| `corpus/pdf-download-queue.jsonl` | queue consumed by the docling pipeline (populated only by `--promote`) |

## Manual review + merge

After a cron run (or anytime):

```bash
# 1. Inspect staging
wc -l corpus/staging-new.jsonl
jq -r '[.arxiv_id, (.buckets|join(",")), .title] | @tsv' corpus/staging-new.jsonl | less

# 2. Drop out-of-scope rows by editing corpus/staging-new.jsonl directly.

# 3. Promote: inserts approved staging rows into morpheus.db AND appends to
#    corpus/pdf-download-queue.jsonl for the docling pipeline to pick up.
python3 scripts/weekly_arxiv_refresh.py --promote

# 4. Clear staging after promotion:
mv corpus/staging-new.jsonl corpus/staging-archive-$(date +%F).jsonl
```

`--commit` (without `--promote`) writes to the DB but skips the PDF queue —
useful if you want to land metadata without triggering downloads.

## Flags

```
python3 scripts/weekly_arxiv_refresh.py               # default: staging only
python3 scripts/weekly_arxiv_refresh.py --no-commit   # same as default, explicit
python3 scripts/weekly_arxiv_refresh.py --commit      # stage + DB insert
python3 scripts/weekly_arxiv_refresh.py --promote     # stage + DB insert + queue PDFs
python3 scripts/weekly_arxiv_refresh.py --dry-run     # fetch + parse, write nothing
python3 scripts/weekly_arxiv_refresh.py \
    --date-from 2026-04-13 --date-to 2026-04-20       # override window
python3 scripts/weekly_arxiv_refresh.py --max-results 100
```

## Install / disable the cron

```bash
bash scripts/install_weekly_cron.sh     # prints instructions; does NOT modify crontab
crontab -e                              # paste the line shown
crontab -l | grep weekly_arxiv_refresh  # verify
```

To disable: `crontab -e` and remove the line. If you used `/schedule`
instead of system cron, run `/schedule list` then `/schedule delete <id>`.

## Rate limiting & ToS

- One HTTP request per bucket (11 per run), 3 s sleep between requests
  (arXiv ToS: ≤1 request / 3 s).
- `User-Agent: Morpheus-the-Dreamer/0.1 (mailto:cardenalito@gmail.com)` per
  arXiv's automated-access guidance.

## Troubleshooting

- **No results ever** — check `corpus/refresh-log.jsonl` for `errors`.
  A network blip will be recorded per bucket; rerun the script.
- **Duplicate rows after promote** — safe: `INSERT OR IGNORE` against the
  `arxiv_id` unique constraint.
- **Window too wide on first run** — default falls back to 7 days ago.
  Override with `--date-from`.
- **Cron runs but produces nothing** — check `corpus/refresh-log.out`;
  most common cause is a stale `PATH` in the non-login shell cron uses.
  The install script pins `python3` absolute path to avoid that.
