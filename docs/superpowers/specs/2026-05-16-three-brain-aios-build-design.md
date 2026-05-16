# AIS-OS Three-Brain Build — Design Spec

**Date:** 2026-05-16
**Author:** Bryan Aaron + Claude
**Status:** Draft pending Bryan review
**Approach:** K2 (hybrid) — Karpathy LLM Wiki inside `Bryan-Aaron-Master/` w/ existing 01-07 domain folders preserved + Roberts CC-OS dashboard layer in `AIS-OS/` + Herk skills/agents machine.

## Source material

- Andrej Karpathy — LLM Wiki tweet/gist (markdown-only knowledge base pattern)
- Nate Herk — walkthrough video `youtu.be/sboNwYmH3AY` (Karpathy pattern w/ Obsidian)
- Jack Roberts — Claude Code OS video `youtu.be/MAuLQzcMrS0` (dashboard + dreaming engine)

## Goal

Unify Bryan's existing AIS-OS repo + Bryan-Aaron-Master Obsidian vault into one operating system:
- Vault = knowledge layer (Karpathy LLM Wiki + existing domain folders)
- AIS-OS = operator layer (dashboard, dreaming engine, skills, agents)
- Bridged by CLAUDE.md files declaring paths + read/write rules

Serves Bryan's Q-goals: close 50 schools on Ag Coach Pro by Aug 2026, hit $120K/yr, reduce manual ops via dreaming-suggested automations.

---

## 1. Architecture

```
Bryan-Aaron-Master/                  ← Karpathy wiki + Herk domains
├── CLAUDE.md                        ← vault schema + ingest rules
├── raw/                             ← inbox only (replaces 00-INBOX)
│   └── _ingested/                   ← post-ingest archive
├── wiki/                            ← LLM-derived crosslinks layer
│   ├── index.md                     ← master index
│   ├── log.md                       ← ingest history (append-only)
│   ├── hot.md                       ← 500-char recent cache
│   ├── sources/                     ← article/video/transcript pages
│   ├── people/
│   ├── organizations/
│   ├── concepts/
│   ├── analysis/
│   └── comparisons/
├── 01-AG-COACH-PRO/                 ← human-curated truth (unchanged)
├── 02-AARON-FAMILY-LIVESTOCK/
├── 03-TEACHING/
├── 04-FINANCES/
├── 05-PERSONAL/
├── 06-AI-WORKFLOW/
├── 07-RESOURCES/
└── Business_Brain.md

AIS-OS/                              ← Roberts OS layer
├── CLAUDE.md                        ← declares wiki_path = vault/wiki
├── dashboard/                       ← 6-pillar dashboard (existing scaffold)
│   ├── index.html
│   ├── config.json                  ← $hourly_value + paths
│   ├── data/dreams/                 ← canonical dream JSON (dream.py writes here)
│   └── scripts/memory_graph.py
├── skills/ (.claude/skills/)        ← Herk machine
├── scripts/
│   ├── ingest.py                    ← raw → wiki pipeline trigger
│   ├── lint.py                      ← Karpathy health check
│   └── dream.py                     ← 8-dim nightly pass
└── docs/superpowers/specs/          ← this file
```

### Data flow

1. Bryan drops note/article/transcript into `vault/raw/`.
2. `/ingest` (skill) → Claude reads raw → writes wiki pages w/ `[[links]]` → updates index + log + hot.
3. Wiki crosslinks to 01-07 via `[[01-AG-COACH-PRO/...]]` syntax. Domain folders never overwritten.
4. Dashboard reads `vault/wiki/{index,log,hot}.md` + `dreams/*.json` + `.claude/skills/*` + `connections.md`.
5. Dream engine runs nightly (cron), scans 8 dims, writes ≤4 cards to `AIS-OS/dashboard/data/dreams/YYYY-MM-DD.json`.

### Rules

- `raw/` = write-only inbox until ingest moves it to `raw/_ingested/`.
- One source of truth per fact. Wiki = derived. 01-07 = authoritative.
- Vault CLAUDE.md = schema/ingest rules. AIS-OS CLAUDE.md = OS rules + wiki_path.
- AIS-OS scripts never mutate 01-07 directly. Dream may suggest; Bryan executes.

---

## 2. Ingest pipeline

Trigger: file in `vault/raw/` → `/ingest` or "ingest raw" prompt → Claude executes.

Steps:
1. List new files in `raw/` not in `wiki/log.md`.
2. Classify per file: source / transcript / note / meeting / article / image-OCR.
3. Load context: `vault/CLAUDE.md`, `wiki/index.md`, last 10 `log.md` entries, `Business_Brain.md`.
4. First ingest per session only: ask focus/granularity/domain hint.
5. Semantic chunk + extract entities (people, orgs, concepts), claims, dates, links.
6. Write wiki pages — one per entity, in correct subdir, YAML frontmatter required.
7. Crosslink to 01-07 when entity belongs to domain.
8. Update `wiki/index.md` (append under right section).
9. Append `wiki/log.md` (date, source, pages, links, open questions).
10. Overwrite `wiki/hot.md` w/ 500-char summary.
11. Move raw file → `raw/_ingested/YYYY-MM-DD-<name>`.

