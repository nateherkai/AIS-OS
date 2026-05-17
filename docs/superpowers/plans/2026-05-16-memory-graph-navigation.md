# Memory Graph Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Obsidian-style sidebar (search, sort, filter, list) + bottom-right minimap to `#memory-graph` view.

**Architecture:** Single-page edits in `dashboard/index.html` + one additive field in `dashboard/scripts/memory_graph.py`. No new files, no new deps. Reuses existing d3@7 simulation; layers DOM controls + minimap canvas over current SVG.

**Tech Stack:** Vanilla JS + d3@7 + plain CSS. FastAPI server (no change to routes).

**Spec:** `docs/superpowers/specs/2026-05-16-memory-graph-navigation-design.md`

---

## File Structure

- `dashboard/scripts/memory_graph.py` — emit `mtime` on file-backed nodes (additive)
- `dashboard/index.html`:
  - Markup: sidebar container + minimap canvas inside `#memory-graph` view
  - CSS: `.graph-sidebar`, `.graph-list-row`, `.graph-minimap`, sidebar-toggle, dim classes
  - JS: `setupGraphSidebar()`, `renderNodeList()`, `applyVisibility()`, `setupMinimap()`, `drawMinimap()`, persistence (`localStorage`)

---

## Task 1: Backend — emit `mtime` on file-backed nodes

**Files:**
- Modify: `dashboard/scripts/memory_graph.py`

- [ ] **Step 1:** Read `dashboard/scripts/memory_graph.py` end-to-end. Identify the function/loop that builds wiki/page nodes.

- [ ] **Step 2:** For each node whose source is a real file path, attach `node["mtime"] = int(os.path.getmtime(path))`. Skip if path unknown.

- [ ] **Step 3:** Run `python3 dashboard/scripts/memory_graph.py` (or the route handler) and confirm one wiki-source node in output JSON now has integer `mtime` field. Use `curl -s http://localhost:8080/api/memory-graph | python3 -c "import json,sys; d=json.load(sys.stdin); [print(n['id'], n.get('mtime')) for n in d['nodes'][:5]]"`.

- [ ] **Step 4:** Commit.
```bash
git add dashboard/scripts/memory_graph.py
git commit -m "feat(graph): emit mtime on file-backed nodes for recency sort"
```

---

## Task 2: Sidebar markup + CSS (no behavior yet)

**Files:**
- Modify: `dashboard/index.html`

- [ ] **Step 1:** Inside the `#memory-graph` view container, add sidebar shell as the first child:
```html
<aside id="graph-sidebar" class="graph-sidebar open">
  <button class="graph-sidebar-toggle" onclick="toggleGraphSidebar()" title="Toggle sidebar">≡</button>
  <div class="graph-sidebar-body">
    <input type="search" id="graph-search" placeholder="Find node…" autocomplete="off">
    <select id="graph-sort">
      <option value="degree">Connections (high→low)</option>
      <option value="alpha">A → Z</option>
      <option value="recent">Recently touched</option>
      <option value="type">Type</option>
    </select>
    <div class="graph-filter-row" id="graph-filter-row"></div>
    <div class="graph-list" id="graph-list"></div>
  </div>
</aside>
```
Move the existing `#graph-filter-row` element here if it currently sits elsewhere — only one filter row should exist.

- [ ] **Step 2:** Add minimap canvas as a sibling of the SVG canvas, anchored absolutely:
```html
<canvas id="graph-minimap" width="180" height="120"></canvas>
```

