"""Turn a laid-out spec into a cartoon SVG, and wrap it in an HTML page."""
from __future__ import annotations

import html
import re
import zlib

from . import fonts, icons, palette
from . import layout as L
from .layout import Box, Layout
from .palette import INK, PAPER, WHITE
from .route import ARROW_LEN, ARROW_W, Route, sample
from .spec import Spec

MARGIN = 52
TITLE_SIZE = 38
SUB_SIZE = 18
ROLE_INK = "#3B3552"
ICON = 80

CSS = """
.flow{stroke-dasharray:1.5 16;animation:arch-flow 1.1s linear infinite}
@keyframes arch-flow{to{stroke-dashoffset:-17.5}}
.node .pop{transition:transform .18s ease;transform-box:fill-box;transform-origin:center}
a.node:hover .pop,a.node:focus-visible .pop{transform:translate(-3px,-4px) rotate(-3deg)}
a.node{cursor:pointer}
a.node:focus{outline:none}
a.node:focus-visible .tile{stroke-width:6}
@media (prefers-reduced-motion:reduce){.flow{animation:none}.node .pop{transition:none}}
"""


def _e(s) -> str:
    return html.escape(str(s), quote=True)


def _f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _tilt(key: str, max_deg: float) -> float:
    return ((zlib.crc32(key.encode()) % 1000) / 999 * 2 - 1) * max_deg


def _path_d(segs) -> str:
    out = [f"M{_f(segs[0][0][0])} {_f(segs[0][0][1])}"]
    for _, c1, c2, p in segs:
        out.append(f"C{_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p[0])} {_f(p[1])}")
    return " ".join(out)


def _text(x, y, s, size, fill=INK, anchor="middle", halo=None) -> str:
    h = (f' paint-order="stroke" stroke="{halo}" stroke-width="6" stroke-linejoin="round"' if halo else "")
    s = str(s)
    if fonts.ARROW not in s:
        return (f'<text x="{_f(x)}" y="{_f(y)}" font-size="{_f(size)}" text-anchor="{anchor}" '
                f'fill="{fill}"{h}>{_e(s)}</text>')
    # the font has no arrow: lay the words out by hand and draw each arrow
    pieces = fonts.split_arrows(s)
    total = fonts.text_width(s, size)
    cur = x - total / 2 if anchor == "middle" else (x - total if anchor == "end" else x)
    out = []
    ay = y - size * 0.32
    for i, piece in enumerate(pieces):
        if piece:
            out.append(f'<text x="{_f(cur)}" y="{_f(y)}" font-size="{_f(size)}" text-anchor="start" '
                       f'fill="{fill}"{h}>{_e(piece)}</text>')
            cur += fonts.text_width(piece, size)
        if i < len(pieces) - 1:
            a0, a1 = cur + size * 0.25, cur + size * (fonts.ARROW_EM - 0.25)
            d = (f"M{_f(a0)} {_f(ay)} H{_f(a1)} M{_f(a1 - size * 0.26)} {_f(ay - size * 0.24)} "
                 f"L{_f(a1)} {_f(ay)} L{_f(a1 - size * 0.26)} {_f(ay + size * 0.24)}")
            if halo:
                out.append(f'<path d="{d}" fill="none" stroke="{halo}" stroke-width="{_f(size * 0.11 + 5)}" '
                           'stroke-linecap="round" stroke-linejoin="round"/>')
            out.append(f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{_f(size * 0.11)}" '
                       'stroke-linecap="round" stroke-linejoin="round"/>')
            cur += size * fonts.ARROW_EM
    return "".join(out)


def chars_used(spec: Spec) -> str:
    parts = [spec.title, spec.subtitle, spec.note, icons.ICON_TEXT, "…0123456789"]
    for n in spec.nodes.values():
        parts += [n.label, n.tech, n.role]
    for e in spec.edges:
        parts += [e.label, str(e.step) if e.step is not None else ""]
    for g in spec.groups.values():
        parts.append(g.label)
    return "".join(parts)


