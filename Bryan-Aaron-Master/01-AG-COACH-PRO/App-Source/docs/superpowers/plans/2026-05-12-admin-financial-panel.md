# Admin Financial Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a superadmin-only financial panel to `app/(admin)/index.tsx` showing net income, MRR, burn, paid school count, and trial count — visible only when `role === 'superadmin'`.

**Architecture:** Single-file edit. Add a `FinancialPanel` component and two new state vars (`paidSchools`, `trialSchools`) to the existing `AdminDashboard`. Query `schools` table directly via the existing `supabase` client (already imported in the app via `@/lib/supabase`). Monthly burn is a hardcoded constant updated manually after each Apple Card CSV sync.

**Tech Stack:** React Native, TypeScript, Expo Router, Supabase JS client (`@/lib/supabase`)

**Spec:** `docs/superpowers/specs/2026-05-12-admin-financial-panel-design.md`

---

## File Map

```
app/(admin)/index.tsx   ← Only file changed. Add MONTHLY_BURN constant,
                          FinancialPanel component, paidSchools/trialSchools
                          state, Supabase query in loadData(), render call
                          gated by role === 'superadmin'.
```

---

## Task 1: Add Supabase Import + MONTHLY_BURN Constant

**Files:**
- Modify: `app/(admin)/index.tsx:1-9`

- [ ] **Step 1: Add supabase import and burn constant**

Replace the existing import block (lines 1–9) with:

```typescript

import { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, ActivityIndicator, Modal, TextInput, Alert } from 'react-native';
import { AnimatedButton as TouchableOpacity } from '@/components/common/AnimatedButton';
import { useRouter } from 'expo-router';
import { Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import { TeacherService, TeacherStats, ChapterGamification, Team, ContestEvent, SubscriptionStatus } from '@/lib/teacher';
import { useAuthStore } from '@/lib/store/auth';
import { Theme, GlassEffect } from '@/constants/theme';
import { supabase } from '@/lib/supabase';

// Monthly burn — update after each Apple Card CSV sync in AIOS dashboard
const MONTHLY_BURN = 373;
const MRR_PER_SCHOOL = 124.58;
const SCHOOL_GOAL = 50;
```

- [ ] **Step 2: Type-check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npx tsc --noEmit -p . 2>&1 | grep "index.tsx" | head -10
```

Expected: no errors on `index.tsx`.

- [ ] **Step 3: Commit**

```bash
git add app/(admin)/index.tsx
git commit -m "feat(admin): add supabase import and financial constants"
```

---

## Task 2: FinancialPanel Component

**Files:**
- Modify: `app/(admin)/index.tsx` — insert after line 107 (after `QuickAction` component, before `AddContestModal`)

- [ ] **Step 1: Add FinancialPanel component**

Insert the following block immediately after the closing `);` of the `QuickAction` component (after line 107, before the `// ─── Add Contest Modal` comment):

