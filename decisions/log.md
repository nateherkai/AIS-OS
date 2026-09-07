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

## 2026-09-07 — Idea→Script Draft Pipeline (`/level-up` #1)

**Decision:** Build a workflow that turns a raw captured idea into a structured
first-draft script, targeting the constraint named in the 2026-09-07 `/audit`
(AIOS-2026-09-07-03): none of the 3 stated 90-day priorities had a supporting
workflow yet.

**Constraint (Mindset):** Top pain is idea→script, not editing (per `About Brandon.md`
/ Not A Work Bro Channel Identity). This is also the actual blocker between "no
content this week" and the 1-video/week target.

**EAD:** Eliminate — no, scripting is core to shipping a video. Automate — yes,
~60% deterministic (capture → structured template) / ~30% AI-drafted (idea →
script text in channel format) / ~10% manual. The manual slice is larger than
usual right now because `references/voice.md` doesn't exist yet (Q2 deferred at
onboarding) — every AI draft needs a real pass from Brandon until it does.
Delegate — not needed.

**Process map:**
- Trigger: new entry in a dedicated Google Drive doc ("Idea Inbox") — Google Keep
  was the first choice but has no available connector in this environment; Drive
  is confirmed live.
- Data sources: the Idea Inbox entry + channel format rules (`Not A Work Bro
  Channel Identity`, Home-Base locked decisions) from the Obsidian vault, read-only.
- Transformation: raw idea → structured draft (hook / body beats / CTA).
- Decision point: long-form (counts toward YPP watch-hours) vs. Shorts
  (discovery-only) — treated differently per the channel's own constraint.
- Destination: a new `scripts/` folder in this repo (not the vault — keeps the
  vault read-only-for-this-AIOS as designed).

**Autonomy level:** L2 (Drafted) — AI drafts, Brandon reviews/edits every time.
Not higher: no voice reference exists yet to justify less review.

**KPI:** Bucket = more customers (watch-hours toward YPP). Metric = script drafts
produced per week, target ≥1.

**Alternatives considered:** A full animation/resource-generation pipeline
(candidate #3 from the Mindset interview) — rejected as lower leverage, since it's
downstream of having a script at all. A cadence-enforcement nudge (candidate #2) —
lower leverage than removing the actual bottleneck.

**Owner:** Brandon.

**Out of scope, tracked separately:** a Home Base UI change (modal preview on the
"continue script" container) was raised during scoping — not part of this
workflow; flagged as a follow-up for a main-bro dev session, not built here.

**Shipped (Machine, Phase 3):** Prompt-only (option 1 of 4) — Boring-is-Beautiful
default, since a saved prompt costs nothing to build and the voice gap means every
draft needs manual review regardless of infrastructure. Artifact:
`references/idea-to-script-prompt.md`. Output lands in the new `video-scripts/`
folder (not `scripts/`, which is already used for `sync-codex-skills.sh`).
`bike-method-phase: 1` — run manually, validate before any automation upgrade.
