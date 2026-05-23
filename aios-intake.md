# AIS-OS Intake

This is the source-of-truth file for your AIOS. Fill it in by typing, voice-pasting (Wispr Flow / OS dictation), or running `/onboard` for a guided conversation. Whichever mode, this file is what `/onboard` reads to scaffold your Day-1 setup.

**Hard cap: 7 questions.** Each answerable in under 60 seconds. Don't overthink — you can edit and re-run `/onboard` any time.

---

## Q1 — Who are you, what do you sell, who do you sell it to?

Identity, offer, ICP. One paragraph each is fine.

```
Identity: Travis Peng — Northeastern University student, Associate GTM Intern (Sales & Operations Strategy) at Everest Labs since January 2026. Based out of Everest Labs HQ in Fremont, CA. Email travis@everestlabs.ai, GitHub Coderman562, personal site travispeng.com. Builder by instinct (code/engineering background), now learning the commercial side of a hard-tech robotics company.

Offer: Everest Labs sells AI-powered software + robotics to recycling plants and Material Recovery Facilities (MRFs). Camera-vision systems and robotic arms identify and sort recyclable materials so they don't end up in landfills. The platform (RecycleOS) also provides operational data MRF operators use to optimize throughput and brands use to track/verify sustainability claims. RaaS (robots-as-a-service) and CapEx commercial models. Sold via RSGs (Recycling Solutions Group quotes) and facility-level proposals.

ICP: MRF operators (recycling facility owners/operators) — primary buyers. Secondary: consumer-goods brands and waste haulers who want supply-chain sustainability data. Deals are facility-by-facility; commercial conversations involve plant managers, ops directors, and sometimes corporate sustainability buyers.
```

---

## Q2 — Paste 1-2 things you've written recently. Don't edit them.

An email, a LinkedIn post, a DM, a doc — anything that sounds like you when you're not trying. **Paste verbatim.** Do not type these mid-conversation with Claude — chat-shaped samples are worse than no samples (voice contamination).

```
Sample 1 — Slack/messaging thread with Mylinda Jacobsen (external contact)

[06/05/2026 12:51 PM] Travis Peng: Mylinda, thanks for the conversation! Hope I didn't seem like I was doing other things near the end because I was telling Katie that I was going to be running late for my meeting scheduled with her

[06/05/2026 12:57 PM] Travis Peng: I can bring up the idea of adding Navigator to the Sarasota vision POC with Apurba tonight from what we talked about, and would love to get the Tom/Jamie/Chris intros whenever convenient. Also if you could share the the case study that would be awesome!

[06/05/2026 1:00 PM] Mylinda Jacobsen: Yes on all

[06/05/2026 1:24 PM] Mylinda Jacobsen: I sent the grey parrot newsletter and I am coordinating with the CS guys

[06/05/2026 1:26 PM] Travis Peng: ok awesome I got it thank you!

[18/05/2026 11:56 AM] Travis Peng: Mylinda, an update on my side. I'm learning more as I go and I want to keep you included! My last conversation with you was very nice, and I remember I was introducing what my idea of Navigator was and we were developing out a vision for what it could be used for and you were very helpful to share your years of experience on things. Now I have a more full picture of Navigator and how we plan to market it aswell as build it out. It seems like Apurba's plan is to use the POCs we have, which includes Caglia, Circular Services, and RSG OEE, as a way to introduce Navigator later on when we are in early stages of development. And he brought be on to manage those POCs which I'm getting more info on as I go. Recently I brought up that you were kind enough to offer intros with the folks at Circular Services to which Apurba said that he'd be working with services on the POC and wouldn't want to do anything extra, which is fair and I don't want to step on Apurba's toes.

[18/05/2026 11:57 AM] Travis Peng: what do you think would be best and how is the status coordinating with the CS guys? and has everything been working well with the Claude skills on Project Jetstream?
```

```
Sample 2 — Slack intro DM to Georgia Seto (internal teammate)

[14/05/2026 1:04 PM] Travis Peng: Hi Georgia! I don't think we've formally met yet. I'd like to introduce myself as the summer Product GTM Associate intern who is working here until end of the summer. As given by Apurba, I'll be the running point on the Navigator POCs and helping with marketing. I feel like we may be working together down the line, so I'm reaching out to connect! If you have the availability, may I schedule a time to meet with you next week? If so, what's your schedule like?

[14/05/2026 2:54 PM] Georgia Seto: Hey Travis! We actually met before and have been in a few zoom calls together. Let me check my calendar next week but yes that sounds good.

[14/05/2026 2:54 PM] Georgia Seto: How about Monday around 130/2pm?

[14/05/2026 3:27 PM] Travis Peng: Oh that's great! I do know

[14/05/2026 3:29 PM] Travis Peng: Yes let's do that

[14/05/2026 3:29 PM] Travis Peng: 1:30 would be great, sending an invite

[14/05/2026 3:43 PM] Georgia Seto: Great! Looking forward to it
```

---

## Q3 — What are your 2-3 biggest priorities for the next 90 days?