- [ ] **Step 3:** Add CSS in the existing `<style>` block:
```css
.graph-sidebar { position:absolute; top:0; left:0; bottom:0; width:280px; background:rgba(0,0,0,0.55); backdrop-filter:blur(10px); border-right:1px solid rgba(255,255,255,0.08); display:flex; flex-direction:column; transition:width 0.18s; z-index:5; overflow:hidden; }
.graph-sidebar:not(.open) { width:0; }
.graph-sidebar-toggle { position:absolute; top:10px; right:-36px; width:32px; height:32px; border:1px solid rgba(255,255,255,0.12); background:rgba(0,0,0,0.55); color:#D4A574; border-radius:7px; cursor:pointer; font-size:18px; backdrop-filter:blur(8px); }
.graph-sidebar-body { padding:14px 12px; display:flex; flex-direction:column; gap:10px; height:100%; box-sizing:border-box; overflow:hidden; }
#graph-search { background:rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.12); border-radius:7px; padding:8px 10px; color:#fff; font-size:14px; }
#graph-sort { background:rgba(0,0,0,0.5); border:1px solid rgba(255,255,255,0.12); border-radius:7px; padding:7px 10px; color:#fff; font-size:13px; }
.graph-list { flex:1; overflow-y:auto; border-top:1px solid rgba(255,255,255,0.06); padding-top:8px; position:relative; }
.graph-list-row { display:flex; align-items:center; gap:8px; padding:5px 8px; border-radius:5px; cursor:pointer; height:28px; box-sizing:border-box; font-size:13px; color:rgba(255,255,255,0.82); }
.graph-list-row:hover { background:rgba(212,165,116,0.12); color:#D4A574; }
.graph-list-row .dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.graph-list-row .label { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.graph-list-row .badge { font-size:11px; color:rgba(255,255,255,0.45); }
.graph-list-row.active { background:rgba(212,165,116,0.2); color:#D4A574; }
#graph-minimap { position:absolute; bottom:14px; right:14px; background:rgba(0,0,0,0.55); border:1px solid rgba(255,255,255,0.1); border-radius:8px; backdrop-filter:blur(8px); cursor:crosshair; z-index:6; }
.graph-dimmed { opacity:0.15 !important; transition:opacity 0.18s; }
```

- [ ] **Step 4:** Hard refresh `http://localhost:8080/#memory-graph`. Confirm sidebar visible left, minimap visible bottom-right, toggle button present. No JS behavior yet expected.

- [ ] **Step 5:** Commit.
```bash
git add dashboard/index.html
git commit -m "feat(graph): sidebar shell + minimap canvas markup and CSS"
```

---

## Task 3: Sidebar JS — search, sort, filter, list, persistence

**Files:**
- Modify: `dashboard/index.html` (JS section)

- [ ] **Step 1:** Add the following functions to the existing graph JS block (after the existing graph init that sets `window.__graphNodes` / `window.__graphLinks` / `window.__graphSimulation`):

