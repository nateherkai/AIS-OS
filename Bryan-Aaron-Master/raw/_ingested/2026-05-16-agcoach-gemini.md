# Gemini (Data Schemas & Maintenance Log)

## Data Schemas

### InterviewResult
Represents the outcome of a document or interview simulation analysis.
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

### CreedResult
Represents the grading of a Creed Speaking recitation.
```json
{
  "score": number,
  "accuracy": number, // Percentage of word-perfect match
  "delivery": number, // AI assessment of pace/tone
  "response": number, // AI assessment of Q&A
  "feedback": string,
  "missingPhrases": string[],
  "transcription": string
}
```

## Maintenance Log
- **2026-03-10**: System initialized.
