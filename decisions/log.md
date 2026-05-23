# Decisions Log

Append-only record of meaningful decisions and why they were made. `/level-up` Phase 2 (Method interview) writes scoped automation specs here. You can also append manually whenever you decide something worth remembering.

**Format per entry:**

```
## YYYY-MM-DD — Short title

**Decision:** what was decided.

**Why:** the reasoning, constraints, and what would change your mind.

**Alternatives considered:** what else was on the table.

**Owner:** who's accountable.
```

Keep it terse. Future-you will thank present-you for capturing the *why*, not just the *what*.

---

## 2026-05-19 — `/level-up` run: Granola → Personal Brain wiki ingest workflow

**Decision:** Ship `references/granola-mcp.md` as the prompt-only artifact for ingesting Granola meetings into the Personal Brain wiki. Autonomy L2 (Drafted) — Claude drafts the source page and touched updates; Travis reviews at two pause points per meeting in the interactive ingest loop.

**Method (5-step Method pipeline):**

- *Constraint*: doc-scatter — no unified access to Everest meeting context across Granola / Drive / Salesforce / Flock. Granola was the highest-leverage starting connector because 51 Everest meetings live there.
- *EAD*: Automate. Eliminate rejected — meetings are already recorded and valuable. Delegate rejected — no other human bandwidth.
- *Process map*: Trigger = backlog ingest or specific recall. Data source = 4 Granola MCP tools via Composio. Transformations = query → format → write raw → run wiki INGEST per `Personal Brain/CLAUDE.md` §4a. Decision points = which Granola tool, confidentiality, page-vs-mention, grouping. Destination = `Personal Brain/raw/meetings/` then `wiki/sources/`.
- *Autonomy*: L2.
- *KPI*: Bucket = less cost (Travis's time). Metric = time to recall meeting context — seconds via wiki query vs minutes hunting in Granola directly.

**Machine:** Prompt-only (Boring-is-Beautiful option 1). Reference doc + an interactive ingest-loop prompt for a separate Claude chat to drive the wiki repo session-by-session.

**Why:** Granola is the rawest source of Everest meeting context and the wiki schema's INGEST workflow was already designed for it. Pattern is reusable for Fireflies and any future meeting sources.

**Alternatives considered:**
1. Deterministic skill that fully automates ingest — rejected; too much judgment per source (confidentiality calls, page-vs-mention, conflict resolution).
2. Skip the reference doc and just exercise tools ad-hoc — rejected; future agents would re-discover the same gotchas.
3. Start with Calendar instead — rejected; Granola is closer to Travis's stated top pain (chasing things down).

**Owner:** Travis.

---

## 2026-05-19 — `/level-up` run: Fireflies → Personal Brain wiki ingest workflow

**Decision:** Ship `references/fireflies-mcp.md` as the prompt-only artifact for ingesting Fireflies meetings (Everest channel) into the wiki. Same L2 autonomy as Granola; the existing interactive ingest-loop prompt covers both sources.

**Method (5-step Method pipeline):**

- *Constraint*: 5 Everest-channel Fireflies meetings (Avinash data pipeline x2, JIRA Structure, Grafana/CADLIA Project Update, Grafana Assistant Evaluation) are siloed and not queryable from the wiki. Closes Everest coverage from 5/56 to 10/56 once ingested.
- *EAD*: Automate. Same rejection logic as Granola.
- *Process map*: Trigger = same as Granola. Data source = Composio Fireflies tools (`GET_TRANSCRIPT_BY_ID`, `GET_TRANSCRIPTS`, `CREATE_ASK_FRED_THREAD`). Transformations = list → client-side filter on `channels[0].id === "6a0c1cec7610454b44024df2"` → format speaker labels (named or anonymized) → write raw → run wiki INGEST. Decision points = same as Granola plus channel filter, auto-title overrides, null-sentences handling. Destination = same.
- *Autonomy*: L2.
- *KPI*: Bucket = less cost. Metric = coverage % (Everest meetings ingested / total across Granola + Fireflies).

**Machine:** Prompt-only. Same Boring-is-Beautiful default; same reasoning.

**Why:** Fireflies catches what Granola misses for Everest work (architecture + engineering meetings in May 2026). Without the parallel reference doc, agents re-derive the channel filter pattern, null-sentence handling, and auto-title problem on every session.

**Alternatives considered:**
1. Build a generic "meeting source" abstraction covering both Granola and Fireflies — rejected; the two APIs differ enough (channel model vs no channel, summary shape, speaker labeling) that the abstraction would leak immediately.
2. Defer Fireflies until all Granola is ingested — rejected; Fireflies-only meetings on May 4 and May 15 are operationally important now (data pipeline, JIRA, Grafana).

**Owner:** Travis.

---

## 2026-05-19 — `/level-up` run: Google Calendar → AIOS query reference

**Decision:** Ship `references/googlecalendar-mcp.md` as the prompt-only artifact for Google Calendar workflows. Autonomy L1 (Suggested) — Claude pulls calendar data, Travis decides what to do with it (no automation runs Calendar in the background yet).

**Method (5-step pipeline):**
- *Constraint*: pre-meeting context rebuild costs minutes per meeting. Without programmatic Calendar access, Travis manually opens Calendar / Granola / wiki for each meeting.
- *EAD*: Automate.
- *Process map*: Trigger = morning brief or 30-min-before-meeting. Data source = Composio Google Calendar tools across two accounts (`travis-everestlabs` default, `travis-personal` secondary). Transformations = list events → extract attendees → enrich from wiki. Decisions = which account, single vs all-calendars query, recurring vs instances. Destination = pre-meeting brief (output only; no wiki write).
- *Autonomy*: L1.
- *KPI*: Bucket = less cost. Metric = time-to-context-readiness before a meeting.

**Machine:** Prompt-only. Reference doc with multi-account flagged (default `travis-everestlabs` — opposite of Gmail).

**Why:** Calendar is foundational for the pre-meeting briefer, Calendar↔Granola cross-check, and week-ahead Everest meeting roll-ups. Cheap to wire; high-leverage downstream.

**Alternatives considered:**
1. Deterministic skill for the pre-meeting briefer — deferred; needs Calendar + wiki + Granola query orchestration that's better proven manually first.

**Owner:** Travis.

---

## 2026-05-19 — `/level-up` run: Gmail → AIOS query reference

**Decision:** Ship `references/gmail-mcp.md` as the prompt-only artifact for Gmail workflows. Autonomy L1.

**Method (5-step pipeline):**
- *Constraint*: email context is scattered across two accounts (work + personal). Travis manually searches for specific threads. Project Jetstream label already exists for the work account but isn't being queried programmatically.
- *EAD*: Automate.
- *Process map*: Trigger = catch-up scan, specific person lookup, or surname resolution. Data source = Composio Gmail tools (`travis-everestlabs` for work, `travis-personal-gmail` for personal). Transformations = query construction → metadata-first list → selective full hydration → base64url decode of body parts. Decisions = which account, `label_ids` vs `label:` in query, verbose vs metadata-only. Destination = wiki ingest (when email is the source) or context for other workflows.
- *Autonomy*: L1.
- *KPI*: Bucket = less cost. Metric = time-to-find-thread + surname/people-data fill rate against open wiki questions.

**Machine:** Prompt-only. Reference doc with strong emphasis on the default-account gotcha (Gmail default is personal — opposite of Calendar/Drive).

**Why:** Gmail surfaces Drive doc links from email threads (e.g., Apurba's May 13 "POC background materials" email — the entry point for proposal Drive IDs), produces surname resolutions cheaply, and the Project Jetstream label is a curated scoping mechanism that beats `subject:jetstream` queries.

**Alternatives considered:**
1. Build a deterministic skill that auto-classifies inbox emails into wiki-actionable buckets — deferred; needs human-in-the-loop on classification calls until the pattern is proven.

**Owner:** Travis.

---

## 2026-05-19 — `/level-up` run: Google Drive → AIOS query reference

**Decision:** Ship `references/googledrive-mcp.md` as the prompt-only artifact for Google Drive workflows. Autonomy L1.

**Method (5-step pipeline):**
- *Constraint*: doc-scatter — Customer Deployment Dashboard, POC proposals (Caglia/Republic/Circular), the onboarding doc Travis is writing — all in Drive without consolidation. Travis must remember each file's URL.
- *EAD*: Automate.
- *Process map*: Trigger = ingest a doc as a wiki source, pull deployment dashboard snapshot, or refresh proposal context. Data source = Composio Drive tools across two accounts (`travis-everestlabs` default; `travis-personal` rarely). Transformations = JQL-style search → metadata check → export-as-format (markdown for Docs, CSV for Sheets, plain text for Slides). Decisions = native download vs Workspace export, mimeType targeting, sharedWithMe vs owned. Destination = `Personal Brain/raw/proposals/` and `raw/data/` parallel to `raw/meetings/`, then wiki INGEST.
- *Autonomy*: L1.
- *KPI*: Bucket = less cost. Metric = number of doc-driven facts in the wiki / total Drive sources referenced in conversation.

**Machine:** Prompt-only. Reference doc with known-resources table (Customer Deployment Dashboard ID, etc.) and use-case-specific query patterns.

**Why:** Drive is the data layer below most wiki content. Without programmatic access, doc-scatter persists.

**Alternatives considered:**
1. Build a "Drive folder watcher" that auto-ingests new POC docs into the wiki — deferred; requires defining what "POC doc" means programmatically.

**Owner:** Travis.

---

## 2026-05-19 — `/level-up` run: JIRA (Atlassian) → AIOS query reference

**Decision:** Ship `references/jira-mcp.md` as the prompt-only artifact for JIRA workflows. Autonomy L1. **Includes a wiki-correction note** because the data contradicts a prior wiki claim ("team not yet active on JIRA").

**Method (5-step pipeline):**
- *Constraint*: POC dependency tracking and weekly status briefing both require querying JIRA. Wiki's prior claim that the team wasn't on JIRA was wrong — POC project alone has 34+ issues with Travis as assignee on POC-6, POC-14, POC-19; active churn within the last 24 hours.
- *EAD*: Automate.
- *Process map*: Trigger = weekly POC status, pre-meeting brief, "what did Apurba assign me," surfacing engineering dependencies for a customer-feature. Data source = Atlassian MCP (`mcp__claude_ai_Atlassian__*`) — not Composio — with constant `cloudId: "e830597d-ffd6-4aed-a34b-e0bbb574db04"`. Transformations = narrow JQL query → markdown response → field extraction. Decisions = which project to scope to, `responseContentFormat: "markdown"` vs `"adf"`, when to follow `issuelinks` chains. Destination = status brief output or wiki cross-reference notes on customer pages.
- *Autonomy*: L1.
- *KPI*: Bucket = less cost. Metric = time to resolve "why isn't this feature ready" via dependency walk.

**Machine:** Prompt-only. Reference doc includes the 13 Jira projects, the load-bearing four (POC, NAV, L2, ENG), and load-bearing JQL patterns. Also flags that the same Atlassian connector exposes Confluence with read/write — deserves its own future `/level-up` for `references/confluence-mcp.md`.

**Why:** JIRA is the operational truth layer below the wiki. Wiki captures why; JIRA captures what's open and what's blocking. Combined they answer the questions Apurba and the team are most likely to ask.

**Alternatives considered:**
1. Use Composio's Atlassian integration instead of Anthropic's claude.ai Atlassian connector — rejected; the claude.ai Atlassian connector is already wired with both Jira and Confluence scopes on Travis's account.
2. Defer JIRA until the team is more active — rejected; the team is already active. The wiki was stale on this point.

**Owner:** Travis.
