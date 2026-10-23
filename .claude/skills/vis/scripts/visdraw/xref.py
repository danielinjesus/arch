"""xref: categories (vertical knowledge) x tags (horizontal knowledge), shown four ways.

Matrix, two-column relation graph, category tree and tag list. Clicking anything gathers the linked notes in a
side panel, so one tag's rules can be reviewed together even when they are spread over many categories.
"""
from __future__ import annotations

from .common import Page, SpecError, auto_colour, colour, esc, korean, shell, text

_TOP = {"kind", "title", "subtitle", "source", "steps", "words", "categories", "tags", "links", "note"}

WORDS = {
    "ko": {"category": "카테고리", "tag": "tag", "matrix": "교차 지도", "graph": "관계 그래프", "tree": "개괄 카테고리",
           "tags": "전체 tag 목록", "times": "회", "cats": "개", "pick": "칸이나 이름을 누르면 여기에 연결된 내용이 모입니다.",
           "criteria": "분류기준", "gather": "이 tag 가 흩어진 곳을 한데 모았습니다.", "all_tag": "이 tag 전체 보기",
           "this_cat": "이 카테고리 보기", "linked": "연결된 tag", "no_notes": "메모 없음",
           "hover": "왼쪽은 세로 지식(카테고리), 오른쪽은 가로 지식(tag). 이름에 마우스를 올리면 연결만 남고, 누르면 내용이 모입니다.",
           "count_note": "숫자는 그 tag 가 걸린 카테고리 수입니다."},
    "en": {"category": "category", "tag": "tag", "matrix": "Matrix", "graph": "Relations", "tree": "Categories",
           "tags": "All tags", "times": "×", "cats": "", "pick": "Click a cell or a name to gather what is linked to it.",
           "criteria": "Criteria", "gather": "Everything this tag touches, in one place.", "all_tag": "Whole tag",
           "this_cat": "This category", "linked": "Linked tags", "no_notes": "no notes",
           "hover": "Left: categories (vertical). Right: tags (horizontal). Hover a name to keep only its links; click to gather.",
           "count_note": "The number is how many categories the tag touches."},
}


