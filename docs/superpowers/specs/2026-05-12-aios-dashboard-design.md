# AIS-OS Dashboard — Design Spec
**Date:** 2026-05-12
**Owner:** Bryan Aaron
**Status:** Approved for implementation

---

## Overview

A local web dashboard that gives Bryan a single-screen view of every dollar in and out of Ag Coach Pro, plus live pipeline status and quick-launch buttons for his AIOS skills. Runs on his MacBook. Opens in browser with one command.

**Litmus test:** Bryan opens his laptop in the morning, runs one command, and knows his net position, which trials are going cold, and what to do first — without logging into Stripe, Supabase, Gmail, or any other tool separately.

---

## Architecture

### Stack
- **Backend:** Python (FastAPI or simple http.server)
- **Frontend:** Single HTML file with vanilla JS — no framework
- **Data refresh:** Backend fetches live data on page load; auto-refreshes every 5 minutes
- **Launch:** `python3 dashboard/server.py` → opens http://localhost:8080

### Data Sources

| Source | Mechanism | Refresh |
|--------|-----------|---------|
| Supabase (schools/trials) | Python script via REST API | On load + 5min |
| Stripe (invoices) | Python script via stripe-python | On load + 5min |
| Apple Card CSV | File import (`dashboard/imports/apple-card-*.csv`) | Manual export monthly |
| Gmail receipts | Gmail API — search for charge emails | Daily cron or manual trigger |
| Manual expenses | `dashboard/data/expenses.json` — edited directly | On save |
| Tasks | `dashboard/data/tasks.json` — persisted locally | On save |
| Debt tracker | `dashboard/data/debt.json` — persisted locally | On save |

### File Structure
```
AIS-OS/
└── dashboard/
    ├── server.py           ← Python server + API endpoints
    ├── index.html          ← Frontend (single file, dark glass UI)
    ├── data/
    │   ├── expenses.json   ← Manual + parsed expense list
    │   ├── tasks.json      ← Today's focus tasks
    │   └── debt.json       ← Debt payoff log
    ├── imports/
    │   └── apple-card-*.csv ← Drop CSV here, server auto-parses on load
    └── scripts/
        ├── parse_apple_card.py   ← CSV parser → updates expenses.json
        └── parse_gmail_receipts.py ← Gmail API → updates expenses.json
```

---

## UI Design

### Layout
- **Command Center** — fixed left sidebar (220px) + scrollable main area
- Dark glass aesthetic: `#050510` background, `rgba(255,255,255,0.04)` glass panels, gold `#D4A574` accents, navy `#001F4D`
- Matches Ag Coach Pro brand exactly

### Sidebar
- Logo mark (AC) + "Ag Coach Pro / Business OS"
- Nav: Dashboard, Revenue, Schools, Expenses, Inbox
- Skills section: Run Pipeline Check, Draft Reply, Trial Follow-Up (buttons that open skill modals)
- Bottom: live burn / revenue / net summary

### Main Panels (7 total)

#### 1. Net Income Banner
- Full-width alert bar: current net (revenue − expenses)
- Red when negative, green when positive
- Note: "X more schools to break even"

#### 2. KPI Row (4 cards)
- Monthly Revenue (with % progress to $10K/mo goal)
- School Goal (paid count / 50, progress bar)
- Monthly Burn (total expenses)
- Active Trials (count + school names)

#### 3. School Pipeline (live)
- All schools from Supabase (excluding seed data)
- Green dot = paid, yellow = trial
- Click row → modal with advisor details + "Draft Email" button
- Shows days in trial for each trial school

#### 4. Monthly Expenses
- Bar chart per service, sorted by amount
- Pulls from `expenses.json` (populated by Apple Card CSV + Gmail parser)
- Total burn shown in panel header

#### 5. Inbox Triage (Gmail)
- Last 5 unread emails from school advisors
- Click → marks read, shows "Draft Reply" button
- "Draft Reply" opens modal with instructions to run `/draft-reply` in Claude Code

#### 6. Today's Focus (Tasks)
- 3 tasks, click to check off
- Persisted to `tasks.json` (survive page refresh)
- Counter: X/3 done
- Edit tasks inline (click text to edit)

#### 7. Debt Payoff Tracker + AI Credits
- Log a payment → updates running total and progress bar toward goal
- Progress bar toward debt-free (goal: Dec 31, 2026)
- AI credit usage per school (pulled from Supabase token tracking)

---

## Expense Auto-Update

### Apple Card CSV Import
1. Bryan exports CSV from Wallet app (monthly, ~2 min)
2. Drops file in `dashboard/imports/`
3. Server auto-detects new CSV on next load
4. `parse_apple_card.py` matches vendors to known services:
   - "ANTHROPIC" → Claude API
   - "OPENAI" → ChatGPT / OpenAI API
   - "GOOGLE" → Google Workspace / Gemini
   - "VERCEL" → Vercel
   - "SUPABASE" → Supabase
   - "MAILERLITE" → MailerLite
   - "FIRECRAWL" → Firecrawl
   - "FAL" → Fal.ai
5. Updates `expenses.json` with actual amounts
6. Unknown vendors flagged for manual review in UI

### Gmail Receipt Parser
- Searches Gmail for: `subject:(receipt OR invoice OR charge) from:(anthropic OR openai OR google OR vercel OR supabase OR mailerlite)`
- Parses amount from email body
- Updates `expenses.json` for matched vendors
- Runs on demand via "Sync Receipts" button in Expenses panel

---

## Skill Buttons (read-only — no Claude Code required in browser)

| Button | Action |
|--------|--------|
| Run Pipeline Check | Calls server endpoint → runs pipeline logic → displays result in modal |
| Draft Reply | Opens modal with instructions + email composer hint |
| Trial Follow-Up | Calls server endpoint → pulls trial schools → displays close email templates |

Long-term: Claude Code CLI integration for full skill execution. Phase 1: modals with output.

---

## Launch Command

```bash
python3 dashboard/server.py
# Opens http://localhost:8080 automatically
```

Add to `README.md` in AIS-OS root.

---

## Known Expenses Seed (from onboarding)

| Service | $/mo | Category |
|---------|------|----------|
| Claude Max | $130 | AI Tools |
| Supabase | $25 | Infrastructure |
| Vercel | $20 | Infrastructure |
| Google Workspace | $20 | Productivity |
| ChatGPT Plus | $20 | AI Tools |
| Firecrawl | $19 | AI API |
| MailerLite | $15 | Marketing |
| Pinecone | $0 | AI Infrastructure |
| Fal.ai | ~$0 | AI API (video) |
| **Total** | **$229** | |

---

## Phase 1 Scope (ship first)

- Static expense list from seed data
- Live Supabase school/trial data
- Task checklist (local JSON)
- Debt tracker (local JSON)
- Skill modals (no live Claude Code integration)
- Apple Card CSV parser

## Phase 2 (after Phase 1 validated)

- Gmail inbox triage panel (live)
- Gmail receipt parser
- Stripe live data
- Auto-refresh every 5 min
- Edit tasks inline

## Out of Scope (for now)

- Mobile/responsive layout
- Multi-user access
- Cloud hosting
- Real-time notifications
- Plaid bank integration

---

## Success Criteria

Bryan opens the dashboard in the morning and within 10 seconds knows:
1. Net income (positive or negative)
2. How many trials need follow-up
3. What his biggest expense is
4. What to focus on today

No other tool needs to be opened.
