# The Three Ms of AI™ — Mindset, Method, Machine

> *Adapted from The Three Ms of AI™. © 2026 Nate Herk. All rights reserved.*
> *The Three Ms of AI™ is a trademark of Nate Herk.*

> *"The best automation is the one you barely notice. Start by eliminating what doesn't need to exist, then automate what's left with the least amount of AI possible."*

**Boring is Beautiful.**

---

## Why this is in your kit

This framework is the operator brain you'll use every time you run `/level-up`. Three layers, each one builds on the last. Read it once, refer back as needed.

Here's the thing most people get wrong: they think AI automation is about tools. It's not. Tools change every six months. The platform you're using today might not exist next year. What doesn't change is how you THINK about automation, how you DECIDE what to automate, and how you BUILD and OPERATE the thing once it's running. That's what The Three Ms of AI™ gives you. A way to think that works regardless of platform, model, or hype cycle.

This framework is for everyone. Business owners hearing about AI for the first time. Engineers exploring automation. Consultants who need a methodology they can hand to a client. It scales.

---

## Layer 1 — MINDSET (How to Think)

Before you touch a single tool, you need to rewire how you approach work. The way you think about tasks determines whether you'll spot automation opportunities or walk past them every day.

### 1. The Default Shift

The core habit: before doing any task the old way, ask "How could AI do this?"

If the answer is "it can't do all of it," the follow-up: "How could AI assist with the first 30%?"

It's never binary. The real question is always **"to what extent can AI be leveraged here?"** Maybe 80%. Maybe 10%. You don't know until you ask.

**Real example.** Updating tracking links across 300+ YouTube video descriptions. The old way: open each video in YouTube Studio, find the link, replace it, save, next. Hours of mind-numbing work. The new way: describe the problem to Claude Code and walk to the kitchen for water. By the time you come back, it's researched the YouTube Data API, figured out quota limits, written a script, and laid out a plan. Approve, run, done. Now you have a reusable system.

The Default Shift is like learning to type instead of writing by hand. Once it clicks, you physically cannot go back. Every manual task starts to itch.

**One thing to internalize:** AI is better than you think, and improving faster than you think. Client needed infographic visuals; models couldn't deliver. Three months later, new model dropped. Shipped the work. *If AI can't do something today, try again next month. Seriously.*

### 2. The Function Breakdown

Your role is a set of functions. Your job description has about five bullet points. Each breaks into dozens of tiny tasks. **You don't automate your whole job. You automate one tiny piece. Then another. Then chain them.**

Think "automate a YouTube video." Sounds impossible. Break it down: ideation, scripting, title generation, thumbnail generation, description writing, comment replies, timestamps, analytics. Each piece is its own automation. Build one, get it working, move on.

One small task per day. Six months later, hundreds automated. Compounding is real.

### 3. The Curiosity Rule

Never accept AI output without asking why. Ask for three alternatives. Ask which one it thinks is best and why. Push back. Dig in.

This is the antidote to "dark code" — automations or code you don't understand. **If you build something and you can't explain how it works, you've built a liability, not an asset.** When it breaks (and it will), you'll have no idea where to start.

Treat AI as a mentor, not a vending machine. The vending machine gives you output. The mentor gives you understanding.

### Expect the Dip

Productivity dip at the start: ~20% less output for the first week or two. New workflows, new prompting cadence. That's normal. Within two weeks, baseline doubles. But you have to push through.

**Fail fast, learn faster.** Get to your first 10 mistakes as safely and quickly as possible. That's where the real learning lives, not in your first 10 successes.

---

## Layer 2 — METHOD (How to Decide)

Mindset tells you how to think. Method tells you what to do with that thinking. The operational core — turning "I should probably automate something" into "here's exactly what I'm building and why."

### 1. Find the Constraint

Two power questions surface everything:

**Q1:** *"If 500 new clients showed up tomorrow, what would break first?"* — finds bottlenecks (clogs in the pipe). Onboarding? Invoicing? Support response times?

