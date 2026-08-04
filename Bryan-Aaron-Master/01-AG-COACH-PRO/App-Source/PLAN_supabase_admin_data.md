# Ag Coach Pro — Supabase + Gravity Claw + Admin Page Plan

**Date:** April 26, 2026
**Goal:** Gravity Claw queries real data. Admin page shows real metrics. Both pull from the *actual* Supabase schema — not the assumed one.

---

## What we know (verified)

Real tables in Supabase:

| Table | Rows | Purpose |
|---|---|---|
| `users` | 46 | App users (teachers + students) |
| `subscriptions` | 7 | Individual subscription records |
| `biz_subscriptions` | 2 | School/chapter-level subscriptions |
| `memberships` | 5 | Teacher ↔ school links |
| `biz_chapters` | 561 | FFA chapters / schools |
| `invitations` | 2 | Pending teacher invites |

Two problems blocking us:

1. **Gravity Claw can't execute queries** — connection setup works, queries fail.
2. **Skills + admin page were built against a guessed schema**, not the real one.

---

## Phase 1 — Lock the schema as source of truth (30 min)

Goal: stop guessing. Get one canonical reference for every table, column, and relationship.

**Steps**

1. Run `mcp__e1280b0f-…__generate_typescript_types` against the project. Save output to `lib/types/supabase.ts`.
2. Run `list_tables` for `public` schema and save the JSON to `supabase/schema-snapshot-2026-04-26.json`.
3. Add a short `SCHEMA.md` at project root with the 6-table summary above plus the foreign keys (who references whom). This becomes the truth file every skill reads first.
4. Update `CLAUDE.md` to point at `SCHEMA.md` so future sessions don't re-guess.

**Done when:** TS types compile clean, and `SCHEMA.md` lists every table with its primary key + foreign keys.

---

## Phase 2 — Fix Gravity Claw's database connection (1–2 hrs)

Goal: agent can run a query and get rows back.

**Diagnostic order (stop the moment one works):**

1. **Confirm what Gravity Claw is actually using** — connection string, key, host. If it's pointed at the wrong project or using anon key for admin queries, that's the whole problem.
2. **Test the same credentials via the Supabase MCP directly** with a known-good query: `select count(*) from users`. If MCP works and Gravity Claw doesn't, the issue is in the agent, not Supabase.
3. **Service role vs anon key** — admin reads need the service role key. RLS will block anon for any table with policies. Verify which key Gravity Claw has.
4. **RLS policies** — list policies on `users`, `subscriptions`, `biz_subscriptions`, `memberships`. If Gravity Claw is using a non-service role, you'll need either (a) a service role for the agent, or (b) explicit policies that allow it.
5. **Network / pooler** — if it's a connection pooler issue (PgBouncer transaction mode breaks prepared statements), switch the agent to the direct connection string.

**Done when:** Gravity Claw runs `select id, email from users limit 3` and returns real rows.

---

## Phase 3 — Define what the admin page actually needs (45 min)

Goal: stop building queries before we know the questions.

**Core admin KPIs (proposed — adjust before building):**

- Total users, by role (teacher / student / admin)
- Active subscriptions (individual + biz, separated)
- MRR estimate (sum of active sub prices)
- New signups last 7 / 30 days
- Teacher → chapter coverage (how many `biz_chapters` have a linked teacher via `memberships`)
- Pending invitations
- Top 10 chapters by user count

**Step:** write these as plain English questions in `admin/METRICS.md`. Each one becomes one SQL view in Phase 4.

**Done when:** the metrics doc lists every number the admin page should display.

---

## Phase 4 — Write the SQL as Supabase views (1–2 hrs)

Goal: clean, reusable views the admin page calls — no inline SQL in the React code.

**Pattern**

For each KPI in `METRICS.md`:

1. Write the SQL in the Supabase SQL editor first. Verify the number looks right against a manual count.
2. Save as a migration: `supabase/migrations/2026-04-26_admin_views.sql`.
3. Wrap as a `create or replace view admin_<name> as …`.
4. Add an RLS policy on each view restricting reads to `role = 'admin'` in JWT.

**Suggested views**

- `admin_user_stats` — counts by role + last 7/30 day signups
- `admin_subscription_summary` — active counts + MRR for both sub types
- `admin_chapter_coverage` — chapter ↔ teacher join with counts
- `admin_pending_invitations` — invites where `accepted_at is null`

**Done when:** `select * from admin_user_stats` returns a single-row dashboard payload.

---

## Phase 5 — Wire the admin page to the views (2–3 hrs)

Goal: real numbers on screen.

1. Create `lib/data/admin-queries.ts`. One function per view. Use the typed Supabase client from Phase 1.
2. Build a `useAdminDashboard()` hook in `app/(super-admin)/dashboard.tsx` that calls the four queries in parallel.
3. Render with the existing dark glass theme. KPI cards on top, two tables below (chapters + invitations).
4. Add a "Last refreshed" timestamp + manual refresh button. No auto-polling yet — ship the simple version first.

**Done when:** loading the admin page shows real counts that match what you see in the Supabase dashboard.

---

## Phase 6 — Update the skills so they stop guessing (30 min)

Goal: the helper skills (`module-status`, `rag-coverage-report`, anything that reads the DB) reference `SCHEMA.md` instead of assumed tables.

1. Open each skill in `skills/` that touches the DB.
2. Replace any hardcoded table list with: "Read `/Volumes/Samsung PSSD T7/ag-coach-app/SCHEMA.md` first. Use only those tables."
3. Re-run one skill end-to-end to confirm it works against the real schema.

**Done when:** any skill that queries the DB starts by reading the schema doc.

---

## Phase 7 — Verification (15 min)

1. Cross-check three numbers between (a) the admin page, (b) a manual Supabase SQL query, (c) Gravity Claw running the same query. All three must match.
2. Pick one KPI (e.g., active subscriptions) and trace it from `subscriptions` table → view → React component. Confirm the math is right.
3. Note any drift in `KNOWN_ISSUES.md`.

**Done when:** the same number shows up in all three places.

---

## Order of operations (next 6 working hours)

1. Phase 1 (schema lock) — do this first, everything depends on it.
2. Phase 3 (metrics doc) — cheap, unblocks Phase 4.
3. Phase 4 (SQL views) — builds the foundation.
4. Phase 5 (admin page) — visible win.
5. Phase 2 (Gravity Claw) — fix in parallel or after the page works. The page doesn't need Gravity Claw to function; Gravity Claw is bonus.
6. Phase 6 (skills cleanup) — tidy up so the next session doesn't repeat this hour.
7. Phase 7 (verify) — always last.

**Why this order:** the admin page can ship without Gravity Claw. Gravity Claw without the schema doc and views just keeps failing the same way. Schema first, ship the page, then come back and finish the agent.

---

## What I need from you to start Phase 1

- Confirm which Supabase project ID is the production one (so I generate types against the right one).
- Confirm whether Gravity Claw should use the service role key or a custom admin role.

Once those two are answered, I can run Phase 1 + Phase 3 in one session and have the schema doc and metrics list ready for review.
