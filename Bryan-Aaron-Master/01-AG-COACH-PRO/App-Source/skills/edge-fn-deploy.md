# Skill: Edge Function Deploy

## Purpose

Pre-deploy gate for Supabase edge functions. Catches `verify_jwt` misconfig, missing secrets, dead crons. Smoke-probes after deploy.

24 edge fns live. Ad-hoc deploys cause silent 401s, missing-secret 500s, stale code.

---

## When to Use

- Any change in `supabase/functions/<name>/`
- After adding new edge fn
- Suspect deployed version diverged from repo

---

## Pre-Deploy Checklist

### 1. `config.toml` — verify_jwt setting

```bash
grep -A1 "\[functions.<name>\]" supabase/config.toml
```

Rules:
- Client-callable (called from app) → `verify_jwt = true`
- Stripe webhook, cron-driven, internal-key auth → `verify_jwt = false` + manual auth check in handler
- Never gate on JWT shape (`sb_publishable_...` is NOT a JWT)

### 2. Secrets required

Scan handler for `Deno.env.get(...)`:

```bash
grep -h "Deno.env.get" supabase/functions/<name>/*.ts | sort -u
```

Confirm each secret exists:

```bash
npx supabase secrets list | grep -E "RESEND_API_KEY|STRIPE_|GEMINI_|INTERNAL_CRON_KEY"
```

Missing → `npx supabase secrets set KEY=value`

### 3. Shared deps

Imports from `_shared/` (`notifyOps`, `cors`, etc.) — confirm path resolves. Edge runtime cannot reach outside `supabase/functions/`.

### 4. CORS

Client-callable fn must return CORS headers. Use `_shared/cors.ts` helper. OPTIONS preflight must short-circuit before auth.

---

## Deploy

```bash
npx supabase functions deploy <name> --project-ref nkoyotdafqllgbpuklva
```

Multi-fn:

```bash
for fn in match-knowledge-v2 stripe-webhook trial-reminder; do
  npx supabase functions deploy "$fn" --project-ref nkoyotdafqllgbpuklva
done
```

---

## Smoke Probe

### Client-callable (verify_jwt=true)

```bash
curl -i -X POST "https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/<name>" \
  -H "Authorization: Bearer $SUPABASE_PUBLISHABLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expect: 200 / 400 / 422. **Never 401** with valid key. 401 = `verify_jwt` misconfig or JWT-shape gate in handler.

### Internal/cron (verify_jwt=false)

```bash
curl -i -X POST "https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/<name>" \
  -H "Authorization: Bearer $INTERNAL_CRON_KEY"
```

### Webhook (Stripe)

```bash
stripe trigger checkout.session.completed
# Then: check stripe_event_log for new row
```

---

## Log Tail

```bash
npx supabase functions logs <name> --tail
```

Or MCP:

```
mcp__claude_ai_Supabase__get_logs(service="edge-function", project_id="nkoyotdafqllgbpuklva")
```

Look for: `BOOT_ERROR`, missing env var, import resolve fail.

---

## Cron-Driven Functions

If fn invoked by pg_cron (`drain-role-promotions`, `stripe-reconcile`, `trial-reminder`, `self-heal-check`, `daily-report`):

1. Auth header **must** be `Bearer ` + `private.internal_cron_key()` — NOT `current_setting('app.settings.service_role_key')` (returns NULL in cron worker)
2. `net.http_post` call needs `timeout_milliseconds := 60000` minimum (default 5s aborts)
3. Verify with `cron-audit` skill

---

## Rollback

```bash
git log -- supabase/functions/<name>/ | head
git checkout <sha> -- supabase/functions/<name>/
npx supabase functions deploy <name>
```

---

## Function Inventory

24 fns. Categories:
- **Client-callable** (`verify_jwt=true`): `match-knowledge`, `match-knowledge-v2`, `gemini-proxy`, `anthropic-proxy`, `tts-proxy`, `elevenlabs-transcript`, `create-payment-intent`, `clever-auth`, `mint-impersonation-token`
- **Webhook**: `stripe-webhook` (sig-verified, `verify_jwt=false`)
- **Cron**: `drain-role-promotions`, `stripe-reconcile`, `trial-reminder`, `self-heal-check`, `daily-report`, `generate-annual-invoices`, `health-watch`
- **Trial/onboarding**: `start-trial`, `create-invite`, `promote-to-teacher`, `notify-signup`, `notify-assignment`, `process-support-email`
- **Sync**: `stripe-sync`
