# Memory Graph Navigation — Design Spec

**Date:** 2026-05-16
**Topic:** Obsidian-style sidebar + minimap for `#memory-graph` view in AIS-OS dashboard
**Scope:** UI/UX rewrite of navigation controls only. Force-simulation engine unchanged.

---

## Problem

Current `#memory-graph` view in `dashboard/index.html`:
- No search box. Cannot jump to a node by name.
- Filter chip row (`#graph-filter-row`) renders but does not produce expected dim/highlight behavior.
- No sort. Cannot order nodes by connections, recency, or type.
- Focus mode (`graphFocusNode`) reachable only by clicking node in canvas; click target hard to hit and unclear.
- No spatial navigation aid. Large graph hard to pan/zoom to discover hubs.

User feedback (2026-05-16): "the memory graph is not sortable" and "hard to maneuver to see areas of the graph".

## Goal

Add Obsidian-clone navigation: persistent left sidebar with search, sort, filter chips, scrollable node list — plus bottom-right minimap for spatial pan.

Mirror the navigation feel of Obsidian's graph view so Bryan can recognize it instantly.

## Non-Goals

- Do not change force-simulation parameters, node sizing, or link rendering.
- Do not change `/api/memory-graph` payload shape (only additive `mtime` field if missing).
- Do not add new data sources.
- Do not touch other dashboard views.

---

## Layout

```
┌─────────────────────────────────────────────┐
│ [≡] Sidebar 280px   │  Graph canvas         │
│ ┌─────────────────┐ │                       │
│ │ 🔍 search…      │ │                       │
│ │ Sort: [Conn ▾]  │ │       (force graph)   │
│ │ Filter chips    │ │                       │
│ │ Node list       │ │           ┌────────┐  │
│ │  • aios (24)    │ │           │minimap │  │
│ │  • ag-coach(18) │ │           └────────┘  │
│ └─────────────────┘ │                       │
└─────────────────────────────────────────────┘
```

- Sidebar fixed 280px wide, full height of `#memory-graph` view, left-aligned.
- Toggle button `≡` in top-left of canvas collapses sidebar to 0px. Default state: open.
- Minimap 180×120 px, anchored bottom-right of canvas, 14px padding from edges.
- Existing `.graph-legend`, `.graph-stats`, `.graph-breadcrumb`, `.graph-focus-btns` remain.

## Sidebar Components

### 1. Search input

- `<input type="search" id="graph-search" placeholder="Find node…">` at top of sidebar.
- Debounced 120 ms on `input` event.
- Match: case-insensitive substring on `node.label`.
- Behavior on non-empty query:
  - List filters to matching rows only.
  - Canvas: non-matching nodes drop to opacity 0.15; matching nodes stay full opacity.
  - Links: dim if both endpoints non-match.
- Clear button (built-in) restores full list and opacity.
- Esc while focused clears query.

### 2. Sort dropdown

- `<select id="graph-sort">` below search.
- Options:
  - `Connections (high→low)` — default. Sort by `degree` (link count for that node).
  - `A → Z` — alphabetical on `label`.
  - `Recently touched` — by `mtime` desc (node mtime from wiki page; for nodes without mtime, sort to bottom).
  - `Type` — group by `node.group` then alpha within group.
- Sort applies to **list order only**. Canvas layout unchanged.

### 3. Filter chips

- Render one chip per unique `node.group` value.
- Chip shows label + count of nodes in that group.
- Click toggles active state.
- Logic: if zero chips active, all groups visible. If one or more active, only nodes whose `group` is in the active set are "matched."
- Behavior identical to search: filtered-out nodes drop to opacity 0.15, links dim if both endpoints filtered out, list filters to matched rows.
- Combines with search via AND (node must satisfy both to stay full).

### 4. Node list

- Scrollable container below filter chips, fills remaining sidebar height.
- Row template: `<div class="graph-list-row"> <span class="dot" style="background:{color}"></span> <span class="label">{label}</span> <span class="badge">{degree}</span> </div>`
- Row click → `graphFocusNode(id)` (existing function): focus mode on, dim non-neighbors, pan+zoom canvas to that node.
- Row hover → temporarily highlight matching node in canvas (same dim treatment as canvas hover).
- Virtualize when total nodes > 200. Render only rows in viewport ± 10. Use plain JS windowing (no library): listen to `scroll` on container, compute `startIdx`/`endIdx` from `scrollTop` / `rowHeight`, render visible rows + top/bottom spacer divs to maintain scroll height. Fixed `rowHeight = 28` px.

