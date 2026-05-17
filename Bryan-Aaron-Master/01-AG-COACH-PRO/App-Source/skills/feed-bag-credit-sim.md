# Skill: Feed Bag Credit Sim

## Purpose

Pre-deploy gate: estimate token burn for new feature against tier credit pools. Prevents launching a feature that drains Greenhand's 5M credits in a week.

---

## When to Use

- New AI-call feature (quiz module, evaluator, brain chat surface)
- Suspected high-burn feature live ("usage alert at 80% hit too fast")
- Pricing review

---

## Credit Pools (annual)

| Tier | Credits | Seats |
|---|---|---|
| Greenhand | 5M | LDE team + individual quiz |
| Blue & Gold | 15M | + 40 CDE logins |
| Lone Star Elite | 40M | Unlimited |
| Feed Bag | +1M | $100 each, rollover |

Alert at 80%. 1 credit ≈ 1 token (input + output combined).

---

## Estimate Inputs

For new feature, gather:

1. **Calls per student per week** (`N`)
2. **Input tokens per call** (`T_in`): prompt + RAG context + history
3. **Output tokens per call** (`T_out`)
4. **Active students per chapter** (assume 25 avg, 40 for B&G cap)
5. **Weeks active per year** (≈40 school weeks)

Burn per chapter per year:

```
burn = N × (T_in + T_out) × students × weeks
```

---

## Reference Burn Rates (existing modules)

| Feature | T_in | T_out | Avg N/wk |
|---|---|---|---|
| RAG quiz (10 Q) | ~4500 | ~2000 | 3 |
| Brain v2 chat turn | ~3000 | ~600 | 8 |
| Livestock evaluator (one set) | ~2500 | ~1500 | 1 |
| Horse lead AI video | tokens N/A (fal cost) | — | 2 |
| Flashcard set | ~3500 | ~1500 | 2 |

Tokens approximate. Actuals in `ai_usage_log` table.

---

## Query Actual Burn

```sql
-- Token burn by feature, last 30 days
select
  feature,
  count(*) as call_count,
  sum(input_tokens + output_tokens) as total_tokens,
  avg(input_tokens + output_tokens)::int as avg_per_call
from ai_usage_log
where created_at > now() - interval '30 days'
group by feature
order by total_tokens desc;
```

```sql
-- Burn by chapter / classroom
select
  c.name as classroom,
  s.tier,
  sum(a.input_tokens + a.output_tokens) as tokens_30d,
  s.credits_remaining
from ai_usage_log a
join public.users u on u.id = a.user_id
join classrooms c on c.id = u.classroom_id
join biz_subscriptions s on s.user_id = c.owner_id
where a.created_at > now() - interval '30 days'
group by c.name, s.tier, s.credits_remaining
order by tokens_30d desc;
```

---

## Sim Worksheet

```
Feature: <name>
Tier required: Blue & Gold
T_in: 4000
T_out: 1500
N per student per week: 5
Students per chapter: 25 (B&G cap 40)
Weeks/yr: 40

burn = 5 × 5500 × 25 × 40 = 27.5M tokens/yr
```

B&G pool = 15M. **Feature alone exceeds pool by 12.5M.** Options:

1. Cap calls per student (rate limit)
2. Cache responses (RAG retrieval, common queries)
3. Move feature to Lone Star Elite (40M pool)
4. Smaller model for first-pass (`gemini-1.5-flash` vs `gemini-1.5-pro`)
5. Reduce `T_in` (tighter RAG chunks, shorter system prompt)
6. Up tier pricing or Feed Bag attach rate

---

## Rate Limit Pattern

```sql
-- Per-user-per-day cap
create table if not exists ai_rate_limit (
  user_id uuid not null,
  day date not null default current_date,
  feature text not null,
  call_count int not null default 0,
  primary key (user_id, day, feature)
);

-- In edge fn, before calling model:
-- INSERT ... ON CONFLICT (user_id, day, feature) DO UPDATE SET call_count = call_count + 1
-- If call_count > CAP → return 429
```

---

## Caching Pattern

For RAG retrieval, hash `(query, filters)` → cache embedding + chunk IDs in `match_knowledge_cache`. Skip re-embed + ANN on cache hit. Cuts input tokens 30-60% on repeat queries.

---

## Output Format

Sim report:

| Feature | T_in | T_out | N/wk | Chapter burn/yr | Tier pool | Margin |
|---|---|---|---|---|---|---|
| Widget eval | 4000 | 1500 | 5 | 27.5M | 15M (B&G) | ❌ -12.5M |
| With rate limit @ 2/day | 4000 | 1500 | 2 | 11M | 15M | ✅ +4M |
