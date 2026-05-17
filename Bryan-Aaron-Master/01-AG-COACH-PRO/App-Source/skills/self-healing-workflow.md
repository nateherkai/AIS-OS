# self-healing-workflow

## When to use
Building any new revenue-side workflow that touches Stripe, auth.users, or `biz_*` billing tables: refunds, invoicing automation, dunning, plan upgrades, new product launches, partner programs. Use this pattern instead of inventing a new one or reaching for an external orchestrator (n8n / Zapier / Make).

## Why
Onboarding v1 leaned on n8n — invisible failures, no idempotency, role drift, no audit trail. Replaced by an in-repo pattern proven through the May 2026 onboarding-v2 rebuild (commits `f4160582` → `9395e543`). Every external orchestrator we kill removes a silent-failure surface.

---

## The pattern

Eight layers. Every revenue-touching workflow ships all eight.

### 1. Single signed entry point
- Inbound: Stripe webhook → signature verified by `stripe.webhooks.constructEvent()` against `STRIPE_WEBHOOK_SECRET`. **No fallback** to `JSON.parse` if secret missing — refuse the request 500.
- Outbound: any internal-fired job authenticated via `Bearer <INTERNAL_CRON_KEY>` (vault-backed `private.internal_cron_key()`).

### 2. Atomic idempotency log
- One table per inbound event type. PK is the provider's event id.
- First DB op in the handler: `INSERT ... ON CONFLICT (event_id) DO NOTHING RETURNING *`. Zero rows = duplicate, return 200 immediately.
- Mark `status='processing'` on insert, `status='completed'` after work done.
- On exception: DELETE the row so the next retry processes fresh. Count prior failures via `onboarding_alerts`; tombstone (keep row + alert ops) after N retries to break Stripe's 72h retry storm.

```ts
const { error } = await supabase
  .from('stripe_event_log')
  .insert({ stripe_event_id: event.id, event_type: event.type, status: 'processing' })
  .select('stripe_event_id')
  .maybeSingle()
if (error?.code === '23505') return new Response('{"duplicate":true}', { status: 200 })
```

### 3. Outbox for cross-system writes
Never call admin APIs (Supabase `auth.admin.updateUserById`, Stripe customer mutations) on the webhook hot path. Insert a row into a `pending_*` table; a drain cron handles it out-of-band.

Why: webhook must return 200 in <30s. Admin APIs can be slow / 503. The outbox decouples durability from network reliability. Failure isolated to one row, not the whole event.

`pending_role_promotions` is the canonical example. `drain-role-promotions` cron every 5m picks it up.

### 4. Self-healing reconciler
A scheduled job (`*/15 * * * *`) that:
- Drains stuck outbox rows (admin API retries with `attempt_count` increment).
- Escalates exhausted rows (>5 attempts) to `onboarding_alerts`.
- Detects drift: provider says X, our DB says Y → repair to X.
- Deduped via `last_alerted_at` (no repeat alert for same `(user_id, type)` within 4h).

### 5. Fire-and-forget notifications (`notifyOps`)
`supabase/functions/_shared/notifyOps.ts`. Resend email + Telegram (Gravity Claw bot) in parallel. Wrapper guarantees:
- Never throws into caller.
- 4s `AbortSignal.timeout()` per channel.
- `Promise.allSettled` — one channel down doesn't block the other.
- Total failure writes `onboarding_alerts (type='notification_failed')` for ops visibility.

Call pattern: `notifyOpsFAF(args)` wraps a `.catch(console.error)` so even calling the helper is non-blocking.

### 6. Durable audit (`onboarding_alerts`)
Every cross-boundary failure inserts here. Columns: `user_id`, `chapter_id`, `type`, `status`, `detail jsonb`, `last_alerted_at`, `last_healed_at`. RLS: service role write, superadmin select+resolve. **No cascade delete** on `user_id` (audit must survive account deletion).

Types in use today: `webhook_processing_failed`, `notification_failed`, `role_promote_failed`, `role_promote_enqueue_failed`, `role_promote_exhausted`, `orphan_no_chapter`, `trial_reminder_send_failed`.

