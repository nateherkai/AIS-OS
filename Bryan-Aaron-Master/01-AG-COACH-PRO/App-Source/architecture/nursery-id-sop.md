# SOP: Nursery & Landscape Identification

## Goal
Provide a deterministic identification contest module for plants, pests, and tools in the Nursery & Landscape CDE.

## Inputs
- **Official ID List**: Master list of items required for the contest.
- **High-Resolution Images**: Mapped to official items.
- **Scoring Rules**: +2 pts for correct ID, 0 for incorrect.

## Deterministic Contest Logic

1. **Randomization**
    - Select X items from the master list (typically 25 or 50).
    - Ensure no duplicates in a single contest.

2. **Scoring**
    - Input: `user_answer_id`, `correct_item_id`.
    - Logic: `score = (user_answer_id == correct_item_id ? 2 : 0)`.

3. **Image Verification**
    - SOP for ensuring every item ID in the database has a verified asset path in `nursery-landscape-images.ts`.

## Tools Required
- `tools/id_asset_auditor.py`: Deterministic script to verify all items have images.
- `tools/contest_generator.py`: Deterministic randomization and scoring engine.
