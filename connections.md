# Connections

Registry of every system your AIOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | Stripe (acct 51Sm6ps — live) | key+ref | .env | 2026-05-11 |
| 2 | Customer interactions | Gmail (support@agcoachpro.com) | mcp (claude.ai) | active | 2026-05-12 |
| 3 | Customer interactions | Facebook DMs, iMessage | not yet connected | — | — |
| 4 | Bulk Email | MailerLite | not yet connected | — | — |
| 5 | Calendar | Google Calendar | mcp (claude.ai) | active | 2026-05-11 |
| 6 | Files / Docs | Google Drive | mcp (claude.ai) | active | 2026-05-11 |
| 7 | Project / task tracking | (none yet — in head) | not yet connected | — | — |
| 8 | Meeting intelligence | (none yet) | not yet connected | — | — |
| 9 | Product DB | Supabase (nkoyotdafqllgbpuklva) | mcp (claude.ai) | active | 2026-05-11 |
| 10 | Product Deploy | Vercel (prj_4xPOIb5yS0qzoJFmLstwRURR9KC9) | mcp (claude.ai) | active | 2026-05-11 |

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `not yet connected`.

When you wire a new tool, also save `references/{tool}-api.md` capturing endpoints, auth flow, and common queries — researched-once-saved-forever.