def build(data: dict) -> Page:
    warnings = [f"unknown top-level key {k!r} ignored" for k in data if k not in _TOP]
    ko = korean(data)
    words = {**WORDS["ko" if ko else "en"], **{k: text(v) for k, v in (data.get("words") or {}).items()}}

    cgroups, cats, cat_ix = [], [], {}
    for gi, g in enumerate(_list(data, "categories")):
        g = g if isinstance(g, dict) else {"group": g}
        cgroups.append({"name": text(g.get("group"))})
        for it in g.get("items") or []:
            it = {"label": it} if isinstance(it, str) else (it or {})
            cid = text(it.get("id") or it.get("label"))
            if not cid:
                raise SpecError(f"category group {gi + 1}: every item needs an id or a label")
            if cid in cat_ix:
                raise SpecError(f"category {cid!r} appears twice")
            cat_ix[cid] = len(cats)
            cats.append({"label": text(it.get("label")) or cid, "prefix": text(it.get("prefix")),
                         "meta": text(it.get("meta")), "kids": [text(k) for k in it.get("children") or []], "g": gi})
    if not cats:
        raise SpecError("`categories:` needs at least one group with items")

    tgroups, tags, tag_ix = [], [], {}
    for gi, g in enumerate(_list(data, "tags")):
        g = g if isinstance(g, dict) else {"group": g}
        tgroups.append({"name": text(g.get("group")),
                        "color": colour(g.get("color"), f"tag group {g.get('group')}") or auto_colour(gi)})
        for it in g.get("items") or []:
            it = {"name": it} if isinstance(it, str) else (it or {})
            tid = text(it.get("id") or it.get("name"))
            if not tid:
                raise SpecError(f"tag group {gi + 1}: every tag needs an id or a name")
            if tid in tag_ix:
                raise SpecError(f"tag {tid!r} appears twice")
            tag_ix[tid] = len(tags)
            tags.append({"name": text(it.get("name")) or tid, "g": gi, "crit": text(it.get("criteria"))})
    if not tags:
        raise SpecError("`tags:` needs at least one group with items")

    links = {}
    for i, ln in enumerate(data.get("links") or []):
        if not isinstance(ln, dict):
            raise SpecError(f"link #{i + 1}: write it as {{category: a, tag: b, weight: 2, notes: [...]}}")
        c, t = text(ln.get("category")), text(ln.get("tag"))
        if c not in cat_ix:
            raise SpecError(f"link #{i + 1}: no category called {c!r}")
        if t not in tag_ix:
            raise SpecError(f"link #{i + 1}: no tag called {t!r}")
        notes = ln.get("notes") or []
        notes = [text(n) for n in (notes if isinstance(notes, list) else [notes]) if text(n)]
        w = ln.get("weight", len(notes) or 1)
        if not isinstance(w, (int, float)) or w <= 0:
            raise SpecError(f"link #{i + 1}: weight must be a number above 0")
        key = f"{cat_ix[c]},{tag_ix[t]}"
        if key in links:
            warnings.append(f"link {c} x {t} given twice; notes merged")
            links[key]["n"] += w
            links[key]["notes"] += notes
        else:
            links[key] = {"n": w, "notes": notes}
    unused = [t["name"] for i, t in enumerate(tags) if not any(k.endswith(f",{i}") for k in links)]
    if unused:
        warnings.append(f"tags with no link: {', '.join(unused)}")

    src = data.get("source") or {}
    src = {"label": src} if isinstance(src, str) else src
    lead = ""
    if text(src.get("label")):
        lead = esc(src["label"])
        if text(src.get("url")):
            lead = f'<a href="{esc(src["url"])}" target="_blank" rel="noopener">{lead}</a>'
    steps = "".join(
        f'<li class="{"here" if s.get("here") else ""}">{esc(text(s.get("label")))}<small>{esc(text(s.get("sub")))}</small></li>'
        for s in (x if isinstance(x, dict) else {"label": x} for x in data.get("steps") or []))
    body = (f'<ol class="pipe">{steps}</ol>' if steps else "") + f"""
<nav class="bar">
  <button data-v="matrix" class="on">{esc(words['matrix'])}</button>
  <button data-v="graph">{esc(words['graph'])}</button>
  <button data-v="tree">{esc(words['tree'])}</button>
  <button data-v="tags">{esc(words['tags'])}</button>
</nav>
<div class="wrap">
  <main class="card">
    <div class="legend" id="legend"></div>
    <section class="view on" id="matrix"><div class="scroll"><table class="mx" id="mx"></table></div></section>
    <section class="view" id="graph"></section>
    <section class="view tree" id="tree"></section>
    <section class="view" id="tags"></section>
  </main>
  <aside><div class="card panel" id="panel"><p class="empty">{esc(words['pick'])}</p></div></aside>
</div>"""
    payload = {"W": words, "CG": cgroups, "C": cats, "TG": tgroups, "T": tags, "L": links}
    html_text = shell(title=text(data.get("title")) or "Cross reference", subtitle=text(data.get("subtitle")),
                      lead_html=lead, ko=ko, css=CSS, body=body, script=JS, payload=payload,
                      foot=text(data.get("note")))
    return Page(html_text, 1440, max(900, 260 + 26 * (len(cats) + len(cgroups))), warnings)


def _list(data: dict, key: str) -> list:
    v = data.get(key)
    if not isinstance(v, list) or not v:
        raise SpecError(f"`{key}:` must be a list of groups, each with items")
    return v


