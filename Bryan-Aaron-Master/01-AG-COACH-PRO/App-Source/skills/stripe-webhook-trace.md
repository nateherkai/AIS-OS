# Skill: Stripe Webhook Trace

## Purpose

Trace single Stripe event through onboarding pipeline. Diagnoses retry tombstones, role-promotion stalls, idempotency hits, drift between Stripe state and `biz_*` tables.

---

## When to Use

- "Customer paid but role still student"
- "Webhook keeps retrying"
- "Duplicate charge" / "Why didn't this run again"
- Trial conversion not firing

---

## Pipeline Recap

1. Stripe POST → `stripe-webhook` edge fn
2. Verify signature → `INSERT ON CONFLICT DO NOTHING` into `stripe_event_log` (idempotency gate)
3. Process: write `biz_*` tables, insert `pending_role_promotions`
4. `drain-role-promotions` cron (5m) calls `auth.admin.updateUserById` → sets role
5. `stripe-reconcile` cron (15m) heals stale promos + drift
6. `notifyOps` fires Resend + Telegram
7. On exception: DELETE `stripe_event_log` row, increment retry, tombstone after 5

---

## Inputs

- `stripe_event_id` (e.g. `evt_1Q...`)
- OR customer email
- OR `cus_...` ID

---

## Trace SQL

### 1. Event log state

```sql
select stripe_event_id, event_type, status, retry_count, processed_at, error_message, created_at
from stripe_event_log
where stripe_event_id = 'evt_...';
```

| Status | Meaning |
|---|---|
| row absent | First retry never made it / sig verify failed |
| `processing` | In-flight (rare unless crashed mid-handler) |
| `done` | Success — webhook returned 200 |
| `failed` + retry_count < 5 | Will retry on next Stripe attempt |
| `failed` + retry_count >= 5 | Tombstoned, Stripe stops |

### 2. Role promotion queue

```sql
select user_id, target_role, source, status, attempts, last_error, created_at
from pending_role_promotions
where user_id = (select id from auth.users where email = '<email>')
order by created_at desc;
```

### 3. Biz table drift

```sql
select
  u.email,
  u.raw_user_meta_data->>'role' as auth_role,
  pub.role as public_role,
  bs.status as biz_status,
  bs.tier,
  bs.current_period_end
from auth.users u
left join public.users pub on pub.id = u.id
left join biz_subscriptions bs on bs.user_id = u.id
where u.email = '<email>';
```

### 4. Alerts

```sql
select type, payload, created_at
from onboarding_alerts
where payload::text ilike '%<email-or-event-id>%'
order by created_at desc
limit 20;
```

### 5. Stripe-side state

```bash
stripe events retrieve evt_...
stripe customers retrieve cus_...
stripe subscriptions list --customer cus_...
```

---

## Decision Tree

| Symptom | Cause | Fix |
|---|---|---|
| Event log row absent, retries 5+ in Stripe | Sig verify fails | Check `STRIPE_WEBHOOK_SECRET`, endpoint URL |
| `failed`, retry_count = 5 | Tombstoned | Inspect `error_message`, fix bug, manually re-run via `stripe events resend evt_...` after deleting tombstone |
| `done` but no `pending_role_promotions` | Handler skipped promotion path | Check event_type → handler mapping in `stripe-webhook/index.ts` |
| `pending_role_promotions.status='pending'` > 10m old | Drain cron broken | `cron-audit` skill |
| `pending_role_promotions.status='failed'` | Admin API error | Check `last_error`, retry via `manual_heal_orphan(uuid)` RPC |
| `auth_role != public_role` | Drift | `stripe-reconcile` next run heals, or call `manual_heal_orphan` |
| `biz_subscriptions.status='active'` but role still student | Promo never queued | Trace handler path, may need manual insert into `pending_role_promotions` |

---

## Manual Heal

```sql
-- CRM "Heal now" RPC
select public.manual_heal_orphan('<user_uuid>');
```

Force-runs reconcile for one user. Idempotent.

---

## Force Re-process

```bash
# Delete tombstone, then resend
psql ... -c "delete from stripe_event_log where stripe_event_id = 'evt_...';"
stripe events resend evt_...
```

⚠️ Only delete if you know root cause is fixed. Otherwise you re-enter the same failure loop.

---

## Live IDs

- Supabase project: `nkoyotdafqllgbpuklva`
- Webhook URL: `https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/stripe-webhook`
- Logs: `npx supabase functions logs stripe-webhook --tail`
