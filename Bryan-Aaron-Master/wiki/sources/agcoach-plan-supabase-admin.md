---
name: agcoach-plan-supabase-admin
type: source
tags: [ag-coach-pro, supabase, admin, plan, gravity-claw, database]
source_files: [raw/_ingested/2026-05-16-agcoach-PLAN_supabase_admin_data.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Supabase + Admin Page + Gravity Claw Plan

**Date:** April 26, 2026. Plan to connect Gravity Claw to real Supabase data and build a real admin dashboard.

## Problem Statement

Two blockers as of writing:
1. Gravity Claw cannot execute queries against Supabase — connection setup works but queries fail.
2. Skills and admin page were built against a guessed schema, not the real one.

## Phase Plan (7 Phases)

**Phase 1 — Lock schema as source of truth (30 min)**
- Generate TypeScript types → `lib/types/supabase.ts`
- Run `list_tables` → `supabase/schema-snapshot-2026-04-26.json`
- Write `SCHEMA.md` at project root — single truth file for all sessions
- Update `CLAUDE.md` to point at `SCHEMA.md`

**Phase 2 — Fix Gravity Claw DB connection (1–2 hrs)**
Diagnostic order:
1. Confirm connection string, key, host
2. Test same credentials via Supabase MCP directly
3. Verify service role vs anon key (admin reads need service role; RLS blocks anon)
4. List RLS policies on key tables
5. Check network/pooler (PgBouncer transaction mode breaks prepared statements)

**Phase 3 — Define admin page KPIs (45 min)**
Core metrics:
- Total users by role (teacher / student / admin)
- Active subscriptions (individual + biz, separated)
- MRR estimate
- New signups last 7/30 days
- Teacher → chapter coverage
- Pending invitations
- Top 10 chapters by user count

**Phase 4 — Write SQL as Supabase views (1–2 hrs)**
Views: `admin_user_stats`, `admin_subscription_summary`, `admin_chapter_coverage`, `admin_pending_invitations`. Each restricted to `role = 'admin'` in JWT.

**Phase 5 — Wire admin page to views (2–3 hrs)**
`lib/data/admin-queries.ts` → `useAdminDashboard()` hook → dark glass KPI cards. Manual refresh only (no auto-polling).

**Phase 6 — Update skills to use SCHEMA.md (30 min)**
Replace hardcoded table lists in `skills/` with: "Read `SCHEMA.md` first."

**Phase 7 — Verification (15 min)**
Cross-check 3 numbers between: admin page, manual SQL, Gravity Claw. All three must match.

## Execution Order

Schema lock → metrics doc → SQL views → admin page → Gravity Claw fix → skills cleanup → verify.

*Note: Admin page can ship without Gravity Claw working. Schema first, ship the page, then fix the agent.*

## Related

- [[../sources/agcoach-schema|Database Schema (result of Phase 1)]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
