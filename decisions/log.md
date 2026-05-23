# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

---

## 2026-05-12 — Email reply drafting automation

**Decision:** Build L2 AI-assisted skill (`draft-reply`) to draft email/message replies in Bryan's voice. Bryan pastes incoming message, AIOS drafts, Bryan reviews and sends manually.

**Why:** Email response is the #1 daily time-suck outside of teaching. At 50 schools it becomes a job. Voice samples already captured. Lowest viable autonomy that solves the problem.

**Alternatives considered:** L4 autonomous reply (rejected — too early, no validation history). Social media post drafting (deferred — doesn't move revenue directly).

**KPI:** Response time reduced to same-session. Bucket: more value per customer.

**Owner:** Bryan

## 2026-05-18 — Filter smoke-test rows from stripe stuck-event alert

**Decision:** Patched `health-watch` edge function (ag-coach-app) to exclude `stripe_event_id LIKE 'evt_smoke%'` and `event_type LIKE 'smoke.%'` from the >5min stale-processing check. Tombstoned the offending `evt_smoke_lifecycle` row and resolved 6 open false-positive `health_stuck_event_log` alerts.

**Why:** A synthetic lifecycle smoke test row sat in `stripe_event_log` with `status='processing'` and triggered urgent pages to Gravity Claw every ~5h for 24h. Real customer Stripe events untouched; alert query lacked a synthetic-row filter. Reason to revert: only if smoke harness changes naming convention away from `evt_smoke*` / `smoke.*`.

**Alternatives considered:** (1) Remove smoke harness — rejected, lifecycle smoke is load-bearing. (2) Have smoke test mark row `completed` on cleanup — preferred long-term, but filter is defense-in-depth either way. (3) Add reaper cron auto-tombstoning any `processing` row >15min — deferred; could mask real webhook crashes.

**KPI:** Zero false-positive pages on this rule going forward. Verified by manual `health-watch` invoke returning `stale_processing_events: 0, alertsFired: 0`.

**Commit:** `a556f944` on `ag-coach-app:main`, deployed to project `nkoyotdafqllgbpuklva`.

**Owner:** Bryan
