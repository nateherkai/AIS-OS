---
name: agcoach-superpowers-plans
type: source
tags: [ag-coach-pro, plans, superpowers, implementation, catalog]
source_files: [repo:/docs/superpowers/plans/]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Superpowers Plans Catalog

`docs/superpowers/plans/` holds 10 task-by-task implementation plans authored against the `superpowers:subagent-driven-development` / `executing-plans` skills. Each is checkbox-driven (`- [ ]`) and pairs with a sibling design spec (see [[agcoach-superpowers-specs|Specs catalog]]).

| Date | Plan | Goal | Architecture (1-liner) |
|---|---|---|---|
| 2026-04-25 | `fix-stripe-payments-invoices` | Admin dashboard at `app/(super-admin)/index.tsx` is empty — 3 webhook bugs + `stripe-sync` conflict-key mismatch | Fix in `stripe-webhook` + `stripe-sync` edge fns + 1 SQL migration; no UI change |
| 2026-05-04 | `cotton-image-scraper` | Collect 3–5 cotton-grade sample images per grade (16 grades) for Visual ID Drill, Grading carousel, Flashcard photo-front | Python Firecrawl USDA scrape → fal-ai gpt-image-1 gap-fill → Supabase Storage `cotton-grade-images` → JSON merged into `COTTON_GRADES` at startup |
| 2026-05-08 | `ag-tech-gauntlet` | Replace static math drill with 10-question adaptive Formula Gauntlet (formulas + RAG-backed written, Gemini coaching, chapter leaderboard) | `lib/ag-tech-gauntlet.ts` owns assembly/scoring/coaching; single-screen `app/practice/ag-tech/gauntlet.tsx`; extends `ag-tech-formulas.ts` with difficulty tags |
| 2026-05-10 | `livestock-phenotype-accuracy` | Fix AI livestock phenotype accuracy via score anchors, photo quality gate, per-trait confidence, Bryan's calibrated baseline, judge correction loop | Bryan seeds 15–20 anchor images with expert scores → injected as calibration text into every Gemini prompt; quality gate rejects bad inputs; corrections build training dataset |
| 2026-05-12 | `admin-financial-panel` | Add superadmin-only financial panel (net income, MRR, burn, paid school count, trial count) to `app/(admin)/index.tsx` | Single-file edit; `FinancialPanel` component + 2 state vars; queries `schools` directly via `@/lib/supabase`; monthly burn hardcoded post-Apple-Card CSV |
| 2026-05-12 | `job-interview-rag-voice-agent` | Replace phone/video interview sims with real-time ElevenLabs voice grounded in uploaded JD + resume; video adds continuous MediaRecorder scoring | Gemini Vision extracts text → ElevenLabs agent `dynamic_variables` → phone scores PHONE_INTERVIEW_RUBRIC (50pt); video = two-pass transcript+video out of 400pt; session-only, never persisted |
| 2026-05-13 | `teacher-role-bulletproof` | (a) Trinity + Athens ISD log in flawlessly w/o re-signup, (b) every teacher gets `user_metadata.role='teacher'` at every path, (c) only teachers start trials/subs | 3 Supabase migrations + 3 new edge fns (`promote-to-teacher`, `drain-role-promotions`, `start-trial`) + role check on `create-payment-intent` + 4 client edits + Athens repair script + smoke test |
| 2026-05-15 | `ai-brain-second-brain-rebuild` | Rebuild `app/study/ai-brain.tsx` into hardened tool-capable assistant with verified citations, deterministic confidence, injection defenses, customer-service navigation | Single pgvector store w/ `source_type` tagging; new `match-knowledge-v2` edge fn (auth-gated, rate-limited, two-phase ANN); `lib/ai/brain-v2.ts` orchestrates retrieve → sanitize → Gemini tools → validate → confidence; flagged with legacy fallback |
| 2026-05-15 | `brain-personality` | Brain v2 gets situational ag-teacher voice (dry default, warm on encouragement), bullets-first concision; strip raw `[Source:id=<uuid>]` from rendered chat | Prompt-only edit to `AG_COACH_PRO_V2_PROMPT` in `lib/prompts/core-prompts.ts`; one new helper in `lib/ai/brain/citationValidator.ts`; render path calls helper; validator/retrieval/tools untouched |
| 2026-05-15 | `rag-taxonomy` | Backfill `contest_category` + new `subcategory` on 16k+ `knowledge_documents` rows; enforce on ingest; plumb subcategory hint through brain-v2 stack | Additive migration adds `subcategory`/`classified_by`/`classified_at` + `classification_failures` table; Python `scripts/classify_chunk.py` heuristic-first + Gemini Flash fallback <0.6 confidence; `match_knowledge_v2` gets `p_subcategory` arg; `queryRouter.ts` regex keyword map; final `NOT NULL` enforcement migration |
| 2026-05-16 | `brain-rules-accuracy` | Wire Brain chatbot to taxonomy-aware Brain v3 RPC via Gemini Flash intent classifier + post-answer verification gate; eliminates subcategory retrieval misses | `classifyBrainIntent` pre-retrieval → `match_knowledge_v3` strict-or-boost routing → generate → `verifyBrainAnswer` parallel → optional re-retrieve; logs misses to `brain_verification_misses`; feature flag `EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED`; public `askBrainV2` signature unchanged |

## How to use

Each plan is the LLM-executable artifact. Pair every plan with its matching spec ([[agcoach-superpowers-specs]]) — specs explain the **why** and decisions; plans encode the **what** as checkboxes. To resume work on any of these, open the plan file and follow the `subagent-driven-development` skill from the superpowers plugin.

## Related

- [[agcoach-superpowers-specs|Superpowers Specs catalog]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../concepts/agcoach-edge-functions-architecture|Edge Functions Architecture]]
- [[../concepts/agcoach-billing-systems|Billing Systems]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
