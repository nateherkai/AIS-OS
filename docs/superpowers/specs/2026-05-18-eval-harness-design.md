# GravityClaw Eval Harness — Design

## Context

Bryan asked how to improve quality, functionality, and accuracy of his AIS. Two of the three subprojects shipped (Dream→Skill promote pipeline; Live HUD). This third subproject targets the missing piece: **measurement**. The bot has factuality guardrails baked into its system prompt (`gravity-claw/src/agent/factuality.ts`) and an `accuracy.ts` filesystem audit, but nothing actually measures whether the bot is right. If a prompt change, model swap, or RAG drift degrades answers, Bryan finds out by being personally wrong in front of a customer — not by signal in his dashboard.

This spec defines an accuracy regression harness: a hand-curated YAML eval set of ~30 known questions, a runner that calls `askClaude` for each question, a composite scorer (substring includes/excludes + LLM judge), and a mission-control dashboard panel that shows the score over time and surfaces failing questions.

Two prior subprojects deferred / out of scope:
- AIS quality v1.1 polish (memory hygiene cleanup, retrieval recall@k) — separate specs if needed later.

---

## Decisions Locked (from brainstorm)

| # | Question | Choice |
|---|---|---|
| 1 | Eval set authoring | Hand-written YAML, version-controlled |
| 2 | Scoring | Composite: `must_include` + `must_not_include` + LLM judge (Haiku), avg of 3 dimensions |
| 3 | Schedule | Manual `/eval` on demand + launchd nightly cron at 02:30 |
| 4 | Storage / surface | JSON files in `AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json` + new `/eval` panel in mission-control |
| 5 | Target | `askClaude` function directly (bypass Telegram); fastest, isolates LLM behavior |

---

## Architecture

**Name:** `/eval` — accuracy regression harness for GravityClaw.

