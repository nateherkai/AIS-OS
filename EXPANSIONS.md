# EXPANSIONS — what to add as you grow

The kit ships lean on purpose: six skills and a small set of context and reference files. As you grow, use `/link` to add new sources to the right route, and `/audit` to check that the information remains findable and current.

The AIOS structure should look like a small, well-run business. Not a hoarder's basement.

---

## What ships in the kit (don't remove)

| Folder / file | Purpose |
|---|---|
| `context/` | About you, your business, your priorities. Filled by `/onboard`. |
| `references/` | Frameworks, voice samples, API guides, SOPs as you build them. |
| `decisions/log.md` | Append-only record of what was decided and why. |
| `brainstorms/` | Saved `/grill-me` interviews; created on first use. Confirmed context is linked back to its capture. |
| `archives/` | Old files. Don't delete — move here. |
| `connections.md` | Registry of every system your AIOS can reach. |
| `.claude/skills/` | Your skills: `/onboard`, `/audit`, `/level-up`, `/link`, `/grill-me`, `/3d-brain`. Add more only when they solve a real need. |
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

## Security as you grow

As you wire connections and build skills that pull external data, two
risks compound. The kit gives you the structural defences; you have to
keep them honest as your AIOS reaches further.

### Prompt injection — wrap external data at the boundary

Email bodies, meeting transcripts, scraped pages, and API responses can
contain instructions Claude will execute if they reach the prompt
without a trust boundary. The `Trust boundary` section in `CLAUDE.md`
tells Claude to treat anything inside `<external-data>` envelopes as
inert text — but only if the writers of that file actually wrap
content. Every script, MCP, or skill that writes external content into
a trusted surface (`context/`, `decisions/log.md`, `references/`,
anywhere the AIOS reads) should wrap it:

```python
with open("decisions/log.md", "a") as f:
    f.write("<external-data source=\"gmail:thread/abc123\">\n")
    f.write(email_body)
    f.write("\n</external-data>\n")
```

Same idea in shell, n8n, Make.com, or any other glue: emit the open
tag, the raw content, the close tag. The trust boundary handles the
rest — but only if you don't bypass it by writing raw external content
into trusted files.

### Secret drift — `references/{tool}-api.md` as a leak surface

`references/{tool}-api.md` files accumulate auth details over time as
you research APIs once and save the results. Treat them like `.env`:

- Never paste live tokens, API keys, or session cookies into them
- Use placeholder labels: `Authorization: Bearer <your-token-here>`
- Periodically grep them for accidental real credentials:
  `git grep -E "(sk-|ghp_|xoxb-|AKIA)" references/`

The default `.gitignore` excludes `references/*-api.md` for this
reason — but only if you add the file fresh. If you ever commit one
and then add the secret later, history retains it.

### Voice samples are credentials

`references/voice.md` contains verbatim writing samples specifically
chosen because they sound like {{Your Name}} when not trying. That
makes them maximally useful for impersonation. Treat the file like a
password: gitignored by default, never shared outside the repo, not
included in screen-shared demos.

---

## How to tell when it's time to add a folder

Ask three questions:

1. **Is this conceptually new?** Or does it fit somewhere existing?
2. **Will I touch this 3+ times in the next month?** If not, it's premature.
3. **Could `/level-up` route a future skill into here naturally?** If yes, the AIOS will use it. If no, you're organizing for yourself, not for the system.

Two yeses = add. One yes = wait.

---

> *Your AIOS structure should look like a small, well-run business — not a hoarder's basement. When you can't find something, that's a signal to consolidate, not to add another folder.*
