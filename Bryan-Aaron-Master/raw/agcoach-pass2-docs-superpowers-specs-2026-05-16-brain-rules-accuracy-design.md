# Ag Coach Brain — Rules Accuracy Upgrade

**Date:** 2026-05-16
**Status:** Design — pending user review
**Owner:** Bryan
**Related:** `2026-05-15-rag-taxonomy-design.md`, `2026-05-15-ai-brain-second-brain-rebuild-design.md`

---

## Problem

Ag Coach Brain chatbot (`app/study/ai-brain.tsx`) returns incorrect rule answers despite the correct rule chunk being present in `knowledge_documents`.

### Concrete failure (2026-05-16)

User question: *"How do I calculate my slaughter cattle grading score in the Livestock CDE?"*

Brain answered with the **placings/cuts scoring system** (50-point class, pair switches, simple bust). The correct answer is the **USDA grading scoring system** (quality grade: 4/3/2/0 points per half-grade; cutability: 6/4/2/0 points per half-grade; 50 points per class).

Diagnosis (verified via SQL):
- Correct chunk **exists**: `id=ac73f75d-1499-4460-a39c-2d59e7cdc316`, `contest_category=Livestock`, `subcategory=Livestock-USDA-Grading`, `source_file=Livestock_Rules_UPDATED_8.20.24.pdf`.
- Brain cited unrelated chunks (`cf518e1c`, `f6d1ec49`, `8d933bef`) — generic livestock placings/cuts content.
- Root cause: **retrieval miss**. Brain chatbot uses `askBrainV2`, which calls `match-knowledge-v2`. v2 is a single ANN over all chunks with no taxonomy-aware filtering or subcategory boost. The query embedding for "slaughter cattle grading score" drifts toward chunks that lexically overlap on "score" / "cattle" but live in the wrong subcategory.

Brain v3 (taxonomy-aware, shipped 2026-05-16 to quiz path) was never wired into the chatbot.

---

## Goal

Brain chatbot must answer rule-grounded questions with the correct rule chunk, every time, when the chunk exists in `knowledge_documents`. Accept up to ~7s worst-case latency in exchange for accuracy.

**Non-goals:**
- Improving answers when the chunk is genuinely missing (separate ingest problem).
- Restructuring `knowledge_documents` schema.
- Changing the quiz retrieval path (already on v3).

---

## Success criteria

1. The slaughter-cattle-grading question above returns the USDA grading rubric, citing chunk `ac73f75d`.
2. A reproducible test set of 20 rule questions across Livestock, Wool, Meats, Horse, Ag Tech, Forestry, Wildlife scores ≥18/20 correct citations on first try.
3. Brain self-reports `confidence: low` (and refuses to answer authoritatively) when no in-category chunk is retrieved above threshold.
4. Latency p50 ≤ 5s, p95 ≤ 7s.

---

## Approach: Intent Classifier + Verification Gate (A + C)

Two additions to the Brain chatbot path. Both reuse infrastructure already shipped (Brain v3 RPC, Gemini Flash).

### Component 1 — Intent classifier (pre-retrieval)

Before retrieval, run a fast Gemini Flash call that classifies the user's question into the contest taxonomy.

**Input:** the user's question string.

**Output (structured JSON, enforced via `responseSchema`):**

```ts
{
  contest_category: string | null,      // one of Livestock, Wool, Meats, Horse, Forestry, Wildlife, Ag Tech, Ag Sales, FFA Knowledge, FFA Admin, App Meta, or null
  subcategory: string | null,           // one of the known subcategories under that category, or null
  confidence: number,                   // 0.0 – 1.0
  reasoning: string                     // one short sentence — for logging / debug only, not surfaced
}
```

The category/subcategory enum is built from a fixed list defined in `lib/ai/taxonomy.ts` (new file) and shared with the classifier prompt. The list is the same set already used by Brain v3 / the backfill scripts — single source of truth.

**Routing logic:**

| Classifier output | Retrieval call |
|---|---|
| `confidence ≥ 0.85` and `contest_category` non-null | `match_knowledge_v3` with `filter_category=<cat>`, `strict_category=true`, `filter_subcategory=<subcat or null>` |
| `confidence ≥ 0.6` and `< 0.85` | `match_knowledge_v3` with `filter_category=<cat>`, `strict_category=false` (boost only, not filter) |
| `confidence < 0.6` or category null | Fall back to existing v2 behavior (no taxonomy filter) |

This means an obviously-Livestock question gets hard-filtered to Livestock chunks; ambiguous questions get the boost but not the filter; truly-unknown questions degrade gracefully to today's behavior.

### Component 2 — Verification gate (post-answer)

After the main answer is drafted, run a second Gemini Flash call that asks:

> "Here is a user's question and the answer Brain produced, including which chunks it cited. Does the cited chunk's subcategory match the topic of the question? Respond with `{match: boolean, reason: string}`."

Inputs: question, answer text, list of cited chunks with their `contest_category` and `subcategory` fields.

**On `match: false`:**
1. Log the miss to a new `brain_verification_misses` table (question, original answer chunks, classifier output, verifier reason).
2. Re-retrieve with `strict_category=true` using the classifier's category, even if confidence was below the 0.85 threshold.
3. Re-generate the answer with the new chunks. Prepend a short "Updating to use the correct rulebook section…" note so streaming UIs don't look broken.
4. If the second answer still verifies false, surface `confidence: low` and a message asking the user to clarify the contest area.

**Skip-C optimization:** If classifier `confidence ≥ 0.9` AND retrieval returned ≥1 chunk whose subcategory matches the classifier's predicted subcategory, skip C entirely. The check is deterministic and free.

