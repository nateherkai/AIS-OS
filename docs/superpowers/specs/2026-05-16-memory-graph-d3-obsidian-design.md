# Memory Graph — D3-force Obsidian-clone Design

**Date:** 2026-05-16
**Goal:** Replace custom force-sim renderer in `dashboard/index.html` with D3-force impl matching Obsidian Graph View behavior — pan, zoom, drag-to-move, hover highlights 1-hop neighborhood w/ kind colors, constant gentle drift, dimmed colored edges that brighten on hover.
**Approach:** B (D3-force) + E2 (hybrid edges — colored but dimmed at rest, full on hover).

## Scope

Replaces `runForceGraph(nodes, edges)` body in `dashboard/index.html`. Adds D3 v7 CDN script. Keeps `KIND_COLORS`, filters, hub detection, node renderer markup, pulse fire logic.

## Architecture

### Library
- D3 v7: `<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>` in `<head>` (or before runForceGraph)

### SVG structure
```
<svg id="graph-svg">
  <defs>...glow filters (existing)...</defs>
  <g id="zoom-root">         <-- new: pan/zoom transform applied here
    <g id="g-stars"/>        <-- star field
    <g id="g-edges"/>        <-- thin colored filaments
    <g id="g-pulses"/>       <-- traveling fire dots
    <g id="g-nodes"/>        <-- node groups (halo+core+hot+label)
  </g>
</svg>
```

### Forces
| Force | Param | Value |
|---|---|---|
| forceManyBody | strength | -1200 |
| forceLink | distance | `160 + (degreeOf(src) + degreeOf(tgt)) * 4` |
| forceLink | strength | 0.08 |
| forceCollide | radius | `d.size + 14` |
| forceCenter | strength | 0.02 |
| simulation | alphaDecay | 0 (never cool) |
| simulation | alphaMin | 0 |
| simulation | alphaTarget | 0.04 (constant gentle drift) |

### Interactions
- **Pan:** `d3.zoom()` on SVG, transform applied to `#zoom-root`
- **Zoom:** wheel, scaleExtent [0.3, 4]
- **Drag node:** `d3.drag()` on each node `<g>`, sets `d.fx/d.fy` while dragging, restored to null on end. alphaTarget bumps to 0.3 during drag, back to 0.04 after.
- **Hover:** mouseenter → highlight neighborhood, mouseleave → restore
- **Click:** pin selection (sticky highlight) + call existing `showGraphNode(n)` on second click

### Hover highlight algorithm
```
function highlightNode(idx, on) {
  const focused = new Set([idx, ...neighbors[idx]]);
  nodeEls.forEach((g, i) => {
    g.style.opacity = on ? (focused.has(i) ? 1 : 0.12) : 1;
    const lbl = g.querySelector('.node-label');
    if (lbl) lbl.style.opacity = on ? (focused.has(i) ? 1 : 0) : (isHub[i] ? 1 : 0);
  });
  edgeEls.forEach((e, i) => {
    const link = links[i];
    const touch = focused.has(link.s) || focused.has(link.t);
    e.style.opacity = on ? (touch ? 0.85 : 0.04) : 0.08;
    e.style.strokeWidth = on && touch ? '1.2' : '0.7';
  });
}
```

### Edge rendering (E2 hybrid)
- Stroke: kind-colored (source kind's color), alpha 0.08 at rest
- Width: 0.7 at rest, 1.2 on highlight
- Pulses: keep current 55% fire rate logic — runs independently of hover

### Hubs
- Compute top-5 nodes by degree on graph build
- Hubs get permanent label
- Hubs render with `n.size *= 1.4` (set before D3 init)

### State
- `selectedIdx`: int | null — sticky pinned node
- Click empty SVG → selectedIdx = null
- If a node is selected, its highlight stays applied; hover overlays additional but doesn't override

## Out of scope (v1)
- Smooth zoom-to-fit
- Search-jump-to-node
- Multi-select
- Touch gestures
- 3D depth shading
- Edge bundling

## Files modified
- `dashboard/index.html` — D3 script tag + `runForceGraph` body rewrite

## Success criteria
- Graph spreads across full canvas, drifts continuously
- Pan/zoom work smoothly
- Drag any node → physics responds
- Hover node → that + 1-hop neighbors stay bright (kind colors), everything else fades to 12%
- Edges dim cyan/purple at rest, bright on hover
- Top-5 hubs always labeled — easy to find central structure
- Click → showGraphNode opens detail panel (existing function)

## Rollback
Git revert to commit before this change. Custom force-sim restored.
