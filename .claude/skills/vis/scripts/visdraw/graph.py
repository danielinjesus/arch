# graph: a network of nodes and edges, laid out by forces. Drag nodes, pan, zoom, click to read.
from __future__ import annotations

import re

from .common import Page, SpecError, auto_colour, colour, esc, korean, shell, text

_TOP = {"kind", "title", "subtitle", "groups", "nodes", "edges", "directed", "note"}
_NODE = {"label", "group", "size", "note", "url"}
_EDGE = {"from", "to", "label", "weight", "both", "dashed"}
_ARROW = re.compile(r"^\s*([\w.]+)\s*(<?--?>|--)\s*([\w.]+)\s*(?::\s*(.*?))?\s*$")

WORDS = {
    "ko": {"find": "찾기", "fit": "다시 맞추기", "labels": "선 이름", "pick": "노드를 누르면 같은 그룹 및 연결된 항목과 설명이 여기에 나와요. 끌어서 옮기고, 휠로 확대해요.",
           "links": "연결", "link": "공식 문서", "out": "→", "in": "←"},
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
  <main class="card" style="padding:0;overflow:hidden"><svg id="gv" viewBox="0 0 1320 820" role="img"></svg></main>
  <aside><div class="card panel" id="panel"><p class="empty">{esc(w['pick'])}</p></div></aside>
</div>"""
    return Page(shell(title=text(data.get("title")) or "Graph", subtitle=text(data.get("subtitle")), ko=ko,
                      css=CSS, body=body, script=JS, payload={"W": w, "G": groups, "N": nodes, "E": edges},
                      foot=text(data.get("note"))),
                1600, 980, warnings)


CSS = """
#gv{display:block;width:100%;height:min(80vh,800px);touch-action:none;cursor:grab;background:var(--card)}
#gv.drag{cursor:grabbing}
#gv rect.gb{fill-opacity:.055;stroke-opacity:.38;stroke-width:1.5;stroke-dasharray:6 4;rx:18}
#gv text.gt{font-size:14px;font-weight:700;fill-opacity:.92;stroke:var(--card);stroke-width:4px;paint-order:stroke;pointer-events:none}
#gv line{stroke:var(--sub);stroke-opacity:.42}
#gv path.ah{fill:var(--sub)}
#gv line.lit{stroke-opacity:.95}
#gv .faded{opacity:.12}
#gv g.n{cursor:pointer}
#gv g.n circle{stroke:var(--card);stroke-width:2.5}
#gv g.n.sel circle{stroke:var(--ink);stroke-width:3.5}
#gv g.n.hit circle{stroke:var(--accent);stroke-width:4.5}
#gv text.nl{fill:var(--ink);font-size:14.5px;font-weight:600;paint-order:stroke;stroke:var(--card);stroke-width:4.5px;stroke-linejoin:round;pointer-events:none}
#gv text.el{fill:var(--sub);font-size:12px;font-weight:500;paint-order:stroke;stroke:var(--card);stroke-width:3px;display:none;pointer-events:none}
#gv.labels text.el,#gv text.el.lit{display:block}
.legend .gchip{cursor:pointer;user-select:none;padding:4px 10px;border-radius:999px;border:1px solid var(--line);background:var(--soft)}
.legend .gchip.off{opacity:.35;text-decoration:line-through}
.panel ul{margin:8px 0;padding-left:20px;line-height:1.65}
.panel li span{cursor:pointer;font-weight:600}
.panel li span:hover{color:var(--accent)}
"""

JS = r"""
const {W, G, N, E} = D;
const esc = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const svg = document.getElementById('gv'), NS = 'http://www.w3.org/2000/svg';
const VW = 1320, VH = 820;
const colr = n => n.g >= 0 ? G[n.g].color : '#8A8797';
const R = n => 8 + Math.sqrt(n.size) * 6;
const off = new Set();
let sel = null, hits = new Set();

const gc = G.map((_, gi) => {
  if (G.length <= 1) return {x: VW / 2, y: VH / 2};
  const cols = G.length <= 4 ? 2 : (G.length <= 6 ? 3 : (G.length === 9 ? 3 : Math.ceil(G.length / 2)));
  const rows = Math.ceil(G.length / cols);
  const c = gi % cols, r = Math.floor(gi / cols);
  const rowCols = r === rows - 1 ? (G.length - r * cols) : cols;
  return {
    x: (VW * 0.13) + ((c + 0.5) / rowCols) * (VW * 0.74),
    y: (VH * 0.14) + ((r + 0.5) / rows) * (VH * 0.70)
  };
});

const gMembers = G.map(() => []);
N.forEach((n, i) => { if (n.g >= 0) gMembers[n.g].push(i); });
N.forEach((n, i) => {
  if (n.g >= 0 && G.length > 1) {
    const anchor = gc[n.g], list = gMembers[n.g], idx = list.indexOf(i), cnt = list.length;
    const a = 2 * Math.PI * (idx / Math.max(1, cnt)) - Math.PI / 2;
    const rad = cnt <= 1 ? 0 : (40 + cnt * 8);
    n.x = anchor.x + rad * 1.18 * Math.cos(a);
    n.y = anchor.y + rad * 0.75 * Math.sin(a);
  } else {
    const a = 2 * Math.PI * (i / N.length);
    n.x = VW / 2 + 260 * Math.cos(a);
    n.y = VH / 2 + 220 * Math.sin(a);
  }
  n.vx = n.vy = 0;
});
const nb = N.map(() => new Set());
E.forEach(e => { nb[e.s].add(e.t); nb[e.t].add(e.s); });

function tick(alpha) {
  const k = G.length > 3 ? 84 : 95;
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
    const a = N[i], b = N[j];
    let dx = a.x - b.x, dy = a.y - b.y;
    const sameG = a.g >= 0 && a.g === b.g;
    const minDx = R(a) + R(b) + Math.min(136, (a.label.length + b.label.length) * 3.9) + (sameG ? 4 : 48);
    const minDy = R(a) + R(b) + (sameG ? 42 : 58);
    if (Math.abs(dx) < minDx && Math.abs(dy) < minDy) {
      const push = (sameG ? 0.24 : 0.34) * alpha;
      const sx = dx >= 0 ? 1 : -1, sy = dy >= 0 ? 1 : -1;
      a.vx += sx * (minDx - Math.abs(dx)) * push * 0.44;
      b.vx -= sx * (minDx - Math.abs(dx)) * push * 0.44;
      a.vy += sy * (minDy - Math.abs(dy)) * push;
      b.vy -= sy * (minDy - Math.abs(dy)) * push;
    }
    let d2 = dx * dx + dy * dy || 0.01;
    if (d2 > 220000) continue;
    const rep = sameG ? 0.55 : 1.45;
    const f = (k * k / d2) * alpha * rep;
    a.vx += dx * f / 10; a.vy += dy * f / 10; b.vx -= dx * f / 10; b.vy -= dy * f / 10;
  }
  E.forEach(e => {
    const a = N[e.s], b = N[e.t], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
    const sameG = a.g >= 0 && a.g === b.g;
    const target = sameG ? (70 + R(a) + R(b)) : (220 + R(a) + R(b));
    const strength = sameG ? 0.055 : 0.004;
    const f = (d - target) / d * strength * alpha * Math.min(2.2, e.w);
    a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
  });
  N.forEach(n => {
    if (n.g >= 0 && G.length > 1) {
      const anchor = gc[n.g];
      n.vx += (anchor.x - n.x) * 0.075 * alpha;
      n.vy += (anchor.y - n.y) * 0.075 * alpha;
    } else {
      n.vx += (VW / 2 - n.x) * 0.005 * alpha;
      n.vy += (VH / 2 - n.y) * 0.005 * alpha;
    }
    if (n.fixed) { n.vx = n.vy = 0; return; }
    n.x += n.vx; n.y += n.vy; n.vx *= 0.55; n.vy *= 0.55;
  });
}
for (let i = 0; i < 450; i++) tick(1 - i / 500);

