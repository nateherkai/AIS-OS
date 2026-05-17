# Job Interview RAG + ElevenLabs Voice Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace both phone and video interview simulators with real-time ElevenLabs voice conversations grounded in the student's uploaded job description and resume; video interview additionally records camera continuously and scores visual criteria separately.

**Architecture:** On interview start, extract plain text from uploaded files via Gemini Vision, inject into ElevenLabs agent `dynamic_variables`, run real-time voice session. Phone: fetch transcript on end, score against `PHONE_INTERVIEW_RUBRIC` (50pts). Video: run continuous MediaRecorder alongside voice session, fetch transcript + video blob on end, two-pass scoring — transcript for verbal criteria + video for visual criteria (First Impressions, Poise) — combined score out of 400pts. All student content is session-only — never written to Supabase.

**Tech Stack:** Expo Router / React Native (web target), Gemini 2.0 Flash (multimodal), ElevenLabs Conversational AI SDK (`@elevenlabs/react`), Zustand (`useJobInterviewStore`), Jest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `lib/prompts/job-interview-rubrics.ts` | Modify | Add `PHONE_FIXED_QUESTIONS`, `ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT`, `ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT` |
| `lib/scoring/job-interview.ts` | Modify | Add `extractDocumentText()`, `scoreInterviewTranscript()`, `scoreVideoInterview()`. Rewrite `generateInterviewQuestions()` signature. |
| `lib/scoring/job-interview.test.ts` | Create | Unit tests for all new functions |
| `app/practice/job-interview/phone.tsx` | Modify | Replace recording flow with `useConversation` hook |
| `app/practice/job-interview/video.tsx` | Modify | Replace per-question recording with ElevenLabs agent + continuous MediaRecorder + dual scoring |
| `.env.example` | Modify | Add `EXPO_PUBLIC_ELEVENLABS_PHONE_AGENT_ID`, `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID`, `EXPO_PUBLIC_ELEVENLABS_API_KEY` |

---

## Task 1: Install ElevenLabs SDK

**Files:**
- Modify: `package.json` (via npm)

- [ ] **Step 1: Install**

```bash
npm install @11labs/react
```

- [ ] **Step 2: Verify install**

```bash
npm ls @11labs/react
```

Expected output includes `@11labs/react@x.x.x` with no errors.

- [ ] **Step 3: Commit**

```bash
git add package.json package-lock.json
git commit -m "deps: add @11labs/react for conversational voice agent"
```

---

## Task 2: Add env vars

**Files:**
- Modify: `.env` (local, not committed)
- Modify: `app.config.js` or `app.json` — expose vars to Expo

- [ ] **Step 1: Add to `.env`**

Add these two lines (fill in real values from ElevenLabs dashboard):

```
EXPO_PUBLIC_ELEVENLABS_AGENT_ID=your_agent_id_here
EXPO_PUBLIC_ELEVENLABS_API_KEY=your_api_key_here
```

- [ ] **Step 2: Verify Expo can see them**

Expo automatically exposes `EXPO_PUBLIC_*` vars — no `app.config.js` change needed. Verify:

```bash
node -e "require('dotenv').config(); console.log(process.env.EXPO_PUBLIC_ELEVENLABS_AGENT_ID ? 'OK' : 'MISSING')"
```

Expected: `OK`

- [ ] **Step 3: No commit** — `.env` must not be committed. Confirm `.gitignore` includes `.env`:

```bash
grep "^\.env" .gitignore
```

Expected: `.env` line present.

---

## Task 3: Add constants to rubrics file

**Files:**
- Modify: `lib/prompts/job-interview-rubrics.ts`

- [ ] **Step 1: Write failing test** — create `lib/scoring/job-interview.test.ts`:

```typescript
import { PHONE_FIXED_QUESTIONS, ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT } from '../prompts/job-interview-rubrics';

describe('job-interview rubric constants', () => {
  test('PHONE_FIXED_QUESTIONS has exactly 4 items', () => {
    expect(PHONE_FIXED_QUESTIONS).toHaveLength(4);
  });

  test('PHONE_FIXED_QUESTIONS ids are unique', () => {
    const ids = PHONE_FIXED_QUESTIONS.map(q => q.id);
    expect(new Set(ids).size).toBe(4);
  });

  test('PHONE_FIXED_QUESTIONS[0] asks student to introduce themselves', () => {
    expect(PHONE_FIXED_QUESTIONS[0].text.toLowerCase()).toContain('yourself');
  });

  test('ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT contains dynamic variable slots', () => {
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('{{job_description_text}}');
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('{{resume_text}}');
  });

  test('ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT contains all 4 required questions', () => {
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('Tell us about yourself');
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('Why do you want this job');
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('What do you know about our company');
    expect(ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT).toContain('Do you have any questions for us');
  });
});
```

- [ ] **Step 2: Run to confirm failure**

```bash
npm test -- job-interview
```

Expected: FAIL — `PHONE_FIXED_QUESTIONS` not exported.

- [ ] **Step 3: Add constants to `lib/prompts/job-interview-rubrics.ts`**

Append at the bottom of the file:

```typescript
export const PHONE_FIXED_QUESTIONS: { id: string; text: string }[] = [
  { id: 'p1', text: 'Tell us about yourself and your interest in this position.' },
  { id: 'p2', text: 'Why do you want this job?' },
  { id: 'p3', text: 'What do you know about our company?' },
  { id: 'p4', text: 'Do you have any questions for us?' },
];

export const ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT = `
You are an official FFA Job Interview CDE judge conducting a telephone interview.

You are evaluating a student for the position described below.
Use the student's resume to ask tailored follow-up questions.

JOB DESCRIPTION:
{{job_description_text}}

STUDENT RESUME:
{{resume_text}}

REQUIRED QUESTIONS — Ask ALL of these verbatim, in this order, before ending:
1. "Tell us about yourself and your interest in this position."
2. "Why do you want this job?"
3. "What do you know about our company?"
4. "Do you have any questions for us?"

After each required question you may ask 1-2 natural follow-up questions based on the student's answer.
Keep the interview concise — 5-8 minutes total. Thank the student and end when all required questions are answered.
`.trim();
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
npm test -- job-interview
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/prompts/job-interview-rubrics.ts lib/scoring/job-interview.test.ts
git commit -m "feat(job-interview): add fixed phone questions and ElevenLabs agent system prompt"
```

---

## Task 4: Add `extractDocumentText()` to scoring lib

Gemini Vision reads the uploaded file and returns plain text. Same base64 pattern used by `analyzeDocument()`.

**Files:**
- Modify: `lib/scoring/job-interview.ts`
- Modify: `lib/scoring/job-interview.test.ts`

- [ ] **Step 1: Write failing test** — add to `lib/scoring/job-interview.test.ts`:

