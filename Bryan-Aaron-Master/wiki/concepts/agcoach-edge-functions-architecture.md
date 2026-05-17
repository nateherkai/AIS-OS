---
name: agcoach-edge-functions-architecture
type: concept
tags: [ag-coach-pro, supabase, edge-functions, architecture, deno]
source_files: [raw/_ingested/2026-05-16-agcoach-CLAUDE.md, raw/_ingested/2026-05-16-agcoach-SCHEMA.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Edge Functions Architecture

26 Supabase Deno functions in `supabase/functions/` (plus `_shared/` helpers). Grouped by purpose. Auth: most use `verify_jwt = true` in `config.toml`; pg_cron callers use the dedicated `internal_cron_key` Vault secret (NOT `sb_secret_*`).

## AI proxies (4)

Hide model API keys, enforce per-uid rate limits, normalize errors.

- `gemini-proxy` — Gemini Flash / Pro requests for quizzes, grading, structured output.
- `anthropic-proxy` — Claude calls (backup / specific paths).
- `tts-proxy` — text-to-speech.
- `elevenlabs-transcript` — Whisper-style transcription for Creed / interview audio.

## RAG retrieval (3)

All `verify_jwt=true`, per-uid rate-limit, return ranked chunks from `knowledge_documents` (3072-dim halfvec, HNSW).

- `match-knowledge` — v1, single-category filter. Legacy path still used by `lib/ai/rag-quiz.ts` fallback and media path.
- `match-knowledge-v2` — Brain v2 (chip-less Second Brain). Two-phase ANN + boost RPC `match_knowledge_v2`, rulebook slot reservation, inner CTE bypasses HNSW-unsafe composite ORDER BY.
- `match-knowledge-v3` — Brain v3 taxonomy-aware. Adds `filter_subcategory` (+0.04 boost) and `strict_category` boolean (hard filter, 8× ANN widening so top-N signal survives rare-category filters). Client `lib/ai/brain-v3.ts` falls back to v2 on error.

See [[agcoach-rag-architecture|RAG Architecture]] for full detail.

## Auth & role (5)

- `clever-auth` — Clever SSO integration for school chapter onboarding.
- `create-invite` — teacher-side invite generation (joinCode → student or staff).
- `mint-impersonation-token` — superadmin "view-as" any user; logged + bounded.
- `promote-to-teacher` — flips `auth.users.user_metadata.role` after a paid signup, invoked from `drain-role-promotions`.
- `drain-role-promotions` — pg_cron worker (every 5 min) that walks `pending_role_promotions` outbox + calls `promote-to-teacher` + invalidates sessions. Webhook hot path never calls `auth.admin.updateUserById` directly.

## Billing & Stripe (7)

- `stripe-webhook` — first op after sig verify is `INSERT ... ON CONFLICT DO NOTHING` into `stripe_event_log` (idempotency gate). On processing failure the row is DELETED so Stripe's retry runs fresh; after `MAX_RETRY_ATTEMPTS=5` it tombstones to stop the 72h retry storm. Insert into `pending_role_promotions` for role changes (NEVER call admin API in hot path).
- `stripe-sync` — pulls invoice / payment objects into `biz_*` tables (the current source of truth; `subscriptions`/`schools` are grandfathered).
- `stripe-reconcile` — pg_cron (every 15 min). Self-heals stale role promos + canceled-drift. Needs `timeout_milliseconds=60000+` (default 5s aborts the workload).
- `start-trial` — TOCTOU-safe per-IP rate-limited trial start with repair path. Called from `app/start-trial.tsx`.
- `trial-reminder` — pg_cron daily at 14:00 UTC. Drives 7/3/1/0/-7 day milestone emails via `trial_reminder_log` idempotency.
- `create-payment-intent` — Stripe Payment Intents for Feed Bag credit packs + one-off purchases.
- `generate-annual-invoices` — produces yearly site-license invoices for chapter tiers.

See [[agcoach-billing-systems|Billing Systems (Dual)]] for `biz_*` vs legacy detail.

## Ops & notifications (6)

- `notify-signup` — fan-out on new student/teacher signup. Routes through `_shared/notifyOps.ts` (Resend + Telegram Gravity Claw bot, fire-and-forget; total failure writes `onboarding_alerts (type='notification_failed')`).
- `notify-assignment` — teacher assignment → student push/email.
- `process-support-email` — inbound support inbox → ticket row + ops alert.
- `daily-report` — pg_cron daily roll-up to admin email / Telegram.
- `health-watch` — periodic check on core deps, writes status row.
- `self-heal-check` — companion to `stripe-reconcile`; verifies expected state for active accounts and queues repairs.

## Cross-cutting rules (from [[agcoach-app-working-instructions|CLAUDE.md]])

- Never gate proxies on JWT shape — Supabase `sb_publishable_...` keys are NOT JWTs. Use `verify_jwt=true` or non-empty length check only.
- Role promotion never bypasses the `pending_role_promotions` outbox in the webhook hot path.
- `.catch()` on PostgREST builders is forbidden — PostgrestBuilder is thenable, not a Promise. Use `try { await ... } catch {}`. `notifyOps()` returns a real Promise and is `.catch()`-safe.
- pg_cron URLs use `private.internal_cron_key()` for Bearer auth; `current_setting('app.settings.service_role_key')` returns NULL in cron sessions and silently 401s.
- Every `net.http_post` from cron needs `timeout_milliseconds` ≥ 60_000.

## Shared helpers

`supabase/functions/_shared/` — `notifyOps.ts` (Resend + Telegram), CORS, env loaders, Stripe verify, embedding helpers (always assert `gemini-embedding-2-preview@3072` at runtime).

## Related

- [[agcoach-rag-architecture|RAG Architecture]]
- [[agcoach-billing-systems|Billing Systems (Dual)]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions (CLAUDE.md)]]
- [[../sources/agcoach-schema|Supabase Schema]]
- [[../sources/agcoach-migration-drift-audit|Migration Drift Audit]]
- [[../organizations/supabase|Supabase]]
- [[../organizations/stripe|Stripe]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
