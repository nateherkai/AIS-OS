# Phase A — Onboarding Wizard + Supabase + Pinecone Design

**Date:** 2026-05-16
**Goal:** Close 3 high-priority Jack-Roberts-CC-OS gaps: in-dashboard onboarding wizard w/ AI detection toggles, Supabase widget + route, Pinecone widget + route w/ activity feed and vector query.

## 1. Onboarding Wizard

### Route
- New `#wizard` view in dashboard sidebar (under OS LAYER, above Memory)
- Gear icon top-right of every view → opens wizard modal/route

### UI — 6 steps
1. **Models** — auto-detect rows w/ status pill + toggle:
   - Claude CLI (check `which claude` + `~/.claude/`)
   - Codex CLI (check `~/.claude/plugins/cache/openai-codex` + `which codex`)
   - Gemini CLI (check `which gemini`)
   - OpenRouter (check `OPENROUTER_API_KEY` env in gravity-claw `.env`)
   - ChatGPT (manual — no auto detect; user toggles "yes I use this")
2. **Storage** — auto-detect AIOS dirs (toggle inclusion in dashboard surfaces):
   - `Bryan-Aaron-Master/` (vault)
   - `~/.claude/`
   - `/Volumes/Samsung PSSD T7/gravity-claw/`
   - `/Volumes/Samsung PSSD T7/ag-coach-app/`
3. **Memory** — env-pulled, confirm/edit:
   - Obsidian path (`vault_root` from current config)
   - Pinecone index name + namespace (from `gravity-claw/.env`)
   - Supabase project_id (from AIS-OS CLAUDE.md / existing supabase_client.py)
4. **Hourly value** — number input + slider $25–$500. Default = current `config.json.hourly_value_usd`.
5. **Dream prefs**:
   - `[ ]` Web search during dream
   - `[ ]` AI image per card (requires OpenAI key)
   - Frequency: `( ) AM only ( ) PM only ( ) Both ( ) Disabled`
6. **Review + Save** — diff vs current config + write button.

### Server endpoints
- `GET /api/wizard/detect` → `{models: [{name, detected, path, enabled}], storage: [...], memory: {obsidian, pinecone, supabase}, hourly_value, dream_prefs}`
- `POST /api/wizard/save` (body = same shape) → writes `dashboard/config.json`

### Files
- `dashboard/scripts/wizard_detect.py` — detection helpers (subprocess `which`, env reads, path checks)
- `dashboard/server.py` — 2 new routes
- `dashboard/index.html` — `#wizard` view + sidebar entry + gear icon

---

## 2. Supabase Widget + Route

### Dashboard card (existing Dashboard view)
- Project ID (truncated): `nkoyot...kva` w/ status dot
- Top-5 tables by row count (table name + row count)
- Last-24h-insert count (counts rows where `created_at > now() - 24h` across writable tables)
- Last insert timestamp

### Dedicated route `#supabase` (sidebar entry under OS LAYER, after Memory)
- All tables list w/ row counts (sortable by name/rows)
- Click table → expand to show recent 20 rows (read-only preview, max 8 columns shown)
- Stats panel: paid_schools, trial_schools, 24h_events_count
- Advisor warnings (RLS, missing indexes) from MCP `get_advisors`

### Server endpoints
- `GET /api/supabase/status` → `{project_id, status: 'ok'|'error', tables_count, last_insert_ts}`
- `GET /api/supabase/tables` → `{tables: [{name, rows, last_modified}]}`
- `GET /api/supabase/table/{name}?limit=20` → `{name, columns, rows}`
- `GET /api/supabase/advisors` → MCP `get_advisors` output

### Files
- `dashboard/scripts/supabase_widget.py` — wraps existing `supabase_client.py`
- `dashboard/server.py` — 4 new routes
- `dashboard/index.html` — Supabase card on Dashboard + `#supabase` view

### Constraint
- All queries READ-ONLY. No writes from dashboard.
- Use existing `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` from env.

---

## 3. Pinecone Widget + Route

### Memory view card (above the graph)
- Index name (`gravityclaw`)
- Namespace (`knowledge`)
- Total vector count
- Recent-5 vectorizations feed (timestamp + 1-line summary)
- Query input box → opens full route on submit