### Conventions

- Filenames: kebab-case. Date in frontmatter, not filename.
- Every wiki page MUST have ≥1 outbound link. No orphans.
- Wiki never duplicates raw verbatim — summary + claims + links.
- Domain crosslinks use full path: `[[01-AG-COACH-PRO/Competitor-Intel|Competitor Intel]]`.

### Failure modes

- Ambiguous classification → ask once, log answer for similar future files.
- Duplicate entity → merge into existing page, append `source_files`, log merge.
- No clear domain → tag `domains: [unassigned]`, surface in next lint.

---

## 3. Schema

### `vault/CLAUDE.md` (append to existing)

```markdown
## Vault as Karpathy LLM Wiki

- raw/ — inbox. Drop sources here. Never edit by hand after ingest.
- wiki/ — LLM-derived crosslinks. Read for queries, write only via ingest.
- 01-07/ — human-curated domain truth. Wiki crosslinks here, never overwrites.

### Ingest rules
1. Read vault/CLAUDE.md, wiki/index.md, wiki/log.md (last 10), Business_Brain.md before ingest.
2. One page per entity. YAML frontmatter required.
3. Every page ≥1 outbound link. No orphans.
4. Crosslink to 01-07 by full path.
5. Move raw file to raw/_ingested/ after.
6. Update index.md + log.md + hot.md each ingest.

### Query rules
- Start at wiki/index.md → follow links.
- Read wiki/hot.md for recent context.
- Don't crawl raw/ unless wiki insufficient.
- Don't read 01-07 unless wiki points there.
```

### `vault/wiki/index.md`

Master TOC. Sections: Tools, Techniques, Sources, People, Organizations, Concepts, Comparisons, Domain Map (→ 01-07).

### `vault/wiki/log.md`

Append-only. Each entry: timestamp, source file, type, pages created, domains linked, open questions, archive path.

### `vault/wiki/hot.md`

500-char ceiling, overwrite each ingest. Recent context cache for query speed.

### Wiki page template

```markdown
---
name: <slug>
type: <concept|source|person|organization|analysis|comparison>
tags: [...]
source_files: [...]
domains: [...]              # links to 01-07 or [unassigned]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# <Title>

<Summary 1-3 paragraphs>

## <Section headers as needed>

## Related
- [[other-wiki-page]]
- [[01-DOMAIN/note-name]]
```

### `AIS-OS/CLAUDE.md` (append)

```markdown
## Vault bridge (Roberts OS ↔ Karpathy wiki)

- vault_root: ./Bryan-Aaron-Master/
- wiki_path: ./Bryan-Aaron-Master/wiki/
- raw_path: ./Bryan-Aaron-Master/raw/
- Dashboard reads vault/wiki/{index,log,hot}.md (never writes).
- Dream engine writes to AIS-OS/dashboard/data/dreams/, may suggest vault changes (Bryan executes).
- Ingest skill writes to vault. AIS-OS scripts never touch 01-07.
```

### `~/.claude/CLAUDE.md` (append)

```markdown
## Bryan-Aaron-Master vault pointer

Karpathy LLM Wiki at /Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master.
- Domain queries: read vault/wiki/index.md → follow links.
- Recent context: read vault/wiki/hot.md.
- Don't crawl vault/raw/ or 01-07 unless wiki insufficient.
```

### Updated session-start protocol

```
1. gravity-claw/memory/00_Core/MEMORY.md
2. gravity-claw/memory/01_Bryan/bryan.md
3. Bryan-Aaron-Master/wiki/hot.md     ← NEW
4. Bryan-Aaron-Master/wiki/index.md   ← NEW (skim only)
5. Project CLAUDE.md
```

### Updated query protocol

1. Vault wiki (Karpathy) — primary for domain knowledge
2. Graphify graph.json — codebase structure
3. Gravity Claw vault — decisions, session logs
4. Pinecone — semantic recall across sessions
5. Raw code / raw vault files — only when 1-4 insufficient

---

## 4. Dashboard + Dreaming engine (Roberts OS layer)

### 6 dashboard cards

1. **Models** — auto-detect Claude Code, Codex, Gemini, ChatGPT, OpenRouter from local config; show current limits.
2. **Plans** — subscriptions w/ monthly cost. Manual entry first pass; MCP later if available.
3. **Memory** — Pinecone (gravityclaw/knowledge), Obsidian vault, AIS-OS memory/, Supabase. Visual map.
4. **Skills** — `.claude/skills/` + project skills listing. Last-used date, invoke count, est. ROI per use.
5. **Knowledge** — vault wiki stats: page count, orphans, last ingest, hot.md preview, graph link.
6. **Connections** — `connections.md` rendered live. Status dots per service.

