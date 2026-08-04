
# Advisor Intelligence Skill

Owns the technical implementation of high-fidelity analytics, team management, and learning gap visualization for FFA Advisors.

## Principles of "Premier Advisor Intelligence"
1. **Data over Dates**: Don't just show *when* they practiced; show *what* they missed.
2. **Actionable Insights**: Highlight "The Top 5 Weakest Areas" for the entire team to focus on in class tomorrow.
3. **Simulation Fidelity**: Reports should reflect real Contest formats (Scantron-ready scoring).
4. **Advisor Efficiency**: Batch management of students and one-click assignments.

## Core Capabilities

### 1. Granular Gap Analysis (Intelligence View)
Instead of a simple "85%" average, we calculate performance by **Category** or **Taxonomy**.
- **Entomology Example**: "Your team is 95% on Orthoptera, but only 40% on Hymenoptera larvae."
- **Dairy Example**: "Your team is missing 90% of questions related to Mastitis prevention."

### 2. Engagement Heatmaps
Visualize "Practice Velocity" to identify if students are cramming the night before a contest or maintaining a healthy streak.

### 3. Live Contest Leaderboards
During a practice contest day in the classroom, the advisor sees a live-updating leaderboard of their students' progress.

### 4. Assignment & Goal Setting
Ability to "Lock" a contest until a student reaches a certain mastery level in Study mode.

## Implementation Patterns

### Data Model: Performance Record
```typescript
interface PerformanceGap {
  categoryId: string;
  categoryName: string;
  attempts: number;
  correct: number;
  errorRate: number;
  mostMissedId?: string;
}
