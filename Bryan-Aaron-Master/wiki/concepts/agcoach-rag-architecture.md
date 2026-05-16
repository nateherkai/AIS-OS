---
name: agcoach-rag-architecture
type: concept
tags: [ag-coach-pro, rag, pgvector, gemini, supabase, ai, retrieval]
source_files: [raw/_ingested/2026-05-16-agcoach-CLAUDE.md, raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md, raw/_ingested/2026-05-16-agcoach-SCHEMA.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — RAG Architecture

Retrieval-Augmented Generation powers all CDE quiz modules and the Ag Coach Brain chatbot.

## Stack

- **Vector store**: Supabase `knowledge_documents` table — pgvector halfvec, 3072 dimensions, HNSW index, ~390 MB, 20,987 chunks as of 2026-05-16
- **Embeddings**: `gemini-embedding-2-preview@3072` (hardcoded everywhere — dim assertion at runtime)
- **Retrieval**: Supabase Edge Function `match-knowledge` (v1/v2/v3)
- **Generation**: `gemini-2.0-flash` with structured JSON output schema

## RAG Quiz Generation Flow

1. Student starts practice quiz
2. App sends semantic query to `match-knowledge` Edge Function
3. Edge function embeds query with `gemini-embedding-2-preview`
4. pgvector cosine similarity search against `knowledge_documents`
5. Returns top-K matching chunks as grounding context
6. Chunks + prompt → `gemini-2.0-flash` with structured output schema
7. Returns `QuizQuestion[]` (multiple choice + true/false + explanations)

Key files: `lib/ai/rag-quiz.ts` (engine + 150+ TOPIC_QUERIES), `supabase/functions/match-knowledge/index.ts`

## Three Retrieval Versions

**v1 (legacy)**: `match_knowledge()` RPC — returns `{context, sources}` string. Still wired as fallback in `rag-quiz.ts`.

**v2 (Brain v2)**: `match_knowledge_v2()` — chip-less unified retrieval, soft category boost. Two-phase ANN+boost RPC. Per-uid rate limit. Rulebook slot reservation.

**v3 (Brain v3, current)**: `match_knowledge_v3()` — hard `strict_category` boolean filter with 8× ANN widening (preserves top-N signal under rare-category filters) + `+0.04` subcategory boost. Shipped 2026-05-16.

## Taxonomy Classification (Brain Accuracy v1)

All 20,987 knowledge chunks classified as of 2026-05-16 backfill:
- Fields: `contest_category`, `subcategory`, `classified_by` ∈ {heuristic, llm}
- Phase 1 heuristic: 18,716 chunks (89.2%) into 25+ contest cats — top: Ag Tech 3600, Horse 2158, Meats 1988, Wildlife 1240, Forestry 934, Livestock 574
- Phase 2 sentinel categories for remaining 2,271: `FFA Knowledge`, `FFA Admin`, `Forestry`, `Ag Sales`, `App Meta`

**Gemini Flash Intent Classifier** (`lib/ai/brain-intent-classifier.ts`): maps query → `{contest_category, subcategory, confidence}` via fixed taxonomy (`lib/ai/taxonomy.ts`, 41 categories from live DB).

**Confidence routing**: ≥0.85 → v3 strict_category, 0.6–0.85 → v3 boost-only, <0.6 → v2 fallback.

**Brain Verifier** (`lib/ai/brain-verifier.ts`): checks cited-chunk subcategory matches question. On mismatch, logs to `brain_verification_misses` + re-retrieves. Skip when classifier ≥0.9 AND a cited chunk matches predicted subcategory.

## Key Rules

- Every new RAG topic must have an entry in `TOPIC_QUERIES` map in `lib/ai/rag-quiz.ts` or quiz generation silently degrades
- Gemini structured output: build `Schema` from `@google/generative-ai`, use `responseMimeType: 'application/json'`, parse with `parseAIJson` from `lib/ai/parser.ts`
- RAG ≠ Pinecone (Pinecone reserved for Claude session memory only)

## Related

- [[../sources/agcoach-schema|Database Schema (knowledge_documents table)]]
- [[../sources/agcoach-business-brain|Business Brain (AI Features section)]]
- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../concepts/agcoach-contest-modules|Contest Modules]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
