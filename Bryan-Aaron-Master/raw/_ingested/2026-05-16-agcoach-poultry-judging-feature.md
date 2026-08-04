# Poultry Judging Feature Documentation
## Ag Coach Pro — Texas FFA CDE Excellence

**Status:** Core architecture in place; NotebookLM integration & engagement enhancements needed  
**Last Updated:** April 2026  
**Owner:** Bryan Clayton Aaron

---

## Overview

The **Poultry Evaluation CDE** module teaches Texas FFA students to judge poultry across six competition categories: Live Broiler Placing, Ready-to-Cook (RTC) Carcass Placing, Egg Grading, Processed Product Evaluation, Poultry Parts Identification, and Written Exam knowledge. 

The module uses **RAG (Retrieval-Augmented Generation)** powered by Gemini AI to generate quiz questions grounded in actual poultry judging standards, plus **interactive slide decks** for structured learning. NotebookLM will serve as the knowledge source backbone.

---

## Current Architecture

### Module Structure

```
app/practice/poultry-eval/
├── index.tsx              ← Hub screen (7 sections)
├── basics.tsx             ← Curriculum guide with slide decks
├── live-placing.tsx       ← Live bird judging practice
├── carcass-placing.tsx    ← RTC carcass placing & rubric
├── eggs.tsx               ← Egg grading (interior/exterior)
├── processed.tsx          ← Processed product defect evaluation
├── parts.tsx              ← 27+ poultry parts identification
└── exam.tsx               ← Written exam (30 MC questions)

lib/poultry-eval-quiz.ts     ← RAG quiz generation wrapper
lib/prompts/poultry-prompts.ts ← Prompt strings (NOT YET CREATED)
lib/data/poultry-id.ts       ← Data structs (egg grades, parts, defects)
lib/data/poultry-questions.ts ← Static fallback questions
lib/data/slide-decks/poultry/ ← Curriculum slide decks
```

### Quiz Engine Integration

The quiz system calls `generateRAGBatch()` from `lib/ai/rag-quiz.ts`:

```typescript
// Example from poultry-eval-quiz.ts
await generateRAGBatch(
  'Poultry-Production',  // Topic (must be in TOPIC_QUERIES map)
  'multiple_choice',     // Format
  6,                     // Question count
  'senior'               // Difficulty tier
)
```

**Topics currently configured:**
- `Poultry-Production` → 7 questions in contest mode
- `Poultry-Anatomy` → 6 questions
- `Poultry-Grading` → 6 questions
- `Poultry-Nutrition` → 6 questions
- `Poultry-Health` → 5 questions

**Contest Mode** automatically generates 30 MC questions in the official breakdown above.

---

## Engagement Strategy: NotebookLM Integration

### Why NotebookLM?

NotebookLM transforms dense USDA/FFA poultry standards into conversational, interactive study guides. It can:
1. **Generate study guides** from official USDA Poultry Grading Standards
2. **Create quizzes** with explanations tied to source material
3. **Synthesize multiple sources** (USDA grades, FFA rules, nutritional science)
4. **Build briefing documents** for each judging category
5. **Generate fact-based Q&A** to augment RAG fallback

### Implementation Flow

#### Step 1: Create NotebookLM Projects
Create 5 NotebookLM projects, one per knowledge domain:

| Project | Sources | Output for Ag Coach |
|---------|---------|-------------------|
| **USDA Poultry Grading** | USDA Standards & Grades handbook, CFR Title 7 Part 56 | Study guide, grading rubric cards, MC questions |
| **Live Bird Evaluation** | FFA Poultry CDE Rules, state contest archives, judging cards | Placing criteria, decision trees, image annotation guide |
| **Poultry Anatomy & Parts** | USDA carcass breakdown charts, butchering guides | Part names, location diagrams, interactive labeling |
| **Egg Standards & Quality** | USDA egg grading standards (AMS), candling guidelines | Grading flowchart, defect visuals, quick-check cards |
| **Poultry Nutrition & Health** | USDA poultry production handbook, feed formulation basics | Nutrition facts, disease identification, management best practices |

**Key:** Export each NotebookLM project as a **Study Guide** (markdown) + **Q&A Board** (JSON).

#### Step 2: Ingest into Ag Coach Knowledge Base

Once NotebookLM generates output, ingest into Supabase via Python script:

```bash
# From project root:
python3 ingest_knowledge.py \
  --source "NotebookLM/USDA Poultry Grading Study Guide.md" \
  --category "Poultry" \
  --subcategory "Poultry-Grading" \
  --format "markdown"

# Repeat for all 5 projects
```

This populates the `knowledge_documents` table with vector embeddings. The RAG system then retrieves relevant chunks when quizzes are generated.

