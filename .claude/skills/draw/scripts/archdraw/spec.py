"""Read a diagram spec (YAML or JSON) into plain objects, with friendly errors."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import icons, palette


class SpecError(ValueError):
    pass


@dataclass
class Node:
    id: str
    label: str
    icon: str
    color: str
    tech: str = ""
    role: str = ""
    doc: str = ""
    group: str | None = None
    col: int | None = None
    at: tuple[float, float] | None = None


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    both: bool = False
    dashed: bool = False
    step: int | str | None = None
    color: str | None = None


@dataclass
class Group:
    id: str
    label: str
    color: str


@dataclass
class Spec:
    title: str = ""
    subtitle: str = ""
    note: str = ""
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    groups: dict[str, Group] = field(default_factory=dict)
    manual: bool = False
    warnings: list[str] = field(default_factory=list)


_ID = r"[\w.]+"
_ARROW = re.compile(rf"^\s*({_ID})\s*(<?--?>)\s*({_ID})\s*(?::\s*(.*?))?\s*$")
_TOP = {"title", "subtitle", "note", "nodes", "edges", "groups", "layout"}
_NODE = {"label", "icon", "color", "tech", "role", "doc", "group", "col", "at"}
_EDGE = {"from", "to", "label", "both", "dashed", "step", "color"}
_GROUP = {"label", "color"}


def load(path: str | Path) -> Spec:
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as e:
            raise SpecError("PyYAML is needed for .yaml specs: pip install pyyaml (or write the spec as .json)") from e
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise SpecError(f"{path.name}: not valid YAML ({e}). Quote labels that contain ': '.") from e
    return parse(data)


def _str(v) -> str:
    return "" if v is None else str(v).strip()


def parse(data) -> Spec:
    if not isinstance(data, dict):
        raise SpecError("the spec must be a mapping with at least `nodes:`")
    spec = Spec(title=_str(data.get("title")), subtitle=_str(data.get("subtitle")), note=_str(data.get("note")))
    for k in data:
        if k not in _TOP:
            spec.warnings.append(f"unknown top-level key {k!r} ignored")
    layout = _str(data.get("layout") or "auto").lower()
    if layout not in ("auto", "manual"):
        raise SpecError("layout must be auto or manual")

    auto_i = 0
    for gid, g in (data.get("groups") or {}).items():
        g = {"label": g} if isinstance(g, str) else (g or {})
        _unknown(spec, f"group {gid}", g, _GROUP)
        color = _color(g.get("color"), f"group {gid}") or palette.COLORS[palette.AUTO_ORDER[auto_i % len(palette.AUTO_ORDER)]]
        auto_i += 1
        spec.groups[str(gid)] = Group(str(gid), _str(g.get("label")) or str(gid), color)

    nodes = data.get("nodes")
    if not isinstance(nodes, dict) or not nodes:
        raise SpecError("`nodes:` must map ids to nodes, e.g. nodes: {server: {label: Server, icon: house}}")
    auto_i = 0
    for nid, n in nodes.items():
        nid = str(nid)
        if not re.fullmatch(_ID, nid):
            raise SpecError(f"node id {nid!r}: use letters, digits, _ or . only")
        n = {"label": n} if isinstance(n, str) else (n or {})
        _unknown(spec, f"node {nid}", n, _NODE)
        icon = icons.resolve(n.get("icon") or nid)
        if icon is None:
            if n.get("icon"):
                spec.warnings.append(f"node {nid}: unknown icon {n.get('icon')!r}, drawing a box (see --icons)")
            icon = icons.FALLBACK
        color = _color(n.get("color"), f"node {nid}")
        if color is None:
            if n.get("icon") or icons.resolve(nid):
                color = icons.default_color(icon)
            else:
                color = palette.COLORS[palette.AUTO_ORDER[auto_i % len(palette.AUTO_ORDER)]]
                auto_i += 1
        group = n.get("group")
        if group is not None and str(group) not in spec.groups:
            spec.groups[str(group)] = Group(str(group), str(group), palette.COLORS["sky"])
            spec.warnings.append(f"node {nid}: group {group!r} is not under groups:, using its id as the label")
        col = n.get("col")
        if col is not None and (not isinstance(col, int) or col < 0):
            raise SpecError(f"node {nid}: col must be a whole number >= 0")
        at = n.get("at")
        if at is not None:
            if not (isinstance(at, (list, tuple)) and len(at) == 2 and all(isinstance(v, (int, float)) for v in at)):
                raise SpecError(f"node {nid}: at must be [col, row]")
            at = (float(at[0]), float(at[1]))
        spec.nodes[nid] = Node(nid, _str(n.get("label")) or nid, icon, color, _str(n.get("tech")),
                               _str(n.get("role")), _str(n.get("doc")), str(group) if group is not None else None,
                               col, at)

    with_at = [n.id for n in spec.nodes.values() if n.at is not None]
    if layout == "manual" or with_at:
        missing = [n.id for n in spec.nodes.values() if n.at is None]
        if missing:
            raise SpecError(f"manual layout needs `at: [col, row]` on every node; missing on {', '.join(missing)}")
        spec.manual = True

    for i, e in enumerate(data.get("edges") or []):
        spec.edges.append(_edge(spec, e, i))
    for e in spec.edges:
        for end in (e.src, e.dst):
            if end not in spec.nodes:
                raise SpecError(f"edge {e.src} -> {e.dst}: no node called {end!r}")
        if e.src == e.dst:
            raise SpecError(f"edge {e.src} -> {e.dst}: an edge needs two different nodes")
    for n in spec.nodes.values():
        if n.doc and not re.match(r"^https?://", n.doc):
            spec.warnings.append(f"node {n.id}: doc should be an http(s) link")
    return spec


def _edge(spec: Spec, e, i: int) -> Edge:
    opts: dict = {}
    if isinstance(e, str):
        head, label = e, None
    elif isinstance(e, dict) and "from" not in e and len(e) == 1:
        head, val = next(iter(e.items()))
        if isinstance(val, dict):
            opts, label = val, val.get("label")
        else:
            label = val
    elif isinstance(e, dict):
        opts = e
        _unknown(spec, f"edge #{i + 1}", e, _EDGE)
        if "to" not in e:
            raise SpecError(f"edge #{i + 1}: needs from and to")
        return Edge(str(e["from"]), str(e["to"]), _str(e.get("label")), bool(e.get("both")), bool(e.get("dashed")),
                    e.get("step"), _color(e.get("color"), f"edge #{i + 1}"))
    else:
        raise SpecError(f"edge #{i + 1}: write it as 'a -> b: label' or {{from: a, to: b, label: ...}}")
    m = _ARROW.match(str(head))
    if not m:
        raise SpecError(f"edge #{i + 1} {head!r}: expected 'a -> b', 'a <-> b', 'a --> b' (dashed) or 'a <--> b'")
    src, arrow, dst, tail = m.groups()
    if label is None:
        label = tail
    _unknown(spec, f"edge {src} -> {dst}", opts, _EDGE - {"from", "to"})
    return Edge(src, dst, _str(label), arrow.startswith("<") or bool(opts.get("both")),
                "--" in arrow or bool(opts.get("dashed")), opts.get("step"),
                _color(opts.get("color"), f"edge {src} -> {dst}"))


def _color(v, where: str) -> str | None:
    try:
        return palette.resolve(v)
    except ValueError as e:
        raise SpecError(f"{where}: {e}") from None


def _unknown(spec: Spec, where: str, d: dict, known: set[str]) -> None:
    if not isinstance(d, dict):
        raise SpecError(f"{where}: expected a mapping")
    for k in d:
        if k not in known:
            spec.warnings.append(f"{where}: unknown key {k!r} ignored (known: {', '.join(sorted(known))})")
