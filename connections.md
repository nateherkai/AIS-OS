# Connections

Registry of every system the AIOS can reach. `/audit` checks for domain coverage and freshness. Status legend: `connected` = live + tested, `mcp-only` = MCP available but not wired into a skill yet, `manual` = human draft/paste boundary, `missing` = needed but not yet wired.

## Core registry

| # | Domain | Tool | Mechanism | Auth | Status | Used by | Last checked |
|---|---|---|---|---|---|---|---|
| 1 | Revenue | Stripe (acct `51Sm6ps`) | key+ref | `.env STRIPE_KEY` | connected | `stripe-snapshot`, `revenue-snapshot` (planned) | 2026-05-11 |
| 2 | Customer email | Gmail `support@agcoachpro.com` | mcp (claude.ai) | active | connected | `draft-reply` | 2026-05-12 |
| 3 | Customer DMs | Facebook DMs | — | — | manual | draft-then-paste | — |
| 4 | Customer SMS | iMessage | — | — | manual | draft-then-paste | — |
| 5 | Bulk email | MailerLite | REST | TODO `.env MAILERLITE_KEY` | missing | `content-draft` (planned) | — |
| 6 | Calendar | Google Calendar | mcp (claude.ai) | active | connected | session briefings | 2026-05-11 |
| 7 | Files / Docs | Google Drive | mcp (claude.ai) | active | mcp-only | ad-hoc | 2026-05-11 |
| 8 | Project / tasks | (none yet) | — | — | missing | — | — |
| 9 | Meeting intelligence | (none yet) | — | — | missing | — | — |
| 10 | Product DB (ACP) | Supabase `nkoyotdafqllgbpuklva` | mcp (claude.ai) | active | connected | `trial-follow-up`, `weekly-pipeline-check`, eval | 2026-05-11 |
| 11 | Product deploy (ACP) | Vercel `prj_4xPOIb5yS0qzoJFmLstwRURR9KC9` | mcp (claude.ai) | active | connected | deploy ops | 2026-05-11 |
| 12 | Agent infra (Hermes) | Railway + local | bridge.py + WebSocket + Pantheon | active | connected | `acp-pipeline`, `aios-audit`, `wiki-hot-loader`, `bryan` persona | 2026-05-21 |
| 13 | Vector recall | Pinecone `gravityclaw-vector` / ns `knowledge` | script | `OPENAI_API_KEY` in `.env` | connected | `pinecone_memory.py`, wiki-query fallback | 2026-05-21 |
| 14 | Vault graph | Graphify | local script | — | connected | wiki-query, dream | 2026-05-21 |

## Per-business connection map

| Business | Stripe | DB | Domain | Comms |
|---|---|---|---|---|
| Ag Coach Pro | `51Sm6ps` (live) | Supabase `nkoyotdafqllgbpuklva` | agcoachpro.com (Vercel) | Gmail support@, MailerLite, FB DMs, in-person |
| AFL | TODO | TODO | TODO | TODO |
| AFL Livestock Solutions | TODO | TODO | TODO | TODO |
| AFL Detailing | TODO | TODO | TODO | TODO |
| Ranch Dad Strength | TODO | TODO | TODO | TODO |

## Boundaries (intentional manual)

- **iMessage / FB DMs:** no API. Skills draft replies → Bryan pastes. Don't try to automate sending.
- **In-person sales:** no automation. Logged manually to `decisions/log.md` after each event.

## Mechanism options

`mcp` (MCP server) · `script` (Python/Bash hitting an API, in `scripts/`) · `export` (CSV/JSON dump pipeline) · `key+ref` (`.env` key + `references/{tool}-api.md` guide) · `manual` (human boundary) · `missing` (needed, not wired).

When wiring a new tool, save `references/{tool}-api.md` capturing endpoints, auth flow, common queries.

---

## Hermes Integration Detail (v2 — 2026-05-21)

The Hermes ↔ AIS-OS bridge is now fully wired. Architecture:

| Layer | What | Where |
|---|---|---|
| Memory | Hermes vault_root → AIS-OS/Bryan-Aaron-Master/wiki | `hermes/memory/config.py` (env: HERMES_VAULT_PATH) |
| Identity | soul.md upgraded with full Bryan context | `hermes/memory/soul.md` |
| Persona | Bryan Pantheon persona (@Bryan in Telegram) | `hermes/personas/bryan.md` |
| Skills | acp-pipeline, aios-audit, wiki-hot-loader, session-summary-pusher | `hermes-claw/skills/` |
| Dashboard | hermes-panel.html — live WebSocket feed + pipeline KPIs | `dashboard/hermes-panel.html` |
| Bridge | bridge.py — /api/bridge/handshake, /api/bridge/query, /api/bridge/push | `dashboard/scripts/bridge.py` |
| Launch | super-aios.sh — unified startup script | `AIS-OS/super-aios.sh` |

**What you can do from Telegram today:**
- `@Bryan pipeline check` → live Supabase school count + cold leads
- `@Bryan run audit` → Four-Cs gap report on the OS
- `@Bryan what's on my hot list` → vault hot.md top-of-mind topics
- `@Bryan draft follow-up for cold trials` → auto-drafts outreach to aging trials
- `@Bryan memory <topic>` → 5-layer memory query

**Crons running in Hermes (once gateway is live):**
- Mon 06:00 → acp-pipeline → Telegram summary
- Sun 21:00 → aios-audit → Four-Cs gap report to Telegram
