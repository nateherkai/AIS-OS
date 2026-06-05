# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

---

## 2026-06-04 — Repo hosts many projects under `projects/`; job search is the first

**Decision:** This repo is the AIOS home and will host multiple project workspaces. AIOS-level context (`context/`, `references/`, `connections.md`, `CLAUDE.md`, `decisions/`) stays at the root and is shared across projects. Each initiative lives under `projects/<name>/`. The job search is first: `projects/job-search/` with `applications.md` (tracker), `tasks.md`, `notes/`, and `.md` docs (tailored CVs, cover letters).

**Why:** Yuan wants one repo for many future projects, with the job search tracked as markdown in-repo (no external PM tool). Shared context at the root avoids duplicating identity/voice per project.

**Alternatives considered:** Separate repo per project (more overhead, context duplication); external tracker like Notion/ClickUp (rejected — Yuan prefers markdown-in-repo).

**Owner:** Yuan.

---

## 2026-06-04 — AIOS repurposed to run a job search (not a business)

**Decision:** Treat this AIOS install as a job-search engine. The "offer" is Yuan as a candidate; the "ICP" is companies hiring. Q4-Q7 connection domains are adapted accordingly (opportunity pipeline, recruiter/network, etc.).

**Why:** Yuan isn't selling a product right now; the goal is to land a remote/startup Software or AI Engineering role and automate the search. The kit's structure (context, voice, priorities, connections, weekly `/level-up`) maps cleanly onto that.

**Alternatives considered:** Using the kit as-shipped for a business (N/A — no business to run).

**Owner:** Yuan.
