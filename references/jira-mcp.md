---
bike-method-phase: 1  # Phase 1 — Training wheels. Run manually first.
three-ms-attribution: |
  Adapted from The Three Ms of AI™ © 2026 Nate Herk.
---

# JIRA (Atlassian) MCP — reference for the AIOS

JIRA is reached through the Atlassian MCP server (`mcp__claude_ai_Atlassian__*`) — a separate connector from Composio. The same connector also exposes **Confluence**, with read/write scopes for both products on Everest's site.

## Connection facts (constants)

- **Cloud ID:** `e830597d-ffd6-4aed-a34b-e0bbb574db04`
- **Site URL:** `https://everestlabs.atlassian.net`
- **Authenticated user:** Travis Peng (`travis@everestlabs.ai`), Associate GTM Intern, Operations team. Atlassian account created 2026-02-02.
- **Scopes:**
  - Jira: `read:jira-work`, `write:jira-work`
  - Confluence: `read:page`, `write:page`, `read:comment`, `write:comment`, `read:space`, `read:confluence-user`, `search:confluence`

Pass `cloudId` on every Jira/Confluence call. Don't hardcode it in callers; reference it from this doc (or call `getAccessibleAtlassianResources` once to verify if it changes).

---

## How Jira is used at Everest (org context)

The Jira structure at Everest is being **formalized in real time as of 2026-05-19** by Apurba with the engineering core (Anish, Ravi, Sid). The wider POC team isn't on this structure yet — broader adoption + onboarding is mid-flight and is on Travis.

### Two active workspaces

| Workspace | Board type | Sprint cadence | What lives here |
|---|---|---|---|
| **Navigator (`NAV`)** | Scrum | Two-week sprints | All Navigator product engineering work. ~6 epics covering line / process / plant levels (4 boxes each). Stories ≤ 4 story points (≤ 2 weeks). |
| **POC (`POC`)** | Kanban | Continuous | Customer-facing POC work. **One epic per customer** (Caglia, Circular Services, RSG OEE, etc.) with stories + subtasks underneath. Travis's home base. |

**`L2` is being deprecated** in favor of Navigator. Was set up as Kanban and Apurba needed Scrum for the release cycle; rather than convert, he stood Navigator up fresh. Don't write new tickets to L2; existing L2 work is being migrated.

### Issue hierarchy

`Epic → Story → Sub-task`. Bugs are treated as Stories (same hierarchy level, just labeled). Stories should be ≤ 4 story points (~15 days / 2 weeks max). If bigger, break into multiple stories under the same epic.

### Status workflow (as of 2026-05-19)

Five statuses on the Navigator scrum board:

| Status | Means |
|---|---|
| **To Do** | Accepted into a sprint but not started. |
| **In Progress** | Actively being worked. |
| **In Review** | Implementation done, waiting on review / sign-off. (Added 2026-05-19.) |
| **Hold** | Blocked by something the assignee can't unblock alone. Can sit here indefinitely. (Added 2026-05-19.) |
| **Done** | Implemented + unit-tested + accepted. Definition-of-done required at end of green planning phase (see release cycle below). |

### Release cycle (3-month staggered, monthly cadence)

Each release moves through three monthly phases:

| Phase | Color | What happens | Vocabulary |
|---|---|---|---|
| **Plan** (month 1) | green | Apurba/PM hands requirements; engineering scopes, architects, picks technologies, defines done. Output: committed feature list + DoD for each. | "Green box" |
| **Execute** (month 2) | yellow | Coding, unit testing, internal demo at the end. PM clarifications minimized. | "Yellow box" / **alpha** (Everest-side) |
| **Field QA** (month 3) | blue | Deploy at customer site, gather feedback, fix issues, finalize. Engineering moves on to next release's execute phase while this runs. | "Blue box" / **beta** (customer-side) |

Cycles **stagger** — every month, the team is simultaneously planning release `N+2`, executing `N+1`, and field-testing `N`. As of May 2026: planning July release + executing June release + field-QA May release.

End of each phase has a deliverable:
- **End of green:** committed feature list with definition-of-done.
- **End of yellow:** internal demo of the alpha. UI is part of every demo plan.
- **End of blue:** customer-ready ship.

### Commitment discipline

Engineering changes commitments only **once a month** (at planning). Mid-month replanning should be < 10% of the time — only for exceptional events ("Apurba just signed Ecology and we need X now" or "we started Grafana and it's the wrong tech"). Otherwise: lock the commitment, ship the commitment.

