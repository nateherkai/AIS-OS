# Three-Brain AIS-OS Build — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire `Bryan-Aaron-Master/` Obsidian vault as Karpathy LLM Wiki (K2 hybrid w/ 01-07 domain folders preserved) + extend `AIS-OS/` as Roberts-style operator dashboard + Herk skills layer. Single OS, dual repos, bridged by CLAUDE.md.

**Architecture:** Vault = knowledge (raw/ inbox + wiki/ derived crosslinks + 01-07 human-curated). AIS-OS = operator (dashboard reads vault, scripts/dream.py runs nightly, skills handle ingest/query/lint/dream). All bridges declared in CLAUDE.md files.

**Tech Stack:** Markdown, Python 3 (Claude API via `anthropic` SDK), Obsidian (vault viewer only), Claude Code skills, bash, git.

**Spec:** `docs/superpowers/specs/2026-05-16-three-brain-aios-build-design.md`

---

## File structure

**Created in vault (`Bryan-Aaron-Master/`):**
- `raw/` (empty dir + `.gitkeep`)
- `raw/_ingested/` (empty dir + `.gitkeep`)
- `wiki/index.md`
- `wiki/log.md`
- `wiki/hot.md`
- `wiki/sources/.gitkeep`, `people/.gitkeep`, `organizations/.gitkeep`, `concepts/.gitkeep`, `analysis/.gitkeep`, `comparisons/.gitkeep`

**Modified in vault:**
- `CLAUDE.md` (append Karpathy schema block)
- `00-INBOX/` → moved into `raw/`, then deleted

**Created in AIS-OS (`/Volumes/Samsung PSSD T7/AIS-OS/`):**
- `scripts/dream.py` (8-dim nightly engine)
- `scripts/lint.py` (vault health check)
- `scripts/ingest.py` (CLI wrapper for ingest skill)
- `scripts/__init__.py`
- `scripts/test_dream.py`
- `scripts/test_lint.py`
- `dashboard/config.json` (hourly_value + paths)
- `requirements.txt`

**Modified in AIS-OS:**
- `dashboard/index.html` (Knowledge card, Hot tile, Dreams card)
- `dashboard/scripts/memory_graph.py` (include vault wiki nodes) — NOTE: user has existing uncommitted changes; preserve them
- `CLAUDE.md` (append vault bridge block)

**Created in global Claude config (`~/.claude/`):**
- `skills/ingest/SKILL.md`
- `skills/wiki-query/SKILL.md`
- `skills/wiki-lint/SKILL.md`
- `skills/dream/SKILL.md`
- `skills/hot-update/SKILL.md`
- `skills/skill-suggest/SKILL.md`

**Modified in global config:**
- `~/.claude/CLAUDE.md` (append vault pointer block)

---

## Task 1: Safety net — backup vault + git init

**Files:**
- Create: `Bryan-Aaron-Master.backup-2026-05-16/` (snapshot)
- Verify: vault git status

- [ ] **Step 1: Verify vault is a git repo**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git rev-parse --is-inside-work-tree 2>/dev/null || echo "NOT_GIT"
```

Expected: `true` OR `NOT_GIT`. If `NOT_GIT`, proceed to Step 2. If `true`, skip to Step 3.

- [ ] **Step 2: Init vault git repo (only if NOT_GIT)**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git init && git add . && git commit -m "chore: initial vault snapshot before Karpathy wiki conversion"
```

Expected: `Initialized empty Git repository...` then commit confirmation.

- [ ] **Step 3: Backup vault**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && cp -r Bryan-Aaron-Master Bryan-Aaron-Master.backup-2026-05-16
```

Expected: silent success. Verify: `ls -d Bryan-Aaron-Master.backup-2026-05-16` exists.

- [ ] **Step 4: Verify backup integrity**

```bash
diff -rq "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master.backup-2026-05-16" | head -5
```

Expected: no output (identical).

- [ ] **Step 5: Commit AIS-OS baseline (preserve user's WIP)**

The user has uncommitted changes to `dashboard/index.html` and `dashboard/scripts/memory_graph.py`. Do NOT commit those — preserve as WIP. Only stash if needed for clean Phase 5.

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git stash push -m "wip-dashboard-before-three-brain-build" dashboard/index.html dashboard/scripts/memory_graph.py
```

Expected: `Saved working directory and index state ...`. WIP recoverable via `git stash pop`.

---

## Task 2: Vault scaffold — raw/ and wiki/ skeleton

**Files:**
- Create: `Bryan-Aaron-Master/raw/.gitkeep`
- Create: `Bryan-Aaron-Master/raw/_ingested/.gitkeep`
- Create: `Bryan-Aaron-Master/wiki/{sources,people,organizations,concepts,analysis,comparisons}/.gitkeep`

- [ ] **Step 1: Create dirs**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && mkdir -p raw/_ingested wiki/{sources,people,organizations,concepts,analysis,comparisons}
```

- [ ] **Step 2: Add .gitkeep to empty dirs**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && touch raw/.gitkeep raw/_ingested/.gitkeep wiki/sources/.gitkeep wiki/people/.gitkeep wiki/organizations/.gitkeep wiki/concepts/.gitkeep wiki/analysis/.gitkeep wiki/comparisons/.gitkeep
```

- [ ] **Step 3: Verify structure**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && find raw wiki -type d
```

Expected output:
```
raw
raw/_ingested
wiki
wiki/sources
wiki/people
wiki/organizations
wiki/concepts
wiki/analysis
wiki/comparisons
```

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git add raw wiki && git commit -m "feat(vault): scaffold Karpathy LLM Wiki dirs (raw, wiki + subdirs)"
```

---

## Task 3: Wiki seed files — index, log, hot

**Files:**
- Create: `Bryan-Aaron-Master/wiki/index.md`
- Create: `Bryan-Aaron-Master/wiki/log.md`
- Create: `Bryan-Aaron-Master/wiki/hot.md`

- [ ] **Step 1: Write `wiki/index.md`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/index.md`

```markdown
# Wiki Index

Updated: 2026-05-16

## Tools

_(populated by ingest)_

## Techniques

_(populated by ingest)_

## Concepts

_(populated by ingest)_

## Sources

_(populated by ingest)_

## People

_(populated by ingest)_

## Organizations

_(populated by ingest)_

## Comparisons

_(populated by ingest)_

## Analysis

_(populated by ingest)_

## Domain Map

- Ag Coach Pro → [[../01-AG-COACH-PRO/]]
- AFL → [[../02-AARON-FAMILY-LIVESTOCK/]]
- Teaching → [[../03-TEACHING/]]
- Finances → [[../04-FINANCES/]]
- Personal → [[../05-PERSONAL/]]
- AI Workflow → [[../06-AI-WORKFLOW/]]
- Resources → [[../07-RESOURCES/]]
```

- [ ] **Step 2: Write `wiki/log.md`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/log.md`

```markdown
# Ingest Log

Append-only history of raw/ → wiki/ ingest operations.

Format per entry:
- Timestamp + source filename
- Type (source/transcript/note/meeting/article)
- Pages created (list)
- Domains linked
- Open questions
- Archive path in raw/_ingested/

---

_(first entry appears after first /ingest run)_
```

- [ ] **Step 3: Write `wiki/hot.md`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/hot.md`

```markdown
# Hot Cache

Updated: 2026-05-16

Vault initialized as Karpathy LLM Wiki. Two YT transcripts queued for first ingest test (Nate Herk Karpathy walkthrough + Jack Roberts CC-OS dashboard). 01-07 domain folders preserved. Bridge declared in AIS-OS/CLAUDE.md.
```

(Max 500 chars — verify length.)

- [ ] **Step 4: Verify hot.md under 500 chars**

```bash
wc -c "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/hot.md"
```

Expected: < 500.

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git add wiki/index.md wiki/log.md wiki/hot.md && git commit -m "feat(vault): seed wiki index/log/hot files"
```

---

## Task 4: Vault CLAUDE.md — append Karpathy schema block

**Files:**
- Modify: `Bryan-Aaron-Master/CLAUDE.md` (append at end)

- [ ] **Step 1: Verify current CLAUDE.md ends cleanly**

```bash
tail -5 "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/CLAUDE.md"
```

