---
name: level-up
description: Use weekly to find and ship one new automation. Walks the 3Ms interview — Mindset (find the candidate) → Method (scope one) → Machine (build it). Trigger on "let's level up", "what should I automate next", "find me leverage this week", or as a Friday ritual. One run = one shipped artifact.
---

> *Adapted from The Three Ms of AI™. © 2026 Nate Herk. All rights reserved.*
> *The Three Ms of AI™ is a trademark of Nate Herk.*

## What this skill does

Walks the user through the 3Ms each week to surface and ship one new automation. **One interview = one artifact.** It also installs the 3Ms framework into the user's head over time — after 4-6 runs, the user starts spotting opportunities mid-week without prompting because the questions have become internal defaults.

This is the brain-rewire mechanism. The kit doesn't need cron jobs to anchor behavior; it needs `/level-up` running every Friday.

## What `/level-up` is NOT

- Not `/audit`. `/audit` is structural ("is the AIOS built right?"). `/level-up` is functional ("what business leverage am I missing?"). Run `/audit` first if structure is messy.
- Not a multi-candidate planner. One run = one shipped artifact.
- Not a coach. The user does the thinking. The skill conducts the interview.

## When `/level-up` runs

- **First run: Day 14.** After the user has connected ≥1 MCP/script and run `/audit` once. Earlier yields trivial output.
- **Cadence: weekly, Friday afternoon.** Review the week, surface one automation, ship Monday.
- **On-demand any time.** Mid-week if a manual task itches.

## Inputs the skill reads

