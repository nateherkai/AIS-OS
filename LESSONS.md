# Lessons Learned

Distilled from dream engine, promote loop, and session activity. Newest first.

---

## 2026-05-24

- No em dashes in Bryan's written communication. Short, direct intros only.
- Self-registered teacher trials (like Darrin Gilley's Friona signup) don't wire up to Stripe. Product gap, not conversion problem. Flag for fix, don't chase as cold lead.

## 2026-05-22

- hc_nlm_* tools: always parse JSON before checking exit code. `artifact wait` exits 1 but returns valid JSON. Fixed in b93308036.
- hc_nlm_* tools: NotebookLM CLI returns `task_id` not `id`. Check actual response shape, not assumed schema.

## 2026-05-21

- NotebookLM OAuth tokens expire silently. No auto-refresh. Must re-auth interactively when Frank skill reports auth failure.

## 2026-05-18

- Smoke-test rows in stripe_event_log trigger false alerts. Always filter synthetic rows (`evt_smoke*`, `smoke.*`) from monitoring queries.

## 2026-05-12

- Bryan's email voice: warm, direct, unpretentious. Never corporate. Always draft, never send without approval.
