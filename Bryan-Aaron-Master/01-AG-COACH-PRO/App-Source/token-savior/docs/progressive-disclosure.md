# Progressive Disclosure — Memory Search

## Principe

L'accès aux observations mémoire est organisé en **3 layers** au coût croissant.
**Toujours commencer par Layer 1.** On ne descend que si le layer précédent
confirme qu'il y a quelque chose à creuser. Ce contrat minimise le nombre de
tokens dépensés avant d'obtenir la réponse utile.

Conceptuellement : `memory.search` → `memory.timeline` → `memory.get_observations`.
Les noms MCP réels utilisent des underscores (`memory_index`, `memory_search`,
`memory_get`) parce que l'API Anthropic valide les noms d'outils contre
`^[a-zA-Z0-9_-]{1,128}$` et rejette les points. Les deux formes renvoient aux
mêmes handlers — l'outil canonique est celui en underscore.

## Layer 1 — `memory_index` *(conceptuellement `memory.search`)*

- **Input** : `query` optionnel, `type_filter`, `limit`
- **Output** : titres + type + importance + relevance + UCB + age + `ts://obs/{id}`
- **~15 tokens/résultat**
- **Usage** : « existe-t-il des obs sur X ? », vue d'ensemble rapide, shortlist

Le résultat est une table markdown compacte. Chaque ligne se termine par une
URI `[ts://obs/{id}]` qu'on peut passer directement à Layer 3.

## Layer 2 — `memory_search` *(conceptuellement `memory.timeline`)*

- **Input** : `query` (FTS5 : AND/OR/NOT/phrase), `type_filter`, `limit`
- **Output** : hits avec snippets + section « Session rollups » si matches
- **~60 tokens/résultat**
- **Usage** : « quand et dans quel contexte ? », confirmer que Layer 1 matche
  vraiment, filtrer par mots-clés précis

Layer 2 surfaces **aussi** les rollups de session (`session_summaries`) dans
une section séparée — c'est la vue « contexte chronologique » enrichie.

## Layer 3 — `memory_get` *(conceptuellement `memory.get_observations`)*

- **Input** : liste d'IDs (int, digit string, ou `ts://obs/{id}` URI)
- **Output** : contenu complet (`content`, `why`, `how_to_apply`, tags, links)
- **~200 tokens/résultat**
- **Usage** : « donne-moi le détail exact », exploitation finale une fois la
  shortlist confirmée aux layers 1+2

## Token cost table

| Layer | Tool          | Tokens/result | Quand                     |
|-------|---------------|---------------|---------------------------|
| 1     | `memory_index`  | ~15           | Toujours en premier       |
| 2     | `memory_search` | ~60           | Si Layer 1 matche         |
| 3     | `memory_get`    | ~200          | Si Layer 2 confirme       |

## Exemple de flow

```
memory_index(type_filter="guardrail")    # Layer 1 — shortlist par titre
  ↓ une ligne a l'air pertinente, ex: id=42
memory_search(query="token savior mandatory")   # Layer 2 — contexte FTS
  ↓ le snippet confirme, on veut le contenu complet
memory_get(ids=["ts://obs/42"])          # Layer 3 — full content
```

À chaque étape on n'escalade que si le layer précédent a payé en info utile.