```typescript
import { extractDocumentText } from './job-interview';

// Mock askBrainWithMedia
jest.mock('../ai/gemini', () => ({
  askBrain: jest.fn(),
  askBrainWithMedia: jest.fn().mockResolvedValue({ answer: 'Extracted plain text content.' }),
  retryOperation: jest.fn((fn) => fn()),
  genAI: {},
  getModel: jest.fn(() => ({
    generateContent: jest.fn().mockResolvedValue({
      response: { text: () => JSON.stringify([{ id: '1', text: 'Test question?' }]) }
    })
  })),
}));

// Mock expo-file-system
jest.mock('expo-file-system/legacy', () => ({
  readAsStringAsync: jest.fn().mockResolvedValue('base64encodedcontent'),
  EncodingType: { Base64: 'base64' },
}));

describe('extractDocumentText', () => {
  beforeEach(() => jest.clearAllMocks());

  test('returns string from Gemini response', async () => {
    const result = await extractDocumentText('file:///test.pdf', 'application/pdf');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
  });

  test('returns empty string on error without throwing', async () => {
    const { askBrainWithMedia } = require('../ai/gemini');
    (askBrainWithMedia as jest.Mock).mockRejectedValueOnce(new Error('Network error'));
    const result = await extractDocumentText('file:///bad.pdf', 'application/pdf');
    expect(result).toBe('');
  });
});
```

- [ ] **Step 2: Run to confirm failure**

```bash
npm test -- job-interview
```

Expected: FAIL — `extractDocumentText` not exported.

- [ ] **Step 3: Add `extractDocumentText` to `lib/scoring/job-interview.ts`**

Add after the existing imports, before `analyzeInterviewResponse`:

```typescript
export async function extractDocumentText(fileUri: string, mimeType: string): Promise<string> {
  try {
    let base64 = '';
    if (Platform.OS === 'web') {
      const response = await fetch(fileUri);
      const blob = await response.blob();
      base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } else {
      base64 = await FileSystem.readAsStringAsync(fileUri, { encoding: FileSystem.EncodingType.Base64 });
    }

    const response = await askBrainWithMedia(
      'Extract all text from this document. Return only the plain text content with no formatting or markdown.',
      '',
      { base64, mimeType }
    );
    return response.answer || '';
  } catch (error) {
    console.error('[extractDocumentText] failed:', error);
    return '';
  }
}
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
npm test -- job-interview
```

Expected: `extractDocumentText` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/scoring/job-interview.ts lib/scoring/job-interview.test.ts
git commit -m "feat(job-interview): add extractDocumentText via Gemini Vision"
```

---

## Task 5: Rewrite `generateInterviewQuestions()` with multimodal support

Change signature to accept optional media parts instead of a text string. Builds a multi-part Gemini request when files are provided.

**Files:**
- Modify: `lib/scoring/job-interview.ts`
- Modify: `lib/scoring/job-interview.test.ts`

- [ ] **Step 1: Write failing tests** — add to `lib/scoring/job-interview.test.ts`:

```typescript
describe('generateInterviewQuestions', () => {
  beforeEach(() => jest.clearAllMocks());

  test('returns array of questions with id and text', async () => {
    const questions = await generateInterviewQuestions(3);
    expect(Array.isArray(questions)).toBe(true);
    expect(questions[0]).toHaveProperty('id');
    expect(questions[0]).toHaveProperty('text');
  });

  test('returns fallback questions when genAI unavailable', async () => {
    const { getModel } = require('../ai/gemini');
    (getModel as jest.Mock).mockReturnValueOnce({
      generateContent: jest.fn().mockRejectedValueOnce(new Error('unavailable'))
    });
    const questions = await generateInterviewQuestions(3);
    expect(questions.length).toBeGreaterThan(0);
  });

  test('accepts mediaParts without throwing', async () => {
    const mediaParts = [{ base64: 'abc123', mimeType: 'application/pdf' }];
    const questions = await generateInterviewQuestions(2, mediaParts);
    expect(Array.isArray(questions)).toBe(true);
  });
});
```

- [ ] **Step 2: Run to confirm failures**

```bash
npm test -- job-interview
```

Expected: FAIL — new signature mismatch.

- [ ] **Step 3: Replace `generateInterviewQuestions` in `lib/scoring/job-interview.ts`**

Remove the old function entirely and replace with:

```typescript
export async function generateInterviewQuestions(
  count: number,
  mediaParts?: { base64: string; mimeType: string }[]
): Promise<{ id: string; text: string }[]> {
  const prompt = mediaParts && mediaParts.length > 0
    ? `Based on the job description and resume provided, generate ${count} professional interview questions tailored to this specific role and candidate background. Focus on the STAR method, industry knowledge, and alignment between the candidate's experience and the role requirements. Return a JSON array of objects with "id" (string) and "text" (string) fields.`
    : `Generate ${count} professional FFA Job Interview CDE practice questions covering knowledge of job/industry, STAR-method responses, and communication skills. Return a JSON array of objects with "id" (string) and "text" (string) fields.`;

  try {
    const questions = await retryOperation(async () => {
      if (!genAI) return null;

      const model = getModel({
        model: 'gemini-2.0-flash',
        generationConfig: { responseMimeType: 'application/json' },
      });

      const parts: any[] = [];
      if (mediaParts && mediaParts.length > 0) {
        mediaParts.forEach(mp => {
          parts.push({ inlineData: { data: mp.base64, mimeType: mp.mimeType } });
        });
      }
      parts.push({ text: prompt });

      const result = await model.generateContent({ contents: [{ role: 'user', parts }] });
      return JSON.parse(result.response.text());
    }, 'generateInterviewQuestions');

    if (!questions) throw new Error('GenAI instance missing');

    return Array.isArray(questions)
      ? questions.map((q: any, i: number) => ({
          id: q.id || String(i + 1),
          text: q.text || q.question || '',
        })).filter(q => q.text.length > 0)
      : [];
  } catch (error) {
    console.error('[generateInterviewQuestions] failed, using fallback:', error);
    return [
      { id: '1', text: "Tell us about yourself and why you're interested in this position." },
      { id: '2', text: "What do you consider to be your greatest strength and weakness?" },
      { id: '3', text: "Describe a situation where you had to work as part of a team to achieve a goal." },
    ];
  }
}
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
npm test -- job-interview
```

Expected: all `generateInterviewQuestions` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add lib/scoring/job-interview.ts lib/scoring/job-interview.test.ts
git commit -m "feat(job-interview): rewrite generateInterviewQuestions with multimodal Gemini support"
```

---

## Task 6: Add `scoreInterviewTranscript()` for full conversation scoring

Scores a complete ElevenLabs conversation transcript (all turns) against the phone rubric.

**Files:**
- Modify: `lib/scoring/job-interview.ts`
- Modify: `lib/scoring/job-interview.test.ts`

- [ ] **Step 1: Write failing test** — add to `lib/scoring/job-interview.test.ts`:

