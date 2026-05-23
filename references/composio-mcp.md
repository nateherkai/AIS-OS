---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

# Composio MCP — umbrella reference for the AIOS

Composio is the **substrate** that exposes most of the AIOS's toolkits — not a domain-specific connection in its own right. This file is the canonical reference for the patterns shared across every Composio-backed toolkit, so per-tool reference docs don't have to repeat them.

If you're working with a specific service (Gmail / Calendar / Drive / Docs / Granola / Fireflies), read this **and** the per-tool reference. They split the work: umbrella concepts live here; service-specific gotchas live in the per-tool doc.

## What Composio is

A tool-router that wraps many third-party APIs behind a unified MCP interface (`mcp__mcp-router__COMPOSIO_*`). Auth is managed centrally; each underlying service is a "toolkit" with its own slugs (e.g. `gmail`, `googlecalendar`, `googledrive`, `granola_mcp`, `fireflies`). One Composio session can address many toolkits in parallel.

## Active toolkits at Everest

Confirmed wired to Travis's Composio account:

| Toolkit slug | What it covers | Reference |
|---|---|---|
| `gmail` | Gmail (read + write) | "Per-toolkit notes" below |
| `googlecalendar` | Google Calendar (read primarily) | "Per-toolkit notes" below |
| `googledrive` | Google Drive files (read + export) | "Per-toolkit notes" below |
| `googledocs` | Google Docs (plaintext + structured) | "Per-toolkit notes" below |
| `googlesheets` | Google Sheets — export via Drive's export tool | "Per-toolkit notes" below |
| `notion` | Notion pages + databases (workspace "Travis's Notion") | "Per-toolkit notes" below |
| `granola_mcp` | Granola meeting notes + transcripts | `granola-mcp.md` (standalone — distinct concepts) |
| `fireflies` | Fireflies transcripts | `fireflies-mcp.md` (standalone — distinct concepts) |

Other connected toolkits Travis has authenticated but the AIOS hasn't actively used yet: `apify`, `deepgram`, `exa`, `firecrawl`, `github`, `gladia`, `google_maps`, `linkedin`, `mem0`, `strava`, `supabase`, `supadata`, `youtube`. Prefer these over external API integrations when the use case maps.

---

## Account-alias system

Composio supports **multiple authenticated accounts per toolkit**. Each is referenced by an alias (e.g. `travis-everestlabs`, `travis-personal`) or an opaque ID (e.g. `gmail_weakly-taa`). Pass `account: "<alias>"` on every `MULTI_EXECUTE_TOOL` call.

### Travis's account map (verified 2026-05-19)

| Toolkit | Default | Other |
|---|---|---|
| `gmail` | **`travis-personal-gmail`** (travispeng@gmail.com, ~66k msgs) | `travis-everestlabs` (travis@everestlabs.ai, ~659 msgs) |
| `googlecalendar` | **`travis-everestlabs`** (work primary) | `travis-personal` (personal primary + AI Squads cohort) |
| `googledrive` | **`travis-everestlabs`** (workspace `everestlabs.ai`) | `travis-personal` (personal Google) |
| `googledocs` | **`travis-everestlabs`** | `travis-personal` |
| `granola_mcp` | single account | — |
| `fireflies` | single account | — |

**Cardinal gotcha — default mismatch.** Gmail defaults to **personal**. Calendar / Drive / Docs default to **work**. Forgetting this and omitting `account` is the #1 wasted call across the AIOS. Always pass the alias explicitly.

### Managing accounts

Use `COMPOSIO_MANAGE_CONNECTIONS` for:
- `action: "list"` — list accounts for a toolkit (returns IDs, aliases, active status).
- `action: "add"` — initiate OAuth for a new account (returns a redirect URL to give Travis).
- `action: "rename"` — change an alias on an existing account.
- `action: "remove"` — delete an account.

After `add`, always follow with `COMPOSIO_WAIT_FOR_CONNECTIONS` to poll until the connection is `active` before executing tools.

---

## Cardinal workflow patterns

### 1. Search-then-execute

Composio's tool registry is huge — schemas aren't preloaded. The pattern is:

1. `COMPOSIO_SEARCH_TOOLS` with one or more `use_case` queries. Returns the relevant tool slugs **and full schemas inline** for the matches.
2. `COMPOSIO_MULTI_EXECUTE_TOOL` with `tool_slug` + `arguments` + optional `account`.

