---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

# Fireflies MCP — reference for the AIOS

Fireflies is reached through the Composio MCP server (`mcp__mcp-router__COMPOSIO_*`). This file is a workflow reference for the things Travis actually does with Fireflies — not a tool catalog (those schemas are discoverable via `COMPOSIO_SEARCH_TOOLS`).

**Connection:** single account, `fireflies_relink-spacer`, no alias needed.

**Tied to:** the Personal Brain wiki INGEST workflow at `/Users/tpeng2025/Documents/Personal Brain/CLAUDE.md` §4a. Fireflies is the upstream source (parallel to Granola); the wiki is the destination.

**Channel IDs (Travis's setup):**

| Channel ID | What it holds |
|---|---|
| `6a0c1cec7610454b44024df2` | **Everest channel** — work meetings (~5 in Apr–May 2026 inventory) |
| `6a0c1e3554702d1c5aa6d4e3` | Personal / family — Family Dinner, Project House Cleanup, etc. |
| `6a0c1e84ffa599853238be96` | Date-stamped catch-all — auto-titled recordings like `"Apr 30, 09:35 AM"` |
| `[]` (empty channels array) | One-off recordings — Game Night, Roblox Night, ad-hoc captures |

---

## When to use which tool

Four tools matter for the wiki workflow. Picked by question shape:

| If the question is… | Use | Why |
|---|---|---|
| "What did we say / decide / agree about X?" — open-ended, with citations | `FIREFLIES_CREATE_ASK_FRED_THREAD` with `channel_ids: ["6a0c1cec7610454b44024df2"]` to scope to Everest | Natural-language query across meetings. Continue threads with `FIREFLIES_CONTINUE_ASK_FRED_THREAD`. Best default. |
| "List meetings in <date range>" — inventory | `FIREFLIES_GET_TRANSCRIPTS` with `from_date` + `to_date` (ISO 8601 with timezone) | Metadata only. **No channel filter on this tool** — filter client-side on `channels[]`. |
| "Get the transcript for one meeting (have the ID)" | `FIREFLIES_GET_TRANSCRIPT_BY_ID` with `include_sentences: true` | Verbatim sentences with speaker labels + timestamps. |
| "Find a meeting whose title I don't quite remember" | `FIREFLIES_CREATE_ASK_FRED_THREAD` ("find the meeting about X — return ID and date") | Returns IDs you can pass to GET_TRANSCRIPT_BY_ID. |

**Default chain when ingesting one Fireflies meeting into the wiki:**
LIST_TRANSCRIPTS over a date window → filter client-side on `channels[0].id === "6a0c1cec7610454b44024df2"` → pick the one → GET_TRANSCRIPT_BY_ID with `include_sentences: true` → format speaker labels → write `raw/meetings/<slug>.md`.

---

## Critical gotchas

These bite repeatedly if not internalized.

- **Channel filter only works on AskFred.** `FIREFLIES_GET_TRANSCRIPTS` has no channel parameter. Filter client-side on each transcript's `channels[]` array (length 0 or 1).
- **Response is nested deep.** `FIREFLIES_GET_TRANSCRIPT_BY_ID` returns the transcript at `data.outputs.data.transcript`, not at the top level. `data.transcripts` for LIST_TRANSCRIPTS.
- **Auto-titled meetings are common.** Many entries are titled `"Apr 30, 09:35 AM"` — Fireflies doesn't always derive a meaningful title. Open the transcript, derive a descriptive slug from content, and use *that* for `raw/meetings/YYYY-MM-DD-<topic>.md` instead of the auto-title.
- **`sentences` and `attendees` can be null.** Always defensive-check. If sentences is null, the transcript may still be useful via the summary, but for the raw file you want verbatim — skip and flag.
- **`summary.action_items` may be a single newline-delimited string, not a list.** Split by `\n` rather than iterating.
- **`from_date` / `to_date` need ISO 8601 with timezone.** `"2026-04-01T00:00:00Z"` works; `"2026-04-01"` does not.
- **Time fields are UTC.** Convert to PDT for display in raw files (subtract 7 hours during DST). The `dateString` field is already ISO.
- **`duration` appears to be in minutes** (decimal), not seconds. Verify on a known-length meeting before relying on it.
- **Skip transcripts with non-`processed` status.** `meeting_info.summary_status` of `"skipped"` or `"failed"` means partial / missing content. Filter to `"processed"` only before fetching.
- **Pagination uses `skip` + `limit`; max limit is 50.** 429s on rapid requests — apply exponential backoff, respect `Retry-After`.

---

## INGEST workflow (Fireflies → Personal Brain wiki)

Same shape as the Granola flow. The wiki's INGEST is at `/Users/tpeng2025/Documents/Personal Brain/CLAUDE.md` §4a.

1. **Identify the meeting.** If title is known: LIST_TRANSCRIPTS over the date window, filter for Everest channel, match. If fuzzy: AskFred to surface a candidate ID by content.
2. **Fetch the verbatim transcript.** `GET_TRANSCRIPT_BY_ID` with `include_sentences: true`. The `sentences` array has `{speaker_name, text, start_time, end_time}` per line.
3. **Format speaker labels.** Fireflies speakers may be named (`"Apurba"`, `"Travispeng"`) or anonymized (`"Speaker 1"`, `"Speaker 2"`). Preserve exactly as returned — don't relabel.
4. **Write the raw file** at `Personal Brain/raw/meetings/YYYY-MM-DD-<slug>.md`. Include: title (descriptive, not the auto-title if auto), date/time (converted to PDT), attendees (from `meeting_attendees` if populated, otherwise `speakers[]`), Fireflies transcript ID, then verbatim transcript reconstructed from the sentences array. `raw/` is immutable after write.
5. **Run the wiki INGEST** per CLAUDE.md §4a steps 2–9: discuss takeaways, create `wiki/sources/<slug>.md`, update touched people/concepts/techniques/tools/customers, append to `wiki/log.md`, update `wiki/index.md`.

---

## Naming conventions for ingested files

- Raw transcript file: `raw/meetings/YYYY-MM-DD-<participants-or-topic>.md`.
- Wiki source page: mirror the raw filename in `wiki/sources/<same-slug>.md`.
- Slug is all-lowercase, hyphenated. No spaces, no underscores.
- For auto-titled Fireflies meetings, derive the slug from transcript content — don't preserve the date-stamp title.

---

## Useful repeat queries

- **"What was discussed in the Everest channel about <topic> in <date range>?"** — AskFred with `channel_ids: ["6a0c1cec7610454b44024df2"]` and the date filter. Channel scoping prevents personal-channel contamination.
- **"Find the meeting where <event happened>"** — AskFred natural-language; returns IDs to pass to GET_TRANSCRIPT_BY_ID.
- **"List all my Everest-channel meetings in May."** — GET_TRANSCRIPTS for May, then filter on `channels[0].id`.
- **"Compare what was decided across these two Avinash meetings."** — AskFred with `transcript_ids: [id1, id2]` for scoped multi-meeting synthesis.

---

## Fireflies vs Granola — when to use which

- **Granola** is the primary capture for Everest meetings as of May 2026. Better LLM-derived titles, better summaries, no channel structure needed.
- **Fireflies** catches what Granola misses for Everest work (some Zoom calls — architecture + engineering sessions in May 2026 appear here but not in Granola). Channel-based filtering is the discriminator.
- **Same meeting in both** is possible. Default to Granola as canonical when overlap is detected; ingest the Fireflies version only if it has unique value (e.g., better speaker labeling, a longer recording).
- **For backlog ingest:** check both sources for each date. Cross-reference the inventory before writing a raw file to avoid double-ingesting the same meeting under different slugs.

---

## Confidentiality cross-reference

Same rule as Granola. Everest meeting content surfaced via Fireflies → default `confidential: internal` on the resulting wiki source page unless the meeting is clearly public-facing.

---

## Tools not yet exercised

- `FIREFLIES_GRAPHQL_QUERY` — read-only GraphQL passthrough. Powerful escape hatch for queries the named tools don't cover; document a working example once one is needed.
- AskFred with `transcript_ids` for scoped multi-meeting synthesis — useful for comparison-page candidates in the wiki.
- `FIREFLIES_CREATE_BITE` — extract a video/audio clip from a transcript range. Not part of the wiki path but useful for sharing soundbites.
- `FIREFLIES_GET_USERS` — resolve team members' emails if the channel filter alone isn't enough.