```typescript
// ─── Financial Panel (superadmin only) ───────────────────────────────────────

interface FinancialPanelProps {
  paidSchools: number;
  trialSchools: number;
}

const FinancialPanel = ({ paidSchools, trialSchools }: FinancialPanelProps) => {
  const mrr = paidSchools * MRR_PER_SCHOOL;
  const net = mrr - MONTHLY_BURN;
  const isPositive = net >= 0;
  const schoolsToBreakEven = Math.ceil(Math.abs(net) / MRR_PER_SCHOOL);
  const goalPct = Math.min((paidSchools / SCHOOL_GOAL) * 100, 100);

  return (
    <View style={fin.wrapper}>
      <Text style={styles.sectionTitle}>FINANCIAL OVERVIEW</Text>

      {/* Net banner */}
      <View style={[fin.banner, isPositive ? fin.bannerPos : fin.bannerNeg]}>
        <View>
          <Text style={fin.bannerLabel}>NET INCOME</Text>
          <Text style={fin.bannerSub}>
            {isPositive
              ? `Profitable — ${SCHOOL_GOAL - paidSchools} schools to goal`
              : `Close ${schoolsToBreakEven} more school${schoolsToBreakEven !== 1 ? 's' : ''} to break even`}
          </Text>
        </View>
        <Text style={[fin.bannerValue, { color: isPositive ? '#4ADE80' : '#f87171' }]}>
          {isPositive ? '+' : ''}${net.toFixed(0)}/mo
        </Text>
      </View>

      {/* KPI row */}
      <View style={fin.kpiRow}>
        <View style={[fin.kpiCard, fin.kpiGold]}>
          <Text style={fin.kpiLabel}>MRR</Text>
          <Text style={[fin.kpiValue, { color: '#F2A900' }]}>${mrr.toFixed(0)}</Text>
          <Text style={fin.kpiSub}>{paidSchools} school{paidSchools !== 1 ? 's' : ''} paid</Text>
        </View>

        <View style={fin.kpiCard}>
          <Text style={fin.kpiLabel}>BURN</Text>
          <Text style={[fin.kpiValue, { color: '#f87171' }]}>${MONTHLY_BURN}</Text>
          <Text style={fin.kpiSub}>update after CSV sync</Text>
        </View>

        <View style={fin.kpiCard}>
          <Text style={fin.kpiLabel}>SCHOOLS</Text>
          <Text style={fin.kpiValue}>
            {paidSchools}
            <Text style={{ fontSize: 18, color: 'rgba(255,255,255,0.25)' }}>/{SCHOOL_GOAL}</Text>
          </Text>
          <View style={fin.progBar}>
            <View style={[fin.progFill, { width: `${goalPct}%` as any }]} />
          </View>
        </View>

        <View style={fin.kpiCard}>
          <Text style={fin.kpiLabel}>TRIALS</Text>
          <Text style={[fin.kpiValue, { color: '#facc15' }]}>{trialSchools}</Text>
          <Text style={fin.kpiSub}>in pipeline</Text>
        </View>
      </View>
    </View>
  );
};

const fin = StyleSheet.create({
  wrapper: { marginBottom: 8 },

  banner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginHorizontal: 16, marginBottom: 12,
    padding: 18, borderRadius: 18, borderWidth: 1,
  },
  bannerPos: { backgroundColor: 'rgba(74,222,128,0.07)', borderColor: 'rgba(74,222,128,0.2)' },
  bannerNeg: { backgroundColor: 'rgba(248,113,113,0.07)', borderColor: 'rgba(248,113,113,0.2)' },
  bannerLabel: { fontSize: 11, fontWeight: '700', color: 'rgba(255,255,255,0.4)', letterSpacing: 1, marginBottom: 4 },
  bannerSub: { fontSize: 12, color: 'rgba(255,255,255,0.3)' },
  bannerValue: { fontSize: 28, fontWeight: '900' },

  kpiRow: {
    flexDirection: 'row', gap: 10,
    paddingHorizontal: 16, marginBottom: 8,
  },
  kpiCard: {
    flex: 1, padding: 14, borderRadius: 16,
    backgroundColor: 'rgba(255,255,255,0.04)',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)',
  },
  kpiGold: {
    backgroundColor: 'rgba(242,169,0,0.07)',
    borderColor: 'rgba(242,169,0,0.2)',
  },
  kpiLabel: {
    fontSize: 9, fontWeight: '700', letterSpacing: 0.8,
    color: 'rgba(255,255,255,0.35)', marginBottom: 6,
  },
  kpiValue: { fontSize: 22, fontWeight: '900', color: '#fff', lineHeight: 26 },
  kpiSub: { fontSize: 9, color: 'rgba(255,255,255,0.3)', marginTop: 4 },
  progBar: {
    height: 3, backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: 2, marginTop: 8, overflow: 'hidden',
  },
  progFill: {
    height: 3, borderRadius: 2,
    backgroundColor: '#F2A900',
  },
});
```

- [ ] **Step 2: Type-check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npx tsc --noEmit -p . 2>&1 | grep "index.tsx" | head -10
```

Expected: no errors on `index.tsx`.

- [ ] **Step 3: Commit**

```bash
git add app/(admin)/index.tsx
git commit -m "feat(admin): add FinancialPanel component"
```

---

## Task 3: State + Data Fetch

**Files:**
- Modify: `app/(admin)/index.tsx:190-221` — add state vars and Supabase query in `loadData`

- [ ] **Step 1: Add paidSchools and trialSchools state**

Find this block (around line 190–198):

```typescript
export default function AdminDashboard() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<TeacherStats | null>(null);
  const [gamification, setGamification] = useState<ChapterGamification | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [events, setEvents] = useState<ContestEvent[]>([]);
  const [showAddContest, setShowAddContest] = useState(false);
  const [sub, setSub] = useState<SubscriptionStatus | null>(null);
```

Replace with:

```typescript
export default function AdminDashboard() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [stats, setStats] = useState<TeacherStats | null>(null);
  const [gamification, setGamification] = useState<ChapterGamification | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [events, setEvents] = useState<ContestEvent[]>([]);
  const [showAddContest, setShowAddContest] = useState(false);
  const [sub, setSub] = useState<SubscriptionStatus | null>(null);
  const [paidSchools, setPaidSchools] = useState(0);
  const [trialSchools, setTrialSchools] = useState(0);