### Cross-project dependencies

When POC needs work in NAV / ENG / another team's Jira:

1. Create the dependency as an `is blocked by` link between the POC issue and the upstream issue.
2. **Don't mirror tickets across projects.** One source of truth per piece of work; link instead.
3. **The owner of the upstream issue owns the conversation.** If Travis's POC ticket is blocked by a NAV ticket, Travis goes to whoever owns the NAV ticket.

This is the model Apurba designed and that the team is just now standing up.

### Check-ins

Two recurring forums (being formalized):

- **Navigator sync** — engineering core (Anish, Ravi, Sid, + Travis for cross-link visibility). Weekly. Discuss Navigator scrum board state.
- **POC sync** — Travis + customer-side stakeholders. Weekly, 15 minutes. Discuss the POC kanban board.

Apurba and Avinash join either as needed; their tickets show up via `is blocked by` links.

### Adoption status

- **On the structure (as of May 19):** Anish, Ravi, Sid, Travis. Engineering core.
- **Not yet on:** wider engineering (Valeria, Purvang, others maintain their own jiras elsewhere — linked in as dependencies but not yet sprint participants); broader POC team / customer-side counterparts.
- **Onboarding others is on Travis** for the POC side. Until that's done, JQL queries that try to walk the full POC → engineering dependency chain will hit gaps.

---

## Projects (Jira — Everest's instance has 13)

| Key | Name | Type | What it tracks |
|---|---|---|---|
| `POC` | POC | software | **Travis's home project. Kanban.** POC features (Caglia, Republic OEE, Circular Services) — one Epic per customer with Stories tagged by priority (P1, etc.) and Subtasks for HW val / HW deploy / model fine-tune / data dashboard. Travis is assignee on multiple. |
| `NAV` | Navigator | software | **Active Navigator product workspace. Scrum, 2-week sprints.** Set up 2026-05-19 to replace L2. ~6 epics covering line/process/plant levels. Tasks / Bugs / Stories / Epics / Subtasks. |
| `L2` | L2: Vision & Data Capabilities | software | **Deprecating** as of 2026-05-19. Was Kanban; Apurba needed Scrum for the new release cycle so Navigator was stood up fresh instead of converting. Existing L2 work being migrated; don't write new tickets here. |
| `ENG` | Engineering | software | Engineering team's general work. Tasks + Epics + Subtasks. |
| `CORE` | Core | software | Core platform work. Tasks + Bugs + Epics + Subtasks. |
| `CI` | Customer Installations | business | Customer deployment tracking. Full issue type set (Task / Story / Bug / Epic / Sub-task). |
| `PI` | Product Installations | software | Product-side install tracking. |
| `PB` | Production Builds | software | |
| `POI` | Production Open Issues | software | |
| `RR` | R&D Robot | software | Robot R&D. |
| `DPUC` | Deployment Process - Under Construction | business | Process development. |
| `PART` | Partnerships | software | |
| `WT` | Web Tools | classic | Older classic-style project. |

**For Travis's daily work**, the load-bearing projects are `POC` (home), `NAV` (cross-link target for engineering dependencies), and (less so) `ENG`. `L2` is on its way out.

---

## When to use which tool

| If the question is… | Use | Why |
|---|---|---|
| "Find issues matching <criteria>" | `searchJiraIssuesUsingJql` with a JQL query | Full JQL power. Specify `fields` to control response size. Default `responseContentFormat: "markdown"` is cheaper than ADF. |
| "Get one issue's full state" | `getJiraIssue` with `issueIdOrKey` | Key like `POC-6` or numeric ID. Use `responseContentFormat: "markdown"` for descriptions/comments. |
| "List visible projects" | `getVisibleJiraProjects` with `action: "view"` | Includes `issueTypes` per project. Useful to discover Epic / Story / Subtask IDs for project-specific creation. |
| "What can I transition this issue to?" | `getTransitionsForJiraIssue` then `transitionJiraIssue` | Workflow-aware. Don't guess transition IDs. |
| "What issue link types exist?" | `getIssueLinkTypes` then `createIssueLink` | Use for the "POC depends on engineering" link Apurba described. |
| "Look up someone by name → accountId" | `lookupJiraAccountId` | Needed to filter by `assignee = "<accountId>"`. |
| "Add a comment" | `addCommentToJiraIssue` with `responseContentFormat: "markdown"` | Write a markdown comment; ADF is auto-converted server-side. |
| "Log work" | `addWorklogToJiraIssue` | Time tracking; minor for Travis's workflow but available. |
| "What can I currently transition issues to?" | `getJiraProjectIssueTypesMetadata` | Useful before `createJiraIssue` to know required fields per type. |

