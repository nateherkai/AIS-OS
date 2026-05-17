---
name: reviewing-code
description: Performs comprehensive code reviews for pull requests or specific files. Use when the user asks for a code review, feedback on a PR, or to check for best practices and potential bugs.
---

# Reviewing Code

## When to use this skill
- When the user submits code for review.
- Before merging a feature branch.
- When searching for architectural inconsistencies or performance bottlenecks.

## Workflow
1. [ ] Analyze the scope of changes (diffs or specific files).
2. [ ] Identify architectural patterns and verify compliance.
3. [ ] Check for common pitfalls (security, performance, edge cases).
4. [ ] Provide a structured feedback report with actionable suggestions.
5. [ ] (Optional) Apply suggested fixes if requested by the user.

## Instructions

### 1. Analysis Phase
- Use `git diff` to understand the context of the changes if in a git repository.
- Review `tsconfig.json` or project-specific config files to understand strictness levels.

### 2. Review Criteria
- **Patterns**: Verify usage of established project patterns (e.g., Tailwind classes, React hooks, service layers).
- **Security**: Look for hardcoded secrets, lack of input validation, or unsafe data handling.
- **Performance**: Identify unnecessary re-renders, slow database queries, or inefficient loops.

### 3. Feedback Format
Keep feedback concise and actionable. Use code blocks for suggested improvements:

```typescript
// Prefer:
const data = useMemo(() => compute(items), [items]);

// Instead of:
const data = compute(items); // Re-computes on every render
```

## Resources
- [review.sh](scripts/review.sh) - A script for automated linting and static analysis.
