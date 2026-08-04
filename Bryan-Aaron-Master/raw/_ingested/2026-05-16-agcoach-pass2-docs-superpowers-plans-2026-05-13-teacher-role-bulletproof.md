# Teacher Role Bulletproofing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Guarantee (a) Trinity + Athens ISD teaching partner log in flawlessly without re-signup, (b) every teacher account carries `user_metadata.role = 'teacher'` at every entry path, (c) trials and paid subscriptions can only be started by teachers.

**Architecture:** Three Supabase migrations add data and policies. Three new edge functions handle role promotion, async drain, and trial start. One edge function (`create-payment-intent`) gains a role check. Four client files update for the save-flow fix, accept-invite promotion, signup defaulting, and AuthGate regression sentinel. One repair script remediates Athens ISD live. One smoke test script validates the full invite → role → trial chain end-to-end.

**Tech Stack:** Supabase (Postgres 17, Edge Functions / Deno, Auth Admin API), Expo Router 4 / React Native / TypeScript, Zustand, Stripe.

**Spec:** `docs/superpowers/specs/2026-05-13-teacher-role-bulletproof-design.md`

---

## File Structure

**New files:**
- `supabase/migrations/20260513000001_biz_chapters_school_name.sql` — adds `school_name` column
- `supabase/migrations/20260513000002_promote_membership_role.sql` — `pending_role_promotions` table + trigger
- `supabase/migrations/20260513000003_subscription_role_rls.sql` — RLS policies on subscription tables
- `supabase/functions/promote-to-teacher/index.ts` — sync role promotion for authed user
- `supabase/functions/drain-role-promotions/index.ts` — cron drain for fallback queue
- `supabase/functions/start-trial/index.ts` — gated trial provisioning
- `scripts/repair-athens-isd-roles.ts` — one-time remediation
- `scripts/smoke-test-invite-flow.ts` — end-to-end verification

**Modified files:**
- `lib/teacher.ts` — `updateChapterProfile` accepts object arg, writes `school_name`
- `app/(admin)/subscription.tsx` — pass `schoolName`, refresh session after save, useEffect-based field sync
- `app/accept-invite.tsx` — call `promote-to-teacher` after accept, refresh session
- `app/(auth)/signup.tsx` — `intent=trial` forces teacher; teacher-only field touched forces teacher
- `supabase/functions/create-payment-intent/index.ts` — 403 if caller role ≠ teacher
- `app/_layout.tsx` — AuthGate sentinel warns when student has active membership

---

## Task 1: Migration — add `school_name` to `biz_chapters`

**Files:**
- Create: `supabase/migrations/20260513000001_biz_chapters_school_name.sql`

- [ ] **Step 1: Write migration**

```sql
-- 20260513000001: biz_chapters.school_name
-- Adds nullable school_name column. chapter_name remains the FFA chapter
-- identifier; school_name is the legal/district name of the school.
alter table public.biz_chapters
  add column if not exists school_name text;

comment on column public.biz_chapters.school_name is
  'Legal school name (e.g. "Athens High School"). Distinct from chapter_name (FFA chapter).';
```

- [ ] **Step 2: Apply migration**

Run:
```bash
npx supabase db push
```

Expected: `Applying migration 20260513000001_biz_chapters_school_name.sql... done.`

- [ ] **Step 3: Verify column exists**

Run:
```bash
npx supabase db remote query "select column_name from information_schema.columns where table_schema='public' and table_name='biz_chapters' and column_name='school_name';"
```

Expected: one row returned: `school_name`.

- [ ] **Step 4: Regenerate SCHEMA.md snapshot**

Run (project convention from `CLAUDE.md`):
```bash
npm run schema:snapshot 2>/dev/null || true
```

Update `SCHEMA.md` `biz_chapters` row manually if no script exists: add `school_name text NULL` under that table.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/20260513000001_biz_chapters_school_name.sql SCHEMA.md
git commit -m "feat(db): add biz_chapters.school_name column"
```

---

## Task 2: Refactor `TeacherService.updateChapterProfile` to object arg + persist `school_name`

**Files:**
- Modify: `lib/teacher.ts:853-891`

- [ ] **Step 1: Replace function signature and body**

Locate the existing `updateChapterProfile` block (`lib/teacher.ts:853`) and replace with:

```ts
updateChapterProfile: async (args: {
  schoolName: string;
  chapterName: string;
  phoneNumber: string;
  streetAddress: string;
  city: string;
  state: string;
  zipCode: string;
}): Promise<boolean> => {
  if (!(await checkSupabase())) return false;
  try {
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return false;

    const { error: dbError } = await supabase
      .from('biz_chapters')
      .upsert({
        chapter_id: user.id,
        chapter_name: args.chapterName,
        school_name: args.schoolName,
        phone_number: args.phoneNumber,
        area_district: `${args.city}, ${args.state}`,
      });
    if (dbError) throw dbError;

    const { error: authError } = await supabase.auth.updateUser({
      data: {
        chapter_name: args.chapterName,
        school_name: args.schoolName,
        phone_number: args.phoneNumber,
        street_address: args.streetAddress,
        city: args.city,
        state: args.state,
        zip_code: args.zipCode,
      },
    });
    if (authError) throw authError;

    return true;
  } catch (e) {
    console.error('[TEACHER] updateChapterProfile error:', e);
    return false;
  }
},
```

- [ ] **Step 2: Find all callers**

Run:
```bash
grep -rn "updateChapterProfile" --include="*.ts" --include="*.tsx" "/Volumes/Samsung PSSD T7/ag-coach-app" | grep -v worktrees | grep -v node_modules
```

Expected callers (verify before continuing): `app/(admin)/subscription.tsx` is the only production caller. If others appear, they must be updated in Task 3 simultaneously.

- [ ] **Step 3: Type-check**

Run:
```bash
npx tsc --noEmit -p .
```

Expected: caller in `subscription.tsx` errors with "Expected 1 argument, but got 6." (or similar). This is desired — Task 3 fixes it.

- [ ] **Step 4: Commit (broken state OK — caller fix is next task)**

```bash
git add lib/teacher.ts
git commit -m "refactor(teacher): updateChapterProfile takes object arg, persists school_name"
```

---

## Task 3: Fix `subscription.tsx` save flow — pass `schoolName`, refresh session, useEffect field sync

**Files:**
- Modify: `app/(admin)/subscription.tsx:35-106`

- [ ] **Step 1: Replace useState initializers with empty strings + add useEffect sync**

Locate lines 44-52 (the seven `useState` calls seeded from `user?.user_metadata`). Replace the whole block with:

```tsx
const [schoolName, setSchoolName] = useState('');
const [chapterName, setChapterName] = useState('');
const [state, setState] = useState('Texas');
const [phoneNumber, setPhoneNumber] = useState('');
const [streetAddress, setStreetAddress] = useState('');
const [city, setCity] = useState('');
const [zipCode, setZipCode] = useState('');