```typescript
import { scoreInterviewTranscript } from './job-interview';

describe('scoreInterviewTranscript', () => {
  beforeEach(() => jest.clearAllMocks());

  test('returns InterviewAnalysis shape', async () => {
    const { askBrain } = require('../ai/gemini');
    (askBrain as jest.Mock).mockResolvedValueOnce({
      answer: JSON.stringify({ score: 42, feedback: 'Good job.', strengths: ['Clear voice'], improvements: ['Speak slower'] })
    });
    const result = await scoreInterviewTranscript('Interviewer: Hello\nStudent: Hi, I am Jane.');
    expect(result).toHaveProperty('score');
    expect(result).toHaveProperty('feedback');
    expect(result).toHaveProperty('strengths');
    expect(result).toHaveProperty('improvements');
  });

  test('returns score 0 with error message on bad AI response', async () => {
    const { askBrain } = require('../ai/gemini');
    (askBrain as jest.Mock).mockRejectedValueOnce(new Error('timeout'));
    const result = await scoreInterviewTranscript('some transcript');
    expect(result.score).toBe(0);
    expect(typeof result.feedback).toBe('string');
  });
});
```

- [ ] **Step 2: Run to confirm failure**

```bash
npm test -- job-interview
```

Expected: FAIL — `scoreInterviewTranscript` not exported.

- [ ] **Step 3: Add function to `lib/scoring/job-interview.ts`**

Add after `analyzeInterviewResponse`:

```typescript
export async function scoreInterviewTranscript(transcript: string): Promise<InterviewAnalysis> {
  try {
    const context = `
      ${JOB_INTERVIEW_JUDGE_SYSTEM_PROMPT}

      RUBRIC:
      ${PHONE_INTERVIEW_RUBRIC}

      TASK: Score this complete telephone interview transcript against the rubric above.
      Consider the full conversation arc — greeting, conviction, closure, all question responses in context.

      TRANSCRIPT:
      ${transcript}

      OUTPUT FORMAT (JSON only, no markdown):
      {
        "score": number (0-50),
        "feedback": "string (constructive feedback using judging terminology)",
        "strengths": ["string", "string"],
        "improvements": ["string", "string"]
      }
    `;

    const response = await askBrain('Score this interview transcript', context);

    const result = parseAIJson(response.answer, {
      score: 0,
      feedback: 'AI Analysis Failed',
      strengths: [],
      improvements: [],
    });

    return {
      score: typeof result.score === 'number' ? result.score : 0,
      maxScore: 50,
      feedback: String(result.feedback || 'No feedback provided.'),
      strengths: Array.isArray(result.strengths) ? result.strengths.map(String) : [],
      improvements: Array.isArray(result.improvements) ? result.improvements.map(String) : [],
    };
  } catch (error: any) {
    return {
      score: 0,
      maxScore: 50,
      feedback: `Failed to score transcript. Error: ${error.message || 'Unknown error'}`,
      strengths: [],
      improvements: [],
    };
  }
}
```

- [ ] **Step 4: Run tests to confirm pass**

```bash
npm test -- job-interview
```