### ROI calculator

Bryan sets `$hourly_value` in `AIS-OS/dashboard/config.json`. Each skill invocation logs estimated minutes saved. Dashboard sums monthly: `time_saved × hourly − subs = net ROI`.

### Dreaming engine

- File: `AIS-OS/scripts/dream.py` (Python, calls Claude API).
- Trigger: cron nightly (default 02:00). Manual via `/dream`.
- Output: `AIS-OS/dashboard/data/dreams/YYYY-MM-DD.json` (canonical, existing path).
- Cap: ≤4 cards per night (Roberts pattern).

### 8 dimensions

| # | Dim | Source | Looks for |
|---|---|---|---|
| 1 | Conversation | last 7d Claude Code transcripts | tasks done manually 3+ times → skill candidate |
| 2 | Cost | model call logs | Opus used for Haiku-tier work, low cache hit |
| 3 | Skill perf | `.claude/skills/` usage logs | stale skills, high-ROI skills, missing skills |
| 4 | Memory health | vault wiki + Pinecone | orphan pages, stale entries, missing crosslinks |
| 5 | Session hygiene | token usage / session | bloat patterns, when limits hit |
| 6 | Workflow | git log + file changes | duplicated work across projects |
| 7 | External opps | web search (user permission) | new tools/skills fitting Bryan's stack |
| 8 | Business context | Business_Brain.md + wiki | progress vs 50-schools/$120K goal |

### Card JSON schema

```json
{
  "date": "2026-05-16",
  "cards": [
    {
      "id": "d1",
      "dim": "skill-perf",
      "title": "Trial follow-up skill not used in 14 days",
      "insight": "5 trials cooling. Skill exists, unused.",
      "action": "Run /trial-follow-up this week.",
      "estimated_value_minutes": 90,
      "status": "open"
    }
  ],
  "summary": "1-line dream summary",
  "next_run": "2026-05-17T02:00:00"
}
```

### Lint (separate from dream)

- File: `AIS-OS/scripts/lint.py`. Weekly cadence.
- Checks: orphan pages, stale `updated:` (>90d), broken crosslinks, missing frontmatter, raw files >7d unprocessed.
- Output: `AIS-OS/dashboard/lint-report.md` + dashboard badge w/ issue count.

---

## 5. Skills & agents layer (Herk machine)

### Skill locations

| Path | Scope | Use case |
|---|---|---|
| `~/.claude/skills/` | global | cross-project skills (graphify, three-brain, level-up, audit, etc.) |
| `AIS-OS/.claude/skills/` | project | OS-specific (onboard, trial-follow-up, weekly-pipeline-check) |
| `Bryan-Aaron-Master/.obsidian/scripts/` | vault | optional vault-side helpers |

### New skills (this build)

| Skill | Trigger | Function |
|---|---|---|
| `ingest` | `/ingest` | raw → wiki pipeline per §2 |
| `wiki-query` | `/wiki <topic>` | query wiki by following index → links |
| `wiki-lint` | `/lint` | weekly health check per §4 |
| `dream` | `/dream` or cron | 8-dim dream pass, write card JSON |
| `skill-suggest` | auto (dream dim 1) | surface "you did X 3+ times, make skill?" |
| `hot-update` | sub-action of ingest | refresh `wiki/hot.md` |

### Existing skills (kept)

`onboard`, `audit`, `level-up`, `trial-follow-up`, `weekly-pipeline-check`, `draft-reply`, `three-brain`, `graphify`, `wrapup`.

### Agent roster

| Agent | Subagent type | When |
|---|---|---|
| Codex rescue | `codex:codex-rescue` | adversarial review, stuck 3+ tries, sensitive paths |
| Gemini bridge | `cc-gemini-plugin:gemini-agent` | video/audio/large repo scans |
| Explore | `Explore` | quick code lookups |
| Plan | `Plan` | implementation plans |
| Claude default | `claude` | everything else |

Routed by existing `three-brain` skill.

---

## 6. Bridge + slash commands

### Slash command registry

| Command | Skill | Runs in | Function |
|---|---|---|---|
| `/ingest` | `ingest` | vault | raw → wiki pipeline |
| `/wiki <q>` | `wiki-query` | any | query wiki by index+links |
| `/lint` | `wiki-lint` | any | health check vault |
| `/dream` | `dream` | AIS-OS | manual dream pass |
| `/dashboard` | (open file) | AIS-OS | launch dashboard/index.html |
| `/hot` | `hot-update` | vault | refresh hot.md manually |
| `/level-up` | existing | AIS-OS | weekly 3Ms |
| `/audit` | existing | AIS-OS | Four-Cs |
| `/onboard` | existing | AIS-OS | intake refresh |
| `/trial-follow-up` | existing | AIS-OS | trial close drafts |
| `/wrapup` | existing | any | session end |