- `context/priorities.md` — what the user said matters
- `context/about-me.md` — top_pain, role
- `connections.md` — what's reachable, by what mechanism
- `references/3ms-framework.md` — the framework (used to quote principles back)
- `decisions/log.md` — recent decisions (what's already shipped or considered)
- `.Codex/skills/*/SKILL.md` frontmatter — what capabilities exist
- Recent `audits/audit-{date}.md` if present

## Execution — three phases

### Phase 1 — Mindset interview (find the candidate)

Surface 1-3 candidates ranked by leverage. Ask these in order, conversationally:

1. *"Walk me through your week. What did you do 3+ times?"* (frequency)
2. *"Anything that felt manual, boring, or copy-paste?"* (drudgery)
3. *"Anything where you thought 'a smart intern could handle this'?"* (delegation)
4. *"If 500 new clients showed up tomorrow, what would break first?"* (constraint)
5. *"What would give you 500 more clients tomorrow?"* (growth lever)

Quote relevant Mindset principles when they fit:
- *"Sounds like the Default Shift applies — to what extent could AI be leveraged here?"*
- *"This is the Function Breakdown — you're not automating the whole job, just this one piece."*
- *"AI is better than you think and improving faster than you think. If it couldn't do this last quarter, it might be ready now."*

**Output of Phase 1:** numbered list of 1-3 candidate opportunities, one-line "why this is leverage" per candidate. Ask: *"Pick one to scope."*

### Phase 2 — Method interview (scope one)

User picks one candidate. Walk the 5-step Method pipeline:

**Step 1 — Find the constraint.** Which bottleneck does this solve, or which growth lever does it open? Tie back to Phase 1 answers.

**Step 2 — EAD: Eliminate / Automate / Delegate.**
- **Eliminate first:** *"What happens if we just stop doing this?"* If the answer is "nothing breaks" → skill exits cheerfully. *"Don't automate waste."* This is a win, log to `decisions/log.md` and stop.
- **Automate second:** apply 60/30/10 framing. ~60% deterministic, ~30% AI-assisted, ~10% manual.
- **Delegate third:** if too complex/variable/judgment-heavy → suggest a person. Skill exits with a delegation suggestion, log it.

**Step 3 — Map the process.** Five elements:
- Trigger (what kicks it off)
- Data sources (where info comes from)
- Data transformations (how data changes shape)
- Decision points (where it branches)
- Destination (where output goes)

If the user can't articulate any of the five: *"If you can't explain it to a person, you can't explain it to an AI. Sketch it on paper first, then come back."* Skill stops.

**Step 4 — Pick the autonomy level.**

| Level | Name | What happens |
|---|---|---|
| L0 | Manual | No AI |
| L1 | Suggested | AI suggests, human decides every step |
| L2 | Drafted | AI drafts, human reviews and edits |
| L3 | Supervised | AI runs, human validates periodically |
| L4 | Autonomous | AI handles end-to-end |

**Default = lowest level that solves the problem.** Push back on L4 unless the user has explicitly run lower levels first. *"Workflows beat agents. If a decision doesn't HAVE to be made by AI, don't let AI make it."*

**Step 5 — Tie to a KPI.** Which of the Three Buckets does this move?
- More customers
- More value per customer
- Less cost

Plus a specific metric (response time, error rate, conversion rate, time-to-completion). **If the user can't name a bucket and a metric, skill stops.** *"If your automation doesn't move a number, why are you building it?"*

**Output of Phase 2:** scoped automation spec written to `decisions/log.md` as a dated entry with all five answers + autonomy level + KPI. Durable record of what was decided and why.

### Phase 3 — Machine handoff (build it)

Ask: *"How do you want to ship this?"* Options ordered by Boring-is-Beautiful default:

1. **Prompt-only** — saved prompt template the user runs by hand. Zero infrastructure. Highest manual involvement.
2. **Deterministic skill** — SKILL.md that runs a script (no AI step). Best for transformations with clear rules.
3. **AI-assisted skill** — SKILL.md with one AI call inside. Drafts, classifies, summarizes.
4. **Sub-agent** — multi-step agent. Last resort. Only if the work genuinely needs reasoning + tool use.

**Default selected = highest non-AI option that solves the problem.** User has to explicitly choose more autonomy.

Once chosen, route to the appropriate scaffolder:
- `skill-creator` if available globally (Anthropic-shipped)
- `skill-builder` if user has it locally
- Otherwise write a SKILL.md / agent file inline with frontmatter, location, and contents

**Every scaffolded artifact ships with these two headers at top:**

```markdown
---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---
```

This locks the user into Phase 1 of the Bike Method on first build. They can't silently skip manual validation. Phase advances only by explicit edit.

Surface the Machine principles when scaffolding:
- **Lego Principle** — smallest steps, zero-AI first if possible
- **Validation Chain** — test each step before chaining
- **Iteration Mindset** — ship the POC, expand from real usage

## Output contract

Every `/level-up` run produces:

1. **One `decisions/log.md` entry** — dated, with the Method spec
2. **One scaffolded artifact** — prompt, skill, or agent file
3. **A one-screen close** — what was scoped, what was built, and the Bike Method Phase 1 reminder

## Critical implementation rules

1. **One interview = one artifact.** No multi-candidate parallel scoping.
2. **Mindset phase always runs first.** Even if user comes in with a pre-formed idea.
3. **EAD enforces "eliminate first."** If the answer is Eliminate, exit cheerfully — that's a win, not a failure.
4. **Default to the lowest autonomy level that works.** Push back on L4.
5. **Boring-is-Beautiful default in Machine handoff.** Default = highest non-AI option.
6. **Tie-to-KPI is mandatory.** If user can't name bucket + metric, skill stops.
7. **Bike Method ships into every artifact.** `bike-method-phase: 1` in frontmatter.
8. **Read-only on user files except `decisions/log.md` and the new artifact.** Don't modify other existing files.
9. **Trademark + attribution on output.** Every report and every scaffolded artifact references the framework.

## Verification (for the implementer)

- **Dry run on Nate's Herk-2** with no prompt. Expected: skill surfaces 2-3 candidates pulled from his recent activity, priorities, and top_pain. Generic output ("you should build a brief") = fail.
- **Eliminate-first test.** Feed an obviously eliminate-able candidate. Expected: skill suggests Eliminate, exits, logs the win.
- **L4 push-back test.** User asks for autonomous email-replier on first build. Expected: skill insists on L1/L2 first, won't ship L4 without explicit override.
- **Boring-is-Beautiful test.** Candidate solvable with deterministic Python. Expected: skill recommends `(2) deterministic skill` as default.
- **Bike Method anti-skip.** User scaffolds, asks to advance to Phase 4 immediately. Expected: skill makes them read what each phase means and confirm they've validated lower phases.

---

> *The Three Ms of AI™ is a trademark of Nate Herk. © 2026 Nate Herk. All rights reserved.*
