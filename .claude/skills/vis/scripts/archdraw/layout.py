"""Place nodes: columns by flow (left to right), groups as boxes that nothing else enters.

Auto layout:
1. column = longest path from a source (back edges of cycles are ignored; `col:` pins a node);
2. each group becomes one block that spans its columns, so its zone never covers other nodes;
3. items in a column are ordered by the mean height of their neighbours, then pulled toward their
   neighbours and pushed apart until nothing overlaps.
Manual layout (`at: [col, row]` on every node) uses a plain grid.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import fonts
from .spec import Spec

TILE = 108
LABEL_SIZE = 23
LABEL_H = 30
LABEL_GAP = 10
TECH_SIZE = 14
TECH_H = 26
TECH_GAP = 12
ROLE_SIZE = 14.5
ROLE_LINE = 19
ROLE_GAP = 7
ROLE_MAX_W = 196
ROLE_MAX_LINES = 3
TILE_TOP = LABEL_H + LABEL_GAP          # node top -> tile top
TILE_MID = TILE_TOP + TILE / 2          # node top -> tile centre

EDGE_LABEL_SIZE = 15
EDGE_LABEL_H = 30
EDGE_LABEL_PAD = 12
STEP_W = 26

COL_GAP_MIN = 120
V_GAP = 46
ZONE_PAD = 22
ZONE_TAB = 16                           # extra room above members for the group tab
ZONE_TAB_SIZE = 17


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def r(self) -> float:
        return self.x + self.w

    @property
    def b(self) -> float:
        return self.y + self.h

    def inflate(self, d: float) -> "Box":
        return Box(self.x - d, self.y - d, self.w + 2 * d, self.h + 2 * d)

    def overlap(self, o: "Box") -> float:
        w = min(self.r, o.r) - max(self.x, o.x)
        h = min(self.b, o.b) - max(self.y, o.y)
        return w * h if w > 0 and h > 0 else 0.0

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x <= self.r and self.y <= y <= self.b


@dataclass
class NodeGeom:
    id: str
    col: float
    w: float
    h: float
    role_lines: list[str]
    label_w: float
    tech_w: float
    cx: float = 0.0
    top: float = 0.0

    @property
    def box(self) -> Box:
        return Box(self.cx - self.w / 2, self.top, self.w, self.h)

    @property
    def tile(self) -> Box:
        return Box(self.cx - TILE / 2, self.top + TILE_TOP, TILE, TILE)

    @property
    def mid(self) -> float:
        return self.top + TILE_MID


@dataclass
class Layout:
    nodes: dict[str, NodeGeom]
    zones: dict[str, Box]
    col_left: list[float]
    col_right: list[float]
    warnings: list[str] = field(default_factory=list)


def wrap(text: str, size: float, max_w: float, max_lines: int) -> list[str]:
    if not text:
        return []
    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}" if cur else word
        if fonts.text_width(trial, size) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        cur = ""
        for ch in word:  # a single word wider than the line: break it by characters
            if fonts.text_width(cur + ch, size) > max_w and cur:
                lines.append(cur)
                cur = ""
            cur += ch
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and fonts.text_width(last + "…", size) > max_w:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    return lines


def tech_width(tech: str) -> float:
    return fonts.text_width(tech, TECH_SIZE) + 30 if tech else 0.0


def edge_label_width(label: str, step) -> float:
    if not label and step is None:
        return 0.0
    w = fonts.text_width(label, EDGE_LABEL_SIZE) + 2 * EDGE_LABEL_PAD if label else 8
    return w + (STEP_W if step is not None else 0)


def _measure(spec: Spec) -> dict[str, NodeGeom]:
    out = {}
    for n in spec.nodes.values():
        role = wrap(n.role, ROLE_SIZE, ROLE_MAX_W, ROLE_MAX_LINES)
        label_w = fonts.text_width(n.label, LABEL_SIZE)
        tech_w = tech_width(n.tech)
        role_w = max((fonts.text_width(line, ROLE_SIZE) for line in role), default=0)
        w = max(TILE + 24, label_w + 12, tech_w + 6, role_w + 6)
        h = TILE_TOP + TILE
        if n.tech:
            h += TECH_GAP + TECH_H
        if role:
            h += ROLE_GAP + len(role) * ROLE_LINE
        out[n.id] = NodeGeom(n.id, 0, w, h, role, label_w, tech_w)
    return out


def layout(spec: Spec) -> Layout:
    geoms = _measure(spec)
    if spec.manual:
        return _manual(spec, geoms)
    return _auto(spec, geoms)


# ---------------------------------------------------------------- manual

def _manual(spec: Spec, g: dict[str, NodeGeom]) -> Layout:
    col_w = max(n.w for n in g.values()) + COL_GAP_MIN
    row_h = max(n.h for n in g.values()) + V_GAP + 20
    for n in spec.nodes.values():
        c, r = n.at
        g[n.id].col = c
        g[n.id].cx = c * col_w + col_w / 2
        g[n.id].top = r * row_h
    ncols = int(max(n.at[0] for n in spec.nodes.values())) + 1
    col_left = [c * col_w + COL_GAP_MIN / 2 for c in range(ncols)]
    col_right = [x + col_w - COL_GAP_MIN for x in col_left]
    zones = {}
    for gid in spec.groups:
        members = [g[n.id].box for n in spec.nodes.values() if n.group == gid]
        if members:
            zones[gid] = _zone_box(members)
    lay = Layout(g, zones, col_left, col_right)
    _check_overlaps(spec, lay)
    return lay


def _zone_box(members: list[Box]) -> Box:
    x = min(b.x for b in members) - ZONE_PAD
    y = min(b.y for b in members) - ZONE_PAD - ZONE_TAB
    r = max(b.r for b in members) + ZONE_PAD
    b = max(b.b for b in members) + ZONE_PAD
    return Box(x, y, r - x, b - y)


def _check_overlaps(spec: Spec, lay: Layout) -> None:
    ids = list(lay.nodes)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if lay.nodes[a].box.overlap(lay.nodes[b].box) > 0:
                lay.warnings.append(f"nodes {a} and {b} overlap: move one of them (at:)")
    for gid, z in lay.zones.items():
        for n in spec.nodes.values():
            if n.group != gid and z.overlap(lay.nodes[n.id].box) > 0:
                lay.warnings.append(f"node {n.id} sits inside group {gid}'s box: move it or add it to the group")


# ---------------------------------------------------------------- auto

def _ranks(spec: Spec) -> dict[str, int]:
    order = list(spec.nodes)
    out_edges: dict[str, list[str]] = {n: [] for n in order}
    for e in spec.edges:
        out_edges[e.src].append(e.dst)
    # drop back edges found by DFS, in declaration order
    forward: dict[str, list[str]] = {n: [] for n in order}
    state: dict[str, int] = {}

    def dfs(u: str) -> None:
        state[u] = 1
        for v in out_edges[u]:
            if state.get(v) == 1:
                continue  # back edge
            forward[u].append(v)
            if v not in state:
                dfs(v)
        state[u] = 2

    roots = [n for n in order if not any(n in out_edges[m] for m in order)] + order
    for n in roots:
        if n not in state:
            dfs(n)
    preds: dict[str, list[str]] = {n: [] for n in order}
    for u, vs in forward.items():
        for v in vs:
            preds[v].append(u)

    rank: dict[str, int] = {}
    pinned = {n.id: n.col for n in spec.nodes.values() if n.col is not None}

    def r(n: str) -> int:
        if n in rank:
            return rank[n]
        if n in pinned:
            rank[n] = pinned[n]
            return rank[n]
        rank[n] = max((r(p) + 1 for p in preds[n]), default=0)
        return rank[n]

    for n in order:
        r(n)
    # pull sources right next to what they feed
    for n in order:
        if n in pinned or preds[n] or not forward[n]:
            continue
        rank[n] = max(0, min(rank[v] for v in forward[n]) - 1)
    return rank


@dataclass
class _Item:
    key: str
    nodes: list[str]
    cols: list[int]
    h: float = 0.0
    y: float = 0.0
    offs: dict[str, float] = field(default_factory=dict)
    group: str | None = None


def _auto(spec: Spec, g: dict[str, NodeGeom]) -> Layout:
    rank = _ranks(spec)
    for nid, c in rank.items():
        g[nid].col = c
    ncols = max(rank.values()) + 1

    nbrs: dict[str, list[str]] = {n: [] for n in spec.nodes}
    for e in spec.edges:
        nbrs[e.src].append(e.dst)
        nbrs[e.dst].append(e.src)

    # items: one per ungrouped node, one per group (a block over its column range)
    items: list[_Item] = []
    item_of: dict[str, _Item] = {}
    for gid in spec.groups:
        members = [n.id for n in spec.nodes.values() if n.group == gid]
        if not members:
            continue
        cols = list(range(min(rank[m] for m in members), max(rank[m] for m in members) + 1))
        it = _Item(f"group:{gid}", members, cols, group=gid)
        items.append(it)
        for m in members:
            item_of[m] = it
    for n in spec.nodes.values():
        if n.group is None:
            it = _Item(n.id, [n.id], [rank[n.id]])
            items.append(it)
            item_of[n.id] = it

    # first guess: declaration order, stacked
    decl = {n: i for i, n in enumerate(spec.nodes)}
    col_items: list[list[_Item]] = [[] for _ in range(ncols)]
    for it in sorted(items, key=lambda i: min(decl[n] for n in i.nodes)):
        for c in it.cols:
            col_items[c].append(it)
    member_order: dict[str, list[list[str]]] = {}  # group item key -> per-column member lists

    def block_geometry(it: _Item) -> None:
        if it.group is None:
            it.h = g[it.nodes[0]].h
            it.offs = {it.nodes[0]: 0.0}
            return
        per_col = member_order[it.key]
        stacks = [sum(g[m].h for m in ms) + V_GAP * max(0, len(ms) - 1) for ms in per_col]
        inner = max(stacks)
        it.h = inner + 2 * ZONE_PAD + ZONE_TAB
        it.offs = {}
        for ms, sh in zip(per_col, stacks):
            y = ZONE_PAD + ZONE_TAB + (inner - sh) / 2
            for m in ms:
                it.offs[m] = y
                y += g[m].h + V_GAP

    for it in items:
        if it.group is not None:
            member_order[it.key] = [[m for m in sorted(it.nodes, key=decl.get) if rank[m] == c] for c in it.cols]
        block_geometry(it)
    _pack(col_items)

    def anchor(n: str) -> float:
        it = item_of[n]
        return it.y + it.offs[n] + TILE_MID

    def bary(n: str) -> float:
        ys = [anchor(m) for m in nbrs[n] if item_of[m] is not item_of[n]]
        return sum(ys) / len(ys) if ys else anchor(n)

    for _ in range(4):
        _relax(items, col_items, nbrs, item_of, anchor)
        keys = {it.key: sum(bary(n) for n in it.nodes) / len(it.nodes) for it in items}
        for c in range(ncols):
            col_items[c].sort(key=lambda it: keys[it.key])
        for it in items:
            if it.group is not None:
                member_order[it.key] = [sorted(ms, key=bary) for ms in member_order[it.key]]
                block_geometry(it)
        _pack(col_items)
    _relax(items, col_items, nbrs, item_of, anchor)
    _pack(col_items)
    low = min(it.y for it in items)
    for it in items:
        it.y -= low

    # columns, with room between them for the edge labels that cross the gap
    col_w = [max((g[n].w for n in spec.nodes if rank[n] == c), default=TILE) for c in range(ncols)]
    gap = [COL_GAP_MIN] * max(0, ncols - 1)
    for e in spec.edges:
        a, b = sorted((rank[e.src], rank[e.dst]))
        if b - a == 1:
            gap[a] = max(gap[a], edge_label_width(e.label, e.step) + 56)
    col_left, x = [], 0.0
    for c in range(ncols):
        col_left.append(x)
        x += col_w[c] + (gap[c] if c < ncols - 1 else 0)
    col_right = [col_left[c] + col_w[c] for c in range(ncols)]
    for n in spec.nodes:
        it = item_of[n]
        g[n].cx = col_left[rank[n]] + col_w[rank[n]] / 2
        g[n].top = it.y + it.offs[n]

    zones = {}
    for it in items:
        if it.group is None:
            continue
        x0 = col_left[it.cols[0]] - ZONE_PAD
        x1 = col_right[it.cols[-1]] + ZONE_PAD
        zones[it.group] = Box(x0, it.y, x1 - x0, it.h)
    lay = Layout(g, zones, col_left, col_right)
    _check_overlaps(spec, lay)
    return lay


def _pack(col_items: list[list[_Item]]) -> None:
    """Push items down until no two in a column overlap (keeps their order)."""
    for _ in range(200):
        moved = False
        for col in col_items:
            for a, b in zip(col, col[1:]):
                need = a.y + a.h + V_GAP
                if b.y < need - 0.01:
                    b.y = need
                    moved = True
        if not moved:
            return


def _relax(items, col_items, nbrs, item_of, anchor, rounds: int = 60) -> None:
    """Pull each item toward its neighbours, then spread overlapping ones apart."""
    for _ in range(rounds):
        for it in items:
            diffs = [anchor(m) - anchor(n) for n in it.nodes for m in nbrs[n] if item_of[m] is not it]
            if diffs:
                it.y += 0.5 * sum(diffs) / len(diffs)
        for _ in range(8):
            for col in col_items:
                for a, b in zip(col, col[1:]):
                    over = a.y + a.h + V_GAP - b.y
                    if over > 0:
                        a.y -= over / 2
                        b.y += over / 2
