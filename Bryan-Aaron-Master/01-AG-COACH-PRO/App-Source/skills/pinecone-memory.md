# Pinecone Memory System

> **Infinite memory for Claude Code sessions.** Query and store knowledge in Pinecone using natural language — no MCP required.
> 

---

## How It Works

This skill gives any Claude Code session (including Cowork) the ability to **search, store, and manage** memories in a Pinecone vector database. It uses Pinecone's Inference API to convert text → embeddings, then queries your index directly.

| Detail | Value |
| --- | --- |
| **Index** | `agcoachpro` |
| **Embedding Model** | `multilingual-e5-large` (1024 dimensions) |
| **Metric** | Cosine similarity |
| **Host** | `agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io` |

---

## Instructions for Claude

When the user asks you to **search, recall, remember, or store** something in long-term memory, use the following methods. **API key is read from `PINECONE_API_KEY` environment variable** (stored in `.env`).

### Searching Memories (Semantic Query)

This is a **two-step process**: embed the query text, then search Pinecone.

```bash
API_KEY="$PINECONE_API_KEY"

# Step 1: Convert text to embedding via Pinecone Inference API
EMBEDDING=$(curl -s -X POST "https://api.pinecone.io/embed" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Pinecone-API-Version: 2025-01" \
  -d '{"model":"multilingual-e5-large","inputs":[{"text":"YOUR QUERY HERE"}],"parameters":{"input_type":"query","truncate":"END"}}' \
  | python3 -c "import sys,json; print(json.dumps(json.loads(sys.stdin.read())['data'][0]['values']))")

# Step 2: Query Pinecone with the embedding
curl -s -X POST "https://agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io/query" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"vector\":$EMBEDDING,\"topK\":5,\"includeMetadata\":true}" \
  | python3 -m json.tool
```

Replace `YOUR QUERY HERE` with the user's question. Adjust `topK` as needed (default 5).

### Storing Memories

```bash
API_KEY="$PINECONE_API_KEY"

# Step 1: Embed the text (note input_type is "passage" not "query")
EMBEDDING=$(curl -s -X POST "https://api.pinecone.io/embed" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -H "X-Pinecone-API-Version: 2025-01" \
  -d '{"model":"multilingual-e5-large","inputs":[{"text":"TEXT TO STORE"}],"parameters":{"input_type":"passage","truncate":"END"}}' \
  | python3 -c "import sys,json; print(json.dumps(json.loads(sys.stdin.read())['data'][0]['values']))")

# Step 2: Upsert to Pinecone with metadata
curl -s -X POST "https://agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io/vectors/upsert" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"vectors\":[{\"id\":\"mem_$(date +%s)_$(head -c 4 /dev/urandom | xxd -p)\",\"values\":$EMBEDDING,\"metadata\":{\"text\":\"TEXT TO STORE\",\"timestamp\":$(date +%s),\"source\":\"claude-code\"}}]}"
```

### Fetching by ID

```bash
API_KEY="$PINECONE_API_KEY"

curl -s -X GET "https://agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io/vectors/fetch?ids=RECORD_ID" \
  -H "Api-Key: $API_KEY" \
  | python3 -m json.tool
```

### Deleting a Record

```bash
API_KEY="$PINECONE_API_KEY"

curl -s -X POST "https://agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io/vectors/delete" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"ids":["RECORD_ID"]}'
```

### Index Stats

```bash
API_KEY="$PINECONE_API_KEY"

curl -s -X POST "https://agcoachpro-7macm39.svc.aped-4627-b74a.pinecone.io/describe_index_stats" \
  -H "Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

---

## Rules

1. **Always use the configured index** — never query a different index.
2. Default to `topK: 5` unless the user asks for more or fewer results.
3. When storing, always include `source` metadata so we know where it came from.
4. Present query results clearly — show the text content and relevance score.
5. The two-step process (embed then query/upsert) is **required** because the raw Pinecone API only accepts numerical vectors, not text.
