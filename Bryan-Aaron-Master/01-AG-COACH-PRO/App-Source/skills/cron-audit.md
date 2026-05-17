# Skill: Cron Audit

## Purpose

pg_cron jobs silently fail when auth uses wrong setting or timeout too short. Two specific footguns:

1. `current_setting('app.settings.service_role_key')` returns **NULL** in cron worker sessions → 401
2. `net.http_post` default `timeout_milliseconds := 5000` aborts most reconcile workloads

This skill verifies every cron job is wired correctly.

---

## When to Use

- After adding new cron job
- Recurring "cron didn't fire" report
- After auth secret rotation
- Periodic audit (quarterly)

---

## Required Pattern

```sql
select cron.schedule(
  'job-name',
  '*/5 * * * *',  -- cron expression
  $$
  select net.http_post(
    url := 'https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/<fn>',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || private.internal_cron_key()  -- ← NOT current_setting(...)
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000  -- ← 60s min (longer for reconcile: 120000)
  );
  $$
);
```

---

## Audit SQL

### 1. List all jobs

```sql
select jobid, jobname, schedule, active, command
from cron.job
order by jobname;
```

### 2. Recent runs + failures

```sql
select j.jobname, r.status, r.return_message, r.start_time
from cron.job_run_details r
join cron.job j on j.jobid = r.jobid
where r.start_time > now() - interval '24 hours'
order by r.start_time desc
limit 50;
```

### 3. Audit each job command

```sql
select jobname, command
from cron.job
where command ilike '%app.settings.service_role_key%'  -- BAD
   or command ilike '%timeout_milliseconds := 5%'      -- BAD (5s)
   or (command ilike '%net.http_post%'
       and command not ilike '%timeout_milliseconds%') -- missing
   or (command ilike '%Authorization%'
       and command not ilike '%internal_cron_key%'
       and command not ilike '%pg_read_server_files%');
```

Every row returned = bug.

### 4. Confirm vault secret

```sql
select name from vault.secrets where name = 'internal_cron_key';
-- Must return 1 row
```

And helper exists:

```sql
select pg_get_functiondef('private.internal_cron_key'::regproc);
```

---

## Required Jobs

| Job | Schedule | Function | Notes |
|---|---|---|---|
| `drain-role-promotions` | `*/5 * * * *` | `drain-role-promotions` | 60s timeout |
| `stripe-reconcile` | `*/15 * * * *` | `stripe-reconcile` | **120s timeout** (long workload) |
| `trial-reminder` | `0 14 * * *` | `trial-reminder` | Daily 14:00 UTC |
| `self-heal-check` | `*/30 * * * *` | `self-heal-check` | 60s |
| `health-watch` | `*/10 * * * *` | `health-watch` | 60s |
| `generate-annual-invoices` | `0 6 1 * *` | `generate-annual-invoices` | Monthly day 1 |
| `daily-report` | `0 13 * * *` | `daily-report` | Daily 13:00 UTC |

---

## Fix Template

Wrong:

```sql
'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
```

Right:

```sql
'Authorization', 'Bearer ' || private.internal_cron_key()
```

To replace existing job:

```sql
select cron.unschedule('job-name');
-- Then re-run cron.schedule(...) with fixed command
```

---

## Verify Vault Secret Exists

If missing:

```sql
-- One-time setup (run by superuser)
select vault.create_secret('<long-random-string>', 'internal_cron_key');

-- Helper function
create or replace function private.internal_cron_key()
returns text
language sql
security definer
set search_path = ''
as $$
  select decrypted_secret
  from vault.decrypted_secrets
  where name = 'internal_cron_key'
$$;
```

Same value goes to edge fn env var `INTERNAL_CRON_KEY` so handlers can verify:

```bash
npx supabase secrets set INTERNAL_CRON_KEY=<same-value>
```

---

## Anti-Patterns

| Wrong | Why broken |
|---|---|
| `current_setting('app.settings.service_role_key')` | Returns NULL in cron worker → 401 |
| `timeout_milliseconds := 5000` (default) | Reconcile/scan abort mid-batch |
| Hardcoded `eyJ...` JWT in command | Rotation breaks job; visible in `cron.job` table |
| Same `internal_cron_key` for app + cron | Vault secret should differ from app secrets |
| No `pg_read_server_files`-equivalent guard in handler | Anyone with cron key can hit endpoint |
