# AIOS Task System

The operating manual for Travis's task + project management. A fresh chat session reading this file, querying Notion, and reading the current week's plan should have everything needed to work on any open task without further context.

## Purpose

This system is designed around one principle: **cold-start function**.

A new session (no prior context) must be able to:
1. Read this file → understand the system
2. Query the Notion Tasks DB → see what's open
3. Follow a Task's `Project` relation → get surrounding context
4. Follow a Task's `Related tasks` → see connected work
5. Read the current week's plan in `weekly-plans/` → know *when* and *why* the task is scheduled
6. Execute the work and update the Task's Status + Update log

If a fresh session can't do this, the system has failed at its primary purpose.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Source of truth — what the work IS + how to do it         │
│                                                            │
│  Notion: Projects DB ─── parent ───┐                       │
│                                    ▼                       │
│  Notion: Tasks DB ─────────────────┘                       │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Source of truth — WHEN work is scheduled + WHY            │
│                                                            │
│  Repo: weekly-plans/{YYYY-MM-DD}.md                        │
│  (one file per week, snapshot + append-only change log)    │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Operating manual + supporting files                       │
│                                                            │
│  references/aios-task-system.md  ← this file               │
│  links.md                        ← link registry by project│
└────────────────────────────────────────────────────────────┘
```

## Notion: Projects DB

Container for workstreams that **live ≥1 month and have multiple related tasks**. Shorter / smaller workstreams are just tasks (optionally with a parent project).

### Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Name | title | yes | Project name |
| Status | select | yes | `Active` · `Parked` · `Done` · `Reevaluating` |
| Parent project | relation → Projects (self) | optional | Max 2 levels of nesting. Top-level projects have none. |
| Dependencies | relation → Projects (self) | optional | Cross-pillar sequencing (what must finish before this can move). Different from Parent (containment) vs Dependencies (sequencing). |

### Page body template

```markdown
## Purpose
One paragraph — why this project exists, what problem it solves, what success looks like at the end.

## Scope
- In: what this project covers
- Out: what's intentionally NOT in scope

## Definition of done
Concrete completion criteria. Not "make Navigator better" — instead "all 5 Internal Rollout steps shipped + 3 internal stakeholders onboarded + first wave external touch sent"

## Stakeholders
Who's involved, what role, what they need from you, what you need from them

## Sources
References that informed or birthed this project. Meetings, docs, articles, conversations. Not load-bearing — background context only.

## Open questions
Unresolved issues blocking decisions; flagged so future-you (or a fresh chat) sees them surfaced

## Decision log
Append-only. Decisions about the project itself (scope, approach, choices).
- YYYY-MM-DD: <what was decided>
  Why: <reason>

## Linked references
External docs, dashboards, repos, slides
```

## Notion: Tasks DB

Container for concrete work items. Consolidates what used to be Academic Calendar + Loose Tasks.

### Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| Name | title | yes | Concrete action |
| Status | select | yes | `To-do` · `In progress` · `Blocked` · `Done` · `Deferred` |
| Project | relation → Projects | optional | Parent workstream. Hierarchy / pillar is inferred by following the Project's Parent chain. |
| Deadline | date (no time) | optional | Only set when a real deadline exists. Never invent. |
| Due Time | rich_text | optional | Separate from Deadline because Notion's datetime field breaks calendar view rendering. `8am`, `11:59pm`. |
| Type | select | optional | `Deep work` · `Quick`. Deep work = >30 min; Quick = <30 min. |
| Context links | URL list | optional | Direct refs the task needs (visible on calendar view for quick access) |
| Related tasks | relation → Tasks (self) | optional | Captures task-to-task relationships ONCE. Notion auto-mirrors. Use for "blocks", "informs", "shares dependency on X" — prose semantics in body. |

### Page body template

```markdown
## Goal
One sentence — what done looks like for THIS task.

## Context
Relevant background a fresh chat needs to do this task without re-reading the whole project. Why this matters now.

## Steps (optional, for non-trivial)
Brief outline. Skip if the task is simple.

## Blocked by
Only if Status=Blocked. What's blocking, when it should clear.

## References
Inline links — docs, meeting notes, prior decisions.

## Update log
Append-only.
- YYYY-MM-DD HH:MM: <what changed / what was done>
```

## Repo: weekly-plans/

One markdown file per week. Captures the planning *rationale* — the layer of information that's about scheduling decisions, not about the work itself.

### File naming
`weekly-plans/{YYYY-MM-DD}.md` where the date is the Monday of the week.

### File shape

```markdown
# Week of {Monday date}

