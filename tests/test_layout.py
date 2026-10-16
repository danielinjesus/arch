from pathlib import Path

from archdraw import draw, load, parse
from archdraw import layout as L
from archdraw import route

ROOT = Path(__file__).resolve().parents[1]
TRANSLATOR = ROOT / "examples" / "translator.yaml"


def test_translator_layout_is_clean():
    spec = load(TRANSLATOR)
    lay = L.layout(spec)
    cols = {n: g.col for n, g in lay.nodes.items()}
    assert cols["viewer"] < cols["page"] < cols["tunnel"] < cols["server"] < cols["speech"]
    assert cols["youtube"] == cols["speech"] == cols["agent"] == cols["dubbing"]
    boxes = list(lay.nodes.items())
    for i, (a, ba) in enumerate(boxes):
        for b, bb in boxes[i + 1:]:
            assert ba.box.overlap(bb.box) == 0, (a, b)
    zone = lay.zones["foundry"]
    for n, g in lay.nodes.items():
        inside = zone.overlap(g.box) > 0
        assert inside == (spec.nodes[n].group == "foundry"), n
    assert draw(spec).warnings == []


def test_cycle_and_groups():
    spec = parse({
        "groups": {"cloud": "Cloud", "lab": "Lab"},
        "nodes": {"op": {"icon": "user"}, "chat": {}, "agent": {"group": "cloud"}, "llm": {"group": "cloud"},
                  "mcp": {"group": "lab"}, "arm": {"group": "lab"}, "log": {}},
        "edges": ["op -> chat", "chat <-> agent", "agent <-> llm", "agent -> mcp", "mcp -> arm",
                  "mcp --> log", "agent -> op: done"],
    })
    lay = L.layout(spec)
    assert lay.nodes["op"].col == 0 and lay.nodes["agent"].col == 2  # the loop back to op is ignored
    a, b = lay.zones["cloud"], lay.zones["lab"]
    assert a.overlap(b) == 0
    d = draw(spec)
    assert not [w for w in d.warnings if "runs through" in w]


def test_detour_avoids_nodes():
    # a -> d skips two columns that hold b and c on the same row
    spec = parse({"nodes": {"a": {}, "b": {}, "c": {}, "d": {}},
                  "edges": ["a -> b", "b -> c", "c -> d", "a -> d: skip"]})
    lay = L.layout(spec)
    routes, warnings = route.route_all(spec, lay)
    assert warnings == []
    skip = routes[3]
    assert skip.lane is not None
    for p, _ in route.sample(skip.segs):
        for n in ("b", "c"):
            assert not lay.nodes[n].box.contains(*p)


def test_col_pin():
    spec = parse({"nodes": {"a": {}, "b": {"col": 3}}, "edges": ["a -> b"]})
    assert L.layout(spec).nodes["b"].col == 3


def test_manual_layout_and_overlap_warning():
    spec = parse({"nodes": {"a": {"at": [0, 0]}, "b": {"at": [0, 0.2]}}, "edges": ["a -> b"]})
    lay = L.layout(spec)
    assert any("overlap" in w for w in lay.warnings)


def test_wrap():
    lines = L.wrap("a fairly long role line that will not fit on one line at all", 14.5, 120, 3)
    assert 1 < len(lines) <= 3
    assert lines[-1].endswith("…")
