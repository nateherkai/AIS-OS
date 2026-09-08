# Connections

Registry of every system your AIOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as you wire new tools. `/audit` checks this file for domain coverage and freshness.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | None yet — YouTube Studio (subs/watch-hours) as proxy metric | not yet connected | — | — |
| 2 | Customer interactions | Discord | not yet connected — no MCP connector available in this environment | — | — |
| 3 | Calendar | Google Calendar (`roman.brandon503@gmail.com`) | mcp | OAuth (session-scoped) | 2026-09-06 |
| 4 | Communication | Gmail (`roman.brandon503@gmail.com`) — connected; Outlook and Discord not yet | mcp | OAuth (session-scoped) | 2026-09-06 |
| 5 | Project / task tracking | Per-repo `PROJECT-STATE.md`, each scoped to its own project — **Home Base** (the NOT A WORK BRO app, priority #2): `C:\Users\roman\main-bro\apps\home-base\PROJECT-STATE.md`. **Main Rig** (the harness/dashboard project, a separate effort): `C:\Users\roman\main-bro\PROJECT-STATE.md` — do not use this one for Home Base questions | filesystem (direct path, read-only) | none needed — local files | 2026-09-07 |
| 6 | Meeting intelligence | None — no separate tool | not yet connected | — | — |
| 7 | Knowledge / files | Obsidian vault (`C:\Users\roman\Claude Main\content-brand\Obsidian Vault`) | filesystem (direct path, read-only) | none needed — local files | 2026-09-06 |

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `filesystem` (direct local path, no auth — e.g. a synced Obsidian vault), `not yet connected`.

When you wire a new tool, also save `references/{tool}-api.md` capturing endpoints, auth flow, and common queries — researched-once-saved-forever.