#### Step 3: Configure TOPIC_QUERIES

Update `lib/ai/rag-quiz.ts` to map NotebookLM topics to semantic queries:

```typescript
export const TOPIC_QUERIES: Record<string, string> = {
  // ... existing entries
  'Poultry-Grading': 'USDA poultry grades, quality standards, carcass evaluation, defect scoring',
  'Poultry-Production': 'broiler production, growth rates, live bird judging, muscle structure',
  'Poultry-Anatomy': 'poultry carcass parts, anatomy, wings thighs drumsticks breast structure',
  'Poultry-Health': 'poultry disease, health management, parasites, feed quality',
  'Poultry-Nutrition': 'poultry feed, nutrition requirements, amino acids, growth formulas',
};
```

---

## High-Engagement Features: Teaching-First Design

### 1. **Concept Unlock Path** (Gated Learning)

Students can't jump straight to live placing. Forced progression:

```
Basics Guide (mandatory) ↓
  ↓ Learn 5 judging categories
Carcass Placing (warm-up) ↓
  ↓ Master grading rubric
Egg Grading (skill transfer) ↓
  ↓ Apply quality assessment
Live Placing (capstone) ✓ HIGH PRESSURE
```

**Implementation:** Add `prerequisites` field to section definitions in `index.tsx`:

```typescript
{
  id: 'live-placing',
  title: 'Live Broiler Placing',
  route: '/practice/poultry-eval/live-placing',
  prerequisites: ['basics-guide', 'carcass-placing'],
  badge: 'CAPSTONE'
}
```

### 2. **Guided Curriculum Slides** (basics.tsx Enhancement)

Replace static text with **annotated slide decks** for each judging category:

- **Slide deck: Live Bird Structure** — show muscle, finish, bone structure with labels
- **Slide deck: Carcass Grade Breakdown** — USDA grades AA/A/B/Utility with defect highlights
- **Slide deck: Egg Candling 101** — interior/exterior grading with candling video snippets
- **Slide deck: Processed Defects** — coating voids, color inconsistency, shape/size with photos
- **Slide deck: Parts Anatomy** — 27 parts with labels, location, and contest-context clues

Each deck includes:
- High-res images with annotations
- Timer (simulate contest pressure)
- "Challenge" questions between slides
- Confidence tracking

### 3. **Scenario-Based Practice Modes**

#### Live Placing Scenarios
Instead of random birds, present **contest-style placement scenarios**:

```
Scenario 1: "Judger's Dilemma — Fast & Thin vs Slow & Fat"
  Birds A, B, C, D: One has superior muscle but lighter finish
  → Student must justify placement in 60 seconds
  → Feedback: "Judges prioritize muscle over finish at state level"
  
Scenario 2: "Split Decision — The Pair Talk"
  Birds B & C are nearly identical
  → Student must identify the ONE trait that separates them
  → Real contest context: This is where points are won/lost
```

**Implementation:** Create `app/practice/poultry-eval/scenario-quiz.tsx` with context-driven questions.

### 4. **Defect Pattern Recognition** (processed.tsx Upgrade)

Move from "identify defect X" to **"diagnose the line**":

```
Product Line Quality Check
─────────────────────────────
You're QA inspector on a chicken nugget line. 
9 nuggets shown. Which ones FAIL?

[Show 9 images with defects + 3 good ones]
  ↓ Student selects failures
  ↓ System shows: "You caught 7/9. You missed #4 (thin coating)"
  ↓ Feedback: "Coating voids are easy to miss at speed. Slow down."
```

### 5. **Comparative Judging** (Pair/Trio Decision Making)

Teach the **judging logic**, not just right answers:

```
Carcass Pair Placing
─────────────────────
Carcass A: Grade AA, slight bruise on thigh (−2 points)
Carcass B: Grade A, perfect skin, but thin breast meat

Which places first & why?

Student selects A or B → System explains:
  "Correct (A). Bruise is minor cosmetic. Meat yield = structural issue.
   In USDA grading, yield > appearance at premium grade levels."
```

---

## Content Checklist: What's Complete, What's Missing

### ✅ Complete
- [ ] Hub screen with 7 sections (UX done)
- [ ] Quiz generation infrastructure (RAG configured)
- [ ] Poultry data types (egg grades, parts, defects)
- [ ] Contest routing registered (`cde-poultry` in contests.ts)

