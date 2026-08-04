# SOP: Job Interview Simulation

## Goal
Provide a high-fidelity, deterministic simulation of the FFA Job Interview Career Development Event (CDE) following official Texas FFA rubrics.

## Inputs
- **Application Materials**: Resume, Cover Letter, Application, Follow-up Letter.
- **Phone Interview Audio**: User's response to AI-generated questions.
- **Video Interview Video**: User's visual and verbal performance.
- **Official Rubric Data**: Document Rubric (100 pts each), Interview Rubric (500 pts).

## Deterministic Scoring Logic

1. **Document Analysis (Navigation Layer -> AI Engine)**
    - AI analyzes materials against specific Texas FFA criteria (Formatting, Content, Professionalism).
    - Results stored in `JobInterviewStore`.

2. **Interview Evaluation (Navigation Layer -> AI Engine)**
    - Speech-to-text conversion (Deterministic).
    - Evaluation of content relevance, communication skills, and professionalism.

3. **No-Audio Penalty (Deterministic)**
    - If transcription < 5 characters or empty, score = 0.
    - Applies to both Phone and Video simulations.

4. **Native Fallback (Deterministic)**
    - Check browser/platform capability before recording.
    - If `MediaRecorder` or `mediaDevices` unavailable, block entry and redirect to Phone Sim.

## Tools Required
- `tools/rubric_calculator.py`: Shared tool for final score aggregation.
- `tools/document_validator.py`: (Planned) Deterministic checks for file types and metadata.
