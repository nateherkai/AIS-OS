---
name: dreaming-engine
type: concept
tags: [overnight-agent, self-improvement, memory-health, automation, anthropic, dreaming, ai-os]
source_files: [jack-roberts-cc-os]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Dreaming Engine

A nightly automated analysis process that scans all AI usage data on the user's computer and generates high-leverage improvement recommendations. Inspired by (and independent of) Anthropic's research preview of "Dreaming" for managed agents.

## Origin

Anthropic shipped a research preview of a "Dreaming" feature — an overnight memory pass for managed agents that "sees everything." Jack Roberts built his own version that:
1. Runs across all AI tools (not just Claude) — Codex, Gemini, terminal, etc.
2. Generates four specific, actionable recommendations each morning
3. Connects to eight analysis dimensions
4. Optionally runs web searches to enrich findings
5. Optionally generates a daily image (for the experience of it)

Jack's version pre-dates or parallels Anthropic's release; he didn't wait for official tooling.

## Eight Dimensions of Dream Intelligence

See: [[../concepts/eight-dim-dream-intelligence|Eight Dimensions of Dream Intelligence]]

1. **Conversation analysis** — reads last 7 days of user messages, embeds + clusters by intent, flags tasks done manually 3+ times (candidates for new skills)
2. **Cost intelligence** — inspects every model call for high-Opus usage on simple work, low cache-hit rates, oversized contexts
3. **Skill performance** — tracks last-use dates, identifies antiquated skills, surfaces kill/keep decisions
4. **Memory health** — flags stale memories that haven't been referenced, checks memory is current
5. **Session hygiene** — token run-out risk, session patterns
6. **Workflow patterns** — identifies inefficiencies and duplicated work
7. **External opportunities** — scans for new skills, tools, or repos that match the user's work patterns
8. **Business context** — understands what the user is focusing on and aligns recommendations to it

## Output Format

Four high-leverage recommendations per morning. Each has: what was found, why it matters, specific action to take. UI allows mark-as-done or dismiss per item.

## Example Recommendations (from demo)

- "Your video scripts memory is 2.5 weeks behind your work." → action: update memory
- "You're paying Opus prices for jobs Haiku can do." → action: route specific task types to cheaper model
- "You did the same competitive research four times this week." → action: create a skill for it

## Configuration

User sets:
- Frequency (daily/weekly)
- Morning vs evening run time
- Whether to enable web search enrichment
- What dimensions to weight
- Time value (hourly rate) for ROI calculations

## Related

- [[../concepts/claude-code-os|Claude Code OS]]
- [[../concepts/eight-dim-dream-intelligence|Eight Dimensions of Dream Intelligence]]
- [[../concepts/six-pillars-os|Six Pillars OS]]
- [[../people/jack-roberts|Jack Roberts]]
- [[../sources/jack-roberts-cc-os-walkthrough|Jack Roberts CC-OS Walkthrough]]