```

- [ ] **Step 2: Add Supabase query inside loadData**

Find the existing `loadData` function:

```typescript
  const loadData = async () => {
    try {
      const [statsData, gameStats, teamsData, eventsData, subData] = await Promise.all([
        TeacherService.getStats(),
        TeacherService.getGamificationStats(),
        TeacherService.getTeams(),
        TeacherService.getContestEvents(),
        TeacherService.getSubscription(),
      ]);
      setStats(statsData);
      setGamification(gameStats);
      setTeams(teamsData);
      setEvents(eventsData);
      setSub(subData);
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  };
```

Replace with:

```typescript
  const loadData = async () => {
    try {
      const [statsData, gameStats, teamsData, eventsData, subData, schoolsData] = await Promise.all([
        TeacherService.getStats(),
        TeacherService.getGamificationStats(),
        TeacherService.getTeams(),
        TeacherService.getContestEvents(),
        TeacherService.getSubscription(),
        supabase.from('schools').select('id, subscription_status').not('id', 'like', '11111111%'),
      ]);
      setStats(statsData);
      setGamification(gameStats);
      setTeams(teamsData);
      setEvents(eventsData);
      setSub(subData);
      if (schoolsData.data) {
        setPaidSchools(schoolsData.data.filter(s => s.subscription_status === 'active').length);
        setTrialSchools(schoolsData.data.filter(s => s.subscription_status === 'trialing').length);
      }
    } catch (e) { console.error(e); }
    finally { setLoading(false); setRefreshing(false); }
  };
```

- [ ] **Step 3: Type-check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npx tsc --noEmit -p . 2>&1 | grep "index.tsx" | head -10
```

Expected: no errors on `index.tsx`.

- [ ] **Step 4: Commit**

```bash
git add app/(admin)/index.tsx
git commit -m "feat(admin): fetch school pipeline counts for financial panel"
```

---

## Task 4: Render FinancialPanel in JSX

**Files:**
- Modify: `app/(admin)/index.tsx` — insert render call after the header `<View>`, before the trial banner

- [ ] **Step 1: Insert FinancialPanel render**

Find this JSX block (around line 260–265):

```typescript
      {/* ── TRIAL BANNER ─────────────────────────────────── */}
      {sub?.isTrialing && (
```

Insert immediately before it:

```typescript
      {/* ── FINANCIAL OVERVIEW (superadmin only) ─────────── */}
      {role === 'superadmin' && (
        <FinancialPanel paidSchools={paidSchools} trialSchools={trialSchools} />
      )}

      {/* ── TRIAL BANNER ─────────────────────────────────── */}
      {sub?.isTrialing && (
```

- [ ] **Step 2: Type-check**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npx tsc --noEmit -p . 2>&1 | grep "index.tsx" | head -10
```

Expected: no errors on `index.tsx`.

- [ ] **Step 3: Verify web build**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npm run web -- --no-open &
sleep 15
kill %1
```

Expected: build completes with no TypeScript or bundle errors.

- [ ] **Step 4: Commit**

```bash
git add app/(admin)/index.tsx
git commit -m "feat(admin): render superadmin financial panel on admin dashboard"
```

---

## Task 5: Deploy + Smoke Test

- [ ] **Step 1: Build for production**

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app"
npm run build
```

Expected: `dist/` produced, no errors.

- [ ] **Step 2: Deploy to Vercel**

```bash
npx vercel --prod
```

Expected: deployment URL printed, no errors.

- [ ] **Step 3: Smoke test on agcoachpro.com/admin**

Open https://www.agcoachpro.com/admin in browser while logged in as Bryan (superadmin).

Verify:
- "FINANCIAL OVERVIEW" section appears above the trial banner
- Net banner shows correct value (red, ~-$248/mo given 1 paid school + $373 burn)
- MRR card shows ~$125
- Schools card shows 1/50 with gold progress bar
- Trials card shows 0
- Section is completely absent when logged in as a teacher account

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add app/(admin)/index.tsx
git commit -m "fix(admin): financial panel smoke test fixes"
```

---

## Self-Review

**Spec coverage:**
- ✓ Superadmin-only gate (`role === 'superadmin'`)
- ✓ Net income banner — red/green, break-even note
- ✓ MRR from live Supabase school count
- ✓ Monthly burn as hardcoded constant (`MONTHLY_BURN = 373`)
- ✓ Paid schools KPI with progress bar toward 50
- ✓ Trial count KPI
- ✓ Styling matches admin screen (`#F2A900`, `rgba(255,255,255,0.04)` glass, `#000` bg)
- ✓ Single file change — no new routes, no new Edge Functions

**No placeholders found.** All code complete.

**Type consistency:** `FinancialPanelProps` defined in Task 2, used identically in Task 4. `paidSchools`/`trialSchools` defined as `number` in Task 3, passed as `number` in Task 4.
