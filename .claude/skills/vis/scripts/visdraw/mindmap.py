"""mindmap: a collapsible tree drawn left to right. Click a node to open or close it and read its note."""
from __future__ import annotations

from .common import Page, SpecError, auto_colour, colour, esc, korean, shell, text

_TOP = {"kind", "title", "subtitle", "open", "root", "note"}
_NODE = {"label", "note", "url", "color", "open", "children"}

WORDS = {
    "ko": {"all": "모두 펼치기", "none": "모두 접기", "level": "단계", "find": "찾기", "pick": "노드를 누르면 펼치거나 접고, 메모가 여기에 나옵니다.",
           "kids": "하위 항목", "link": "자세히"},
    "en": {"all": "Expand all", "none": "Collapse all", "level": "level", "find": "Find", "pick": "Click a node to open or close it; its note shows here.",
           "kids": "Children", "link": "More"},
}


def build(data: dict) -> Page:
    warnings = [f"unknown top-level key {k!r} ignored" for k in data if k not in _TOP]
    root = data.get("root")
    if root is None:
        raise SpecError("`root:` is required, e.g. root: {label: Topic, children: [A, B]}")
    nodes: list[dict] = []
    open_depth = data.get("open")
    if open_depth is not None and (not isinstance(open_depth, int) or open_depth < 0):
        raise SpecError("open must be a whole number >= 0 (how many levels start expanded)")

    def add(n, parent: int, depth: int, branch: int, where: str) -> None:
        if isinstance(n, str) or isinstance(n, (int, float)):
            n = {"label": str(n)}
        elif isinstance(n, dict) and len(n) == 1 and not (set(n) & _NODE):
            (k, v), = n.items()          # {Label: [children]} short form
            n = {"label": str(k), "children": v if isinstance(v, list) else [v]}
        elif not isinstance(n, dict):
            raise SpecError(f"{where}: a node is a label or {{label: ..., children: [...]}}")
        for k in n:
            if k not in _NODE:
                warnings.append(f"{where}: unknown key {k!r} ignored")
        label = text(n.get("label"))
        if not label:
            raise SpecError(f"{where}: every node needs a label")
        i = len(nodes)
        if depth == 1:
            branch = i
        c = colour(n.get("color"), where)
        is_open = n.get("open")
        nodes.append({"label": label, "note": text(n.get("note")), "url": text(n.get("url")), "p": parent,
                      "d": depth, "kids": [], "c": c, "b": branch,
                      "open": bool(is_open) if is_open is not None else (open_depth is None or depth < open_depth)})
        if parent >= 0:
            nodes[parent]["kids"].append(i)
        kids = n.get("children") or []
        if not isinstance(kids, list):
            raise SpecError(f"{where}: children must be a list")
        for j, k in enumerate(kids):
            add(k, i, depth + 1, branch, f"{label} > child {j + 1}")

    add(root, -1, 0, 0, "root")
    k = 0
    for n in nodes:                       # first-level branches get a colour each, the rest inherit
        if n["d"] == 1:
            n["c"] = n["c"] or auto_colour(k)
            k += 1
    for n in nodes:
        if n["d"] > 1 and not n["c"]:
            n["c"] = nodes[n["b"]]["c"]
    nodes[0]["c"] = nodes[0]["c"] or "#5B6CFF"
    for n in nodes:
        if n["url"] and not n["url"].startswith(("http://", "https://")):
            warnings.append(f"{n['label']}: url should be an http(s) link")

    ko = korean(data)
    w = WORDS["ko" if ko else "en"]
    depth = max(n["d"] for n in nodes)
    levels = "".join(f'<button data-lv="{d}">{d}{esc(w["level"]) if ko else " " + esc(w["level"])}</button>'
                     for d in range(1, min(depth, 4) + 1))
    body = f"""
<nav class="bar">
  <button data-lv="all">{esc(w['all'])}</button><button data-lv="0">{esc(w['none'])}</button>{levels}
  <input id="q" type="search" placeholder="{esc(w['find'])}">
</nav>
<div class="wrap">
  <main class="card"><div class="mm" id="mm"></div></main>
  <aside><div class="card panel" id="panel"><p class="empty">{esc(w['pick'])}</p></div></aside>
</div>"""
    leaves = sum(1 for n in nodes if not n["kids"])
    return Page(shell(title=text(data.get("title")) or nodes[0]["label"], subtitle=text(data.get("subtitle")),
                      ko=ko, css=CSS, body=body, script=JS, payload={"W": w, "N": nodes},
                      foot=text(data.get("note"))),
                1440, max(700, 220 + 30 * leaves), warnings)


CSS = """
.mm{overflow:auto;max-height:80vh}
.mm svg{display:block}
.mm path{fill:none;stroke-width:2;stroke-opacity:.55}
.mm g.n{cursor:pointer}
.mm g.n text{fill:var(--ink);font-size:13.5px;dominant-baseline:central}
.mm g.n.d0 text{fill:#fff;font-weight:700;font-size:15px}
.mm g.n.d1 text{font-weight:700;font-size:14px}
.mm g.n.hit text{text-decoration:underline;text-decoration-thickness:2px}
.mm g.n.sel rect.box{stroke-width:2.5}
.mm g.n:hover text{text-decoration:underline}
.mm .more{font-size:11px;font-weight:700;fill:#fff}
.panel .crumb{color:var(--sub);font-size:12.5px;margin-bottom:4px}
.panel p.body{white-space:pre-wrap;margin:6px 0}
"""