Expected: all `scoreInterviewTranscript` tests PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
npm test
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add lib/scoring/job-interview.ts lib/scoring/job-interview.test.ts
git commit -m "feat(job-interview): add scoreInterviewTranscript for full conversation scoring"
```

---

## Task 7: Configure ElevenLabs agent (one-time dashboard setup)

This task cannot be automated — do it manually in the ElevenLabs dashboard before implementing `phone.tsx`.

- [ ] **Step 1: Create a Conversational AI agent**

Go to [elevenlabs.io/app/conversational-ai](https://elevenlabs.io/app/conversational-ai) → Create Agent.

- [ ] **Step 2: Set system prompt**

Copy the value of `ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT` from `lib/prompts/job-interview-rubrics.ts` into the agent's system prompt field.

- [ ] **Step 3: Add dynamic variables**

In agent settings, add two dynamic variables:
- `job_description_text` (type: string, default: "No job description provided.")
- `resume_text` (type: string, default: "No resume provided.")

- [ ] **Step 4: Choose a voice**

Select a professional, neutral voice (e.g., "Rachel" or similar). This is the AI judge's voice.

- [ ] **Step 5: Copy agent ID**

From the agent settings page, copy the Agent ID. Paste it into `.env` as `EXPO_PUBLIC_ELEVENLABS_AGENT_ID`.

- [ ] **Step 6: Copy API key**

From [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys), copy your key. Paste into `.env` as `EXPO_PUBLIC_ELEVENLABS_API_KEY`.

---

## Task 8: Rewrite `phone.tsx` with ElevenLabs conversational agent

Replaces the per-question recording flow with a real-time voice session. Web-only (same constraint as current MediaRecorder). Native fallback: show a message directing user to web.

**Files:**
- Modify: `app/practice/job-interview/phone.tsx`

- [ ] **Step 1: Replace the component**

Replace the entire contents of `app/practice/job-interview/phone.tsx` with:

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, ActivityIndicator, Platform } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { Stack } from 'expo-router';
import { safeBack } from '@/lib/navigation';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Theme, GlassEffect } from '@/constants/theme';
import { useJobInterviewStore } from '@/lib/store/job-interview';
import { extractDocumentText, scoreInterviewTranscript, InterviewAnalysis } from '@/lib/scoring/job-interview';
import { useHistoryStore } from '@/lib/store/history';
import { saveQuizResult } from '@/lib/data';
import { useAuthStore } from '@/lib/store/auth';
import { TeacherService } from '@/lib/teacher';

// ElevenLabs SDK is web-only — dynamic import to avoid native bundling errors
let useConversation: any = null;
if (Platform.OS === 'web') {
  useConversation = require('@11labs/react').useConversation;
}

const AGENT_ID = process.env.EXPO_PUBLIC_ELEVENLABS_AGENT_ID ?? '';
const API_KEY = process.env.EXPO_PUBLIC_ELEVENLABS_API_KEY ?? '';

type Step = 'intro' | 'preparing' | 'active' | 'scoring' | 'results';

function NativeFallback() {
  return (
    <View style={styles.center}>
      <Ionicons name="phone-portrait-outline" size={48} color={Theme.colors.accent} />
      <Text style={styles.fallbackTitle}>WEB ONLY</Text>
      <Text style={styles.fallbackBody}>
        The phone interview voice agent requires a web browser. Open AgCoachPro at agcoachpro.com to access this feature.
      </Text>
    </View>
  );
}

export default function PhoneSimulator() {
  const router = useRouter();
  const { jobDescription, resume } = useJobInterviewStore();
  const [step, setStep] = useState<Step>('intro');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [result, setResult] = useState<InterviewAnalysis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // ElevenLabs hook — only initialised on web
  const conversation = Platform.OS === 'web' && useConversation
    ? useConversation({
        onConnect: (data: { conversationId: string }) => {
          setConversationId(data.conversationId);
          setStep('active');
        },
        onDisconnect: () => {
          // Session ended — fetch transcript and score
          handleSessionEnd();
        },
        onError: (err: Error) => {
          console.error('[ElevenLabs]', err);
          setErrorMsg('Voice connection failed. Please try again.');
          setStep('intro');
        },
      })
    : null;

  const startInterview = useCallback(async () => {
    if (!conversation) return;
    setStep('preparing');
    setErrorMsg(null);

    try {
      // Extract text from both files (falls back to '' on error)
      const jdText = jobDescription
        ? await extractDocumentText(jobDescription.uri, jobDescription.mimeType ?? 'application/pdf')
        : '';
      const resumeText = resume
        ? await extractDocumentText(resume.uri, resume.mimeType ?? 'application/pdf')
        : '';

      await conversation.startSession({
        agentId: AGENT_ID,
        dynamicVariables: {
          job_description_text: jdText || 'No job description uploaded.',
          resume_text: resumeText || 'No resume uploaded.',
        },
      });
    } catch (err: any) {
      console.error('[startInterview]', err);
      setErrorMsg('Could not start voice session. Check your internet connection.');
      setStep('intro');
    }
  }, [conversation, jobDescription, resume]);

  const endInterview = useCallback(async () => {
    if (!conversation) return;
    await conversation.endSession();
    // onDisconnect fires → handleSessionEnd called
  }, [conversation]);

  const handleSessionEnd = useCallback(async () => {
    if (!conversationId) {
      setStep('intro');
      return;
    }
    setStep('scoring');

    try {
      // Fetch transcript from ElevenLabs
      const resp = await fetch(
        `https://api.elevenlabs.io/v1/convai/conversations/${conversationId}`,
        { headers: { 'xi-api-key': API_KEY } }
      );
      const data = await resp.json();

      const turns: { role: string; message: string }[] = data.transcript ?? [];
      const fullTranscript = turns
        .map(t => `${t.role === 'agent' ? 'Interviewer' : 'Student'}: ${t.message}`)
        .join('\n');

      const analysis = await scoreInterviewTranscript(fullTranscript);
      setResult(analysis);

      // Save to history
      const { user } = useAuthStore.getState();
      useHistoryStore.getState().addResult({
        type: 'job-interview',
        score: analysis.score,
        maxScore: analysis.maxScore ?? 50,
        details: analysis,
        metadata: { mode: 'phone', conversationId },
      });
      if (user?.id) {
        void saveQuizResult({
          userId: user.id,
          contestId: 'lde-job-interview',
          type: 'job-interview',
          score: analysis.score,
          maxScore: analysis.maxScore ?? 50,
          details: analysis,
        });
        void TeacherService.logAction('complete_lde_session', undefined, 'lde-job-interview', {
          contestName: 'Job Interview',
          mode: 'phone_voice_agent',
        });
      }

      setStep('results');
    } catch (err: any) {
      console.error('[handleSessionEnd]', err);
      setErrorMsg('Could not retrieve interview transcript. Try again.');
      setStep('intro');
    }
  }, [conversationId]);

  if (Platform.OS !== 'web') return <NativeFallback />;

  const isSpeaking = conversation?.isSpeaking ?? false;
  const status = conversation?.status ?? 'disconnected';

  return (
    <View style={{ flex: 1, backgroundColor: Theme.colors.black }}>
      <Stack.Screen options={{ title: 'PHONE INTERVIEW', headerTransparent: true, headerTintColor: '#fff' }} />
      <ScrollView contentContainerStyle={styles.scroll}>

        {/* Header */}
        <View style={styles.header}>
          <View style={styles.iconCircle}>
            <Ionicons name="call-outline" size={40} color={Theme.colors.accent} />
          </View>
          <Text style={styles.title}>PHONE INTERVIEW</Text>
          <Text style={styles.subtitle}>FFA JOB INTERVIEW CDE — TELEPHONE SIMULATION</Text>
        </View>

        {errorMsg && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        )}

        {/* INTRO */}
        {step === 'intro' && (
          <View style={[styles.card, GlassEffect]}>
            <Text style={styles.cardTitle}>HOW IT WORKS</Text>
            <Text style={styles.cardBody}>
              An AI judge will call you and ask the official FFA rubric questions plus tailored questions based on your uploaded job description and resume.{'\n\n'}
              Speak naturally. The judge will respond in real-time. End the call when you are finished.
            </Text>
            {!jobDescription && (
              <Text style={styles.warningText}>
                Tip: upload a job description and resume for tailored questions.
              </Text>
            )}
            <TouchableOpacity style={styles.primaryButton} onPress={startInterview}>
              <Ionicons name="call" size={20} color={Theme.colors.black} style={{ marginRight: 8 }} />
              <Text style={styles.buttonText}>START CALL</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* PREPARING */}
        {step === 'preparing' && (
          <View style={[styles.card, GlassEffect, styles.center]}>
            <ActivityIndicator size="large" color={Theme.colors.accent} />
            <Text style={[styles.cardBody, { marginTop: 16, textAlign: 'center' }]}>
              Preparing your interview session…
            </Text>
          </View>
        )}

        {/* ACTIVE */}
        {step === 'active' && (
          <View style={[styles.card, GlassEffect]}>
            <View style={styles.statusRow}>
              <View style={[styles.dot, { backgroundColor: isSpeaking ? Theme.colors.accent : '#444' }]} />
              <Text style={styles.statusText}>
                {isSpeaking ? 'JUDGE IS SPEAKING' : 'YOUR TURN — SPEAK NOW'}
              </Text>
            </View>
            <Text style={styles.cardBody}>
              The AI judge is on the line. Answer each question naturally. When you are finished with the interview, tap End Call.
            </Text>
            <TouchableOpacity style={styles.endButton} onPress={endInterview}>
              <Ionicons name="call" size={20} color="#fff" style={{ marginRight: 8 }} />
              <Text style={[styles.buttonText, { color: '#fff' }]}>END CALL</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* SCORING */}
        {step === 'scoring' && (
          <View style={[styles.card, GlassEffect, styles.center]}>
            <ActivityIndicator size="large" color={Theme.colors.accent} />
            <Text style={[styles.cardBody, { marginTop: 16, textAlign: 'center' }]}>
              Scoring your interview against the official FFA rubric…
            </Text>
          </View>
        )}

        {/* RESULTS */}
        {step === 'results' && result && (
          <View style={[styles.card, GlassEffect]}>
            <View style={styles.scoreRow}>
              <View style={styles.scoreBadge}>
                <Text style={styles.scoreText}>{result.score}/{result.maxScore ?? 50}</Text>
              </View>
              <Text style={styles.scoreLabel}>OFFICIAL GRADE</Text>
            </View>
            <Text style={styles.feedbackText}>{result.feedback}</Text>

            {result.strengths.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>STRENGTHS</Text>
                {result.strengths.map((s, i) => (
                  <Text key={i} style={styles.bullet}>• {s}</Text>
                ))}
              </View>
            )}

            {result.improvements.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>GROWTH AREAS</Text>
                {result.improvements.map((s, i) => (
                  <Text key={i} style={styles.bullet}>• {s}</Text>
                ))}
              </View>
            )}

            <TouchableOpacity style={styles.primaryButton} onPress={() => setStep('intro')}>
              <Text style={styles.buttonText}>PRACTICE AGAIN</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: 60 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: 24, paddingTop: 100 },
  header: { alignItems: 'center', marginBottom: 24 },
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(0,242,255,0.1)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(0,242,255,0.3)', marginBottom: 20 },
  title: { fontSize: 24, fontWeight: '900', color: '#fff', letterSpacing: 2 },
  subtitle: { fontSize: 11, color: Theme.colors.text.muted, marginTop: 8, letterSpacing: 1, fontWeight: '700', textAlign: 'center' },
  card: { backgroundColor: Theme.colors.card, padding: 20, borderRadius: 24, marginBottom: 20 },
  cardTitle: { fontSize: 14, fontWeight: '900', color: Theme.colors.accent, letterSpacing: 1, marginBottom: 12 },
  cardBody: { fontSize: 14, color: 'rgba(255,255,255,0.7)', lineHeight: 22, fontWeight: '600' },
  warningText: { fontSize: 12, color: Theme.colors.warning, marginTop: 12, fontWeight: '700' },
  center: { alignItems: 'center', justifyContent: 'center' },
  statusRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  dot: { width: 12, height: 12, borderRadius: 6, marginRight: 10 },
  statusText: { fontSize: 13, fontWeight: '900', color: '#fff', letterSpacing: 1 },
  primaryButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: Theme.colors.accent, padding: 16, borderRadius: 12, marginTop: 20 },
  endButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: Theme.colors.error, padding: 16, borderRadius: 12, marginTop: 20 },
  buttonText: { color: Theme.colors.black, fontSize: 15, fontWeight: '900', letterSpacing: 1 },
  errorBox: { backgroundColor: 'rgba(255,60,60,0.1)', borderWidth: 1, borderColor: 'rgba(255,60,60,0.3)', padding: 16, borderRadius: 12, marginBottom: 16 },
  errorText: { color: Theme.colors.error, fontSize: 13, fontWeight: '700' },
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 16 },
  scoreBadge: { backgroundColor: Theme.colors.accent, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  scoreText: { color: Theme.colors.black, fontWeight: '900', fontSize: 18 },
  scoreLabel: { color: Theme.colors.accent, fontSize: 10, fontWeight: '800', letterSpacing: 1 },
  feedbackText: { fontSize: 14, color: '#fff', lineHeight: 22, marginBottom: 16, fontWeight: '600' },
  section: { marginTop: 12 },
  sectionTitle: { fontSize: 11, fontWeight: '800', color: Theme.colors.warning, letterSpacing: 1, marginBottom: 8 },
  bullet: { fontSize: 13, color: 'rgba(255,255,255,0.7)', fontWeight: '600', marginBottom: 4 },
  fallbackTitle: { fontSize: 20, fontWeight: '900', color: '#fff', marginTop: 20, letterSpacing: 2 },
  fallbackBody: { fontSize: 14, color: 'rgba(255,255,255,0.6)', textAlign: 'center', lineHeight: 22, marginTop: 12, paddingHorizontal: 24, fontWeight: '600' },
});
```

- [ ] **Step 2: Type-check**

```bash
npx tsc --noEmit -p .
```

Expected: no errors in `phone.tsx`.

- [ ] **Step 3: Commit**

```bash
git add app/practice/job-interview/phone.tsx
git commit -m "feat(job-interview): replace phone sim with ElevenLabs conversational voice agent"
```

---

## Task 9: Rewrite `video.tsx` with ElevenLabs agent + continuous recording + dual scoring

Replaces per-question recording flow. ElevenLabs conversational agent runs free-form interview while MediaRecorder captures video continuously. Two-pass scoring at session end.

**Files:**
- Modify: `app/practice/job-interview/video.tsx`
- Modify: `lib/scoring/job-interview.ts` (add `scoreVideoInterview`)
- Modify: `lib/prompts/job-interview-rubrics.ts` (add `ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT`)
- Modify: `lib/scoring/job-interview.test.ts` (add tests for `scoreVideoInterview`)
- Modify: `.env.example` (add `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID`)

### Step 1: Add `ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT` to `lib/prompts/job-interview-rubrics.ts`

Append after `ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT`:

```typescript
export const ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT = `
You are an official FFA Job Interview CDE judge conducting an in-person interview.

You are evaluating a student for the position described below.
Use the student's resume to ask tailored questions and meaningful follow-ups.

JOB DESCRIPTION:
{{job_description_text}}

STUDENT RESUME:
{{resume_text}}

Begin with: "Tell me about yourself."

Then cover these rubric domains naturally through conversation:
- Knowledge of Job/Industry (understanding of role, industry trends)
- Response to Questions (use STAR method: Situation, Task, Action, Result)
- Communication Skills (grammar, vocabulary, articulation)
- General Effect (overall employability and fit)

Keep the interview professional — 10–15 minutes. Ask 6–8 questions total.
Thank the student and close when you have sufficient evaluation data.
`.trim();
```

### Step 2: Write failing test for `scoreVideoInterview`

Add to `lib/scoring/job-interview.test.ts`:

```typescript
import { scoreVideoInterview } from './job-interview';

