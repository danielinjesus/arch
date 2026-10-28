# graph: a network of nodes and edges, laid out by forces. Drag nodes, pan, zoom, click to read.
from __future__ import annotations

import re

from .common import Page, SpecError, auto_colour, colour, esc, korean, shell, text

_TOP = {"kind", "title", "subtitle", "groups", "nodes", "edges", "directed", "note"}
_NODE = {"label", "group", "size", "note", "url"}
_EDGE = {"from", "to", "label", "weight", "both", "dashed"}
_ARROW = re.compile(r"^\s*([\w.]+)\s*(<?--?>|--)\s*([\w.]+)\s*(?::\s*(.*?))?\s*$")

WORDS = {
    "ko": {"find": "찾기", "fit": "다시 맞추기", "labels": "선 이름",
           "links": "연결", "link": "공식 문서", "out": "→", "in": "←", "close": "닫기"},
    "en": {"find": "Find", "fit": "Fit", "labels": "Edge labels",
           "links": "Links", "link": "More", "out": "→", "in": "←", "close": "Close"},
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
  <span class="tools">
    <input id="q" type="search" placeholder="{esc(w['find'])}">
    <button id="fit">{esc(w['fit'])}</button><button id="lab">{esc(w['labels'])}</button>
  </span>
</nav>
<div class="wrap">
  <main class="card stage"><svg id="gv" viewBox="0 0 1640 820" role="img"></svg></main>
  <aside id="aside" hidden><div class="card panel" id="panel"></div></aside>
</div>"""
    return Page(shell(title=text(data.get("title")) or "Graph", subtitle=text(data.get("subtitle")), ko=ko,
                      css=CSS, body=body, script=JS, payload={"W": w, "G": groups, "N": nodes, "E": edges},
                      foot=text(data.get("note"))),
                1600, 980, warnings)


CSS = """
header{max-width:none;padding:8px 16px 2px;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
h1{font-size:23px;margin:0}
.lead{font-size:14.5px}
.bar{max-width:none;margin:4px 0 0;padding:0 16px;display:flex;align-items:center;justify-content:space-between;gap:6px;flex-wrap:wrap}
.bar .tools{display:inline-flex;gap:6px;align-items:center;margin-left:auto}
.bar button,.chip{padding:5px 12px;font-size:13.5px}
.bar input{padding:5px 12px;font-size:13.5px;min-width:160px}
.legend{gap:6px;font-size:13.5px;margin:0}
.legend .gchip{cursor:pointer;user-select:none;padding:3px 9px;border-radius:999px;border:1px solid var(--line);background:var(--soft)}
.legend .gchip.off{opacity:.35;text-decoration:line-through}
.wrap{display:block;position:relative;max-width:none;margin:6px 0 4px;padding:0 10px}
.stage{padding:0;overflow:hidden}
#aside{position:absolute;top:12px;right:22px;width:min(380px,calc(100vw - 44px));z-index:20}
#aside[hidden]{display:none}
.panel{position:static;max-height:calc(100vh - 140px);overflow:auto;font-size:15.5px;box-shadow:0 10px 28px rgba(0,0,0,.14)}
.panel .phead{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.panel .pclose{border:1px solid var(--line);background:var(--soft);color:var(--ink);border-radius:999px;width:28px;height:28px;cursor:pointer;font-size:16px;line-height:1;flex:none}
.foot{max-width:none;margin:0 0 6px;padding:0 16px;font-size:13px}
#gv{display:block;width:100%;height:calc(100vh - 136px);min-height:540px;touch-action:none;cursor:grab;background:var(--card)}
#gv.drag{cursor:grabbing}
#gv rect.gb{fill-opacity:.065;stroke-opacity:.52;stroke-width:2;stroke-dasharray:7 4;rx:18}
#gv text.gt{font-size:17.5px;font-weight:800;fill-opacity:.96;stroke:var(--card);stroke-width:5px;paint-order:stroke;pointer-events:none}
#gv line{stroke:var(--sub);stroke-opacity:.42}
#gv path.ah{fill:var(--sub)}
#gv line.lit{stroke-opacity:.95}
#gv .faded{opacity:.12}
#gv g.n{cursor:pointer}
#gv g.n circle{stroke:var(--card);stroke-width:2.8}
#gv g.n.sel circle{stroke:var(--ink);stroke-width:4}
#gv g.n.hit circle{stroke:var(--accent);stroke-width:5}
#gv text.nl{fill:var(--ink);font-size:17px;font-weight:700;paint-order:stroke;stroke:var(--card);stroke-width:5px;stroke-linejoin:round;pointer-events:none}
#gv text.el{fill:var(--sub);font-size:13.5px;font-weight:600;paint-order:stroke;stroke:var(--card);stroke-width:3.5px;display:none;pointer-events:none}
#gv.labels text.el,#gv text.el.lit{display:block}
.panel ul{margin:8px 0;padding-left:20px;line-height:1.65}
.panel li span{cursor:pointer;font-weight:600}
.panel li span:hover{color:var(--accent)}
"""

JS = r"""
const {W, G, N, E} = D;
const esc = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const svg = document.getElementById('gv'), aside = document.getElementById('aside'), NS = 'http://www.w3.org/2000/svg';
const VW = 1640, VH = 820;
const colr = n => n.g >= 0 ? G[n.g].color : '#8A8797';
const R = n => 10 + Math.sqrt(n.size) * 7.5;
const LW = n => Math.max(R(n) * 2 + 12, n.label.length * 9.6 + 18);
const off = new Set();
let sel = null, hits = new Set();

const cols = G.length <= 1 ? 1 : (G.length <= 4 ? 2 : (G.length <= 6 ? 3 : (G.length === 9 ? 3 : Math.ceil(G.length / 2))));
const rows = Math.max(1, Math.ceil(G.length / cols));
const cellW = VW / cols, cellH = VH / rows;
const gc = G.map((_, gi) => {
  if (G.length <= 1) return {x: VW / 2, y: VH / 2};
  const c = gi % cols, r = Math.floor(gi / cols);
  const rowCols = r === rows - 1 ? (G.length - r * cols) : cols;
  const xSpan = rowCols >= 3 ? 0.72 : 0.56;
  const xStart = (1 - xSpan) / 2;
  return {
    x: (rowCols <= 1 ? 0.5 : xStart + (c / (rowCols - 1)) * xSpan) * VW,
    y: ((r + 0.5) / rows) * VH
  };
});

const gMembers = G.map(() => []);
N.forEach((n, i) => { if (n.g >= 0) gMembers[n.g].push(i); });
N.forEach((n, i) => {
  if (n.g >= 0 && G.length > 1) {
    const anchor = gc[n.g], list = gMembers[n.g], idx = list.indexOf(i), cnt = list.length;
    const a = 2 * Math.PI * (idx / Math.max(1, cnt)) - Math.PI / 2;
    const rx = cnt <= 1 ? 0 : Math.min(cellW * 0.35, 84 + cnt * 15);
    const ry = cnt <= 1 ? 0 : Math.min(cellH * 0.25, 38 + cnt * 5.5);
    n.x = anchor.x + rx * Math.cos(a);
    n.y = anchor.y + ry * Math.sin(a);
  } else {
    const a = 2 * Math.PI * (i / N.length);
    n.x = VW / 2 + 320 * Math.cos(a);
    n.y = VH / 2 + 230 * Math.sin(a);
  }
  n.vx = n.vy = 0;
});
const nb = N.map(() => new Set());
E.forEach(e => { nb[e.s].add(e.t); nb[e.t].add(e.s); });

function tick(alpha) {
  const k = G.length > 1 ? 62 : 95;
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
    const a = N[i], b = N[j];
    const sameG = a.g >= 0 && a.g === b.g;
    if (G.length > 1 && !sameG) continue;
    let dx = a.x - b.x, dy = a.y - b.y;
    const minDx = (LW(a) + LW(b)) * 0.52;
    const minDy = R(a) + R(b) + 38;
    const ox = minDx - Math.abs(dx), oy = minDy - Math.abs(dy);
    if (ox > 0 && oy > 0) {
      const sx = dx >= 0 ? 1 : -1, sy = dy >= 0 ? 1 : -1;
      if (ox < oy * 1.35) {
        const p = ox * 0.32 * alpha; a.vx += sx * p; b.vx -= sx * p;
      } else {
        const p = oy * 0.32 * alpha; a.vy += sy * p; b.vy -= sy * p;
      }
    }
    let d2 = dx * dx + dy * dy || 0.01;
    const f = (k * k / d2) * alpha * 0.45;
    a.vx += dx * f / 10; a.vy += dy * f / 10; b.vx -= dx * f / 10; b.vy -= dy * f / 10;
  }
  E.forEach(e => {
    const a = N[e.s], b = N[e.t], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
    const sameG = a.g >= 0 && a.g === b.g;
    if (G.length > 1 && !sameG) return;
    const target = 90 + R(a) + R(b);
    const strength = 0.022;
    const f = (d - target) / d * strength * alpha * Math.min(2.2, e.w);
    a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
  });
  N.forEach(n => {
    if (n.g >= 0 && G.length > 1) {
      const anchor = gc[n.g];
      n.vx += (anchor.x - n.x) * 0.09 * alpha;
      n.vy += (anchor.y - n.y) * 0.11 * alpha;
    } else {
      n.vx += (VW / 2 - n.x) * 0.005 * alpha;
      n.vy += (VH / 2 - n.y) * 0.005 * alpha;
    }
    if (n.fixed) { n.vx = n.vy = 0; return; }
    n.x += n.vx; n.y += n.vy; n.vx *= 0.55; n.vy *= 0.55;
    if (n.g >= 0 && G.length > 1) {
      const anchor = gc[n.g], cnt = gMembers[n.g].length;
      const maxX = cellW * (cnt >= 6 ? 0.40 : 0.34), maxY = cellH * (cnt >= 6 ? 0.25 : 0.21);
      n.x = Math.max(anchor.x - maxX, Math.min(anchor.x + maxX, n.x));
      n.y = Math.max(anchor.y - maxY + 8, Math.min(anchor.y + maxY, n.y));
    }
  });
}
for (let i = 0; i < 480; i++) tick(1 - i / 520);
// Final de-overlap pass within each group
for (let pass = 0; pass < 40; pass++) {
  for (let i = 0; i < N.length; i++) for (let j = i + 1; j < N.length; j++) {
    const a = N[i], b = N[j];
    if (G.length > 1 && a.g !== b.g) continue;
    const dx = a.x - b.x, dy = a.y - b.y;
    const minDx = (LW(a) + LW(b)) * 0.50, minDy = R(a) + R(b) + 34;
    const ox = minDx - Math.abs(dx), oy = minDy - Math.abs(dy);
    if (ox > 0 && oy > 0) {
      const sx = dx >= 0 ? 1 : -1, sy = dy >= 0 ? 1 : -1;
      if (ox < oy * 1.4) { a.x += sx * ox * 0.52; b.x -= sx * ox * 0.52; }
      else { a.y += sy * oy * 0.52; b.y -= sy * oy * 0.52; }
    }
  }
}

let view = {x: 0, y: 0, k: 1}, cw = VW, ch = VH;
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
      const x0 = Math.min(...gn.map(n => n.x - LW(n) * 0.5 - 12)), x1 = Math.max(...gn.map(n => n.x + LW(n) * 0.5 + 12));
      const y0 = Math.min(...gn.map(n => n.y - R(n) - 30)), y1 = Math.max(...gn.map(n => n.y + R(n) + 32));
      const fade = focus && !gn.some(n => focus.has(N.indexOf(n)));
      s += `<rect class="gb${fade ? ' faded' : ''}" x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" fill="${g.color}" stroke="${g.color}"/>`;
      s += `<text class="gt${fade ? ' faded' : ''}" x="${x0 + 14}" y="${y0 + 21}" fill="${g.color}">${esc(g.label)}</text>`;
    });
  }
  E.forEach((e, i) => {
    const a = N[e.s], b = N[e.t]; if (off.has(a.g) || off.has(b.g)) return;
    const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1, ux = dx / d, uy = dy / d;
    const x1 = a.x + ux * (R(a) + (e.both ? 3 : 0)), y1 = a.y + uy * (R(a) + (e.both ? 3 : 0)), x2 = b.x - ux * (R(b) + 3), y2 = b.y - uy * (R(b) + 3);
    const on = focus && (e.s === sel || e.t === sel), fade = focus && !on;
    const lcol = (a.g >= 0 && a.g === b.g) ? G[a.g].color : '';
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke-width="${(1.2 + Math.log2(1 + e.w)).toFixed(2)}"${lcol ? ` style="stroke:${lcol}"` : ''} class="${on ? 'lit' : ''}${fade ? ' faded' : ''}"${e.dash ? ' stroke-dasharray="6 5"' : ''}${e.dir ? ' marker-end="url(#ah)"' : ''}${e.dir && e.both ? ' marker-start="url(#ah)"' : ''}/>`;
    if (e.label) t += `<text class="el${on ? ' lit' : ''}${fade ? ' faded' : ''}" x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2 - 5}" text-anchor="middle">${esc(e.label)}</text>`;
  });
  N.forEach((n, i) => {
    if (off.has(n.g)) return;
    const fade = focus && !focus.has(i);
    s += `<g class="n${sel === i ? ' sel' : ''}${hits.has(i) ? ' hit' : ''}${fade ? ' faded' : ''}" data-i="${i}"><circle cx="${n.x}" cy="${n.y}" r="${R(n)}" fill="${colr(n)}"/></g>`;
    t += `<text class="nl${fade ? ' faded' : ''}" x="${n.x}" y="${n.y + R(n) + 19}" text-anchor="middle">${esc(n.label)}</text>`;
  });
  root.innerHTML = s + t;
}
function fit() {
  const top = svg.getBoundingClientRect().top;
  const foot = document.querySelector('.foot');
  const fh = foot ? foot.offsetHeight + 10 : 10;
  const availH = (navigator.webdriver || /Headless/i.test(navigator.userAgent)) ? Math.min(window.innerHeight, 970) : window.innerHeight;
  const h = Math.max(520, availH - top - fh);
  svg.style.height = h + 'px';
  cw = svg.clientWidth || VW;
  ch = svg.clientHeight || h || VH;
  svg.setAttribute('viewBox', `0 0 ${cw} ${ch}`);
  const vis = N.filter(n => !off.has(n.g));
  const pts = vis.length ? vis : N;
  const x0 = Math.min(...pts.map(n => n.x - LW(n) * 0.5 - 18)), x1 = Math.max(...pts.map(n => n.x + LW(n) * 0.5 + 18));
  const y0 = Math.min(...pts.map(n => n.y - R(n) - 36)), y1 = Math.max(...pts.map(n => n.y + R(n) + 38));
  const k = Math.min((cw - 20) / (x1 - x0), (ch - 16) / (y1 - y0), 2.4);
  view = {k, x: (cw - (x1 + x0) * k) / 2, y: (ch - (y1 + y0) * k) / 2}; render();
}
addEventListener('resize', fit);
function show(i) {
  if (i == null) { aside.hidden = true; return; }
  const n = N[i], out = E.filter(e => e.s === i), inn = E.filter(e => e.t === i);
  const li = (e, j, arrow) => `<li>${arrow} <span data-i="${j}">${esc(N[j].label)}</span>${e.label ? ` <span class="meta">· ${esc(e.label)}</span>` : ''}</li>`;
  document.getElementById('panel').innerHTML = `<div class="phead"><h2 style="color:${colr(n)}">${esc(n.label)}</h2><button type="button" class="pclose" id="pclose" aria-label="${esc(W.close || '닫기')}">×</button></div><div class="meta">${n.g >= 0 ? esc(G[n.g].label) + ' · ' : ''}${esc(W.links)} ${nb[i].size}</div>`
    + (n.note ? `<p style="white-space:pre-wrap;margin:8px 0">${esc(n.note)}</p>` : '')
    + (n.url ? `<p><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(W.link)} ↗</a></p>` : '')
    + `<ul>${out.map(e => li(e, e.t, W.out)).join('')}${inn.map(e => li(e, e.s, W.in)).join('')}</ul>`;
  aside.hidden = false;
}
document.getElementById('panel').addEventListener('click', e => {
  if (e.target.closest('#pclose')) { sel = null; show(null); render(); return; }
  const x = e.target.closest('span[data-i]');
  if (x) { sel = +x.dataset.i; show(sel); render(); }
});