**Run flow:**
1. `/eval` slash command (or nightly cron) invokes `node bot/dist/scripts/eval-run.js`
2. Loads + validates `gravity-claw/data/evals/eval-set.yaml`
3. For each question: call `askClaude(question, useHistory=false)` → reply
4. Score reply: substring checks + Haiku judge call → composite 0-100
5. Aggregate: overall score, per-category scores, list of failing questions (composite < 60)
6. Write `AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json` (today's run; overwrites if same-day re-run)
7. If overall score changed by >10 absolute percentage points vs prior run, append entry to `decisions/log.md`

**Composite scoring (per question):**
- 33%: `must_include` — % of required strings present in reply (case-insensitive)
- 33%: `must_not_include` — % of banned strings absent
- 33%: LLM judge — Haiku scores reply 0-100 vs `expected_summary` on a rubric
- composite = round((include_pct + exclude_pct + judge) / 3)

**Surface:** new `/eval` page in mission-control. Reads `dashboard/data/eval-runs/*.json`. Renders:
- Overall score (big number)
- 30-day trend sparkline
- Per-category bars
- Failing-questions list (composite < 60) with judge reasoning

No realtime; reload-on-demand. Mirrors the read-only pattern of the existing dream cards panel.

---

## Components

**Bot (`gravity-claw/`):**
- `data/evals/eval-set.yaml` — seed set ~30 questions, hand-curated
- `data/evals/eval-set.schema.json` — JSON Schema for validation
- `src/scripts/eval-run.ts` — CLI entrypoint
- `src/agent/eval-runner.ts` — iterates eval set, calls `askClaude`, returns raw results
- `src/agent/eval-scorer.ts` — composite scoring (includes + excludes + judge)
- `src/agent/__tests__/eval-scorer.test.ts`
- `src/agent/__tests__/eval-runner.test.ts`

**AIS-OS / mission-control:**
- `dashboard/data/eval-runs/.gitkeep` — output dir. JSON files ARE committed (small, version-controlled history is useful for diffing score regressions)
- `dashboard/scripts/eval-cron.sh` — invoked by launchd
- `mission-control/src/app/eval/page.tsx`
- `mission-control/src/app/eval/page.module.css`
- `mission-control/src/components/eval/ScoreTrend.tsx`
- `mission-control/src/components/eval/CategoryBars.tsx`
- `mission-control/src/components/eval/FailingQuestions.tsx`
- `mission-control/__tests__/ScoreTrend.test.tsx`
- `mission-control/__tests__/CategoryBars.test.tsx`
- `mission-control/__tests__/FailingQuestions.test.tsx`

**Skill:**
- `~/.claude/skills/eval/SKILL.md` — `/eval` slash command wrapping the script

**Reused:**
- `src/ai/claude.ts:askClaude` — bot LLM call (target of eval)
- Anthropic client init pattern from `claude.ts` for Haiku judge
- `data/evals/` convention mirrors `data/youtube/`, `data/livestock-judging/`
- Dashboard JSON pattern from `dashboard/data/dreams/` — same shape

**Types (in `eval-runner.ts`):**

```ts
interface EvalQuestion {
  id: string;
  category: string;
  question: string;
  must_include: string[];
  must_not_include: string[];
  expected_summary: string;
}

interface QuestionResult {
  id: string;
  category: string;
  question: string;
  reply: string;
  scores: {
    include_pct: number;   // 0-100
    exclude_pct: number;   // 0-100
    judge: number | null;  // 0-100, null if judge errored
    composite: number;     // 0-100
  };
  judge_reasoning?: string;
  duration_ms: number;
  error?: string;
}

interface EvalRun {
  date: string;
  generated_at: string;
  total_questions: number;
  overall_score: number;
  by_category: Record<string, number>;
  failing_questions: QuestionResult[]; // composite < 60
  results: QuestionResult[];
}
```

**Cron:**
- macOS launchd plist at `~/Library/LaunchAgents/com.bryan.aios-eval.plist`, fires at 02:30 local (after `/dream` at 02:00)
- Production fallback: Railway cron if the bot is hosted there with persistent storage for output

---

## Data Flow

```
INVOCATION
  Manual: user types `/eval` in Claude Code
  Nightly: launchd → dashboard/scripts/eval-cron.sh (02:30)
  Both run: node bot/dist/scripts/eval-run.js
       │
       ▼
eval-run.ts
  1. Load YAML at data/evals/eval-set.yaml
  2. Validate schema → fail-fast on violations
  3. For each question (sequential, rate-limit friendly):
        result = await runOne(q)
        results.push(result)
  4. Aggregate: overall, by_category, failing_questions
  5. Write JSON → AIS-OS/dashboard/data/eval-runs/YYYY-MM-DD.json
  6. Print summary to stdout (overall + top 3 failures)
  7. If |today - yesterday| > 10 absolute pp, append to decisions/log.md
       │
       ▼
runOne(q)  (eval-runner.ts)
  startTs = Date.now()
  reply = await askClaude(q.question, false)
  scores = await score(q, reply)
  return { id, category, question, reply, scores, duration_ms }
       │
       ▼
score(q, reply)  (eval-scorer.ts)
  include_pct = checkIncludes(q.must_include, reply)
  exclude_pct = checkExcludes(q.must_not_include, reply)
  { judge, judge_reasoning } = await llmJudge(q, reply)
  composite = judge === null
    ? round((include_pct + exclude_pct) / 2)
    : round((include_pct + exclude_pct + judge) / 3)
  return { include_pct, exclude_pct, judge, composite, judge_reasoning }

       ─── separately ───
       │
       ▼
mission-control /eval page (browser)
  Server-render: read all dashboard/data/eval-runs/*.json
  Latest = today's; trend = last 30
  Render: big score, 30-day sparkline, category bars, failing list
  Reload-on-demand (no realtime)
```

**LLM judge prompt:**

```
You score a chatbot reply against an expected summary.

Question: {q.question}
Expected: {q.expected_summary}
Reply:    {reply}

Score correctness 0-100. 100 = matches expected facts and intent.
0 = wrong, contradicts, or refuses without reason.
Return JSON only: {"score": <int>, "reasoning": "<one sentence>"}
```

Judge uses Haiku.

**Cost per nightly run (current bot uses Sonnet/Opus per config):**
- 30 askClaude calls ≈ $0.30
- 30 judge calls (Haiku) ≈ $0.02
- Total ≈ $0.32/night = ~$10/month

---

## Eval Set Seeding

Initial ~30 questions across 6 categories (≈5 each). See plan for the full seed content.

| Category | What it tests |
|---|---|
| `business_pricing` | Tier prices, package names — must include exact $ figures |
| `business_identity` | Who buys, what for, Q3 goals — Texas FFA, 50 schools, $120K |
| `bryan_identity` | Bryan's bio facts — Overton HS, wife Jennifer, son Vance |
| `aios_conventions` | Where things live (decisions/log.md, etc.) — AIS-OS conventions |
| `factuality_red_lines` | Hallucination guards — bot MUST say "check live source", NOT invent numbers |
| `ffa_domain` | FFA/CDE knowledge — Bryan's deepest domain expertise |

**Special category — `factuality_red_lines`:** Questions where the right answer is "I can't verify that — query the live source." Bot must NOT invent. `must_include` = "check Supabase" / "live tool" / "would need to query" etc. `must_not_include` = any specific made-up number/name/status.

**Authoring workflow:**
1. Engineer creates `data/evals/eval-set.yaml` with the 30 seed entries (plan task has full text)
2. Bryan edits in his IDE — adds his real Q/A pairs over time
3. Eval set version-controlled — `git log data/evals/eval-set.yaml` shows expectation history
4. Score regressions are diffable: "did the bot get worse" vs "did we change the expectation"

**Schema validation** at runtime:
- Required: `id`, `category`, `question`, `must_include`, `must_not_include`, `expected_summary`
- Unique `id` across set
- `must_include`/`must_not_include` are string arrays (may be empty)
- Fail-fast with line-number error if invalid

---

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| YAML parse error | `yaml.load` throws | Print line + error, exit 1, no JSON written |
| Schema validation fails | Pre-check | Print violations, exit 1 |
| `askClaude` throws | try/catch per Q | Record `error`, all scores=0, continue |
| Judge throws | try/catch per scorer | Composite from 2/3 dims (judge=null) |
| Output dir missing | Pre-write check | `mkdir -p`, then write |
| Same-day re-run | Exists check | Overwrite (intentional — latest wins) |
| Rate limit (429) | Response code | Exp backoff retry once; second fail → record error |
| Ctrl-C mid-run | Signal handler | Write partial JSON with `incomplete: true` |
| Empty eval set | length check | Print "no questions", exit 0 |

**Logging:**
- stdout: one summary line + 3 lowest-scoring Qs
- stderr: API errors per question
- `decisions/log.md`: only on score change >10 absolute percentage points vs prior run

---

## Testing

**Unit (`gravity-claw/src/agent/__tests__/`):**

`eval-scorer.test.ts`:
- `checkIncludes` 100% when all strings present, 0% when none, 50% on partial
- case-insensitive substring matching
- `checkExcludes` mirror logic
- `score()` composite formula
- judge throw → composite from 2 dimensions (judge=null)
- judge prompt format includes question + expected + reply

`eval-runner.test.ts`:
- `runOne` calls `askClaude(q, false)` (no history)
- `runOne` records `duration_ms`
- `runOne` catches `askClaude` errors → returns result w/ error, scores=0
- `aggregate` computes `overall_score` = mean of composites
- `aggregate` groups `by_category` correctly
- `aggregate` filters `failing_questions` to composite < 60
- YAML loader rejects duplicate ids
- YAML loader rejects missing required fields

**Integration (opt-in, `@vitest.mark.live`):**
- Run script against 3-question synthetic set with real API
- Assert JSON written to tmp dir with valid shape

**Component (mission-control):**
- `ScoreTrend` renders sparkline with N data points + empty state
- `CategoryBars` one bar per category, sorted desc
- `FailingQuestions` empty state + populated list with judge reasoning

**Manual verification:**
1. Author 3 seed questions in `data/evals/eval-set.yaml`
2. `npx tsx src/scripts/eval-run.ts` → JSON appears
3. Score plausible (>50% on real questions bot knows)
4. `npm run dev` in mission-control → `/eval` renders today's score + trend
5. Tweak one expected_summary to break it → re-run → failing_questions populated
6. Set up launchd → next day at 02:30 JSON appears

**Performance budget:**
- Full 30-Q run: <2 minutes (sequential)
- Per-question: <4s (Sonnet reply + Haiku judge)
- JSON output: <50KB per run

---

## Out of Scope (deferred to future plans)

- Eval set mined from past Telegram conversations (option 2 in brainstorm — manual YAML wins for v1)
- Full bot via Telegram channel (option in brainstorm — `askClaude` direct wins for v1)
- Supabase storage of runs (JSON-only for v1; add later if querying across runs needed)
- Deploy-blocking eval (no Railway post-deploy hook in v1)
- Per-question pass/fail thresholds (composite < 60 is the only threshold for v1)
- Retrieval recall@k harness — different spec
- Memory hygiene / wiki dedup — different spec
- Hallucination prevention (already in `factuality.ts`; this measures it, doesn't prevent)
- Public-facing scoreboard (local dashboard only for v1)