Quarterly priorities. Not yearly aspirations. Things that, if not done by July, would make you say "I wasted Q2."

```
Window: now (mid-May 2026) → end of summer internship (~mid-August). Anchored to the meeting with Apurba on May 13. Overarching outcome: be able to say at the end of the internship that I was on the launch team for Everest Labs' first agentic product (Navigator) — breadth across customer engineering, GTM, and launch docs.

1. Own the Navigator POC rollouts. Be the Navigator rollout guy across Caglia, Republic OEE, and Circular Services (Sarasota) — plus the two on deck (ecology + Connections). For each feature: scope with customer, coordinate engineering (Sid/Anish/Avinash/Ted), deploy, gather feedback, iterate. Track everything in JIRA with customer-facing feature epics and dependencies on engineering tickets. "Don't let any balls drop." Current sprint dev milestone: end of May.

2. Build the "What is Navigator" internal training artifact before July GA. Turn the long onboarding doc into a 2-minute consumable artifact (video or animated PowerPoint) that paints Navigator without going "LLM pilled." Use it to bring the engineering team up to speed first, then sales team in late summer. Target: ready well before GA (July).

3. Design and run the external customer warming program for July GA. ~30–40 existing robot customers who already have hardware deployed. Build the program: teaser video, walkthrough demo (group + 1:1 options), free month of Navigator wired to their robot data via MCP. Goal: get real feedback from advanced users before GA, and seed demand at zero hardware cost. Plan now, execute around GA.
```

---

## Q4 — Where does revenue actually land, and where is it tracked?

Multiple answers OK. Stripe? Skool? GoHighLevel? QuickBooks? A spreadsheet?

```
Reframed for an intern context — "where does deal / customer financial data live that I need visibility into."

- Salesforce — system of record for deals. Accounts, customer type/stage, proposals, Gmail integration on account records. Filter by customer type to see who has paid / is paying.
- Customer Deployment Dashboard — Google Sheet listing actively deployed lines/systems (separate from Salesforce). Link: https://docs.google.com/spreadsheets/d/1gMk0GkQqDjQ6MINHCkFHA-rco6ZddxbvlhbXSoNXz8M/edit?gid=0#gid=0
- Proposals — currently scattered. Apurba is compiling RSG / Caglia / Circular Services proposal links into one doc for me and Avinash.
```

---

## Q5 — Where do you talk to customers, your team, and the outside world day-to-day?

Email (which one — Gmail / Outlook)? Slack? Teams? DMs (Skool / Discord / iMessage)? Phone?

```
- Internal team (Everest Labs): Flock — company messaging platform, functions like Slack. Primary day-to-day comms with Apurba, Garima, Dan, Sid, Anish, Avinash, Ted, Georgia, and the rest of the team.
- Customers: Gmail (travis@everestlabs.ai) is the main channel as of now. Zoom for scheduled meetings (customer transcripts referenced in May 13 onboarding meeting). Other texting channels exist for some customers — to be added once Travis surfaces them from meeting notes.
- Outside world / external (peers, Mylinda Jacobsen, Northeastern network): Gmail + LinkedIn DMs likely. Add personal channels (iMessage, etc.) as they become relevant.
```

---

## Q6 — Where do meeting recordings, notes, and important docs live?

Granola? Otter? Fireflies? Google Drive? Notion? Dropbox? A folder on your desktop you keep meaning to organize?

```
- Meeting recordings (Everest): Granola is primary. Fireflies holds the odd Everest meeting plus personal/family audio recordings worth keeping. Both should be searchable for context when pulling priorities or follow-ups.
- Notes: no central document hub. Notes live wherever they happen (Flock messages, scratch docs, the in-progress onboarding doc).
- Important docs: currently scattered across links — Salesforce, Google Drive, Flock, individual share links. Consolidation in progress. Apurba is compiling RSG / Caglia / Circular Services proposals into one document. Onboarding doc Travis is writing will house links as it grows.

Open gap: no single source of truth for docs yet. This is a known pain point that the AIOS should help triage as docs get surfaced.
```

---

## Q7 — What's the one task that eats your week, and where do you currently track work?

The single biggest time-suck or recurring drudgery. Plus where tasks/projects live (ClickUp / Asana / Linear / Notion / a notebook).

```
Top pain: chasing things down. Tracking my own TODOs, tracking POC state across Caglia / Republic OEE / Circular Services, and surfacing info that's scattered across Salesforce, Google Drive, Flock, Granola, and individual share links. Coordinating the "middle person" load between engineering and customer for each Navigator feature is a related drain.

Where work is tracked: JIRA is the formal system going forward — feature epics per customer with dependencies on engineering tickets (Apurba/Anish's structure). But the team is not actively on JIRA yet, and there are likely micro-tracking formalities across teams (sprint boards, Flock threads, spreadsheets) that I am not yet aware of. To be mapped as I find them.
```

---

When this file is filled, run `/onboard` (or re-run it) and the wizard will scaffold your Day-1 file set: `context/`, `references/voice.md`, populated `connections.md`, and a filled `CLAUDE.md`.