### Streaming order

To keep p50 latency reasonable:

1. Run intent classifier (parallel with no other work) → ~500ms.
2. Run retrieval → ~300ms.
3. Begin streaming the main answer → first token ~1s after retrieval, full answer ~3s.
4. **In parallel with answer streaming**, kick off verification call. It finishes around the same time as the answer.
5. If verification passes, no UI change. If verification fails, append a correction message below the original answer (do not erase — transparency).

User sees first words at ~1.8s, full primary answer at ~4-5s, correction (rare) at ~6-7s.

---

## File-level plan

### New files

- `lib/ai/taxonomy.ts` — canonical list of `contest_category` → `subcategory[]` mappings. Exported as a typed const. Source of truth for classifier prompt, classifier enum, and any future taxonomy-aware code.
- `lib/ai/brain-intent-classifier.ts` — `classifyBrainIntent(question: string): Promise<IntentResult>`. Wraps Gemini Flash with structured output. Uses `parseAIJson` for safety. Returns the JSON shape above. Falls back to `{contest_category: null, confidence: 0}` on any error.
- `lib/ai/brain-verifier.ts` — `verifyBrainAnswer(question, answer, citedChunks): Promise<{match: boolean, reason: string}>`. Same Flash + structured output pattern. Falls back to `{match: true}` on error (don't punish the user for our infra hiccups).
- `supabase/migrations/20260516120000_brain_verification_misses.sql` — table `brain_verification_misses` (id, created_at, user_id, question, classifier_output jsonb, original_cited_chunks jsonb, verifier_reason, second_answer_succeeded bool). RLS: only `superadmin` selects. Inserts done from edge function with service role.

### Modified files

- `lib/ai/brain-v2.ts` → renames internal `askBrainV2` to `runBrainPipeline`. New public `askBrainV2` orchestrates: classifier → retrieval (v3 or v2 fallback) → generate → verify → optional re-retrieve. Public signature unchanged so `app/study/ai-brain.tsx` does not need to change.
- `supabase/functions/match-knowledge-v2/index.ts` → no changes. Stays as legacy fallback.
- `supabase/functions/match-knowledge-v3/index.ts` → no changes (already supports `strict_category` + `filter_subcategory`).
- `lib/prompts/brain-prompts.ts` (new or extend existing) → add two prompts: `BRAIN_INTENT_CLASSIFIER_PROMPT`, `BRAIN_VERIFICATION_PROMPT`. Pure strings; reusable.

### Feature flag

`EXPO_PUBLIC_BRAIN_ACCURACY_V1_ENABLED` (default `true`). Setting to `false` falls all the way back to today's v2 path. Used for fast rollback if the classifier mis-routes too often in practice.

---

## Cost & latency budget

Per Brain message (worst case, classifier + verifier both fire, re-retrieval happens):

| Step | Time | Cost (Gemini, USD) |
|---|---|---|
| Intent classifier (Flash) | 500ms | ~$0.00005 |
| Retrieve v3 | 300ms | $0 (Supabase RPC) |
| Generate (Pro) | 2-4s | ~$0.001 |
| Verifier (Flash, parallel) | 600ms (hidden behind generate) | ~$0.00008 |
| Re-retrieve + re-generate (rare, <10%) | +2-3s | ~$0.001 |

Typical message: 4-5s, ~$0.0012.
Worst case (verifier fails, re-run): 7s, ~$0.0022.

At 1000 Brain messages/month: ~$2/month incremental. Negligible vs current Brain spend.

---

## Failure modes considered

1. **Classifier hallucinates a subcategory** that doesn't exist. *Mitigation:* enum constraint in `responseSchema` (Gemini structured output rejects out-of-enum values). On parse failure, fall back to v2.
2. **Classifier confident but wrong** (e.g., predicts Forestry for a Wildlife question). *Mitigation:* `strict_category=true` would return zero chunks; v3 already handles empty result by widening (per the 2026-05-15 RAG taxonomy design — "8x ANN widening to preserve top-N signal under rare-category filters"). If still empty, fall back to v2 with the original query.
3. **Verifier loop** — answer 1 fails, answer 2 also fails, answer 3 also fails. *Mitigation:* hard cap at one re-retrieval. After that, surface `confidence: low` and stop.
4. **Verifier wrongly rejects a correct answer**. *Mitigation:* log every miss so we can review. If the false-rejection rate goes above ~5% in early dogfooding, tune the verifier prompt or raise the skip-C confidence threshold.
5. **Latency creep on low-end devices** — the classifier adds visible delay to the "thinking…" state before first token. *Mitigation:* show a contextual loading message ("Pinpointing the right rulebook…") so the user sees progress.

---

## Verification plan

Before merge:

1. **Smoke test** — re-ask the slaughter cattle grading question. Confirm answer cites `ac73f75d` and matches the USDA grading rubric. Confirm no placings chunks cited.
2. **Test set** — 20 rule questions across all 7 active CDE categories. Track citation accuracy and verifier-trigger rate. Target ≥18/20 first-try correct.
3. **Latency test** — measure p50/p95 across the test set. Confirm within budget.
4. **Fallback test** — disable feature flag. Confirm behavior identical to today's `askBrainV2`.
5. **Edge cases** — ambiguous question ("how do I score better?"), no-match question ("what's the capital of France?"), classifier-error injection (mock Flash failure). Confirm graceful degradation each time.

The test set + automated scoring lives in `tests/test_brain_accuracy.py` (new). Run before every Brain-related deploy.

---

## Open questions

None blocking. Implementation can begin after user review of this spec.
