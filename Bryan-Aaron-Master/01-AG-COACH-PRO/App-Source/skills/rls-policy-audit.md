# Skill: RLS Policy Audit

## Purpose

New tables need RLS + correct EXECUTE grants. Missing either → 401s in prod or data leaks across teachers/students. This skill audits existing tables + generates policies in repo style.

---

## When to Use

- New table in migration
- "Customer can't see X" / silent-empty bugs (after `account-health-audit`)
- Periodic policy review

---

## Repo Pattern

### Standard student-scoped table

```sql
alter table public.<t> enable row level security;

-- Student sees own
create policy "<t>_owner_select" on public.<t>
  for select using (user_id = auth.uid());

-- Student writes own
create policy "<t>_owner_write" on public.<t>
  for all using (user_id = auth.uid()) with check (user_id = auth.uid());
```

### Teacher-scoped (classroom)

```sql
-- Teacher sees students in their classrooms
create policy "<t>_teacher_select" on public.<t>
  for select using (
    exists (
      select 1 from public.memberships m
      where m.user_id = auth.uid()
        and m.role = 'teacher'
        and m.classroom_id = <t>.classroom_id
    )
  );
```

### Superadmin override

```sql
create policy "<t>_superadmin_all" on public.<t>
  for all using (
    exists (
      select 1 from public.users
      where id = auth.uid() and role = 'superadmin'
    )
  );
```

### RPC EXECUTE grant

```sql
-- ANY client-callable RPC needs this
grant execute on function public.<rpc_name>(<args>) to authenticated;
```

`SECURITY DEFINER` does **not** waive PostgREST's EXECUTE check. Internal role gate goes inside function body via `raise exception` (see `admin_get_leads_overview()` pattern).

---

## Audit SQL

### 1. Tables without RLS

```sql
select schemaname, tablename
from pg_tables
where schemaname = 'public'
  and tablename not in (
    select tablename from pg_tables t
    join pg_class c on c.relname = t.tablename
    where c.relrowsecurity = true
  )
order by tablename;
```

Every row = data leak risk.

### 2. RLS-enabled tables without policies

```sql
select c.relname as table_name
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relrowsecurity = true
  and not exists (
    select 1 from pg_policies p
    where p.schemaname = 'public' and p.tablename = c.relname
  );
```

RLS on + no policies = all queries return zero rows (silent empty).

### 3. Client RPCs missing EXECUTE grant

```sql
select p.proname as fn_name
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and not has_function_privilege('authenticated', p.oid, 'EXECUTE')
  and p.proname not like 'pg_%'
  and p.proname not like 'crypto_%';
```

Cross-reference against client-callable list. Any missing = 401.

### 4. Helper functions missing EXECUTE

`is_teacher_of(classroom_id)`, `is_classroom_member(...)`, etc. used inside RLS policies need `to authenticated`:

```sql
select p.proname,
  has_function_privilege('authenticated', p.oid, 'EXECUTE') as auth_can_exec
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in ('is_teacher_of','is_classroom_member','is_superadmin','user_role');
```

### 5. Policy overlap / shadowing

```sql
select tablename, count(*) as policy_count,
  array_agg(policyname) as policies
from pg_policies
where schemaname = 'public'
group by tablename
having count(*) > 6
order by policy_count desc;
```

> 6 policies on one table = likely overlap; review.

---

## Generate Policies (template)

For new table `public.widget_scores (id, user_id, classroom_id, score)`:

```sql
alter table public.widget_scores enable row level security;

create policy "widget_scores_owner_select" on public.widget_scores
  for select using (user_id = auth.uid());

create policy "widget_scores_owner_insert" on public.widget_scores
  for insert with check (user_id = auth.uid());

create policy "widget_scores_teacher_select" on public.widget_scores
  for select using (
    exists (
      select 1 from public.memberships m
      where m.user_id = auth.uid()
        and m.role = 'teacher'
        and m.classroom_id = widget_scores.classroom_id
    )
  );

create policy "widget_scores_superadmin_all" on public.widget_scores
  for all using (
    exists (select 1 from public.users where id = auth.uid() and role = 'superadmin')
  );

-- If any RPC reads this table for client, also:
-- grant execute on function public.get_widget_scores() to authenticated;
```

---

## Verification

After policies applied:

```sql
-- Test as anon (must return zero rows)
set local role anon;
select count(*) from public.widget_scores;
reset role;

-- Test as authed student (set jwt claims to mimic auth.uid())
-- Use Supabase dashboard SQL editor with "Impersonate user" feature
```

App-side smoke:

```ts
const { data, error } = await supabase.from('widget_scores').select();
// error?.code === '42501' → permission denied → policy missing or wrong
// data === [] for valid user → policy too restrictive
```

---

## Related

- `account-health-audit` — diagnoses 4 silent-empty root causes (membership row, EXECUTE on helper, EXECUTE on RPC, role drift)
- `migration-write` — apply via migration, never direct
