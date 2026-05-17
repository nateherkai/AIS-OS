# Teacher Role Bulletproofing — Design Spec

**Date:** 2026-05-13
**Driver:** Trinity (Athens ISD, Lone Star Elite). Chapter/school name does not persist on save; invited teaching partner landed as student; new trial signups defaulting to student.
**Goal:** Three guarantees.
1. Trinity and her teaching partner log in flawlessly with their existing accounts — no re-signup, no manual remediation visible to them.
2. Every teacher account (existing and future) carries `user_metadata.role = 'teacher'`. The "student misclassification" pathway is closed at every layer.
3. Free trials always create teacher accounts. Students cannot start a trial and cannot purchase subscriptions.

---

## Root Causes (Confirmed)

1. **Save-profile data loss.** `app/(admin)/subscription.tsx` collects `schoolName` in UI but `handleSave` calls `TeacherService.updateChapterProfile(chapterName, phoneNumber, streetAddress, city, state, zipCode)` (`lib/teacher.ts:853`) — `schoolName` argument does not exist on the function. The `biz_chapters` upsert has no `school_name` column. `auth.updateUser` metadata write does not include `school_name`. After a successful save, the local Zustand store is not refreshed, so `useState` initial values remain stale on every remount.

2. **Invitation acceptance leaves app role unchanged.** `accept_invitation` RPC (`supabase/migrations/046_accept_invitation.sql`) inserts a `memberships` row at the invited school role (`member`/`admin`) but never updates `auth.users.user_metadata.role`. App routing (`AuthGate`, all `(admin)` routes) reads `user_metadata.role`. A user who signed up as `student` and later accepted a teacher invite remains in the student app forever.

3. **Trial signup default is `student`.** `app/(auth)/signup.tsx:22` reads `roleParam === 'teacher' ? 'teacher' : 'student'`. Direct visits to `/signup` (or trial CTAs that omit the `role` query param) drop into student mode. Marketing trial paths are not audited for the `role=teacher` param.

4. **Tier-purchase / trial-start endpoints do not enforce `role=teacher`.** `create-payment-intent`, Stripe webhook upgrades, and the trial-provisioning path in `signUp → provisionTeacher` are gated by code shape rather than by a server-side role check.

---

## Architecture

Five workstreams. (1) is a one-time remediation script. (2)–(5) are durable fixes shipped together as a single PR + migration set.

### 1. In-Place Repair (one-time, tonight)

Script: `scripts/repair-athens-isd-roles.ts` (or Bash + `psql` + service-role REST). Run from local with service-role key. Idempotent.

Steps:
- Resolve Athens ISD `schools.id` by exact name match. Verify `subscription_tier = 'enterprise'`. Bail if not found or ambiguous.
- For every `memberships` row at that school (`status='active'`):
  - Fetch `auth.users` user.
  - If `user_metadata.role !== 'teacher'`: call `auth.admin.updateUserById(user_id, { user_metadata: { ...existing, role: 'teacher' } })`.
  - If `user_metadata.chapter_name` empty: backfill from `biz_chapters.chapter_name` or `schools.name`.
  - If `user_metadata.school_name` empty: backfill from `schools.name`.
- Print a summary: how many accounts repaired, which fields backfilled.
- For Trinity specifically: also write the values she attempted to save (Bryan supplies via Trinity over the phone or email). Writes to both `biz_chapters` and `user_metadata`.
- After updates: revoke her existing refresh tokens with `auth.admin.signOut(user_id, 'others')` so her next app open pulls a fresh JWT carrying the new metadata. (Avoids stale 1-hour JWT showing old role.)

Acceptance: Trinity opens app → lands on admin dashboard, chapter/school filled. Partner opens app → admin dashboard, listed as teacher in Team screen.

### 2. Save Flow Fix

Files: `app/(admin)/subscription.tsx`, `lib/teacher.ts`, new migration `074_biz_chapters_school_name.sql`.

- Migration adds `school_name text` to `biz_chapters`.
- `TeacherService.updateChapterProfile` new signature:
  ```ts
  updateChapterProfile(args: {
    schoolName: string;
    chapterName: string;
    phoneNumber: string;
    streetAddress: string;
    city: string;
    state: string;
    zipCode: string;
  }): Promise<boolean>
  ```
  Pass object, not positional. Avoids future drop-on-floor bugs.
- Upsert writes `school_name` + `chapter_name` to `biz_chapters`.
- `auth.updateUser` writes both to `user_metadata`.
- On success: `const { data } = await supabase.auth.refreshSession(); useAuthStore.setState({ user: data.user, session: data.session });`
- `subscription.tsx`: replace `useState(user?.user_metadata?.x ?? '')` with `useState('')` + `useEffect` that syncs from `user.user_metadata` on store change. Edits stay local until save; save resets from refreshed metadata.

Acceptance: profile save persists across reload, sign-out/in, and app restart.

### 3. Invite → Role Promotion (Two Layers)

**Layer A — Edge function + client integration.**

