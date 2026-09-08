# Gmail — Connection Guide

**Domain:** 4 — Communication
**Mechanism:** `mcp` — Gmail MCP server, session-scoped OAuth (already authorized).
**Account:** `roman.brandon503@gmail.com`
**Last checked:** 2026-09-06 (`list_labels` returned 95,003 inbox messages, 39,791 unread)

## What's available

Read: `search_threads`, `get_thread`, `get_message`, `list_labels`, `list_drafts`,
`get_draft`.
Write (draft only, safe): `create_draft`, `update_draft`.
Write (side-effecting — **needs Brandon's explicit approval before calling**, per his
standing multi-AI norms — "explicit approval required before anything that ... sends
communications"): `send_message`, `reply`, `forward`.
Organization: `label_message`/`label_thread`, `unlabel_*`, `create_label`,
`update_label`, `delete_label`, `mark_*_spam`, `trash_*`/`untrash_*`.

User labels currently on the account: `Personal`, `Receipts`, `Work`, `Junk`.

## Common queries

- **"Anything urgent in my inbox?"** → `search_threads` scoped to `INBOX` +
  `IMPORTANT`/`UNREAD`, summarize subjects/senders — don't dump raw bodies unless asked.
- **"Draft a reply to X"** → `create_draft`, never `send_message`, until Brandon
  reviews and says to send.
- **"What's in Receipts/Work/Personal?"** → filter by the matching `labelId`
  (`Label_2`/`Label_4`/`Label_1`).

## Guardrails

- 39k+ unread inbox messages — never fetch/summarize the whole inbox by default; scope
  by label, sender, date range, or search query the way Brandon actually asked.
- No sending, forwarding, replying, trashing, or spam-marking without explicit
  confirmation in the moment — a past approval doesn't carry forward to new messages.
