# Skill: Brand Voice Lint

## Purpose

Brand voice = Authoritative Coach + Competitive Motivator. Banned terms erode positioning. Light backgrounds break dark-glass aesthetic. This skill scans for both.

---

## When to Use

- Before merge of UI-touching PR
- After AI prompt extract (`prompt-extract`)
- Periodic audit (monthly)
- Onboarding copy / marketing pages

---

## Banned Terms

Voice violations (per CLAUDE.md Brand System):

```
fun
easy
quick
gamified
unlock
journey
student journey
learning experience
skill-building
personal coach
amazing
awesome
super
```

Plus superlatives without proof ("best ever", "ultimate").

## Required Terms (when context fits)

```
CDE / LDE
placing(s)
score
mastery
judge perspective
evaluation criteria
24/7 AI feedback
AI-guided practice
progress dashboard
readiness
```

---

## Scan Commands

### Voice scan

```bash
# Banned words in user-facing strings
grep -rEni --include="*.tsx" --include="*.ts" \
  -E "\b(fun|easy|quick|gamified|unlock|journey|amazing|awesome)\b" \
  app/ components/ \
  | grep -v "node_modules" \
  | grep -iE "(text|title|label|placeholder|message|description|subtitle)"
```

### Light background scan

```bash
# White / light backgrounds
grep -rEn --include="*.tsx" --include="*.ts" \
  -E "(backgroundColor:\s*['\"]?(white|#fff|#ffffff|#f|#e))" \
  app/ components/

# Default View with no Theme bg
grep -rEn --include="*.tsx" "<View " app/ components/ \
  | grep -v "style=" | grep -v "Theme\." \
  | head -20
```

### Touchable that should be AnimatedButton

```bash
# Native TouchableOpacity import — should alias AnimatedButton
grep -rEn --include="*.tsx" \
  "from 'react-native'" app/ components/ \
  | xargs -I{} sh -c "grep -l 'TouchableOpacity' {}" 2>/dev/null
```

---

## Triage

For each hit:

| Issue | Fix |
|---|---|
| "Have fun!" in onboarding | "Build mastery." or "Drill the rubric." |
| "Quick quiz" | "Practice set" / "10-question drill" |
| "Easy mode" | "Foundation" / "Greenhand" |
| "Unlock this feature" | "Available in Blue & Gold" |
| "Your learning journey" | "Your placing trajectory" / "Your scores" |
| `backgroundColor: 'white'` | `Theme.colors.background` or `GlassEffect.background` |
| `import { TouchableOpacity } from 'react-native'` | `import AnimatedButton from '@/components/common/AnimatedButton'` aliased as `TouchableOpacity` |

---

## Audience Tone Check

| Audience | Right | Wrong |
|---|---|---|
| Students | "Your last 3 tests dropped. Focus on parasite ID." | "Great job! Keep going!" |
| Teachers | "Your students get 24/7 feedback. You get readiness dashboards." | "Make teaching fun and easy!" |
| Parents | "FFA-aligned curriculum. Track competition readiness." | "A magical learning adventure" |

---

## Colors Reference

| Token | Hex | Use |
|---|---|---|
| Navy | `#001F4D` | Primary, authority, UI |
| Gold | `#D4A574` | Achievement, progress, accent |
| White | `#FFFFFF` | Text on dark only |
| Dark Gray | `#2B2B2B` | Secondary surfaces |

Source: `constants/theme.ts → Theme`. Never hardcode hex in components.

---

## Output Format

Report as triage table:

| File:line | Issue | Suggested fix |
|---|---|---|
| `app/(auth)/signup.tsx:42` | "Quick and easy signup" | "Start your trial" |
| `app/practice/forages/index.tsx:88` | `backgroundColor: '#fff'` | `Theme.colors.background` |