describe('scoreVideoInterview', () => {
  beforeEach(() => jest.clearAllMocks());

  test('returns InterviewAnalysis with maxScore 400', async () => {
    const result = await scoreVideoInterview(
      'Interviewer: Tell me about yourself.\nStudent: Hi, I am Jane.',
      'blob:http://localhost/fake-video'
    );
    expect(result).toHaveProperty('score');
    expect(result).toHaveProperty('feedback');
    expect(result).toHaveProperty('strengths');
    expect(result).toHaveProperty('improvements');
    expect(result.maxScore).toBe(400);
  });

  test('returns score 0 on error without throwing', async () => {
    // Use mock pattern from existing tests to force askBrain to throw
    const result = await scoreVideoInterview('', '');
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.maxScore).toBe(400);
    expect(typeof result.feedback).toBe('string');
  });
});
```

Run: `npm test -- job-interview` — expect FAIL (function not exported yet).

### Step 3: Add `scoreVideoInterview` to `lib/scoring/job-interview.ts`

Add after `scoreInterviewTranscript`:

```typescript
export async function scoreVideoInterview(
  transcript: string,
  videoUri: string
): Promise<InterviewAnalysis> {
  try {
    // Pass 1: verbal scoring from transcript
    const verbalContext = `
      ${JOB_INTERVIEW_JUDGE_SYSTEM_PROMPT}

      RUBRIC (verbal criteria only):
      ${PERSONAL_INTERVIEW_RUBRIC}

      TASK: Score this personal interview transcript on VERBAL criteria only:
      - Response to Questions (100pts): Content, depth, examples (STAR method)
      - Communication Skills (50pts): Grammar, vocabulary, articulation
      - Knowledge of Job/Industry (50pts): Understanding of role, industry trends
      - General Effect (100pts): Overall employability and fit
      Total verbal score: 0–300pts

      TRANSCRIPT:
      ${transcript}

      OUTPUT FORMAT (JSON only, no markdown):
      {
        "score": number (0-300),
        "feedback": "string",
        "strengths": ["string"],
        "improvements": ["string"]
      }
    `;
    const verbalResponse = await askBrain('Score verbal criteria', verbalContext);
    const verbalResult = parseAIJson(verbalResponse.answer, {
      score: 0, feedback: 'Verbal analysis failed', strengths: [], improvements: []
    });

    // Pass 2: visual scoring from video
    let visualScore = 0;
    let visualFeedback = 'Visual analysis unavailable.';
    let visualStrengths: string[] = [];
    let visualImprovements: string[] = [];

    if (videoUri) {
      try {
        let base64 = '';
        let mimeType = 'video/webm';
        if (Platform.OS === 'web') {
          const resp = await fetch(videoUri);
          const blob = await resp.blob();
          mimeType = blob.type || 'video/webm';
          base64 = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(((reader.result as string).split(',')[1]) || '');
            reader.onerror = reject;
            reader.readAsDataURL(blob);
          });
        }

        if (base64) {
          const visualResponse = await askBrainWithMedia(
            `
            Score this interview video on VISUAL criteria only:
            - First Impressions (50pts): Confidence, professional appearance, posture
            - Poise and Presence (50pts): Composure, eye contact, body language
            Total visual score: 0–100pts

            OUTPUT FORMAT (JSON only, no markdown):
            {
              "score": number (0-100),
              "feedback": "string",
              "strengths": ["string"],
              "improvements": ["string"]
            }
            `,
            PERSONAL_INTERVIEW_RUBRIC,
            { base64, mimeType }
          );
          const vr = parseAIJson(visualResponse.answer, {
            score: 0, feedback: 'Visual parse failed', strengths: [], improvements: []
          });
          visualScore = typeof vr.score === 'number' ? vr.score : 0;
          visualFeedback = String(vr.feedback || '');
          visualStrengths = Array.isArray(vr.strengths) ? vr.strengths.map(String) : [];
          visualImprovements = Array.isArray(vr.improvements) ? vr.improvements.map(String) : [];
        }
      } catch (visualErr) {
        console.error('[scoreVideoInterview] visual pass failed:', visualErr);
      }
    }

    const verbalScore = typeof verbalResult.score === 'number' ? verbalResult.score : 0;

    return {
      score: verbalScore + visualScore,
      maxScore: 400,
      feedback: [verbalResult.feedback, visualFeedback].filter(Boolean).join(' | '),
      strengths: [
        ...( Array.isArray(verbalResult.strengths) ? verbalResult.strengths.map(String) : []),
        ...visualStrengths,
      ],
      improvements: [
        ...(Array.isArray(verbalResult.improvements) ? verbalResult.improvements.map(String) : []),
        ...visualImprovements,
      ],
    };
  } catch (error: any) {
    return {
      score: 0,
      maxScore: 400,
      feedback: `Failed to score video interview. Error: ${error.message || 'Unknown error'}`,
      strengths: [],
      improvements: [],
    };
  }
}
```

Run: `npm test -- job-interview` — all tests must pass.

Commit:
```bash
git add lib/scoring/job-interview.ts lib/scoring/job-interview.test.ts lib/prompts/job-interview-rubrics.ts
git commit -m "feat(job-interview): add scoreVideoInterview dual-pass scoring and video agent prompt"
```

### Step 4: Rewrite `app/practice/job-interview/video.tsx`

Replace the entire file with a structure mirroring `phone.tsx` but with:
- `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID` instead of phone agent ID
- `MediaRecorder` running continuously alongside the voice session (web-only)
- On session end: stop MediaRecorder → collect video blob → call `scoreVideoInterview(transcript, blobUrl)`
- `NativeFallback` component (same as phone — web-only feature)

```typescript
import React, { useState, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator, Platform } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Theme, GlassEffect } from '@/constants/theme';
import { useJobInterviewStore } from '@/lib/store/job-interview';
import { extractDocumentText, scoreVideoInterview, InterviewAnalysis } from '@/lib/scoring/job-interview';
import { useHistoryStore } from '@/lib/store/history';
import { saveQuizResult } from '@/lib/data';
import { useAuthStore } from '@/lib/store/auth';
import { TeacherService } from '@/lib/teacher';