CSS = """
.pipe{display:flex;flex-wrap:wrap;gap:6px;list-style:none;max-width:1440px;margin:10px auto 0;padding:0 24px;counter-reset:p}
.pipe li{counter-increment:p;flex:1 1 140px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:7px 10px;font-weight:600;font-size:14px}
.pipe li::before{content:counter(p);color:var(--sub);font-weight:400;margin-right:6px}
.pipe li small{display:block;font-weight:400;color:var(--sub);font-size:12px}
.pipe li.here{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
.view{display:none}.view.on{display:block}
.scroll{overflow:auto;max-height:78vh}
table.mx{border-collapse:separate;border-spacing:0;font-size:13px}
.mx th,.mx td{padding:0}
.mx thead th{position:sticky;top:0;background:var(--card);z-index:2;vertical-align:bottom}
.mx thead th.corner{left:0;z-index:3;text-align:left;padding:0 8px 6px 0;color:var(--sub);font-weight:400}
.mx .colh{writing-mode:vertical-rl;white-space:nowrap;padding:6px 0;cursor:pointer;font-weight:500;width:30px;margin:0 auto;font-size:12.5px}
.mx .colh.cjk{text-orientation:upright;letter-spacing:-1px}
.mx .colh:hover,.mx .colh.sel{text-decoration:underline}
.mx tbody th{position:sticky;left:0;background:var(--card);text-align:left;font-weight:400;white-space:nowrap;padding:3px 10px 3px 0;cursor:pointer;z-index:1;max-width:260px;overflow:hidden;text-overflow:ellipsis}
.mx tbody th:hover,.mx tbody th.sel{color:var(--accent)}
.mx tr.grp th{font-weight:700;padding-top:12px;color:var(--sub);cursor:default;font-size:12px}
.mx td.c{width:30px;height:26px;text-align:center;cursor:pointer}
.mx td.c span{display:inline-block;border-radius:50%;vertical-align:middle}
.mx td.c:hover,.mx td.hl{background:var(--soft)}
.mx td.dim span{opacity:.18}
.pre{display:inline-block;min-width:62px;color:var(--sub)}
#graph svg{display:block;width:100%;height:auto}
#graph text{font-size:12.5px;fill:var(--ink);cursor:pointer}
#graph text.gh{font-weight:700;fill:var(--sub);font-size:12px;cursor:default}
#graph path{fill:none;stroke-opacity:.35;transition:stroke-opacity .15s}
#graph .faded{opacity:.12}
#graph path.faded{stroke-opacity:.04}
#graph path.lit{stroke-opacity:.9}
.tree details{border-bottom:1px solid var(--line);padding:6px 0}
.tree summary{cursor:pointer;font-weight:700}
.tree ul{margin:6px 0 6px 6px;padding-left:18px}
.tree li{margin:3px 0}
.tree .ci{cursor:pointer}
.tree .ci:hover{color:var(--accent)}
.tg{margin-bottom:14px}
.tg h3{font-size:14px;margin:0 0 4px}
.crit{background:var(--soft);border-radius:8px;padding:8px 10px;font-size:13.5px;margin:6px 0 10px}
.snip{border-left:3px solid var(--line);padding:4px 0 4px 10px;margin:8px 0;font-size:13.5px}
.snip .where{font-size:12px;color:var(--sub);display:block;margin-bottom:2px}
@media (max-width:900px){.pipe{padding:0 16px}.mx tbody th{max-width:150px}}
"""