JS = r"""
const {W, N} = D;
const esc = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const ctx = document.createElement('canvas').getContext('2d');
const FONT = '"Pretendard","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif';
const width = n => { ctx.font = (n.d === 0 ? '700 15px ' : n.d === 1 ? '700 14px ' : '13.5px ') + FONT; return ctx.measureText(n.label).width; };
N.forEach(n => n.w = width(n) + (n.d <= 1 ? 26 : 16));
let sel = null, hits = new Set();
const ROW = 30, GAP = 54, PAD = 20;

function draw() {
  const vis = [], colW = [];
  (function walk(i) { const n = N[i]; vis.push(i); colW[n.d] = Math.max(colW[n.d] || 0, n.w); if (n.open) n.kids.forEach(walk); })(0);
  const xs = [PAD]; colW.forEach((w, d) => xs[d + 1] = xs[d] + w + GAP + 14);
  let cur = PAD + ROW / 2;
  (function place(i) {
    const n = N[i], kids = n.open ? n.kids : [];
    n.x = xs[n.d];
    if (!kids.length) { n.y = cur; cur += ROW; return; }
    kids.forEach(place);
    n.y = (N[kids[0]].y + N[kids[kids.length - 1]].y) / 2;
  })(0);
  const Wd = Math.max(...vis.map(i => N[i].x + N[i].w)) + PAD + 40, H = cur + PAD;
  let s = `<svg width="${Wd}" height="${H}" viewBox="0 0 ${Wd} ${H}">`;
  vis.forEach(i => { const n = N[i]; if (n.p < 0) return; const p = N[n.p], x1 = p.x + p.w, m = (x1 + n.x) / 2;
    s += `<path d="M${x1},${p.y} C${m},${p.y} ${m},${n.y} ${n.x},${n.y}" stroke="${n.c}"/>`; });
  vis.forEach(i => {
    const n = N[i], cls = `n d${Math.min(n.d, 2)}${sel === i ? ' sel' : ''}${hits.has(i) ? ' hit' : ''}`;
    s += `<g class="${cls}" data-i="${i}">`;
    if (n.d === 0) s += `<rect class="box" x="${n.x}" y="${n.y - 15}" width="${n.w}" height="30" rx="15" fill="${n.c}" stroke="${n.c}"/>`;
    else if (n.d === 1) s += `<rect class="box" x="${n.x}" y="${n.y - 14}" width="${n.w}" height="28" rx="8" fill="${n.c}26" stroke="${n.c}" stroke-width="1.5"/>`;
    else s += `<rect class="box" x="${n.x}" y="${n.y - 12}" width="${n.w}" height="24" rx="6" fill="transparent" stroke="${sel === i ? n.c : 'transparent'}"/><line x1="${n.x}" y1="${n.y + 11}" x2="${n.x + n.w}" y2="${n.y + 11}" stroke="${n.c}" stroke-width="1.5" stroke-opacity=".5"/>`;
    s += `<text x="${n.x + (n.d <= 1 ? 13 : 8)}" y="${n.y}">${esc(n.label)}</text>`;
    if (n.kids.length && !n.open) s += `<circle cx="${n.x + n.w + 12}" cy="${n.y}" r="10" fill="${n.c}"/><text class="more" x="${n.x + n.w + 12}" y="${n.y + 0.5}" text-anchor="middle" dominant-baseline="central">+${n.kids.length}</text>`;
    s += '</g>';
  });
  document.getElementById('mm').innerHTML = s + '</svg>';
}
function crumb(i) { const out = []; for (let p = N[i].p; p >= 0; p = N[p].p) out.unshift(N[p].label); return out.join(' › '); }
function show(i) {
  const n = N[i];
  document.getElementById('panel').innerHTML = `${n.p >= 0 ? `<div class="crumb">${esc(crumb(i))}</div>` : ''}<h2 style="color:${n.d ? n.c : 'inherit'}">${esc(n.label)}</h2>`
    + (n.note ? `<p class="body">${esc(n.note)}</p>` : '')
    + (n.url ? `<p><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(W.link)} ↗</a></p>` : '')
    + (n.kids.length ? `<div class="meta">${esc(W.kids)} ${n.kids.length}</div><ul style="margin:0;padding-left:18px">${n.kids.map(k => `<li>${esc(N[k].label)}</li>`).join('')}</ul>` : '');
}
document.getElementById('mm').addEventListener('click', e => {
  const g = e.target.closest('g.n'); if (!g) return;
  const i = +g.dataset.i;
  if (N[i].kids.length && (sel === i || !N[i].open)) N[i].open = !N[i].open;
  sel = i; show(i); draw();
});
document.querySelectorAll('nav.bar button').forEach(b => b.onclick = () => {
  const lv = b.dataset.lv;
  N.forEach(n => n.open = lv === 'all' ? true : n.d < +lv);
  if (lv === '0') N[0].open = false;
  draw();
});
document.getElementById('q').addEventListener('input', e => {
  const q = e.target.value.trim().toLowerCase(); hits = new Set();
  if (q) N.forEach((n, i) => { if ((n.label + ' ' + n.note).toLowerCase().includes(q)) { hits.add(i); for (let p = n.p; p >= 0; p = N[p].p) N[p].open = true; } });
  draw();
});
draw();
"""
