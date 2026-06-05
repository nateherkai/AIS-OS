# Connections

Registry of every system this AIOS can reach. Filled by `/onboard` from Q4-Q7; expanded as new tools are wired. `/audit` checks this file for domain coverage and freshness. Domains are adapted for a job search.

| # | Domain | Tool | Mechanism | Auth | Last checked |
|---|---|---|---|---|---|
| 1 | Opportunity pipeline | `projects/job-search/applications.md` (tracker) + Seek, LinkedIn Jobs, Wellfound, YC Work at a Startup, HN Who's Hiring | in-repo md (live); job boards not yet connected | — | 2026-06-04 |
| 2 | Recruiter / network | LinkedIn (in/yuanxchen) | not yet connected | — | — |
| 3 | Calendar | Google Calendar (via Gmail) | not yet connected | — | — |
| 4 | Communication | Gmail (yuancdata@gmail.com), LinkedIn, X (@magicfish23) | not yet connected | — | — |
| 5 | Project / task tracking | `projects/job-search/tasks.md` | in-repo md (live) | — | 2026-06-04 |
| 6 | Interview / call notes | `projects/job-search/notes/` | in-repo md (live) | — | 2026-06-04 |
| 7 | Knowledge / files | Job-search docs as `.md` in `projects/job-search/`; master CV in Google Docs / `~/Downloads` PDF | in-repo md (live); Google Docs not yet connected | — | 2026-06-04 |

**Mechanism options:** `mcp` (MCP server), `script` (Python/Bash hitting an API, in `scripts/`), `export` (CSV/JSON dump pipeline), `key+ref` (`.env` key + `references/{tool}-api.md` guide), `in-repo md` (markdown managed by Claude in this repo), `not yet connected`.

## Day-2+ wiring priority
1. **Gmail** (`yuancdata@gmail.com`) — read recruiter threads, draft replies. Likely MCP.
2. **LinkedIn** — recruiter conversations + people discovery. Mostly manual/Chrome for now.
3. **Job boards** — Seek + LinkedIn Jobs first; automate discovery into `applications.md`.
4. **Google Calendar** — schedule recruiter calls / interviews.

When you wire a tool, save `references/{tool}-api.md` (endpoints, auth flow, common queries) and update the row above.