## Anchors (locked dates)
Calendar items + deadlines that shape the week.

## Plan (snapshot — written by /plan-my-week)

### {Weekday} {Month} {Day}
- {Task name}  [link to Notion task]
  Why this slot: ...

(repeat per day)

## Reasoning / context that didn't fit elsewhere
Free-form. Week's center of gravity, load-bearing pieces, squeeze points.

## Change log (append-only mid-week)
- YYYY-MM-DD HH:MM: <what changed>
  Why: <reason>
```

A fresh agent reads this file alongside the Notion Tasks DB to understand both *what* is on the plate today AND *why* it landed today.

## Cold-start protocol

The exact sequence a fresh agent runs to pick up Travis's TODO list:

1. **Read this file** (`references/aios-task-system.md`) — understand the system.
2. **Read the current week's plan file** (`weekly-plans/{this Monday}.md`) — see what's scheduled today + this week's anchors + reasoning.
3. **Query Notion Tasks DB** — filter `Status` in `{To-do, In progress, Blocked}` AND `Deadline ≤ today + 7 days` (or as needed). Surface what's open.
4. **For each task of interest**:
   - Read task body — Goal, Context, Steps
   - Follow `Project` relation → read project body — Purpose, Scope, DoD, Stakeholders, Sources, Open questions, Decision log
   - Follow `Related tasks` if any — see connected work
   - Follow `Context links` — direct references
5. **Cross-reference week plan** — confirm scheduling rationale ("why is this on Tuesday")
6. **Act**. When done, update task Status + append to task body's Update log. If the scheduling changes, append to the current week plan's Change log.

## Conventions

### Project vs task
- **Project**: workstream that lives ≥1 month AND has multiple related tasks under it
- **Task**: concrete action item (or a short-lived multi-step deliverable)
- Examples that ARE projects: Caglia, Navigator, House Cleanup, Family Finances, NEU subjects
- Examples that are NOT projects (tasks instead): Central Compute certification work, Newsletter w/ Makenna, Vendor list, Profile cluster

When in doubt: smaller and shorter → task. Bigger and longer → project.

### Parent project depth
Max 2 levels of nesting. Top-level → sub-project. No deeper.

- Top-level: `Everest`, `Career`, `Family`, `Personal`, `Academic`, `Admin`
- Sub-projects: nest under one top-level (e.g., `Caglia` parent=`Everest`)

If a 3rd level feels needed, the structure is wrong. Either:
- Flatten — the deepest item becomes a sub-project under the top-level
- Or break the middle level into multiple sibling sub-projects

### Subjects (when school active)
- "Northeastern" is **not** a separate project layer. NEU subjects (ENTR2303, INMI0300, etc.) are sub-projects directly under `Academic`.
- Class metadata (professor, room, schedule) lives in the subject's page body, not in a separate Subjects DB.

### Deadlines
- Never invent. Only set when Travis named a date or one is externally imposed.
- For things that feel like they need a deadline but don't have one: surface that as a question; don't bake one in.

### Type values
- `Deep work` = anything >30 min
- `Quick` = anything <30 min
- That's it. No prep/errand/group distinctions.

### Decision log vs Schedule log
Two different "decision" layers, intentionally separate:
- **Project body's Decision log** = decisions about *the work itself* (scope, approach, choices about how to do it)
- **Weekly plan's Change log** = decisions about *when to do it* (timing, deferral, sequencing)

### Recurring tasks
Recurring projects (e.g., belt-lacing daily, weekly newsletter) spawn fresh dated tasks each occurrence rather than maintaining one persistent task with reset Status. Better audit trail.

## Project taxonomy (initial state)

### Top-level projects
- `Everest`
- `Career`
- `Family`
- `Personal`
- `Academic`
- `Admin`

### Sub-projects (as of system creation)
- Under Everest: `Caglia`, `Navigator`
- Under Family: `House Cleanup`, `Family Finances`
- Under Personal: `Personal Enrichment`
- Under Academic (NEU subjects, Spring 2026): `ENTR2303: Marketing for Startups`, `PHIL3343: Existentialism`, `ACCT1201: Accounting`, `ECON1116: Microecon`, `Everest Labs (New Venture Development)`, `INMI0300`

The taxonomy is dynamic. Projects come and go — add or archive as workstreams evolve.

## Migration approach (from old system)

This system replaces the old Academic Calendar + Loose Tasks + Subjects DBs. Migration is **organic, not bulk**:

1. New tasks get created directly in the new Tasks DB.
2. Old items get migrated by hand when they become relevant — they're either re-created with their new project context OR they're stale enough to drop entirely.
3. Old DBs (Academic Calendar, Loose Tasks, Subjects) stay alive until they're empty of anything load-bearing, then archived.
4. Galguera, LinkedIn post Sales/Ops → GTM = both already Done — closure happens in old DB as cleanup, no migration needed.

No bulk import. Quality over completeness.

## What this system intentionally does NOT have

- **No "future container DBs"** placeholder for hypothetical extension. If a new entity type emerges (e.g., Clubs), it lives as a project in Projects DB.
- **No Schedule Log DB**. Planning rationale lives in `weekly-plans/{YYYY-MM-DD}.md` files in this repo, not in Notion.
- **No Type=Subtask**. Subtasks are handled by either making a task more complex (extra detail in body) or breaking it into multiple peer tasks. Self-relation on Tasks isn't a Parent-Child hierarchy — it's a Related-task relation.
- **No Owner field**. Travis is the implicit owner. Rare exceptions (external owner) live in the task body's Context.
- **No Tags field**. Cross-cutting categorization that doesn't fit Pillar-via-Project goes in task or project body prose.
- **No Pillar/Sub-pillar enum field**. Pillars ARE the top-level projects. Adding a new pillar = adding a new top-level project, not changing the schema.

These omissions are intentional. They keep the system small and lived-in. Add back only when a real, recurring need surfaces.

## Open / TBD

- **Backpacking Club** — currently misfiled in Subjects DB. Wind-down workstream. Needs to be created as a sub-project (parent TBD: Career? Personal?). Travis to confirm placement.
- **BigScholars** — also misfiled in Subjects DB. Parked workstream. Will be reevaluated. When unparked, becomes a top-level project (`BigScholars`) or sub-project under Career.
- **Fall 2025 NEU subjects** — not in Subjects DB. Travis to name if he wants them captured for historical purposes.
- **Notion DB IDs** — to be filled in after Projects DB and Tasks DB are created in Notion.

## Notion DB IDs

- **Projects DB** (`Projects`): `3690c75c-46b3-81ed-ae3a-eeb3be8d1303` — lives inside `Life Hub` page (`8280c75c-46b3-8268-8b42-01cd65b1f230`)
- **Tasks DB** (`Life Calendar`): `bfc0c75c-46b3-837b-9676-01cbead97b7d` — lives at workspace top-level

## Initial Project rows (created 2026-05-22)

### Top-level
- **Everest** 🏔️ — `3690c75c-46b3-81df-ad1d-d593f664365b`
- **Career** 💼 — `3690c75c-46b3-81fb-8bcf-d31a42dcea71`
- **Family** 👨‍👩‍👧 — `3690c75c-46b3-8124-97ec-edf7b2b1db9d`
- **Personal** 🌿 — `3690c75c-46b3-817d-9644-e4a11f1d7b36`
- **Academic** 🎓 — `3690c75c-46b3-8138-8c65-e03243cbaf8d`
- **Admin** 🗂️ — `3690c75c-46b3-81a2-888e-f61b56cb5a27`

### Sub-projects
- **Caglia** 🏭 — `3690c75c-46b3-81f2-922b-c2193a6fcb89` (parent: Everest)
- **Navigator** 🧭 — `3690c75c-46b3-8118-a02b-f5c4f120edbf` (parent: Everest)
- **House Cleanup** 🏡 — `3690c75c-46b3-8103-a049-d973c243effd` (parent: Family)
- **Family Finances** 💰 — `3690c75c-46b3-8191-a31a-c1be78806dec` (parent: Family)
- **Personal Enrichment** 📚 — `3690c75c-46b3-81d7-b6d9-fb970dd90e39` (parent: Personal)
- **ENTR2303: Marketing for Startups** 📈 — `3690c75c-46b3-814a-9a9b-d3cdaff8d287` (parent: Academic, Status: Done)
- **PHIL3343: Existentialism** 🕯️ — `3690c75c-46b3-81d0-a9be-dea87fc7a538` (parent: Academic, Status: Done)
- **ACCT1201: Accounting** 🧾 — `3690c75c-46b3-8100-a235-cec64b9a30df` (parent: Academic, Status: Done)
- **ECON1116: Microecon** ⚰️ — `3690c75c-46b3-81bd-9549-c596aa13a1ac` (parent: Academic, Status: Done)
- **INMI0300** 🔬 — `3690c75c-46b3-81a9-afea-e9af2acf2a81` (parent: Academic, Status: Reevaluating)

---

*This file is the cold-start handshake. Keep it accurate. When schema or convention changes, update this file in the same commit.*
