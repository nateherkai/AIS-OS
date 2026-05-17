# Skill: View-As Impersonation

## Purpose

Superadmin needs to test teacher/student paths without logging out. `mint-impersonation-token` edge fn issues short-lived JWT for target user. Wraps token mint + URL open + cleanup.

---

## When to Use

- Bug repro for specific teacher account
- QA new teacher dashboard feature
- Verify RLS policies as student vs teacher
- Demo to stakeholder using real-data account

---

## Prerequisite

- Authenticated as superadmin (in `public.users.role = 'superadmin'`)
- Target user `auth.users.id` known (lookup via CRM screen or SQL)

---

## Flow

### 1. Lookup target

```sql
select u.id, u.email, pub.role, c.name as classroom
from auth.users u
left join public.users pub on pub.id = u.id
left join classrooms c on c.id = pub.classroom_id
where u.email ilike '%<search>%'
   or u.id::text = '<uuid>';
```

### 2. Mint token via edge fn

From app (super-admin CRM screen has button) OR curl:

```bash
curl -X POST "https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/mint-impersonation-token" \
  -H "Authorization: Bearer $(your superadmin session JWT)" \
  -H "Content-Type: application/json" \
  -d '{"target_user_id":"<uuid>", "ttl_minutes": 30}'
```

Response:

```json
{
  "access_token": "ey...",
  "refresh_token": "ey...",
  "expires_at": "2026-05-15T15:00:00Z",
  "impersonating_user_id": "<uuid>",
  "actor_user_id": "<superadmin uuid>"
}
```

### 3. Open in fresh browser context

**Use incognito / private window** — do not overwrite your own superadmin session.

```bash
open -na "Google Chrome" --args --incognito "https://www.agcoachpro.com/auth/impersonate?token=<access_token>"
```

Or paste tokens into Supabase client manually:

```ts
await supabase.auth.setSession({
  access_token: '...',
  refresh_token: '...',
});
```

### 4. Test

Now session belongs to target user. Hit screens. Reproduce bug. Note `actor_user_id` is logged server-side — every action attributable.

### 5. Cleanup

Close incognito window. Token TTL expires within 30m default. No manual revoke needed for short TTLs; for emergency:

```sql
-- Revoke session by deleting refresh token row
delete from auth.refresh_tokens
where user_id = '<target_uuid>'
  and updated_at > now() - interval '30 minutes';
```

---

## Audit

Every impersonation logs to `impersonation_audit_log`:

```sql
select created_at, actor_user_id, impersonated_user_id, ttl_minutes, reason
from impersonation_audit_log
order by created_at desc
limit 20;
```

Use for compliance + incident review.

---

## Anti-Patterns

| Wrong | Why |
|---|---|
| Reuse same browser window | Overwrites your superadmin session, locks you out |
| Long TTL (24h+) | Lost token = unauthorized access window |
| Skip incognito | Browser stores tokens in localStorage, cross-contaminates sessions |
| Impersonate to make changes | Audit log shows target user as actor — use with care; documented `actor_user_id` mitigates but doesn't eliminate confusion |
| Impersonate without logging reason | `reason` field exists in audit log; populate it |

---

## Related

- `mint-impersonation-token` edge fn
- `app/(super-admin)/crm.tsx` — "View as" button per user card
- `impersonation_audit_log` table