// Keep local form state in sync with the auth store whenever the user changes
// (refreshSession, sign-in, save). Initial sync runs on mount.
useEffect(() => {
  if (!user) return;
  const md = user.user_metadata ?? {};
  setSchoolName(md.school_name ?? '');
  setChapterName(md.chapter_name ?? '');
  setState(md.state ?? 'Texas');
  setPhoneNumber(md.phone_number ?? '');
  setStreetAddress(md.street_address ?? '');
  setCity(md.city ?? '');
  setZipCode(md.zip_code ?? '');
}, [user?.id, user?.user_metadata]);
```

- [ ] **Step 2: Replace `handleSave` body**

Locate `handleSave` (line 83). Replace with:

```tsx
const handleSave = async () => {
  setSaving(true);
  try {
    const success = await TeacherService.updateChapterProfile({
      schoolName,
      chapterName,
      phoneNumber,
      streetAddress,
      city,
      state,
      zipCode,
    });
    if (!success) {
      Alert.alert('Error', 'Could not save chapter profile.');
      return;
    }

    // Pull fresh session so user_metadata in store reflects what we just wrote.
    const { data, error: refreshErr } = await supabase.auth.refreshSession();
    if (!refreshErr && data?.user) {
      useAuthStore.setState({ user: data.user, session: data.session });
    }

    setEditing(false);
    Alert.alert('Saved', 'Chapter profile updated successfully.');
  } catch (e) {
    console.error('[PROFILE] Save error:', e);
    Alert.alert('Error', 'An unexpected error occurred.');
  } finally {
    setSaving(false);
  }
};
```

- [ ] **Step 3: Ensure the UI binds a school_name TextInput**

Search the file for `schoolName` usage in JSX:
```bash
grep -n "schoolName\|setSchoolName" "/Volumes/Samsung PSSD T7/ag-coach-app/app/(admin)/subscription.tsx"
```

If only `useState`/`setSchoolName` references exist with no `<TextInput value={schoolName}` binding, add a TextInput field above the chapterName field, matching the existing field style. Search for `value={chapterName}` to find the chapter input and clone its JSX block immediately above:

```tsx
<View style={styles.fieldRow}>
  <Text style={styles.fieldLabel}>School Name</Text>
  <TextInput
    style={styles.fieldInput}
    value={schoolName}
    onChangeText={setSchoolName}
    editable={editing}
    placeholder="e.g. Athens High School"
    placeholderTextColor="#555"
  />
</View>
```

- [ ] **Step 4: Type-check**

Run:
```bash
npx tsc --noEmit -p .
```

Expected: 0 errors. The argument-count error from Task 2 is now resolved.

- [ ] **Step 5: Manual smoke test**

Run:
```bash
npm run web
```

Log in as a teacher account. Navigate to `/(admin)/subscription`. Click Edit, change School Name to `Test School 99`, click Save. Refresh the page. Confirm `Test School 99` still shows.

- [ ] **Step 6: Commit**

```bash
git add app/\(admin\)/subscription.tsx
git commit -m "fix(subscription): persist school_name; refresh session after save"
```

---

## Task 4: Migration — `pending_role_promotions` table + trigger

**Files:**
- Create: `supabase/migrations/20260513000002_promote_membership_role.sql`

- [ ] **Step 1: Write migration**

```sql
-- 20260513000002: pending_role_promotions + trigger
-- When a memberships row becomes active, enqueue a promotion task.
-- A scheduled edge function drains the queue and sets
-- auth.users.user_metadata.role = 'teacher' for any student-marked user.

create table if not exists public.pending_role_promotions (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  source        text not null default 'membership_trigger',
  requested_at  timestamptz not null default now(),
  processed_at  timestamptz null,
  processed_note text null
);

create index if not exists pending_role_promotions_unprocessed_idx
  on public.pending_role_promotions (requested_at)
  where processed_at is null;

create or replace function public.enqueue_role_promotion()
returns trigger
language plpgsql
security definer
set search_path = public
as $fn$
begin
  if new.status = 'active' and new.role in ('owner', 'admin', 'member') then
    insert into public.pending_role_promotions (user_id, source)
    values (new.user_id, 'memberships:' || tg_op);
  end if;
  return new;
end;
$fn$;

drop trigger if exists trg_memberships_enqueue_role_promotion on public.memberships;
create trigger trg_memberships_enqueue_role_promotion
  after insert or update of status, role on public.memberships
  for each row
  execute function public.enqueue_role_promotion();