```javascript
const GRAPH_LS = { sidebar: 'graph.sidebarOpen', sort: 'graph.sort', filter: 'graph.filterGroups' };
let __graphSearch = '';
let __graphSortMode = localStorage.getItem(GRAPH_LS.sort) || 'degree';
let __graphActiveGroups = new Set(JSON.parse(localStorage.getItem(GRAPH_LS.filter) || '[]'));
let __graphDegree = new Map();

function toggleGraphSidebar() {
  const el = document.getElementById('graph-sidebar');
  el.classList.toggle('open');
  localStorage.setItem(GRAPH_LS.sidebar, el.classList.contains('open') ? '1' : '0');
}

function computeDegrees() {
  __graphDegree.clear();
  for (const l of window.__graphLinks || []) {
    const s = typeof l.source === 'object' ? l.source.id : l.source;
    const t = typeof l.target === 'object' ? l.target.id : l.target;
    __graphDegree.set(s, (__graphDegree.get(s) || 0) + 1);
    __graphDegree.set(t, (__graphDegree.get(t) || 0) + 1);
  }
}

function nodeMatches(n) {
  if (__graphSearch && !(n.label || n.id || '').toLowerCase().includes(__graphSearch)) return false;
  if (__graphActiveGroups.size > 0 && !__graphActiveGroups.has(n.group)) return false;
  return true;
}

function sortedNodes() {
  const arr = [...(window.__graphNodes || [])];
  if (__graphSortMode === 'degree') arr.sort((a,b) => (__graphDegree.get(b.id)||0) - (__graphDegree.get(a.id)||0));
  else if (__graphSortMode === 'alpha') arr.sort((a,b) => (a.label||'').localeCompare(b.label||''));
  else if (__graphSortMode === 'recent') arr.sort((a,b) => (b.mtime||0) - (a.mtime||0));
  else if (__graphSortMode === 'type') arr.sort((a,b) => (a.group||'').localeCompare(b.group||'') || (a.label||'').localeCompare(b.label||''));
  return arr;
}

function renderFilterChips() {
  const row = document.getElementById('graph-filter-row');
  if (!row) return;
  const counts = new Map();
  for (const n of window.__graphNodes || []) counts.set(n.group, (counts.get(n.group)||0)+1);
  row.innerHTML = '';
  for (const [g, c] of [...counts].sort()) {
    const chip = document.createElement('button');
    chip.className = 'graph-chip' + (__graphActiveGroups.has(g) ? ' active' : '');
    chip.textContent = `${g} (${c})`;
    chip.onclick = () => {
      if (__graphActiveGroups.has(g)) __graphActiveGroups.delete(g); else __graphActiveGroups.add(g);
      localStorage.setItem(GRAPH_LS.filter, JSON.stringify([...__graphActiveGroups]));
      renderFilterChips();
      renderNodeList();
      applyVisibility();
    };
    row.appendChild(chip);
  }
}

function renderNodeList() {
  const container = document.getElementById('graph-list');
  if (!container) return;
  const all = sortedNodes().filter(nodeMatches);
  const useVirtual = all.length > 200;
  if (!useVirtual) {
    container.innerHTML = '';
    if (all.length === 0) { container.innerHTML = '<div style="padding:8px;color:rgba(255,255,255,0.4);font-size:13px">No matches</div>'; return; }
    for (const n of all) container.appendChild(buildRow(n));
    return;
  }
  // Virtualize
  const ROW_H = 28;
  const scrollTop = container.scrollTop;
  const viewportH = container.clientHeight || 400;
  const startIdx = Math.max(0, Math.floor(scrollTop / ROW_H) - 10);
  const endIdx = Math.min(all.length, Math.ceil((scrollTop + viewportH) / ROW_H) + 10);
  container.innerHTML = '';
  const topSpacer = document.createElement('div'); topSpacer.style.height = (startIdx * ROW_H) + 'px'; container.appendChild(topSpacer);
  for (let i = startIdx; i < endIdx; i++) container.appendChild(buildRow(all[i]));
  const botSpacer = document.createElement('div'); botSpacer.style.height = ((all.length - endIdx) * ROW_H) + 'px'; container.appendChild(botSpacer);
  if (!container.__virtScroll) {
    container.__virtScroll = true;
    container.addEventListener('scroll', () => renderNodeList(), { passive: true });
  }
}

function buildRow(n) {
  const row = document.createElement('div');
  row.className = 'graph-list-row';
  row.dataset.nodeId = n.id;
  row.innerHTML = `<span class="dot" style="background:${n.color || '#888'}"></span><span class="label">${n.label || n.id}</span><span class="badge">${__graphDegree.get(n.id) || 0}</span>`;
  row.onclick = () => { graphFocusNode(n.id); highlightListRow(n.id); };
  row.onmouseenter = () => hoverHighlightNode(n.id);
  row.onmouseleave = () => hoverHighlightNode(null);
  return row;
}

function highlightListRow(id) {
  document.querySelectorAll('.graph-list-row.active').forEach(r => r.classList.remove('active'));
  const row = document.querySelector(`.graph-list-row[data-node-id="${CSS.escape(id)}"]`);
  if (row) { row.classList.add('active'); row.scrollIntoView({ block: 'nearest' }); }
}

function hoverHighlightNode(id) {
  document.querySelectorAll('#memory-graph svg .node').forEach(el => {
    el.classList.toggle('graph-dimmed', id !== null && el.__data__?.id !== id);
  });
}

function applyVisibility() {
  document.querySelectorAll('#memory-graph svg .node').forEach(el => {
    el.classList.toggle('graph-dimmed', !nodeMatches(el.__data__));
  });
  document.querySelectorAll('#memory-graph svg .link').forEach(el => {
    const d = el.__data__;
    const s = typeof d.source === 'object' ? d.source : window.__graphNodes.find(n => n.id === d.source);
    const t = typeof d.target === 'object' ? d.target : window.__graphNodes.find(n => n.id === d.target);
    el.classList.toggle('graph-dimmed', !(s && t && nodeMatches(s) && nodeMatches(t)));
  });
}

function setupGraphSidebar() {
  const sb = document.getElementById('graph-sidebar');
  if (localStorage.getItem(GRAPH_LS.sidebar) === '0') sb.classList.remove('open');
  const sortEl = document.getElementById('graph-sort');
  sortEl.value = __graphSortMode;
  sortEl.onchange = () => { __graphSortMode = sortEl.value; localStorage.setItem(GRAPH_LS.sort, __graphSortMode); renderNodeList(); };
  const searchEl = document.getElementById('graph-search');
  let t;
  searchEl.oninput = () => { clearTimeout(t); t = setTimeout(() => { __graphSearch = searchEl.value.trim().toLowerCase(); renderNodeList(); applyVisibility(); }, 120); };
  searchEl.onkeydown = (e) => { if (e.key === 'Escape') { searchEl.value = ''; __graphSearch = ''; renderNodeList(); applyVisibility(); } };
  computeDegrees();
  renderFilterChips();
  renderNodeList();
  applyVisibility();
}
```

