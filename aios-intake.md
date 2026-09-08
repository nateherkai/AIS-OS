# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
Brandon "Broman" Roman, North Las Vegas. Solo full-stack developer, content creator,
music producer/songwriter, streamer, and digital-product builder. Currently between
jobs, working toward sustainable income through content. Primary vehicle is YouTube:
rebranding @xbroman_ (1,298 subs) into NOT A WORK BRO, long-form led, with Shorts/
TikTok/Reels for discovery only (not monetization). Also runs LYTW (older tech-focused
channel) and side dev projects (Home Base, SLASH, Loop, Portfolio). No paying customers
yet — audience is the current ICP, future ICP is viewers/subscribers who convert to
Fan Funding/YPP revenue, plus potential freelance dev/music clients down the line.
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

```
[Skipped for now, 2026-09-06 — Brandon opted to defer this. Re-run /onboard after
pasting real samples (email/LinkedIn/DM) to fill references/voice.md.]
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
1. Hit YouTube watch-hour thresholds — Fan Funding (3,000 hrs) then full YPP (4,000
   hrs) on NOT A WORK BRO, hard deadline 2027-02-01.
2. Ship Home Base — the dev/creator/ADHD productivity hub — to actually support the
   content pipeline (script → record → edit → publish).
3. Fix the real bottleneck: finishing/publishing and idea→script (editing is not the
   bottleneck).
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Multiple answers OK. Stripe? Skool? GoHighLevel? QuickBooks? A spreadsheet?

```
No revenue source yet other than family support. Goal is income from content-related
work: dev work, music, and general content creation. Progress currently tracked via
YouTube Studio (subs/watch-hours) toward Fan Funding/YPP thresholds, not a financial
tool.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Email (which one — Gmail / Outlook)? Slack? Teams? DMs (Skool / Discord / iMessage)? Phone?

```
Discord, Gmail, Outlook.
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Granola? Otter? Fireflies? Google Drive? Notion? Dropbox? A folder on your desktop you keep meaning to organize?

```
No separate tool — everything routes to the Obsidian vault at
"C:\Users\roman\Claude Main\content-brand\Obsidian Vault". That vault is the durable
knowledge system (decisions, architecture notes, session digests); all future
knowledge about Brandon and his projects should reference/connect there.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

The single biggest time-suck or recurring drudgery. Plus where tasks/projects live (ClickUp / Asana / Linear / Notion / a notebook).

```
Biggest time-suck: finishing/publishing and idea→script (editing is not the
bottleneck — gets pulled into creative/visual decisions mid-edit instead). Tasks live
per-project in each repo's own PROJECT-STATE.md (no central board); durable
cross-project decisions live in the Obsidian vault.
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
