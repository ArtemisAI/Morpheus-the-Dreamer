# Sources manifest

The `sources/` directory is gitignored (see `.gitignore`) — the upstream awesome-lists are
reproducible git clones. This manifest records the exact commit each scrape in `scraped/`
was derived from, so the extractions can be regenerated or diffed against upstream.

To restore the sources tree locally:

```bash
mkdir -p sources && cd sources
git clone https://github.com/Necolizer/awesome-rl-for-agents.git necolizer-awesome-rl-for-agents
git clone https://github.com/0russwest0/Awesome-Agent-RL 0russwest0-awesome-agent-rl
git clone https://github.com/tongjingqi/Awesome-Agent-RL tongjingqi-awesome-agent-rl
git clone https://github.com/ventr1c/Awesome-RL-based-Agentic-Search-Papers.git ventr1c-awesome-rl-agentic-search
# then (optionally) check out the pinned SHAs below
```

## Pinned commits (ingestion snapshot)

| Local path | Remote | Commit SHA |
|---|---|---|
| `sources/necolizer-awesome-rl-for-agents` | https://github.com/Necolizer/awesome-rl-for-agents.git | `c7772bd55c16c18c50945ff68d64ed9b0f8f1251` |
| `sources/0russwest0-awesome-agent-rl` | https://github.com/0russwest0/Awesome-Agent-RL | `b2ed27eec91eb258e36dbf8531b9af8cac49f24d` |
| `sources/tongjingqi-awesome-agent-rl` | https://github.com/tongjingqi/Awesome-Agent-RL | `6f3f12d19bcddf414169d7f45fa6e180bcb57ad5` |
| `sources/ventr1c-awesome-rl-agentic-search` | https://github.com/ventr1c/Awesome-RL-based-Agentic-Search-Papers.git | `c79f089cef3061cc511f0da0dbd7b47366599bbc` |

`aitfind-morpheus-project` is not cloned here — it was a redundant wrapper around
`0russwest0-awesome-agent-rl` and is preserved only as an extracted snapshot under
`scraped/aitfind-morpheus-project/` for provenance.
