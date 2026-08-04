# Athens ISD FFA — Account Detail

> Generated 2026-05-16 from live Supabase query (biz_chapters + biz_subscriptions)
> This is the first active paying account for Ag Coach Pro.

---

## Account Record

| Field | Value |
|---|---|
| Chapter ID | `2b427269-7c88-4e8e-b80d-fa4b045c57b2` |
| Chapter Name | Athens ISD FFA |
| School Name | Athens ISD FFA |
| Primary Advisor | Athens ISD |
| Contact Email | tdesselles@athensisd.net |
| Phone | Not on file |
| FFA Area | Not on file |
| District | Not on file |
| Lead Stage | Trial (status in DB — but subscription is Active) |
| Tier | The Lone Star Elite ($1,495/yr) |
| Sub Status | Active |
| Trial Started | Not recorded (school-level account pre-dates individual teacher trials) |
| Renewal Date | 2027-05-11 |
| Stripe Sub ID | None (manually invoiced) |
| Created | 2026-04-11 |

---

## Individual Teacher Accounts (Athens ISD teachers on trial)

Four Athens ISD teachers signed up separately 2026-05-14, trial ends 2026-05-28:

| Teacher | Email |
|---|---|
| Theresa Tindel | ttindel@athensisd.net |
| Hunter Choate | hchoate@athensisd.net |
| David Link | dlink@athensisd.net |
| Britney Edwards | bedwards@athensisd.net |

These individual accounts appear to be separate from the school-level Lone Star Elite account. May indicate a multi-teacher department. The teacher-role-bulletproof plan (2026-05-13) was specifically triggered by Athens ISD teachers failing to log in correctly.

---

## History / Notes

- Athens ISD was the **first school account created** in Ag Coach Pro (2026-04-11)
- Referenced in `teacher-role-bulletproof` plan (commit b80b10bb, 2026-05-13): "Trinity + Athens ISD teachers were missing from staff list"
- Lone Star Elite gives unlimited seats and all 11 LDEs — appropriate for a multi-teacher department
- No Stripe subscription ID means billing is manual — need to get them on Stripe for renewal automation

---

## Open Actions

- [ ] Confirm primary contact name (tdesselles — likely "T. Desselles"?)
- [ ] Verify individual teachers are mapped to the school-level Lone Star Elite account (or need upsell)
- [ ] Move to Stripe subscription before 2027-05-11 renewal

---

## Related

- [[_Sales-Pipeline-Home|Sales Pipeline]]
- [[../../wiki/sources/agcoach-plan-supabase-admin|Supabase + Admin Plan]]
- [[../../01-AG-COACH-PRO/_AG-Coach-Home|Ag Coach Pro home]]
