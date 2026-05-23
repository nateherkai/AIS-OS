# Week of 2026-05-18 — Everest Task Map (Draft 1)

**Status:** Draft. Priority-organized task map produced from Apurba 1:1 (May 20) + May 21 reassignments + supporting meetings. Awaits link drop from Travis → enrichment with state from meetings/JIRA/email → daily breakdown.

**Today is Thu 2026-05-21.**

## Source meetings

- **Apurba 1:1 — May 20 PM** ("Belt utilization and loading metrics") — priority matrix + workstream assignments
- **Apurba — May 21 AM** ("Grafana LLM plugin setup and dashboard testing with MCP") — Travis assigned Grafana chat eval (light-yellow prompts)
- **Apurba — May 21 PM** ("Grafana and Libra chat evaluation — context, reasoning, and plugin options") — Libra chat investigation added; Fresno trip cancelled
- **Ravi — May 20 PM** ("Belt video project") — belt lacing daily artifact handed off to Travis
- **Apurba + Jerry — May 19 PM** ("Vision system deployment — mass balancing, screen optimization, robot ROI") — Connections opportunity, incident response idea
- **Navigator Eng PM Sync — May 19 AM** — release cadence + JIRA structure
- **Navigator launch — May 18 PM** — marketing calendar + PR strategy

## Locked anchors this week

| When | What |
|---|---|
| Thu May 21 (today) | Finish Grafana chat eval — Travis's light-yellow prompts |
| Fri May 22 | Caglia JIRA restructure (Fresno trip CANCELLED — Ravi declined showing-around duty); Libra chat side-by-side eval |
| Sat–Mon May 23–25 | Memorial Day weekend — break |
| Tue May 26 | Avinash + Anish conversations (Caglia eng coordination, Claude account, Libra admin access) |
| **Wed May 27** | **Caglia data review with Apurba + customer** ⭐ |

---

## Priority Matrix (Apurba's framing — May 20, updated May 21)

### Quadrant 1 — High Importance / High Urgency

#### 1. Caglia POC — own end-to-end

The week's center of gravity. Wed May 27 data review is the milestone.

- **JIRA epic/story restructure** per Apurba's blueprint
  - Owner: Travis (assigned Friday May 22)
  - Output: epics + stories organized so eng can pick up cleanly
- **Belt utilization + loading dashboards / UI mockups** for Wed data review
  - Travis project-manages the data review
  - Six datasets in play (per earlier conversation)
- **Belt lacing daily workflow** (Ravi handoff May 20)
  - Pull belt videos from S3 daily
  - Produce day-over-day comparison artifact showing line states
  - Format TBD — confirm with Ravi
- **Eng ↔ customer coordination per feature**
- *Source: Apurba May 20 PM, Ravi May 20 PM*

#### 2. Grafana / Libra chat evaluation (NEW — reassigned May 21)

- **Today (May 21):** finish Travis's light-yellow prompts in the shared spreadsheet
- A/B test: with vs without Sid's MCP skills documentation as context for the Grafana assistant
- Document desired vs actual responses; root-cause each failure (domain context? reasoning? query path?)
- **Tomorrow (May 22):** Libra chat eval — side-by-side vs Grafana chat
- Also flagged by Apurba to investigate: **Open Web UI**, **Onyx** (RAG + white-labeling)
- Long-term: could we build our own Libra-chat-based Grafana plugin and publish to Grafana plugin store?
- *Source: Apurba May 21 AM + PM*

---

### Quadrant 2 — High Importance / Lower Urgency

#### 3. Incident Response automation (Jerry's idea)

Operational alert engine with built-in resolution playbooks for plant operators.

- Define scope before June 6 Caglia workshop
- Parked for now — no action this week
- *Source: Apurba + Jerry May 19*

---

### Quadrant 3 — High Urgency / Lower Importance

#### 4. Central Compute document

- Polish Travis's draft + add visualization layer
- Package for review
- Target: this week (rough)
- *Source: Central Compute supply chain discussion May 19*

#### 5. Navigator MCP testing

- Continue Travis-side testing
- Roll out to broader team once Travis is confident
- **Scope constraint:** material/value data limited to Republic_Services account, 7-day time window, no `C108` conveyor label (see `references/reference_navigator_mcp_scope.md`)
- *Source: Apurba May 20*

#### 6. Weekly customer-status newsletter

- Cadence: weekly
- Draft and send
- *Source: Apurba May 20*

---

### Quadrant 4 — Low / Low (background, time-permitting)

#### 7. Navigator onboarding doc (internal non-technical)
- Recreated version
- Apurba: "leave that with me" — not Travis's to drive right now

#### 8. Navigator strategy document (internal technical)
- Owner TBD — confirm

#### 9. Vendor list document
- Can wait until after Thursday next week

#### 10. Use-case identification (robot upsell, others)
- Surface to team when patterns emerge

#### 11. Project Jetstream — Navigator internal rollout
- Continuation work

---

## Cross-cutting / dependencies

- **Avinash + Anish conversations needed (Tue May 26):**
  - Caglia engineering coordination
  - Claude account situation — Travis2 user or sales-account phone-verification fix (Travis is out of credits until Friday per May 21 meeting)
  - Libra Chat admin access (per Apurba's pointer)
- **Sid's MCP skills documentation:** pasted in Google Meet chat — extract and feed into Grafana assistant as A/B context
- **Fresno trip:** rescheduling, want Corey on-site next time. Apurba committed to regular visits.

---

## External / personal track (low priority but live)

| Status | Item |
|---|---|
| DONE Mon May 18 | LinkedIn Navigator launch post — posted |
| DONE Mon May 18 | Mylinda follow-up — sent |
| OVERDUE | Galguera mezcal case study — readability review (due 2026-05-18) |
| PENDING INFO | Project House Cleanup — Travis to share more |
| OPEN | Wayo loop check-in |
| OPEN | Conexum / Grafana chat thread |

---

## What I need from you next (to finish enrichment + daily breakdown)

### 1. Link drop into `links.md` (top priorities)

To enrich each task with actual state, I most need:

- Grafana chat eval spreadsheet (prompts + pass/fail)
- Grafana chat shareable links (your light-yellow attempts so far)
- Caglia JIRA epics + Confluence pages
- Belt lacing S3 bucket path
- Central compute draft
- Sid's MCP skills documentation (the Google Meet chat paste)
- Navigator internal rollout / Jetstream artifacts
- Project House Cleanup thread

### 2. Notion question

You mentioned organizing "based on Apurba's meeting and Notion." Two options:

- **(a)** Give me your Loose Tasks DB link — I'll read what's already there and merge, then mirror this map into Notion at the end
- **(b)** Keep planning here in markdown; I write to Notion only when you say so

### 3. House Cleanup context — share when you've got it

---

## What happens after enrichment

I produce a daily breakdown (Thu PM → Fri → Tue → Wed) with concrete deliverables per day, ending Wed May 27 with the data review locked and prepped.
