# Job Interview: RAG-Based Question Generation + ElevenLabs Voice Agent

**Date:** 2026-05-12
**Status:** Approved

---

## Problem

The phone interview simulator generates questions using only the uploaded filename — not actual document content. Questions are generic. Students don't get tailored practice based on their specific job application materials.

---

## Goals

1. Generate interview questions from actual content of uploaded job description + resume.
2. Phone interview becomes a real-time voice conversation with an AI judge (ElevenLabs Conversational AI).
3. Video interview gets multimodal Gemini question generation from uploaded documents.
4. Fixed FFA rubric questions always appear verbatim in phone sessions.
5. All student materials stay on-device, session-only — never written to Supabase.
6. School isolation is structural: zero server-side storage of student content.

---

## Out of Scope

- Persistent RAG across sessions (student re-uploads each time)
- New Supabase tables or migrations
- Changes to document scoring (`analyzeDocument()`)

---

## Architecture

### Phone Interview — ElevenLabs Conversational Agent

```
upload.tsx
  └─ jobDescription.uri + resume.uri → useJobInterviewStore

phone.tsx (on session start)
  ├─ extractDocumentText(jd.uri)   → Gemini Vision → plain text string
  ├─ extractDocumentText(resume.uri) → Gemini Vision → plain text string
  ├─ startConversation({ dynamic_variables: { job_description_text, resume_text } })
  │    └─ @11labs/react useConversation hook (WebRTC, web-only)
  │         Agent: FFA judge persona, must ask 4 fixed rubric questions
  │         Has access to injected JD + resume text
  ├─ Student speaks — agent responds in real-time
  └─ session ends
       ├─ fetch transcript from ElevenLabs API
       └─ analyzeInterviewResponse(transcript, 'phone') → Gemini → rubric score → results screen
```

### Video Interview — ElevenLabs Conversational Agent + Continuous Video Recording

```
video.tsx (on session start)
  ├─ extractDocumentText(jd.uri)    → Gemini Vision → plain text string
  ├─ extractDocumentText(resume.uri) → Gemini Vision → plain text string
  ├─ MediaRecorder starts — continuous camera + mic capture (web-only)
  ├─ startConversation({ dynamic_variables: { job_description_text, resume_text } })
  │    └─ @elevenlabs/react useConversation hook (WebRTC, web-only)
  │         Agent: FFA personal interview judge persona
  │         Opens with "Tell me about yourself."
  │         Covers rubric domains: Knowledge of Job/Industry, STAR method,
  │         Communication Skills, General Effect
  │         Has access to injected JD + resume text
  ├─ Student speaks — agent responds in real-time — camera records continuously
  └─ session ends
       ├─ MediaRecorder stops → video blob saved to temp URI
       ├─ fetch transcript from ElevenLabs API
       ├─ scoreVideoInterview(transcript, videoUri)
       │    ├─ pass 1: transcript → Gemini → verbal criteria score
       │    │   (Response to Questions 100pts, Communication Skills 50pts,
       │    │    Knowledge of Job/Industry 50pts, General Effect 100pts)
       │    └─ pass 2: video → Gemini Vision → visual criteria score
       │        (First Impressions 50pts, Poise and Presence 50pts)
       └─ combined score → results screen
```

---

## Fixed Phone Questions (Always Verbatim, Position 1–4)

```typescript
export const PHONE_FIXED_QUESTIONS = [
  { id: 'p1', text: 'Tell us about yourself and your interest in this position.' },
  { id: 'p2', text: 'Why do you want this job?' },
  { id: 'p3', text: 'What do you know about our company?' },
  { id: 'p4', text: 'Do you have any questions for us?' },
];
```

Agent system prompt requires these 4 verbatim. Gemini scores coverage post-conversation — flags rubric criteria not addressed if agent drifts.

---

## Scoring — Phone (Updated)

Current flow scores one audio clip per question. New flow scores the full transcript:

