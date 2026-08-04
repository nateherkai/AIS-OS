---
name: eight-dim-dream-intelligence
type: concept
tags: [dreaming, overnight-agent, analysis-dimensions, ai-os, self-improvement]
source_files: [jack-roberts-cc-os]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Eight Dimensions of Dream Intelligence

The eight analytical dimensions that Jack Roberts' Dreaming Engine processes nightly. Together they produce "eight buckets, four cards, one night" — eight input streams → four actionable recommendations each morning.

## The Eight Dimensions

1. **Conversation Analysis**
   Reads last 7 days of AI messages. Embeds and clusters by intent. Flags any task done manually 3+ times as a skill candidate. (Borrowed from his earlier Hermes agent pattern.)

2. **Cost Intelligence**
   Inspects every model call. Looks for: high-Opus usage on simple tasks, low cache-hit rates, oversized context windows. Recommends cheaper model routing where appropriate.

3. **Skill Performance**
   Tracks last-use date of every skill in the skills directory. Surfaces antiquated skills that aren't being used. Quantifies time saved per skill against user's stated hourly rate.

4. **Memory Health**
   Detects memories that are stale (not referenced in X days) or significantly out of date relative to the user's current work. Example: "Your video scripts memory is 2.5 weeks behind your work."

5. **Session Hygiene**
   Monitors token usage patterns. Flags when the user is likely to run out mid-session. Identifies context-bloat habits.

6. **Workflow Patterns**
   Identifies macro inefficiencies — e.g., duplicating the same research multiple times in a week. Connects to skill creation recommendations.

7. **External Opportunities**
   Scans for new tools, skills, repos, or resources that fit the user's current work patterns. Example: surfaces a design systems repo when design work is detected in recent sessions.

8. **Business Context**
   Understands what the user is currently focused on (projects, clients, goals) and aligns all recommendations to that context.

## Output

Four high-leverage morning recommendations. Each includes: finding, why it matters, specific action step. The UI allows mark-done or dismiss per item. Supports a suggested ROI estimate (time saved).

## Formula

Eight dimensions of input → nightly processing → four cards → morning review → action or dismiss

## Related

- [[../concepts/dreaming-engine|Dreaming Engine]]
- [[../concepts/claude-code-os|Claude Code OS]]
- [[../people/jack-roberts|Jack Roberts]]
- [[../sources/jack-roberts-cc-os-walkthrough|Jack Roberts CC-OS Walkthrough]]