### 7. Superadmin CRM surface
Single RPC `admin_get_leads_overview()` (SECURITY DEFINER, internal `public.users.role = 'superadmin'` caller gate, EXECUTE granted to `authenticated` because PostgREST requires it). Powers the kanban at `app/(super-admin)/crm.tsx` with status columns + one-click `manual_heal_orphan(uuid)` button on orphan cards.

### 8. Real-time + scheduled monitoring
- **Real-time**: every state-change calls `notifyOpsFAF` with a single-line summary. Bryan's Telegram pings as it happens.
- **Daily report** (`daily-report` fn, 13:00 UTC): scans last 24h. Posts: new signups, new trials, new purchases, MRR delta, trials ending in 7/3/1 days, any open alerts.
- **Health-watch** (`health-watch` fn, hourly): alerts when system goes dark — drain queue stuck, recent failure rate >10%, no reconcile in 60min.

---

## Required infrastructure (copy when forking)

| Artifact | Path |
|---|---|
| Idempotency table | `public.stripe_event_log` (or `public.<provider>_event_log`) |
| Outbox table | `public.pending_<verb>` with `attempt_count int default 0, last_attempt_at timestamptz, processed_at, processed_note` |
| Alert sink | `public.onboarding_alerts` (reuse — single ops audit log) |
| Vault secret | `internal_cron_key` (already provisioned) |
| Helper RPC | `private.internal_cron_key()` |
| Shared helper | `supabase/functions/_shared/notifyOps.ts` |
| Cron template | See `supabase/migrations/20260515020000_onboarding_v2_cron_auth_fix.sql` for the `cron.schedule` + `net.http_post` shape with `private.internal_cron_key()` Bearer + `timeout_milliseconds := 60000+`. |

---

## Anti-patterns (do not repeat)

- **`current_setting('app.settings.service_role_key')` in cron** — returns NULL in pg_cron worker sessions. Silently 401s. Use `private.internal_cron_key()` from vault instead. (Killed Bryan's drain-role cron for 24h on 2026-05-13.)
- **`.catch(() => {})` on `supabase.from(...).insert(...)`** — PostgrestBuilder is thenable, not a Promise. Throws `TypeError: .catch is not a function`. Use `try { await ... } catch {}` for postgrest. (Killed the entire webhook on first E2E run on 2026-05-15.)
- **Default 5s pg_net timeout** — reconcile/scan jobs exceed it. Always set `timeout_milliseconds := 60000+`.
- **Sync admin API on webhook hot path** — Stripe will retry on timeout, you'll double-process. Use outbox.
- **External orchestrator for revenue-side automation** — n8n / Zapier failures are invisible; you find out from teachers, not the system. Stay in repo.
- **Cross-mode Stripe price IDs** — hardcoded `price_1TKkt6...` (live) breaks if `STRIPE_SECRET_KEY` swaps to test. Source price IDs from env vars when supporting test/live toggle.
- **Light-mode UI on superadmin screens** — house style is dark glass everywhere.

---

## Definition of done

Before declaring any new workflow done:

1. Run E2E via the synthetic-event approach (build a one-off `<workflow>-trigger` edge fn that signs the payload internally — see git history for `e2e-trigger-webhook` deleted 2026-05-15 as reference).
2. Replay the same event id twice → confirm idempotency log short-circuits with `duplicate:true`.
3. Force-fail one step (e.g. unset Telegram secret) → confirm `notifyOps` returns gracefully + writes `onboarding_alerts`.
4. Run the reconciler with mismatched state → confirm drift heals + no repeat alerts within 4h.
5. Tear down all synthetic data before commit.

---

## Reference commits (onboarding-v2, May 2026)

- `f4160582` initial webhook + start-trial hardening
- `e4a73613` codex review patches + trial-reminder + reconcile hardening
- `f3404ccf` CRM kanban + student-only signup + /start-trial page
- `5a5f8fef` cron auth via INTERNAL_CRON_KEY
- `1b71f1bc` PostgrestBuilder .catch fix (surfaced by E2E)
- `d179223a` pg_net timeout bump
- `f235a9a1` n8n outbound calls removed
- `9395e543` strict student guardrail on start-trial
