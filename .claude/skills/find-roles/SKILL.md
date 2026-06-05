---
name: find-roles
description: Run the job-discovery pipeline on demand. Use when Yuan says "find roles", "find me jobs", "run a job search", or wants new opportunities surfaced and added to the tracker.
---

# Find Roles

Surface new job leads, let Yuan approve, and append approved ones to the tracker.

## Steps

1. **Gather (automated sources):** from `projects/job-search/discovery/core/`, run
   `npx tsx ../aios/discover.ts`. It prints a numbered, ranked shortlist (already deduped against
   the seen-store and `applications.md`) and writes `discovery/queue/last-run.json`.

2. **Present the shortlist** to Yuan as the numbered list, each with a one-line "why it fits"
   (stack overlap / startup / recency, inferred from the score and tags). Keep it tight.
   Mention any sources printed after "Skipped:" — never hide a gap.

3. **Ask which to approve** ("1, 3, 5", "all", or "none"). This is the human-in-the-loop gate —
   never write before Yuan picks.

4. **Approve:** from `core/`, run `npx tsx ../aios/approve.ts <indices>` with the chosen 1-based
   numbers (for "all", pass `1 2 … N`). This appends them as `Lead` rows to `applications.md`
   and marks them seen so they don't resurface.

5. **Confirm:** report how many leads were added.

## Notes
- Gated sources (Seek, LinkedIn, Wellfound, YC) are added in Plan 2; this skill covers automated sources only.
- Re-running `/find-roles` won't resurface approved or already-tracked roles (seen-store + tracker dedup).
