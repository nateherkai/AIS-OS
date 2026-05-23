# Week-of 2026-05-18 — Substrate (working doc, pre-plan)

Working substrate for /plan-my-week. Reflects grouping per Travis as of 2026-05-21. Status updates captured inline. This is NOT the final plan — Step 5 writes the canonical plan.

## Data model
Projects are first-class containers. Tasks live under projects. Deadlines optional. Rich context lives in the DB once unified DB design ships.

## WEEK-SHAPING BLOCKER
Most Claude-dependent tasks WAIT until Fri Claude credit reset → personal wiki ingestion (~2 hrs; needs remaining meetings added; requires knowledge).

**Startable now (Claude-independent):**
- Application Evaluation (Grafana, Libra, etc.)
- Vendor List creation
- Newsletter w/ Makenna

## EVEREST

### 🔵 Navigator Application — 5 projects

#### Project 1. MCP Testing (functional QA)
- Basic functionality validation
- A/B testing
- Scope constraint: Republic_Services only, 7-day window, no `C108` label
- *Volume blocker: Claude credits until Fri reset*

#### Project 2. Use Case Evaluation (capability check)
- Test whether MCP + current application architecture can facilitate execution of needed use cases
- Inputs: list of use cases worth validating (Robot Upsell is one)

#### Project 3. Application Evaluation (chat surface)
- Grafana light-yellow prompts *(in progress today)*
- Libra Chat side-by-side eval *(Apurba assigned for Fri)*
- Open Web UI investigation
- Onyx investigation
- A/B test Grafana w/ Sid's MCP skills doc
- Long-term option: build/own a Libra-Chat Grafana plugin
- *Claude-independent — can run NOW*

#### Project 4. Internal Rollout (Project Jetstream continuation)
*Sequenced 1 → 5 strictly. Depends on: outputs from Projects 1+2+3, AND Robot Upsell completing under Caglia as demo material.*

1. Internal onboarding doc (non-technical — only one, no separate technical version)
2. Travis onboarding gc update
3. Claude basics video tutorial
4. Project Jetstream email (internal AI readiness investigation + intro/get-up-to-speed-on-Claude)
5. Navigator Claude group chat setup

Notion AC entry "Navigator Internal Rollout" (due 5/20) is this workstream. Status: deadline was for plan locked, reevaluating on the go as dependencies move.

#### Project 5. Incident Response automation (Jerry's idea)
- Standalone, parked for later down the line
- Replace passive alerts with PIP-style guided workflows

#### Use-case identification
- **Initial round COMPLETE** (always ongoing background)

---

### 🟠 Caglia POC
*Wed May 27 data review is the customer anchor. Meetings are not tasks.*

- **JIRA epic/story restructure** — assigned Friday 5/22
- **Belt utilization + loading dashboards / UI mockups** — for 5/27 data review
- **Belt-lacing daily workflow** (Ravi handoff 5/20) — pull S3 videos, day-over-day comparison artifact
- **Belt slippage analysis** — Phase 1 motor fluctuation data, Phase 2 encoder ($2K/line)
- **Mass balancing project** — 8 commodities, 3-location vision strategy + landfill stream
- **2D/3D screen optimization** — down the line, no set date
- **Robot upsell** — sequencing: AFTER Navigator MCP testing, BEFORE Navigator internal rollout; produces a demo use case for the internal rollout

Mylinda follow-up — **DONE 5/18** (was a dependency under Internal Rollout, closed)

---

### 🟢 Central Compute
- Get Central Compute certification quote (~$10-15k additional; total projected $35-40k)
- Build certification matrix (Confluence customer-facing + internal spreadsheet)
- Replace Daniel Schmidt as Fanuc contact for ISO 10218-2

### 🟣 Customer Comms
- Weekly customer status + industry news newsletter (w/ Makenna) — *Claude-independent, startable now*

### ⚪ Operational
- Vendor list creation (can wait until after next Thursday) — *Claude-independent, startable now*

### 🔘 Cross-cutting (awareness/calendar — NOT assignments)
- Twice-weekly PM↔Eng check-ins (calendar; status prep when assignments are due)
- POC stakeholder meeting cadence (not established yet, will be done)
- Three-month release cycle (frame: Planning M-2 → Execution M-1 → Field test M; Alpha → Beta) — fit workstreams within
- *(removed: JIRA workspace consolidation — not owned by Travis)*

---

## ACADEMIC

### INMI0300 close-out (consolidated, one workstream)
*Travis: "on my mind for review, will do thorough analysis on whether worth doing."*

- Req 2: Library Module (~1.5-2h) — overdue 53 days
- Req 3a: Faculty Research Conversation — overdue 48 days
- Req 3b: Event Reflections + Req 3 Write-up — overdue 41 days
- Req 4: Final Reflection + Badge Quiz (~1h) — overdue 34 days, blocked by Reqs 1-3

---

## BIGSCHOLARS — *parked, to be reevaluated*
- Analyze NEU finance officer meeting + store insights
- LLM credits (startup-credits-playbook)
- Organize docs + business plan

---

## CAREER

### Profile cluster (sequenced after LinkedIn post — DONE 5/18)
- LinkedIn profile update
- Resume update
- Personal website update

### Standalone Career
- LinkedIn post: Sales/Ops → GTM — **DONE 5/18** (needs Notion close)
- Ansara blog review outreach (Rhami, Andrey, Josh; Tasmin ↔ Paul Singh) — independent
- LinkedIn endorsements plan — Deferred to Aug per Naeem
- Next summer's job (Summer 2027) planning — aspirational
- Naeem summer email cadence — Deferred (milestone-based)
- BigScholars (parked, will reevaluate): NEU finance officer analysis, LLM credits, docs + business plan

---

## FAMILY (was Self & Spaces)
- **Project House Cleanup** — In progress, top of backlog; plan in separate Claude project
- Family finances + Morgan Stanley conversation (prep this week, not the convo)

---

## PERSONAL (broader; absorbed Galguera + Personal Enrichment)

### Personal Enrichment (sub-group)
- Course backlog Summer 2026 (CV Tutorials, Parking Lot CV, Ken's Thought Leadership, NEPQ Sales, OMGYes)
- Real World Crypto course catch-up
- Journal club exploration (aspirational)

### Personal core
- Galguera mezcal case study read + feedback — hard wall was May 4, **VERY overdue**, needs decision
- Sadie apology text (overdue, was bucketed Fri May 1)
- Coach Enrique re: summer XC
- Sister tutoring on econ + Claude research (Deferred)
- Philosophy article — Five-Year-Old PhD Babies (Deferred)
- HS friends summer regroup (Deferred — wait until late May UC / early June CC)

---

## ADMIN
- Firestore billing dispute / RealEstateAPI cancel — **bleeding $38.27/mo since Aug 2025, $309+ total**, marked Deferred but probably shouldn't be
- Set up personal credit card (Deferred)

---

## Cross-pillar dependency spine

```
{ MCP Testing + Use Case Eval + Application Eval }
       (3 parallel Navigator projects)
                ↓
   Robot Upsell (Caglia → Navigator demo asset)
                ↓
       Internal Onboarding Doc (non-tech)
                ↓
       Internal Rollout (1→5 sequential)
```

## Meta — Open thread
Travis flagged: restructure Loose Tasks + Academic Calendar into ONE unified Notion DB. Projects are first-class; tasks live under them; deadlines optional; rich context in DB. Tackle after this week's plan ships.