### Dashboard ↔ vault data paths (read-only)

```
vault/wiki/index.md      → dashboard "Knowledge" card
vault/wiki/log.md        → dashboard "Recent ingests" widget
vault/wiki/hot.md        → dashboard "Hot cache" preview tile
AIS-OS/dashboard/data/dreams/*.json → dashboard "Tonight's dreams" card
.claude/skills/*/SKILL.md → dashboard "Skills" card
connections.md           → dashboard "Connections" card
```

---

## 7. Migration plan + rollout

8 phases. Each = independent commit. Stop after any failure.

### Phase 0 — Safety net
- `git init` if vault not git.
- Snapshot: `cp -r Bryan-Aaron-Master Bryan-Aaron-Master.backup-2026-05-16`
- Commit current AIS-OS state.

### Phase 1 — Vault scaffold (Agent A)
- Create `raw/`, `raw/_ingested/`, `wiki/` + subdirs.
- Write empty `index.md`, `log.md` (header), `hot.md` (placeholder).
- Append Karpathy schema block to vault `CLAUDE.md`.
- Don't touch 01-07.

### Phase 2 — 00-INBOX migration
- Move `Bryan-Aaron-Master/00-INBOX/*` to `raw/` (if any contents). Delete 00-INBOX.
- Commit.

### Phase 3 — Skills build (Agent B, parallel)
- Write SKILL.md for: `ingest`, `wiki-query`, `wiki-lint`, `dream`, `hot-update`, `skill-suggest`.
- Test invocation only (no real ingest).

### Phase 4 — First ingest test
- Drop both YT transcripts (`/tmp/yt_sboNwYmH3AY.txt`, `/tmp/yt_MAuLQzcMrS0.txt`) into `vault/raw/` w/ proper names.
- Run `/ingest`.
- Verify: wiki pages, index updated, log entry, hot.md populated, raw moved to `_ingested/`.
- Block on success.

### Phase 5 — Dashboard wiring (Agent C, parallel w/ Phase 6)
- Update `AIS-OS/dashboard/index.html`: Knowledge card, Hot tile, Dreams card.
- Update `memory_graph.py` to include vault wiki.
- Add `config.json` w/ `hourly_value`.
- Smoke test: open `index.html`, all cards render.

### Phase 6 — Dream engine (Agent D, parallel w/ Phase 5)
- Write `scripts/dream.py` (8-dim, calls Claude API, writes JSON).
- Write `scripts/lint.py`.
- Write `scripts/ingest.py` (CLI wrapper, optional).
- Cron entry drafted, NOT auto-installed (Bryan confirms).
- Manual run → verify card JSON.

### Phase 7 — Bridge + protocol
- Append vault bridge to `AIS-OS/CLAUDE.md`.
- Append vault pointer to `~/.claude/CLAUDE.md`.
- Update three-layer query protocol.
- Codex rescue: adversarial review of `ingest.py` + vault schema.

### Phase 8 — Live test
- New real-source ingest (recent meeting note).
- Run `/lint` → fix issues.
- Run `/dream` → verify 4 cards.
- Open dashboard → all cards live.
- Commit + tag `aios-v1`.

### Time estimate
~2 hrs parallel, ~3.5 hrs serial.

### Rollback
Any phase fails → `git reset --hard` + restore vault from `.backup-2026-05-16`.

---

## Open questions

- Cron auto-install: Bryan confirms before write to crontab? (Default: yes, confirm.)
- `hot.md` per-domain or single? (Default: single global, revisit after 30 days.)
- Wiki page max length? (Default: no cap, but lint flags >2000 words for split.)
- Dream cadence: nightly fixed or "when laptop idle >30min"? (Default: nightly 02:00.)
- External opps (dim 7) — web search consent per-run or once? (Default: once at onboard.)

## Success criteria

- `/ingest` on a real source produces clean wiki pages w/ working crosslinks.
- Dashboard renders all 6 cards w/ live vault data.
- `/dream` produces ≤4 actionable cards w/ ROI estimates.
- `/lint` finds + reports issues, doesn't auto-fix.
- Bryan can query vault knowledge via `/wiki <topic>` in any project, gets synthesized answer w/o full crawl.
- 30-day check: dreaming engine surfaces ≥3 automations Bryan ships.

## Out of scope (v1)

- Multi-user vault (Bryan only).
- Vector DB / RAG fallback (Karpathy pattern only; revisit if vault >500 pages).
- Auto-execute dream suggestions (manual approval always).
- Mobile dashboard.
- Public/team sharing.
