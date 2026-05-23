---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

# Granola MCP — reference for the AIOS

Granola is reached through the Composio MCP server (`mcp__mcp-router__COMPOSIO_*`). This file is not a tool catalog (the schemas are self-documenting via `COMPOSIO_SEARCH_TOOLS`) — it's a workflow reference for the things Travis actually does with Granola.

**Connection:** single account, `granola_mcp_gainly-micro`, no alias needed.

**Tied to:** the [[Personal Brain wiki]] INGEST workflow at `/Users/tpeng2025/Documents/Personal Brain/CLAUDE.md` §4a. Granola is the upstream source; the wiki is the destination.

---

## When to use which tool

Four tools, picked by question shape, not by name. Always favor the one closest to the natural question.

| If the question is… | Use | Why |
|---|---|---|
| "What did we say / decide / agree about X?" — open-ended, across meetings | `GRANOLA_MCP_QUERY_GRANOLA_MEETINGS` | RAG with citations back to source meetings. Best default. |
| "List meetings in <window>" — scanning the calendar of conversations | `GRANOLA_MCP_LIST_MEETINGS` | Returns titles + IDs + dates only. Cheap. |
| "Give me the full notes / summary for these specific meetings" (have IDs) | `GRANOLA_MCP_GET_MEETINGS` | Up to 10 meeting IDs per call. Returns private notes + AI summary + attendees. |
| "Quote the exact words from one meeting" | `GRANOLA_MCP_GET_MEETING_TRANSCRIPT` | Verbatim transcript. One meeting per call. |

**Default chain when ingesting a meeting into the wiki:** `QUERY` (to find the right meeting if title is fuzzy) → `LIST` to confirm + grab the ID → `GET_MEETINGS` for the AI summary → `GET_MEETING_TRANSCRIPT` for the raw transcript that goes into `raw/meetings/`.

---

## Time-range parameter cheatsheet (LIST_MEETINGS)

- `this_week`, `last_week`, `last_30_days` — relative, easiest.
- `custom` with `custom_start` + `custom_end` (ISO `YYYY-MM-DD`) — for older history.
- The tool returns ~50–100 meetings per call without complaining; older meetings carry the same shape.

**Gotcha:** Granola dates are returned in PDT (the server's reported timezone, e.g. "May 13, 2026 2:30 PM PDT"). Composio's session metadata exposes current UTC. Reconcile when computing "this week."

---

## QUERY behavior worth knowing

- Response includes inline citation links like `[[0]](url)` pointing back to specific Granola meeting notes. **Preserve these in any report.**
- Queries can be scoped to specific meetings by passing `document_ids: [uuid, uuid, ...]`. Useful for "summarize this specific stretch of meetings" without contamination from unrelated conversations.
- Querying for "what has X assigned me" or "what's open on Y project" pulls a surprisingly complete operational picture — better than reading any single transcript, because Granola RAGs across all relevant meetings and synthesizes.

---

## INGEST workflow (Granola → Personal Brain wiki)

The wiki's INGEST workflow lives in `/Users/tpeng2025/Documents/Personal Brain/CLAUDE.md` §4a. Granola is upstream of step 1. Concretely:

1. **Identify the meeting.** If the title is exact, jump to LIST → grab ID. If fuzzy, run QUERY to surface candidate IDs first.
2. **Fetch transcript + AI summary** in one parallel call: `GET_MEETING_TRANSCRIPT` (for `raw/meetings/`) + `GET_MEETINGS` (for orientation).
3. **Write the raw file** at `Personal Brain/raw/meetings/YYYY-MM-DD-<short-slug>.md`. Include: title, date/time, attendees, Granola meeting UUID, Granola AI summary (for orientation only), then verbatim transcript. `raw/` is immutable after this — never edit.
4. **Run the wiki INGEST** per the wiki's CLAUDE.md §4a steps 2–9: discuss takeaways, create the `wiki/sources/<slug>.md` page, update touched people/concepts/techniques/tools/customers, append to `wiki/log.md`, update `wiki/index.md`.

**Cite the Granola UUID** in the raw file's frontmatter or first line. It's the cheapest way to re-fetch the source if the transcript ever needs to be regenerated.

---

## Naming conventions for ingested files

- **Raw transcript file:** `raw/meetings/YYYY-MM-DD-<participants-or-topic>.md`. Examples: `2026-03-11-alfiya-salesforce-cleanup.md`, `2026-05-13-apurba-onboarding.md`.
- **Wiki source page:** mirror the raw filename in `wiki/sources/<same-slug>.md` per the wiki's schema §2.
- Slug is all-lowercase, hyphenated. No spaces, no underscores.

---

## Useful repeat queries

Save these as starting points. Adjust the date scope or subject as needed.

- **"What has Apurba assigned me to work on for the Navigator product and the POCs? List concrete deliverables and deadlines."** — pulls the full POC + deliverables + deadlines rundown across all Apurba meetings in scope. Citation-backed.
- **"Find the meeting with <person> about <topic>. Return meeting ID, date, and a one-line summary."** — fastest way to locate a meeting when only the topic is remembered.
- **"What open follow-ups did I leave on <customer> across recent calls?"** — surfaces commitments by customer.
- **"Compare what <person A> said about <topic> versus <person B> across meetings."** — feeds a comparison page candidate for the wiki.

---

## Confidentiality cross-reference

Most Everest meeting content surfaced via Granola is internal (customer names, pricing, personnel, deal state). When the resulting wiki source page is created, default to `confidential: internal` per the wiki's CLAUDE.md §3.1 unless the meeting is clearly public-facing material. Re-read the wiki's confidentiality rules before each ingest — the wiki schema evolves.

---

## Tools not yet exercised

- Multi-meeting queries with `document_ids` scoping — not yet hit; document a working example once one is produced.
- Whether `last_30_days` includes the current day — empirically yes, but worth noting if a meeting is missing.
