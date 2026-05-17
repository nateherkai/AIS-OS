---
name: orchestrating-tasks
description: Routes tasks to the correct specialist agent, manages priorities, resolves cross-cutting concerns, and tracks project state. Use when the user gives a broad or multi-domain task, asks "what should I work on next", or when a task spans multiple areas of the codebase (UI + backend + AI, etc).
---

# Orchestrator Agent

## When to use this skill
- User gives a vague or multi-domain task
- User asks what to work on next or wants a plan
- A task touches 3+ areas (UI, backend, AI, scoring, etc.)
- Need to resolve file ownership conflicts between agents

## Project Context

**App**: FFA Training App — Expo/React Native mobile app for Texas FFA students to practice 29 CDEs and 11 LDEs with AI-powered feedback.

**Stack**: Expo SDK 52, React Native 0.76, TypeScript, Supabase, Zustand, Gemini 1.5 Flash, OpenAI Whisper

**Currently implemented**: Creed Speaking, Spanish Creed, Chapter Conducting, Job Interview, Greenhand Quiz, Senior Quiz, Ag Advocacy, Ag Issues, Ag Skills, Public Relations, Radio Broadcasting

**Remaining**: ~18 CDEs, ~5 LDEs, offline mode, teacher analytics, app store deployment

## Agent Roster & Routing

| Domain | Agent Skill | Trigger Keywords |
|--------|------------|-----------------|
| Screens, components, styling, navigation, animations | `ui-ux` | layout, design, screen, component, color, theme, navigation |
| New contest modules, scoring logic, contest data | `contest-builder` | contest, CDE, LDE, practice module, new event, scoring logic |
| Gemini/Claude/Whisper, prompts, grading, transcription | `ai-engine` | AI, prompt, grading, feedback, transcription, Gemini, Whisper |
| Supabase, auth, database, storage, API routes, state | `backend-data` | database, migration, auth, Supabase, API, storage, Zustand |
| Testing, bugs, bundle size, performance, builds | `qa-performance` | test, bug, crash, performance, bundle, slow, audit |

## Shared Files (changes need coordination)
- `constants/contests.ts` — Contest Builder + UI Agent
- `constants/colors.ts` — UI Agent primary, all agents reference
- `types/index.ts` — All agents
- `lib/supabase.ts` — Backend primary, all agents use

## Workflow
1. [ ] Classify the domain(s) the task involves
2. [ ] Check for file ownership conflicts (see shared files above)
3. [ ] Break into atomic sub-tasks with clear acceptance criteria
4. [ ] Identify dependencies (what must happen first)
5. [ ] Route sub-tasks to the relevant agent skill(s)
6. [ ] Validate output before marking complete

## Priority Roadmap

### Phase 1: Foundation (Week 1-2)
- QA Agent: Bundle audit, remove bloat deps (three.js, gsap, framer-motion)
- Backend Agent: Add migrations for new contest types
- AI Agent: Optimize Gemini prompts for existing contests

### Phase 2: Remaining Contests (Week 3-8)
- Batch 1: Quiz-type CDEs (Agronomy, Entomology, Forestry, etc.)
- Batch 2: Judging CDEs (Dairy Cattle, Horse, Poultry, etc.)
- Batch 3: Speech LDEs (Extemporaneous, Prepared Speaking)
- Batch 4: Skills CDEs (Ag Mechanics, Tractor Tech, etc.)

### Phase 3: Teacher Dashboard (Week 9-10)
- Backend: Teacher analytics queries and class management
- UI: Admin dashboard screens refinement

### Phase 4: Polish & Launch (Week 11-12)
- QA: Full regression, performance optimization
- UI: Onboarding, app store screenshots
- Backend: Production Supabase, monitoring

## Handoff Format
When routing to another agent:
```
HANDOFF → [agent-skill-name]
Task: [what needs to be done]
Files: [paths to create/modify]
Depends on: [what must be done first]
Accept when: [definition of done]
```
