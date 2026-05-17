---
description: Automated web deployment workflow for Ag Coach Pro.
---

# Bulletproof Web Deployment Workflow

1. Add all changes to git and commit them.
```bash
git add .
git commit -m "Deploy: auto commit"
```

2. Push the commit to GitHub. **This is the critical step**. Pushing to GitHub automatically triggers the official production build in Vercel (`ffa-app-clean` project) which correctly handles global domain CDN cache invalidation.
```bash
git push
```

3. Monitor the official Vercel deployment. Wait for the status to show "Ready" in the `ffa-app-clean` project.
```bash
vercel ls ffa-app-clean
```

### 🚨 Vercel CLI Anti-Patterns to Avoid 🚨
- **NEVER** use `vercel --prod` or `vercel --prod --force` to deploy to production.
- **NEVER** use `vercel alias set` to manually assign domains to deployments.
- *Why?* Manual CLI deployments and routing aliases often bypass the automated Edge Cache invalidation that the GitHub Vercel integration performs, causing users and devices to serve stale code indefinitely. Always push to main via Git.