**Default chain for POC status briefing:**
`searchJiraIssuesUsingJql` with `jql: "project = POC AND assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated DESC"` → for each interesting result, `getJiraIssue` (markdown) for the full state.

**Default chain for surfacing dependencies on a customer-feature:**
`getJiraIssue` for the feature → check `issuelinks` field → for each linked engineering issue, `getJiraIssue` to see status.

---

## JQL essentials Travis will actually use

```
# My open POC work
project = POC AND assignee = currentUser() AND statusCategory != Done

# This week's activity across Travis's projects
(project = POC OR project = NAV) AND updated >= -7d ORDER BY updated DESC

# Recently created — what's new
project = POC AND created >= -7d ORDER BY created DESC

# Feature-level (Stories only) in POC
project = POC AND issuetype = Story ORDER BY priority DESC

# Search Caglia-related issues across all projects
text ~ "Caglia" ORDER BY updated DESC

# Issues blocking a specific issue
issue in linkedIssues("POC-6", "is blocked by")

# Open P1 issues
labels = "P1" AND statusCategory != Done

# Apurba assigned
assignee = "<apurba's accountId from lookupJiraAccountId>" AND updated >= -14d
```

---

## Critical gotchas

- **`searchJiraIssuesUsingJql` output can be huge.** A broad query (`updated >= -30d` across all projects) overflows the response limit and spills to a file on disk. Always narrow with `project = X`, `assignee = ...`, or `updated >= -7d`. Use `maxResults` (cap 100) and `fields` array to control size.
- **Use `responseContentFormat: "markdown"` for descriptions/comments.** Default ADF (Atlassian Document Format) is structured JSON — fidelity is higher but token cost is ~3x. Reserve ADF for when you specifically need to preserve formatting for a write-back.
- **Pagination via `nextPageToken`.** Pass it back as `nextPageToken` argument until `isLast: true` or token absent.
- **Project keys are case-sensitive in some contexts.** Always use UPPERCASE in JQL: `project = POC` not `project = poc`.
- **`assignee = currentUser()`** is the cleanest filter for "my work." Avoids hardcoding `accountId`. But for "filter by other person," you must look up their `accountId` first via `lookupJiraAccountId`.
- **Status vs statusCategory.** `status = "Done"` matches exact status names; `statusCategory = Done` matches all done-category statuses (Done, Closed, Resolved, etc.). Prefer `statusCategory` for "anything done" filters. Navigator status set (2026-05-19): `"To Do"`, `"In Progress"`, `"In Review"`, `"Hold"`, `"Done"`. `In Review` and `Hold` map to `statusCategory = "indeterminate"`.
- **Issue types vary by project.** Each project has its own issue type IDs (visible via `getVisibleJiraProjects` with `expandIssueTypes: true`). Don't pass an issue type ID from POC to a NAV `createJiraIssue` call.
- **Labels.** Multi-value. `labels = "P1"` to filter; case-sensitive. P1, P2 visible so far.
- **`addCommentToJiraIssue` / `editJiraIssue` are write ops.** AIOS is read-only by default. Only use when explicitly authorized by Travis.

---

## Use cases

### 1. Weekly POC status brief

Friday afternoon: pull all POC project changes from the past week, grouped by status category. Feeds the Friday review and Sunday plan-the-week.

```jql
project = POC AND updated >= -7d ORDER BY status, updated DESC
```

### 2. Pre-meeting briefer (POC sync)

Before a POC-related meeting, pull the relevant feature epics and their subtasks:

```jql
project = POC AND (key = POC-6 OR parent = POC-6)
```

Combined with wiki context from `wiki/customers/<customer>.md`, produces a one-pager.

### 3. Surface dependencies (the Apurba workflow)

Per the May 13 onboarding meeting, the work model is: customer-facing feature epics in POC, with explicit `depends on` links to engineering issues in ENG / L2 / NAV. To answer "why isn't this feature ready":

```
getJiraIssue("POC-<n>") → check issuelinks → for each "is blocked by" link, getJiraIssue on the target
```

### 4. "What did Apurba assign me this week"

```jql
project in (POC, NAV) AND reporter = "<apurba_accountId>" AND assignee = currentUser() AND created >= -7d
```

