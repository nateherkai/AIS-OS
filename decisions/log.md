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