- New edge function `promote-to-teacher` (service-role). Input: caller JWT. Verifies caller has at least one `memberships` row at `status='active'`. If yes and `user_metadata.role !== 'teacher'`: calls `auth.admin.updateUserById` to set `role='teacher'`, returns `{ promoted: true }`.
- `app/accept-invite.tsx` after `TeacherTeam.acceptInvitation` success:
  - Invoke `promote-to-teacher`.
  - `await supabase.auth.refreshSession()`; push fresh user into `useAuthStore`.
  - `router.replace('/(admin)')` (not just success card).

**Layer B — DB trigger fallback.**

- New migration `075_promote_membership_role.sql`. Trigger on `memberships` insert/update `WHEN status='active'`. Writes to a new `pending_role_promotions(user_id, requested_at, processed_at)` table.
- Cron edge function `drain-role-promotions` (every 5 min via Supabase scheduled function). For each unprocessed row, call `auth.admin.updateUserById` if user is still student. Marks `processed_at`.
- Why two layers: Layer A handles the standard accept-invite flow with no extra latency. Layer B catches Clever SSO, manual SQL insert, future provisioning paths. Belt + suspenders.

Acceptance: any path that creates an active membership for a user → that user is `role='teacher'` within 5 min, ≤1 second on the standard flow.

### 4. Trial / Subscription Gating

**Signup:**

- `signup.tsx:22`: change default. New rule: if any of `chapter_name`, `phone_number`, etc are non-empty, OR `intent=trial` query param present, OR `?role=teacher` → force teacher. Student is the explicit non-default; toggle still shown but requires opt-in plus a class/team code (already required today).
- Audit `app/index.tsx`, marketing landing CTAs — all "Start Free Trial" buttons must route to `/signup?role=teacher&intent=trial`.

**Server-side enforcement (the bulletproof half):**

- `provisionTeacher` (in `lib/store/auth.ts` ~ line 26+): reject if calling user role is not teacher. (Cannot happen via current paths but adds defense.)
- New edge function `start-trial` (service-role) — wraps subscription provisioning. Validates caller `user_metadata.role === 'teacher'`. Returns 403 if student.
- `supabase/functions/create-payment-intent/index.ts`: add role check. Reject 403 if `user_metadata.role !== 'teacher'`. Today the function trusts caller.
- DB-level: RLS policies on `subscriptions`, `biz_subscriptions`, `schools` write paths restrict to `auth.jwt() ->> 'role'` (Supabase app role, not Postgres role) = `'teacher'`. Read access unchanged.

Acceptance: any student attempt to hit `start-trial` or `create-payment-intent` returns 403. Trial provisioning impossible without `role=teacher`.

### 5. Verification

- **Smoke test script** `scripts/smoke-test-invite-flow.ts`:
  1. Create disposable email + signup as student.
  2. Insert invitation via service role for a test school.
  3. Call accept-invite RPC.
  4. Refresh session.
  5. Assert `user_metadata.role === 'teacher'`.
  6. Assert membership exists.
  7. Hit `create-payment-intent` as the same user — expect success.
  8. Same flow with a never-invited student — expect 403.
- **Pre-deploy manual check** with Bryan: log in as Trinity (with her permission) → confirm admin dashboard, profile filled, partner visible as teacher.
- **Post-deploy regression sentinel:** add `console.warn` in `AuthGate` when user has ≥1 active `memberships` row but `role !== 'teacher'`. Page Bryan on first occurrence.

---

## Data Model Changes

- `biz_chapters`: add `school_name text`.
- New `pending_role_promotions(id uuid pk, user_id uuid, requested_at timestamptz, processed_at timestamptz null)`.
- Migration files:
  - `074_biz_chapters_school_name.sql`
  - `075_promote_membership_role.sql` (table + trigger)
  - `076_subscription_role_rls.sql` (RLS policies for trial/sub gating)

---

## Rollout Order

1. Ship migrations 074, 075, 076.
2. Deploy edge functions `promote-to-teacher`, `drain-role-promotions`, `start-trial`. Update `create-payment-intent`.
3. Deploy app changes (`signup.tsx`, `subscription.tsx`, `teacher.ts`, `accept-invite.tsx`).
4. Run `repair-athens-isd-roles.ts` against production. Confirm with Bryan + Trinity.
5. Smoke-test script against production.
6. Set up cron schedule for `drain-role-promotions` (every 5 min).

---

## Risk + Reversibility

- Migrations are additive (new column, new table, new policies). RLS policies can be `DROP POLICY` to revert if a legitimate path breaks.
- `promote-to-teacher` is idempotent and gated on existing active membership — no path to spurious promotion.
- The repair script is idempotent. Re-running causes no drift.
- Refresh-token revoke for Trinity forces one extra login on her next session. Acceptable cost for clean JWT.

---

## Out of Scope

- Migrating `user_metadata.role` storage to a proper `users.app_role` column. Worth doing eventually but not required here.
- Reworking the Stripe webhook to validate role end-to-end (covered indirectly by RLS).
- Clever SSO path verification (Layer B catches it; explicit audit deferred).