### Dedicated route `#pinecone` (sidebar entry under OS LAYER, after Memory)
- Full activity feed (recent 50 vector writes w/ timestamp + summary + source)
- Search box: text → embed via OpenAI ada-002 → query Pinecone → top-10 matches w/ scores + source paths
- Visual cluster map: D3-force, nodes = vectors w/ metadata category, sized by recency (1-week window)

### Activity log
- File: `~/.claude/pinecone_writes.jsonl`
- Format: one line per write: `{"ts": "2026-05-16T...", "action": "upsert", "namespace": "knowledge", "summary": "...", "count": 14}`
- If file missing on first read, show "No recent activity logged. Vector writes will appear here after next memory store."
- Future: add a 1-line append to `pinecone_memory.py` upsert path to populate log. Phase A only reads — separate ticket to wire write-hook.

### Server endpoints
- `GET /api/pinecone/stats` → `{index, namespace, total_vectors, dimension}`
- `GET /api/pinecone/recent?limit=50` → `{items: [{ts, summary, source, count}]}`
- `POST /api/pinecone/query` body `{text, top_k}` → `{matches: [{id, score, metadata, summary}]}`

### Files
- `dashboard/scripts/pinecone_widget.py` — stats + recent-log reader + query (uses existing `~/.claude/pinecone_memory.py` helpers)
- `dashboard/server.py` — 3 new routes
- `dashboard/index.html` — Pinecone card on Memory view + `#pinecone` view

### Constraint
- Read-only Pinecone access (query OK, no upsert from dashboard).
- Embed via OpenAI key in env (`OPENAI_API_KEY`).

---

## Cross-cutting

### Sidebar updates
New entries under "OS LAYER":
- Wizard (after Dashboard, before Memory)
- Supabase (after GC Bridge)
- Pinecone (after Supabase)

### Gear icon
Top-right corner of every view header. Click → navigates to `#wizard`.

### Config writes
`POST /api/wizard/save` writes to `dashboard/config.json` (existing file). Schema becomes:
```json
{
  "hourly_value_usd": 100,
  "vault_path": "../Bryan-Aaron-Master",
  "wiki_path": "../Bryan-Aaron-Master/wiki",
  "dreams_dir": "./data/dreams",
  "skills_global": "~/.claude/skills",
  "skills_project": "../.claude/skills",
  "lint_report": "./lint-report.md",
  "skill_suggestions": "./skill-suggestions.md",
  "subscriptions": [...],
  "dream_cron": "0 2 * * *",
  "models": [{"name": "claude", "enabled": true}, ...],
  "storage": [{"path": "...", "enabled": true}, ...],
  "memory": {"obsidian": "...", "pinecone": {...}, "supabase": {...}},
  "dream_prefs": {"web_search": false, "image_per_card": false, "frequency": "AM"}
}
```

## Files modified (final list)
- `dashboard/server.py` — 9 new routes
- `dashboard/index.html` — 3 new views + 3 new cards + 3 new sidebar entries + gear icon
- `dashboard/scripts/wizard_detect.py` (new)
- `dashboard/scripts/supabase_widget.py` (new)
- `dashboard/scripts/pinecone_widget.py` (new)
- `dashboard/config.json` — schema extended (initial values left empty; populated on first save)

## Out of scope (Phase A)
- Settings UI for editing wizard answers post-save (use `#wizard` route)
- Token/API equivalent calc (Phase B)
- Hermes-style agent panel (Phase B)
- Pinecone write-hook in `pinecone_memory.py` (separate)
- Live token usage (Phase B)
- Knowledge filter chips (Phase C — overlaps w/ nav N5)

## Success criteria
- `#wizard` route renders, detection runs, save writes config.
- Supabase card on Dashboard shows live row counts; `#supabase` route lists tables w/ previews.
- Pinecone card on Memory shows index name + count; `#pinecone` route allows text query → results.
- Sidebar has 3 new entries.
- Server restart picks up new routes without errors.

## Rollback
`git revert` Phase A commit. Config.json hand-fix if save corrupted it.
