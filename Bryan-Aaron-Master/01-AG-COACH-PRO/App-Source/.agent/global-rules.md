# Texas FFA Training App - Global Agent Rules

These rules apply to ALL tasks for this agent.

## 1. Skill Coordination

- ALWAYS search `.agent/skills/` before starting a new feature or complex refactor.
- If a relevant skill exists (e.g., `ui-ux`, `problem-solving`, `ai-engine`), you MUST read its `SKILL.md` before proceeding.
- Follow the "Logic Tree" pattern from `problem-solving` for any task requiring more than 3 file edits.

## 2. Branding & Tone

- **Tone**: Professional, helpful, Texas FFA Advisor style (firm but polite).
- **Branding**: Primary Green (`#004B23`), Navy Blue (`#003366`), Gold (`#FFB800`).
- **Standard**: All new screens must use the Card pattern and include loading/error states.

## 3. Communication Style

- Use **Bullet Points** for plans and explanations.
- Be concise. Don't explain basic concepts (Git, React, etc.).
- When stuck: Stop, summon `problem-solving`, and build a new logic tree.

## 4. Workspaces & Workflows

- Store specific instructions in `.agent/workflows/` and summon with `@` or `/` commands (if available) or by explicitly reading the file.
