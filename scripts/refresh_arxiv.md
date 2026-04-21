# Runbook: Monthly arXiv Refresh

Sweep arXiv for new papers in the Morpheus topic buckets, diff against the
unified corpus, ingest new IDs, and log the refresh. Uses
[`arxiv-mcp-server`](https://github.com/blazickjp/arxiv-mcp-server) wired in
`.mcp.json` with `--storage-path` → `papers/arxiv/`.

## 1. Purpose

Keep the Morpheus research corpus current. Each month, re-query our topic
buckets for papers published **since the last refresh** and merge new ones
into `corpus/unified.jsonl` + `corpus/morpheus.db`. The snapshot for a given
refresh (date, query results, new IDs) is frozen in `corpus/refresh-log.md`.
Do not rewrite history — always append.

## 2. Prereqs

- Launch Claude Code from the repo root so the project-scoped `.mcp.json` is
  honored:
  ```bash
  cd ~/tools/tools-for-agents/Morpheus-the-Dreamer
  claude
  ```
- Verify MCP tools are listed. You should see these prefixed `mcp__arxiv__`:
  - `search_papers`
  - `download_paper`
  - `list_papers`
  - `read_paper`
- Verify storage path matches `papers/arxiv/` (see `.mcp.json`).
- Set the refresh window:
  ```
  {{LAST_REFRESH_DATE}} = latest date stamp in corpus/refresh-log.md
  {{TODAY}}             = today
  ```
  If `refresh-log.md` is empty, seed with `2026-04-01` for the first sweep.

## 3. Query set

Run one `search_papers` call per bucket. Keep `max_results=50` unless a bucket
is known to be noisy. All calls use `date_from={{LAST_REFRESH_DATE}}` and
`date_to={{TODAY}}`.

| # | Bucket | Keywords | Categories |
|---|---|---|---|
| 1 | Agentic Search | `agentic search OR retrieval agent OR search agent reinforcement learning` | `cs.CL, cs.AI, cs.IR` |
| 2 | Tool Use | `tool use LLM reinforcement learning OR tool-integrated reasoning` | `cs.CL, cs.AI` |
| 3 | PPO / GRPO / DPO | `GRPO OR PPO OR DPO language model OR policy optimization LLM` | `cs.LG, cs.CL` |
| 4 | Reward Models | `reward model LLM OR preference model RLHF` | `cs.LG, cs.CL` |
| 5 | Process Supervision | `process reward model OR step-level reward OR PRM reasoning` | `cs.LG, cs.CL` |
| 6 | Memory / Long Context | `agent memory OR long-context retrieval RL` | `cs.CL, cs.AI` |
| 7 | Self-Play / Self-Evolution | `self-play LLM OR self-evolution agent OR self-improving reasoning` | `cs.LG, cs.AI` |
| 8 | GUI / Computer Use | `GUI agent OR computer use agent OR screen agent RL` | `cs.HC, cs.AI, cs.CL` |
| 9 | Multimodal Reasoning | `multimodal reasoning RL OR vision language agent reinforcement learning` | `cs.CV, cs.CL, cs.AI` |
| 10 | Benchmarks | `agent benchmark OR tool-use benchmark OR agentic evaluation` | `cs.AI, cs.CL, cs.LG` |
| 11 | Multi-Agent | `multi-agent LLM OR cooperative agents reinforcement learning` | `cs.MA, cs.AI` |

Example call (bucket 3):
```json
{
  "query": "GRPO OR PPO OR DPO language model",
  "categories": ["cs.LG", "cs.CL"],
  "date_from": "{{LAST_REFRESH_DATE}}",
  "date_to": "{{TODAY}}",
  "max_results": 50
}
```

Persist raw results per bucket to `corpus/refresh-raw/{{TODAY}}/bucket-NN.json`.

## 4. Triage — diff against the corpus

1. Extract all returned arXiv IDs from the 11 raw result files into a sorted,
   deduped list: `corpus/refresh-raw/{{TODAY}}/returned_ids.txt`.
2. Extract existing IDs:
   ```bash
   jq -r '.arxiv_id // empty' corpus/unified.jsonl \
     | sort -u > corpus/refresh-raw/{{TODAY}}/existing_ids.txt
   ```
3. Compute the delta:
   ```bash
   comm -23 returned_ids.txt existing_ids.txt > new_ids.txt
   ```
4. For each ID in `new_ids.txt`, pick the richest matching record from the raw
   bucket JSONs and append it as a row to `corpus/staging-new.jsonl`. Schema
   must match `corpus/unified.jsonl` (arxiv_id, title, authors, year,
   abstract, url, pdf_url, categories, buckets, retrieved_at).
5. Human review pass: open `staging-new.jsonl`, drop anything clearly
   out-of-scope (scope is RL for LLM / MLLM agents, agentic search, tool use,
   reward modeling, observation scoring; see README §"Contributing / scope").

## 5. Ingest

For each approved row in `staging-new.jsonl`:

1. **Download PDF** via MCP:
   ```json
   { "paper_id": "<arxiv_id>" }
   ```
   The server drops the PDF under `papers/arxiv/` per `.mcp.json` storage-path.
2. **Insert into SQLite** (`corpus/morpheus.db`, the index the sibling agent
   is building; tables: `papers`, `authors`, `tags`, `downloads`):
   ```sql
   INSERT INTO papers (arxiv_id, title, year, abstract, url, pdf_path)
     VALUES (?, ?, ?, ?, ?, ?);
   -- then for each author:
   INSERT INTO authors (paper_id, name, position) VALUES (?, ?, ?);
   -- buckets → tags:
   INSERT INTO tags (paper_id, tag) VALUES (?, ?);
   -- download record:
   INSERT INTO downloads (paper_id, path, bytes, sha256, downloaded_at)
     VALUES (?, ?, ?, ?, ?);
   ```
   If `morpheus.db` does not yet exist, skip the SQL step and note it in the
   refresh log — the sibling agent will backfill.
3. **Append to manifests:**
   - `papers/arxiv/MANIFEST.jsonl`: one JSON line per downloaded PDF
     (`{"arxiv_id", "path", "bytes", "sha256", "downloaded_at"}`).
   - `corpus/unified.jsonl`: append the approved row.
4. **Move staged → done:** rename `corpus/staging-new.jsonl` →
   `corpus/refresh-raw/{{TODAY}}/ingested.jsonl`.

## 6. Post-refresh log

Append to `corpus/refresh-log.md`:

```md
## {{TODAY}}
- window: {{LAST_REFRESH_DATE}} → {{TODAY}}
- raw hits: <sum across 11 buckets>
- new after dedup: <count of new_ids.txt>
- ingested: <count in ingested.jsonl>
- notable additions:
  - <arxiv_id> — <title> (<bucket>)
  - ...
- skipped (out of scope): <count>
- notes: <anomalies, e.g. MCP timeouts, placeholder IDs, disk pressure>
```

Then commit:
```bash
git add corpus/refresh-log.md corpus/unified.jsonl \
        papers/arxiv/MANIFEST.jsonl corpus/refresh-raw/{{TODAY}}/
git commit -m "refresh: arxiv sweep {{TODAY}} (+N papers)"
```

Do **not** commit the PDFs themselves — `papers/arxiv/*.pdf` is gitignored and
migrating to Google Drive (see `SESSION-RESUME.md`).

## 7. Schedule

Default cadence: **manual, once per month.** The triage step (§4.5) benefits
from human judgment, so full automation is not recommended.

- To poll-automate the query + diff stages (but stop before ingest), drop the
  above into a slash command and use `/loop 30d /refresh-arxiv` — reviewer
  still runs §4.5 and §5 by hand.
- To schedule a remote sweep, use `/schedule` with cron `0 9 1 * *` (09:00 UTC
  on the 1st of each month) and have the remote agent open a PR containing
  `staging-new.jsonl` + the raw bucket JSONs for review.
- Either way, §4.5 (scope review) and §6 (refresh-log entry) remain manual.