let useConversation: any = null;
if (Platform.OS === 'web') {
  useConversation = require('@elevenlabs/react').useConversation;
}

const VIDEO_AGENT_ID = process.env.EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID ?? '';
const API_KEY = process.env.EXPO_PUBLIC_ELEVENLABS_API_KEY ?? '';

type Step = 'intro' | 'preparing' | 'active' | 'scoring' | 'results';

function NativeFallback() {
  return (
    <View style={styles.center}>
      <Ionicons name="videocam-outline" size={48} color={Theme.colors.accent} />
      <Text style={styles.fallbackTitle}>WEB ONLY</Text>
      <Text style={styles.fallbackBody}>
        The video interview voice agent requires a web browser. Open AgCoachPro at agcoachpro.com.
      </Text>
    </View>
  );
}

export default function VideoSimulator() {
  const router = useRouter();
  const { jobDescription, resume } = useJobInterviewStore();
  const [step, setStep] = useState<Step>('intro');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [result, setResult] = useState<InterviewAnalysis | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const videoChunksRef = useRef<Blob[]>([]);
  const videoBlobUrlRef = useRef<string | null>(null);

  const conversation = Platform.OS === 'web' && useConversation
    ? useConversation({
        onConnect: (data: { conversationId: string }) => {
          setConversationId(data.conversationId);
          setStep('active');
        },
        onDisconnect: () => { handleSessionEnd(); },
        onError: (err: Error) => {
          console.error('[ElevenLabs video]', err);
          stopRecording();
          setErrorMsg('Voice connection failed. Please try again.');
          setStep('intro');
        },
      })
    : null;

  const startRecording = useCallback(() => {
    if (Platform.OS !== 'web' || typeof navigator === 'undefined') return;
    try {
      navigator.mediaDevices.getUserMedia({ video: true, audio: true }).then(stream => {
        const mr = new MediaRecorder(stream, { mimeType: 'video/webm' });
        videoChunksRef.current = [];
        mr.ondataavailable = e => { if (e.data.size > 0) videoChunksRef.current.push(e.data); };
        mr.start(1000);
        mediaRecorderRef.current = mr;
      }).catch(err => console.error('[MediaRecorder]', err));
    } catch (err) {
      console.error('[startRecording]', err);
    }
  }, []);

  const stopRecording = useCallback((): Promise<string | null> => {
    return new Promise(resolve => {
      const mr = mediaRecorderRef.current;
      if (!mr || mr.state === 'inactive') { resolve(null); return; }
      mr.onstop = () => {
        const blob = new Blob(videoChunksRef.current, { type: 'video/webm' });
        const url = URL.createObjectURL(blob);
        videoBlobUrlRef.current = url;
        resolve(url);
      };
      mr.stop();
      mr.stream.getTracks().forEach(t => t.stop());
    });
  }, []);

  const startInterview = useCallback(async () => {
    if (!conversation) return;
    setStep('preparing');
    setErrorMsg(null);
    try {
      const jdText = jobDescription
        ? await extractDocumentText(jobDescription.uri, jobDescription.mimeType ?? 'application/pdf')
        : '';
      const resumeText = resume
        ? await extractDocumentText(resume.uri, resume.mimeType ?? 'application/pdf')
        : '';

      startRecording();

      await conversation.startSession({
        agentId: VIDEO_AGENT_ID,
        dynamicVariables: {
          job_description_text: jdText || 'No job description uploaded.',
          resume_text: resumeText || 'No resume uploaded.',
        },
      });
    } catch (err: any) {
      stopRecording();
      setErrorMsg('Could not start session. Check your internet connection.');
      setStep('intro');
    }
  }, [conversation, jobDescription, resume, startRecording, stopRecording]);

  const endInterview = useCallback(async () => {
    if (!conversation) return;
    await conversation.endSession();
  }, [conversation]);

  const handleSessionEnd = useCallback(async () => {
    const videoUrl = await stopRecording();
    if (!conversationId) { setStep('intro'); return; }
    setStep('scoring');

    try {
      const resp = await fetch(
        `https://api.elevenlabs.io/v1/convai/conversations/${conversationId}`,
        { headers: { 'xi-api-key': API_KEY } }
      );
      const data = await resp.json();
      const turns: { role: string; message: string }[] = data.transcript ?? [];
      const fullTranscript = turns
        .map(t => `${t.role === 'agent' ? 'Interviewer' : 'Student'}: ${t.message}`)
        .join('\n');

      const analysis = await scoreVideoInterview(fullTranscript, videoUrl ?? '');
      setResult(analysis);

      const { user } = useAuthStore.getState();
      useHistoryStore.getState().addResult({
        type: 'job-interview',
        score: analysis.score,
        maxScore: analysis.maxScore ?? 400,
        details: analysis,
        metadata: { mode: 'video', conversationId },
      });
      if (user?.id) {
        void saveQuizResult({
          userId: user.id, contestId: 'lde-job-interview', type: 'job-interview',
          score: analysis.score, maxScore: analysis.maxScore ?? 400, details: analysis,
        });
        void TeacherService.logAction('complete_lde_session', undefined, 'lde-job-interview', {
          contestName: 'Job Interview', mode: 'video_voice_agent',
        });
      }
      setStep('results');
    } catch (err: any) {
      setErrorMsg('Could not retrieve interview results. Try again.');
      setStep('intro');
    }
  }, [conversationId, stopRecording]);

  if (Platform.OS !== 'web') return <NativeFallback />;

  const isSpeaking = conversation?.isSpeaking ?? false;

  return (
    <View style={{ flex: 1, backgroundColor: Theme.colors.black }}>
      <Stack.Screen options={{ title: 'VIDEO INTERVIEW', headerTransparent: true, headerTintColor: '#fff' }} />
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.header}>
          <View style={styles.iconCircle}>
            <Ionicons name="videocam-outline" size={40} color={Theme.colors.accent} />
          </View>
          <Text style={styles.title}>VIDEO INTERVIEW</Text>
          <Text style={styles.subtitle}>FFA JOB INTERVIEW CDE — IN-PERSON SIMULATION</Text>
        </View>

        {errorMsg && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        )}

        {step === 'intro' && (
          <View style={[styles.card, GlassEffect]}>
            <Text style={styles.cardTitle}>HOW IT WORKS</Text>
            <Text style={styles.cardBody}>
              An AI judge will conduct a full personal interview while your camera records. Speak naturally. The judge will ask about your background, the role, and use STAR-method questions.{'\n\n'}
              Scoring covers verbal performance (Response to Questions, Communication Skills, Knowledge of Industry) and visual criteria (First Impressions, Poise).
            </Text>
            {!jobDescription && (
              <Text style={styles.warningText}>Tip: upload a job description and resume for tailored questions.</Text>
            )}
            <TouchableOpacity style={styles.primaryButton} onPress={startInterview}>
              <Ionicons name="videocam" size={20} color={Theme.colors.black} style={{ marginRight: 8 }} />
              <Text style={styles.buttonText}>START INTERVIEW</Text>
            </TouchableOpacity>
          </View>
        )}

        {step === 'preparing' && (
          <View style={[styles.card, GlassEffect, styles.center]}>
            <ActivityIndicator size="large" color={Theme.colors.accent} />
            <Text style={[styles.cardBody, { marginTop: 16, textAlign: 'center' }]}>Setting up your interview session…</Text>
          </View>
        )}

        {step === 'active' && (
          <View style={[styles.card, GlassEffect]}>
            <View style={styles.statusRow}>
              <View style={[styles.dot, { backgroundColor: isSpeaking ? Theme.colors.accent : '#444' }]} />
              <Text style={styles.statusText}>{isSpeaking ? 'JUDGE IS SPEAKING' : 'YOUR TURN — SPEAK NOW'}</Text>
            </View>
            <View style={styles.recordingBadge}>
              <View style={styles.recordingDot} />
              <Text style={styles.recordingText}>CAMERA RECORDING</Text>
            </View>
            <Text style={styles.cardBody}>
              The AI judge is interviewing you. Your camera is recording. Answer each question naturally. End the session when the interview is complete.
            </Text>
            <TouchableOpacity style={styles.endButton} onPress={endInterview}>
              <Ionicons name="stop-circle" size={20} color="#fff" style={{ marginRight: 8 }} />
              <Text style={[styles.buttonText, { color: '#fff' }]}>END INTERVIEW</Text>
            </TouchableOpacity>
          </View>
        )}

        {step === 'scoring' && (
          <View style={[styles.card, GlassEffect, styles.center]}>
            <ActivityIndicator size="large" color={Theme.colors.accent} />
            <Text style={[styles.cardBody, { marginTop: 16, textAlign: 'center' }]}>
              Scoring verbal and visual criteria against the official FFA rubric…
            </Text>
          </View>
        )}

        {step === 'results' && result && (
          <View style={[styles.card, GlassEffect]}>
            <View style={styles.scoreRow}>
              <View style={styles.scoreBadge}>
                <Text style={styles.scoreText}>{result.score}/{result.maxScore ?? 400}</Text>
              </View>
              <Text style={styles.scoreLabel}>OFFICIAL GRADE</Text>
            </View>
            <Text style={styles.feedbackText}>{result.feedback}</Text>
            {result.strengths.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>STRENGTHS</Text>
                {result.strengths.map((s, i) => <Text key={i} style={styles.bullet}>• {s}</Text>)}
              </View>
            )}
            {result.improvements.length > 0 && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>GROWTH AREAS</Text>
                {result.improvements.map((s, i) => <Text key={i} style={styles.bullet}>• {s}</Text>)}
              </View>
            )}
            <TouchableOpacity style={styles.primaryButton} onPress={() => setStep('intro')}>
              <Text style={styles.buttonText}>PRACTICE AGAIN</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: 60 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  scroll: { padding: 24, paddingTop: 100 },
  header: { alignItems: 'center', marginBottom: 24 },
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: 'rgba(0,242,255,0.1)', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(0,242,255,0.3)', marginBottom: 20 },
  title: { fontSize: 24, fontWeight: '900', color: '#fff', letterSpacing: 2 },
  subtitle: { fontSize: 11, color: Theme.colors.text.muted, marginTop: 8, letterSpacing: 1, fontWeight: '700', textAlign: 'center' },
  card: { backgroundColor: Theme.colors.card, padding: 20, borderRadius: 24, marginBottom: 20 },
  cardTitle: { fontSize: 14, fontWeight: '900', color: Theme.colors.accent, letterSpacing: 1, marginBottom: 12 },
  cardBody: { fontSize: 14, color: 'rgba(255,255,255,0.7)', lineHeight: 22, fontWeight: '600' },
  warningText: { fontSize: 12, color: Theme.colors.warning, marginTop: 12, fontWeight: '700' },
  center: { alignItems: 'center', justifyContent: 'center' },
  statusRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  dot: { width: 12, height: 12, borderRadius: 6, marginRight: 10 },
  statusText: { fontSize: 13, fontWeight: '900', color: '#fff', letterSpacing: 1 },
  recordingBadge: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  recordingDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Theme.colors.error, marginRight: 8 },
  recordingText: { fontSize: 11, fontWeight: '800', color: Theme.colors.error, letterSpacing: 1 },
  primaryButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: Theme.colors.accent, padding: 16, borderRadius: 12, marginTop: 20 },
  endButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: Theme.colors.error, padding: 16, borderRadius: 12, marginTop: 20 },
  buttonText: { color: Theme.colors.black, fontSize: 15, fontWeight: '900', letterSpacing: 1 },
  errorBox: { backgroundColor: 'rgba(255,60,60,0.1)', borderWidth: 1, borderColor: 'rgba(255,60,60,0.3)', padding: 16, borderRadius: 12, marginBottom: 16 },
  errorText: { color: Theme.colors.error, fontSize: 13, fontWeight: '700' },
  scoreRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 16 },
  scoreBadge: { backgroundColor: Theme.colors.accent, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  scoreText: { color: Theme.colors.black, fontWeight: '900', fontSize: 18 },
  scoreLabel: { color: Theme.colors.accent, fontSize: 10, fontWeight: '800', letterSpacing: 1 },
  feedbackText: { fontSize: 14, color: '#fff', lineHeight: 22, marginBottom: 16, fontWeight: '600' },
  section: { marginTop: 12 },
  sectionTitle: { fontSize: 11, fontWeight: '800', color: Theme.colors.warning, letterSpacing: 1, marginBottom: 8 },
  bullet: { fontSize: 13, color: 'rgba(255,255,255,0.7)', fontWeight: '600', marginBottom: 4 },
  fallbackTitle: { fontSize: 20, fontWeight: '900', color: '#fff', marginTop: 20, letterSpacing: 2 },
  fallbackBody: { fontSize: 14, color: 'rgba(255,255,255,0.6)', textAlign: 'center', lineHeight: 22, marginTop: 12, paddingHorizontal: 24, fontWeight: '600' },
});
```

### Step 5: Add `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID` to `.env.example`

Add after the existing ElevenLabs entries:
```
EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID=your-video-agent-id-here
```

### Step 6: Type-check

```bash
npx tsc --noEmit -p .
```

Expected: no errors in modified files.

### Step 7: Run full test suite

```bash
npm test
```

Expected: all tests pass (no regressions).

### Step 8: Commit

```bash
git add app/practice/job-interview/video.tsx lib/scoring/job-interview.ts lib/scoring/job-interview.test.ts lib/prompts/job-interview-rubrics.ts .env.example
git commit -m "feat(job-interview): video interview — ElevenLabs agent + continuous recording + dual scoring"
```

---

## Task 10: Manual smoke test

No automated test covers the full end-to-end voice flow. Test manually after Tasks 8 and 9 are complete.

- [ ] **Step 1: Configure ElevenLabs agents**

Ensure both agents are configured in ElevenLabs dashboard:
- Phone agent: `EXPO_PUBLIC_ELEVENLABS_PHONE_AGENT_ID` (system prompt from `ELEVENLABS_PHONE_AGENT_SYSTEM_PROMPT`)
- Video agent: `EXPO_PUBLIC_ELEVENLABS_VIDEO_AGENT_ID` (system prompt from `ELEVENLABS_VIDEO_AGENT_SYSTEM_PROMPT`)
Both agents need `job_description_text` and `resume_text` dynamic variables.

- [ ] **Step 2: Start dev server**

```bash
npm run web
```

- [ ] **Step 3: Upload documents**

Navigate to Job Interview → Document Prep. Upload a real PDF job description and a resume PDF.

- [ ] **Step 4: Test phone interview**

Navigate to Phone Interview. Tap START CALL. Verify:
- Preparing spinner appears briefly
- Status changes to "JUDGE IS SPEAKING" when agent speaks
- Agent asks all 4 fixed rubric questions during the session
- Tap END CALL → Scoring spinner appears
- Results screen shows score (0–50), feedback, strengths, improvements

- [ ] **Step 5: Test video interview**

Navigate to Video Interview. Tap START INTERVIEW. Verify:
- CAMERA RECORDING badge appears once active
- Agent speaks and converses naturally
- Agent opens with "Tell me about yourself"
- Tap END INTERVIEW → "Scoring verbal and visual criteria…" spinner
- Results screen shows score (0–400), feedback with verbal + visual components

- [ ] **Step 6: Test fallback — no uploads**

Clear uploads. Start both phone and video interviews. Verify:
- Agents still start (use default dynamic variable values)
- No crash, graceful degradation

- [ ] **Step 7: Test fallback — native app**

Open on iOS simulator. Navigate to Phone and Video Interview screens. Verify NativeFallback renders on both.

---

## Self-Review

### Spec Coverage

| Spec requirement | Covered by |
|-----------------|-----------|
| Questions from uploaded JD + resume content | Tasks 8 & 9 (dynamic_variables injection) |
| Fixed FFA rubric questions verbatim in phone | Task 3 (PHONE_FIXED_QUESTIONS), Task 8 (agent system prompt) |
| ElevenLabs conversational agent — phone | Task 7 (dashboard), Task 8 (phone.tsx) |
| ElevenLabs conversational agent — video | Task 7 (dashboard), Task 9 (video.tsx) |
| Video: continuous camera recording | Task 9 (MediaRecorder) |
| Video: two-pass scoring (verbal + visual) | Task 9 (scoreVideoInterview) |
| Phone: transcript scoring | Task 6 (scoreInterviewTranscript), Task 8 |
| Session-only storage | Structural — no Supabase writes |
| School isolation | Structural — session-only, zero server storage |
| Fallback — files not uploaded | Tasks 8 & 9 (default dynamic variable values) |
| Fallback — ElevenLabs/Gemini unavailable | Tasks 8 & 9 (error handlers) |
| Native platform fallback | Tasks 8 & 9 (NativeFallback component) |

### Type Consistency

- `extractDocumentText(uri: string, mimeType: string): Promise<string>` — Tasks 8, 9
- `scoreInterviewTranscript(transcript: string): Promise<InterviewAnalysis>` — Task 8
- `scoreVideoInterview(transcript: string, videoUri: string): Promise<InterviewAnalysis>` — Task 9
- `InterviewAnalysis` — `score`, `maxScore`, `feedback`, `strengths`, `improvements` — unchanged throughout