def svg(spec: Spec, lay: Layout, routes: list[Route], interactive: bool = True) -> str:
    # bounds of everything drawn, in layout coordinates
    boxes = [g.box for g in lay.nodes.values()] + list(lay.zones.values())
    boxes += [r.label_box for r in routes if r.label_box]
    for r in routes:
        for p, _ in sample(r.segs, 8):
            boxes.append(Box(p[0] - 8, p[1] - 8, 16, 16))
    for gid, z in lay.zones.items():
        boxes.append(Box(z.x, z.y - 18, fonts.text_width(spec.groups[gid].label, L.ZONE_TAB_SIZE) + 44, 36))
    x0 = min(b.x for b in boxes) - 8
    y0 = min(b.y for b in boxes) - 8
    x1 = max(b.r for b in boxes) + 14
    y1 = max(b.b for b in boxes) + 14

    head = 0.0
    title_w = fonts.text_width(spec.title, TITLE_SIZE) if spec.title else 0.0
    if spec.title:
        head = 74 + (30 if spec.subtitle else 0)
    foot = 34 if spec.note else 0
    width = max(x1 - x0, title_w + 90, fonts.text_width(spec.subtitle, SUB_SIZE) + 20) + 2 * MARGIN
    height = (y1 - y0) + 2 * MARGIN + head + foot
    ox = MARGIN - x0 + max(0.0, (width - 2 * MARGIN - (x1 - x0)) / 2)
    oy = MARGIN + head - y0

    out: list[str] = []
    w = out.append
    w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{_f(width)}" height="{_f(height)}" '
      f'viewBox="0 0 {_f(width)} {_f(height)}" role="img" aria-labelledby="arch-title" '
      f'font-family="{_e(fonts.STACK)}">')
    w(f'<title id="arch-title">{_e(spec.title or "Architecture")}</title>')
    w("<defs><style>" + fonts.font_face(chars_used(spec)) + (CSS if interactive else "") + "</style>")
    w(f'<pattern id="arch-dots" width="22" height="22" patternUnits="userSpaceOnUse">'
      f'<circle cx="11" cy="11" r="1.7" fill="{palette.DOTS}"/></pattern></defs>')
    w(f'<rect width="100%" height="100%" fill="{PAPER}"/>')
    w('<rect width="100%" height="100%" fill="url(#arch-dots)"/>')
    w(f'<rect x="10" y="10" width="{_f(width - 20)}" height="{_f(height - 20)}" rx="26" fill="none" '
      f'stroke="{INK}" stroke-width="4"/>')

    if spec.title:
        _title(w, spec, title_w)

    w(f'<g transform="translate({_f(ox)} {_f(oy)})">')
    for gid, z in lay.zones.items():
        _zone(w, z, spec.groups[gid].color)
    for r in routes:
        _edge(w, r, interactive)
    for nid, g in lay.nodes.items():
        _node(w, spec.nodes[nid], g, interactive)
    for gid, z in lay.zones.items():
        _tab(w, z, spec.groups[gid].label, spec.groups[gid].color, gid)
    for r in routes:
        if r.label_box:
            _edge_label(w, r)
    w("</g>")
    if spec.note:
        w(_text(MARGIN - 8, height - 30, spec.note, 13.5, ROLE_INK, "start"))
    w("</svg>")
    return "\n".join(out)


def _sparkle(x, y, r, fill) -> str:
    k = r * 0.28
    d = (f"M{_f(x)} {_f(y - r)} C{_f(x + k)} {_f(y - k)} {_f(x + k)} {_f(y - k)} {_f(x + r)} {_f(y)} "
         f"C{_f(x + k)} {_f(y + k)} {_f(x + k)} {_f(y + k)} {_f(x)} {_f(y + r)} "
         f"C{_f(x - k)} {_f(y + k)} {_f(x - k)} {_f(y + k)} {_f(x - r)} {_f(y)} "
         f"C{_f(x - k)} {_f(y - k)} {_f(x - k)} {_f(y - k)} {_f(x)} {_f(y - r)} Z")
    return f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'


def _title(w, spec: Spec, title_w: float) -> None:
    x, base = MARGIN - 6, MARGIN + 30
    w(f'<rect x="{_f(x - 10)}" y="{_f(base - 15)}" width="{_f(title_w + 20)}" height="20" rx="7" '
      f'fill="{palette.COLORS["yellow"]}" transform="rotate(-1.2 {_f(x)} {_f(base)})"/>')
    w(_text(x, base, spec.title, TITLE_SIZE, INK, "start"))
    w(_sparkle(x + title_w + 26, base - 26, 12, palette.COLORS["pink"]))
    w(_sparkle(x + title_w + 48, base - 4, 8, palette.COLORS["sky"]))
    if spec.subtitle:
        w(_text(x + 2, base + 34, spec.subtitle, SUB_SIZE, ROLE_INK, "start"))