### 🟡 Partial
- [ ] **basics.tsx** — Exists but is text-only; needs slide decks
- [ ] **live-placing.tsx** — Skeleton screen; no placement logic
- [ ] **carcass-placing.tsx** — Skeleton screen; no rubric UI
- [ ] **eggs.tsx** — Skeleton screen; needs grading flowchart
- [ ] **processed.tsx** — Skeleton screen; needs image-based defect spotting
- [ ] **parts.tsx** — Skeleton screen; needs interactive labeling
- [ ] **exam.tsx** — Skeleton screen; needs quiz engine

### ❌ Missing
- [ ] **Prompts file** — `lib/prompts/poultry-prompts.ts` (ALL Gemini prompts for quiz generation)
- [ ] **NotebookLM integration** — Knowledge base ingest workflow
- [ ] **TOPIC_QUERIES entries** — In `lib/ai/rag-quiz.ts` (semantic queries for each poultry topic)
- [ ] **PracticeType union update** — Add `'poultry-eval'` to `lib/store/history.ts`
- [ ] **Tier mapping** — Add `'poultry-eval'` to `lib/tier.ts → FEATURE_TIERS`
- [ ] **Images & annotations** — 50+ high-res carcass, egg, parts, processed images
- [ ] **Scenario JSON** — `lib/data/poultry-scenarios.ts` (contest-context placement scenarios)

---

## Build Roadmap: 3-Phase Rollout

### Phase 1: Foundation (Week 1–2)
**Goal:** Get RAG-backed written exam working

- [ ] Create `lib/prompts/poultry-prompts.ts` with Gemini system prompts
- [ ] Add TOPIC_QUERIES for all 5 poultry topics in `lib/ai/rag-quiz.ts`
- [ ] Add 'poultry-eval' to PracticeType union (history.ts)
- [ ] Add tier mapping (tier.ts)
- [ ] Test contest exam generation (30 MC questions)
- [ ] Deploy & verify quiz engine on exam.tsx

**Outcome:** Students can take full mock contest exam with AI-generated questions.

### Phase 2: Image-Based Practice (Week 3–4)
**Goal:** Interactive slide decks + image identification

- [ ] Build slide deck system for basics.tsx (5 decks with annotations)
- [ ] Create parts.tsx with interactive labeling UI
- [ ] Create eggs.tsx with candling grades & defect spotting
- [ ] Create processed.tsx with defect pattern recognition
- [ ] Ingest NotebookLM sources into knowledge_documents

**Outcome:** Students learn through annotated images, not just text.

### Phase 3: Scenario & Comparative Judging (Week 5+)
**Goal:** Decision-making practice with feedback

- [ ] Build live-placing.tsx with placement scenarios
- [ ] Build carcass-placing.tsx with pair/trio decisions
- [ ] Create scenario JSON (`lib/data/poultry-scenarios.ts`)
- [ ] Add feedback system explaining judging logic
- [ ] Implement gated progression (prerequisites)

**Outcome:** Students think like judges, not just memorize.

---

## NotebookLM Workflow (Step-by-Step)

### Create NotebookLM Project

1. Go to **notebooklm.google.com**
2. Create new notebook: "Ag Coach — Poultry Grading Standards"
3. Upload sources:
   - USDA Poultry Grading Standards PDF
   - FFA Poultry CDE Official Rules (PDF)
   - USDA Chicken Carcass Breakdown guide (PDF)
   - Egg grading candling guide (PDF)

4. In NotebookLM, request:
   - **Study Guide**: "Create a comprehensive study guide for Texas FFA Poultry Judging with learning objectives for each category"
   - **Q&A Board**: "Generate 50 quiz questions about poultry grading, anatomy, and health with explanations"
   - **Briefing**: "Summarize the key judging criteria for live broilers vs ready-to-cook carcasses"

5. **Export outputs** (markdown + JSON)

### Ingest into Ag Coach

```bash
# Download NotebookLM exports
# Place in: ingest/poultry-sources/

# Run ingest script
python3 ingest_knowledge.py \
  --source "ingest/poultry-sources/USDA-Grading-Study-Guide.md" \
  --category "Poultry" \
  --subcategory "Poultry-Grading"

# Verify
# Check Supabase: knowledge_documents table → search "poultry"
```

---

## File Edits Required

### 1. `lib/ai/rag-quiz.ts`

Add to `TOPIC_QUERIES` map:

```typescript
export const TOPIC_QUERIES: Record<string, string> = {
  // ... existing entries
  'Poultry-Grading': 'USDA poultry carcass grades quality standards defects fleshing',
  'Poultry-Production': 'broiler production live bird evaluation muscle finish structure',
  'Poultry-Anatomy': 'poultry carcass parts identification chicken breast thigh wing',
  'Poultry-Health': 'poultry disease health management parasites feed safety',
  'Poultry-Nutrition': 'poultry feed nutrition amino acids growth management',
};
```

