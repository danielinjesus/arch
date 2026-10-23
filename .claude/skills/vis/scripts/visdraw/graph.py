"""graph: a network of nodes and edges, laid out by forces. Drag nodes, pan, zoom, click to read."""
from __future__ import annotations

import re

from .common import Page, SpecError, auto_colour, colour, esc, korean, shell, text

_TOP = {"kind", "title", "subtitle", "groups", "nodes", "edges", "directed", "note"}
_NODE = {"label", "group", "size", "note", "url"}
_EDGE = {"from", "to", "label", "weight", "both", "dashed"}
_ARROW = re.compile(r"^\s*([\w.]+)\s*(<?--?>|--)\s*([\w.]+)\s*(?::\s*(.*?))?\s*$")

WORDS = {
    "ko": {"find": "찾기", "fit": "다시 맞추기", "labels": "선 이름", "pick": "노드를 누르면 연결과 메모가 여기에 나옵니다. 끌어서 옮기고, 휠로 확대합니다.",
           "links": "연결", "link": "자세히", "out": "→", "in": "←"},
    "en": {"find": "Find", "fit": "Fit", "labels": "Edge labels", "pick": "Click a node to see its links and note. Drag to move, wheel to zoom.",
           "links": "Links", "link": "More", "out": "→", "in": "←"},
}


def build(data: dict) -> Page:
    warnings = [f"unknown top-level key {k!r} ignored" for k in data if k not in _TOP]
    groups, gix = [], {}
    for i, (gid, g) in enumerate((data.get("groups") or {}).items()):
        g = {"label": g} if isinstance(g, str) else (g or {})
        gix[str(gid)] = len(groups)
        groups.append({"label": text(g.get("label")) or str(gid),
                       "color": colour(g.get("color"), f"group {gid}") or auto_colour(i)})
    raw = data.get("nodes")
    if not isinstance(raw, dict) or not raw:
        raise SpecError("`nodes:` must map ids to nodes, e.g. nodes: {a: {label: A, group: g1}}")
    nodes, nix = [], {}
    for nid, n in raw.items():
        nid = str(nid)
        if not re.fullmatch(r"[\w.]+", nid):
            raise SpecError(f"node id {nid!r}: use letters, digits, _ or . only")
        n = {"label": n} if isinstance(n, str) else (n or {})
        for k in n:
            if k not in _NODE:
                warnings.append(f"node {nid}: unknown key {k!r} ignored")
        g = n.get("group")
        if g is not None and str(g) not in gix:
            gix[str(g)] = len(groups)
            groups.append({"label": str(g), "color": auto_colour(len(groups))})
            warnings.append(f"node {nid}: group {g!r} is not under groups:, using its id as the label")
        size = n.get("size", 1)
        if not isinstance(size, (int, float)) or size <= 0:
            raise SpecError(f"node {nid}: size must be a number above 0")
        nix[nid] = len(nodes)
        nodes.append({"label": text(n.get("label")) or nid, "g": gix[str(g)] if g is not None else -1,
                      "size": size, "note": text(n.get("note")), "url": text(n.get("url"))})

    directed = data.get("directed", True)
    edges = []
    for i, e in enumerate(data.get("edges") or []):
        opts = {}
        if isinstance(e, dict) and "from" in e:
            opts = e
            src, dst, arrow, label = str(e["from"]), str(e.get("to", "")), "->", e.get("label")
            for k in e:
                if k not in _EDGE:
                    warnings.append(f"edge #{i + 1}: unknown key {k!r} ignored")
        else:
            if isinstance(e, dict) and len(e) == 1:
                head, val = next(iter(e.items()))
                opts = val if isinstance(val, dict) else {}
                label = val.get("label") if isinstance(val, dict) else val
            elif isinstance(e, str):
                head, label = e, None
            else:
                raise SpecError(f"edge #{i + 1}: write it as 'a -> b: label' or {{from: a, to: b}}")
            m = _ARROW.match(str(head))
            if not m:
                raise SpecError(f"edge #{i + 1} {head!r}: expected 'a -> b', 'a <-> b', 'a --> b' or 'a -- b'")
            src, arrow, dst, tail = m.groups()
            label = tail if label is None else label
        for end in (src, dst):
            if end not in nix:
                raise SpecError(f"edge {src} -> {dst}: no node called {end!r}")
        if src == dst:
            raise SpecError(f"edge {src} -> {dst}: an edge needs two different nodes")
        w = opts.get("weight", 1)
        if not isinstance(w, (int, float)) or w <= 0:
            raise SpecError(f"edge {src} -> {dst}: weight must be a number above 0")
        edges.append({"s": nix[src], "t": nix[dst], "label": text(label), "w": w,
                      "both": arrow.startswith("<") or bool(opts.get("both")),
                      "dash": "--" in arrow or bool(opts.get("dashed")),
                      "dir": bool(directed) and arrow != "--"})
    lonely = [n["label"] for i, n in enumerate(nodes) if not any(e["s"] == i or e["t"] == i for e in edges)]
    if lonely:
        warnings.append(f"nodes with no edge: {', '.join(lonely)}")

    ko = korean(data)
    w = WORDS["ko" if ko else "en"]
    body = f"""
<nav class="bar">
  <span class="legend" id="legend" style="margin:0"></span>
  <input id="q" type="search" placeholder="{esc(w['find'])}">
  <button id="fit">{esc(w['fit'])}</button><button id="lab">{esc(w['labels'])}</button>
</nav>
<div class="wrap">
  <main class="card" style="padding:0;overflow:hidden"><svg id="gv" viewBox="0 0 1000 680" role="img"></svg></main>
  <aside><div class="card panel" id="panel"><p class="empty">{esc(w['pick'])}</p></div></aside>
</div>"""
    return Page(shell(title=text(data.get("title")) or "Graph", subtitle=text(data.get("subtitle")), ko=ko,
                      css=CSS, body=body, script=JS, payload={"W": w, "G": groups, "N": nodes, "E": edges},
                      foot=text(data.get("note"))),
                1440, 900, warnings)