## Minimap

- `<canvas id="graph-minimap" width="180" height="120">` anchored bottom-right.
- Render: every 100 ms (10 fps), copy current simulated node positions, scale to minimap dims, draw 2px dots (color = node color, alpha 0.6).
- Viewport rectangle: derived from main canvas current d3-zoom transform. Stroke 1px rgba(212,165,116,0.9).
- Interactions:
  - Drag inside minimap → translates main canvas viewport. Convert minimap delta to world delta via inverse scale.
  - Click empty area → pan main canvas so clicked point becomes center.
  - Wheel inside minimap → zoom main canvas (passthrough to d3-zoom).

## Interaction Matrix

| Action | List | Canvas | Minimap |
|---|---|---|---|
| Search input changes | filter rows | dim non-match | dim non-match |
| Filter chip toggle | filter rows | dim non-match | dim non-match |
| Sort dropdown change | reorder rows | no change | no change |
| Row click | highlight row | focus mode + pan/zoom to node | viewport rect moves |
| Row hover | n/a | highlight node + neighbors | n/a |
| Canvas node click | scroll-to + highlight row | focus mode | viewport rect moves |
| Minimap drag | n/a | pan | rect follows |
| Esc | clear search | clear focus | rect resets |

## Data Contract

`/api/memory-graph` payload extension (additive, backward-compatible):

```json
{
  "nodes": [
    {
      "id": "string",
      "label": "string",
      "group": "string",          // existing — drives filter chips
      "color": "#hex",            // existing
      "size": 14,                 // existing
      "mtime": 1715800000         // NEW — unix seconds, optional, for recency sort
    }
  ],
  "links": [...]                  // unchanged
}
```

Server change: in `dashboard/scripts/memory_graph.py`, when emitting a node sourced from a wiki page, attach `mtime` from `os.path.getmtime` on the source file. Nodes not backed by a file omit the field.

`degree` is computed client-side from `links`, not sent by server.

## Files Affected

- **Modify** `dashboard/index.html`:
  - Add sidebar markup + minimap canvas inside `#memory-graph` view container.
  - Add CSS for `.graph-sidebar`, `.graph-list-row`, `.graph-minimap`, sidebar toggle.
  - Add JS: `setupGraphSidebar()`, `renderNodeList()`, `applyVisibility()`, `setupMinimap()`, `drawMinimap()`. Hook into existing graph-init flow.
- **Modify** `dashboard/scripts/memory_graph.py`:
  - Attach `mtime` to file-backed nodes.

No new files. No new dependencies (d3 already loaded).

## Performance

- List virtualization activates at `nodes.length > 200`. Below threshold, render all rows (simpler).
- Minimap redraw throttled to 10 fps via `setInterval`. Stops when view not visible (`document.visibilityState !== 'visible'`).
- Visibility recompute (dim logic) sets a CSS class on node DOM elements, not per-frame attribute mutation. Class applies opacity transition for smoothness.
- Search debounce 120 ms prevents thrash on fast typing.

## Error & Edge Cases

- Empty graph (zero nodes): sidebar shows "No nodes loaded" placeholder, minimap blank.
- All nodes filtered out: list shows "No matches", canvas all dimmed.
- Node click while focus already active on same node: toggles focus off (reset).
- Sidebar collapsed state persisted in `localStorage` key `graph.sidebarOpen`.
- Sort and active filter chips also persisted: `graph.sort`, `graph.filterGroups`.

## Testing

Manual checklist (no automated UI tests in this project):

1. Open `#memory-graph`. Sidebar visible with search, sort, chips, list. Minimap visible bottom-right.
2. Type "aios" in search. List narrows. Canvas dims non-matching nodes.
3. Clear search. Everything restored.
4. Click "Wiki" filter chip. Only wiki-grouped nodes remain bright in canvas + list.
5. Change sort to "A → Z". List re-orders alphabetically.
6. Click a row in list. Canvas pans+zooms to node, enters focus mode, neighbors lit.
7. Click empty canvas. Focus clears.
8. Drag minimap viewport rectangle. Main canvas pans.
9. Click point in minimap. Main canvas re-centers.
10. Reload page. Sidebar open/closed state, sort, and active filters persist.

## Out of Scope

- Keyboard nav of list (j/k, enter). Defer to follow-up.
- Multi-node selection. Defer.
- Saved searches / pinned nodes. Defer.
- Mobile/responsive sidebar. Dashboard is desktop-only.

---

## Open Questions

None blocking.
