# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
Identity: Bryan — FFA teacher building toward early retirement through Ag Coach Pro. Operator, developer, and domain expert in one.

Offer: Ag Coach Pro — AI-powered FFA CDE/LDE training platform at agcoachpro.com. Key features:
- RAG-backed quiz generation pulled from official Texas FFA rulebooks (livestock, forages, horse eval, ag skills, and more)
- AI livestock ID drill with 4-panel composite images
- Flashcard mode, builder quiz engine, contest-specific practice modules
- Ag Coach Brain chatbot — RAG-grounded Q&A for students
- Teacher dashboard: performance gaps, class readiness, student progress tracking
- Annual site licenses (Greenhand $495 / Blue & Gold $895 / Lone Star Elite $1,495) with token-based AI credit system (Feed Bags = $100/1M supplemental credits)
- Built on Expo Router / React Native / Supabase / Gemini AI — runs web + mobile

ICP: Texas FFA chapters. Primary buyer = teacher/ag advisor (chapter-level license). Primary users = students drilling for CDEs. Secondary = parents wanting proof of progress.
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

```
Sample 1 — customer check-in email:
Hey Trinity,

Checking in to see how the Athens is getting on with Ag Coach Pro? Since you're set up on the Lone Star Elite plan, I wanted to make sure you've got everything you need. Please list what you like and what we can improve on. I'm still very much in the building phase and I'm adding to it almost daily. Your feedback would be huge in helping me make this the best training platform in the country. 

If you're having any issues please let me know and I'll work to get it fixed ASAP. 

Thank you for your support we truly appreciate it!!
```

```
Sample 2 — customer DM:
Hey Darrel, so glad you got in. The subscription will last for 12 months from when you purchase it. Also,  please give any feedback while using this. I'm constantly updating it. If there is a feature you would like to see please let me know and I'll do my best to incorporate it.
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
1. Close at least 50 schools on Blue & Gold or Lone Star Elite plans by August 2026.
2. Pay off all debt (except house) by end of 2026.
3. Reach $120,000/yr revenue from Ag Coach Pro so Bryan can leave teaching and run the business full time.
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Multiple answers OK. Stripe? Skool? GoHighLevel? QuickBooks? A spreadsheet?

```
Stripe — revenue lands and is tracked there.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Email (which one — Gmail / Outlook)? Slack? Teams? DMs (Skool / Discord / iMessage)? Phone?

```
Email: support@agcoachpro.com (Gmail). Bulk outreach via MailerLite.
Text/iMessage, Facebook DMs.
Lead gen happens at in-person events: Ag Teachers Conference, conventions, FFA events.
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Granola? Otter? Fireflies? Google Drive? Notion? Dropbox? A folder on your desktop you keep meaning to organize?

```
MacBook local files + Google Drive.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

The single biggest time-suck or recurring drudgery. Plus where tasks/projects live (ClickUp / Asana / Linear / Notion / a notebook).

```
Biggest time-suck: teaching (FFA classroom). Bryan prefers coding and building Ag Coach Pro but teaching is still the day job.
Task tracking: currently in his head — no formal system yet. Open to learning new tools.
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
