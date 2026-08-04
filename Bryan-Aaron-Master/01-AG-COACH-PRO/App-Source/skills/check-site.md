# Skill: Check & Fix agcoachpro.com

## Purpose

After deploying, verify that agcoachpro.com is working correctly end-to-end. Checks routing, auth, CDE module access, and RAG quiz generation. Reports any broken screens or regressions.

---

## When to Use

- After deploying a batch of new modules to Vercel
- When a user reports something is broken on the live site
- As a post-build smoke test before announcing modules are ready

---

## Phase 1 — Deployment Status

Use Vercel MCP to check the latest deployment:

```
mcp__claude_ai_Vercel__list_deployments  → get latest deployment URL and status
mcp__claude_ai_Vercel__get_deployment    → confirm "READY" state, no build errors
mcp__claude_ai_Vercel__get_deployment_build_logs → scan for TypeScript errors or missing modules
```

If the deployment shows errors, diagnose from build logs before proceeding.

---

## Phase 2 — Runtime Log Check

```
mcp__claude_ai_Vercel__get_runtime_logs  → last 100 lines
```

Look for:
- `[MODULE_NAME] No questions generated` — RAG coverage missing for that module
- `Error: generateRAGBatch failed` — Edge Function unreachable
- `Route not found` errors — routing registration missing
- `Cannot read properties of undefined` — TypeScript type mismatch in a new module

---

## Phase 3 — Navigation Smoke Test

Use `mcp__claude_ai_Vercel__web_fetch_vercel_url` to fetch key pages and confirm they load (HTTP 200, not blank):

| Page | Expected |
|---|---|
| `/` | Home/auth screen |
| `/(tabs)/cde` | CDE contest list |
| `/(tabs)/lde` | LDE contest list |
| `/practice/forages` | Forages hub (baseline — always should work) |
| `/practice/dairy-cattle` | Newly built module |
| `/practice/forestry` | Newly built module |

A blank white page (200 with no content) usually means a missing `safeBack` → use `no-blank-pages` skill.

---

## Phase 4 — Module Integration Checklist

For each newly built module, verify these items are wired correctly by reading the source:

1. `lib/store/history.ts` — PracticeType is in the union
2. `lib/tier.ts` — FEATURE_TIERS has the module key
3. `lib/ai/rag-quiz.ts` — TOPIC_QUERIES has entries + TOPIC_CONTEST_CATEGORY maps to correct category
4. `app/contest/[id].tsx` — routing `if`-block exists
5. `constants/contests.ts` — `is_active: true`

---

## Phase 5 — RAG Smoke Test

If runtime logs show quiz generation errors, run `rag-coverage-report` to check chunk counts in Supabase for the affected module's `contest_category`.

---

## Common Fixes

| Symptom | Diagnosis | Fix |
|---|---|---|
| "No questions generated" | RAG chunks missing | Run `python3 ingest_knowledge.py`, then re-deploy |
| Blank white screen on module | `router.back()` instead of `safeBack()` | Run `no-blank-pages` skill |
| Module routes to wrong screen | Missing routing block in `startPractice()` | Add `if` block in `app/contest/[id].tsx` |
| Quiz score not in history | Wrong PracticeType string in `addResult()` | Fix `type:` in `quiz.tsx` `finishQuiz()` |
| Tier gate not working | Missing FEATURE_TIERS entry | Add key in `lib/tier.ts` |
| TypeScript build error | Type mismatch in new module | Check `lib/[module]-quiz.ts` exports match imports |

---

## Deploying

```bash
# Deploy via Vercel MCP:
mcp__claude_ai_Vercel__deploy_to_vercel

# Or manually trigger from project root:
# (user runs: ! npx vercel --prod)
```
