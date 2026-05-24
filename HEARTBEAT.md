# AIOS Heartbeat

Last updated: 2026-05-24

## Cron Jobs

| Job | Schedule | Status |
|-----|----------|--------|
| Dream engine | 02:00 daily | Running |
| Vault lint | 18:00 Friday | Running |
| Self-improvement loop | Weekly | Running |
| Frank (NLM librarian) | Weekly | Degraded (NLM auth expired) |

## Tool Health

| Tool | Status | Notes |
|------|--------|-------|
| hc_nlm_* MCP tools | Fixed | task_id bug patched in b93308036 (2026-05-21). CLI fallback no longer needed. |
| image_generate (gpt-image-2) | Unavailable | FAL_KEY not set. Get key from fal.ai/dashboard/keys |
| NotebookLM auth | Expired | Run `notebooklm login` interactively to restore |
| Browser/Playwright | Not installed | N/A |

## Active Concerns

1. NLM auth expired since 2026-05-21. Frank skill degraded.
2. FAL_KEY missing. Image generation unavailable.
3. 4 dormant notebooks need triage (Higgsfield, Antigravity, Pairstart, Cow Lot).
4. 3 AI notebooks (Hermes Agentic OS, Agentic Systems, AI Agent Frameworks) — merge/cross-ref decision pending.
5. Hermes push bridge (decision 2026-05-22) not yet built.
