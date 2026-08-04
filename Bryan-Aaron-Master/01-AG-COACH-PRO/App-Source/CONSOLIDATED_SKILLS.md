# Consolidated FFA Training App Skills

This file provides a single source of truth for all custom agent skills used in the FFA Training App. Each skill defines a specific domain of ownership, core capabilities, and implementation standards.

## Table of Contents

1. [Advisor Intelligence](#1-advisor-intelligence)
2. [AI Engine](#2-ai-engine)
3. [Anatomy Alignment](#3-anatomy-alignment)
4. [Auto-Commit](#4-auto-commit)
5. [Backend & Data](#5-backend--data)
6. [Brand Identity](#6-brand-identity)
7. [Contest Builder](#7-contest-builder)
8. [CSV Question Importer](#8-csv-question-importer)
9. [Deployment & QA](#9-deployment--qa)
10. [Error Handling Patterns](#10-error-handling-patterns)
11. [ID Module Builder](#11-id-module-builder)
12. [Problem Solving](#12-problem-solving)
13. [QA & Performance](#13-qa--performance)
14. [Reviewing Code](#14-reviewing-code)
15. [UI/UX Agent](#15-uiux-agent)

---

## 1. Advisor Intelligence

**File Path:** `.agent/skills/advisor-intelligence/SKILL.md`

Owns the technical implementation of high-fidelity analytics, team management, and learning gap visualization for FFA Advisors.

### Principles

- **Data over Dates**: Show *what* they missed, not just *when*.
- **Actionable Insights**: Highlight weak areas for class focus.
- **Simulation Fidelity**: Scantron-ready scoring formats.
- **Advisor Efficiency**: Batch management and one-click assignments.

---

## 2. AI Engine

**File Path:** `.agent/skills/ai-engine/SKILL.md`

Owns all AI integrations including Gemini grading, Claude backup, OpenAI Whisper transcription, prompt engineering, and scoring pipeline optimization.

### Key Responsibilities

- AI scoring prompts & Whisper transcription fixes.
- Optimizing latency/cost and validating responses.
- Debugging rate limits, malformed responses, and timeouts.

---

## 3. Anatomy Alignment

**File Path:** `.agent/skills/anatomy-alignment/SKILL.md`

Provides a rigorous workflow for verifying and correcting anatomical marker alignment in the Livestock Anatomy module.

### Core Concepts

- **Standardized Grid**: Percentage-based (0-100) coordinates.
- **Aspect Ratio Locking**: Fixed 3:2 container with `resizeMode: "stretch"`.
- **Anatomy Anchors**: Specific X/Y ranges for species profiles.

---

## 4. Auto-Commit

**File Path:** `.agent/skills/auto-commit/SKILL.md`

Enforces that every time a task is completed, changes are automatically added to version control, committed with a descriptive message, and pushed to the remote repository.

### Workflow

1. Verify Completion
2. Review Changes (`git status`)
3. Commit with clear message
4. Push to remote

---

## 5. Backend & Data

**File Path:** `.agent/skills/backend-data/SKILL.md`

Owns Supabase integration, database schema, migrations, authentication, storage, API routes, and Zustand state management.

### Tech Stack

- Supabase (Postgres, Auth, Storage, Edge Functions).
- Zustand + AsyncStorage for state.
- Expo Router API routes.

---

## 6. Brand Identity

**File Path:** `.agent/skills/brand-identity/SKILL.md`

Provides the single source of truth for brand guidelines, design tokens, technology choices, and voice/tone.

### Resources

- Visual Design: `resources/design-tokens.json`
- Tech Stack: `resources/tech-stack.md`
- Voice & Tone: `resources/voice-tone.md`

---

## 7. Contest Builder

**File Path:** `.agent/skills/contest-builder/SKILL.md`

Builds complete FFA contest practice modules end-to-end including screens, data files, scoring logic, and navigation wiring.

### Templates

- Quiz-Based CDEs
- Speech/Presentation LDEs
- Role-Play CDEs
- Document/Portfolio CDEs
- ID / Flashcard Study Modules

---

## 8. CSV Question Importer

**File Path:** `.agent/skills/csv-question-importer/SKILL.md`

Streamlines building FFA contest practice modules by processing a CSV file of questions into the existing generic practice flow.

### Guardrail

- **NO NEW UI**: Use generic screens; only perform data plumbing.

---

## 9. Deployment & QA

**File Path:** `.agent/skills/deployment-qa/SKILL.md`

Enforces comprehensive pre-deployment and post-deployment checks for `agcoachpro.com`.

### Critical Directive

- **NEVER use Vercel CLI for prod**. Use the GitHub pipeline to ensure proper cache invalidation.
- Verify on live domain with `browser_subagent` before completion.

---

## 10. Error Handling Patterns

**File Path:** `.agent/skills/error-handling-patterns/SKILL.md`

Master error handling patterns across languages (exceptions, Result types, etc.) to build resilient applications.

### Best Practices

- Fail Fast, Preserve Context, Meaningful Messages.
- Use Circuit Breakers and Graceful Degradation.

---

## 11. ID Module Builder

**File Path:** `.agent/skills/id-module-builder/SKILL.md`

Automates the creation of Identification (ID) practice modules using AI image generation and categorical mapping.

### Process

1. Data Definition
2. AI Image Generation (One at a time)
3. Asset Mapping (local mapping file)
4. UI Scaffolding (dedicated directory)
5. Master Config

---

## 12. Problem Solving

**File Path:** `.agent/skills/problem-solving/SKILL.md`

Enforces a structural "Logic Tree" approach to complex tasks and breaking out of debugging "death loops".

### Rule

- Before modifying files, build a logic tree (Plan, Validate, Branch, Execute, Verify).

---

## 13. QA & Performance

**File Path:** `.agent/skills/qa-performance/SKILL.md`

Owns testing, performance optimization, bug fixing, bundle auditing, and build pipeline.

### Targets

- Launch < 3s, Scoring < 5s, List Scrolling 60 FPS.
- Audit for bundle bloat (e.g., three.js, gsap).

---

## 14. Reviewing Code

**File Path:** `.agent/skills/reviewing-code/SKILL.md`

Performs comprehensive code reviews for pull requests or specific files.

### Criteria

- Compliance with architectural patterns.
- Security (hardcoded secrets).
- Performance (re-renders, slow queries).

---

## 15. UI/UX Agent

**File Path:** `.agent/skills/ui-ux/SKILL.md`

Builds visual UI components, screens, navigation, theming, and animations.

### Constraints

- Mandatory use of `StyleSheet.create()`.
- **NO NativeWind/Tailwind**.
- 44pt minimum hit targets.
