---
name: agcoach-gemini-schemas
type: source
tags: [ag-coach-pro, gemini, schema, scoring, creed, interview]
source_files: [raw/_ingested/2026-05-16-agcoach-gemini.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Gemini Data Schemas

Two JSON shapes used as the structured-output contract for Gemini-graded simulations.

## InterviewResult (Job Interview LDE)

```json
{
  "score": number,
  "maxScore": number,
  "feedback": string,
  "strengths": string[],
  "improvements": string[],
  "transcription": string,
  "rubricDetails": {
    "preparation": number,
    "communication": number,
    "professionalism": number,
    "technicalScore": number
  },
  "metadata": {
    "mode": "document" | "phone" | "video",
    "timestamp": string,
    "documentType"?: string
  }
}
```

## CreedResult (Creed Speaking LDE)

```json
{
  "score": number,
  "accuracy": number,
  "delivery": number,
  "response": number,
  "feedback": string,
  "missingPhrases": string[],
  "transcription": string
}
```

- `accuracy` = % word-perfect match.
- `delivery` + `response` = AI assessments of pace/tone and Q&A handling.

## Maintenance

- 2026-03-10: file initialized. No updates since — schemas may have drifted from current code.

## Related

- [[../concepts/agcoach-creed-speaking-lde|Creed Speaking LDE]]
- [[../concepts/agcoach-rag-architecture|RAG Architecture]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
