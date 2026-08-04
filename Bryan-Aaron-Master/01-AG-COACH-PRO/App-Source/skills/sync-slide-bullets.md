---
name: sync-slide-bullets
description: Reads every slide deck in lib/data/slide-decks/ and rewrites the matching bullets[] in app/practice/livestock-judging/basics.tsx to reflect the actual slide content. Run this any time a slide deck is changed.
---

# Sync Slide Deck Bullets

When a slide deck changes, the educational bullets shown below each step card in `basics.tsx` must be updated to match the actual deck content. This skill automates that.

## When to run

Run this skill any time you:
- Replace images in a slide deck folder
- Add, remove, or reorder slides in any `lib/data/slide-decks/**/*.ts` file
- Change slide titles or points in a deck file
- Add a new species step that has a `slidedeck` entry

## What it does

1. Reads every slide deck `.ts` file in `lib/data/slide-decks/`
2. Extracts the `deckId`, all `title` values, and the first bullet point from each slide's `points[]`
3. Finds the matching step in `basics.tsx` by `deckId`
4. Rewrites the `bullets[]` for that step to reflect the actual deck content (4 bullets max, derived from the most important slides)
5. Commits and pushes the change

---

## Step 1 — Extract all deck content

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && python3 << 'PYEOF'
import re, json, glob

decks = {}
for filepath in sorted(glob.glob('lib/data/slide-decks/**/*.ts', recursive=True)):
    if filepath.endswith(('index.ts', 'types.ts')):
        continue
    content = open(filepath).read()

    # Extract deckId
    deck_id_match = re.search(r"deckId:\s*'([^']+)'", content)
    if not deck_id_match:
        continue
    deck_id = deck_id_match.group(1)

    # Extract all slide titles (skip first — that's the deck title)
    titles = re.findall(r'title:\s*"([^"]+)"', content)
    slide_titles = titles[1:] if len(titles) > 1 else titles

    # Extract first point from each slide's points array
    points_blocks = re.findall(r'points:\s*\[(.*?)\]', content, re.DOTALL)
    first_points = []
    for pb in points_blocks:
        pts = re.findall(r'"([^"]+)"', pb)
        if pts:
            first_points.append(pts[0])

    decks[deck_id] = {
        'file': filepath,
        'slide_count': len(slide_titles),
        'titles': slide_titles,
        'first_points': first_points,
    }

print(json.dumps(decks, indent=2))
PYEOF
```

Review the output — each deck entry shows its `deckId`, slide titles, and the first point of each slide.

---

## Step 2 — Generate new bullets for each deck

For each deck, synthesize 4 bullets that summarize what students will learn. Rules:
- Pull language directly from the slide titles and first points — don't invent content
- Each bullet = one key concept from the deck, written as a student-facing takeaway
- Max 4 bullets, ~12 words each
- Lead with the most important concept first

Use this prompt with Claude to generate bullets for a specific deck:

```
Given these slide deck titles and first points, write exactly 4 student-facing bullet points
(~12 words each) that summarize what students will learn. Pull language directly from the content.
Do not invent new content.

Deck: [deckId]
Slides: [paste titles + first_points from Step 1 output]
```

---

## Step 3 — Update basics.tsx

Find the matching step by its `deckId` and replace the `bullets[]` array. The step structure is:

```ts
{
  id: 'goats-data',
  ...
  bullets: [
    'BULLET 1',
    'BULLET 2',
    'BULLET 3',
    'BULLET 4',
  ],
  slidedeck: { deckId: 'goat-data-deck' },  // ← match this deckId
}
```

Edit `app/practice/livestock-judging/basics.tsx` directly.

---

## Step 4 — Commit and push

```bash
cd "/Volumes/Samsung PSSD T7/ag-coach-app" && git add app/practice/livestock-judging/basics.tsx && git commit -m "sync: update slide deck bullets to match current deck content" && git push
```

---

## Deck → Step mapping reference

| deckId | Step in basics.tsx |
|---|---|
| `muscle` | `cattle-muscle` |
| `cattle-finish-deck` | `cattle-finish` |
| `bovine-structure-slides` | `cattle-structure` |
| `cattle-balance-deck` | `cattle-balance` |
| `beef-epd-deck` | `cattle-epds` |
| `swine-muscle` | `swine-muscle` |
| `swine-finish-deck` | `swine-finish` |
| `swine-structure-deck` | `swine-structure` |
| `swine-balance-deck` | `swine-balance` |
| `swine-data-deck` | `swine-data` |
| `sheep-muscle` | `sheep-muscle` |
| `sheep-finish-deck` | `sheep-finish` |
| `sheep-structure-deck` | `sheep-structure` |
| `sheep-balance-deck` | `sheep-balance` |
| `sheep-data-deck` | `sheep-epds` |
| `goat-muscle` | `goats-muscle` |
| `goat-finish-deck` | `goats-finish` |
| `goat-structure-deck` | `goats-structure` |
| `goat-balance-deck` | `goats-balance` |
| `goat-data-deck` | `goats-data` |

---

## Full automated run (single command)

If you want to regenerate ALL bullets at once, paste the deck JSON from Step 1 into a Claude prompt with this instruction:

```
For each deck in the JSON below, generate 4 student-facing bullet points (~12 words each)
derived directly from the slide titles and first points. Return a TypeScript object mapping
deckId → string[4] bullets array. Do not invent content.

[paste Step 1 JSON output]
```

Then apply the returned bullets to the matching steps in basics.tsx.
