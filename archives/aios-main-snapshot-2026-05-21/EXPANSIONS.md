# EXPANSIONS — what to add as you grow

The kit ships lean on purpose. Three skills, six folders, one framework reference. That's it. As you use it, you'll outgrow the base — this guide tells you what to add, when, and why.

The AIOS structure should look like a small, well-run business. Not a hoarder's basement.

---

## What ships in the kit (don't remove)

| Folder / file | Purpose |
|---|---|
| `context/` | About you, your business, your priorities. Filled by `/onboard`. |
| `references/` | Frameworks, voice samples, API guides, SOPs as you build them. |
| `decisions/log.md` | Append-only record of what was decided and why. |
| `archives/` | Old files. Don't delete — move here. |
| `connections.md` | Registry of every system your AIOS can reach. |
| `.claude/skills/` | Your skills: `/onboard`, `/audit`, `/level-up`. Add more via `/level-up`. |
| `aios-intake.md` | Source-of-truth for `/onboard`. Edit and re-run any time. |
| `CLAUDE.md` | Root operating manual. Filled by `/onboard`. Edit when your role/voice changes. |

---

## What to add as you grow

| Folder / file | Add when | Why |
|---|---|---|
| `projects/` | You start running 2+ ongoing workstreams that have their own context | Active projects need scoped context separate from the evergreen `context/` files |
| `templates/` | You catch yourself copy-pasting the same prompts or doc scaffolds | Reusable, parameterized starting points; reduces drift |
| `brand-assets/` | You generate visual content (carousels, slides, thumbnails, images) | Centralizes logos, palettes, fonts, voice/tone — the AIOS reaches in instead of guessing |
| `references/sops/` | You document how recurring processes run | Standard operating procedures the AIOS reads to run things consistently |
| `references/{tool}-api.md` | You connect a new API or MCP and figure out how it works | Researched-once-saved-forever. `/audit` rewards this; future skills don't re-research. |
| `scripts/` | You write Python or Bash to hit APIs not covered by MCPs | Most people's second connection is a script, not an MCP |
| `.claude/agents/` | You need a sub-assistant for repeatable, multi-step research/writing | Agents run on cheaper models in their own context — keep your main session lean |
| Sub-OS folders (e.g. `youtube-os/`) | You have a vertical with its own data, sheets, transcripts, scripts | Isolation pattern — vertical workflows get their own scoped operating manual + skills |

---

## Suggested cadences

When each surface gets routinely touched:

- `decisions/log.md` — every meaningful decision (`/level-up` Phase 2 captures these automatically)
- `archives/` — quarterly cleanup; move stale projects, deprecated skills, old intake versions
- `references/sops/` — when a process gets re-run by someone new, write the SOP
- `connections.md` — every time a new tool gets wired in, add a row
- `references/{tool}-api.md` — same time as `connections.md` update; capture the API once
- `CLAUDE.md` — quarterly review; rewrite the persona/priorities section after `/level-up` Q90

---

## What NOT to add

Anti-patterns. These look helpful but rot the structure:

- **Don't dump raw email/Slack archives into `references/`.** The wiki is not a doc dump. Interpreted facts only.
- **Don't build folder-of-folders for organization theater.** Flat with good naming beats deep nesting. If you need a folder hierarchy to find something, you have a search problem, not an organization problem.
- **Don't add `notes/`, `misc/`, `tmp/`, or `inbox/`.** Graveyards. Use `archives/` if it's old, write a real file in the right place if it's new.
- **Don't pre-create folders you don't need yet.** Empty folders are noise. The AIOS will tell you when it's time.
- **Don't have parallel `decisions.md` and `decisions/log.md`.** Pick one. The kit ships `decisions/log.md`.
- **Don't fork your operating manual.** One `CLAUDE.md` at the root. Sub-OS folders can have their own scoped CLAUDE.md, but the root is canonical.

---

## How to tell when it's time to add a folder

Ask three questions:

1. **Is this conceptually new?** Or does it fit somewhere existing?
2. **Will I touch this 3+ times in the next month?** If not, it's premature.
3. **Could `/level-up` route a future skill into here naturally?** If yes, the AIOS will use it. If no, you're organizing for yourself, not for the system.

Two yeses = add. One yes = wait.

---

> *Your AIOS structure should look like a small, well-run business — not a hoarder's basement. When you can't find something, that's a signal to consolidate, not to add another folder.*
