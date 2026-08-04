# FFA Training App — Antigravity Agent Skills

## Installation

Copy the entire `.agent/skills/` folder into your project root, merging with your existing `.agent/skills/` directory.

```bash
# From your project root (ffa-training-app/)
cp -r /path/to/this/download/.agent/skills/* .agent/skills/
```

Your `.agent/skills/` directory should look like this after merging:

```
.agent/skills/
├── orchestrator/          ← NEW: Routes tasks, manages priorities
│   └── SKILL.md
├── ui-ux/                 ← NEW: Screens, components, styling
│   └── SKILL.md
├── contest-builder/       ← NEW: Builds CDE/LDE practice modules
│   └── SKILL.md
├── ai-engine/             ← NEW: Gemini/Whisper/Claude integration
│   └── SKILL.md
├── backend-data/          ← NEW: Supabase, auth, migrations, state
│   └── SKILL.md
├── qa-performance/        ← NEW: Testing, bugs, performance
│   └── SKILL.md
├── brand-identity/        ← EXISTING: Design tokens, voice/tone
│   ├── SKILL.md
│   └── resources/
├── error-handling-patterns/ ← EXISTING: Error patterns
│   ├── SKILL.md
│   ├── resources/
│   └── scripts/
└── reviewing-code/        ← EXISTING: Code review
    ├── SKILL.md
    └── scripts/
```

## How It Works

Antigravity automatically reads SKILL.md files and activates the relevant agent based on your request. The YAML frontmatter tells Antigravity WHEN to trigger each skill:

- **"Build the Extemporaneous Speaking module"** → triggers `contest-builder`
- **"Fix the styling on the dashboard"** → triggers `ui-ux`
- **"Optimize the creed scoring prompt"** → triggers `ai-engine`
- **"Add a table for class rosters"** → triggers `backend-data`
- **"Why is the app so slow to load?"** → triggers `qa-performance`
- **"Plan out what to build next"** → triggers `orchestrator`

## Usage Tips

1. **Be specific**: "Build the Entomology quiz module" works better than "add more contests"
2. **Name the agent if needed**: "Using the AI engine skill, optimize the Chapter Conducting prompt"
3. **Chain agents**: "First use contest-builder to create the Forestry module, then use qa-performance to test it"
4. **The orchestrator is your project manager**: Ask it to plan multi-step work across agents

## Agent Quick Reference

| Agent | Trigger When You Say... |
|-------|------------------------|
| Orchestrator | "plan", "what's next", "prioritize", broad multi-area tasks |
| UI/UX | "screen", "layout", "design", "navigation", "component", "styling" |
| Contest Builder | "contest", "CDE", "LDE", "practice module", "scoring logic" |
| AI Engine | "prompt", "AI", "grading", "Gemini", "Whisper", "transcription" |
| Backend & Data | "database", "migration", "auth", "Supabase", "API", "storage" |
| QA & Performance | "test", "bug", "performance", "bundle", "audit", "crash" |
