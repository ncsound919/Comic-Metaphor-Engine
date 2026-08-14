# Comic Metaphor Engine — Internal Strategy Tool

The engine is wired into the Overlay365 fleet as an **internal tool for strategy and
decision-making** (not a public SaaS). Draymond agents and the human operator use it to
map real-world problems onto comic-book storylines and get scored, actionable insight.

## Interfaces

### 1. FastAPI service (JSON API)

Run: `scripts/run_internal.ps1` → `http://127.0.0.1:8000`

- `POST /api/search` — semantic search of the protocol library
- `POST /api/map` — scored metaphor mapping for a topic
- `POST /api/explain` — plain-language explanation + takeaways + action items
- `POST /api/lesson` — compact lesson bundle (spaced-repetition friendly)
- `POST /api/narrative` — podcast/marketing/dialogue script generation
- `GET  /api/protocols` — browse the library

### 2. MCP server (agent tools)

Run: `python mcp/server.py` (stdio). Add to your agent MCP config:

```json
{
  "mcpServers": {
    "comic-metaphor-engine": {
      "command": "python",
      "args": ["<path>/mcp/server.py"]
    }
  }
}
```

Tools: `list_protocols`, `search_protocols`, `generate_mapping`, `generate_lesson`,
`generate_insight_report`, `strategy_brief`.

### 3. Draymond registry

Registered as a `service` entity in Draymond's local SQLite registry:

- slug: `comic-metaphor-engine` · sector: `writing` · category: `strategy`
- capabilities: `strategy-metaphors`, `metaphor-mapping`, `semantic-search`,
  `lesson-generation`, `narrative-generation`, `insight-reports`
- invocation: `http_api` → `http://127.0.0.1:8000`, health `/health`
- re-register anytime: `python scripts/register_draymond.py`

## Strategy use-cases

- **Decision framing** — `search_protocols` + `generate_mapping` on a business/life
  problem → a storyline + codex scores (Trueness/Flow/PCS/Overall) to reason with.
- **Lesson briefs** — `strategy_brief(topic)` returns mapping + scores + lesson + a
  generated narrative in one call.
- **Uploaded material** — `generate_insight_report(text)` extracts themes, characters,
  and real-world mappings from any narrative (e.g., a strategy doc, pitch, or story).

## Notes

- The embedding model loads lazily on first use (cold start ~60-90s); the keyword
  fallback in `MetaphorIndex` keeps searches working without it.
- No Supabase/Stripe keys are required for internal use — the API runs in dev mode
  (everything allowed, local-only).