Critical: SEARCH_TOOLS often returns **recommended plans** and **known pitfalls** for the chosen tool. Read them before executing — they catch known bugs (e.g. response wrappers, pagination quirks, scope errors). Don't skip.

### 2. Multi-execute is parallel when independent

`COMPOSIO_MULTI_EXECUTE_TOOL` takes a `tools` array. Tools in the array run in parallel **if logically independent** — no shared inputs, no ordering. If tool B needs B's output to use as input, do it as two sequential calls.

Up to 50 tools per call. Batch aggressively when calling the same toolkit on different accounts (e.g. work + personal Gmail in one call).

### 3. Session continuity

`COMPOSIO_SEARCH_TOOLS` returns a `session.id` (e.g. `"lion"`). Pass it back as `session_id` on subsequent `MULTI_EXECUTE_TOOL` calls. Keeps the workflow correlated for telemetry and avoids re-discovery overhead.

For a brand-new workflow: `session: { generate_id: true }` on first SEARCH_TOOLS, then reuse the returned ID.

### 4. Oversized response handling

When response data may be large, set `sync_response_to_workbench: true` on `MULTI_EXECUTE_TOOL`. Inline preview still shows, full data saved to `/mnt/files/mex/*.json`.

For huge file processing:
- `COMPOSIO_REMOTE_WORKBENCH` — run Python on the workbench (e.g. parse a saved JSON file).
- `COMPOSIO_REMOTE_BASH_TOOL` — run bash on the workbench (e.g. `jq`, `rg`).

Used when a Granola transcript or Gmail bulk pull would otherwise overflow inline.

### 5. Schema discovery for one named tool

`COMPOSIO_GET_TOOL_SCHEMAS` with `tool_slugs: [...]`. Use when you already know the slug but need the parameter schema without re-running a SEARCH_TOOLS query.

---

## Critical gotchas

- **Don't omit `account` on multi-account toolkits.** Default isn't always work. See the cardinal-gotcha table above.
- **Don't invent toolkit slugs.** Always use exact slugs returned by `SEARCH_TOOLS`. Inventing a slug fails with `InputValidationError`.
- **Search before manage.** If you're considering `COMPOSIO_MANAGE_CONNECTIONS` to add a new account, run `SEARCH_TOOLS` first — the toolkit may already be connected.
- **`account_selection: "required"`** on the response means the toolkit has multiple accounts and you MUST pass `account`. Failing to do so will error.
- **Response shape varies per tool.** Don't assume `data.items` or `data.messages` etc. — read the structure_info / data_preview that SEARCH_TOOLS returns.
- **Pagination tokens are opaque.** Pass the exact `nextPageToken` string back. Don't construct, truncate, or guess.
- **Rate limits are per-toolkit, not per-Composio.** Gmail / Drive have their own quotas. Apply exponential backoff on 429.
- **Tool slugs vs internal IDs.** Account IDs look like `gmail_weakly-taa`; aliases look like `travis-everestlabs`. Both work as `account` value but aliases are stable across re-auth — prefer them.

---

## Per-toolkit notes

Compact reference for the Composio-backed Google Workspace toolkits. (Granola and Fireflies have their own files because their concepts — channel IDs, AskFred, etc. — are distinct enough to warrant standalone docs.)

### Gmail (`gmail`)

- **Default account is personal** (`travis-personal-gmail`, ~66k messages). Always pass `account: "travis-everestlabs"` for work.
- Query syntax: `from:`, `to:`, `subject:`, `label:`, `has:`, `is:`, `after:YYYY/MM/DD`, `before:YYYY/MM/DD`, AND/OR/NOT.
- **`is:` vs `label:`** — `is:snoozed`, `is:unread`, `is:read`, `is:starred`, `is:important`. `label:` only for user-created labels.
- **Project Jetstream label** ID: `Label_5261162509431064568`. Use `label_ids: ["Label_5261162509431064568"]` for clean Jetstream scope.
- Inventory pass: `verbose: false`, `include_payload: false`. Hydrate selected hits via `GMAIL_FETCH_MESSAGE_BY_MESSAGE_ID` with `format: "full"`.
- Bodies are base64url-encoded in `payload.parts`. Replace `-`→`+`, `_`→`/`, fix padding.
- `messages: []` is a valid no-result state. `nextPageToken: ""` means end-of-pagination — don't loop.
- Sort client-side by `internalDate` (ms epoch); results aren't sorted by recency.
- Tools not yet exercised: `GMAIL_GET_ATTACHMENT`, `GMAIL_SEARCH_PEOPLE`, write ops (`SEND`, `REPLY_TO_THREAD`, `CREATE_LABEL`).

