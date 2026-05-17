---
name: ai-engine
description: Owns all AI integrations including Gemini grading, Claude backup, OpenAI Whisper transcription, prompt engineering, and scoring pipeline optimization. Use when the user asks to improve AI scoring, fix transcription, optimize prompts, reduce AI latency, add AI-powered features, or debug AI response issues.
---

# AI Engine Agent

## When to use this skill
- Improving or creating AI scoring prompts
- Fixing transcription (Whisper) issues
- Optimizing AI response latency or cost
- Parsing or validating AI responses
- Adding new AI-powered features (study tools, feedback)
- Debugging AI errors (rate limits, malformed responses, timeouts)

## Files Owned
```
lib/ai/gemini.ts
lib/ai/claude.ts
lib/ai/openai.ts
lib/ai/whisper.ts
app/api/transcribe+api.ts
app/study/ai-brain.tsx
app/study/ai-quiz.tsx
scripts/stress-test-ai.ts
scripts/test-*-ai*.ts
```

## AI Stack

### Gemini 1.5 Flash (Primary Grading)
- Package: `@google/generative-ai`
- File: `lib/ai/gemini.ts`
- Function: `generateAnalysis(prompt, rubric, transcript)`
- Temperature: `0.3` (consistency for grading)
- Retry: 3 attempts with exponential backoff (1s → 2s → 4s)
- Handles: 429 (rate limit) and 503 (overloaded)
- **CRITICAL**: Throws on error — never returns fake scores

### Claude API (Backup/Advanced)
- File: `lib/ai/claude.ts`
- Use for: Complex rubric evaluation, detailed feedback, appeal reviews
- Reserve for premium features (higher cost per token)

### OpenAI Whisper (Speech-to-Text)
- File: `lib/ai/whisper.ts`
- Function: `transcribeAudio(audioUri)`
- Returns: `{ text: string, confidence: number }`
- Formats: m4a, wav, mp3
- Size limit: 25MB
- Proxied through: `app/api/transcribe+api.ts` (protects API key)

## Scoring Pipeline
```
Student records audio (expo-av)
        ↓
Audio → Whisper API → transcript text
        ↓
Transcript + Rubric → Gemini prompt → JSON response
        ↓
Parse response → validate → ScoreResult object
        ↓
Display scores + feedback in result screen
```

## Prompt Engineering Standards

### Structure
Every grading prompt must follow this pattern:
```
ROLE: You are an expert FFA judge for [contest name].

RUBRIC:
[For each scoring category:]
- Category: [name] (max [X] points)
  - Excellent (90-100%): [criteria]
  - Good (70-89%): [criteria]  
  - Fair (50-69%): [criteria]
  - Poor (below 50%): [criteria]

STUDENT SUBMISSION:
[transcript or content]

RESPOND WITH ONLY VALID JSON:
{
  "categories": [
    { "name": "...", "score": N, "maxScore": N, "feedback": "..." }
  ],
  "totalScore": N,
  "maxTotalScore": N,
  "overallFeedback": "...",
  "confidence": 0.0-1.0
}
```

### Edge Case Handling
Every prompt must include instructions for:
- Empty/silent recordings → score 0 with encouraging "try again" feedback
- Off-topic responses → score low with explanation of what was expected
- Partial completions → score proportionally, note what was missing
- Unintelligible audio → low confidence score, suggest re-recording

### Response Parsing
```typescript
function parseAIResponse(raw: string): ScoreResult {
  // Try direct JSON parse
  try { return JSON.parse(raw); } catch {}
  
  // Try extracting from ```json blocks
  const jsonMatch = raw.match(/```json\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    try { return JSON.parse(jsonMatch[1]); } catch {}
  }
  
  // Try extracting any JSON object
  const objMatch = raw.match(/\{[\s\S]*\}/);
  if (objMatch) {
    try { return JSON.parse(objMatch[0]); } catch {}
  }
  
  // Fallback: throw with the raw response for debugging
  throw new Error(`Failed to parse AI response: ${raw.slice(0, 200)}`);
}
```

## Optimization Priorities

### Cost
- Cache identical requests (same transcript hash + same rubric = same result)
- Use Gemini Flash for all initial scoring (cheapest)
- Reserve Claude for appeals, detailed feedback, or premium tier
- Keep prompts concise — don't repeat rubric text unnecessarily

### Latency (target: < 3 seconds)
- Set maxOutputTokens to minimum needed (~500 for scoring)
- Use streaming for long responses if displaying progressively
- Parallelize independent AI calls (e.g., multiple categories)
- Pre-warm the Gemini client on app launch

### Reliability
- All calls must have 30s timeout
- Retry with exponential backoff (already implemented)
- Log errors to Supabase for monitoring
- Graceful degradation: show "scoring unavailable" not a crash
- Validate every response before displaying to user

## Rules
1. **NEVER** expose API keys in client-side code — use Expo API routes
2. All AI calls must have timeout handling (30s max)
3. All AI calls must have retry logic with backoff
4. All AI responses must be validated/parsed before display
5. Log all AI errors with context (contest, input length, error type)
6. Provide graceful degradation when AI is unavailable
7. Include confidence scores with all AI outputs
8. Temperature 0.3 for grading consistency, 0.7+ for creative/study features
9. Never return hardcoded/fake scores — throw errors instead
