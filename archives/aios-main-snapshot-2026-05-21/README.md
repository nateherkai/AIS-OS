# AIS-OS — AI Operating System starter kit for Claude Code

A free, MIT-licensed starter kit that turns Claude Code into your personal **AI Operating System (AIOS)**. Audience: anyone building automations — solopreneurs, small business operators, managers, creators, AI consultants. Pairs with a companion masterclass video.

The kit personalizes itself to you via an `/onboard` interview, then gives you two recurring thinking skills (`/audit`, `/level-up`) to keep building leverage week over week.

> **AIS-OS** stands for **AI Automation Society OS** — the way Nate designed this AIOS to be set up for members of his community, [AI Automation Society](https://www.skool.com/ai-automation-society). The kit is universal (it works for anyone), but the structure mirrors how AIS members run their own businesses on top of it.

---

## The litmus test

> **"While you're not at your desk, your AIS-OS observes one real-world event and produces an output that's faster and more accurate than what you'd produce yourself."**

Every design decision in this kit rolls up to that test. If a layer, skill, or template doesn't contribute to it, it doesn't ship.

---

## How you'll know it's working

Three felt **success indicators** tell you the AIOS is actually changing how you work. Not KPIs — there's no objective metric. These are lived experiences that show up in your week.

**1. Team-reaches-out:**

> *"A teammate messages you with a question. You realize your AIOS would answer it better, faster, and with exact sources — even if you were awake and free. So you ask your AIOS too. That's the moment you stop being a bottleneck for your own knowledge."*

**2. Context-switching reduction:**

> *"You stop opening new tabs. You stop launching the desktop app. When something new lands, your first move is to ask the AIOS, not to open six things. The default surface for thought work shifts. Silent. Compounding."*

**3. Knowledge-leaves-your-head:**

> *"You stop trying to remember business facts. You don't rehearse what you decided last quarter or what your customer said in that meeting. You trust the retrieval. The AIOS holds the truth, you hold the questions."*

**Personal foundation → company AI-readiness.** Once these indicators show up for one person, the same data architecture powers everything else. Custom dashboards on the data you already collect. Automations on top of the connections you already wired. Team rollout where everyone has theirs. *A company where every operator runs a personal AIOS is a company that's actually AI-ready.*

The kit teaches personal AIOS first. Everything scales from there.

---

## Two frameworks

The kit teaches two complementary frameworks. **Three Ms first, Four Cs second.** Without the brain rewire, the architecture is just a folder structure.

### The Three Ms — operator brain (how you think)

| M | One-liner |
|---|---|
| **Mindset** | Default Shift, Function Breakdown, Curiosity Rule. *To what extent can AI be leveraged here?* |
| **Method** | Find Constraint → EAD (Eliminate, Automate, Delegate) → Map Process → Pick Autonomy Level → Tie to KPI. |
| **Machine** | Lego Principle, Validation Chain, Bike Method, Intern Rule, Kill Switch. *Boring is beautiful. Workflows beat agents.* |

Full breakdown in `references/3ms-framework.md`. The `/level-up` skill walks you through all three weekly.

> *The Three Ms of AI™ is a trademark of Nate Herk. © 2026 Nate Herk.*

### The Four Cs — architecture (what you build)

| # | Layer | One-liner | "This layer is in place" test |
|---|---|---|---|
| 1 | **Context** | Knows your business | Fresh Claude session answers "what does this business do and who works here?" without browsing |
| 2 | **Connections** | Reaches your stuff | "What's on my calendar tomorrow and what tasks are due?" → live data, no paste |
| 3 | **Capabilities** | Knows how to do the work | A short phrase triggers a multi-step workflow that produces an artifact |
| 4 | **Cadence** | Runs without being asked | Laptop closed. A brief lands in the inbox. A teammate messages it and gets a real answer |

**Brand line:** Context. Connections. Capabilities. Cadence.

> *The Four Cs of an AIOS™ is a trademark of Nate Herk. © 2026 Nate Herk.*

Dependency graph: Context is non-skippable. Connections + Capabilities can build in parallel. Cadence is last — don't automate workflows that don't work manually.

---

## What ships — 3 skills

The kit is intentionally lean. Skills here are ideation prompts and thinking tools, not heavy automations. You hack on top of the structure.

| Skill | Type | When to run |
|---|---|---|
| `/onboard` | Setup wizard (one-time) | Day 1, immediately after clone. 7-question interview. Generates Day-1 file set + fills `CLAUDE.md`. |
| `/audit` | Recurring thinking skill | Day 7, then weekly. Four-Cs gap report. Read-only. Watch the score climb. |
| `/level-up` | Recurring thinking skill | Day 14, then weekly. Three Ms interview (Mindset → Method → Machine). One run = one shipped artifact. |

`/audit` asks *"is the AIOS built right?"* (form). `/level-up` asks *"what business leverage am I missing?"* (function). They work in series — fix structure first, then capability planning becomes meaningful.

---

## Quick start

1. **Clone the repo** to a working folder on your machine.
2. **Open it in Claude Code** and run `/onboard`. Answer the 7 questions honestly. Voice samples must be pasted, not described. Takes ~15 minutes. Day-1 file set drops at the end.
3. **Use it for a week.** Bring real questions. Make real decisions. Log them via `/decision` (or just append to `decisions/log.md`).
4. **Day 7:** run `/audit`. Read the Four-Cs gap report. Pick one gap to close.
5. **Day 14:** run `/level-up`. The Three Ms interview surfaces one automation worth building. Build it.
6. **Week 3+:** weekly `/level-up` ritual. One shipped artifact per week.

---

## Repo layout

```
AIS-OS/
├── README.md
├── CLAUDE.md                        ← Your operating manual (filled by /onboard)
├── EXPANSIONS.md                    ← What to add as you grow
├── LICENSE
├── .gitignore
├── aios-intake.md                   ← Source-of-truth for /onboard. Edit + re-run any time.
├── connections.md                   ← Registry of every system your AIOS can reach
├── context/                         ← About you, your business (filled by /onboard)
├── references/
│   └── 3ms-framework.md             ← The operator brain
├── decisions/
│   └── log.md                       ← Append-only record of what was decided and why
├── archives/                        ← Old stuff. Don't delete. Move here.
└── .claude/
    └── skills/
        ├── onboard/SKILL.md
        ├── audit/SKILL.md
        └── level-up/SKILL.md
```

See `EXPANSIONS.md` for what to add as you grow (`projects/`, `templates/`, `scripts/`, `.claude/agents/`, sub-OS folders, etc.).

---

## License + attribution

MIT License. © 2026 Nate Herk.

The Three Ms of AI™ and The Four Cs of an AIOS™ are trademarks of Nate Herk. Both frameworks ship in this repo with attribution. Use freely; don't repackage as your own.

The companion masterclass video walks you through the kit step by step. Link will land here once it ships.
