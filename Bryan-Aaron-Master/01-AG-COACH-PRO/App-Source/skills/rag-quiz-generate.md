# Skill: RAG Quiz Generation

## Objective
Generate Texas FFA quiz questions that are **grounded in ingested source documents** — not in the model's training memory. Questions are produced by:
1. Retrieving semantically relevant text chunks from the `knowledge_documents` Supabase table (via the `match-knowledge` Edge Function).
2. Injecting those chunks as the sole context in a Gemini prompt.
3. Instructing Gemini to generate questions answerable **only** from the retrieved text.

**Why this matters vs. the old approach:** The old approach sent a NotebookLM URL in the prompt. Gemini cannot actually read that URL — it generates questions from its training data, which may be stale or hallucinated. RAG generation produces questions directly tied to files you control.

---

## Prerequisites

| Requirement | Details |
|---|---|
| `knowledge_documents` populated | Run `rag-knowledge-ingest` skill first. Senior/Greenhand Quiz PDFs + CSVs must be ingested with `contest_category` = `"Senior FFA Quiz"` or `"Greenhand FFA Quiz"` and `event_type` = `"LDE"`. |
| `match-knowledge` Edge Function deployed | `supabase functions deploy match-knowledge` |
| `EXPO_PUBLIC_GEMINI_API_KEY` | Gemini 2.0 Flash access |
| `EXPO_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (passed as Bearer token to the Edge Function) |

---

## Implementation File

**`lib/ai/rag-quiz.ts`** — drop-in replacement / supplement to `lib/senior-quiz.ts` and `lib/greenhand-quiz.ts`.

### Key Exports

| Export | Signature | Description |
|---|---|---|
| `generateRAGBatch` | `(topic, questionType, count, difficulty) → Promise<QuizQuestion[]>` | Single topic + single type batch. Fetches RAG context then calls Gemini. |
| `generateRAGQuiz` | `(settings: QuizSettings) → Promise<QuizQuestion[]>` | Full quiz — iterates all topics, splits T/F and MC, batches in groups of 3. |

---

## Logic Flow

```
generateRAGQuiz(settings)
│
├─ FOR EACH topic in settings.topics:
│   ├─ fetchContext(topic, topK=10)
│   │   └─ POST /functions/v1/match-knowledge
│   │       ├─ query: TOPIC_QUERIES[topic]  ← semantic search string
│   │       ├─ contest_category: "Senior FFA Quiz" | "Greenhand FFA Quiz"
│   │       ├─ event_type: "LDE"
│   │       └─ top_k: 10
│   │   └─ Returns: context string (concatenated chunks)
│   │
│   ├─ Build Gemini prompt:
│   │   ├─ Inject context as "RETRIEVED SOURCE MATERIAL"
│   │   ├─ Specify count + question type rules
│   │   ├─ Require every question answerable from context only
│   │   └─ Enforce source field = topic name exactly
│   │
│   └─ genAI.generateContent(prompt) with responseSchema → parse JSON
│
├─ Batch 3 topics at a time (CONCURRENCY = 3)
├─ 800ms pause between chunks
└─ Return flat QuizQuestion[] with rag- prefixed IDs
```

---

## Topic Query Strings

These are the semantic queries sent to `match_knowledge` for each FFA source. Tune these if retrieval quality is poor.

| Topic | Query String |
|---|---|
| `FFA Manual` | `FFA history mission creed motto officer stations emblem colors ceremonies programs awards recognition` |
| `Parliamentary Guide` | `parliamentary procedure motions vote requirements debatable amendable second FFA chapter meeting` |
| `Leadership Guide` | `district officer duties responsibilities chapter leadership president vice president secretary treasurer` |
| `Farm Facts` | `Texas agriculture statistics rankings commodity cattle cotton poultry farm ranch acreage cash receipts exports` |
| `Current Events` | `Texas agriculture current events policy water trade biotechnology farm economy environmental` |

---

## Integration Patterns

### Pattern A — Swap the generator in quiz.tsx (recommended for contest mode)
```typescript
// In app/practice/senior-quiz/quiz.tsx, replace:
import { generateQuizQuestions } from '@/lib/senior-quiz';
// With:
import { generateRAGQuiz } from '@/lib/ai/rag-quiz';

// In loadQuiz():
const generated = await generateRAGQuiz(settings);
```

### Pattern B — Use RAG for mock, notebook for custom (hybrid)
```typescript
import { generateQuizQuestions } from '@/lib/senior-quiz';
import { generateRAGQuiz }       from '@/lib/ai/rag-quiz';

const generated = settings.isMock
  ? await generateRAGQuiz(settings)         // grounded in knowledge base
  : await generateQuizQuestions(settings);  // fast, good enough for practice
```

### Pattern C — Single-topic batch (e.g. for study-guide quizlets)
```typescript
import { generateRAGBatch } from '@/lib/ai/rag-quiz';

const questions = await generateRAGBatch('Parliamentary Guide', 'multiple_choice', 10, 'senior');
```

---

## Question Output Schema

Same as `QuizQuestion` in `lib/senior-quiz.ts`:

```typescript
{
  id: string;           // "q-rag-{topic}-{timestamp}-{index}"
  text: string;         // question text
  type: 'multiple_choice' | 'true_false';
  options: string[];    // 4 options for MC, ["True","False"] for T/F
  correctAnswer: string; // one of the options verbatim
  explanation: string;  // single sentence citing the source fact
  source: string;       // exactly the topic name (e.g. "FFA Manual")
}
```

---

## Fallback Behavior

| Scenario | Behavior |
|---|---|
| `knowledge_documents` empty for topic | `fetchContext` returns `""` → `generateRAGBatch` returns `[]` and logs a warning |
| Edge Function unreachable | Throws — caller should catch and fall back to `generateQuizQuestions` |
| Gemini returns wrong count | Logged as warning; partial array returned |
| `EXPO_PUBLIC_GEMINI_API_KEY` missing | Throws immediately with clear message |

---

## Adding New Topics

1. Add the topic to `TOPIC_QUERIES` in `lib/ai/rag-quiz.ts` with a descriptive semantic query.
2. Add to `TOPIC_CONTEST_CATEGORY` mapping if it belongs to a different contest.
3. Ensure documents for that topic are ingested with the correct `contest_category` value.
4. Add the topic string to the relevant `QUIZ_SOURCES` array in `lib/senior-quiz.ts` or `lib/greenhand-quiz.ts`.

---

## Storage

| Asset | Path |
|---|---|
| Implementation | `lib/ai/rag-quiz.ts` |
| Knowledge base table | `knowledge_documents` (Supabase) |
| Retrieval Edge Function | `supabase/functions/match-knowledge/index.ts` |
| Ingest script | `ingest_knowledge.py` |
| Ingest skill doc | `skills/rag-knowledge-ingest.md` |

---

## Quick Start

```bash
# 1. Make sure knowledge is ingested (run once per new documents)
python3 ingest_knowledge.py

# 2. Deploy the retrieval function (run once or on changes)
supabase functions deploy match-knowledge

# 3. Use in code (see Integration Patterns above)
import { generateRAGQuiz } from '@/lib/ai/rag-quiz';
const questions = await generateRAGQuiz({ topics: ['FFA Manual'], questionCount: 10, type: 'mixed', isMock: false });
```
