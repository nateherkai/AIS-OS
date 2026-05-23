# Connections

Registry of every system the AIOS can reach. Filled by `/onboard` from Q4-Q7 answers; expanded over time as new tools get wired. `/audit` checks this file for domain coverage and freshness.

## Substrates

Two MCP routers carry most of the AIOS's reach. Per-toolkit rows below run through one of these:

| Substrate | What it exposes | Umbrella reference |
|---|---|---|
| **Composio** (`mcp__mcp-router__COMPOSIO_*`) | Gmail, Google Calendar, Google Drive, Google Docs, Google Sheets, Granola, Fireflies — plus other connected-but-not-yet-exercised toolkits (Notion, GitHub, Exa, Firecrawl, LinkedIn read, Supabase, etc.) | `references/composio-mcp.md` |
| **Atlassian** (`mcp__claude_ai_Atlassian__*`) | Jira + Confluence on `everestlabs.atlassian.net` | `references/jira-mcp.md` (covers both) |

## Per-tool registry

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Revenue / Financials | **Customer Deployment Dashboard** (Google Sheet, ID `1gMk0GkQqDjQ6MINHCkFHA-rco6ZddxbvlhbXSoNXz8M`) via Drive MCP | `mcp` | Composio (Drive `travis-everestlabs`) | 2026-05-19 |
| 1b | Revenue / Financials | Salesforce (accounts, deals, customer stage) | not yet connected | — | — |
| 2 | Customer interactions | Gmail (travis@everestlabs.ai) | `mcp` | Composio (Gmail `travis-everestlabs`) | 2026-05-19 |
| 2b | Customer interactions | Zoom + customer texting channels | not yet connected | — | — |
| 3 | Calendar | Google Calendar (work + personal) | `mcp` | Composio (GoogleCalendar `travis-everestlabs` default, `travis-personal`) | 2026-05-19 |
| 4 | Communication | Flock (internal team — Slack-equivalent at Everest) | not yet connected | — | — |
| 4b | Communication | Gmail (travispeng@gmail.com) | `mcp` | Composio (Gmail `travis-personal-gmail`) | 2026-05-19 |
| 4c | Communication | LinkedIn DMs | not yet connected | — | — |
| 5 | Project / task tracking | JIRA (Everest cloud `everestlabs.atlassian.net`, 13 projects — POC, NAV, L2, ENG, CORE, CI, PI, PB, POI, RR, DPUC, PART, WT) | `mcp` | Atlassian (claude.ai connector, cloudId `e830597d-ffd6-4aed-a34b-e0bbb574db04`) | 2026-05-19 |
| 5b | Project / task tracking | Confluence (same site, same connector — read/write scopes) | `mcp` (available, not yet exercised) | Atlassian (claude.ai connector) | 2026-05-19 |
| 6 | Meeting intelligence | Granola (primary, Everest meetings) | `mcp` | Composio (granola_mcp `gainly-micro`) | 2026-05-19 |
| 6b | Meeting intelligence | Fireflies (some Everest + personal recordings) — Everest channel `6a0c1cec7610454b44024df2` | `mcp` | Composio (fireflies `relink-spacer`) | 2026-05-19 |
| 7 | Knowledge / files | Google Drive (work + personal) | `mcp` | Composio (GoogleDrive `travis-everestlabs` default, `travis-personal`; Docs same aliases) | 2026-05-19 |

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `not yet connected`.

When a new tool is wired, also save `references/{tool}-mcp.md` (or `{tool}-api.md` for key+ref tools) capturing endpoints, auth flow, and common queries — researched-once-saved-forever.

**Reference docs in place** (under `references/`):
- `composio-mcp.md` — **umbrella substrate**: account-alias system, search-then-execute pattern, oversized-response handling, default-account-mismatch table, **per-toolkit notes for Gmail / Calendar / Drive / Docs / Sheets** (these are Composio toolkits, not separate MCPs — folded into the umbrella).
- `granola-mcp.md` — meeting intelligence (primary). Standalone because Granola's concepts (query / list / get / transcript) are distinct.
- `fireflies-mcp.md` — meeting intelligence (secondary, Everest channel). Standalone because Fireflies' channel model + AskFred are distinct.
- `jira-mcp.md` — project / task tracking (Everest cloud; also covers Confluence availability via the same connector). Standalone because Atlassian is a different MCP substrate.
- `3ms-framework.md` — operator brain (shipped in kit, read-only)

**Open / known gaps.**

1. **Salesforce** — no MCP yet. Composio doesn't offer Salesforce in Travis's current tool list. Options: build a script with the Salesforce REST API + `references/salesforce-api.md`, or wait for a future Composio integration. Important — Salesforce is the system of record for deals + customer hierarchy ([[salesforce]] in the wiki).
2. **Flock** — internal company messaging, no MCP. The bulk of internal team communication lives here and isn't yet queryable.
3. **Confluence** — connector is wired (Atlassian MCP with read/write scopes), but no reference doc written yet. Worth a future `/level-up` since SE-team-owned per-MRF data lives there.
4. **Google account default mismatch.** Calendar + Drive default to `travis-everestlabs`. Gmail defaults to `travis-personal-gmail`. **Always pass the `account` alias explicitly** — the inconsistency burns time when forgotten.

**JIRA adoption — partial (2026-05-19).** Engineering is on JIRA (POC, NAV, L2, ENG projects have active churn; Travis is assignee on POC-6, POC-14, POC-19 and others). But the POC team / customer-facing structure Apurba designed on May 13 — customer-feature epics with `is blocked by` links to engineering issues — is **not yet rolled out**. Travis has to teach the structure and onboard the rest of the POC team. Until that's done, JQL searches across customer features will be incomplete and dependency walks will hit gaps. Wiki's [[everest-labs]] page should reflect this nuance on next wiki pass (currently overstates the "not active" claim).