Expected: existing content visible. Note where it ends.

- [ ] **Step 2: Append schema block**

Append to `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/CLAUDE.md`:

```markdown

---

## Vault as Karpathy LLM Wiki

This vault uses the Karpathy LLM Wiki pattern + Herk domain folders (K2 hybrid).

### Directory roles

- `raw/` — inbox. Drop sources here. Never edit by hand after ingest.
- `raw/_ingested/` — archive of processed sources. Don't delete.
- `wiki/` — LLM-derived crosslinks layer. Read for queries, write only via `/ingest`.
- `01-07/` — human-curated domain truth. Wiki crosslinks here, never overwrites.

### Ingest rules

1. Read this CLAUDE.md, `wiki/index.md`, `wiki/log.md` (last 10 entries), `Business_Brain.md` before ingest.
2. One wiki page per entity. YAML frontmatter required (`name`, `type`, `tags`, `source_files`, `domains`, `created`, `updated`).
3. Every page ≥1 outbound link. No orphans allowed.
4. Crosslink to 01-07 by relative path: `[[../01-AG-COACH-PRO/Note-Name|Display]]`.
5. Move raw file to `raw/_ingested/YYYY-MM-DD-<name>` after.
6. Update `wiki/index.md` + append `wiki/log.md` + overwrite `wiki/hot.md` each ingest.
7. Wiki pages never duplicate raw verbatim — summary + claims + links only.

### Query rules

- Start at `wiki/index.md` → follow `[[links]]`.
- Read `wiki/hot.md` for recent context cache (<500 chars).
- Don't crawl `raw/` unless wiki insufficient.
- Don't read 01-07 unless wiki points there.

### Failure modes

- Ambiguous classification → ask once, log the answer in `log.md` for similar future files.
- Duplicate entity → merge into existing page, append `source_files`, log the merge.
- No clear domain → tag `domains: [unassigned]`, surface in next `/lint`.
```

Use the Edit tool to append (anchor on the last 2-3 lines of existing CLAUDE.md to make `old_string` unique).

- [ ] **Step 3: Verify append**

```bash
grep -c "Vault as Karpathy LLM Wiki" "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/CLAUDE.md"
```