```
transcript (full conversation) → scoreInterviewTranscript(transcript)
  → Gemini + PHONE_INTERVIEW_RUBRIC (50pts total)
  → { score, maxScore: 50, feedback, strengths, improvements }
```

Transcript-based scoring is more accurate — Gemini sees greeting, conviction, closure, and all question responses in full context.

---

## Scoring — Video (New)

Two-pass scoring at session end. Returns combined `InterviewAnalysis`:

```
Pass 1 (verbal):
  transcript → Gemini + PERSONAL_INTERVIEW_RUBRIC verbal criteria
  → Response to Questions (100pts) + Communication Skills (50pts)
     + Knowledge of Job/Industry (50pts) + General Effect (100pts) = 300pts

Pass 2 (visual):
  video blob URI → Gemini Vision + PERSONAL_INTERVIEW_RUBRIC visual criteria
  → First Impressions (50pts) + Poise and Presence (50pts) = 100pts

Combined: score/400pts, merged feedback, merged strengths/improvements
```

New function: `scoreVideoInterview(transcript: string, videoUri: string): Promise<InterviewAnalysis>`

---

## Files Changed

| File | Change |
|------|--------|
| `lib/scoring/job-interview.ts` | Add `extractDocumentText()` (Gemini Vision → string). Update `generateInterviewQuestions()` to accept optional `mediaParts[]`. Update `analyzeInterviewResponse()` to accept full transcript string for phone. |
| `app/practice/job-interview/phone.tsx` | Replace per-question recording flow with `useConversation` from `@11labs/react`. Read files, inject dynamic variables, fetch transcript on session end, score. |
| `app/practice/job-interview/video.tsx` | Replace per-question recording flow with ElevenLabs conversational agent + continuous MediaRecorder. Dual scoring at end: transcript (verbal) + video (visual). |
| `lib/scoring/job-interview.ts` | Add `scoreVideoInterview(transcript, videoUri)` — two-pass scoring (transcript verbal + video visual), returns combined `InterviewAnalysis`. |
| `lib/prompts/job-interview-rubrics.ts` | Add `PHONE_FIXED_QUESTIONS`, `ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT`, `ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT` constants. |

---

## Fallback Behavior

| Condition | Behavior |
|-----------|----------|
| JD or resume not uploaded | Phone: fixed 4 questions only, no tailoring. Video: generic Gemini questions (no media parts). |
| File read error | Catch → log → proceed with fallback. Not surfaced to student. |
| ElevenLabs unavailable | Fall back to existing per-question recording flow. |
| Gemini returns bad JSON | `parseAIJson` defaults already handle this. |
| Large files (>20MB) | Gemini inline data limit. Student resumes/JDs are well under this. Log warning if exceeded, fall back. |

---

## School Isolation Guarantee

Session-only storage means no cross-school data risk exists by construction:

- Base64 file content read into memory → sent to Gemini/ElevenLabs → discarded at session end
- No Supabase write, no Edge Function invocation, no vector store
- `useJobInterviewStore` is Zustand in-memory state — cleared on session end

---

## Prerequisites

- ElevenLabs account with two Conversational AI agents configured:
  - Phone agent (uses `PHONE_INTERVIEW_RUBRIC` questions)
  - Video agent (uses `PERSONAL_INTERVIEW_RUBRIC` approach, opens with "Tell me about yourself")
- `EXPO_PUBLIC_ELEVENLABS_PHONE_AGENT_ID` — phone interview agent ID
- `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID` — video interview agent ID
- `EXPO_PUBLIC_ELEVENLABS_API_KEY` — shared API key
- `npm install @elevenlabs/react` (maintained successor to `@11labs/react`)

---

## Success Criteria

- Phone interview: student hears AI judge voice, has real conversation, receives rubric-aligned score (0–50) from full transcript
- Video interview: student converses with AI judge while camera records; receives combined verbal + visual rubric score (0–400) at end
- Fixed rubric questions always appear in phone sessions verbatim
- Both agents tailored to student's uploaded JD + resume via dynamic variables
- Zero student materials stored in Supabase at any point
