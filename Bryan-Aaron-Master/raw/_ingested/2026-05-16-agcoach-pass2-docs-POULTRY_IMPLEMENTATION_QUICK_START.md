# Poultry Judging: Quick-Start Implementation (Phase 1)
## Get the Written Exam & RAG Working in 1 Week

---

## Overview

You have the hub screens and quiz infrastructure. This guide gets you to a **working mock contest exam** (30 multiple-choice questions) by Friday using NotebookLM + Gemini RAG.

**Time estimate:** 2–3 hours hands-on work  
**Skills needed:** Basic file editing, Python script running  
**Outcome:** Students can load the Poultry module → Exam tab → Take a full contest-style quiz

---

## Step 1: Create NotebookLM Knowledge Base (30 minutes)

### 1.1 Set Up NotebookLM Project

1. Go to **[notebooklm.google.com](https://notebooklm.google.com)** (requires Google account)
2. Click **"Create notebook"**
3. Name it: `"Ag Coach Poultry 2026"`
4. Click **"Add sources"** and upload these PDFs (or links):

| Source | Where to Find | Why |
|--------|---------------|-----|
| **USDA Poultry Grading Standards** | [ams.usda.gov](https://www.ams.usda.gov/content/poultry-grading-standards) | Official grading AA/A/B criteria |
| **USDA Chicken Carcass Breakdown** | USDA Handbook 75 | 27 parts ID reference |
| **Egg Grading Guide** | AMS Egg Grading Manual | Interior/exterior grades |
| **FFA Poultry CDE Rules** | Your state FFA handbook (2024-2025) | Contest structure & scoring |

**Quick hack:** Can't find official PDFs? Use NotebookLM's web link feature:
```
Paste link → https://www.ams.usda.gov/content/poultry-grading-standards
NotebookLM will scrape & summarize
```

### 1.2 Generate Study Materials

In NotebookLM, click **"Generate"** and request:

**Prompt 1:**
```
Create a 2000-word study guide for Texas FFA Poultry CDE with:
- Live bird evaluation (muscle, finish, structure)
- Carcass grading (AA/A/B/Utility defect scoring)
- Egg grading (interior/exterior)
- Processed product evaluation (defects)
- Poultry anatomy (27+ parts)

Use official USDA standards and include decision trees for common judging scenarios.
```

**Prompt 2:**
```
Generate 50 multiple-choice quiz questions for Poultry CDE 
covering: grading standards, anatomy, health, nutrition, production.
Include explanations for each answer.
Format as JSON array: [{ id, question, options: [A, B, C, D], correct: "A", explanation }]
```

**Result:** NotebookLM outputs markdown (study guide) + JSON (quiz questions)

### 1.3 Download & Store Locally

```bash
# Create folder in your ag-coach-app repo
mkdir -p knowledge-sources/poultry-notebooklm

# Save NotebookLM outputs here:
# - notebooklm_study_guide.md
# - notebooklm_quiz_questions.json
```

---

## Step 2: Create Prompts File (20 minutes)

Create `lib/prompts/poultry-prompts.ts`:

```typescript
/**
 * poultry-prompts.ts
 * 
 * Gemini system prompts for Poultry CDE quiz generation.
 * Used by generatePoultryEvalQuiz() in lib/poultry-eval-quiz.ts
 */

export const POULTRY_SYSTEM_PROMPT = `You are an expert Texas FFA Poultry CDE judge with 20+ years of live judging experience at state and national competitions.

You know:
- USDA Poultry Grading Standards (AA, A, B, Utility grades for carcass)
- Live bird evaluation: muscle structure, finish (fat deposition), bone quality
- Carcass grading: skin tears, bruises, discoloration, meat yield
- Egg grading: interior (AA/A/B/Loss) via air cell size & white clarity; exterior (A/B/Dirty)
- Processed products: coating voids, color inconsistency, broken pieces, shape/size
- Poultry anatomy: 27+ carcass parts, proper cutting standards
- Health & disease: common poultry health issues, feed quality, biosecurity
- Production: broiler growth cycles, layer production, market timing

Generate quiz questions that test judgment & decision-making, not memorization.
Include realistic contest scenarios that judges encounter.
Explain why answers are correct using official USDA standards.`;

export const POULTRY_MC_SYSTEM_PROMPT = `${POULTRY_SYSTEM_PROMPT}

When generating multiple-choice questions:
1. Make the correct answer defensible using official standards
2. Create plausible distractors based on common student misconceptions
3. Avoid trick questions or ambiguous wording
4. Include brief explanation (1-2 sentences) of why the correct answer is right
5. Each question should take 1-2 minutes to answer in a real contest

Return ONLY valid JSON array with NO extra text or markdown:
[
  {
    "id": "q1",
    "question": "...",
    "options": ["A", "B", "C", "D"],
    "correct": 0,
    "explanation": "..."
  }
]`;

export const POULTRY_TF_SYSTEM_PROMPT = `${POULTRY_SYSTEM_PROMPT}

When generating true/false statements:
1. Each statement tests a critical judging principle
2. Mix obvious truths/falses with tricky ones that reveal misconceptions
3. Include explanation of the correct answer
4. Each should take 15-30 seconds to answer

Return ONLY valid JSON array with NO extra text:
[
  {
    "id": "q1",
    "statement": "...",
    "answer": true,
    "explanation": "..."
  }
]`;

// ── Quiz-specific prompts ──────────────────────────────────────────────────

export function generatePoultryMCPrompt(
  count: number,
  topic: string,
  ragContext: string
): string {
  return `${POULTRY_MC_SYSTEM_PROMPT}

Topic: ${topic}
Generate exactly ${count} questions.

Context from official standards:
${ragContext}

Return ONLY the JSON array. No other text.`;
}

export function generatePoultryTFPrompt(
  count: number,
  topic: string,
  ragContext: string
): string {
  return `${POULTRY_TF_SYSTEM_PROMPT}

Topic: ${topic}
Generate exactly ${count} statements.

Context from official standards:
${ragContext}

Return ONLY the JSON array. No other text.`;
}

// ── NotebookLM context injection ──────────────────────────────────────────

export const NOTEBOOKLM_INJECTION = `
Based on NotebookLM synthesis of official poultry standards:

GRADING CRITERIA (Carcass):
- AA: Perfect skin, no defects, excellent meat yield
- A: Slight skin blemishes, minor defects, good yield
- B: Multiple blemishes, visible defects, acceptable yield
- Utility: Multiple defects, poor yield, suitable for processed products

KEY JUDGING LOGIC:
- Muscle structure > finish in live birds
- Meat yield > cosmetic appearance in carcasses
- Defect scoring: each defect category has point values
- Comparative judging: rank birds 1-4 by overall merit, not individual traits

COMMON MISCONCEPTIONS (test these):
- "A faster-growing bird will always be better" → FALSE (muscle quality matters more)
- "Cosmetic defects disqualify a carcass" → FALSE (only affects grade, not processability)
- "Egg AA grades are always superior" → FALSE (A grade is often perfect for commercial use)
`;
```

---

## Step 3: Update TOPIC_QUERIES in RAG Config (10 minutes)

Edit `lib/ai/rag-quiz.ts`:

Find the `TOPIC_QUERIES` constant and add these entries:

```typescript
export const TOPIC_QUERIES: Record<string, string> = {
  // ... existing entries like 'livestock', 'vet-science', etc.
  
  // ADD THESE 5 POULTRY ENTRIES:
  'Poultry-Grading': 'USDA poultry carcass grading standards AA A B Utility grades skin defects bruises meat quality',
  'Poultry-Production': 'broiler live bird judging muscle finish bone structure growth rate performance',
  'Poultry-Anatomy': 'poultry chicken carcass anatomy parts wings thighs drumsticks breast neck liver gizzard',
  'Poultry-Health': 'poultry disease health issues feed quality nutrition biosecurity disease prevention management',
  'Poultry-Nutrition': 'poultry feed amino acids protein growth nutrition requirements layer broiler formulas',
};
```

**Why?** These queries tell the RAG system what to search for in `knowledge_documents` when generating questions. More specific queries = better context injection.

---

## Step 4: Update Type Unions (5 minutes)

### 4.1 Add to `lib/store/history.ts`

Find the `PracticeType` type union:

```typescript
export type PracticeType = 
  | 'creed'
  | 'livestock'
  | 'vet-science'
  | 'meats'
  | 'poultry-eval'  // ← ADD THIS LINE
  | ...other types;
```

### 4.2 Add to `lib/tier.ts`

Find `FEATURE_TIERS` object:

```typescript
export const FEATURE_TIERS: Record<string, 'free' | 'premium' | 'team'> = {
  'creed': 'free',
  'livestock': 'free',
  'poultry-eval': 'free',  // ← ADD THIS LINE
  ...otherFeatures
};
```

### 4.3 Add routing to `app/contest/[id].tsx`

Find the `startPractice()` function. Add this block:

```typescript
if (legacyId === 'cde-poultry') {
  console.log('[POULTRY] Routing to poultry-eval hub');
  return router.push('/practice/poultry-eval');
}
```

(Place it after livestock routing, alphabetical order)

---

## Step 5: Test the Quiz Engine (20 minutes)

### 5.1 Manual Test in Dev Console

Open your app dev server:

```bash
npm start
```

Navigate to Poultry → Exam tab. Open browser dev console and run:

```javascript
// Test quiz generation
import { generatePoultryEvalQuiz } from '@/lib/poultry-eval-quiz';

const testQuiz = await generatePoultryEvalQuiz({
  topics: ['Poultry-Grading'],
  questionCount: 5,
  type: 'multiple_choice',
  isMock: false
});

console.log(testQuiz);
// Should output 5 quiz questions with options & explanations
```

### 5.2 Integration Test (App UI)

1. Open app on web/iOS/Android
2. Navigate: **CDE → Poultry**
3. Click **"Written Exam"**
4. Click **"Start Mock Contest"** (or similar button)
5. **Expected:** 30 MC questions load in <5 seconds, no errors

**If questions don't load:**
- Check Supabase: Are `knowledge_documents` populated? (Search "poultry")
- Check RAG query: Does `TOPIC_QUERIES` have your topic?
- Check Gemini API: Is it responding? (Check logs)

---

## Step 6: Ingest NotebookLM Content (When Ready)

Once Phase 1 is working, enhance the knowledge base:

```bash
# Run Python ingest script
cd ag-coach-app
python3 ingest_knowledge.py \
  --source "knowledge-sources/poultry-notebooklm/notebooklm_study_guide.md" \
  --category "Poultry" \
  --subcategory "Poultry-Grading,Poultry-Production,Poultry-Anatomy" \
  --format "markdown"
```

This adds NotebookLM's synthesis to the RAG context. Quizzes now have grounding from both USDA standards + NotebookLM teaching materials.

---

## Validation Checklist

- [ ] Prompts file created: `lib/prompts/poultry-prompts.ts`
- [ ] TOPIC_QUERIES updated with 5 poultry entries
- [ ] PracticeType union updated with 'poultry-eval'
- [ ] FEATURE_TIERS updated with 'poultry-eval': 'free'
- [ ] Routing block added to startPractice()
- [ ] Quiz generation test passes (5 questions load)
- [ ] Full contest exam test passes (30 questions load)
- [ ] No console errors; scores save to database

---

## Troubleshooting

### "No questions returned from RAG"
- **Fix:** Check `knowledge_documents` table in Supabase. Does it have poultry content?
- If empty: You need to ingest knowledge first. See Step 6.
- If populated: Check TOPIC_QUERIES map. Is your topic there?

### "Gemini API timeout"
- **Fix:** Questions are taking >30s to generate. Reduce batch size:
  ```typescript
  // In poultry-eval-quiz.ts, reduce count:
  const CHUNK = 1; // Was 2
  ```

### "Questions are off-topic or wrong"
- **Fix:** TOPIC_QUERIES semantic query is too vague. Make it more specific:
  ```typescript
  // Too vague:
  'Poultry-Grading': 'poultry grading standards'
  
  // Better:
  'Poultry-Grading': 'USDA poultry carcass grade AA A B Utility defect scoring bruise tear discoloration'
  ```

### "Gemini is hallucinating answers"
- **Fix:** System prompt is unclear. Simplify & add constraints:
  ```typescript
  // Add to POULTRY_MC_SYSTEM_PROMPT:
  "Each question must be directly answerable from the provided context.
   Do not invent facts not in the official standards."
  ```

---

## Next Steps After Phase 1

Once written exam works:

1. **Phase 2** (Week 3–4): Build image-based screens (parts, eggs, carcass placing)
2. **Phase 3** (Week 5+): Scenario-based placing practice with feedback
3. **Engagement:** Add gated progression (students must complete basics before live placing)

---

## Files Modified Summary

```
NEW:
  lib/prompts/poultry-prompts.ts

EDITED:
  lib/ai/rag-quiz.ts                  (TOPIC_QUERIES + 5 entries)
  lib/store/history.ts                (PracticeType union)
  lib/tier.ts                         (FEATURE_TIERS)
  app/contest/[id].tsx                (routing block in startPractice)

CREATED EXTERNALLY:
  knowledge-sources/poultry-notebooklm/  (NotebookLM outputs)
```

---

## Questions?

This is a **head-down, hands-on** quick start. If quiz generation still fails:
1. Check the Supabase `knowledge_documents` table
2. Verify Gemini API key in `.env`
3. Post logs to console → debug TOPIC_QUERIES or system prompt

Good luck! 🐔