**Q2:** *"What would give you 500 more clients tomorrow?"* — finds growth opportunities (untapped pipe). Content you're not creating? Outreach you're not doing? Leads you're not following up on?

One finds what's broken. The other finds what could scale. Start with the constraint.

### 2. EAD: Eliminate, Automate, Delegate

For every process, run EAD — in this order.

**Eliminate first.** *"What happens if we just stop doing this?"* You'd be surprised how many processes exist because they always have. Reports nobody reads. Approval steps that add no value. **If nobody would notice it disappeared, kill it. Don't automate waste.**

**Automate second.** Apply the **60/30/10 Golden Rule:**
- ~60% fully automated (no human touch)
- ~30% AI-assisted (AI does the work, human reviews before it goes out)
- ~10% stays manual (too nuanced, too risky, or too rare)

This ratio normalizes expectations. **Full automation is rarely the goal.** If someone promises 100% on anything meaningful, they're selling you something.

**Delegate third.** If a process can't hit 60/30/10 — too complex, too variable, too judgment-dependent — delegate to a person. Not everything should be automated.

The key: nothing stays as-is. Every process gets killed, automated, or handed off.

### 3. Map the Process

Before you touch any tool, write every step on paper. Five elements per process:

- **Trigger** — what kicks it off (form submission, calendar event, email, time of day)
- **Data Sources** — where information comes from (CRM, spreadsheet, inbox)
- **Data Transformations** — how data changes shape (reformatting, filtering, combining)
- **Decision Points** — where it branches (if qualified, do X; if not, do Y)
- **Destination** — where output goes (back to CRM, email, Slack, document)

**Rule:** *if you can't explain it to a person, you can't explain it to an AI.* The map forces clarity. Skip this step and you'll build something that sort of works but breaks in weird ways.

### 4. The Autonomy Spectrum

Each step gets an autonomy level:

| Level | Name | What Happens |
|-------|------|-------------|
| L0 | Manual | No AI. Human does it. |
| L1 | Suggested | AI suggests, human decides every step. |
| L2 | Drafted | AI drafts, human reviews and edits. |
| L3 | Supervised | Rules set, AI runs, human validates. |
| L4 | Autonomous | AI handles end-to-end. |

**Governing principle: default to the LOWEST level that works.**

Most people get this backwards. They hear "AI automation" and jump to L4. That's where things go wrong. Boring is Beautiful. Deterministic beats non-deterministic. **Workflows beat agents.** If a decision doesn't HAVE to be made by AI, don't let AI make it.

Push autonomy up only when you've proven the lower level works.

### 5. Tie It to a KPI

If your automation doesn't move a number, why are you building it?

**The Three Buckets** (every business metric falls into one):

1. **Get more customers** — content, prospecting, outreach, ads, lead gen
2. **Make each customer worth more** — premium services at lower cost, upselling, retention
3. **Cut costs** — eliminate drudgery, reduce errors, boost productivity

**Specific KPIs** are tied to the individual automation: response time, error rate, tickets per month, conversion rate, time-to-completion.

If your automation doesn't improve a metric in one of the three buckets, stop. *"Because it's cool"* isn't a business case.

---

## Layer 3 — MACHINE (How to Build and Operate)

You've got the thinking (Mindset) and the decisions (Method). Now you build and run the thing. Two halves: BUILD and OPERATE.

### BUILD

#### 1. The Lego Principle

Smallest possible steps. One input, one output per block. Output of block 1 becomes input of block 2.

Start with **zero-AI steps first**. Get the deterministic pieces working — data fetching, formatting, routing. Then layer in AI where actually needed.

This makes the project less overwhelming and lets you validate as you go. If block 3 produces garbage, you know exactly where to look. **Modularity is freedom.**

#### 2. The Assembly Line

Each AI step does one specialized job. Like workers on an assembly line.

**Don't build a generalist.** One model call for copywriting. Another for reasoning. Another for classification. Keep them separate. Easier to debug, swap models, adjust prompts.

