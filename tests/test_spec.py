import pytest

from archdraw import SpecError, parse


def nodes(*ids):
    return {i: {"label": i.title()} for i in ids}


def test_edge_short_forms():
    spec = parse({"nodes": nodes("a", "b", "c"), "edges": [
        "a -> b",
        {"a -> c": "send"},
        {"b <-> c": {"label": "talk", "step": 2}},
        "c --> a: maybe",
        {"from": "a", "to": "c", "label": "full", "dashed": True},
    ]})
    e = spec.edges
    assert (e[0].src, e[0].dst, e[0].label, e[0].both, e[0].dashed) == ("a", "b", "", False, False)
    assert e[1].label == "send"
    assert e[2].both and e[2].step == 2 and e[2].label == "talk"
    assert e[3].dashed and e[3].label == "maybe"
    assert e[4].dashed and e[4].label == "full"


def test_unknown_node_in_edge():
    with pytest.raises(SpecError, match="no node called 'x'"):
        parse({"nodes": nodes("a"), "edges": ["a -> x"]})


def test_bad_arrow():
    with pytest.raises(SpecError, match="expected 'a -> b'"):
        parse({"nodes": nodes("a", "b"), "edges": ["a => b"]})


def test_icon_from_id_alias_and_unknown():
    spec = parse({"nodes": {"agent": "Agent", "db": {"icon": "sql"}, "x": {"icon": "unicorn"}}})
    assert spec.nodes["agent"].icon == "robot"
    assert spec.nodes["db"].icon == "database"
    assert spec.nodes["x"].icon == "box"
    assert any("unknown icon 'unicorn'" in w for w in spec.warnings)


def test_colours():
    spec = parse({"nodes": {"a": {"color": "pink"}, "b": {"color": "#12ab34"}, "c": {"icon": "video"}}})
    assert spec.nodes["a"].color == "#FF6FB5"
    assert spec.nodes["b"].color == "#12AB34"
    assert spec.nodes["c"].color == "#FF5A5F"  # the icon's own colour
    with pytest.raises(SpecError, match="unknown colour"):
        parse({"nodes": {"a": {"color": "beige"}}})


def test_manual_layout_needs_every_at():
    with pytest.raises(SpecError, match="missing on b"):
        parse({"nodes": {"a": {"at": [0, 0]}, "b": {}}})
    assert parse({"nodes": {"a": {"at": [0, 0]}, "b": {"at": [1, 0.5]}}}).manual


def test_unknown_keys_warn():
    spec = parse({"nodes": {"a": {"lable": "typo"}}, "colour": "x"})
    assert any("'lable'" in w for w in spec.warnings)
    assert any("'colour'" in w for w in spec.warnings)


def test_group_without_definition():
    spec = parse({"nodes": {"a": {"group": "home"}}})
    assert spec.groups["home"].label == "home"
    assert spec.warnings