### Google Calendar (`googlecalendar`)

- **Default account is work** (`travis-everestlabs`). Opposite of Gmail.
- Time ranges: RFC3339 with explicit offset. `"2026-05-19T00:00:00-07:00"` works; `"2026-05-19"` doesn't.
- `singleEvents: true` + `orderBy: "startTime"` for clean chronological listing with recurring events expanded.
- `GOOGLECALENDAR_GET_CURRENT_DATE_TIME` first when computing relative dates ("today", "this week") to avoid timezone drift.
- `EVENTS_LIST_ALL_CALENDARS` unifies primary + holidays + group calendars; with `response_detail: "minimal"` events may live under `summary_view` (don't treat empty `events` as "no events").
- All-day vs timed: all-day events have `start.date`; timed events have `start.dateTime`. Normalize before sorting.
- Use case: **pre-meeting briefer**. Get current time → list next-24-hours events on `travis-everestlabs` → extract `attendees[].email` → look up people / customers in the Personal Brain wiki.
- Use case: **Calendar ↔ Granola cross-check** — every event with `conferenceData` should produce a Granola recording. Missing recordings worth surfacing weekly.

### Google Drive (`googledrive`)

- **Default account is work** (`travis-everestlabs`, workspace `everestlabs.ai`).
- `GOOGLEDRIVE_FIND_FILE` is the comprehensive search tool. Supports name, fullText, mimeType, modifiedTime, parents, owners, sharedWithMe, starred, trashed.
- **`'root'`** for the root folder, not `'My Drive'`. `name = 'My Drive'` returns nothing.
- Wildcards (`*`) **not supported**. Use `contains`.
- Email searches: `"'user@example.com' in owners"` (or `in writers`, `in readers`). NOT `owner:user@example.com`.
- Boolean fields explicit: `sharedWithMe = true`, `trashed = false`, `starred = true`.
- `mimeType` decides the next step:
  - `application/vnd.google-apps.document` → use `GOOGLEDOCS_*` tools or export via `EXPORT_GOOGLE_WORKSPACE_FILE`.
  - `application/vnd.google-apps.spreadsheet` → export as CSV via `EXPORT_GOOGLE_WORKSPACE_FILE(mimeType: "text/csv")`.
  - `application/vnd.google-apps.presentation` → export as PDF / text.
  - `application/vnd.google-apps.folder` → use `LIST_CHILDREN_V2`.
  - Anything else → blob; use `DOWNLOAD_FILE`.
- Native Workspace files have `size: null` and `md5Checksum: null`. Classify by mimeType, not size.
- `fullText contains` queries can't be combined with `orderBy`. Sort client-side.
- `LIST_CHILDREN_V2` returns ChildReference objects (`id`, `childLink`, `selfLink`, `kind`) — not full File objects. Re-fetch via `GET_FILE_METADATA` or `FIND_FILE` for file-level details.

**Known Drive resources for Travis:**
- **Customer Deployment Dashboard** (Google Sheet): `1gMk0GkQqDjQ6MINHCkFHA-rco6ZddxbvlhbXSoNXz8M`. Export as CSV for snapshots in `Personal Brain/raw/data/`.
- **POC proposals** (Caglia / Republic / Circular Services): Google Slides, links in Apurba's May 13 "POC background materials" email. Export as plain text or PDF for wiki ingest.

### Google Docs (`googledocs`)

- `GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT` is the cleanest path for ingesting Doc content into the wiki. Configurable: `include_tables`, `include_footers`, `include_headers`, `include_footnotes`, `include_tabs_content`. Accepts either doc ID or full URL.
- `GOOGLEDOCS_GET_DOCUMENT_BY_ID` for full Docs API JSON (styling, comments, structure).
- `GOOGLEDOCS_SEARCH_DOCUMENTS` for Docs-only search (lighter weight than Drive's `FIND_FILE`).

### Google Sheets (via Drive's export tool)

- No dedicated `googlesheets` Composio toolkit slug at runtime — Sheets are reached through Drive.
- Export as CSV: `GOOGLEDRIVE_EXPORT_GOOGLE_WORKSPACE_FILE` with `mimeType: "text/csv"` and the file's Drive ID.
- For analytical data (Customer Deployment Dashboard, etc.), don't row-by-row ingest into the wiki. Snapshot, synthesize, cite the file ID and snapshot date.

### Notion (`notion`)

- **Single account** (`notion_letter-now`). Workspace = **"Travis's Notion"** (ID `5630c75c-46b3-81f5-9bda-000332fa0a04`). Owner travispeng@gmail.com. Composio integration connected 2026-04-06.
- **Permission model gotcha (cardinal):** the Composio integration only sees pages and databases that have been **explicitly shared** with the bot user in Notion. If a search comes back empty for content Travis knows exists, the integration probably wasn't added to that page yet — open the page → Share → connect → add Composio. Empty results ≠ empty workspace.
- **Search index lag.** Recently shared or created items may not appear in `NOTION_SEARCH_NOTION_PAGE` immediately. If a specific title search comes back empty, fall back to `query: ""` (empty) and filter client-side.

**Current shape of Travis's Notion (May 2026 — primarily personal):**

- ~6 databases, ~100+ pages (most are database rows).
- **"Academic Calendar"** (`2e10c75c-46b3-81cd-8e14-f42de1435cce`, 🌦️ icon). Top-level. Properties: `Name` (title), `Type` (select: Assignment / Assessment / Reading / Event), `Subject` (relation → Academic Database), `Due Date`, `Due Time`, `Effort (Hours)`, `Grade` (number), `Index` (select A through E), `HW` / `HW2` (URL), `Description`, **`Done` (checkbox)**. Created Jan 7 2026.
- **"Loose Tasks"** (`34f0c75c-46b3-817d-81f0-fe31e968ddb9`). Parent is a page (not workspace-level). Properties: `Name` (title), `Deadline` (date), `Notes` (rich_text), **`Status` (select: To-do / In progress / Blocked / Deferred / Done)**, `Thread` (select: Everest / Wayo / Big Scholars / Galguera / Cham / Stubbs / Naeem / TiECon / Ansara / Backpacking / LOV / Academic / Personal / Family / Self & spaces / Career / Admin / BigScholars). Created Apr 27 2026.
- **Academic Database** (related to Academic Calendar via `Subject`). Holds per-class records with `Teacher`, `Reading`, `Link 1`, `HW`, `Class Notes (Active)`.
- **No Everest content in Notion yet** (apart from one "Everest" thread tag in Loose Tasks for personal-side Everest items). Notion is currently a personal-leaning tool. If/when Travis brings work content over, this section should be updated.

**Tool decision tree:**

| If you need… | Use |
|---|---|
| Discover what's accessible (inventory) | `NOTION_SEARCH_NOTION_PAGE` with `query: ""` and `filter_value: "page"` or `"database"`. Paginate via `start_cursor` + `has_more`. |
| Page metadata only (properties, parent, archived state) | `NOTION_RETRIEVE_PAGE` with `page_id`. **Page IDs only — database IDs fail.** |
| Full readable page content as markdown | `NOTION_GET_PAGE_MARKDOWN` with `page_id`. One call; clean output. **Page IDs only.** |
| Full hierarchical block tree | `NOTION_FETCH_ALL_BLOCK_CONTENTS` with `block_id` and `recursive: true`. Check `data.recursion_info.block_limit_reached` / `depth_limit_reached` to verify completeness. |
| Database schema (property names + types) | `NOTION_FETCH_DATABASE` with `database_id`. Call this **before** querying — filter type keys must match the property's actual type. |
| Query database rows | `NOTION_QUERY_DATABASE` (simple) or `NOTION_QUERY_DATABASE_WITH_FILTER` (filtered/sorted). |
| Single row's properties | `NOTION_FETCH_ROW` with the row's page ID. |
| Cross-cutting workspace search by content | `NOTION_FETCH_DATA` with `fetch_type: "pages" | "databases" | "all"`. Use when `SEARCH_NOTION_PAGE` returns nothing. |

**Filter gotchas (databases):**

- **Property names are case-sensitive.** `"status"` ≠ `"Status"`.
- **Filter type key must match the schema type, not the property name.** A property named "Status" could be type `select` in one DB and type `status` (Notion's built-in workflow type) in another. Run `FETCH_DATABASE` first to confirm.
- **`title` is reserved.** Always refers to the database's built-in primary title column, regardless of what you renamed it to in the UI.
- **Select / status / multi-select option labels are case-sensitive**, including emoji prefixes. `"✅ Done"` ≠ `"Done"`. Mismatches return empty rather than erroring.
- **System timestamps use simplified format:** `{"created_time": {"on_or_after": "2024-01-01"}}` — not the verbose `{"timestamp": "created_time", ...}` shape.
- **Pagination cursors are opaque.** Pass `next_cursor` back exactly as returned. Stop on `has_more: false` or when cursor repeats.

**Page IDs vs database IDs — common 400.** `NOTION_GET_PAGE_MARKDOWN` and `NOTION_RETRIEVE_PAGE` accept page IDs only. `NOTION_FETCH_DATABASE` and the query tools accept database IDs only. Mixing them is the most frequent error mode.

**Saved queries — verified 2026-05-21:**

These have been run end-to-end and confirmed to return data. Drop in as the `arguments` to `NOTION_QUERY_DATABASE_WITH_FILTER`.

**1. All Academic Calendar items not done** (homework, assignments, readings, events — everything in the database without the `Done` checkbox ticked, oldest due first):

```json
{
  "database_id": "2e10c75c-46b3-81cd-8e14-f42de1435cce",
  "filter": { "property": "Done", "checkbox": { "equals": false } },
  "sorts": [ { "property": "Due Date", "direction": "ascending" } ],
  "page_size": 100
}
```

If you want **only coursework** (exclude `Event` type), wrap with an `and`:

```json
{
  "database_id": "2e10c75c-46b3-81cd-8e14-f42de1435cce",
  "filter": {
    "and": [
      { "property": "Done", "checkbox": { "equals": false } },
      {
        "or": [
          { "property": "Type", "select": { "equals": "Assignment" } },
          { "property": "Type", "select": { "equals": "Assessment" } },
          { "property": "Type", "select": { "equals": "Reading" } }
        ]
      }
    ]
  },
  "sorts": [ { "property": "Due Date", "direction": "ascending" } ],
  "page_size": 100
}
```

**2. All Loose Tasks not done** (everything not in the `Done` Status — covers To-do / In progress / Blocked / Deferred — oldest deadline first):

```json
{
  "database_id": "34f0c75c-46b3-817d-81f0-fe31e968ddb9",
  "filter": { "property": "Status", "select": { "does_not_equal": "Done" } },
  "sorts": [ { "property": "Deadline", "direction": "ascending" } ],
  "page_size": 100
}
```

Loose Tasks deadlines are often null (backlog items without a date). Notion returns null-deadline rows mixed in; sort by `last_edited_time` instead if you want most-recently-touched first.

**Common refinements (paste-ready):**

- Scope Loose Tasks to one Thread (e.g., Everest-side personal): add to the filter — `{ "property": "Thread", "select": { "equals": "Everest" } }`.
- Coursework due in the next 7 days: replace the Due Date sort with a filter — `{ "property": "Due Date", "date": { "next_week": {} } }`.
- Overdue coursework: `{ "property": "Due Date", "date": { "before": "<today ISO>" } }` combined with `Done = false`.

**Write operations (not yet exercised):** Notion exposes write tools (`NOTION_CREATE_PAGE`, `NOTION_UPDATE_PAGE`, `NOTION_APPEND_BLOCK_CHILDREN`, etc.) via Composio. AIOS is read-only by default; only use writes when explicitly authorized.

---

## Read-only by default

The AIOS doesn't write to Composio toolkits unless Travis explicitly authorizes it for a specific task. That means:

- Don't send Gmail messages, create calendar events, modify Drive files, edit Docs, or write to Granola without express permission.
- `COMPOSIO_MANAGE_CONNECTIONS` write actions (`add` / `rename` / `remove`) are also gated — confirm with Travis before changing connection state.

Reads are free. Writes require sign-off.

---

## Confidentiality cross-reference

Most Everest content surfaced via Composio (emails, calendars, Drive docs, Granola transcripts) is internal. When derived content goes into the Personal Brain wiki, default to `confidential: internal` on the resulting page unless the source is clearly public.

---

## Tools not yet exercised across the umbrella

- `COMPOSIO_MANAGE_CONNECTIONS` `add` flow — used briefly during onboarding; not currently a routine AIOS action.
- New toolkits Travis has connected but the AIOS hasn't queried (`apify`, `exa`, `firecrawl`, `github`, `linkedin`, `notion`, `supabase`, etc.) — document per-toolkit reference docs when first exercised.
- `COMPOSIO_REMOTE_WORKBENCH` for non-trivial Python pipelines on large Composio response files — useful pattern when a one-shot query returns more than fits inline.