def _zone(w, z: Box, color: str) -> None:
    w(f'<rect x="{_f(z.x)}" y="{_f(z.y)}" width="{_f(z.w)}" height="{_f(z.h)}" rx="28" '
      f'fill="{palette.zone(color)}" stroke="{palette.mix(color, INK, 0.15)}" stroke-width="3" '
      f'stroke-dasharray="12 9"/>')


def _tab(w, z: Box, label: str, color: str, key: str) -> None:
    tw = fonts.text_width(label, L.ZONE_TAB_SIZE) + 28
    x, y, h = z.x + 16, z.y - 15, 30
    a = _tilt("tab" + key, 2.0) - 1
    w(f'<g transform="rotate({_f(a)} {_f(x + tw / 2)} {_f(y + h / 2)})">')
    w(f'<rect x="{_f(x + 3)}" y="{_f(y + 3)}" width="{_f(tw)}" height="{h}" rx="15" fill="{INK}"/>')
    w(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(tw)}" height="{h}" rx="15" fill="{color}" '
      f'stroke="{INK}" stroke-width="2.5"/>')
    w(_text(x + tw / 2, y + 21, label, L.ZONE_TAB_SIZE, palette.readable_on(color)))
    w("</g>")


def _arrow(tip, d, color) -> str:
    bx, by = tip[0] - d[0] * ARROW_LEN, tip[1] - d[1] * ARROW_LEN
    nx, ny = -d[1], d[0]
    pts = [(tip[0] + d[0] * 2, tip[1] + d[1] * 2),
           (bx + nx * ARROW_W / 2, by + ny * ARROW_W / 2),
           (bx - nx * ARROW_W / 2, by - ny * ARROW_W / 2)]
    return (f'<polygon points="{" ".join(f"{_f(x)},{_f(y)}" for x, y in pts)}" fill="{color}" '
            f'stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>')


def _edge(w, r: Route, interactive: bool) -> None:
    d = _path_d(r.segs)
    dash = ' stroke-dasharray="12 12"' if r.edge.dashed else ""
    w(f'<g class="edge"><path d="{d}" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"{dash}/>')
    w(f'<path d="{d}" fill="none" stroke="{r.color}" stroke-width="4.6" stroke-linecap="round"{dash}/>')
    if interactive and not r.edge.dashed:
        w(f'<path class="flow" d="{d}" fill="none" stroke="{WHITE}" stroke-width="2.4" stroke-linecap="round" '
          f'opacity=".9"/>')
    if r.head:
        w(_arrow(r.head[0], r.head[1], r.color))
    if r.tail:
        w(_arrow(r.tail[0], r.tail[1], r.color))
    w("</g>")


def _edge_label(w, r: Route) -> None:
    b = r.label_box
    cx, cy = b.x + b.w / 2, b.y + b.h / 2
    a = _tilt(f"{r.edge.src}>{r.edge.dst}", 2.2)
    w(f'<g class="edge-label" transform="rotate({_f(a)} {_f(cx)} {_f(cy)})">')
    w(f'<rect x="{_f(b.x + 3)}" y="{_f(b.y + 3)}" width="{_f(b.w)}" height="{_f(b.h)}" rx="{_f(b.h / 2)}" fill="{INK}"/>')
    w(f'<rect x="{_f(b.x)}" y="{_f(b.y)}" width="{_f(b.w)}" height="{_f(b.h)}" rx="{_f(b.h / 2)}" fill="{WHITE}" '
      f'stroke="{INK}" stroke-width="2.5"/>')
    tx = b.x
    if r.edge.step is not None:
        w(f'<circle cx="{_f(b.x + 15)}" cy="{_f(cy)}" r="10.5" fill="{palette.COLORS["yellow"]}" '
          f'stroke="{INK}" stroke-width="2"/>')
        w(_text(b.x + 15, cy + 5, r.edge.step, 14))
        tx += L.STEP_W
    if r.edge.label:
        w(_text((tx + b.r) / 2 + (2 if r.edge.step is not None else 0), cy + 5.5, r.edge.label, L.EDGE_LABEL_SIZE))
    w("</g>")