Expected: `1`.

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git add CLAUDE.md && git commit -m "feat(vault): add Karpathy LLM Wiki schema to CLAUDE.md"
```

---

## Task 5: 00-INBOX migration

**Files:**
- Move: `Bryan-Aaron-Master/00-INBOX/*` → `Bryan-Aaron-Master/raw/`
- Delete: `Bryan-Aaron-Master/00-INBOX/`

- [ ] **Step 1: Inspect 00-INBOX**

```bash
ls -la "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/00-INBOX/" 2>/dev/null
```

Expected: list of files OR `No such file or directory`. If absent, skip Task 5 entirely.

- [ ] **Step 2: Move contents to raw/**

If 00-INBOX has content:

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && find 00-INBOX -mindepth 1 -maxdepth 1 -exec mv -n {} raw/ \;
```

Expected: silent success. Files now in `raw/`.

- [ ] **Step 3: Verify 00-INBOX empty**

```bash
ls -A "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/00-INBOX/"
```

Expected: empty (or only system files like `.DS_Store`).

- [ ] **Step 4: Remove 00-INBOX dir**

```bash
rm -rf "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/00-INBOX"
```

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git add -A && git commit -m "refactor(vault): migrate 00-INBOX contents to raw/, remove 00-INBOX"
```

---

## Task 6: `ingest` skill

**Files:**
- Create: `~/.claude/skills/ingest/SKILL.md`

- [ ] **Step 1: Create skill dir**

```bash
mkdir -p ~/.claude/skills/ingest
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/ingest/SKILL.md`

```markdown
---
name: ingest
description: Ingest files from Bryan-Aaron-Master/raw/ into Karpathy LLM Wiki at Bryan-Aaron-Master/wiki/. Triggers on /ingest, "ingest raw", "process raw", or when files dropped in vault raw/ dir.
---

# Ingest Skill — raw/ → wiki/

Vault: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/`

## Pre-flight reads (in this order)

1. `vault/CLAUDE.md` — vault schema + ingest rules
2. `vault/wiki/index.md` — current TOC
3. `vault/wiki/log.md` — last 10 entries (skip if >100 lines, read last 100)
4. `vault/wiki/hot.md` — recent context
5. `vault/Business_Brain.md` — domain map

## Pipeline

1. **List** new files in `vault/raw/` not yet logged in `wiki/log.md`. Skip files in `raw/_ingested/`.
2. **Classify** each: source | transcript | note | meeting | article | image-OCR. Use filename + first 500 chars.
3. **Ask Bryan** (only first ingest per session, or if classification ambiguous): focus? granularity? domain hint?
4. **Per file, extract entities**: people, organizations, concepts, claims, dates, links. Semantic chunking, no fixed size.
5. **Write wiki pages** — one per entity, in `wiki/<type>/<kebab-slug>.md`. YAML frontmatter required:

```yaml
---
name: <slug>
type: <concept|source|person|organization|analysis|comparison>
tags: [...]
source_files: [...]
domains: [...]              # links to 01-07 dirs or [unassigned]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Body: summary + headers as needed + `## Related` section with `[[wiki-page]]` + `[[../01-DOMAIN/note|Display]]` links.

6. **Enforce no-orphan rule**: every new page MUST have ≥1 outbound `[[link]]`. If isolated, link back to the source page at minimum.
7. **Crosslink to 01-07**: if entity belongs to a domain (e.g. "Greenhand pricing" → 01-AG-COACH-PRO), add link both directions w/o duplicating content.
8. **Update `wiki/index.md`**: append new page links under correct section (Tools | Techniques | Concepts | Sources | People | Organizations | Comparisons | Analysis). Don't rewrite existing entries.
9. **Append `wiki/log.md`** with full entry (see format below).
10. **Overwrite `wiki/hot.md`** with new 500-char summary of just-ingested material. Update `Updated:` line.
11. **Move raw file** → `raw/_ingested/YYYY-MM-DD-<original-name>`.
12. **Report to Bryan**: pages created, domains linked, open questions.

## Log entry format

```markdown
## YYYY-MM-DD HH:MM — <source-filename>

- Type: <type>
- Pages created (N): [[wiki/...]] , [[wiki/...]] , ...
- Domains linked: 01-AG-COACH-PRO, ...
- Open questions: ...
- Moved to: raw/_ingested/YYYY-MM-DD-<filename>
```

## Failure handling

- Ambiguous classification → ask once, log Bryan's answer to use for similar future files.
- Duplicate entity → merge into existing page (append `source_files`, update `updated`, append new claims). Log the merge.
- No clear domain → tag `domains: [unassigned]`. Will surface in next `/lint`.
- Raw file unreadable → leave in raw/, log error, continue with others.

## Constraints

- Wiki never duplicates raw verbatim. Summarize + claims + links.
- Wiki pages live only in `wiki/{sources,people,organizations,concepts,analysis,comparisons}/`. Never write outside wiki/.
- Never modify 01-07 directly. Only crosslink TO them.
- Never overwrite an existing wiki page wholesale — merge.
- Kebab-case filenames. Date in frontmatter, not filename.

## Trigger phrases

`/ingest`, "ingest raw", "process raw", "ingest the new sources", "run wiki ingest"
```

- [ ] **Step 3: Verify skill loads**

```bash
ls -la ~/.claude/skills/ingest/SKILL.md
```

Expected: file exists, readable.

- [ ] **Step 4: Commit (global skills tracked via dotfiles or manual)**

Note: `~/.claude/skills/` may not be git-tracked. If user has a dotfiles repo, commit there; otherwise note the file location and continue.

```bash
ls ~/.claude/.git 2>/dev/null && cd ~/.claude && git add skills/ingest/ && git commit -m "feat(skills): add ingest skill for vault raw→wiki pipeline" || echo "~/.claude not git-tracked; skill saved but not committed"
```

---

## Task 7: `wiki-query` skill

**Files:**
- Create: `~/.claude/skills/wiki-query/SKILL.md`

- [ ] **Step 1: Create skill dir**

```bash
mkdir -p ~/.claude/skills/wiki-query
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/wiki-query/SKILL.md`

```markdown
---
name: wiki-query
description: Query Bryan's Karpathy LLM Wiki by following index → links rather than full-text crawl. Trigger on /wiki <topic>, "what does my wiki say about X", "search vault wiki".
---

# Wiki Query Skill

Vault: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/`

## Query algorithm

1. Read `vault/wiki/hot.md` (cheap, <500 chars).
2. Read `vault/wiki/index.md` — find candidate entries matching topic (substring or semantic).
3. Follow top 3-5 candidate links, read those pages.
4. Follow their `## Related` outbound links one more hop if needed.
5. Synthesize answer from gathered pages. Cite which wiki pages used.
6. If wiki insufficient: ask Bryan whether to crawl `raw/` or check 01-07 directly.

## Do NOT

- Crawl entire `wiki/` dir.
- Read `raw/_ingested/` files.
- Open 01-07 unless a wiki page explicitly linked there.

## Output format

```
**Answer:** <synthesis>

**Sources from wiki:**
- [[wiki/concepts/...]] — <key claim taken from here>
- [[wiki/sources/...]] — <key claim>

**Gaps:** <what wiki doesn't cover, suggest /ingest of source if known>
```

## Trigger phrases

`/wiki <topic>`, "search wiki", "what does the vault say about", "look up in wiki"
```

- [ ] **Step 3: Verify**

```bash
test -f ~/.claude/skills/wiki-query/SKILL.md && echo OK
```

Expected: `OK`.

---

## Task 8: `wiki-lint` skill

**Files:**
- Create: `~/.claude/skills/wiki-lint/SKILL.md`

- [ ] **Step 1: Create skill dir**

```bash
mkdir -p ~/.claude/skills/wiki-lint
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/wiki-lint/SKILL.md`

```markdown
---
name: wiki-lint
description: Run Karpathy-style health checks on vault wiki — orphan pages, stale entries, broken crosslinks, missing frontmatter, unprocessed raw files. Trigger on /lint, "lint vault", "wiki health check".
---

# Wiki Lint Skill

Vault: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/`

## Checks (run all, collect issues)

### 1. Orphan pages
Any wiki page w/ no inbound links from any other wiki page or index.md. Suggest: delete or link.

### 2. Stale pages
Frontmatter `updated:` older than 90 days. List them. Suggest: refresh or archive.

### 3. Broken crosslinks
`[[../01-XYZ/...]]` pointing to nonexistent files. Same for `[[wiki/...]]`. List broken targets.

### 4. Missing frontmatter
Any wiki page missing required fields: `name`, `type`, `tags`, `source_files`, `domains`, `created`, `updated`.

### 5. Unassigned domain
Pages w/ `domains: [unassigned]`. Suggest classification.

### 6. Raw backlog
Files in `raw/` (not `raw/_ingested/`) older than 7 days. Suggest `/ingest`.

### 7. Index drift
Pages in `wiki/<type>/` not listed in `wiki/index.md`. Or links in `wiki/index.md` pointing to deleted pages.

### 8. Oversized pages
Wiki pages > 2000 words. Suggest split.

## Output

Write to: `/Volumes/Samsung PSSD T7/AIS-OS/dashboard/lint-report.md`

Format:
```markdown
# Vault Lint Report

Date: YYYY-MM-DD
Issues: <total>

## Orphans (N)
- [[wiki/...]] — no inbound links

## Stale (N)
- [[wiki/...]] — updated YYYY-MM-DD (X days ago)

## Broken (N)
- [[wiki/.../page]] → links to [[missing-target]]

## Missing frontmatter (N)
- wiki/.../page.md — missing: [tags, domains]

## Unassigned domain (N)
- [[wiki/...]]

## Raw backlog (N)
- raw/file.md — N days old

## Index drift (N)
- wiki/sources/X.md exists but not in index
- index links to wiki/people/Y.md which doesn't exist

## Oversized (N)
- [[wiki/...]] — 2400 words
```

Also print summary to terminal: total issues by category.

## Do NOT auto-fix

Lint reports only. Bryan reviews + fixes manually or via prompt.

## Trigger phrases

`/lint`, "lint vault", "wiki health check", "find orphans"
```

- [ ] **Step 3: Verify**

```bash
test -f ~/.claude/skills/wiki-lint/SKILL.md && echo OK
```

---

## Task 9: `dream` skill

**Files:**
- Create: `~/.claude/skills/dream/SKILL.md`

- [ ] **Step 1: Create dir**

```bash
mkdir -p ~/.claude/skills/dream
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/dream/SKILL.md`

```markdown
---
name: dream
description: Run 8-dimension dream pass over Bryan's AI stack — surfaces ≤4 high-leverage recommendations as JSON cards. Trigger on /dream, "run dreaming", "nightly dream", or by cron.
---

# Dream Skill — 8-dim nightly engine

## Execute

Run: `python3 /Volumes/Samsung\ PSSD\ T7/AIS-OS/scripts/dream.py`

Script handles all 8 dimensions, calls Claude API, writes JSON to `dashboard/data/dreams/YYYY-MM-DD.json`.

## 8 dimensions

| # | Dim | Source | Looks for |
|---|---|---|---|
| 1 | conversation | last 7d Claude Code transcripts (`~/.claude/projects/*/conversations/`) | tasks done manually 3+ times → skill candidate |
| 2 | cost | model call logs | Opus on Haiku-tier work, low cache hit |
| 3 | skill-perf | `~/.claude/skills/` + AIS-OS skills usage | stale skills, high-ROI, gaps |
| 4 | memory-health | vault wiki + Pinecone | orphans, stale, missing crosslinks |
| 5 | session-hygiene | token usage / session | bloat, when limits hit |
| 6 | workflow | git log + file changes across projects | duplicated work |
| 7 | external-opps | web search (consent required, once at onboard) | new tools/skills fitting stack |
| 8 | business-context | `vault/Business_Brain.md` + wiki | progress vs 50-schools/$120K goal |

## Output

`/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/dreams/YYYY-MM-DD.json`

Schema enforced by `scripts/dream.py`. Max 4 cards.

## Constraints

- Never auto-execute card actions. Bryan reviews + executes manually.
- Cap output: 4 cards per night.
- If <4 high-leverage findings, emit fewer. Don't pad.

## Trigger phrases

`/dream`, "run dream engine", "nightly pass", "what should I work on"
```

- [ ] **Step 3: Verify**

```bash
test -f ~/.claude/skills/dream/SKILL.md && echo OK
```

---

## Task 10: `hot-update` skill

**Files:**
- Create: `~/.claude/skills/hot-update/SKILL.md`

- [ ] **Step 1: Create dir**

```bash
mkdir -p ~/.claude/skills/hot-update
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/hot-update/SKILL.md`

```markdown
---
name: hot-update
description: Refresh Bryan-Aaron-Master/wiki/hot.md with up-to-500-char summary of most recent ingest activity or session context. Trigger on /hot, "update hot cache", "refresh hot.md".
---

# Hot Cache Update Skill

Path: `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/hot.md`

## Logic

1. Read last entry in `vault/wiki/log.md`.
2. Read current `vault/wiki/hot.md`.
3. Compose new 500-char-max summary covering most recent ingest(s) or top-of-mind context (whichever applies).
4. Overwrite hot.md with:

```markdown
# Hot Cache

Updated: YYYY-MM-DD HH:MM

<new summary, ≤500 chars body>
```

5. Verify final body section is ≤500 chars (`wc -c` on body).

## Constraint

Body MUST be ≤500 characters. If draft exceeds, compress until under.

## Trigger phrases

`/hot`, "refresh hot.md", "update hot cache"
```

- [ ] **Step 3: Verify**

```bash
test -f ~/.claude/skills/hot-update/SKILL.md && echo OK
```

---

## Task 11: `skill-suggest` skill

**Files:**
- Create: `~/.claude/skills/skill-suggest/SKILL.md`

- [ ] **Step 1: Create dir**

```bash
mkdir -p ~/.claude/skills/skill-suggest
```

- [ ] **Step 2: Write SKILL.md**

Path: `~/.claude/skills/skill-suggest/SKILL.md`

