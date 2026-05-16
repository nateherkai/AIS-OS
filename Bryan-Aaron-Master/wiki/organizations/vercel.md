---
name: vercel
type: organization
tags: [vercel, hosting, deployment, web, infrastructure]
source_files: [raw/_ingested/2026-05-16-agcoach-BUSINESS_BRAIN.md, raw/_ingested/2026-05-16-agcoach-CLAUDE.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Vercel

Web hosting and deployment platform for Ag Coach Pro's web build.

## Role in Ag Coach Pro

- Hosts agcoachpro.com (apex 307 → www)
- Production URL: https://www.agcoachpro.com
- Deploys via GitHub pipeline (not Vercel CLI for production)

## Project Details

- **Project ID**: `prj_4xPOIb5yS0qzoJFmLstwRURR9KC9`
- **Team**: `team_n4rQ2jw7YC7ldt5ZAVXaBWK6`
- **MCP available**: Yes

## Deployment Rule

**NEVER use Vercel CLI for production.** Use GitHub pipeline to ensure proper cache invalidation. Verify on live domain with `browser_subagent` before marking deployment complete (per `deployment-qa` skill).

## Build Commands

```bash
npm run build   # Web export → dist/ (validates bundle contains key content)
npm run export  # Raw web export, no validation
```

## Related

- [[../sources/agcoach-app-working-instructions|App Working Instructions]]
- [[../sources/agcoach-business-brain|Business Brain]]
- [[../organizations/supabase|Supabase]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
