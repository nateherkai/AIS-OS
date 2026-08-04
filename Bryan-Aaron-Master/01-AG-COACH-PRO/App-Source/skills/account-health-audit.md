# Skill: Account Health Audit

## Purpose

Diagnose and repair "silent empty" account bugs — Staff tab shows "No chapter found", View-As picker shows "No matches", teacher dashboards render zeroed metrics. Almost always one of four root causes that compound:

1. Missing `memberships` row (trigger gap, pre-trigger account, partial onboarding).
2. Missing EXECUTE grant on RLS helper functions → RLS errors silently filter all rows.
3. Missing EXECUTE grant on read RPCs → PostgREST returns empty array.
4. `public.users.role` out of sync with `auth.users.user_metadata.role` → RLS embed on `public.users` hides the row.

This skill is the bulletproof checklist. Run it whenever a user reports "I can't see X" and the data clearly exists in the database.

---

## When to Use

- A teacher reports Staff tab empty, View-As picker empty, dashboards blank.
- Superadmin reports "I can see them in the DB but the app shows nothing."
- After any migration that creates a new `public.*` function (RPC or RLS helper).
- After adding any new RLS policy that calls a helper function.

---

## The Four Root Causes

### 1. Missing memberships row

Symptom: `TeacherTeam.currentSchool()` returns `null`. Staff tab → "No chapter found".

Diagnostic:

```sql
select count(*) as gap_count
from public.users u
where u.role = 'teacher'
  and u.school_id is not null
  and not exists (
    select 1 from public.memberships m
    where m.user_id = u.id and m.school_id = u.school_id
  );
```

Fix (idempotent backfill):

```sql
insert into public.memberships (school_id, user_id, role, status)
select u.school_id, u.id, 'owner', 'active'
from public.users u
where u.role = 'teacher'
  and u.school_id is not null
  and not exists (
    select 1 from public.memberships m
    where m.user_id = u.id and m.school_id = u.school_id
  )
on conflict (school_id, user_id) do nothing;
```

Reference: `supabase/migrations/20260513000003_backfill_owner_memberships.sql`.

### 2. Missing EXECUTE on RLS helpers

Symptom: `memberships` SELECT returns empty even though rows exist and user is authenticated. SQL test as the user:

```sql
set local role authenticated;
set local request.jwt.claim.sub = '<user-uuid>';
set local request.jwt.claims = '{"sub":"<user-uuid>","role":"authenticated"}';
select * from public.memberships where user_id = '<user-uuid>';
-- error: permission denied for function is_school_member
```

Diagnostic — list every helper missing EXECUTE for `authenticated`:

```sql
select p.proname, pg_get_function_identity_arguments(p.oid) as args
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.prokind = 'f'
  and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
  and (p.proname like 'is\_%'
    or p.proname like 'school\_%'
    or p.proname like 'shares\_%'
    or p.proname like 'has\_%')
order by p.proname;
```

Fix — grant on every helper the app uses:

```sql
grant execute on function public.is_school_member(uuid, uuid) to authenticated;
grant execute on function public.school_role(uuid, uuid) to authenticated;
grant execute on function public.shares_school_with(uuid, uuid) to authenticated;
grant execute on function public.is_superadmin(uuid) to authenticated;
```

Reference: `supabase/migrations/20260513000004_grant_execute_rls_helpers.sql`.

### 3. Missing EXECUTE on read RPCs

Symptom: `supabase.rpc('get_admin_chapters')` returns `[]` with no error in network tab but actual data exists. View-As picker → "No matches".

Diagnostic — find every `get_*` / `list_*` / `match_*` lacking EXECUTE:

```sql
select p.proname, pg_get_function_identity_arguments(p.oid) as args
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.prokind = 'f'
  and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
  and (p.proname like 'get\_%'
    or p.proname like 'list\_%'
    or p.proname like 'fetch\_%'
    or p.proname like 'match\_%'
    or p.proname like 'search\_%'
    or p.proname like 'current\_%')
order by p.proname;
```

Fix — grant on every read RPC the client calls. Reference: `supabase/migrations/20260513000006_bulletproof_grant_execute_authenticated.sql`. Re-run that pattern with newly-listed functions appended.

**Do NOT** grant on trigger functions (`auto_owner_membership`, `enqueue_role_promotion`, `sync_public_user_role_on_membership`, etc.) — they run as definer during INSERT/UPDATE and never need direct client EXECUTE.

### 4. `public.users.role` out of sync with `auth.users.user_metadata.role`

Symptom: Staff tab header renders ("Athens ISD FFA, 5 active") but TEACHERS (0) — `listMembers` returns empty because the embed `users:user_id(name, email)` is filtered by `public.users` RLS (`users.role = 'teacher'`), and the joined `public.users.role` is still `'student'`.

The `drain-role-promotions` cron only writes `auth.users.user_metadata.role`. It does NOT touch `public.users.role`.

Diagnostic:

```sql
select u.id, u.email, u.role as public_role, m.role as membership_role, m.status
from public.memberships m
join public.users u on u.id = m.user_id
where m.status = 'active' and u.role <> 'teacher';
```

Fix — backfill + add a trigger that mirrors auth promotion into public:

```sql
update public.users u
set role = 'teacher', updated_at = now()
where u.role <> 'teacher'
  and exists (
    select 1 from public.memberships m
    where m.user_id = u.id and m.status = 'active'
  );
```

Reference: `supabase/migrations/20260513000005_sync_public_users_role_from_memberships.sql` (includes the trigger).

---

## Standard Diagnostic Sequence

Given a user complaint "I can't see my staff / teachers / chapters":

1. **Confirm data exists** — query raw tables as service_role via MCP. If empty, this is a different problem (data ingestion, not visibility).
2. **Simulate authenticated context** — `set local role authenticated; set local request.jwt.claims = '...';` then run the same SELECT the client runs. If the error is `permission denied for function X`, jump to root cause #2 or #3.
3. **Check EXECUTE grants** — run both diagnostic queries above. Grant any missing.
4. **Check role sync** — run root cause #4 diagnostic. Backfill if mismatched.
5. **Check membership existence** — run root cause #1 diagnostic. Backfill if gap > 0.
6. **Verify the fix** — re-run the impersonated SELECT. Must return the expected rows.

---

## Defensive Rule for Future Migrations

**Every new `public.*` function must end with an explicit grant.** Add this checklist to migration review:

- If the function is called from a RLS policy → `grant execute ... to authenticated;` (and `anon` if the policy permits anonymous reads).
- If the function is called by `supabase.rpc('...')` from the client → `grant execute ... to authenticated;`.
- If the function is a trigger handler → no client grant needed; do not grant.
- If the function is admin-only → grant to `service_role` only.

Missing grants do not raise visible errors. They produce empty results, which look like "no data yet" to the user and waste hours of debugging.

---

## Related Files

| Concern | File |
|---|---|
| `currentSchool()` read-fallback | `lib/teacher-team.ts:45` |
| Auto-owner trigger | `supabase/migrations/044_multi_teacher_foundation.sql` |
| Role promotion queue | `supabase/migrations/20260513000002_promote_membership_role.sql` |
| Public role sync trigger | `supabase/migrations/20260513000005_sync_public_users_role_from_memberships.sql` |
| Enterprise provisioning | `supabase/migrations/050_provision_enterprise_school.sql` |
| Athens ISD remediation script | `scripts/repair-athens-isd-roles.ts` |