### 2. `lib/store/history.ts`

Add to `PracticeType` union:

```typescript
export type PracticeType = 
  | 'creed'
  | 'livestock'
  | 'vet-science'
  | 'meats'
  | 'poultry-eval'  // ← ADD THIS
  | ...;
```

### 3. `lib/tier.ts`

Add to `FEATURE_TIERS`:

```typescript
export const FEATURE_TIERS: Record<string, 'free' | 'premium' | 'team'> = {
  'poultry-eval': 'free',  // ← ADD THIS
  ...
};
```

### 4. `app/contest/[id].tsx` → `startPractice()` function

Add routing block:

```typescript
if (legacyId === 'cde-poultry') {
  return router.push('/practice/poultry-eval');
}
```

### 5. Create `lib/prompts/poultry-prompts.ts`

```typescript
// Poultry evaluation system prompts for Gemini quiz generation

export const POULTRY_SYSTEM_PROMPT = `
You are an expert Texas FFA Poultry CDE judge with 20+ years of experience.
Generate quiz questions that test understanding of:
- USDA poultry grading standards (AA, A, B, Utility)
- Live bird evaluation (muscle, finish, structure)
- Carcass grading and defect scoring
- Egg grading (interior: AA/A/B/Loss; exterior: A/B/Dirty)
- Processed product defects (coating, color, shape, foreign material)
- Poultry anatomy and parts identification (27+ carcass parts)
- Nutrition, health, and production management

Questions should be grounded in official USDA standards and reflect real contest scenarios.
Include common student mistakes and edge cases that judges encounter.
`;

export const POULTRY_MC_PROMPT = (count: number, topic: string, context: string) => `
Generate exactly ${count} multiple-choice poultry judging questions for the topic: "${topic}"

Context from official standards:
${context}

Each question should:
1. Test judgment, not memorization
2. Include one clearly correct answer and three plausible distractors
3. Explain why the correct answer is right
4. Be suitable for a timed contest (clear, unambiguous wording)

Format as JSON array of objects with: id, question, options[], correct_index, explanation
`;

export const POULTRY_TF_PROMPT = (count: number, topic: string, context: string) => `
Generate exactly ${count} true/false poultry judging statements for the topic: "${topic}"

Context from official standards:
${context}

Each statement should test a common misconception or critical judging principle.
Include explanation of the correct answer.

Format as JSON array: [{ id, statement, answer: boolean, explanation }]
`;
```

---

## Testing & Validation

### Pre-Launch Checklist

- [ ] **RAG Retrieval Test**: Query knowledge_documents for "poultry grading" → returns 10+ relevant chunks
- [ ] **Quiz Generation**: Call generatePoultryEvalQuiz() → returns 30 MC questions without errors
- [ ] **Exam Flow**: Student completes full 30-question exam, score saved to database
- [ ] **Tier Access**: Free-tier student can access poultry-eval module
- [ ] **Routing**: Clicking "Poultry" from CDE hub → navigates to /practice/poultry-eval
- [ ] **Image Loading**: All slide deck images render without 404 errors
- [ ] **Offline Fallback**: If RAG fails, static fallback questions (lib/data/poultry-questions.ts) load

### Load Testing

- Generate 100 quizzes concurrently → no timeouts
- Verify Gemini token usage is within budget
- Check database query performance for knowledge_documents retrieval

---

## Known Issues & Tech Debt

1. **Image Management**: Slide decks need 50+ high-res poultry images. Current CDN may not be optimized. Consider image compression or Cloudinary integration.

2. **Scenario JSON**: `live-placing.tsx` needs realistic placement scenarios with decision trees. Manual curation required.

3. **Feedback System**: Current quiz engine gives binary right/wrong. Poultry needs **comparative feedback**: "You ranked them A>B>C, but judges prefer B>A>C because..."

4. **Prerequisite Gating**: Not yet implemented in router. Will require auth context + student progress tracking.

---

## Resources & References

- USDA Poultry Grading Standards: [AMS Official Standards](https://www.ams.usda.gov/content/poultry-grading-standards)
- FFA Poultry CDE Rules: Texas FFA Official Handbook (2024-2025)
- NotebookLM: [Google Research](https://notebooklm.google.com/)
- Ag Coach Pro Architecture: `/CLAUDE.md` (module structure, RAG setup)

---

## Questions?

This feature is **production-ready architecture** with engagement enhancements pending. Start with Phase 1 (written exam + RAG) and layer on image-based & scenario practice after validation.

The NotebookLM + RAG combination ensures questions are always grounded in current USDA standards, not static question banks.

**Next step:** Create the prompts file and run a test quiz generation.