Surfaces new assignments without trawling email.

### 5. Cross-reference customer-feature with Granola/Fireflies meetings

When ingesting a customer meeting into the wiki:
- After identifying the customer (e.g., Caglia), JQL search `text ~ "Caglia" AND project = POC` to surface the POC issues that meeting probably touches.
- Cross-link in the wiki source page: cite the POC issue key alongside the meeting transcript.

### 6. Wiki freshness — JIRA adoption is mid-flight, not binary

The wiki and intake answer say "team not yet active on JIRA." The truth as of 2026-05-19 is more nuanced:

- **Engineering core (Anish, Ravi, Sid, Travis) is on the new structure** — actively churning issues; POC project alone has 34+ issues; Travis is assignee on POC-6, POC-14, POC-19 and others.
- **Wider engineering** (Valeria, Purvang, others) is on Jira but not yet integrated into the new sprint cadence — their tickets get linked in as `is blocked by` dependencies only.
- **POC team / customer-side counterparts** are not on the structure at all yet; Travis is onboarding them.

When updating `wiki/concepts/everest-labs.md`, reflect the rollout-in-progress framing rather than picking a side of "active vs not." See `connections.md` for the same nuance.

---

## Issue structure quick reference

Fields most commonly used (Markdown response format):

```
key                          # POC-6, NAV-12, etc.
id                           # Numeric internal ID
summary                      # Short title
description                  # Body (markdown or ADF depending on responseContentFormat)
status.name                  # "To Do", "In Progress", "Done", custom names
status.statusCategory.key    # "new" | "indeterminate" | "done"
issuetype.name               # "Task" | "Story" | "Bug" | "Epic" | "Subtask"
priority.name                # When set
assignee                     # null or {accountId, displayName, emailAddress, timeZone}
reporter                     # Same shape as assignee
created                      # ISO timestamp
updated                      # ISO timestamp
labels[]                     # Array of label strings — Travis's instance uses P1, etc.
parent                       # For subtasks, the parent issue key
issuelinks[]                 # Array of {type, inwardIssue / outwardIssue} for dependencies
```

---

## Confluence — same connector, separate workflow

The Atlassian MCP also exposes Confluence (read/write pages, comments, search). The wiki names Confluence as the SE-team-owned authoritative per-MRF data source (mentioned in [[2026-03-04-brian-proposal-gen]]). Worth exercising when Travis needs per-MRF context that the wiki doesn't yet capture.

Confluence tools available (not yet exercised here):
- `mcp__claude_ai_Atlassian__getConfluenceSpaces`
- `mcp__claude_ai_Atlassian__searchConfluenceUsingCql`
- `mcp__claude_ai_Atlassian__getConfluencePage`
- `mcp__claude_ai_Atlassian__getPagesInConfluenceSpace`
- `mcp__claude_ai_Atlassian__getConfluencePageDescendants`

These deserve their own session pass — defer for now. Worth a future `references/confluence-mcp.md`.

---

## Cross-reference with Personal Brain

JIRA is the operational layer below the wiki:

- **Wiki captures the why, who, and decision context.** Customer pages, person pages, decisions log entries.
- **JIRA captures the what, when, and dependency state.** Issues, status, transitions, links.

When updating a wiki customer page (e.g., [[republic-services]]), include a section "JIRA references" with the POC and NAV issue keys most relevant — links survive wiki re-renames but stay actionable. (Don't reference L2 keys going forward; that project is being deprecated.)

When ingesting a Granola meeting that produces commitments ("Travis will set up X, Aneesh will fix Y"), consider whether new JIRA issues should be created (in the appropriate project) and link them back in the wiki source page.

---

## Tools not yet exercised

- `getJiraIssueRemoteIssueLinks` — external links on an issue (e.g., to Confluence pages, Drive docs). Useful when a customer-feature epic links to its proposal deck.
- `getJiraIssueTypeMetaWithFields` — full creation schema for an issue type. Useful before `createJiraIssue` if defaults aren't clear.
- `getTransitionsForJiraIssue` + `transitionJiraIssue` — workflow transitions. Read-only AIOS unless Travis authorizes writes.
- `addWorklogToJiraIssue` — time tracking. Not currently used by Travis.

---

## Confidentiality cross-reference

JIRA issue data (customer names, feature scope, dependency state) is internal. When derived content goes into the wiki, default to `confidential: internal` on pages that quote JIRA descriptions or restate customer-feature state.
