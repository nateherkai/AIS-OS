# Skill: Migration Write

## Purpose

Enforce migration discipline. Stop schema drift. Block orphaned `apply_migration` MCP calls. Regenerate `SCHEMA.md` + snapshot after apply.

Prod has 53+ orphan versions (see `docs/migration-drift-2026-05-15.md`). One uncommitted MCP migration = `db push` permanently broken.

---

## When to Use

- Any schema change (DDL: create/alter/drop table, RPC, policy, index, trigger, grant)
- Before calling `mcp__claude_ai_Supabase__apply_migration`
- After applying migration manually (refresh schema docs)

---

## Hard Rules

1. **Never** `apply_migration` MCP without committed file in `supabase/migrations/`
2. New file naming: `YYYYMMDDHHMMSS_description.sql` — legacy `NNN_*.sql` grandfathered through ~073, do not extend
3. `.upsert(onConflict)` needs unique **constraint**, not just unique index — use `alter table ... add constraint ... unique (col)` or `unique using index`
4. EXECUTE grant on `authenticated` for every client-callable RPC (PostgREST requires it even with `SECURITY DEFINER` internal gate)
5. After apply: regenerate `SCHEMA.md` + `supabase/schema-snapshot-YYYY-MM-DD.json`

---

## Procedure

### Step 1 — Pick timestamp filename

```bash
date -u +"%Y%m%d%H%M%S"
# → 20260515143022
# File: supabase/migrations/20260515143022_add_widget_table.sql
```

### Step 2 — Write migration

Template:

```sql
-- Migration: add_widget_table
-- Date: 2026-05-15
-- Why: <one-line reason>

begin;

create table if not exists public.widgets (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

-- Unique CONSTRAINT (not just index) for upsert support
alter table public.widgets
  add constraint widgets_owner_unique unique (owner_id);

alter table public.widgets enable row level security;

create policy "widgets_owner_select" on public.widgets
  for select using (owner_id = auth.uid());

create policy "widgets_owner_write" on public.widgets
  for all using (owner_id = auth.uid()) with check (owner_id = auth.uid());

-- Client RPCs need EXECUTE on authenticated
-- grant execute on function public.my_rpc() to authenticated;

commit;
```

### Step 3 — Commit FIRST

```bash
git add supabase/migrations/<file>.sql
git commit -m "feat(db): add widgets table"
```

### Step 4 — Apply

Option A (preferred, local): `npx supabase db push`
Option B (managed): `mcp__claude_ai_Supabase__apply_migration` with name matching filename slug

### Step 5 — Refresh schema docs

```bash
# Regen snapshot
npx supabase db dump --schema public > supabase/schema-snapshot-$(date -u +%F).json
```

Update `SCHEMA.md` — add/edit table section, document new columns, FKs, RLS policies.

### Step 6 — Verify

```sql
-- Confirm migration recorded
select version, name from supabase_migrations.schema_migrations
order by version desc limit 5;
```

---

## Anti-Patterns

| Bad | Why | Fix |
|---|---|---|
| `apply_migration` MCP, no file | Creates orphan version, blocks `db push` forever | Write file → commit → apply |
| `create unique index` for upsert | PostgREST `onConflict` silently INSERTs, hits dupe | `add constraint ... unique` |
| `SECURITY DEFINER` RPC, no grant | Client gets 401 from PostgREST | `grant execute on function ... to authenticated` |
| `NNN_*.sql` filename | Legacy scheme, grandfathered | Timestamp `YYYYMMDDHHMMSS_*.sql` |
| Edit existing migration | Already applied to prod | New migration that alters |
| Drop column without backfill plan | Breaks live clients | Migration phase 1: nullable + dual-write. Phase 2: drop. |

---

## Drift Recovery

Symptoms: `db push` errors with "remote migration not found locally" or version mismatch.

```bash
# Inspect drift
npx supabase db remote commit --schema public
# Diff remote vs local migrations
diff <(npx supabase migration list --linked) <(ls supabase/migrations/)
```

See `docs/migration-drift-2026-05-15.md` for current orphan list + repair plan.