```markdown
---
name: skill-suggest
description: Detect repeated manual workflows in recent Claude conversations and propose new skill drafts. Invoked automatically by dream dim 1 or manually via /skill-suggest.
---

# Skill Suggest

## Input

- Recent (7d) Claude Code conversation logs from `~/.claude/projects/*/conversations/` OR explicit list of recent tasks Bryan did.

## Logic

1. Cluster tasks by intent (regex + topic).
2. Flag any intent done ≥3 times in 7 days.
3. For each flagged intent, draft a skill candidate:

```markdown
## Candidate: <skill-name>

**Intent:** <what Bryan did manually 3+ times>
**Frequency:** <N times in 7 days>
**Est. time saved per run:** <minutes>
**Skill draft:**

\`\`\`
---
name: <slug>
description: <one-line trigger>
---

# <Skill Name>

<3-5 line procedure>
\`\`\`

**Trigger phrases:** /...
```

4. Output up to 3 candidates. Surface to Bryan for approval (don't create the skill files automatically).

## Output

Write to: `/Volumes/Samsung PSSD T7/AIS-OS/dashboard/skill-suggestions.md` (overwrite each run).

## Trigger phrases

`/skill-suggest`, "what should be a skill", "find repeated work"
```

- [ ] **Step 3: Verify all 6 new skills present**

```bash
ls ~/.claude/skills/ | grep -E '^(ingest|wiki-query|wiki-lint|dream|hot-update|skill-suggest)$' | wc -l
```

Expected: `6`.

---

## Task 12: AIS-OS scripts dir + requirements

**Files:**
- Create: `AIS-OS/scripts/__init__.py`
- Create: `AIS-OS/requirements.txt`

- [ ] **Step 1: Create scripts dir**

```bash
mkdir -p "/Volumes/Samsung PSSD T7/AIS-OS/scripts"
touch "/Volumes/Samsung PSSD T7/AIS-OS/scripts/__init__.py"
```

- [ ] **Step 2: Write requirements.txt**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/requirements.txt`

```
anthropic>=0.40.0
python-frontmatter>=1.1.0
pytest>=8.0.0
```

- [ ] **Step 3: Install**

```bash
pip3 install -r "/Volumes/Samsung PSSD T7/AIS-OS/requirements.txt" --break-system-packages --quiet
```

Expected: silent success.

- [ ] **Step 4: Verify**

```bash
python3 -c "import anthropic, frontmatter, pytest; print('ok')"
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add scripts/ requirements.txt && git commit -m "chore(scripts): scaffold scripts dir + requirements.txt"
```

---

## Task 13: `lint.py` — TDD (test first)

**Files:**
- Create: `AIS-OS/scripts/test_lint.py`
- Create: `AIS-OS/scripts/lint.py`

- [ ] **Step 1: Write failing test**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/scripts/test_lint.py`

```python
"""Tests for vault lint script."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from scripts.lint import (
    find_orphans,
    find_stale,
    find_broken_links,
    find_missing_frontmatter,
    find_raw_backlog,
    lint_vault,
)


def _setup_vault(tmp: Path) -> Path:
    """Build minimal vault fixture."""
    (tmp / "raw").mkdir()
    (tmp / "raw" / "_ingested").mkdir()
    (tmp / "wiki").mkdir()
    for sub in ["sources", "people", "concepts"]:
        (tmp / "wiki" / sub).mkdir()
    (tmp / "wiki" / "index.md").write_text(
        "# Wiki Index\n\n- [[concepts/connected]]\n"
    )
    (tmp / "wiki" / "log.md").write_text("# Log\n")
    (tmp / "wiki" / "hot.md").write_text("# Hot\n")
    return tmp


def test_find_orphans_detects_unlinked_page(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "connected.md").write_text(
        "---\nname: connected\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Connected\n[[orphan]]\n"
    )
    (vault / "wiki" / "concepts" / "orphan.md").write_text(
        "---\nname: orphan\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Orphan\nno links out\n"
    )
    orphans = find_orphans(vault)
    # orphan has inbound link from connected. connected has none → connected is orphan.
    assert any("connected.md" in str(o) for o in orphans)


def test_find_stale_flags_old_updated(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "old.md").write_text(
        "---\nname: old\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2025-01-01\nupdated: 2025-01-01\n---\n# Old\n"
    )
    stale = find_stale(vault, days=90, today="2026-05-16")
    assert len(stale) == 1
    assert "old.md" in str(stale[0])


def test_find_broken_links_detects_missing_target(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "src.md").write_text(
        "---\nname: src\ntype: concept\ntags: []\nsource_files: []\ndomains: []\ncreated: 2026-05-16\nupdated: 2026-05-16\n---\n# Src\n[[missing-target]]\n"
    )
    broken = find_broken_links(vault)
    assert any("missing-target" in b["target"] for b in broken)


def test_find_missing_frontmatter(tmp_path):
    vault = _setup_vault(tmp_path)
    (vault / "wiki" / "concepts" / "bad.md").write_text("# Bad\nno frontmatter\n")
    missing = find_missing_frontmatter(vault)
    assert any("bad.md" in str(m["path"]) for m in missing)


def test_find_raw_backlog_old_files(tmp_path):
    vault = _setup_vault(tmp_path)
    old_file = vault / "raw" / "old.md"
    old_file.write_text("old")
    # Backdate mtime: 10 days ago
    import time
    ten_days_ago = time.time() - 10 * 86400
    os.utime(old_file, (ten_days_ago, ten_days_ago))
    backlog = find_raw_backlog(vault, max_age_days=7)
    assert any("old.md" in str(b["path"]) for b in backlog)


def test_lint_vault_returns_full_report(tmp_path):
    vault = _setup_vault(tmp_path)
    report = lint_vault(vault, today="2026-05-16")
    assert "orphans" in report
    assert "stale" in report
    assert "broken_links" in report
    assert "missing_frontmatter" in report
    assert "raw_backlog" in report
    assert "total_issues" in report
```

- [ ] **Step 2: Run test, verify all fail**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 -m pytest scripts/test_lint.py -v 2>&1 | tail -20
```

Expected: `ModuleNotFoundError: No module named 'scripts.lint'` or similar. All 6 tests fail.

- [ ] **Step 3: Write `lint.py`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/scripts/lint.py`

```python
"""Vault health checks. Reports issues; does not auto-fix."""
from __future__ import annotations

import argparse
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import frontmatter

REQUIRED_FRONTMATTER_FIELDS = {
    "name",
    "type",
    "tags",
    "source_files",
    "domains",
    "created",
    "updated",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _wiki_pages(vault: Path) -> list[Path]:
    return sorted(
        p
        for p in (vault / "wiki").rglob("*.md")
        if p.name not in {"index.md", "log.md", "hot.md"}
    )


def _wikilinks_in(text: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def find_orphans(vault: Path) -> list[Path]:
    """Pages with zero inbound links."""
    pages = _wiki_pages(vault)
    inbound: dict[str, int] = {p.stem: 0 for p in pages}
    sources = pages + [vault / "wiki" / "index.md"]
    for src in sources:
        if not src.exists():
            continue
        for link in _wikilinks_in(src.read_text()):
            tail = link.split("/")[-1]
            if tail in inbound and src.stem != tail:
                inbound[tail] += 1
    return [p for p in pages if inbound[p.stem] == 0]


def find_stale(vault: Path, days: int = 90, today: str | None = None) -> list[Path]:
    today_d = date.fromisoformat(today) if today else date.today()
    stale: list[Path] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            continue
        updated = fm.get("updated")
        if isinstance(updated, date):
            updated_d = updated
        elif isinstance(updated, str):
            try:
                updated_d = date.fromisoformat(updated)
            except ValueError:
                continue
        else:
            continue
        if (today_d - updated_d).days > days:
            stale.append(p)
    return stale


def find_broken_links(vault: Path) -> list[dict]:
    pages = _wiki_pages(vault)
    page_stems = {p.stem for p in pages}
    broken: list[dict] = []
    for p in pages:
        for link in _wikilinks_in(p.read_text()):
            target = link.strip()
            if target.startswith("../"):
                resolved = (p.parent / target).resolve()
                if not resolved.exists() and not (resolved.parent / f"{resolved.name}.md").exists():
                    broken.append({"page": str(p), "target": target})
            else:
                tail = target.split("/")[-1].replace(".md", "")
                if tail not in page_stems and target not in {"index", "log", "hot"}:
                    broken.append({"page": str(p), "target": target})
    return broken


def find_missing_frontmatter(vault: Path) -> list[dict]:
    out: list[dict] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            out.append({"path": str(p), "missing": list(REQUIRED_FRONTMATTER_FIELDS)})
            continue
        present = set(fm.metadata.keys())
        missing = REQUIRED_FRONTMATTER_FIELDS - present
        if missing:
            out.append({"path": str(p), "missing": sorted(missing)})
    return out


def find_raw_backlog(vault: Path, max_age_days: int = 7) -> list[dict]:
    raw_dir = vault / "raw"
    if not raw_dir.exists():
        return []
    now = datetime.now().timestamp()
    cutoff = now - max_age_days * 86400
    backlog: list[dict] = []
    for p in raw_dir.iterdir():
        if p.is_dir():
            continue
        if p.name.startswith(".") or p.name == ".gitkeep":
            continue
        if p.stat().st_mtime < cutoff:
            age_days = int((now - p.stat().st_mtime) / 86400)
            backlog.append({"path": str(p), "age_days": age_days})
    return backlog


def find_unassigned_domain(vault: Path) -> list[Path]:
    out: list[Path] = []
    for p in _wiki_pages(vault):
        try:
            fm = frontmatter.load(p)
        except Exception:
            continue
        if "unassigned" in (fm.get("domains") or []):
            out.append(p)
    return out


def lint_vault(vault: Path, today: str | None = None) -> dict:
    report = {
        "orphans": [str(p) for p in find_orphans(vault)],
        "stale": [str(p) for p in find_stale(vault, today=today)],
        "broken_links": find_broken_links(vault),
        "missing_frontmatter": find_missing_frontmatter(vault),
        "raw_backlog": find_raw_backlog(vault),
        "unassigned_domain": [str(p) for p in find_unassigned_domain(vault)],
    }
    report["total_issues"] = sum(
        len(v) if isinstance(v, list) else 0 for v in report.values()
    )
    return report


def format_report(report: dict, today: str) -> str:
    lines = [f"# Vault Lint Report\n\nDate: {today}\nIssues: {report['total_issues']}\n"]
    for key, label in [
        ("orphans", "Orphans"),
        ("stale", "Stale"),
        ("broken_links", "Broken links"),
        ("missing_frontmatter", "Missing frontmatter"),
        ("raw_backlog", "Raw backlog"),
        ("unassigned_domain", "Unassigned domain"),
    ]:
        items = report[key]
        lines.append(f"\n## {label} ({len(items)})\n")
        for item in items:
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vault",
        default="/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master",
    )
    parser.add_argument(
        "--out",
        default="/Volumes/Samsung PSSD T7/AIS-OS/dashboard/lint-report.md",
    )
    args = parser.parse_args()
    vault = Path(args.vault)
    today = date.today().isoformat()
    report = lint_vault(vault, today=today)
    Path(args.out).write_text(format_report(report, today))
    print(f"Lint complete. {report['total_issues']} issues. Report: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 -m pytest scripts/test_lint.py -v 2>&1 | tail -20
```

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add scripts/lint.py scripts/test_lint.py && git commit -m "feat(scripts): add lint.py for vault health checks (TDD)"
```

---

## Task 14: `dream.py` — TDD (test the schema + structure)

**Files:**
- Create: `AIS-OS/scripts/test_dream.py`
- Create: `AIS-OS/scripts/dream.py`

- [ ] **Step 1: Write failing tests**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/scripts/test_dream.py`

```python
"""Tests for dream engine. Mocks Claude API to verify card structure."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.dream import (
    Card,
    DreamConfig,
    build_card_json,
    validate_cards,
    write_dream_output,
)


def test_card_dataclass_required_fields():
    c = Card(
        id="d1",
        dim="skill-perf",
        title="t",
        insight="i",
        action="a",
        estimated_value_minutes=30,
        status="open",
    )
    assert c.id == "d1"
    assert c.estimated_value_minutes == 30


def test_validate_cards_rejects_more_than_four():
    cards = [
        Card(id=f"d{i}", dim="x", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")
        for i in range(5)
    ]
    with pytest.raises(ValueError, match="max 4 cards"):
        validate_cards(cards)


def test_validate_cards_accepts_four():
    cards = [
        Card(id=f"d{i}", dim="x", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")
        for i in range(4)
    ]
    validate_cards(cards)  # no raise


def test_validate_cards_accepts_zero():
    validate_cards([])


def test_build_card_json_round_trip():
    cards = [
        Card(id="d1", dim="cost", title="t", insight="i", action="a", estimated_value_minutes=45, status="open")
    ]
    payload = build_card_json(cards, summary="s", date="2026-05-16", next_run="2026-05-17T02:00:00")
    parsed = json.loads(payload)
    assert parsed["date"] == "2026-05-16"
    assert len(parsed["cards"]) == 1
    assert parsed["cards"][0]["estimated_value_minutes"] == 45


def test_write_dream_output(tmp_path):
    out_dir = tmp_path / "dreams"
    out_dir.mkdir()
    cards = [Card(id="d1", dim="x", title="t", insight="i", action="a", estimated_value_minutes=10, status="open")]
    path = write_dream_output(cards, out_dir=out_dir, summary="s", date="2026-05-16", next_run="2026-05-17T02:00:00")
    assert path.exists()
    data = json.loads(path.read_text())
    assert data["summary"] == "s"
    assert len(data["cards"]) == 1


def test_dream_config_defaults():
    cfg = DreamConfig()
    assert cfg.max_cards == 4
    assert cfg.lookback_days == 7
```

- [ ] **Step 2: Run tests, verify fail**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 -m pytest scripts/test_dream.py -v 2>&1 | tail -10
```

Expected: `ModuleNotFoundError` for `scripts.dream`. All tests fail.

- [ ] **Step 3: Write `dream.py`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/scripts/dream.py`

```python
"""Dream engine — 8-dim nightly pass over Bryan's AI stack."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore


VAULT_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")
AISOS_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS")
DREAMS_DIR_DEFAULT = AISOS_DEFAULT / "dashboard" / "data" / "dreams"

DIMENSIONS = [
    "conversation",
    "cost",
    "skill-perf",
    "memory-health",
    "session-hygiene",
    "workflow",
    "external-opps",
    "business-context",
]


@dataclass
class Card:
    id: str
    dim: str
    title: str
    insight: str
    action: str
    estimated_value_minutes: int
    status: str  # open | done | dismissed


@dataclass
class DreamConfig:
    max_cards: int = 4
    lookback_days: int = 7
    model: str = "claude-opus-4-7"
    vault: Path = VAULT_DEFAULT
    aisos: Path = AISOS_DEFAULT
    dreams_dir: Path = DREAMS_DIR_DEFAULT


def validate_cards(cards: list[Card]) -> None:
    if len(cards) > 4:
        raise ValueError("max 4 cards")
    seen_ids: set[str] = set()
    for c in cards:
        if c.id in seen_ids:
            raise ValueError(f"duplicate card id: {c.id}")
        seen_ids.add(c.id)
        if c.dim not in DIMENSIONS:
            raise ValueError(f"invalid dim: {c.dim}")
        if c.status not in {"open", "done", "dismissed"}:
            raise ValueError(f"invalid status: {c.status}")


def build_card_json(
    cards: list[Card], summary: str, date: str, next_run: str
) -> str:
    payload = {
        "date": date,
        "cards": [asdict(c) for c in cards],
        "summary": summary,
        "next_run": next_run,
    }
    return json.dumps(payload, indent=2)


def write_dream_output(
    cards: list[Card],
    out_dir: Path,
    summary: str,
    date: str,
    next_run: str,
) -> Path:
    validate_cards(cards)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date}.json"
    path.write_text(build_card_json(cards, summary, date, next_run))
    return path


def gather_context(cfg: DreamConfig) -> dict[str, str]:
    """Collect compact context for each dim. Read sparingly — keep token cost low."""
    ctx: dict[str, str] = {}
    # Vault: hot + last 20 lines of log
    hot = cfg.vault / "wiki" / "hot.md"
    log = cfg.vault / "wiki" / "log.md"
    ctx["vault_hot"] = hot.read_text()[:600] if hot.exists() else ""
    ctx["vault_log_tail"] = (
        "\n".join(log.read_text().splitlines()[-20:]) if log.exists() else ""
    )
    # Business brain
    bb = cfg.vault / "Business_Brain.md"
    ctx["business_brain"] = bb.read_text()[:2000] if bb.exists() else ""
    # Recent git activity in AIS-OS
    try:
        import subprocess

        ctx["git_recent"] = subprocess.check_output(
            ["git", "log", "--oneline", "-20"], cwd=cfg.aisos, text=True
        )
    except Exception:
        ctx["git_recent"] = ""
    # Skills inventory
    skills_dir = Path.home() / ".claude" / "skills"
    if skills_dir.exists():
        ctx["skills_list"] = "\n".join(sorted(p.name for p in skills_dir.iterdir() if p.is_dir()))
    else:
        ctx["skills_list"] = ""
    return ctx


def build_prompt(ctx: dict[str, str], cfg: DreamConfig) -> str:
    today = date.today().isoformat()
    return f"""You are Bryan's nightly dream engine. Today is {today}. Generate up to {cfg.max_cards} high-leverage recommendations across the 8 dimensions: {", ".join(DIMENSIONS)}.

CONTEXT:

[vault_hot]
{ctx['vault_hot']}

[vault_log_tail]
{ctx['vault_log_tail']}

[business_brain (truncated)]
{ctx['business_brain']}

[git_recent]
{ctx['git_recent']}

[skills_installed]
{ctx['skills_list']}

REQUIREMENTS:
- Max {cfg.max_cards} cards. Fewer is fine if leverage isn't there. Don't pad.
- Each card MUST be specific + actionable + tied to Bryan's Q-goals (50 schools by Aug 2026, $120K/yr, Ag Coach Pro focus).
- Each card has: id (d1..d{cfg.max_cards}), dim (one of {DIMENSIONS}), title (≤80 chars), insight (1-2 sentences), action (imperative, ≤120 chars), estimated_value_minutes (int).
- Output ONLY valid JSON matching this schema:

{{
  "summary": "1-line dream summary",
  "cards": [
    {{"id": "d1", "dim": "skill-perf", "title": "...", "insight": "...", "action": "...", "estimated_value_minutes": 45}}
  ]
}}
"""


def call_claude(prompt: str, cfg: DreamConfig) -> dict:
    if Anthropic is None:
        raise RuntimeError("anthropic SDK not installed. pip install anthropic")
    client = Anthropic()
    msg = client.messages.create(
        model=cfg.model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text
    # Strip code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default=str(VAULT_DEFAULT))
    parser.add_argument("--out-dir", default=str(DREAMS_DIR_DEFAULT))
    parser.add_argument("--dry-run", action="store_true", help="Skip Claude API call; emit empty card set.")
    args = parser.parse_args()

    cfg = DreamConfig(vault=Path(args.vault), dreams_dir=Path(args.out_dir))
    ctx = gather_context(cfg)
    today = date.today().isoformat()
    next_run = (datetime.now() + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0).isoformat()

    if args.dry_run:
        cards: list[Card] = []
        summary = "Dry-run dream pass — no cards generated."
    else:
        prompt = build_prompt(ctx, cfg)
        result = call_claude(prompt, cfg)
        cards = [Card(status="open", **c) for c in result.get("cards", [])]
        summary = result.get("summary", "")

    path = write_dream_output(cards, cfg.dreams_dir, summary, today, next_run)
    print(f"Dream pass complete. Cards: {len(cards)}. Output: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, verify pass**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 -m pytest scripts/test_dream.py -v 2>&1 | tail -15
```

Expected: 7 passed.

- [ ] **Step 5: Smoke test with --dry-run (no API call)**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 scripts/dream.py --dry-run
```

Expected: `Dream pass complete. Cards: 0. Output: .../dashboard/data/dreams/YYYY-MM-DD.json`

- [ ] **Step 6: Verify output file**

```bash
cat "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/data/dreams/$(date +%Y-%m-%d).json" | python3 -m json.tool | head -10
```

Expected: valid JSON with `cards: []`, `summary`, `date`, `next_run`.

- [ ] **Step 7: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add scripts/dream.py scripts/test_dream.py && git commit -m "feat(scripts): add dream.py 8-dim engine (TDD)"
```

---

## Task 15: `ingest.py` CLI wrapper (optional, thin)

**Files:**
- Create: `AIS-OS/scripts/ingest.py`

The skill in Task 6 does the real work. This wrapper is for cron/CLI use.

- [ ] **Step 1: Write `ingest.py`**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/scripts/ingest.py`

```python
"""CLI wrapper for ingest skill. Lists raw/ files; actual ingest happens via Claude Code skill."""
from __future__ import annotations

import argparse
from pathlib import Path

VAULT_DEFAULT = Path("/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master")


def list_raw(vault: Path) -> list[Path]:
    raw = vault / "raw"
    if not raw.exists():
        return []
    out: list[Path] = []
    for p in raw.iterdir():
        if p.is_dir():
            continue
        if p.name.startswith(".") or p.name == ".gitkeep":
            continue
        out.append(p)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="List pending raw files for ingest.")
    parser.add_argument("--vault", default=str(VAULT_DEFAULT))
    args = parser.parse_args()
    pending = list_raw(Path(args.vault))
    if not pending:
        print("No pending files in raw/. Nothing to ingest.")
        return 0
    print(f"{len(pending)} files pending in raw/:")
    for p in pending:
        print(f"  - {p.name}")
    print("\nTo ingest, run `/ingest` in Claude Code (vault working dir).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Smoke test**

```bash
python3 "/Volumes/Samsung PSSD T7/AIS-OS/scripts/ingest.py"
```

Expected: `No pending files in raw/. Nothing to ingest.` (raw/ is empty pre-Task 16).

- [ ] **Step 3: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add scripts/ingest.py && git commit -m "feat(scripts): add ingest.py CLI wrapper"
```

---

## Task 16: First real ingest test — YT transcripts

**Files:**
- Move: `/tmp/yt_sboNwYmH3AY.txt` → `vault/raw/nate-herk-karpathy-walkthrough.txt`
- Move: `/tmp/yt_MAuLQzcMrS0.txt` → `vault/raw/jack-roberts-cc-os.txt`
- Run: `/ingest` (skill)

This task validates the full pipeline end-to-end. Execute INTERACTIVELY in Claude Code (skill needs LLM execution, not scripted).

- [ ] **Step 1: Verify transcripts still present in /tmp**

```bash
ls -la /tmp/yt_sboNwYmH3AY.txt /tmp/yt_MAuLQzcMrS0.txt
```

Expected: both files exist (~22k + ~19k chars).

- [ ] **Step 2: Copy into vault raw/**

```bash
cp /tmp/yt_sboNwYmH3AY.txt "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/raw/nate-herk-karpathy-walkthrough.txt"
cp /tmp/yt_MAuLQzcMrS0.txt "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/raw/jack-roberts-cc-os.txt"
```

- [ ] **Step 3: Verify wrapper sees pending**

```bash
python3 "/Volumes/Samsung PSSD T7/AIS-OS/scripts/ingest.py"
```

Expected: lists 2 files pending.

- [ ] **Step 4: Run `/ingest` in Claude Code from vault working dir**

In Claude Code session, with cwd = `Bryan-Aaron-Master`, invoke:

```
/ingest
```

The `ingest` skill (Task 6) executes the pipeline. Expected outputs:
- 8-15 new wiki pages across `wiki/{sources,people,concepts,comparisons}/`
- `wiki/index.md` updated with new entries
- `wiki/log.md` has new section dated today
- `wiki/hot.md` overwritten w/ summary of these two transcripts
- Both files moved to `raw/_ingested/2026-05-16-nate-herk-karpathy-walkthrough.txt` and `raw/_ingested/2026-05-16-jack-roberts-cc-os.txt`

- [ ] **Step 5: Verify wiki pages created**

```bash
find "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki" -name "*.md" -newer "/tmp/yt_sboNwYmH3AY.txt" | grep -v "^/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/\(index\|log\|hot\)" | wc -l
```

Expected: ≥6.

- [ ] **Step 6: Verify log entry**

```bash
grep -c "nate-herk-karpathy-walkthrough" "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/wiki/log.md"
```

Expected: ≥1.

- [ ] **Step 7: Verify raw files moved**

```bash
ls "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/raw/_ingested/" | grep -c -E 'nate-herk|jack-roberts'
```

Expected: `2`.

- [ ] **Step 8: Run lint, expect low issue count**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 scripts/lint.py
```

Expected: report written, total_issues likely <5 (some orphans on fresh wiki normal).

- [ ] **Step 9: Commit vault**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master" && git add -A && git commit -m "feat(vault): first ingest — Nate Herk + Jack Roberts transcripts"
```

---

## Task 17: AIS-OS CLAUDE.md — vault bridge block

**Files:**
- Modify: `AIS-OS/CLAUDE.md` (append)

- [ ] **Step 1: Locate insertion point**

```bash
tail -10 "/Volumes/Samsung PSSD T7/AIS-OS/CLAUDE.md"
```

Note last 2-3 lines for Edit tool anchor.

- [ ] **Step 2: Append vault bridge block**

Use Edit tool on `/Volumes/Samsung PSSD T7/AIS-OS/CLAUDE.md`. Append at end:

```markdown

---

## Vault bridge (Roberts OS ↔ Karpathy wiki)

- `vault_root`: `./Bryan-Aaron-Master/`
- `wiki_path`: `./Bryan-Aaron-Master/wiki/`
- `raw_path`: `./Bryan-Aaron-Master/raw/`

### Read protocol

1. Domain knowledge queries → read `wiki/index.md` → follow `[[links]]`. See `wiki-query` skill.
2. Recent context → read `wiki/hot.md` (≤500 chars).
3. Don't crawl `raw/` or `01-07/` unless wiki insufficient.

### Write protocol

- Dashboard reads `wiki/{index,log,hot}.md` — NEVER writes.
- Dream engine writes `dashboard/data/dreams/YYYY-MM-DD.json` — may suggest vault changes, never executes them.
- Ingest skill writes to `wiki/` only. Never modifies `01-07/`.
- AIS-OS scripts treat `01-07/` as read-only authoritative truth.

### Slash commands

- `/ingest` — raw → wiki (run inside vault working dir)
- `/wiki <topic>` — query wiki
- `/lint` — vault health
- `/dream` — manual dream pass
- `/hot` — refresh hot cache
```

- [ ] **Step 3: Verify**

```bash
grep -c "Vault bridge" "/Volumes/Samsung PSSD T7/AIS-OS/CLAUDE.md"
```

Expected: `1`.

- [ ] **Step 4: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add CLAUDE.md && git commit -m "feat(claude-md): declare vault bridge (paths, read/write protocol, slash commands)"
```

---

## Task 18: Global `~/.claude/CLAUDE.md` — vault pointer

**Files:**
- Modify: `~/.claude/CLAUDE.md` (append)

- [ ] **Step 1: Inspect tail**

```bash
tail -10 ~/.claude/CLAUDE.md
```

- [ ] **Step 2: Append vault pointer block**

Use Edit tool on `~/.claude/CLAUDE.md`. Append:

```markdown

## Bryan-Aaron-Master vault (Karpathy LLM Wiki)

Vault at `/Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/`.

### Session start read order (extended)

1. `gravity-claw/memory/00_Core/MEMORY.md`
2. `gravity-claw/memory/01_Bryan/bryan.md`
3. `Bryan-Aaron-Master/wiki/hot.md` ← NEW (Karpathy wiki hot cache)
4. `Bryan-Aaron-Master/wiki/index.md` ← NEW (skim only)
5. Project `CLAUDE.md`

### Query routing (three-layer protocol, updated)

1. Vault wiki (Karpathy LLM Wiki) — primary for domain knowledge
2. Graphify graph.json — codebase structure (if graphify output exists)
3. Gravity Claw vault — decisions, session logs
4. Pinecone (`python3 ~/.claude/pinecone_memory.py query`) — semantic recall across sessions
5. Raw code / raw vault files — only when 1-4 insufficient

For vault queries specifically, use `wiki-query` skill or invoke `/wiki <topic>`.
```

- [ ] **Step 3: Verify**

```bash
grep -c "Bryan-Aaron-Master vault (Karpathy LLM Wiki)" ~/.claude/CLAUDE.md
```

Expected: `1`.

---

## Task 19: Dashboard `config.json`

**Files:**
- Create: `AIS-OS/dashboard/config.json`

- [ ] **Step 1: Write config.json**

Path: `/Volumes/Samsung PSSD T7/AIS-OS/dashboard/config.json`

```json
{
  "hourly_value_usd": 150,
  "vault_path": "../Bryan-Aaron-Master",
  "wiki_path": "../Bryan-Aaron-Master/wiki",
  "dreams_dir": "./data/dreams",
  "skills_global": "~/.claude/skills",
  "skills_project": "../.claude/skills",
  "lint_report": "./lint-report.md",
  "skill_suggestions": "./skill-suggestions.md",
  "subscriptions": [
    {"name": "Claude Pro Max", "monthly_usd": 200, "model": "claude"},
    {"name": "ChatGPT Pro", "monthly_usd": 200, "model": "openai"},
    {"name": "Gemini Advanced", "monthly_usd": 20, "model": "gemini"}
  ],
  "dream_cron": "0 2 * * *"
}
```

NOTE: `hourly_value_usd` is a placeholder. Ask Bryan to set his actual value after this task.

- [ ] **Step 2: Verify JSON**

```bash
python3 -m json.tool "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/config.json" > /dev/null && echo OK
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add dashboard/config.json && git commit -m "feat(dashboard): add config.json (hourly_value, paths, subs, cron)"
```

---

## Task 20: Restore user's dashboard WIP + extend with Knowledge/Hot/Dreams cards

**Files:**
- Modify: `AIS-OS/dashboard/index.html`
- Modify: `AIS-OS/dashboard/scripts/memory_graph.py`

User's prior WIP was stashed in Task 1, Step 5. Restore first.

- [ ] **Step 1: Restore stash**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git stash list | grep wip-dashboard
```

If listed:

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git stash pop
```

Expected: WIP restored. `dashboard/index.html` + `memory_graph.py` show as modified.

- [ ] **Step 2: Read current index.html structure**

```bash
wc -l "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/index.html"
grep -n "<section\|<div class=\"card" "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/index.html" | head -30
```

Identify where existing cards are defined. Plan card insertion AFTER existing structure, BEFORE closing `</main>` or equivalent.

- [ ] **Step 3: Add Knowledge card, Hot tile, Dreams card**

Use Edit tool on `dashboard/index.html`. Locate the existing cards section (use a unique nearby element as anchor). Append three new cards. Exact HTML depends on existing styling — match the existing pattern. Template:

```html
<section class="card" id="card-knowledge">
  <h2>Knowledge (Vault Wiki)</h2>
  <ul id="knowledge-stats">
    <li>Pages: <span id="wiki-page-count">—</span></li>
    <li>Last ingest: <span id="wiki-last-ingest">—</span></li>
    <li>Orphans: <span id="wiki-orphans">—</span></li>
  </ul>
  <a href="../Bryan-Aaron-Master/wiki/index.md" target="_blank">Open wiki index →</a>
</section>

<section class="card" id="card-hot">
  <h2>Hot Cache</h2>
  <pre id="hot-cache-preview">loading…</pre>
</section>

<section class="card" id="card-dreams">
  <h2>Tonight's Dreams</h2>
  <ol id="dream-cards"><li>loading…</li></ol>
  <small>Updated: <span id="dream-date">—</span></small>
</section>
```

Add JS at end of `<body>` (before closing tag) to populate. Match existing JS style:

```html
<script>
(async function loadVaultCards() {
  try {
    const idx = await fetch('../Bryan-Aaron-Master/wiki/index.md').then(r => r.text());
    const pageCount = (idx.match(/\[\[/g) || []).length;
    document.getElementById('wiki-page-count').textContent = pageCount;
  } catch (e) {}

  try {
    const hot = await fetch('../Bryan-Aaron-Master/wiki/hot.md').then(r => r.text());
    document.getElementById('hot-cache-preview').textContent = hot;
  } catch (e) {}

  try {
    const today = new Date().toISOString().slice(0, 10);
    const dream = await fetch(`./data/dreams/${today}.json`).then(r => r.json());
    document.getElementById('dream-date').textContent = dream.date;
    const ol = document.getElementById('dream-cards');
    ol.innerHTML = '';
    if (!dream.cards || dream.cards.length === 0) {
      ol.innerHTML = '<li><em>No cards tonight.</em></li>';
    } else {
      for (const c of dream.cards) {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${c.title}</strong><br><em>${c.insight}</em><br>→ ${c.action} <small>(${c.estimated_value_minutes}m)</small>`;
        ol.appendChild(li);
      }
    }
  } catch (e) {}
})();
</script>
```

- [ ] **Step 4: Open dashboard in browser, verify**

```bash
open "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/index.html"
```

Expected: page loads, three new cards render, no console errors (some "—" placeholders OK if data files not yet present).

- [ ] **Step 5: Update memory_graph.py to include vault wiki nodes**

Read current `memory_graph.py`:

```bash
wc -l "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/scripts/memory_graph.py"
```

Append a function that walks `Bryan-Aaron-Master/wiki/` and emits nodes + edges from `[[links]]`. Specific implementation depends on existing structure — add (don't rewrite). Pattern:

```python
def load_vault_wiki_nodes(vault_root: Path) -> list[dict]:
    """Walk vault wiki, return nodes with type + edges from [[links]]."""
    import re
    wiki = vault_root / "wiki"
    if not wiki.exists():
        return []
    link_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    nodes: list[dict] = []
    for md in wiki.rglob("*.md"):
        if md.name in {"index.md", "log.md", "hot.md"}:
            continue
        text = md.read_text()
        links = [m.group(1).strip().split("/")[-1] for m in link_re.finditer(text)]
        nodes.append({
            "id": md.stem,
            "type": md.parent.name,  # sources/people/concepts/...
            "edges": links,
            "path": str(md.relative_to(vault_root)),
        })
    return nodes
```

Then in the main graph assembly function (whatever it's called in user's WIP), call `load_vault_wiki_nodes()` and merge results.

- [ ] **Step 6: Smoke test memory_graph.py**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 dashboard/scripts/memory_graph.py 2>&1 | tail -10
```

Expected: script runs without error. If it produces a graph file, verify vault wiki pages appear.

- [ ] **Step 7: Commit**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add dashboard/index.html dashboard/scripts/memory_graph.py && git commit -m "feat(dashboard): add Knowledge + Hot + Dreams cards; memory_graph reads vault wiki"
```

---

## Task 21: Codex adversarial review of ingest pipeline + lint + dream

**Files:**
- Reviewed (no changes unless issues found): `~/.claude/skills/ingest/SKILL.md`, `scripts/lint.py`, `scripts/dream.py`, `Bryan-Aaron-Master/CLAUDE.md`

Sensitive: ingest writes across all vault knowledge. Required forced review per three-brain skill (sensitive paths rule).

- [ ] **Step 1: Invoke codex:codex-rescue in adversarial mode**

In Claude Code, invoke the Agent tool:

```
Agent(
  description="Adversarial review of vault ingest pipeline",
  subagent_type="codex:codex-rescue",
  prompt="Adversarial review. Find every way the ingest pipeline can corrupt Bryan's vault knowledge. Files to inspect:\n\n1. ~/.claude/skills/ingest/SKILL.md (ingest skill instructions)\n2. /Volumes/Samsung PSSD T7/AIS-OS/Bryan-Aaron-Master/CLAUDE.md (vault schema)\n3. /Volumes/Samsung PSSD T7/AIS-OS/scripts/lint.py\n4. /Volumes/Samsung PSSD T7/AIS-OS/scripts/dream.py\n\nQuestions to answer:\n- Can ingest overwrite an existing wiki page wholesale? (should merge only)\n- Can ingest write outside wiki/?\n- Can the no-orphan rule be enforced if Claude misses a [[link]]?\n- Race condition if two ingests run concurrently?\n- What if frontmatter parsing fails on existing pages — does lint mis-report?\n- Symlink/path-traversal hazards in raw filename → archive path?\n- JSON parse failure paths in dream.py — does it leave partial output?\n- ANY way 01-07 domain folders get mutated?\n\nReport: list each finding with severity (critical/high/medium/low) and concrete fix. Be specific — file:line where possible."
)
```

- [ ] **Step 2: Apply fixes for critical + high findings**

For each finding, write an Edit tool call. After fixes, re-run all tests:

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 -m pytest scripts/ -v 2>&1 | tail -10
```

Expected: all pass.

- [ ] **Step 3: Commit fixes**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git add -A && git commit -m "fix: adversarial-review-driven hardening of ingest + lint + dream"
```

(If no fixes needed, skip commit and note in summary.)

---

## Task 22: Live test + final commit + tag

- [ ] **Step 1: Re-run full lint**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 scripts/lint.py
cat dashboard/lint-report.md
```

Expected: report renders, low issue count. Note any required fixes.

- [ ] **Step 2: Manual `/dream --dry-run` test**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && python3 scripts/dream.py --dry-run
```

Expected: JSON file written. If Bryan has `ANTHROPIC_API_KEY` set + wants live dream test, run without `--dry-run`. Confirm before live run.

- [ ] **Step 3: Open dashboard, walk all 6 pillars**

```bash
open "/Volumes/Samsung PSSD T7/AIS-OS/dashboard/index.html"
```

Verify:
- Knowledge card shows page count >0
- Hot cache renders content from `wiki/hot.md`
- Dreams card shows today's JSON (may say "No cards tonight" if dry-run)
- Existing cards (memory graph, etc.) still functional

- [ ] **Step 4: Tag**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git tag aios-v1 && git log --oneline -10
```

Expected: tag created. Recent commits visible.

- [ ] **Step 5: Update MEMORY.md index**

Path: `/Users/aaronfamilylivestock/.claude/projects/-Volumes-Samsung-PSSD-T7-AIS-OS/memory/MEMORY.md`

Append:

```markdown
- [AIS-OS v1 three-brain build](project_aios_v1_three_brain_build.md) — Karpathy wiki in vault + Roberts dashboard + Herk skills, shipped 2026-05-16
```

Then create the memory file at `/Users/aaronfamilylivestock/.claude/projects/-Volumes-Samsung-PSSD-T7-AIS-OS/memory/project_aios_v1_three_brain_build.md`:

```markdown
---
name: project-aios-v1-three-brain-build
description: AIS-OS v1 — Karpathy LLM Wiki in Bryan-Aaron-Master vault + Roberts dashboard + Herk skills shipped 2026-05-16 from spec + plan in docs/superpowers/
metadata:
  type: project
---

Shipped 2026-05-16. K2 hybrid (Karpathy wiki + 01-07 domain folders preserved).

**Why:** Bryan watching Karpathy/Roberts/Herk videos asked to consolidate Obsidian vault + AIS-OS repo into one operating system.

**How to apply:** When Bryan asks about vault queries, route through `wiki-query` skill or `wiki/index.md` → `[[links]]`. When suggesting automations, run `/dream` first to see if dream engine already surfaced it. For raw inbox processing, always `/ingest` — never edit `wiki/` manually.

**Pointers:**
- Spec: `docs/superpowers/specs/2026-05-16-three-brain-aios-build-design.md`
- Plan: `docs/superpowers/plans/2026-05-16-three-brain-aios-build.md`
- Git tag: `aios-v1`
```

- [ ] **Step 6: Final state verification**

```bash
cd "/Volumes/Samsung PSSD T7/AIS-OS" && git status && echo "---" && git tag | grep aios
```

Expected: clean working tree (or only intentional WIP), tag `aios-v1` present.

---

## Post-launch (optional, not part of v1)

- Install cron: `0 2 * * * cd /Volumes/Samsung\ PSSD\ T7/AIS-OS && /usr/bin/python3 scripts/dream.py` (confirm w/ Bryan first; macOS may need launchd instead).
- Weekly `/lint` cadence in calendar.
- 30-day check: ≥3 automations shipped from dream cards?

## Rollback

Any task fails → `git reset --hard HEAD~N` to last good state, restore vault from `Bryan-Aaron-Master.backup-2026-05-16` if scaffold corrupted.
