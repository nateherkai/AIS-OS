---
name: agcoach-advisor-intelligence-skill
type: source
tags: [ag-coach-pro, advisor, analytics, teacher, intelligence]
source_files: [raw/_ingested/2026-05-16-agcoach-advisor-intelligence-skill.md]
domains: [01-AG-COACH-PRO]
created: 2026-05-16
updated: 2026-05-16
---

# Ag Coach Pro — Advisor Intelligence Skill

`.agent/skills/advisor-intelligence/SKILL.md` — owns analytics, team management, and learning-gap visualization for FFA Advisors (teachers).

## Four principles of "Premier Advisor Intelligence"

1. **Data over Dates** — show *what* students missed, not just *when* they practiced.
2. **Actionable Insights** — surface "Top 5 Weakest Areas" for class-tomorrow focus.
3. **Simulation Fidelity** — Scantron-ready scoring that mirrors real contest formats.
4. **Advisor Efficiency** — batch student management + one-click assignments.

## Four core capabilities

1. **Granular Gap Analysis** — per-category mastery, not aggregate averages. Examples:
   - Entomology: "95% on Orthoptera, only 40% on Hymenoptera larvae."
   - Dairy: "Missing 90% of Mastitis-prevention questions."
2. **Engagement Heatmaps** — "Practice Velocity" view to spot crammers vs steady streaks.
3. **Live Contest Leaderboards** — real-time leaderboard during in-class practice contests.
4. **Assignment & Goal Setting** — lock a contest until mastery threshold met in Study mode.

## Data model

```typescript
interface PerformanceGap {
  categoryId: string;
  categoryName: string;
  attempts: number;
  correct: number;
  errorRate: number;
  mostMissedId?: string;
}
```

Backed in code by `TeacherService.getPerformanceGaps(classroomId?)` — always pass `classroomId` when feeding an AI prompt so other classes' weak data does not leak in (rule from [[agcoach-app-working-instructions|CLAUDE.md]]).

## Related

- [[../concepts/agcoach-app-internal-skills-catalog|App Internal Skills Catalog]]
- [[agcoach-business-brain|Business Brain]]
- [[agcoach-agent-global-rules|Agent Global Rules]]
- [[../../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
