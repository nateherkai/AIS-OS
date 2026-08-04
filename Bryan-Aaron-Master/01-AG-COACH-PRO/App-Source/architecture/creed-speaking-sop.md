# SOP: Creed Speaking Simulation

## Goal
Provide a high-fidelity, deterministic simulation of the FFA Creed Speaking Leadership Development Event (LDE) following official national rubrics.

## Inputs
- **Recitation Video/Audio**: User's attempt at the five paragraphs of the FFA Creed.
- **Q&A Video/Audio**: Responses to three randomly selected official questions.
- **Official Rubric Data**: Points for Oral (400), Non-Verbal (300), and Q&A (300).

## Deterministic Scoring Logic
The simulation separates AI "judgment" (probabilistic) from rubric "calculation" (deterministic).

1. **Recitation Accuracy (Deterministic)**
    - Compare transcription vs. official FFA Creed text.
    - Deduction: **-20 pts per missed/added word**.
    - Threshold: Accuracy < 5% constitutes "No Audio/Failure".

2. **Time Deduction (Deterministic)**
    - Time Limit: 4 minutes (240 seconds).
    - Deduction: **-1 pt per second over 240s**.

3. **Oral & Non-Verbal Analysis (Navigation Layer)**
    - Call AI Engine with official rubric descriptors.
    - Map AI scores (1-5) to weighted points (e.g., Hesitation x 25).

4. **Q&A Evaluation (Navigation Layer)**
    - Transcribe responses.
    - Evaluate relevance and spontaneity against rubric.

## Edge Cases
- **No Audio**: Force 0 score + "Microphone Error" feedback.
- **Ambiguous Speech**: Use confidence thresholds from Whisper; if low, provide "Clarification Required" feedback.
- **Language**: Standard FFA rules apply to English. Spanish Creed follows specific state-level variations if applicable.

## Tools Required
- `tools/whisper_transcribe.py`: Deterministic audio-to-text.
- `tools/rubric_calculator.py`: Deterministic score summing and deduction application.
- `tools/creed_qa_router.py`: Logic for selecting and evaluating random questions.
