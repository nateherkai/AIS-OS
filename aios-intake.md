# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
This AIOS runs a JOB SEARCH, not a business. The "offer" is Yuan as a candidate; the "ICP" is companies hiring.

Who: Yuan Chen. Full-stack Software Engineer specialising in integrations and automations. Currently Software & Customer Engineer at Magic Eden (Solana NFT marketplace, Mar 2022 - Present). ~7 years across software + cloud engineering. Based in Melbourne, Australia (Malvern East, VIC 3145). Contact on CV: yuan.chen90@gmail.com / 0401 417 068.

Offer (the candidate): Full-stack engineer with deep integrations + automation experience. Highlights — built an automated support-ticket escalation workflow wiring Intercom + Notion + Slack; shipped an NFT collection auto-lister off internal indexer APIs; maintained the Creator Hub app. Strong cloud background (GCP, Azure, AWS), IaC (Terraform, Ansible), CI/CD, and data/BI (BigQuery, Power BI). Codes in NodeJS, Python, C#, React, Vue, SQL. Uses LLMs (Claude/ChatGPT/Grok) for prototyping and automation. NAB Hackathon 2021 winner.

ICP (target roles): Software Engineering or AI Engineering roles. Prefers fully remote (open to international companies); open to hybrid if local to Melbourne. Strong preference for startups (more exciting). Salary target $150K+ AUD plus super.
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

Source: LinkedIn recruiter replies + a Gmail message. Yuan's words only, transcribed verbatim from screenshots (light typos left as-is — they reflect fast casual typing, not a style to copy). Identifiers/PII stripped.

```
[Reply to a recruiter, LinkedIn]
Hey Luke,
Thanks for the message, definitely interestes in hearing more about this role.
Would you like to talk tomorrow? Im free after 10am to have a chat.
Regards,
Yuan

[To a recruiter, LinkedIn]
Hey Donna, I missed a call from you today and wanted to know if you're interested in rescheduling for another call tomorrow morning?

[Reply to a recruiter, LinkedIn]
Hi Darren, yep absolutely. What roles do you have in mind?
```

```
[Follow-up after a call, LinkedIn]
Hi Eli,
Hope you had a good day off on Wednesday, it was great chatting to you!
Just checking in to see if you have any feedback from our quick call. I'm keen about the prospects of Kasna and working on GCP.
Have a great weekend mate.
Regards,
Yuan

[Support email, Gmail]
Hi there,
Just wanted to check in to make sure that I don't have an active subscription with your platform!
Warm regards
Yuan
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
1. Build a robust process to automate the job search. Sub-goals:
   - Surface >=10 quality job opportunities per week to review
   - Auto-tailor CV + cover letter for each application
   - Discover key recruiters / industry people to follow + connect with on LinkedIn / X
   - Build a routine to stay current on industry news
   - Produce a visualisation of Yuan's skillsets and their relevancy to industry areas/roles
2. Sharpen the demo portfolio. Has projects to demo already; wants ideas for new projects that build + showcase AI experience (e.g. AI orchestration and workflows).
3. Build a shortlist of 20 startups Yuan actually wants, and get warm intros to a few of them.
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Adapted for the job search: where opportunities come from + where applications are tracked.

```
Sources today: Seek and LinkedIn. Open to any. Suggested additions for a remote/startup focus: Wellfound (AngelList), Y Combinator's Work at a Startup, Hacker News "Who's Hiring", Indeed.

Tracking: none yet — just getting started. Decision: keep the application tracker as a markdown file inside THIS repo. This repo is intended to host many future projects, so create a `projects/` directory and put the job search under `projects/job-search/` (e.g. `projects/job-search/applications.md`). AIOS-level context (context/, references/, connections.md, CLAUDE.md) stays at the repo root and is shared across projects.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Adapted for the job search: outreach + networking surfaces.

```
- Email (job search): yuancdata@gmail.com (Gmail). NOTE: the current CV lists yuan.chen90@gmail.com — align the CV to yuancdata@gmail.com so replies land in the watched inbox.
- LinkedIn: https://www.linkedin.com/in/yuanxchen/ — primary channel for recruiter conversations + networking.
- X / Twitter: @magicfish23 — for following + connecting with key industry people.
- Phone (on CV): 0401 417 068.
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Adapted for the job search: where CVs, cover letters, and notes live.

```
Today: Google Docs (master CV; source PDF was read from ~/Downloads). Master CV on file: "Resume - Yuan Chen 2026.02.02.docx.pdf".
Going forward: Claude creates + stores all job-search docs as .md files in this repo under projects/job-search/ — tailored CV variants, cover letters, interview-prep notes, recruiter-call notes. Convert to PDF/Docs only at send time.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

Adapted for the job search: biggest drudgery + where work is tracked.

```
Top pain: the whole process feels like a drainer; the single biggest gripe is tailoring CVs + cover letters per role. Goal: automate as much of the end-to-end process as possible.
Task tracking: simple markdown in this repo (e.g. projects/job-search/tasks.md). No ClickUp/Asana/Notion.
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
