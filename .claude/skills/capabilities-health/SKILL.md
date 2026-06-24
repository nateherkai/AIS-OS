---
name: capabilities-health
description: >-
  Structural health check of your AIOS Capability layer — skills, scripts, and the
  index that lists them. Use when you say "/capabilities-health", "lint my skills",
  "is my README/index stale", "check for skill drift / undocumented skills / broken
  references", or as a periodic pass on a growing .claude/skills/. The deterministic
  floor under the Capabilities C of /audit. Report-only — never auto-rewrites.
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
---

# capabilities-health

The deterministic floor under the **Capabilities** C of `/audit`. `/audit` *scores*
whether your skills are in good shape; this *proves* it, item by item, and never
guesses. It is the 3Ms **Operate** layer — the Bike Method and the Kill Switch — turned
into a tool: keep what earns its place, see what is drifting, retire what does not.

It is a **drift-surfacer, not a janitor.** **Report-only** — it never rewrites your
index or a `SKILL.md`. It surfaces; you decide what to act on.

## Why you need it

A fast-growing skill folder outruns its own documentation. You add skills faster than
you update the README or index that lists them, and within a month the map that is
supposed to tell you what you own is lying. That silently kills leverage: you forget
what you own, so you stop using it. This catches the drift the moment it appears.

## When to run

Monthly, or after a burst of skill authoring (`/level-up`, imports). The deterministic
half is cheap; the AI half wants an interactive session.

## How it runs — deterministic first, AI second

### 1. Deterministic census (the ~60%)

```
python3 scripts/capabilities-health.py            # run from your AIOS root
python3 scripts/capabilities-health.py --index README.md
python3 scripts/capabilities-health.py --section drift
```

Stdlib-only, no writes, always exits 0. Every section degrades gracefully if a layer is
absent (no `scripts/`, no `knowledge/`, no formal index — all fine). Six sections:
- **Census drift** — skill/page counts claimed in your index (`CAPABILITIES.md` or
  `README.md`) vs disk. The headline number.
- **Undocumented skills** — skills on disk whose name never appears in the index.
- **Phantom refs** — `` `/name` `` refs in the index with no skill dir.
- **Broken references** — `scripts/<file>` refs (resolved against root `scripts/` AND a
  skill's own `scripts/` subdir) and `/skill` refs in the curated docs that resolve to
  nothing. Skill-body example slash-tokens are deliberately not flagged here.
- **Frontmatter** — each `SKILL.md` has `name:`+`description:`, `name:` matches dir.
- **Orphan scripts** — `scripts/` files referenced nowhere (document or retire).

Read the report. The high-value items are census drift and undocumented skills.

### 2. AI pass (the ~30% — judgment only)

Only on what the census surfaces — do **not** re-read every skill:
- **Regenerate the index** — for census drift + undocumented skills, draft an updated
  index (correct counts; slot each undocumented skill into the right section by reading
  just its frontmatter `description:`). **Propose the diff; don't apply.** This is the
  skill's main payload.
- **Retire-vs-keep (the Kill Switch)** — for orphan scripts and any skill not referenced
  anywhere, ask: still earning its place, or retire it? Don't keep a skill running on
  sunk cost.

### 3. Output contract

- A one-screen report: census numbers + the AI pass's index diff / retire calls.
- Propose (don't apply) the index rewrite. Section placement is yours to curate — a
  script can't decide which group a skill belongs in.

## Guardrails

- **No auto-fix.** The script has no `--write`. Your index grouping is hand-curated;
  surfacing drift is the job, not silently rewriting the map.
- **Examples aren't breaks.** Slash-tokens and `./scripts/x` snippets inside a
  `SKILL.md`'s fenced code are illustrative; the script already filters them.
- **Drift ≠ rot.** An undocumented skill is usually just a new skill the index hasn't
  caught up to, not a problem with the skill. Update the map.

---

Built by Marko Stankovic on top of the AIS-OS kit. Complements `/audit` (it makes the
Capabilities C deterministic) and `/level-up`. Free to reuse.