- [ ] **Step 2:** Call `setupGraphSidebar()` at the end of the existing graph-init flow (right after the simulation starts and nodes/links are in the DOM). The existing code path that fetches `/api/memory-graph` and sets `window.__graphNodes` is the right hook point.

- [ ] **Step 3:** Add CSS for chips + dimmed link variant (append to existing style block):
```css
.graph-chip { font-size:11px; padding:4px 8px; border-radius:11px; border:1px solid rgba(255,255,255,0.12); background:rgba(0,0,0,0.4); color:rgba(255,255,255,0.65); cursor:pointer; }
.graph-chip.active { background:rgba(212,165,116,0.22); color:#D4A574; border-color:rgba(212,165,116,0.4); }
#memory-graph svg .node.graph-dimmed { opacity:0.15; }
#memory-graph svg .link.graph-dimmed { opacity:0.05; }
```

- [ ] **Step 4:** Hard refresh. Verify:
  - Sidebar shows search, sort dropdown, chips (one per group), node list with dots + counts.
  - Typing in search filters list AND dims canvas nodes.
  - Changing sort reorders list.
  - Clicking chip toggles dim of that group.
  - Clicking row pans canvas to node + enters focus mode.
  - Hovering row dims all other canvas nodes.
  - Reload page → sidebar state + sort + active chips persist.

- [ ] **Step 5:** Commit.
```bash
git add dashboard/index.html
git commit -m "feat(graph): search, sort, filter chips, node list with virtualization"
```

---

## Task 4: Minimap — render + drag + click

**Files:**
- Modify: `dashboard/index.html` (JS section)

- [ ] **Step 1:** Add minimap JS at end of the graph block:
```javascript
let __minimapTimer = null;

function setupMinimap() {
  const c = document.getElementById('graph-minimap');
  if (!c) return;
  const svg = document.querySelector('#memory-graph svg');
  if (!svg) return;
  c.addEventListener('mousedown', (e) => startMinimapDrag(e, c, svg));
  c.addEventListener('click', (e) => { if (!c.__dragging) minimapJumpTo(e, c, svg); });
  c.addEventListener('wheel', (e) => { e.preventDefault(); svg.dispatchEvent(new WheelEvent('wheel', { deltaY: e.deltaY, clientX: window.innerWidth/2, clientY: window.innerHeight/2, bubbles: true })); }, { passive: false });
  if (__minimapTimer) clearInterval(__minimapTimer);
  __minimapTimer = setInterval(() => { if (document.visibilityState === 'visible') drawMinimap(); }, 100);
}

function getGraphBounds() {
  const ns = window.__graphNodes || [];
  if (ns.length === 0) return { minX:0,minY:0,maxX:1,maxY:1 };
  let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
  for (const n of ns) { if (n.x<minX)minX=n.x; if (n.y<minY)minY=n.y; if (n.x>maxX)maxX=n.x; if (n.y>maxY)maxY=n.y; }
  const padX = (maxX-minX)*0.1 || 50, padY = (maxY-minY)*0.1 || 50;
  return { minX:minX-padX, minY:minY-padY, maxX:maxX+padX, maxY:maxY+padY };
}

function drawMinimap() {
  const c = document.getElementById('graph-minimap');
  if (!c) return;
  const ctx = c.getContext('2d');
  ctx.clearRect(0,0,c.width,c.height);
  const ns = window.__graphNodes || [];
  if (ns.length === 0) return;
  const b = getGraphBounds();
  const sx = c.width / (b.maxX-b.minX), sy = c.height / (b.maxY-b.minY);
  const s = Math.min(sx, sy);
  for (const n of ns) {
    if (n.x == null) continue;
    ctx.fillStyle = n.color || '#888';
    ctx.globalAlpha = nodeMatches(n) ? 0.6 : 0.15;
    ctx.beginPath();
    ctx.arc((n.x-b.minX)*s, (n.y-b.minY)*s, 1.6, 0, Math.PI*2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  // Viewport rect: derive from main svg's d3-zoom transform
  const svg = document.querySelector('#memory-graph svg');
  const t = svg && d3.zoomTransform(svg);
  if (t && svg) {
    const w = svg.clientWidth || svg.parentElement.clientWidth;
    const h = svg.clientHeight || svg.parentElement.clientHeight;
    const x0 = (-t.x / t.k - b.minX) * s;
    const y0 = (-t.y / t.k - b.minY) * s;
    const ww = (w / t.k) * s;
    const hh = (h / t.k) * s;
    ctx.strokeStyle = 'rgba(212,165,116,0.9)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x0, y0, ww, hh);
  }
}

function minimapJumpTo(e, c, svg) {
  const rect = c.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const b = getGraphBounds();
  const s = Math.min(c.width/(b.maxX-b.minX), c.height/(b.maxY-b.minY));
  const wx = mx/s + b.minX, wy = my/s + b.minY;
  const t = d3.zoomTransform(svg);
  const w = svg.clientWidth, h = svg.clientHeight;
  const newT = d3.zoomIdentity.translate(w/2 - wx*t.k, h/2 - wy*t.k).scale(t.k);
  d3.select(svg).transition().duration(250).call(window.__graphZoom.transform, newT);
}

function startMinimapDrag(e, c, svg) {
  c.__dragging = false;
  let last = { x: e.clientX, y: e.clientY };
  const onMove = (mv) => {
    c.__dragging = true;
    const b = getGraphBounds();
    const s = Math.min(c.width/(b.maxX-b.minX), c.height/(b.maxY-b.minY));
    const t = d3.zoomTransform(svg);
    const dx = (mv.clientX - last.x) / s * t.k;
    const dy = (mv.clientY - last.y) / s * t.k;
    last = { x: mv.clientX, y: mv.clientY };
    const newT = d3.zoomIdentity.translate(t.x - dx, t.y - dy).scale(t.k);
    d3.select(svg).call(window.__graphZoom.transform, newT);
  };
  const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); setTimeout(()=>{c.__dragging=false;}, 50); };
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
}
```

