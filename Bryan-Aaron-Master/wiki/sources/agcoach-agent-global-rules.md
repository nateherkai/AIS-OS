---
name: agcoach-agent-global-rules
type: source
tags: [ag-coach-pro, agent, rules, branding, workflow]
source_files: [raw/_ingested/2026-05-16-agcoach-agent-global-rules.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Agent Global Rules

Rules applying to ALL tasks for Ag Coach Pro agents.

## 1. Skill Coordination

- Always search `.agent/skills/` before starting a new feature or complex refactor
- If a relevant skill exists (e.g., `ui-ux`, `problem-solving`, `ai-engine`), read its `SKILL.md` before proceeding
- Follow the "Logic Tree" pattern from `problem-solving` for any task requiring more than 3 file edits

## 2. Branding & Tone

- **Tone**: Professional, helpful, Texas FFA Advisor style (firm but polite)
- **Branding**: Primary Green (#004B23), Navy Blue (#003366), Gold (#FFB800)
- **Standard**: All new screens must use the Card pattern and include loading/error states

*Note: Current production CLAUDE.md specifies Navy #001F4D, Gold #D4A574 as primary colors. The values above reflect an earlier branding document.*

## 3. Communication Style

- Use bullet points for plans and explanations
- Be concise — don't explain basic concepts (Git, React, etc.)
- When stuck: Stop, summon `problem-solving`, build a new logic tree

## 4. Workspaces & Workflows

- Store specific instructions in `.agent/workflows/`
- Summon with `@` or `/` commands (if available) or by explicitly reading the file

## Related

- [[../sources/agcoach-agent-master-prompt|B.L.A.S.T. Master Prompt]]
- [[../concepts/agcoach-app-internal-skills-catalog|App Internal Skills Catalog]]
- [[../sources/agcoach-landing-page-guardrails|Landing Page Guardrails]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