JS = r"""
const {W, CG, C, TG, T, L} = D;
const col = i => TG[T[i].g].color;
const esc = s => String(s).replace(/[&<>"]/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));
const cname = c => (c.prefix ? c.prefix + ' ' : '') + c.label;
const link = (c, t) => L[c + ',' + t];
const cjk = s => /[ㄱ-힝一-鿿]/.test(s);
document.getElementById('legend').innerHTML = TG.map(g => `<span><i style="background:${g.color}"></i>${esc(g.name)}</span>`).join('');
document.querySelectorAll('nav.bar button').forEach(b => b.onclick = () => {
  document.querySelectorAll('nav.bar button').forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('on', v.id === b.dataset.v));
});

function buildMatrix() {
  let h = `<thead><tr><th class="corner">${esc(W.category)} \\ ${esc(W.tag)}</th>`;
  T.forEach((t, i) => h += `<th><div class="colh${cjk(t.name) ? ' cjk' : ''}" data-t="${i}" style="color:${col(i)}">${esc(t.name)}</div></th>`);
  h += '</tr></thead><tbody>';
  let g = -1;
  C.forEach((c, r) => {
    if (c.g !== g) { g = c.g; if (CG[g].name) h += `<tr class="grp"><th colspan="${T.length + 1}">${esc(CG[g].name)}</th></tr>`; }
    h += `<tr><th data-c="${r}" title="${esc(cname(c))}">${c.prefix ? `<span class="pre">${esc(c.prefix)}</span>` : ''}${esc(c.label)}</th>`;
    T.forEach((t, i) => {
      const x = link(r, i), s = x ? Math.min(20, 6 + Math.sqrt(x.n) * 2.6) : 0;
      h += `<td class="c" data-c="${r}" data-t="${i}">${x ? `<span style="width:${s}px;height:${s}px;background:${col(i)}" title="${esc(c.label)} × ${esc(t.name)}: ${x.n}"></span>` : ''}</td>`;
    });
    h += '</tr>';
  });
  const mx = document.getElementById('mx');
  mx.innerHTML = h + '</tbody>';
  mx.onclick = e => {
    const td = e.target.closest('td.c'), th = e.target.closest('tbody th[data-c]'), ch = e.target.closest('.colh');
    if (td && link(+td.dataset.c, +td.dataset.t)) showCell(+td.dataset.c, +td.dataset.t);
    else if (th) showCat(+th.dataset.c);
    else if (ch) showTag(+ch.dataset.t);
  };
}
function highlight(c, t) {
  const any = c != null || t != null;
  document.querySelectorAll('#mx td.c').forEach(td => {
    const on = (c == null || +td.dataset.c === c) && (t == null || +td.dataset.t === t);
    td.classList.toggle('dim', any && !on);
    td.classList.toggle('hl', any && on && !!td.firstChild);
  });
  document.querySelectorAll('#mx tbody th[data-c]').forEach(th => th.classList.toggle('sel', +th.dataset.c === c));
  document.querySelectorAll('#mx .colh').forEach(x => x.classList.toggle('sel', +x.dataset.t === t));
  graphFocus(c, t);
}

let G = {};
function buildGraph() {
  const rowH = 24, top = 30, left = [], right = [];
  let y = top, g = -1;
  C.forEach((c, r) => { if (c.g !== g) { g = c.g; if (CG[g].name) { left.push({head: CG[g].name, y}); y += rowH; } } left.push({c: r, y}); y += rowH; });
  const H1 = y; y = top; g = -1;
  T.forEach((t, i) => { if (t.g !== g) { g = t.g; right.push({head: TG[g].name, y, g}); y += rowH; } right.push({t: i, y}); y += rowH; });
  const H = Math.max(H1, y) + 10, off = (H - 10 - y) / 2;
  right.forEach(r => r.y += off);
  const Wd = 980, LX = 330, RX = Wd - 230, cy = {}, ty = {};
  left.forEach(r => r.c != null && (cy[r.c] = r.y));
  right.forEach(r => r.t != null && (ty[r.t] = r.y));
  let s = `<svg viewBox="0 0 ${Wd} ${H}" role="img">`;
  Object.entries(L).forEach(([k, x]) => {
    const [c, t] = k.split(',').map(Number), y1 = cy[c] - 4, y2 = ty[t] - 4, m = (LX + RX) / 2;
    s += `<path data-c="${c}" data-t="${t}" d="M${LX + 6},${y1} C${m},${y1} ${m},${y2} ${RX - 10},${y2}" stroke="${col(t)}" stroke-width="${(0.8 + Math.log2(1 + x.n) * 0.7).toFixed(2)}"/>`;
  });
  const cut = s => s.length > 22 ? s.slice(0, 22) + '…' : s;
  left.forEach(r => s += r.head != null ? `<text class="gh" x="${LX}" y="${r.y}" text-anchor="end">${esc(r.head)}</text>`
    : `<text data-c="${r.c}" x="${LX}" y="${r.y}" text-anchor="end">${esc(cut(C[r.c].label))}${C[r.c].prefix ? '  ' + esc(C[r.c].prefix) : ''}</text>`);
  right.forEach(r => s += r.head != null ? `<text class="gh" x="${RX}" y="${r.y}" style="fill:${TG[r.g].color}">${esc(r.head)}</text>`
    : `<text data-t="${r.t}" x="${RX}" y="${r.y}" style="fill:${col(r.t)}">● ${esc(T[r.t].name)}</text>`);
  const el = document.getElementById('graph');
  el.innerHTML = `<p class="empty" style="margin:0 0 6px">${esc(W.hover)}</p>${s}</svg>`;
  const svg = el.querySelector('svg');
  const pick = e => e.target.closest('text[data-c],text[data-t]');
  svg.addEventListener('mouseover', e => { const x = pick(e); if (x) graphFocus(x.dataset.c != null ? +x.dataset.c : null, x.dataset.t != null ? +x.dataset.t : null, true); });
  svg.addEventListener('mouseleave', () => graphFocus(G.c, G.t, true));
  svg.addEventListener('click', e => { const x = pick(e); if (x) x.dataset.c != null ? showCat(+x.dataset.c) : showTag(+x.dataset.t); });
}
function graphFocus(c, t, hover) {
  if (!hover) G = {c, t};
  const el = document.getElementById('graph'), any = c != null || t != null, lt = new Set(), lc = new Set();
  Object.keys(L).forEach(k => { const [a, b] = k.split(',').map(Number); if (a === c) lt.add(b); if (b === t) lc.add(a); });
  el.querySelectorAll('path').forEach(p => {
    const on = (c == null || +p.dataset.c === c) && (t == null || +p.dataset.t === t);
    p.classList.toggle('faded', any && !on); p.classList.toggle('lit', any && on);
  });
  el.querySelectorAll('text[data-c]').forEach(x => x.classList.toggle('faded', any && !(+x.dataset.c === c || lc.has(+x.dataset.c))));
  el.querySelectorAll('text[data-t]').forEach(x => x.classList.toggle('faded', any && !(+x.dataset.t === t || lt.has(+x.dataset.t))));
}

function buildTree() {
  let h = '', g = -1;
  C.forEach((c, r) => {
    if (c.g !== g) { if (g >= 0) h += '</ul></details>'; g = c.g; h += `<details open><summary>${esc(CG[g].name || W.category)}</summary><ul>`; }
    h += `<li><span class="ci" data-c="${r}"><b>${esc(c.prefix)}</b> ${esc(c.label)}</span>${c.meta ? ` <span class="meta">· ${esc(c.meta)}</span>` : ''}`;
    if (c.kids.length) h += '<ul>' + c.kids.map(k => `<li>${esc(k)}</li>`).join('') + '</ul>';
    h += '</li>';
  });
  const el = document.getElementById('tree');
  el.innerHTML = h + '</ul></details>';
  el.onclick = e => { const x = e.target.closest('.ci'); if (x) showCat(+x.dataset.c); };
}

function buildTags() {
  let h = '';
  TG.forEach((g, k) => {
    h += `<div class="tg"><h3 style="color:${g.color}">${esc(g.name)}</h3><div class="chips">`;
    T.forEach((t, i) => {
      if (t.g !== k) return;
      const n = C.filter((c, r) => link(r, i)).length;
      h += `<button class="chip" data-t="${i}" title="${esc(t.crit)}">${esc(t.name)}<b>${n}${esc(W.cats)}</b></button>`;
    });
    h += '</div></div>';
  });
  const el = document.getElementById('tags');
  el.innerHTML = h + `<p class="note">${esc(W.count_note)}</p>`;
  el.onclick = e => { const x = e.target.closest('.chip'); if (x) showTag(+x.dataset.t); };
}

const P = document.getElementById('panel');
const notes = (c, t, max) => {
  const x = link(c, t), list = x.notes.length ? x.notes.slice(0, max) : [W.no_notes];
  return list.map(s => `<div class="snip" style="border-color:${col(t)}"><span class="where">${esc(cname(C[c]))} · ${esc(T[t].name)}</span>${esc(s)}</div>`).join('');
};
function showCat(r) {
  const c = C[r], ts = T.map((t, i) => i).filter(i => link(r, i)).sort((a, b) => link(r, b).n - link(r, a).n);
  P.innerHTML = `<h2>${esc(cname(c))}</h2><div class="meta">${esc(CG[c.g].name)}${c.meta ? ' · ' + esc(c.meta) : ''}</div>`
    + (c.kids.length ? '<ul style="margin:0 0 8px;padding-left:18px">' + c.kids.map(k => `<li>${esc(k)}</li>`).join('') + '</ul>' : '')
    + `<div class="meta">${esc(W.linked)} ${ts.length}</div><div class="chips">`
    + ts.map(i => `<button class="chip" data-cell="${r},${i}" style="border-color:${col(i)}">${esc(T[i].name)}<b>${link(r, i).n}</b></button>`).join('') + '</div>';
  highlight(r, null);
}
function showTag(i) {
  const cs = C.map((c, r) => r).filter(r => link(r, i)), total = cs.reduce((a, r) => a + link(r, i).n, 0);
  P.innerHTML = `<h2 style="color:${col(i)}">${esc(T[i].name)}</h2><div class="meta">${esc(TG[T[i].g].name)} · ${cs.length}${esc(W.cats)} ${esc(W.category)} · ${total}${esc(W.times)}</div>`
    + (T[i].crit ? `<div class="crit"><b>${esc(W.criteria)}</b> ${esc(T[i].crit)}</div>` : '')
    + `<div class="meta">${esc(W.gather)}</div>` + cs.map(r => notes(r, i, 2)).join('');
  highlight(null, i);
}
function showCell(r, i) {
  P.innerHTML = `<h2>${esc(cname(C[r]))} × <span style="color:${col(i)}">${esc(T[i].name)}</span></h2><div class="meta">${link(r, i).n}${esc(W.times)}</div>`
    + notes(r, i, 5) + `<div class="chips"><button class="chip" data-tag="${i}">${esc(W.all_tag)}</button><button class="chip" data-ch="${r}">${esc(W.this_cat)}</button></div>`;
  highlight(r, i);
}
P.onclick = e => {
  const b = e.target.closest('.chip'); if (!b) return;
  if (b.dataset.cell) { const [r, i] = b.dataset.cell.split(',').map(Number); showCell(r, i); }
  else if (b.dataset.tag) showTag(+b.dataset.tag);
  else if (b.dataset.ch) showCat(+b.dataset.ch);
};
buildMatrix(); buildGraph(); buildTree(); buildTags();
"""
