# Skill: no-blank-pages

Audit the entire app for blank-page / white-screen navigation bugs and fix them.

## When to invoke

- After adding any new screen that has a "Back", "Done", "Return to Hub", or result/finish button
- When a user reports a white or blank screen after completing a quiz, test, or flow
- Before any major release

---

## Root Cause

On web (Expo Router + Vercel), `router.back()` calls `window.history.back()`.
If the user landed directly on a deep URL (bookmark, shared link, page refresh), the browser history stack is **empty**. Calling `router.back()` exits the SPA entirely → white blank page.

**This never shows up in local dev** (where navigation history always exists) but always hits in production web.

---

## The Rule

> **Never call `router.back()` on a result screen, finish screen, or hub-return button.**
> Use `safeBack(router, fallback)` from `lib/navigation.ts` instead.

`router.back()` is acceptable ONLY for:
- Dismissing error alerts mid-flow (where a specific fallback isn't meaningful)
- Within a modal/sheet that is always opened from a known parent

---

## Shared Utility

```typescript
// lib/navigation.ts
import { safeBack } from '@/lib/navigation';

// Usage in any screen:
safeBack(router, '/practice/livestock-anatomy');  // replace with correct hub route
```

`safeBack` checks `router.canGoBack()` first. If true, it calls `router.back()` normally. If false (empty history), it calls `router.replace(fallback)` to land on a known valid route.

---

## Audit Steps

Run these steps when invoked:

### Step 1 — Find all router.back() calls in result/finish screens

```bash
grep -rn "router\.back()" app/ --include="*.tsx" | grep -v "node_modules"
```

Look for `router.back()` in these high-risk patterns:
- Files named `results.tsx`, `quiz.tsx`, `test.tsx`, `contest.tsx`, `exam.tsx`
- Buttons labeled: "Back", "Done", "Finish", "Return", "Go to Dashboard", "Back to Hub", "Back to [X]"
- `onPress` handlers on the **last screen** of a multi-step flow
- Any screen that can be navigated to directly via a deep link

### Step 2 — Check for missing background colors (causes flash-to-white)

```bash
grep -rn "backgroundColor" app/ --include="*.tsx" | grep -c "#000\|black\|Theme.colors.black"
```

Every root `View` / `SafeAreaView` / `ScrollView` container MUST have `backgroundColor: '#000'` (or `Theme.colors.black`). A missing or `undefined` background causes white flash during navigation transitions.

Check pattern:
```tsx
// ❌ Bad — white flash on transition
<View style={{ flex: 1 }}>

// ✅ Good
<View style={{ flex: 1, backgroundColor: '#000' }}>
// or
<View style={styles.container}>  // where container has backgroundColor: '#000'
```

### Step 3 — Check Stack.Screen title changes mid-screen

Multiple conditional `Stack.Screen` definitions in one component (e.g., different titles for start/test/results) cause a header re-render flash when state changes.

**Fix:** Use a single `Stack.Screen` at the top of the component and update its `options` prop dynamically:

```tsx
// ❌ Bad — causes flash when showResults changes
if (showResults) {
  return (
    <View>
      <Stack.Screen options={{ title: 'Results' }} />
      ...
    </View>
  );
}
return (
  <View>
    <Stack.Screen options={{ title: 'Test' }} />
    ...
  </View>
);

// ✅ Good — single Stack.Screen, dynamic title
const screenTitle = showResults ? 'Results' : testStarted ? `Q ${idx+1}/${total}` : 'Anatomy Test';
return (
  <View>
    <Stack.Screen options={{ title: screenTitle, headerLeft: showResults ? () => null : undefined }} />
    ...
  </View>
);
```

### Step 4 — Check result screens for back gesture / header back button

On result screens, the native back gesture or header back button should NOT be able to reach a blank page. Use `headerLeft: () => null` on result `Stack.Screen` options to disable the back gesture, and provide an explicit "Return" button using `safeBack`.

```tsx
<Stack.Screen options={{
  title: 'Results',
  headerLeft: () => null,  // disables swipe-back and header back button
}} />
```

### Step 5 — Fix all identified issues

For each `router.back()` on a result/finish screen:

```tsx
// Before
onPress={() => router.back()}

// After
import { safeBack } from '@/lib/navigation';
onPress={() => safeBack(router, '/practice/livestock-anatomy')}
```

Fallback routes by screen type:
| Screen type | Fallback route |
|---|---|
| Practice quiz/test results | Parent hub (e.g., `/practice/livestock-anatomy`) |
| Contest results | `/practice` |
| Assessment results | `/(tabs)` (student dashboard) |
| Admin screens | `/(admin)` |
| Auth screens | `/` |
| Settings / Profile | Previous tab (use `router.replace` to the tab) |

### Step 6 — Verify

After fixes, test by navigating directly to deep URLs (simulate empty history):
1. Open a fresh browser tab and paste the direct URL of a quiz/test
2. Complete the quiz
3. Click the back/return button — should land on the fallback, never blank

---

## Files Already Fixed

- `app/practice/livestock-anatomy/test.tsx` — uses `safeBack` + `headerLeft: () => null` on results
- `app/assignments/results.tsx` — uses `router.replace('/(tabs)')` directly (no history needed)
- `app/study/ai-quiz.tsx` — results "Back to Library" → `safeBack(router, '/(tabs)')`
- `app/practice/greenhand-quiz/quiz.tsx` — results "Return to Menu" → `safeBack(router, '/practice/greenhand-quiz')`
- `app/practice/senior-quiz/quiz.tsx` — results "Return to Menu" → `safeBack(router, '/practice/senior-quiz')`
- `app/practice/horse-eval/quiz.tsx` — results "Return to Menu" → `safeBack(router, '/practice/horse-eval')`
- `app/practice/forages/quiz.tsx` — results "Return to Menu" → `safeBack(router, '/practice/forages')`
- `app/practice/forages/flashcards.tsx` — results "Back to Forages CDE" → `safeBack(router, '/practice/forages')`
- `app/practice/livestock-judging/exam.tsx` — results "Return to Hub" → `safeBack(router, '/practice/livestock-judging')`
- `app/practice/livestock-judging/class-eval.tsx` — results "Return to Hub" → `safeBack(router, '/practice/livestock-judging')`
- `app/practice/livestock-judging/drills.tsx` — end-of-session + close → `safeBack(router, '/practice/livestock-judging')`
- `app/practice/meats-id/contest.tsx` — results + mid-contest close → `safeBack(router, '/practice/meats-id')`
- `app/practice/meats-id/quiz.tsx` — results "Return to Menu" → `safeBack(router, '/practice/meats-id')`
- `app/practice/meats-id/grading-drill.tsx` — results + close → `safeBack(router, '/practice/meats-id')`
- `app/practice/meats-id/list.tsx` — backBtn → `safeBack(router, '/practice/meats-id')`
- `app/practice/meats-id/study.tsx` — backBtn → `safeBack(router, '/practice/meats-id')`
- `app/practice/entomology-id/contest.tsx` — results + mid-contest close → `safeBack(router, '/practice/entomology-id')`
- `app/practice/entomology-id/list.tsx` — backBtn → `safeBack(router, '/practice/entomology-id')`
- `app/practice/entomology-id/study.tsx` — backBtn → `safeBack(router, '/practice/entomology-id')`
- `app/practice/floral-id/contest.tsx` — results + mid-contest close → `safeBack(router, '/practice/floral-id')`
- `app/practice/floral-id/exam.tsx` — results + mid-exam close → `safeBack(router, '/practice/floral-id')`
- `app/practice/floral-id/list.tsx` — backBtn → `safeBack(router, '/practice/floral-id')`
- `app/practice/floral-id/study.tsx` — backBtn → `safeBack(router, '/practice/floral-id')`
- `app/practice/vet-science-id/contest.tsx` — results + mid-contest close → `safeBack(router, '/practice/vet-science-id')`
- `app/practice/vet-science-id/study.tsx` — results + error state + mid-quiz close → `safeBack(router, '/practice/vet-science-id')`
- `app/practice/vet-science-id/list.tsx` — backBtn → `safeBack(router, '/practice/vet-science-id')`
- `app/practice/vet-science-id/flashcards.tsx` — error state + close → `safeBack(router, '/practice/vet-science-id')`
- `app/practice/nursery-landscape-id/contest.tsx` — selection back + results → `safeBack(router, '/practice/nursery-landscape-id')`
- `app/practice/nursery-landscape-id/exam.tsx` — results + mid-exam close → `safeBack(router, '/practice/nursery-landscape-id')`
- `app/practice/nursery-landscape-id/list.tsx` — backBtn → `safeBack(router, '/practice/nursery-landscape-id')`
- `app/practice/nursery-landscape-id/study.tsx` — backBtn → `safeBack(router, '/practice/nursery-landscape-id')`
- `app/practice/nursery-landscape-id/flashcards.tsx` — backBtn → `safeBack(router, '/practice/nursery-landscape-id')`
- `app/practice/wildlife/contest.tsx` — selection back + results → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/exam.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/flashcards.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/habitat-eval.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/id-hub.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/list.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/plant-preference.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/population.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/species-id.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/study.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/wildlife/techniques.tsx` — backBtn → `safeBack(router, '/practice/wildlife')`
- `app/practice/poultry-eval/parts.tsx` — results + mid-contest close → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/poultry-eval/processed.tsx` — results + mid-contest close → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/poultry-eval/exam.tsx` — hub selection backBtn → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/poultry-eval/carcass-placing.tsx` — results + mid-session close → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/poultry-eval/eggs.tsx` — results + mid-session close → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/poultry-eval/live-placing.tsx` — results + mid-session close → `safeBack(router, '/practice/poultry-eval')`
- `app/practice/chapter-conducting/quiz.tsx` — results + mid-quiz close → `safeBack(router, '/practice/chapter-conducting')`
- `app/practice/forestry/contest.tsx` — results "Return to Hub" → `safeBack(router, '/practice/forestry')`
- `app/practice/forestry/station.tsx` — station ghostBtn → `safeBack(router, '/practice/forestry')`
- `app/practice/ag-tech/math-drill.tsx` — results + close → `safeBack(router, '/practice/ag-tech')`
- `app/practice/ag-sales/pitch.tsx` — results "Return to Ag Sales Hub" → `safeBack(router, '/practice/ag-sales')`
- `app/practice/agronomy/grain-grading.tsx` — backButton → `safeBack(router, '/practice/agronomy')`
- `app/practice/agronomy/id.tsx` — results + close → `safeBack(router, '/practice/agronomy')`
- `app/practice/farm-ag-management.tsx` — header back + exit → `safeBack(router, '/(tabs)/cde')`
- `app/practice/video.tsx` — back link + exit button → `safeBack(router, '/(tabs)')`
- `app/practice/flashcard.tsx` — Done "Back to Hub" → `safeBack(router, '/(tabs)')`
- `app/practice/forages-id/list.tsx` — backBtn → `safeBack(router, '/practice/forages-id')`
- `app/practice/forages-id/study.tsx` — backBtn → `safeBack(router, '/practice/forages-id')`
- `app/practice/forages-id/flashcards.tsx` — backBtn → `safeBack(router, '/practice/forages-id')`
- `app/practice/job-interview/phone.tsx` — feedback "Back to Prep" → `safeBack(router, '/practice/job-interview')`
- `app/practice/job-interview/video.tsx` — feedback "Finish Session" → `safeBack(router, '/practice/job-interview')`
- `app/contest/[id].tsx` — error state "Go Back" → `safeBack(router, '/(tabs)/cde')`
- `app/contest/creed-speaking.tsx` — already uses `canGoBack()` + `router.replace('/')` fallback ✓
- `app/contest/spanish-creed-speaking.tsx` — already uses `canGoBack()` + `router.replace('/')` fallback ✓
- `lib/navigation.ts` — shared `safeBack` utility

---

## Do NOT change

- `router.back()` calls inside error Alert handlers (mid-flow dismissals) — these are fine
- `router.back()` in modal close handlers — modals always have a parent
- Navigation inside `(auth)` flows — Expo Router handles auth redirects