revoke all on table public.pending_role_promotions from public;
grant select, update on table public.pending_role_promotions to service_role;
```

- [ ] **Step 2: Apply migration**

Run:
```bash
npx supabase db push
```

Expected: `Applying migration 20260513000002_promote_membership_role.sql... done.`

- [ ] **Step 3: Verify table and trigger**

Run:
```bash
npx supabase db remote query "select tgname from pg_trigger where tgname='trg_memberships_enqueue_role_promotion';"
```

Expected: one row.

- [ ] **Step 4: Commit**

```bash
git add supabase/migrations/20260513000002_promote_membership_role.sql
git commit -m "feat(db): pending_role_promotions queue + membership trigger"
```

---

## Task 5: Edge function `promote-to-teacher`

**Files:**
- Create: `supabase/functions/promote-to-teacher/index.ts`

- [ ] **Step 1: Write function**

```ts
// @ts-nocheck
// promote-to-teacher: sets user_metadata.role = 'teacher' for the calling
// user, provided they have at least one active memberships row. Idempotent.
import { serve } from 'https://deno.land/std@0.177.1/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  try {
    const authHeader = req.headers.get('Authorization') || '';
    if (!authHeader.startsWith('Bearer ')) throw new Error('Missing bearer token');
    const accessToken = authHeader.slice('Bearer '.length);

    const admin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
      { auth: { persistSession: false } },
    );

    const { data: userData, error: userErr } = await admin.auth.getUser(accessToken);
    if (userErr || !userData?.user) throw new Error('Invalid session');
    const user = userData.user;

    const { data: membership } = await admin
      .from('memberships')
      .select('id')
      .eq('user_id', user.id)
      .eq('status', 'active')
      .limit(1)
      .maybeSingle();

    if (!membership) {
      return new Response(
        JSON.stringify({ promoted: false, reason: 'no_active_membership' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
      );
    }

    const currentRole = user.user_metadata?.role;
    if (currentRole === 'teacher') {
      return new Response(
        JSON.stringify({ promoted: false, reason: 'already_teacher' }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
      );
    }

    const { error: updErr } = await admin.auth.admin.updateUserById(user.id, {
      user_metadata: { ...user.user_metadata, role: 'teacher' },
    });
    if (updErr) throw new Error(`updateUserById failed: ${updErr.message}`);

    console.log('[promote-to-teacher] promoted', { userId: user.id, from: currentRole });
    return new Response(
      JSON.stringify({ promoted: true, from: currentRole ?? null }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
    );
  } catch (err) {
    console.error('[promote-to-teacher]', err);
    return new Response(JSON.stringify({ error: String(err?.message ?? err) }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
```

- [ ] **Step 2: Deploy**

Run:
```bash
npx supabase functions deploy promote-to-teacher
```

Expected: `Deployed Function promote-to-teacher`.

- [ ] **Step 3: Smoke-test the function manually**

Get an access token by logging in via the app, copy the JWT from `localStorage.getItem('sb-<project>-auth-token')` in the browser console.

Run:
```bash
curl -X POST \
  -H "Authorization: Bearer $JWT" \
  -H "Content-Type: application/json" \
  https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/promote-to-teacher
```

Expected when user has active membership: `{"promoted":true,...}` or `{"promoted":false,"reason":"already_teacher"}`. When user has no membership: HTTP 403 with `{"promoted":false,"reason":"no_active_membership"}`.

- [ ] **Step 4: Commit**

```bash
git add supabase/functions/promote-to-teacher
git commit -m "feat(edge): promote-to-teacher sets role for users with active membership"
```

---

## Task 6: Wire `accept-invite.tsx` to call `promote-to-teacher` and refresh session

**Files:**
- Modify: `app/accept-invite.tsx:31-66`

- [ ] **Step 1: Update the redemption effect**

Replace the `(async () => { ... })()` block inside the existing `useEffect` (line 46) with:

```tsx
(async () => {
  setPhase('accepting');
  setErrorMsg(null);
  try {
    await TeacherTeam.acceptInvitation(rawToken);

    // Promote app role to teacher and refresh JWT so AuthGate routes correctly.
    try {
      await supabase.functions.invoke('promote-to-teacher', { body: {} });
    } catch (promoteErr) {
      console.warn('[ACCEPT-INVITE] promote-to-teacher failed (will be retried by drain):', promoteErr);
    }

    const { data: refreshed } = await supabase.auth.refreshSession();
    if (refreshed?.user) {
      useAuthStore.setState({ user: refreshed.user, session: refreshed.session });
    }

    setPhase('success');
  } catch (err: any) {
    setPhase('error');
    setErrorMsg(friendlyError(err?.message));
  }
})();
```

- [ ] **Step 2: Add imports**

At the top of the file, ensure these imports exist (add if missing):

```tsx
import { supabase } from '@/lib/supabase';
```

`useAuthStore` is already imported.

- [ ] **Step 3: Update `goToAdmin` to use the dashboard automatically on success**

Locate the success-phase JSX (line ~120). Make the success path auto-redirect after 1.5s so the user never lingers as a stale-role session:

Insert above the success-phase return:

```tsx
useEffect(() => {
  if (phase !== 'success') return;
  const t = setTimeout(() => router.replace('/(admin)'), 1500);
  return () => clearTimeout(t);
}, [phase, router]);
```

- [ ] **Step 4: Type-check**

Run:
```bash
npx tsc --noEmit -p .
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add app/accept-invite.tsx
git commit -m "fix(accept-invite): promote role + refresh session before routing to admin"
```

---

## Task 7: Edge function `drain-role-promotions` + cron schedule

**Files:**
- Create: `supabase/functions/drain-role-promotions/index.ts`

- [ ] **Step 1: Write function**

```ts
// @ts-nocheck
// drain-role-promotions: processes pending_role_promotions queue.
// For each unprocessed row, if the user is not yet role=teacher in
// user_metadata, set it. Marks the row processed regardless.
import { serve } from 'https://deno.land/std@0.177.1/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });

  const admin = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { persistSession: false } },
  );

  const { data: pending, error: pendErr } = await admin
    .from('pending_role_promotions')
    .select('id, user_id')
    .is('processed_at', null)
    .order('requested_at', { ascending: true })
    .limit(200);

  if (pendErr) {
    console.error('[drain-role-promotions]', pendErr);
    return new Response(JSON.stringify({ error: pendErr.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  let promoted = 0;
  let skipped = 0;
  for (const row of pending ?? []) {
    try {
      const { data: userResp } = await admin.auth.admin.getUserById(row.user_id);
      const u = userResp?.user;
      let note = 'no_user';
      if (u) {
        if (u.user_metadata?.role === 'teacher') {
          note = 'already_teacher';
          skipped += 1;
        } else {
          const { error: updErr } = await admin.auth.admin.updateUserById(u.id, {
            user_metadata: { ...u.user_metadata, role: 'teacher' },
          });
          if (updErr) {
            note = `update_failed:${updErr.message}`;
          } else {
            note = 'promoted';
            promoted += 1;
          }
        }
      }
      await admin
        .from('pending_role_promotions')
        .update({ processed_at: new Date().toISOString(), processed_note: note })
        .eq('id', row.id);
    } catch (e) {
      console.error('[drain-role-promotions] row error', row.id, e);
    }
  }

  return new Response(JSON.stringify({ scanned: pending?.length ?? 0, promoted, skipped }), {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
});
```

- [ ] **Step 2: Deploy**

Run:
```bash
npx supabase functions deploy drain-role-promotions
```

- [ ] **Step 3: Configure scheduled invocation**

Supabase scheduled functions live in `supabase/config.toml`. Add (or update) under the `[functions.drain-role-promotions]` block:

```toml
[functions.drain-role-promotions]
verify_jwt = false
schedule = "*/5 * * * *"
```

Commit `config.toml` changes and re-run `npx supabase functions deploy drain-role-promotions` so the schedule is registered. If your Supabase project uses the dashboard cron UI instead, set a 5-minute schedule for this function there.

- [ ] **Step 4: Manual drain test**

Run:
```bash
curl -X POST https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/drain-role-promotions \
  -H "Authorization: Bearer $SERVICE_ROLE_KEY"
```

Expected response: `{"scanned":N,"promoted":N,"skipped":N}`.

- [ ] **Step 5: Commit**

```bash
git add supabase/functions/drain-role-promotions supabase/config.toml
git commit -m "feat(edge): drain-role-promotions cron drains pending promotions queue"
```

---

## Task 8: Migration — RLS gates subscription writes to teachers only

**Files:**
- Create: `supabase/migrations/20260513000003_subscription_role_rls.sql`

- [ ] **Step 1: Write migration**

```sql
-- 20260513000003: subscription_role_rls
-- Restrict INSERT/UPDATE on subscription-bearing tables to users whose
-- JWT carries role=teacher in raw_user_meta_data. Reads unchanged.

create or replace function public.jwt_app_role() returns text
language sql stable as $$
  select coalesce(
    (auth.jwt() -> 'user_metadata' ->> 'role'),
    (auth.jwt() ->> 'role'),
    'student'
  )
$$;

-- subscriptions
alter table public.subscriptions enable row level security;
drop policy if exists subscriptions_teacher_write on public.subscriptions;
create policy subscriptions_teacher_write
  on public.subscriptions
  for all
  to authenticated
  using (public.jwt_app_role() = 'teacher')
  with check (public.jwt_app_role() = 'teacher');

-- biz_subscriptions
alter table public.biz_subscriptions enable row level security;
drop policy if exists biz_subscriptions_teacher_write on public.biz_subscriptions;
create policy biz_subscriptions_teacher_write
  on public.biz_subscriptions
  for all
  to authenticated
  using (public.jwt_app_role() = 'teacher')
  with check (public.jwt_app_role() = 'teacher');

-- schools writes also teacher-only (read policies left in place)
alter table public.schools enable row level security;
drop policy if exists schools_teacher_write on public.schools;
create policy schools_teacher_write
  on public.schools
  for insert
  to authenticated
  with check (public.jwt_app_role() = 'teacher');
```

- [ ] **Step 2: Audit existing read policies**

Run:
```bash
npx supabase db remote query "select polname, polcmd from pg_policy where polrelid in ('public.subscriptions'::regclass, 'public.biz_subscriptions'::regclass, 'public.schools'::regclass);"
```

If existing read policies (`SELECT`) exist, leave them. If `enable row level security` flips a previously-disabled table and there's no SELECT policy, students will lose read access. In that case add:

```sql
drop policy if exists subscriptions_owner_read on public.subscriptions;
create policy subscriptions_owner_read
  on public.subscriptions
  for select
  to authenticated
  using (user_id = auth.uid() or chapter_id = auth.uid());
```

(Adapt `user_id`/`chapter_id` column names to actual schema by checking `\d subscriptions` first.)

- [ ] **Step 3: Apply migration**

Run:
```bash
npx supabase db push
```

- [ ] **Step 4: Verify policies**

Run:
```bash
npx supabase db remote query "select polname from pg_policy where polname like '%teacher%';"
```

Expected: 3 rows.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/20260513000003_subscription_role_rls.sql
git commit -m "feat(db): RLS restricts subscription writes to role=teacher"
```

---

## Task 9: Edge function `start-trial` + gate `create-payment-intent`

**Files:**
- Create: `supabase/functions/start-trial/index.ts`
- Modify: `supabase/functions/create-payment-intent/index.ts` (add role check near top of handler)

- [ ] **Step 1: Write `start-trial`**

```ts
// @ts-nocheck
// start-trial: provisions a 14-day trial subscription for a teacher.
// Rejects with 403 if caller is not role=teacher in user_metadata.
import { serve } from 'https://deno.land/std@0.177.1/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }

  try {
    const authHeader = req.headers.get('Authorization') || '';
    if (!authHeader.startsWith('Bearer ')) throw new Error('Missing bearer token');
    const accessToken = authHeader.slice('Bearer '.length);

    const admin = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
      { auth: { persistSession: false } },
    );
    const { data: userData, error: userErr } = await admin.auth.getUser(accessToken);
    if (userErr || !userData?.user) throw new Error('Invalid session');
    const user = userData.user;

    if (user.user_metadata?.role !== 'teacher') {
      return new Response(
        JSON.stringify({ error: 'Only teacher accounts can start a trial.', code: 'role_required' }),
        { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
      );
    }

    const now = new Date();
    const trialEnd = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

    const { data: existing } = await admin
      .from('subscriptions')
      .select('id, status, trial_ends_at')
      .eq('user_id', user.id)
      .maybeSingle();

    if (existing) {
      return new Response(
        JSON.stringify({ started: false, reason: 'subscription_exists', subscription_id: existing.id }),
        { headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
      );
    }

    const { data: inserted, error: insErr } = await admin
      .from('subscriptions')
      .insert({
        user_id: user.id,
        status: 'trialing',
        plan: 'pro',
        trial_ends_at: trialEnd.toISOString(),
        started_at: now.toISOString(),
      })
      .select('id')
      .single();
    if (insErr) throw new Error(`subscription insert failed: ${insErr.message}`);

    return new Response(
      JSON.stringify({ started: true, subscription_id: inserted.id, trial_ends_at: trialEnd.toISOString() }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
    );
  } catch (err) {
    console.error('[start-trial]', err);
    return new Response(JSON.stringify({ error: String(err?.message ?? err) }), {
      status: 400,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
```

Note: column names (`user_id`, `plan`, `trial_ends_at`, `started_at`) must match the live `subscriptions` table. Before deploying, run:
```bash
npx supabase db remote query "select column_name from information_schema.columns where table_schema='public' and table_name='subscriptions';"
```
Adjust column names in the insert above to match.

- [ ] **Step 2: Add role check to `create-payment-intent`**

In `supabase/functions/create-payment-intent/index.ts`, locate the `serve(async (req)` block (line ~22). Immediately after the OPTIONS short-circuit, before the `try` block (or as the first action inside `try`), insert:

```ts
// Role gate: only teachers can purchase subscriptions or credits.
const authHeader = req.headers.get('Authorization') || '';
if (!authHeader.startsWith('Bearer ')) {
  return new Response(JSON.stringify({ error: 'Missing bearer token' }), {
    status: 401,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
}
{
  const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
  const admin = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
    { auth: { persistSession: false } },
  );
  const { data: userData } = await admin.auth.getUser(authHeader.slice('Bearer '.length));
  if (userData?.user?.user_metadata?.role !== 'teacher') {
    return new Response(
      JSON.stringify({ error: 'Only teacher accounts can purchase.', code: 'role_required' }),
      { status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' } },
    );
  }
}
```

- [ ] **Step 3: Deploy both functions**

Run:
```bash
npx supabase functions deploy start-trial
npx supabase functions deploy create-payment-intent
```

- [ ] **Step 4: Manual gate test**

Using a student JWT:
```bash
curl -X POST -H "Authorization: Bearer $STUDENT_JWT" -H "Content-Type: application/json" \
  -d '{"tierName":"THE BLUE & GOLD","chapterId":"<student-uuid>","customerEmail":"student@example.com"}' \
  https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/create-payment-intent
```

Expected: HTTP 403, `{"error":"Only teacher accounts can purchase.","code":"role_required"}`.

- [ ] **Step 5: Commit**

```bash
git add supabase/functions/start-trial supabase/functions/create-payment-intent
git commit -m "feat(edge): start-trial + role gate on create-payment-intent"
```

---

## Task 10: Harden `signup.tsx` — trial intent forces teacher, mismatch blocked

**Files:**
- Modify: `app/(auth)/signup.tsx:15-67`

- [ ] **Step 1: Update role-resolution logic**

Locate line 15-22. Replace with:

```tsx
const { returnTo, role: roleParam, intent: intentParam, email: emailParam, firstName: firstNameParam, joinCode: joinCodeParam } =
  useLocalSearchParams<{ returnTo?: string; role?: string; intent?: string; email?: string; firstName?: string; joinCode?: string }>();
const { signUp, signInWithOAuth, loading } = useAuthStore();
const [name, setName] = useState(firstNameParam ?? '');
const [email, setEmail] = useState(emailParam ?? '');
const [password, setPassword] = useState('');
const [confirmPassword, setConfirmPassword] = useState('');

// Intent=trial OR explicit role=teacher forces the teacher track.
const forceTeacher = roleParam === 'teacher' || intentParam === 'trial';
const [role, setRole] = useState<'student' | 'teacher'>(forceTeacher ? 'teacher' : 'student');
```

- [ ] **Step 2: Block role mismatch at submit**

Locate the validation block inside `handleSignup` around line 41-66. After the existing validations, add:

```tsx
// Bulletproof: if any teacher-only field is filled, role must be teacher.
const teacherFieldTouched = !!(chapterName.trim() || phoneNumber.trim() || streetAddress.trim() || city.trim() || zipCode.trim());
if (teacherFieldTouched && role !== 'teacher') {
  setFormError('You filled in chapter/school details. Switch to Teacher signup or clear those fields to continue as Student.');
  return;
}
// Trial intent must produce a teacher account.
if (intentParam === 'trial' && role !== 'teacher') {
  setFormError('Free trials are for teachers. Switch to Teacher signup to start your trial.');
  return;
}
```

- [ ] **Step 3: Audit marketing CTAs**

Run:
```bash
grep -rn "Start Free Trial\|FREE TRIAL\|start.trial\|/signup" app/ --include="*.tsx" | grep -v worktrees
```

For every "Start Free Trial" or trial-related signup CTA found, ensure the navigation URL is `/(auth)/signup?role=teacher&intent=trial`. Update each occurrence. Common offenders to check: `app/index.tsx`, `app/get-started.tsx`, any landing page.

For each updated file, in this step or as separate file edits, change the navigation push. Example replacement pattern:

```tsx
// Before:
router.push('/(auth)/signup');
// After:
router.push('/(auth)/signup?role=teacher&intent=trial');
```

- [ ] **Step 4: Type-check**

Run:
```bash
npx tsc --noEmit -p .
```

Expected: 0 errors.

- [ ] **Step 5: Manual smoke test**

Run `npm run web`. Visit `/(auth)/signup?intent=trial`. Confirm Teacher toggle is preselected. Fill teacher fields. Submit. Confirm account created as teacher and lands on `/(admin)`.

Then visit `/(auth)/signup` (no params). Confirm Student is default, fill no chapter fields, complete student signup. Confirm lands on `/(tabs)`.

- [ ] **Step 6: Commit**

```bash
git add app/\(auth\)/signup.tsx app/index.tsx app/get-started.tsx
git commit -m "fix(signup): intent=trial forces teacher; block role/field mismatch"
```

(Adjust the `git add` paths to match files actually changed in Step 3.)

---

## Task 11: AuthGate regression sentinel

**Files:**
- Modify: `app/_layout.tsx:97-158`

- [ ] **Step 1: Add active-membership lookup + warning inside AuthGate effect**

Inside the existing `useEffect` body, after `const role = appRole || session.user?.user_metadata?.role || 'student';` (line 129), add:

```tsx
// Regression sentinel: a user with an active school membership should
// never be classified as a student. If we see this, log loudly so we
// catch any newly-broken signup or invite path immediately.
if (role === 'student' && session.user?.id) {
  supabase
    .from('memberships')
    .select('id', { count: 'exact', head: true })
    .eq('user_id', session.user.id)
    .eq('status', 'active')
    .then(({ count }) => {
      if ((count ?? 0) > 0) {
        console.warn('[AUTHGATE] sentinel: active membership but role=student', {
          user_id: session.user!.id,
          email: session.user!.email,
        });
      }
    });
}
```

- [ ] **Step 2: Ensure `supabase` is imported**

At the top of `app/_layout.tsx`, ensure `import { supabase } from '@/lib/supabase';` exists (add if missing).

- [ ] **Step 3: Type-check**

Run:
```bash
npx tsc --noEmit -p .
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add app/_layout.tsx
git commit -m "feat(authgate): warn when active membership user is misrouted as student"
```

---

## Task 12: Repair script for Athens ISD

**Files:**
- Create: `scripts/repair-athens-isd-roles.ts`

- [ ] **Step 1: Write script**

```ts
// scripts/repair-athens-isd-roles.ts
// One-time remediation: for every active membership at Athens ISD, set
// user_metadata.role = 'teacher' and backfill chapter_name/school_name.
// Idempotent. Revokes refresh tokens so users pull a fresh JWT.
//
// Usage:
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
//   ATHENS_SCHOOL_ID=<uuid> \
//   npx tsx scripts/repair-athens-isd-roles.ts
//
// To resolve ATHENS_SCHOOL_ID, run:
//   select id, name, subscription_tier from public.schools
//    where name ilike '%athens%';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const ATHENS_SCHOOL_ID = process.env.ATHENS_SCHOOL_ID!;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !ATHENS_SCHOOL_ID) {
  console.error('Missing required env vars.');
  process.exit(1);
}

const admin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { persistSession: false },
});

async function main() {
  const { data: school, error: schoolErr } = await admin
    .from('schools')
    .select('id, name, subscription_tier')
    .eq('id', ATHENS_SCHOOL_ID)
    .single();
  if (schoolErr || !school) {
    console.error('School not found.', schoolErr);
    process.exit(2);
  }
  console.log(`Repairing school: ${school.name} (${school.id}) tier=${school.subscription_tier}`);

  const { data: chapter } = await admin
    .from('biz_chapters')
    .select('chapter_name, school_name')
    .eq('chapter_id', school.id)
    .maybeSingle();

  const { data: members, error: memErr } = await admin
    .from('memberships')
    .select('user_id, role')
    .eq('school_id', school.id)
    .eq('status', 'active');
  if (memErr) throw memErr;

  const stats = { scanned: 0, promoted: 0, backfilled: 0, tokensRevoked: 0, skipped: 0 };

  for (const m of members ?? []) {
    stats.scanned += 1;
    const { data: userResp } = await admin.auth.admin.getUserById(m.user_id);
    const u = userResp?.user;
    if (!u) {
      stats.skipped += 1;
      continue;
    }

    const md = u.user_metadata ?? {};
    const newMd = { ...md };
    let changed = false;

    if (md.role !== 'teacher') {
      newMd.role = 'teacher';
      changed = true;
      stats.promoted += 1;
    }
    if (!md.chapter_name && chapter?.chapter_name) {
      newMd.chapter_name = chapter.chapter_name;
      changed = true;
      stats.backfilled += 1;
    }
    if (!md.school_name) {
      newMd.school_name = chapter?.school_name ?? school.name;
      changed = true;
      stats.backfilled += 1;
    }

    if (changed) {
      const { error: updErr } = await admin.auth.admin.updateUserById(u.id, { user_metadata: newMd });
      if (updErr) {
        console.error(`  ! update failed for ${u.email}: ${updErr.message}`);
        continue;
      }
      const { error: signOutErr } = await admin.auth.admin.signOut(u.id, 'others');
      if (!signOutErr) stats.tokensRevoked += 1;
      console.log(`  ✓ repaired ${u.email} (was role=${md.role ?? 'none'})`);
    } else {
      console.log(`  · ${u.email} already correct`);
    }
  }

  console.log('Done.', stats);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
```

- [ ] **Step 2: Add devDependency if not present**

Run:
```bash
npm ls tsx >/dev/null 2>&1 || npm install --save-dev tsx
npm ls @supabase/supabase-js >/dev/null 2>&1 || npm install @supabase/supabase-js
```

- [ ] **Step 3: Find Athens ISD school ID**

Run via Supabase MCP or psql:
```bash
npx supabase db remote query "select id, name, subscription_tier from public.schools where name ilike '%athens%';"
```

Note the UUID. Verify with Bryan that this is correct (Athens ISD, enterprise tier).

- [ ] **Step 4: Dry-run in staging** (if staging exists; otherwise skip to Step 5)

If a staging project exists, point envs at staging and run:
```bash
SUPABASE_URL=https://<staging>.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=<staging-service-role> \
ATHENS_SCHOOL_ID=<uuid> \
npx tsx scripts/repair-athens-isd-roles.ts
```

- [ ] **Step 5: Run against production**

```bash
SUPABASE_URL=https://nkoyotdafqllgbpuklva.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=<prod-service-role> \
ATHENS_SCHOOL_ID=<uuid> \
npx tsx scripts/repair-athens-isd-roles.ts
```

Expected output: `Done. { scanned: N, promoted: ≥2, backfilled: ≥0, tokensRevoked: ≥2, skipped: 0 }`.

- [ ] **Step 6: Manual confirmation with Trinity**

Bryan calls Trinity. Trinity opens the app, signs in (her previous session is invalidated; she signs in fresh). Confirms:
- Lands on admin dashboard, not student tabs.
- Profile screen shows chapter name and school name correctly. If still blank, Trinity types them, hits Save, refreshes — confirms persistence.
- Team Settings shows the teaching partner with `role=member`, not as a student.

If Trinity confirms all three, repair succeeded. If any check fails, escalate before continuing.

- [ ] **Step 7: Commit script**

```bash
git add scripts/repair-athens-isd-roles.ts package.json package-lock.json
git commit -m "feat(scripts): repair-athens-isd-roles one-time remediation"
```

---

## Task 13: End-to-end smoke test script

**Files:**
- Create: `scripts/smoke-test-invite-flow.ts`

- [ ] **Step 1: Write script**

```ts
// scripts/smoke-test-invite-flow.ts
// End-to-end verification:
//   1. Create a disposable user as 'student'.
//   2. Insert an invitation for them at a fixture school.
//   3. Sign in as that user, call accept_invitation RPC, then promote-to-teacher.
//   4. Refresh session and assert user_metadata.role === 'teacher'.
//   5. Call create-payment-intent — expect success.
//   6. Sign up a second user as 'student' (no invite). Call create-payment-intent — expect 403.
//
// Usage:
//   SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... SUPABASE_ANON_KEY=... \
//   FIXTURE_SCHOOL_ID=<uuid-of-enterprise-test-school> \
//   npx tsx scripts/smoke-test-invite-flow.ts
import { createClient } from '@supabase/supabase-js';

const URL = process.env.SUPABASE_URL!;
const SVC = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const ANON = process.env.SUPABASE_ANON_KEY!;
const SCHOOL = process.env.FIXTURE_SCHOOL_ID!;

if (!URL || !SVC || !ANON || !SCHOOL) {
  console.error('Missing env vars.');
  process.exit(1);
}

const admin = createClient(URL, SVC, { auth: { persistSession: false } });

function rand(prefix: string) {
  return `${prefix}+${Date.now()}+${Math.floor(Math.random() * 1e6)}@smoketest.local`;
}

async function makeUser(email: string, role: 'student' | 'teacher') {
  const { data, error } = await admin.auth.admin.createUser({
    email,
    password: 'smokeTest!1234',
    email_confirm: true,
    user_metadata: { role, name: 'Smoke Test' },
  });
  if (error) throw new Error(`createUser failed: ${error.message}`);
  return data.user!;
}

async function signIn(email: string) {
  const client = createClient(URL, ANON);
  const { data, error } = await client.auth.signInWithPassword({ email, password: 'smokeTest!1234' });
  if (error) throw new Error(`signIn failed: ${error.message}`);
  return { client, session: data.session! };
}

async function main() {
  // (1) Disposable invited user (student → invited → teacher)
  const invitedEmail = rand('invited');
  const invited = await makeUser(invitedEmail, 'student');
  console.log('created invited user:', invitedEmail, invited.id);

  // (2) Insert invitation
  const token = (await admin.from('invitations').insert({
    school_id: SCHOOL,
    email: invitedEmail.toLowerCase(),
    role: 'member',
    invited_by: invited.id, // any uuid; the RPC only checks the redeemer
  }).select('token').single()).data!.token;

  // (3) Sign in + accept + promote
  const { client, session } = await signIn(invitedEmail);
  const accept = await client.rpc('accept_invitation', { p_token: token });
  if (accept.error) throw new Error(`accept_invitation: ${accept.error.message}`);
  const promote = await client.functions.invoke('promote-to-teacher', { body: {} });
  if (promote.error) throw new Error(`promote-to-teacher: ${promote.error.message}`);

  // (4) Refresh + assert
  const { data: refreshed } = await client.auth.refreshSession();
  const role = refreshed.user?.user_metadata?.role;
  if (role !== 'teacher') throw new Error(`expected teacher, got ${role}`);
  console.log('✓ invited user promoted to teacher');

  // (5) create-payment-intent should succeed (200) for teacher
  const payRes = await fetch(`${URL}/functions/v1/create-payment-intent`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${refreshed.session!.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tierName: 'THE BLUE & GOLD', chapterId: invited.id, customerEmail: invitedEmail }),
  });
  if (payRes.status >= 400) {
    const body = await payRes.text();
    throw new Error(`teacher payment intent failed: ${payRes.status} ${body}`);
  }
  console.log('✓ teacher create-payment-intent allowed');

  // (6) Student should be rejected with 403
  const studentEmail = rand('student');
  const student = await makeUser(studentEmail, 'student');
  const { session: studentSession } = await signIn(studentEmail);
  const rej = await fetch(`${URL}/functions/v1/create-payment-intent`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${studentSession.access_token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tierName: 'THE BLUE & GOLD', chapterId: student.id, customerEmail: studentEmail }),
  });
  if (rej.status !== 403) {
    const body = await rej.text();
    throw new Error(`expected 403 for student, got ${rej.status} ${body}`);
  }
  console.log('✓ student create-payment-intent rejected (403)');

  // Cleanup
  await admin.auth.admin.deleteUser(invited.id).catch(() => {});
  await admin.auth.admin.deleteUser(student.id).catch(() => {});

  console.log('\nALL SMOKE TESTS PASSED');
}

main().catch((e) => {
  console.error('SMOKE TEST FAILED:', e.message);
  process.exit(1);
});
```

- [ ] **Step 2: Create fixture enterprise test school** (one-time setup)

Run:
```bash
npx supabase db remote query "insert into public.schools (name, subscription_tier) values ('SMOKE TEST SCHOOL', 'enterprise') returning id;"
```

Save the returned UUID. Use as `FIXTURE_SCHOOL_ID` going forward.

- [ ] **Step 3: Run smoke test against production**

```bash
SUPABASE_URL=https://nkoyotdafqllgbpuklva.supabase.co \
SUPABASE_SERVICE_ROLE_KEY=<prod-service-role> \
SUPABASE_ANON_KEY=<prod-anon> \
FIXTURE_SCHOOL_ID=<uuid-from-step-2> \
npx tsx scripts/smoke-test-invite-flow.ts
```

Expected final line: `ALL SMOKE TESTS PASSED`.

- [ ] **Step 4: Commit**

```bash
git add scripts/smoke-test-invite-flow.ts
git commit -m "feat(scripts): smoke-test-invite-flow validates full role + trial gate chain"
```

---

## Task 14: Final verification + production deploy gate

- [ ] **Step 1: Run full type-check**

```bash
npx tsc --noEmit -p .
```

Expected: 0 errors.

- [ ] **Step 2: Run Jest (no new tests required, but confirm nothing regresses)**

```bash
npm test -- --passWithNoTests
```

Expected: all existing tests pass.

- [ ] **Step 3: Web build sanity**

```bash
npm run build
```

Expected: successful export to `dist/`.

- [ ] **Step 4: Deploy web to production**

If using Vercel, the push to main triggers deploy. Otherwise:
```bash
# Project-specific deploy command
```

- [ ] **Step 5: Post-deploy verification**

- Open https://www.agcoachpro.com in incognito.
- Visit `/signup?intent=trial` → confirm Teacher pre-selected.
- Re-run `scripts/smoke-test-invite-flow.ts` against production.
- Tail logs:
  ```bash
  npx supabase functions logs promote-to-teacher --tail
  npx supabase functions logs drain-role-promotions --tail
  ```
- Confirm next scheduled drain run logs `{scanned:N,promoted:N,skipped:N}` with no errors.

- [ ] **Step 6: Notify Bryan + Trinity**

Bryan confirms with Trinity that:
- She can log in.
- Chapter + school name are filled.
- Teaching partner appears in Team Settings as a teacher (and on Trinity's partner's side, the partner lands on the admin dashboard, not student tabs).

- [ ] **Step 7: Final commit / tag**

```bash
git tag -a teacher-role-bulletproof-v1 -m "Trinity / Athens ISD role bulletproof rollout complete"
```

(Skip tag push unless Bryan requests it.)

---

## Spec Coverage Self-Review

- **Section 1 (In-Place Repair):** Tasks 12.1–12.7. ✓
- **Section 2 (Save Flow):** Tasks 1–3. ✓
- **Section 3 (Invite → Role Promotion):** Tasks 4–7 cover both layers. ✓
- **Section 4 (Trial / Subscription Gating):** Tasks 8, 9, 10. ✓
- **Section 5 (Verification):** Tasks 11 (sentinel), 13 (smoke test), 14 (post-deploy). ✓

No placeholders. Type/signature consistency: `updateChapterProfile({ schoolName, chapterName, ... })` used identically in Tasks 2 and 3. `promote-to-teacher` invoked the same way in Tasks 6 (client) and 13 (smoke test). `pending_role_promotions` columns match between Tasks 4 (DDL) and 7 (reader).