- [ ] **Step 2:** Ensure `window.__graphZoom` is exposed where d3.zoom() is created in the existing graph code. If currently `const zoom = d3.zoom()...`, change to `const zoom = window.__graphZoom = d3.zoom()...`.

- [ ] **Step 3:** Call `setupMinimap()` at the end of graph init, after `setupGraphSidebar()`.

- [ ] **Step 4:** Hard refresh. Verify:
  - Minimap visible bottom-right with dots matching node positions.
  - Amber viewport rectangle visible, moves when main canvas pans/zooms.
  - Drag inside minimap → main canvas pans.
  - Click point in minimap → main canvas re-centers there with transition.
  - Search/filter changes also dim corresponding minimap dots.

- [ ] **Step 5:** Commit.
```bash
git add dashboard/index.html
git commit -m "feat(graph): minimap with viewport rect, drag-to-pan, click-to-jump"
```

---

## Task 5: Bidirectional sync — canvas click highlights list row

**Files:**
- Modify: `dashboard/index.html` (JS section)

- [ ] **Step 1:** Locate the existing canvas node click handler that calls `graphFocusNode(id)`. Add a call to `highlightListRow(id)` immediately after it.

- [ ] **Step 2:** Locate the existing `graphResetFocus()` function. Add at the end:
```javascript
document.querySelectorAll('.graph-list-row.active').forEach(r => r.classList.remove('active'));
```

- [ ] **Step 3:** Add Esc-anywhere reset. After `setupGraphSidebar()` call, add:
```javascript
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && document.querySelector('#memory-graph.active, [data-view=memory-graph].active, #memory-graph:not([hidden])')) {
    if (typeof graphResetFocus === 'function') graphResetFocus();
  }
});
```
(Use whichever active-view selector already indicates the graph view is showing — adapt to existing convention.)

- [ ] **Step 4:** Hard refresh. Verify:
  - Click node on canvas → corresponding list row gets `.active` class and scrolls into view.
  - Click ↺ Reset → list row deselects.
  - Esc while on graph view → focus clears.

- [ ] **Step 5:** Commit.
```bash
git add dashboard/index.html
git commit -m "feat(graph): sync canvas selection to list + esc to reset focus"
```

---

## Final verification

Manual run-through of spec checklist (10 steps in spec "Testing" section). Confirm all pass before declaring done.
