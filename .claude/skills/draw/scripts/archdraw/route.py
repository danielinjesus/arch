"""Draw paths for edges and find a free spot for each edge label.

A path is a list of cubic Bézier segments. Neighbouring columns get an S-curve; an edge that would
run through another node takes the nearest free horizontal lane instead, with rounded corners.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import layout as L
from .layout import Box, Layout
from .spec import Edge, Spec

P = tuple[float, float]
Seg = tuple[P, P, P, P]

ARROW_LEN = 15
ARROW_W = 17
PORT_SPREAD = 0.62  # share of the tile side that ports may use


@dataclass
class Route:
    edge: Edge
    segs: list[Seg]
    color: str
    head: tuple[P, P] | None          # (tip, direction) at the target
    tail: tuple[P, P] | None          # (tip, direction) at the source, for both-way edges
    label_box: Box | None = None
    lane: tuple[float, float] | None = None  # arc-length range of the free lane, if any


def _line(a: P, b: P) -> Seg:
    return (a, (a[0] + (b[0] - a[0]) / 3, a[1] + (b[1] - a[1]) / 3),
            (a[0] + 2 * (b[0] - a[0]) / 3, a[1] + 2 * (b[1] - a[1]) / 3), b)


def _bez(s: Seg, t: float) -> P:
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = s
    u = 1 - t
    return (u ** 3 * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x3,
            u ** 3 * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y3)


def sample(segs: list[Seg], per: int = 24) -> list[tuple[P, float]]:
    pts: list[tuple[P, float]] = []
    dist = 0.0
    prev = None
    for s in segs:
        for i in range(per + 1):
            if prev is not None and i == 0:
                continue
            p = _bez(s, i / per)
            if prev is not None:
                dist += math.dist(prev, p)
            pts.append((p, dist))
            prev = p
    return pts


def point_at(pts: list[tuple[P, float]], d: float) -> P:
    for (p, dp), (q, dq) in zip(pts, pts[1:]):
        if dq >= d:
            t = 0 if dq == dp else (d - dp) / (dq - dp)
            return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    return pts[-1][0]


def _rounded(points: list[P], radius: float = 22) -> list[Seg]:
    """Polyline -> cubic segments with rounded corners."""
    pts = [p for i, p in enumerate(points) if i == 0 or math.dist(p, points[i - 1]) > 0.5]
    if len(pts) < 3:
        return [_line(pts[0], pts[-1])]
    segs: list[Seg] = []
    cur = pts[0]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        r = min(radius, math.dist(a, b) / 2, math.dist(b, c) / 2)
        ab = ((b[0] - a[0]) / (math.dist(a, b) or 1), (b[1] - a[1]) / (math.dist(a, b) or 1))
        bc = ((c[0] - b[0]) / (math.dist(b, c) or 1), (c[1] - b[1]) / (math.dist(b, c) or 1))
        p_in = (b[0] - ab[0] * r, b[1] - ab[1] * r)
        p_out = (b[0] + bc[0] * r, b[1] + bc[1] * r)
        segs.append(_line(cur, p_in))
        k = 0.55
        segs.append((p_in, (p_in[0] + ab[0] * r * k, p_in[1] + ab[1] * r * k),
                     (p_out[0] - bc[0] * r * k, p_out[1] - bc[1] * r * k), p_out))
        cur = p_out
    segs.append(_line(cur, pts[-1]))
    return segs


def _sides(lay: Layout, e: Edge) -> tuple[str, str]:
    a, b = lay.nodes[e.src].col, lay.nodes[e.dst].col
    if b > a:
        return "R", "L"
    if b < a:
        return "L", "R"
    return "R", "R"


def _hits(segs: list[Seg], lay: Layout, skip: set[str]) -> list[str]:
    boxes = {n: g.box.inflate(6) for n, g in lay.nodes.items() if n not in skip}
    hit = []
    for p, _ in sample(segs, 16):
        for n, b in boxes.items():
            if n not in hit and b.contains(*p):
                hit.append(n)
    return hit


def route_all(spec: Spec, lay: Layout) -> tuple[list[Route], list[str]]:
    warnings: list[str] = []
    sides = [_sides(lay, e) for e in spec.edges]

    # ports: spread the ends that share a side of a tile, ordered by where the other end is
    ends: dict[tuple[str, str], list[tuple[float, int, int]]] = {}
    for i, (e, (s_side, d_side)) in enumerate(zip(spec.edges, sides)):
        ends.setdefault((e.src, s_side), []).append((lay.nodes[e.dst].mid, i, 0))
        ends.setdefault((e.dst, d_side), []).append((lay.nodes[e.src].mid, i, 1))
    port: dict[tuple[int, int], P] = {}
    for (nid, side), lst in ends.items():
        lst.sort()
        t = lay.nodes[nid].tile
        n = len(lst)
        step = min(22.0, L.TILE * PORT_SPREAD / max(1, n - 1))
        x = t.r + 3 if side == "R" else t.x - 3
        for k, (_, i, which) in enumerate(lst):
            port[(i, which)] = (x, t.y + t.h / 2 + (k - (n - 1) / 2) * step)

    # edges between the same two nodes bow apart so their labels don't collide
    pairs: dict[frozenset, list[int]] = {}
    for i, e in enumerate(spec.edges):
        pairs.setdefault(frozenset((e.src, e.dst)), []).append(i)
    bow: dict[int, float] = {}
    for lst in pairs.values():
        for k, i in enumerate(lst):
            bow[i] = (k - (len(lst) - 1) / 2) * 30 if len(lst) > 1 else 0.0

    routes: list[Route] = []
    lanes_used: list[float] = []
    for i, e in enumerate(spec.edges):
        p0, p1 = port[(i, 0)], port[(i, 1)]
        s_side, d_side = sides[i]
        sx = 1 if s_side == "R" else -1
        dx = 1 if d_side == "R" else -1
        span = abs(lay.nodes[e.dst].col - lay.nodes[e.src].col)
        lane = None
        if s_side == d_side:  # same column: a bulge to the right
            k = 46 + abs(p1[1] - p0[1]) * 0.22
            segs = [(p0, (p0[0] + k, p0[1]), (p1[0] + k, p1[1]), p1)]
        else:
            k = max(34.0, abs(p1[0] - p0[0]) * 0.45)
            b = bow[i]
            segs = [(p0, (p0[0] + sx * k, p0[1] + b), (p1[0] + dx * k, p1[1] + b), p1)]
            if span > 1 and _hits(segs, lay, {e.src, e.dst}):
                detour = _detour(lay, e, p0, p1, sx, lanes_used)
                if detour:
                    segs, lane = detour
        if (hit := _hits(segs, lay, {e.src, e.dst})):
            warnings.append(f"edge {e.src} -> {e.dst} runs through {', '.join(hit)}: "
                            f"pin columns with col:, or use layout: manual")
        segs, head, tail = _trim(segs, e.both)
        color = e.color or spec.nodes[e.dst].color
        routes.append(Route(e, segs, color, head, tail, lane=lane))

    _place_labels(spec, lay, routes, warnings)
    return routes, warnings


def _detour(lay: Layout, e: Edge, p0: P, p1: P, sx: int, lanes_used: list[float]):
    c0, c1 = int(lay.nodes[e.src].col), int(lay.nodes[e.dst].col)
    if not (0 <= min(c0, c1) and max(c0, c1) < len(lay.col_left) and lay.nodes[e.src].col == c0
            and lay.nodes[e.dst].col == c1):
        return None  # fractional manual columns: keep the curve
    if sx > 0:
        xa = (lay.col_right[c0] + lay.col_left[c0 + 1]) / 2
        xb = (lay.col_right[c1 - 1] + lay.col_left[c1]) / 2
    else:
        xa = (lay.col_left[c0] + lay.col_right[c0 - 1]) / 2
        xb = (lay.col_left[c1] + lay.col_right[c1 + 1]) / 2
    lo_x, hi_x = sorted((xa, xb))
    obstacles = sorted(
        (g.box.inflate(12) for n, g in lay.nodes.items()
         if n not in (e.src, e.dst) and g.box.r > lo_x and g.box.x < hi_x),
        key=lambda b: b.y)
    if not obstacles:
        return None
    merged: list[list[float]] = []
    for b in obstacles:
        if merged and b.y <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b.b)
        else:
            merged.append([b.y, b.b])
    candidates = [merged[0][0] - 24, merged[-1][1] + 24]
    for (_, top_end), (next_top, _) in zip(merged, merged[1:]):
        if next_top - top_end >= 26:
            candidates.append((top_end + next_top) / 2)
    # a lane level with one end needs no jog at that end
    candidates += [y for y in (p0[1], p1[1]) if not any(a - 4 <= y <= b + 4 for a, b in merged)]
    target = (p0[1] + p1[1]) / 2
    for cy in sorted(candidates, key=lambda y: abs(y - p0[1]) + abs(y - p1[1])
                     + 0.05 * min(abs(y - p0[1]), abs(y - p1[1]))):
        while any(abs(cy - u) < 12 for u in lanes_used):
            cy += 14 if cy >= target else -14
        segs = _rounded([p0, (xa, p0[1]), (xa, cy), (xb, cy), (xb, p1[1]), p1])
        if not _hits(segs, lay, {e.src, e.dst}):
            lanes_used.append(cy)
            pts = sample(segs)
            # arc-length range of the horizontal lane, for the label
            on_lane = [d for p, d in pts if abs(p[1] - cy) < 0.5 and lo_x + 20 <= p[0] <= hi_x - 20]
            lane = (min(on_lane), max(on_lane)) if on_lane else None
            return segs, lane
    return None


def _unit(a: P, b: P) -> P:
    d = math.dist(a, b) or 1.0
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _trim(segs: list[Seg], both: bool):
    """Shorten the path so the stroke stops where an arrowhead begins."""
    segs = list(segs)
    p0, c1, c2, p1 = segs[-1]
    d = _unit(c2 if math.dist(c2, p1) > 1 else c1, p1)
    head = (p1, d)
    segs[-1] = (p0, c1, c2, (p1[0] - d[0] * ARROW_LEN, p1[1] - d[1] * ARROW_LEN))
    tail = None
    if both:
        q0, k1, k2, q1 = segs[0]
        d0 = _unit(k1 if math.dist(k1, q0) > 1 else k2, q0)
        tail = (q0, d0)
        segs[0] = ((q0[0] - d0[0] * ARROW_LEN, q0[1] - d0[1] * ARROW_LEN), k1, k2, q1)
    return segs, head, tail


def _place_labels(spec: Spec, lay: Layout, routes: list[Route], warnings: list[str]) -> None:
    blocked = [g.box.inflate(4) for g in lay.nodes.values()]
    for gid, z in lay.zones.items():
        w = _tab_width(spec.groups[gid].label)
        blocked.append(Box(z.x + 14, z.y - 17, w, 34))
    placed: list[Box] = []
    order = sorted(range(len(routes)), key=lambda i: routes[i].lane is not None)
    for i in order:
        r = routes[i]
        w = L.edge_label_width(r.edge.label, r.edge.step)
        if not w:
            continue
        h = L.EDGE_LABEL_H
        pts = sample(r.segs)
        total = pts[-1][1]
        if r.lane:
            a, b = r.lane
            along = [a + (b - a) * f for f in (0.5, 0.35, 0.65, 0.2, 0.8)]
        else:
            along = [total * f for f in (0.5, 0.42, 0.58, 0.34, 0.66, 0.26, 0.74)]
        cands = [(d, dy) for dy in (0, -7, 7, -14, 14) for d in along]
        best, best_cost = None, None
        for d, dy in cands:
            x, y = point_at(pts, d)
            box = Box(x - w / 2, y + dy - h / 2, w, h)
            cost = sum(box.overlap(o) for o in blocked) + 2 * sum(box.overlap(o.inflate(3)) for o in placed)
            if best_cost is None or cost < best_cost - 1e-6:
                best, best_cost = box, cost
            if cost == 0:
                break
        if best_cost:
            warnings.append(f"label {r.edge.label!r} on {r.edge.src} -> {r.edge.dst} is crowded: "
                            "shorten it, or give the columns more room")
        r.label_box = best
        placed.append(best)


def _tab_width(label: str) -> float:
    from . import fonts
    return fonts.text_width(label, L.ZONE_TAB_SIZE) + 28
