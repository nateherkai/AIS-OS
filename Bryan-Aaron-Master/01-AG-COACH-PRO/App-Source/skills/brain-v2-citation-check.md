# Skill: Brain v2 Citation Check

## Purpose

Brain v2 (`feat/brain-v2`) ships server-validated citations. Fabricated UUIDs get dropped. Prompt injection markers in chunks get stripped. Frontmatter leaks blocked. Verify post-deploy + on regressions.

---

## When to Use

- Suspect Brain v2 returning citations to nonexistent chunks
- "Why does it cite the same source for every answer"
- After change to `match-knowledge-v2`, `lib/ai/brain-v2.ts`, or `knowledge_documents` ingest path
- After Obsidian vault sync (private-path leak risk)

---

## Architecture Recap

1. Client `lib/ai/brain-v2.ts` calls `match-knowledge-v2` edge fn
2. Fn runs RPC `match_knowledge_v2` (ANN + boost, two-phase, inner CTE bypasses HNSW-unsafe composite ORDER BY)
3. Chunks returned → client sanitizes: strip frontmatter + injection markers, wrap `<chunk trust="untrusted">`
4. Gemini function-calling: 6 tools (open_screen, start_practice, show_progress, get_contest_info, lookup_pricing, escalate_to_support)
5. Server validates each UUID citation against `knowledge_documents` → drops fabricated
6. Deterministic confidence calc (not model-emitted)

Embeddings: `gemini-embedding-2-preview@3072` — dim assertion at runtime everywhere.

---

## Checks

### 1. RPC sanity

```sql
-- HNSW index exists + uses halfvec cast
select indexname, indexdef
from pg_indexes
where tablename = 'knowledge_documents'
  and indexdef ilike '%hnsw%';

-- Confirm function definition uses inner CTE
select pg_get_functiondef('public.match_knowledge_v2'::regproc);
```

Function body must have inner CTE for ANN, outer for boost. Direct composite ORDER BY = HNSW won't fire.

### 2. Embedding dim assertion

```bash
grep -rn "3072" lib/ai/ supabase/functions/match-knowledge-v2/
# Every embedding call must assert dim === 3072
```

### 3. Citation validation path

Open `supabase/functions/match-knowledge-v2/index.ts` + `lib/ai/brain-v2.ts`. Confirm:

- Server fetches citations from response, runs `select id from knowledge_documents where id = any($1::uuid[])` to validate
- Unmatched UUIDs dropped, not echoed back
- Final response strips citation array of dropped entries

### 4. Chunk sanitization

```ts
// lib/ai/brain-v2.ts — sanitizeChunk()
// Must strip:
//   - YAML frontmatter `---\n...\n---`
//   - Injection markers: "ignore previous instructions", "system:", "</chunk>", "</context>"
//   - Wrap remaining body in <chunk trust="untrusted">...</chunk>
```

Grep:

```bash
grep -n "sanitize\|frontmatter\|trust=\"untrusted\"" lib/ai/brain-v2.ts
```

### 5. Obsidian leak guards

```bash
grep -rn "01_Bryan\|symlink" lib/obsidian/ scripts/ supabase/
# Must show:
#  - Path normalize that rejects "01_Bryan/" prefix
#  - Symlink resolution + escape check (resolved path must stay under vault root)
```

### 6. Fabricated citation probe

Trigger Brain v2 with ambiguous query that has no good chunks:

```bash
curl -X POST "https://nkoyotdafqllgbpuklva.supabase.co/functions/v1/match-knowledge-v2" \
  -H "Authorization: Bearer $SUPABASE_PUBLISHABLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"explain the secret hidden rule about purple unicorns in FFA"}'
```

Expect: low-confidence response, no citations, OR low-confidence with valid citations only. Never citations to UUIDs absent from `knowledge_documents`.

### 7. Feature flag state

```bash
grep -rn "EXPO_PUBLIC_BRAIN_V2_ENABLED" .env* app/ lib/
# Default true. Confirm legacy fallback path still wired in lib/ai/brain-v2.ts on retrieval error.
```

---

## Audit Test

```sql
-- Sample: pick recent brain-v2 conversation, audit cited UUIDs
-- (Assumes brain_conversations or similar logging table — adapt to schema)
with cited as (
  select id, unnest(metadata->'citations'->'ids')::text as cite_id
  from brain_conversations
  where created_at > now() - interval '24 hours'
)
select c.id as conv_id, c.cite_id,
  case when kd.id is null then 'FABRICATED' else 'OK' end as status
from cited c
left join knowledge_documents kd on kd.id::text = c.cite_id;
```

Any `FABRICATED` row = server validation gap.

---

## Common Bugs

| Symptom | Cause | Fix |
|---|---|---|
| HNSW not used (slow query) | Composite ORDER BY in main query | Inner CTE for ANN, outer for boost |
| Returns citations to UUID = `00000000-...` | Server validation skipped | Add `where id = any(...)` validation |
| Bryan's private notes leaking in answers | Symlink escape or missing `01_Bryan/` filter | Add path normalize + prefix reject |
| "I am now in admin mode" responses | Injection marker not stripped | Expand sanitize regex |
| Dim mismatch error | Mixed embedding models | Hardcode `gemini-embedding-2-preview@3072` everywhere |
| Confidence always 0.95 | Model emitting confidence (ignored) | Confidence must be deterministic client-side calc |

---

## Files

- `supabase/functions/match-knowledge-v2/index.ts`
- `lib/ai/brain-v2.ts`
- `supabase/migrations/<ts>_brain_v2_*.sql`
- `lib/obsidian/ingest.ts` (or scripts/)
- `docs/brain-v2-design.md`