let view = {x: 0, y: 0, k: 1};
const root = document.createElementNS(NS, 'g'); svg.appendChild(root);
const defs = document.createElementNS(NS, 'defs');
defs.innerHTML = `<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0,0 L10,5 L0,10 z"/></marker>`;
svg.insertBefore(defs, root);
function render() {
  root.setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`);
  let s = '', t = '';
  const focus = sel != null ? new Set([sel, ...nb[sel]]) : null;
  if (G.length > 1) {
    G.forEach((g, gi) => {
      if (off.has(gi)) return;
      const gn = N.filter(n => n.g === gi);
      if (!gn.length) return;
      const x0 = Math.min(...gn.map(n => n.x - R(n) - 52)), x1 = Math.max(...gn.map(n => n.x + R(n) + 52));
      const y0 = Math.min(...gn.map(n => n.y - R(n) - 34)), y1 = Math.max(...gn.map(n => n.y + R(n) + 34));
      const fade = focus && !gn.some(n => focus.has(N.indexOf(n)));
      s += `<rect class="gb${fade ? ' faded' : ''}" x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" fill="${g.color}" stroke="${g.color}"/>`;
      s += `<text class="gt${fade ? ' faded' : ''}" x="${x0 + 14}" y="${y0 + 20}" fill="${g.color}">${esc(g.label)}</text>`;
    });
  }
  E.forEach((e, i) => {
    const a = N[e.s], b = N[e.t]; if (off.has(a.g) || off.has(b.g)) return;
    const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const x1 = a.x + ux * (R(a) + (e.both ? 3 : 0)), y1 = a.y + uy * (R(a) + (e.both ? 3 : 0)), x2 = b.x - ux * (R(b) + 3), y2 = b.y - uy * (R(b) + 3);
    const on = focus && (e.s === sel || e.t === sel), fade = focus && !on;
    const lcol = (a.g >= 0 && a.g === b.g) ? G[a.g].color : '';
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke-width="${(1.1 + Math.log2(1 + e.w)).toFixed(2)}"${lcol ? ` style="stroke:${lcol}"` : ''} class="${on ? 'lit' : ''}${fade ? ' faded' : ''}"${e.dash ? ' stroke-dasharray="6 5"' : ''}${e.dir ? ' marker-end="url(#ah)"' : ''}${e.dir && e.both ? ' marker-start="url(#ah)"' : ''}/>`;
    if (e.label) t += `<text class="el${on ? ' lit' : ''}${fade ? ' faded' : ''}" x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 5}" text-anchor="middle">${esc(e.label)}</text>`;
  });
  N.forEach((n, i) => {
    if (off.has(n.g)) return;
    const fade = focus && !focus.has(i);
    s += `<g class="n${sel === i ? ' sel' : ''}${hits.has(i) ? ' hit' : ''}${fade ? ' faded' : ''}" data-i="${i}"><circle cx="${n.x}" cy="${n.y}" r="${R(n)}" fill="${colr(n)}"/></g>`;
    t += `<text class="nl${fade ? ' faded' : ''}" x="${n.x}" y="${n.y + R(n) + 16}" text-anchor="middle">${esc(n.label)}</text>`;
  });
  root.innerHTML = s + t;
}
function fit() {
  const vis = N.filter(n => !off.has(n.g));
  const pts = vis.length ? vis : N;
  const x0 = Math.min(...pts.map(n => n.x - R(n) - 72)), x1 = Math.max(...pts.map(n => n.x + R(n) + 72));
  const y0 = Math.min(...pts.map(n => n.y - R(n) - 52)), y1 = Math.max(...pts.map(n => n.y + R(n) + 64));
  const k = Math.min(VW / (x1 - x0), VH / (y1 - y0), 2.2);
  view = {k, x: (VW - (x1 + x0) * k) / 2, y: (VH - (y1 + y0) * k) / 2}; render();
}
function show(i) {
  const n = N[i], out = E.filter(e => e.s === i), inn = E.filter(e => e.t === i);
  const li = (e, j, arrow) => `<li>${arrow} <span data-i="${j}">${esc(N[j].label)}</span>${e.label ? ` <span class="meta">· ${esc(e.label)}</span>` : ''}</li>`;
  document.getElementById('panel').innerHTML = `<h2 style="color:${colr(n)}">${esc(n.label)}</h2><div class="meta">${n.g >= 0 ? esc(G[n.g].label) + ' · ' : ''}${esc(W.links)} ${nb[i].size}</div>`
    + (n.note ? `<p style="white-space:pre-wrap;margin:8px 0">${esc(n.note)}</p>` : '')
    + (n.url ? `<p><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(W.link)} ↗</a></p>` : '')
    + `<ul>${out.map(e => li(e, e.t, W.out)).join('')}${inn.map(e => li(e, e.s, W.in)).join('')}</ul>`;
}
document.getElementById('panel').addEventListener('click', e => { const x = e.target.closest('span[data-i]'); if (x) { sel = +x.dataset.i; show(sel); render(); } });

// drag a node, or pan the canvas; wheel zooms around the pointer
const pt = e => { const r = svg.getBoundingClientRect(), sx = VW / r.width, sy = VH / r.height; return {x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sy}; };
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
  for (let t = 0; t < 3; t++) tick(0.22);
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