// drag a node, or pan the canvas; wheel zooms around the pointer
const pt = e => { const r = svg.getBoundingClientRect(), sx = cw / r.width, sy = ch / r.height; return {x: (e.clientX - r.left) * sx, y: (e.clientY - r.top) * sy}; };
let drag = null;
svg.addEventListener('pointerdown', e => {
  const g = e.target.closest('g.n'), p = pt(e);
  drag = g ? {i: +g.dataset.i, moved: false} : {pan: true, moved: false, x: p.x - view.x, y: p.y - view.y};
  svg.setPointerCapture(e.pointerId); svg.classList.add('drag');
});
svg.addEventListener('pointermove', e => {
  if (!drag) return; const p = pt(e);
  if (drag.pan) {
    if (Math.hypot(p.x - view.x - drag.x, p.y - view.y - drag.y) > 4) drag.moved = true;
    view.x = p.x - drag.x; view.y = p.y - drag.y; render(); return;
  }
  const n = N[drag.i]; n.x = (p.x - view.x) / view.k; n.y = (p.y - view.y) / view.k; n.fixed = true; drag.moved = true;
  for (let t = 0; t < 3; t++) tick(0.22);
  render();
});
svg.addEventListener('pointerup', () => {
  if (drag && !drag.moved) {
    if (drag.i != null) { sel = sel === drag.i ? null : drag.i; show(sel); render(); }
    else if (sel != null) { sel = null; show(null); render(); }
  }
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
