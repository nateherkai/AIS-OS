# Memory Graph — Jack-Clone Visual Redesign

**Date:** 2026-05-16
**Goal:** Make `dashboard/index.html` Memory Graph match Jack Roberts' Claude Code OS visual (sparse, glowing, hover-only labels, neural firing).
**Approach:** A2 targeted tuning (~40 line patch). No code structure changes.

## Changes

### `dashboard/index.html` ~lines 921-963 — node renderer
- Drop outer halo (`n.size+22` circle).
- Keep one soft halo at `n.size+8`, opacity 0.22.
- Core circle at `n.size`, opacity 0.95.
- Hot center at `n.size*0.4`, opacity 0.85.
- **Remove always-on labels.**

### `dashboard/scripts/memory_graph.py` — shrink node sizes
- core 22 → 14
- workspace 12 → 6
- file 7 → 4
- skill 8 → 5
- decision 9 → 5
- vector 14 → 8
- wiki-source/concept 8 → 5
- wiki-person/org 9-10 → 6
- wiki-comparison/analysis 7 → 4

### `dashboard/index.html` ~line 952 — label policy
- Default: no text rendered.
- Compute top-5 hubs by inbound+outbound edge count → render their labels permanently.
- Hover any node → show its label + labels of 1-hop neighbors.
- Click → persistent label sticky until next click.

### `dashboard/index.html` ~lines 966-971 — force sim params
| Param | Old | New |
|---|---|---|
| REPULSION | 14500 | 28000 |
| LINK_K | 0.026 | 0.022 |
| LINK_LEN | 190-250 | 280-360 |
| CENTER_K | 0.003 | 0.0008 |
| COLLISION_PAD | 42 | 24 |
| DAMP | 0.86 | 0.92 |

### `dashboard/index.html` ~line 924 — edge stroke
- alpha 0.34 → 0.18
- width 1.3 → 0.8
- (pulse fire rate kept at 55%)

## Success criteria
- Nodes spread across full canvas with visible gaps.
- ≤6 labels visible at rest.
- Hover lights up node + neighbors w/ labels.
- Edges visible as thin cyan threads (not blob).
- Constant pulse firing along 50%+ edges.

## Out of scope
- 3D feel / depth shading.
- Touch/mobile interactions.
- Server-side label ranking.
- Replacing custom force sim with library.