#### 3. The Validation Chain

Validate each step's output before chaining. **Do NOT build the whole pipeline and test end-to-end.** That's a recipe for "it doesn't work and I have no idea why."

Build step 1. Run it. Confirm output. Build step 2. Run with step 1's actual output. Confirm. Chain. Add step 3. This is how POCs actually work.

#### 4. The Iteration Mindset

There's no finished product — especially with AI. Deterministic scripts CAN be done (a CSV reformatter, sure). AI steps are always evolving. New models. New capabilities. The prompt that was optimal six months ago is verbose and expensive today.

Ship the POC. Get real-usage feedback. Expand. Iterate. **Perfectionism is the enemy of deployment.**

### OPERATE

#### 5. The Bike Method

Roll out in phases, like teaching a kid to ride.

- **Phase 1 — Training wheels.** Run manually. Watch everything. Correct mistakes by hand.
- **Phase 2 — Guided.** Automation runs but you review every output. It drafts, doesn't send.
- **Phase 3 — Watched.** Runs autonomously. You monitor. Alerts for anomalies. Periodic batch review.
- **Phase 4 — Hands-off.** Helmet on, go ride.

Even at 90% confidence, roll out 10% of volume first. Watch a week. Add 20% more. Like drug trials — not full dose to everyone day one.

Use confidence thresholds: high → auto-send, medium → draft queue, low → escalate to human. Tighten or loosen as data accumulates.

#### 6. The Intern Rule

Treat AI like a brand-new hire on day one.

- **Own identity.** Its own email, accounts, credentials. Never yours.
- **Read-only by default.** View-only until you've proven write access is needed.
- **Never impersonates you.** Signs off as "[your name]'s AI assistant."
- **No personal credentials.** No passwords, bank info, personal logins.
- **Full audit trail.** Visibility into everything it did, spent, created, deleted.
- **Scoped permissions.** API keys with minimal scope. Exactly what's needed, nothing more.

*"You wouldn't trust someone you just met with your bank account."*

#### 7. The Kill Switch

Monitor what's running. If an automation consistently needs patches, produces low-quality output, or costs more to maintain than it saves — **tear it down.** Dismantle. Delete.

Don't fall into the sunk cost trap. *"But I spent three weeks building this"* is not a reason to keep something running that doesn't work. **Good operators know when to build AND when to destroy.** The kill switch is just as important as the launch button.

---

## Governing Principles

Three principles that sit above everything else. When in doubt, return to these.

1. **Boring is beautiful.** Predictable beats clever. Default to the simplest, most deterministic approach that gets the job done.
2. **Deterministic steps can be finished. AI steps are always evolving.** Set expectations — yours and your client's — accordingly. A rule-based filter is done. An AI classifier needs tuning forever.
3. **Fail fast, learn faster.** Get to your first 10 mistakes safely and quickly. Real learning lives there, not in planning, not in your first 10 successes.

---

## Branch Frameworks (future hooks)

The 3Ms is the mothership. Specific topics go deeper in dedicated frameworks. Most aren't built into this kit yet. They'll grow into `references/` over time:

- **The Data Retrieval Hierarchy** — Filters, SQL, Full Context, RAG: when to use which
- **The Integration Ladder** — API, CLI, Browser Automation, Scraping: hierarchy of reliability
- **The Error Handling Playbook** — What to do when things break (and they will)
- **The Model Selection Guide** — How to pick the right model for the right job
- **The Context Engineering Framework** — How to feed AI the right information at the right time
- **The Discovery Playbook** — How to run discovery with a client or team before building
- **The Security and Permissions Playbook** — Access control, audit trails, risk management

Each plugs into the 3Ms at specific points. Start here, branch out as you need depth.

---

> *Adapted from The Three Ms of AI™. © 2026 Nate Herk. All rights reserved.*
> *Full breakdown with diagrams and examples: [insert link to YouTube companion video / public-facing page when published].*
