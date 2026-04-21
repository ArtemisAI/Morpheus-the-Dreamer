#!/usr/bin/env bash
# Print cron setup instructions for the weekly arXiv refresh.
# Does NOT modify crontab — review, then install yourself with `crontab -e`.

set -euo pipefail

REPO="/home/artemisai/tools/tools-for-agents/Morpheus-the-Dreamer"
PYTHON="$(command -v python3 || echo /usr/bin/python3)"
CRON_LINE="0 6 * * 1 cd ${REPO} && ${PYTHON} scripts/weekly_arxiv_refresh.py >> corpus/refresh-log.out 2>&1"

cat <<EOF
Morpheus weekly arXiv refresh — cron setup
==========================================

Cadence: Mondays at 06:00 local time (arXiv posts Sun-Thu nights, so Monday
morning catches the full week's new submissions).

Default behavior: staging-only. New papers land in corpus/staging-new.jsonl.
The DB is NOT modified until you run --promote manually. See
scripts/weekly_arxiv_refresh.md for the review workflow.

Cron line:
----------
${CRON_LINE}

Option A — system cron (recommended for unattended operation)
-------------------------------------------------------------
  1. Review the line above.
  2. Open your crontab:         crontab -e
  3. Paste the line, save, exit.
  4. Verify:                    crontab -l | grep weekly_arxiv_refresh

Option B — Claude-managed schedule (via the /schedule skill)
------------------------------------------------------------
  From a Claude Code session in this repo, run:

      /schedule

  When prompted, supply:
      cron:      0 6 * * 1
      command:   python3 scripts/weekly_arxiv_refresh.py
      cwd:       ${REPO}

  This registers a remote trigger that Claude runs on the schedule; output
  lands in the trigger's session log rather than corpus/refresh-log.out.

Disable
-------
  System cron:   crontab -e  and remove the line.
  /schedule:     /schedule list  -> then /schedule delete <id>

Logs
----
  Structured run log:  ${REPO}/corpus/refresh-log.jsonl
  Raw stdout/stderr:   ${REPO}/corpus/refresh-log.out  (system cron only)
  Staging file:        ${REPO}/corpus/staging-new.jsonl
EOF
