# weekly-plans/

One markdown file per week. Each file is a **snapshot of the weekly plan at planning time**, plus an **append-only change log** capturing mid-week shifts.

This folder holds the *planning rationale* — the layer that's about scheduling decisions, not about the work itself. The work itself (Tasks, Projects) lives in Notion. See `references/aios-task-system.md` for the architecture.

## File naming

`{YYYY-MM-DD}.md` where the date is the Monday of the week.

Examples:
- `2026-05-18.md` — week of Monday May 18
- `2026-05-25.md` — week of Monday May 25

## File shape

```markdown
# Week of {Monday date}

## Anchors (locked dates)
Calendar items + deadlines that shape the week. The fixed points everything else routes around.

Example:
- Wed 5/27 — Caglia Data Review 10-11:30am
- Thu 5/28 — Wisdom teeth surgery 8:45-10am (recovery day)
- Sat-Sun — Google I/O Hack (if confirmed)

## Plan (snapshot — written by /plan-my-week at planning time)

### {Weekday} {Month} {Day} (~Xh free)

- {Task name}  [link to Notion task page]
  Why this slot: short rationale
- ...

(repeat per day across the 7-day window)

## Reasoning / context that didn't fit elsewhere

Free-form. Week's center of gravity. Load-bearing pieces. Squeeze points. Strategy notes that apply to the week as a whole.

## Change log (append-only mid-week)

Append entries as the week unfolds. NEVER overwrite the Plan section above; the original snapshot stays intact.

- YYYY-MM-DD HH:MM: <what changed>
  Why: <reason>
```

## How this interacts with the Notion task system

- **Notion Tasks DB** = canonical source of *what* the work is + *how* to do it
- **This file (current week)** = canonical source of *when* the work is scheduled + *why* it landed on that day

A fresh chat session reading both:
1. Sees today's date
2. Reads the current week's file → knows what's planned for today + this week's anchors + the reasoning
3. Queries Notion Tasks DB → gets the actual task details
4. Cross-references the two

If the plan changes mid-week, the change log captures it here. The underlying Notion task status / deadline updates happen in Notion. Both surfaces update; this file does NOT replace Notion.

## What this folder is NOT

- **Not a content store** for projects or tasks. That's Notion.
- **Not a permanent record of every change** beyond the week. Once a week passes, the file becomes a historical snapshot. We don't actively maintain it forward in time.
- **Not a substitute for Notion**. If Notion is unavailable, the week's plan loses its underlying task references.

## Naming pre-existing files

- `2026-05-21-substrate.md` — working substrate from initial system design conversation. Predates the snapshot+change-log shape. Archived in spirit, kept for reference.