CSS = """
#gv{display:block;width:100%;height:min(78vh,760px);touch-action:none;cursor:grab;background:var(--card)}
#gv.drag{cursor:grabbing}
#gv line{stroke:var(--sub);stroke-opacity:.45}
#gv path.ah{fill:var(--sub)}
#gv line.lit{stroke-opacity:.95}
#gv .faded{opacity:.1}
#gv g.n{cursor:pointer}
#gv g.n circle{stroke:var(--card);stroke-width:2}
#gv g.n.sel circle{stroke:var(--ink);stroke-width:3}
#gv g.n.hit circle{stroke:var(--accent);stroke-width:4}
#gv text{fill:var(--ink);font-size:12.5px;paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
#gv text.el{fill:var(--sub);font-size:11px;display:none}
#gv.labels text.el,#gv text.el.lit{display:block}
.legend .gchip{cursor:pointer;user-select:none}
.legend .gchip.off{opacity:.35;text-decoration:line-through}
.panel ul{margin:4px 0;padding-left:18px}
.panel li span{cursor:pointer}
.panel li span:hover{color:var(--accent)}
"""

JS = r"""
const {W, G, N, E} = D;
const esc = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const svg = document.getElementById('gv'), NS = 'http://www.w3.org/2000/svg';
const colr = n => n.g >= 0 ? G[n.g].color : '#8A8797';
const R = n => 7 + Math.sqrt(n.size) * 5;
const off = new Set();
let sel = null, hits = new Set();
// place nodes on a circle by group so the first frame already looks ordered
N.forEach((n, i) => { const a = 2 * Math.PI * (i / N.length) + (n.g + 1); n.x = 500 + 260 * Math.cos(a); n.y = 340 + 220 * Math.sin(a); n.vx = n.vy = 0; });
const nb = N.map(() => new Set());
E.forEach(e => { nb[e.s].add(e.t); nb[e.t].add(e.s); });

function tick(alpha) {
  const k = 90;
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
    const a = N[i], b = N[j]; let dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy || 0.01;
    if (d2 > 160000) continue;
    const f = (k * k / d2) * alpha * 0.9; a.vx += dx * f / 10; a.vy += dy * f / 10; b.vx -= dx * f / 10; b.vy -= dy * f / 10;
  }
  E.forEach(e => { const a = N[e.s], b = N[e.t], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
    const f = (d - (k + R(a) + R(b))) / d * 0.06 * alpha * Math.min(2, e.w); a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f; });
  N.forEach(n => { n.vx += (500 - n.x) * 0.004 * alpha; n.vy += (340 - n.y) * 0.004 * alpha;
    if (n.fixed) { n.vx = n.vy = 0; return; } n.x += n.vx; n.y += n.vy; n.vx *= 0.6; n.vy *= 0.6; });
}
for (let i = 0; i < 400; i++) tick(1 - i / 450);

let view = {x: 0, y: 0, k: 1};
const root = document.createElementNS(NS, 'g'); svg.appendChild(root);
const defs = document.createElementNS(NS, 'defs');
defs.innerHTML = `<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0,0 L10,5 L0,10 z"/></marker>`;
svg.insertBefore(defs, root);
function render() {
  root.setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`);
  let s = '';
  const focus = sel != null ? new Set([sel, ...nb[sel]]) : null;
  E.forEach((e, i) => {
    const a = N[e.s], b = N[e.t]; if (off.has(a.g) || off.has(b.g)) return;
    const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const x1 = a.x + ux * (R(a) + (e.both ? 3 : 0)), y1 = a.y + uy * (R(a) + (e.both ? 3 : 0)), x2 = b.x - ux * (R(b) + 3), y2 = b.y - uy * (R(b) + 3);
    const on = focus && (e.s === sel || e.t === sel), fade = focus && !on;
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke-width="${(1 + Math.log2(1 + e.w)).toFixed(2)}" class="${on ? 'lit' : ''}${fade ? ' faded' : ''}"${e.dash ? ' stroke-dasharray="5 5"' : ''}${e.dir ? ' marker-end="url(#ah)"' : ''}${e.dir && e.both ? ' marker-start="url(#ah)"' : ''}/>`;
    if (e.label) s += `<text class="el${on ? ' lit' : ''}${fade ? ' faded' : ''}" x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 4}" text-anchor="middle">${esc(e.label)}</text>`;
  });
  N.forEach((n, i) => {
    if (off.has(n.g)) return;
    const fade = focus && !focus.has(i);
    s += `<g class="n${sel === i ? ' sel' : ''}${hits.has(i) ? ' hit' : ''}${fade ? ' faded' : ''}" data-i="${i}"><circle cx="${n.x}" cy="${n.y}" r="${R(n)}" fill="${colr(n)}"/><text x="${n.x}" y="${n.y + R(n) + 14}" text-anchor="middle">${esc(n.label)}</text></g>`;
  });
  root.innerHTML = s;
}
function fit() {
  const xs = N.map(n => n.x), ys = N.map(n => n.y), pad = 60;
  const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad, y0 = Math.min(...ys) - pad, y1 = Math.max(...ys) + pad;
  const k = Math.min(1000 / (x1 - x0), 680 / (y1 - y0), 2.5);
  view = {k, x: (1000 - (x1 + x0) * k) / 2, y: (680 - (y1 + y0) * k) / 2}; render();
}
function show(i) {
  const n = N[i], out = E.filter(e => e.s === i), inn = E.filter(e => e.t === i);
  const li = (e, j, arrow) => `<li>${arrow} <span data-i="${j}">${esc(N[j].label)}</span>${e.label ? ` <span class="meta">· ${esc(e.label)}</span>` : ''}</li>`;
  document.getElementById('panel').innerHTML = `<h2 style="color:${colr(n)}">${esc(n.label)}</h2><div class="meta">${n.g >= 0 ? esc(G[n.g].label) + ' · ' : ''}${esc(W.links)} ${nb[i].size}</div>`
    + (n.note ? `<p style="white-space:pre-wrap;margin:6px 0">${esc(n.note)}</p>` : '')
    + (n.url ? `<p><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(W.link)} ↗</a></p>` : '')
    + `<ul>${out.map(e => li(e, e.t, W.out)).join('')}${inn.map(e => li(e, e.s, W.in)).join('')}</ul>`;
}
document.getElementById('panel').addEventListener('click', e => { const x = e.target.closest('span[data-i]'); if (x) { sel = +x.dataset.i; show(sel); render(); } });

// drag a node, or pan the canvas; wheel zooms around the pointer
const pt = e => { const r = svg.getBoundingClientRect(), sx = 1000 / r.width, sy = 680 / r.height; return {x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sy}; };
let drag = null;
svg.addEventListener('pointerdown', e => {
  const g = e.target.closest('g.n'), p = pt(e);
  drag = g ? {i: +g.dataset.i, moved: false} : {pan: true, x: p.x - view.x, y: p.y - view.y};
  svg.setPointerCapture(e.pointerId); svg.classList.add('drag');
});
svg.addEventListener('pointermove', e => {
  if (!drag) return; const p = pt(e);
  if (drag.pan) { view.x = p.x - drag.x; view.y = p.y - drag.y; render(); return; }
  const n = N[drag.i]; n.x = (p.x - view.x) / view.k; n.y = (p.y - view.y) / view.k; n.fixed = true; drag.moved = true;
  for (let t = 0; t < 3; t++) tick(0.3);
  render();
});
svg.addEventListener('pointerup', () => {
  if (drag && drag.i != null && !drag.moved) { sel = sel === drag.i ? null : drag.i; sel != null ? show(sel) : null; render(); }
  drag = null; svg.classList.remove('drag');
});
svg.addEventListener('wheel', e => {
  e.preventDefault(); const p = pt(e), f = e.deltaY < 0 ? 1.12 : 1 / 1.12, k = Math.max(0.2, Math.min(5, view.k * f));
  view.x = p.x - (p.x - view.x) * (k / view.k); view.y = p.y - (p.y - view.y) * (k / view.k); view.k = k; render();
}, {passive: false});

const lg = document.getElementById('legend');
lg.innerHTML = G.map((g, i) => `<span class="gchip" data-g="${i}"><i style="background:${g.color}"></i>${esc(g.label)}</span>`).join('');
lg.onclick = e => { const x = e.target.closest('.gchip'); if (!x) return; const g = +x.dataset.g; off.has(g) ? off.delete(g) : off.add(g); x.classList.toggle('off'); render(); };
document.getElementById('fit').onclick = fit;
document.getElementById('lab').onclick = e => { svg.classList.toggle('labels'); e.target.classList.toggle('on'); };
document.getElementById('q').addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase(); hits = new Set();
  if (q) N.forEach((n, i) => { if ((n.label + ' ' + n.note).toLowerCase().includes(q)) hits.add(i); });
  render();
});
fit();
"""
