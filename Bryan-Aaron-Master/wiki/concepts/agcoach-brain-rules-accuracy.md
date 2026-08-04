---
name: agcoach-brain-rules-accuracy
type: concept
tags: [ag-coach-pro, rag, brain-v3, taxonomy, accuracy, gemini, intent-classifier]
source_files: [raw/_ingested/2026-05-16-agcoach-pass2-docs-superpowers-plans-2026-05-16-brain-rules-accuracy.md, raw/_ingested/2026-05-16-agcoach-pass2-docs-superpowers-specs-2026-05-16-brain-rules-accuracy-design.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Brain Rules Accuracy (v3 Wiring)

**Goal:** Wire Ag Coach Brain chatbot (`app/study/ai-brain.tsx`) to taxonomy-aware retrieval (Brain v3 RPC) via Gemini Flash intent classifier + post-answer verification gate. Eliminates subcategory retrieval misses — e.g., "slaughter cattle grading score" returning placings/cuts chunks instead of USDA grading rubric.

## Problem Statement

Brain chatbot uses `askBrainV2` → `match-knowledge-v2` (single ANN, no taxonomy filter). Query embedding for "slaughter cattle grading score" drifted to lexically-similar but wrong subcategory chunks. Correct chunk (`id=ac73f75d`, `subcategory=Livestock-USDA-Grading`) existed but ranked below generic livestock-placings content.

Brain v3 (taxonomy-aware, shipped 2026-05-16) was only wired to the quiz path, not the chatbot.

## Architecture: Intent Classifier + Verification Gate

### Component 1 — Pre-retrieval intent classifier (Gemini Flash)

Classifies user question into contest taxonomy before retrieval.

Output: `{ contest_category, subcategory, confidence (0-1), reasoning }`

Routing:
- `confidence ≥ 0.85` → `match_knowledge_v3` with `strict_category=true`, `filter_subcategory`
- `0.6 ≤ confidence < 0.85` → `match_knowledge_v3` with `strict_category=false` (boost only)
- `confidence < 0.6` → fall back to v2 (today's behavior)

### Component 2 — Post-answer verification gate (Gemini Flash, parallel)

After answer generated, Flash checks: "Does cited chunk subcategory match the question topic?"

On mismatch: log to `brain_verification_misses` table → re-retrieve with `strict_category=true` → re-generate → if still fails, surface `confidence: low`.

Skip-C optimization: if classifier confidence ≥ 0.9 AND retrieved chunk subcategory matches prediction → skip verification entirely.

## New Files

- `lib/ai/taxonomy.ts` — canonical `contest_category → subcategory[]` mappings (single source of truth)
- `lib/ai/brain-intent-classifier.ts` — `classifyBrainIntent(question)` Gemini Flash call
- `lib/ai/brain-verifier.ts` — `verifyBrainAnswer(question, answer, citedChunks)` Flash call
- `lib/prompts/brain-prompts.ts` — `BRAIN_INTENT_CLASSIFIER_PROMPT`, `BRAIN_VERIFICATION_PROMPT`
- `supabase/migrations/20260516120000_brain_verification_misses.sql`
- Unit tests: taxonomy, classifier, verifier; Python smoke harness (20 questions)

Modified: `lib/ai/brain-v2.ts` only (public signature unchanged, internal pipeline rebuilt)

## Cost & Latency Budget

| Scenario | Time | Cost |
|---|---|---|
| Typical (classifier + generate) | 4-5s | ~$0.0012 |
| Worst case (verifier fails, re-run) | 7s | ~$0.0022 |

At 1,000 Brain messages/month: ~$2/month incremental.

## Feature Flag

`EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default: `true`). Rollback: set false → rebuild.

## Success Criteria

1. Slaughter cattle grading question cites chunk `ac73f75d` (USDA grading rubric)
2. 20-question test set scores ≥18/20 correct first-try citations
3. Confidence `low` when no in-category chunk above threshold
4. p50 ≤ 5s, p95 ≤ 7s

## Related

- [[agcoach-rag-architecture|RAG Architecture (v1/v2/v3)]]
- [[../sources/agcoach-superpowers-plans|Superpowers Plans Catalog]]
- [[../sources/agcoach-superpowers-specs|Superpowers Specs Catalog]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
