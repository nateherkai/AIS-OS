# Google Calendar — Connection Guide

**Domain:** 3 — Calendar
**Mechanism:** `mcp` — Calendar MCP server, session-scoped OAuth (already authorized).
**Account:** `roman.brandon503@gmail.com`
**Last checked:** 2026-09-06 (`list_calendars` returned the personal calendar plus the
US Holidays calendar)

## Calendars

- `roman.brandon503@gmail.com` — primary personal calendar
- `en.usa#holiday@group.v.calendar.google.com` — US Holidays (read-only, informational)

## What's available

Read: `list_events`, `get_event`, `search_events`, `suggest_time`.
Write (**needs Brandon's explicit approval before calling** — creating/editing/
deleting events or responding to invites are account-changing actions per his standing
norms): `create_event`, `update_event`, `delete_event`, `respond_to_event`.

## Common queries

- **"What's on my calendar tomorrow?"** → `list_events` scoped to the date range,
  primary calendar only unless holidays are relevant.
- **"When am I free this week?"** → `suggest_time` against the primary calendar.
- **"Put X on my calendar"** → confirm the exact title/time/duration with Brandon
  before `create_event` — don't guess at details he didn't state.

## Guardrails

- Never create, move, or delete an event, or accept/decline an invite, without
  explicit in-the-moment confirmation — matches the send/publish/delete approval rule
  applied to Gmail.
