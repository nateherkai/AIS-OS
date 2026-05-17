---
name: deployment-qa
description: Enforces comprehensive pre-deployment and post-deployment checks. Use this skill whenever the user asks to deploy to production, push an update live, or fix a broken production feature. It ensures code is rigorously tested, strictly pushed via the GitHub integration, and visually verified on the live domain using the browser subagent.
---

# Deployment & QA Skill Setup

This skill is the **absolute, ultimate source of truth** for deploying updates to `agcoachpro.com`. We have suffered severe issues in the past from Vercel CDN caching and unverified "blind" deployments.

If the user asks you to update the site, deploy a feature, or push changes, you MUST enforce the following 3-phase workflow. NO EXCEPTIONS. Do not skip any phase.

## Phase 1: Pre-Deployment Guardrails

Before you even think about deploying, you must ensure the app won't crash when it hits the build server.

1. **Verify Types**: Run `npx tsc --noEmit` to ensure there are no TypeScript compilation errors. If there are, fix them first.
2. **Verify Env Vars**: If your feature relies on a new Supabase Edge Function or an external API (like Stripe, OpenAI), confirm with the user that those secrets are set in the Vercel Production Environment.
3. **Data Parity Check**: Look out for "Hardcoded Slug vs Live UUID" issues. If your logic relies on a CDE ID (e.g., `cde-livestock`), ensure it also gracefully handles live Supabase UUIDs (e.g., by matching `contest.name`).

## Phase 2: The Bulletproof GitHub Deployment Pipeline

**CRITICAL RULE:** **NEVER use the Vercel CLI (`vercel --prod`) to deploy to production.**
Manual deployments bypass Vercel's automated Edge Cache invalidation, resulting in users seeing stale, broken code permanently cached on their devices.

Your ONLY deployment workflow is:

1. `git add .`
2. `git commit -m "[Brief summary of your changes]"`
3. `git push`

This triggers the GitHub Vercel Integration.
4. **Monitor the Build:** Run `sleep 60 && vercel ls ffa-app-clean` to monitor the build. Wait until the newest branch hits the **"Ready"** status under the "Production" column.

## Phase 3: Post-Deployment Live Verification (The "Trust But Verify" Rule)

You are not done just because Vercel says "Ready". You MUST verify the deployment actually works on the live domain.

1. **Dispatch Browser Subagent**: Call the `browser_subagent` tool.
2. **Target URL**: Advise the subagent to navigate to `https://agcoachpro.com`.
3. **Task Instructions**: Give the subagent highly specific instructions to:
   - Login to the Student Demo mode.
   - Navigate specifically to the URL(route) of the feature you just deployed.
   - Click the actual buttons/inputs you added.
   - Confirm they function correctly without crashing, dead-ending, or encountering 0-quantity data bugs.

**Do NOT notify the user that the site is updated until the subagent returns a SUCCESS report.**
If the subagent discovers the deployment is broken, iterate on Phase 1, Phase 2, and Phase 3 again until it passes.

Once Phase 3 passes, use the `notify_user` tool to inform the user the deployment is complete, live, and verified!
