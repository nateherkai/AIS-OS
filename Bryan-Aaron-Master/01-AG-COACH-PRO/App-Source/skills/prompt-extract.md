# Skill: Prompt Extract

## Purpose

CLAUDE.md rule: AI prompts belong in `lib/prompts/`, not inline. Inline prompts → duplicated strings, no diff visibility, untestable. This skill finds inline prompts + moves them.

---

## When to Use

- Periodic audit (monthly)
- After feature merge that touched Gemini/Anthropic call sites
- When prompts diverge across modules

---

## Detection

```bash
# Long string literals near Gemini/Anthropic calls
grep -rn --include="*.ts" --include="*.tsx" \
  -E "(generateContent|sendMessage|createMessage|askBrain)" lib/ app/ \
  | head -50

# Inline backtick prompts > 200 chars
grep -rEn --include="*.ts" --include="*.tsx" \
  '`[^`]{200,}`' lib/ app/ \
  | grep -iE "you are|system|prompt|assistant|grade|evaluate"
```

Flag any hit OUTSIDE `lib/prompts/`.

---

## Extract Procedure

### 1. Identify domain

Existing files in `lib/prompts/`:
- `core-prompts.ts` — Ag Coach Brain system prompt
- `livestock-analyzer-prompts.ts`
- `horseLeadPrompts.ts`
- `wool-prompts.ts`
- `milk-quality-prompts.ts`
- `ag-skills-prompts.ts`
- `ag-tech-prompts.ts`
- `fbm-problem-prompts.ts`
- `evaluationPrompt.ts`
- `job-interview-rubrics.ts`
- `training-plan-prompts.ts`

Add to existing if domain matches. Else new file `<domain>-prompts.ts`.

### 2. Extract pattern

Before (inline):

```ts
// lib/some-feature.ts
const res = await model.generateContent(`You are an FFA coach. Grade this answer: ${input}. Return JSON: { score, feedback }`);
```

After:

```ts
// lib/prompts/some-feature-prompts.ts
export const GRADE_ANSWER_PROMPT = (input: string) => `You are an FFA coach. Grade this answer: ${input}. Return JSON: { score, feedback }`;

// lib/some-feature.ts
import { GRADE_ANSWER_PROMPT } from './prompts/some-feature-prompts';
const res = await model.generateContent(GRADE_ANSWER_PROMPT(input));
```

### 3. Naming

- Constants: `SCREAMING_SNAKE` for static, function for parameterized
- File: `<feature>-prompts.ts` (kebab)
- Export named, never default

### 4. Schema co-location

If prompt uses structured output, put `Schema` next to prompt:

```ts
import { SchemaType } from '@google/generative-ai';

export const GRADE_RESPONSE_SCHEMA = {
  type: SchemaType.OBJECT,
  properties: {
    score: { type: SchemaType.NUMBER },
    feedback: { type: SchemaType.STRING },
  },
  required: ['score', 'feedback'],
};
```

---

## Anti-Patterns

| Bad | Fix |
|---|---|
| Inline prompt in component | Extract to `lib/prompts/` |
| Prompt string built across 5 lines with `+` | Single template literal in prompts file |
| Same prompt copy-pasted across 2+ files | Single export, import both places |
| Brand voice violations in prompts (fun/easy/journey) | Run `brand-voice-lint` after extract |
| Hardcoded CDE scores as facts | Defer to RAG context (see `core-prompts.ts` pattern) |

---

## Verification

After extract:

```bash
npx tsc --noEmit -p .
# All call sites resolve
```

Diff prompt content unchanged — only location moved. Use `git diff --color-words` for char-level check.
