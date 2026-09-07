# Obsidian Vault — Connection Guide

**Domain:** 7 — Knowledge / files
**Mechanism:** `filesystem` — direct local read access, no auth, no MCP server needed.
**Path:** `C:\Users\roman\Claude Main\content-brand\Obsidian Vault`
**Last checked:** 2026-09-06

This is Brandon's durable cross-project knowledge base — decisions, architecture
notes, model/tool routing, and session digests that outlive any single repo. It
complements (doesn't replace) per-repo `PROJECT-STATE.md` files, which hold live
day-to-day task state.

## Entry points

- `Home.md` — index, explains the division of labor across memory systems (Honcho /
  this vault / PROJECT-STATE.md) and links every top-level folder.
- `About Brandon.md` — canonical cross-project profile: who Brandon is, how he works
  (ADHD-aware preferences), dev-stack defaults, communication style, multi-AI
  collaboration norms. Source for `context/about-me.md` in this AIOS.

## Structure

| Path | Contents |
|---|---|
| `00-Inbox/` | Unsorted capture, triage into the right folder later |
| `01-Projects/<name>/<name> MOC.md` | One MOC (Map of Content) per active project — start any project-specific lookup here. Projects: Home-Base, LYTW, SLASH, Loop, Portfolio, Main-Bro |
| `02-Decisions/` | Cross-project conventions promoted out of a single project's PROJECT-STATE.md — e.g. `Development Workflow Conventions.md` |
| `03-AI-Workflow/` | Zero-cost multi-model routing lane matrix (`AI Model Routing MOC.md`) |
| `04-Sessions/` | Dated session digests — one note per significant work session, linking what changed |
| `05-Notes and Thoughts/` | Looser, stream-of-consciousness capture; tentative, not locked decisions |

## How to query it

No API — read directly with filesystem tools (`Read`/`Glob`/`Grep`, or the platform's
equivalent) against the path above. Common patterns:

- **"What's the current state of project X?"** → read `01-Projects/X/X MOC.md`, follow
  its linked notes (locked decisions, rejected ideas, architecture).
- **"Has this idea been tried before?"** → grep the vault for the keyword; check any
  hit's `#rejected` tag before proposing it again.
- **"What did we decide about Y, and why?"** → check `02-Decisions/` first (things that
  apply beyond one project), then the relevant project's MOC.
- **"What happened in the last session?"** → most recent file in `04-Sessions/` by
  date in the filename.

## Conventions to respect

- Tags (`#decision`, `#rejected`, `#architecture`, `#session`) mark note type — use
  them to filter search results, not just filenames.
- `[[wikilinks]]` form the actual graph — a note's neighbors often matter as much as
  its own content.
- Current user instructions in a live conversation outrank stale vault notes, especially
  ones in `05-Notes and Thoughts` (tentative) vs. `02-Decisions` (locked).
- This is Brandon's personal knowledge base — read-only for this AIOS. Don't write back
  into it from AIS-OS skills; if something belongs there, tell Brandon and let him (or
  a Main-Bro-side tool) add it.