def _node(w, n, g: L.NodeGeom, interactive: bool) -> None:
    t = g.tile
    tcx, tcy = t.x + t.w / 2, t.y + t.h / 2
    tip = " — ".join(x for x in (n.label, n.role) if x)
    if n.tech:
        tip += f"\n{n.tech}"
    link = interactive and n.doc
    if link:
        tip += f"\n{n.doc}"
        w(f'<a class="node" href="{_e(n.doc)}" target="_blank" rel="noopener" aria-label="{_e(n.label)}: {_e(n.doc)}">')
    else:
        w('<g class="node">')
    w(f"<title>{_e(tip)}</title>")
    a = _tilt(n.id, 2.4)
    w(f'<g transform="rotate({_f(a)} {_f(tcx)} {_f(tcy)})">')
    w(f'<rect x="{_f(t.x + 6)}" y="{_f(t.y + 6)}" width="{L.TILE}" height="{L.TILE}" rx="24" fill="{INK}"/>')
    w('<g class="pop">')
    w(f'<rect class="tile" x="{_f(t.x)}" y="{_f(t.y)}" width="{L.TILE}" height="{L.TILE}" rx="24" '
      f'fill="{palette.tile(n.color)}" stroke="{INK}" stroke-width="4"/>')
    w(f'<path d="M{_f(t.x + 13)} {_f(t.y + 36)} Q{_f(t.x + 13)} {_f(t.y + 13)} {_f(t.x + 36)} {_f(t.y + 13)}" '
      f'fill="none" stroke="{WHITE}" stroke-width="5" stroke-linecap="round" opacity=".85"/>')
    s = ICON / 100
    w(f'<g transform="translate({_f(t.x + (L.TILE - ICON) / 2)} {_f(t.y + (L.TILE - ICON) / 2)}) scale({s})" '
      f'stroke="{INK}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round">')
    w(icons.markup(n.icon, n.color))
    w("</g>")
    if link:
        bx, by = t.r - 6, t.y + 6
        w(f'<circle cx="{_f(bx)}" cy="{_f(by)}" r="12" fill="{WHITE}" stroke="{INK}" stroke-width="2.5"/>')
        w(f'<path d="M{_f(bx - 4)} {_f(by + 4)} L{_f(bx + 4)} {_f(by - 4)} M{_f(bx - 2)} {_f(by - 4.5)} '
          f'H{_f(bx + 4.5)} V{_f(by + 2)}" fill="none" stroke="{INK}" stroke-width="2.5" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    w("</g></g>")

    w(_text(g.cx, g.top + L.LABEL_H - 6, n.label, L.LABEL_SIZE, INK, halo=PAPER))
    y = t.b
    if n.tech:
        y += L.TECH_GAP
        tw = g.tech_w
        x = g.cx - tw / 2
        w(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(tw)}" height="{L.TECH_H}" rx="{L.TECH_H / 2}" '
          f'fill="{WHITE}" stroke="{INK}" stroke-width="2.2"/>')
        w(f'<circle cx="{_f(x + 13)}" cy="{_f(y + L.TECH_H / 2)}" r="5" fill="{n.color}" stroke="{INK}" '
          f'stroke-width="1.6"/>')
        w(_text(x + 23, y + 18, n.tech, L.TECH_SIZE, INK, "start"))
        y += L.TECH_H
    if g.role_lines:
        y += L.ROLE_GAP
        for line in g.role_lines:
            y += L.ROLE_LINE
            w(_text(g.cx, y - 5, line, L.ROLE_SIZE, ROLE_INK, halo=PAPER))
    w("</a>" if link else "</g>")


def page(spec: Spec, svg_text: str) -> str:
    korean = bool(re.search(r"[가-힣]", chars_used(spec)))
    hint = "아이콘을 누르면 공식 문서가 열려요." if korean else "Click an icon to open its documentation."
    has_docs = any(n.doc for n in spec.nodes.values())
    title = spec.title or "Architecture"
    return f"""<!doctype html>
<html lang="{'ko' if korean else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)}</title>
<style>
:root{{--page:#F4EADB;--text:#1E1B2E}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--page:#17151F;--text:#F4EADB}}}}
:root[data-theme="dark"]{{--page:#17151F;--text:#F4EADB}}
html,body{{margin:0;background:var(--page);color:var(--text)}}
main{{max-width:1600px;margin:0 auto;padding:24px 16px 32px}}
main svg{{display:block;width:100%;height:auto}}
p{{font:15px/1.5 system-ui,sans-serif;text-align:center;margin:14px 0 0;opacity:.8}}
</style>
</head>
<body>
<main>
{svg_text}
{f'<p>{_e(hint)}</p>' if has_docs else ''}
</main>
</body>
</html>
"""
