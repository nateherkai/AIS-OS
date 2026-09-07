---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

# Idea → Script Draft Prompt

**What this is:** a prompt-only workflow (autonomy level L2 — Drafted). You run this
by hand whenever a new entry lands in your "Idea Inbox" Google Drive doc. No skill,
no automation — you paste, Claude drafts, you review. See `decisions/log.md`
(2026-09-07) for the full Method spec this came from.

**Why prompt-only, not a skill:** `references/voice.md` doesn't exist yet (Q2 was
deferred at onboarding). Until it does, every draft needs your own pass to sound like
you instead of generic AI copy — staying manual keeps you in that loop by default. If
you want it automated later, re-run `/level-up` and Phase 3 can upgrade this to an
AI-assisted skill.

---

## The prompt

Copy this, fill in the bracketed idea, and run it as-is:

```
I have a raw video idea for my YouTube channel NOT A WORK BRO (long-form, watch-hour
focused) or a Shorts/TikTok/Reels post (discovery-only, doesn't count toward
watch-hours). Here's the idea, verbatim:

[PASTE THE IDEA INBOX ENTRY HERE]

Before drafting, read:
- The Obsidian vault's "Not A Work Bro Channel Identity" note (channel brand facts,
  the Shorts-vs-long-form constraint, and the personal bottlenecks/energy-curve notes)
- Any Home-Base locked decisions relevant to format/visual system

Then:
1. Tell me whether this reads as long-form or Shorts material, and why.
2. Draft a structured first-pass script: hook, body beats, CTA. Keep it a draft, not
   a finished piece — I will do a voice pass on this myself.
3. Flag anywhere you had to guess at tone or register, since there's no voice
   reference on file yet.
4. Save the draft to video-scripts/YYYY-MM-DD-<short-slug>.md, tagged [Long-form] or
   [Shorts] in the header.
```

## After you run it

- Do your own voice pass on the draft before it's post-ready — that's the ~10%
  manual slice this workflow was scoped with.
- If you paste voice samples into `aios-intake.md` and re-run `/onboard`, come back
  and re-run `/level-up` to consider upgrading this to L3+ or an actual skill.
