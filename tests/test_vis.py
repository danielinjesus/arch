import json
import re

import pytest

from visdraw import build, cli
from visdraw.common import SpecError

from conftest import ROOT

EX = ROOT / "examples"


def payload(html):
    return json.loads(re.search(r"const D = (\{.*?\});\n", html, re.S).group(1))


@pytest.mark.parametrize("name", ["handbook.yaml", "kinds-mindmap.yaml", "modules-graph.yaml"])
def test_examples_render_html(tmp_path, name):
    out = tmp_path / "x"
    assert cli.main([str(EX / name), "-o", str(out), "--formats", "html"]) == 0
    html = (tmp_path / "x.html").read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>") and "const D = " in html
    assert "http" not in re.sub(r'href="https?://[^"]*"', "", html).split("<script>")[0]  # no CDN in the head


def test_kind_arch_goes_to_archdraw(tmp_path):
    out = tmp_path / "a"
    assert cli.main([str(EX / "translator.yaml"), "-o", str(out), "--formats", "svg"]) == 0
    assert (tmp_path / "a.svg").exists()


def test_unknown_kind(tmp_path, capsys):
    p = tmp_path / "k.yaml"
    p.write_text("kind: pie\n", encoding="utf-8")
    assert cli.main([str(p), "--formats", "html"]) == 2
    assert "kind 'pie'" in capsys.readouterr().err


def test_svg_not_for_html_kinds(tmp_path):
    with pytest.raises(SystemExit):
        cli.main([str(EX / "handbook.yaml"), "--formats", "svg"])


XREF = {"kind": "xref", "categories": [{"group": "G", "items": [{"id": "a", "label": "A"}, "B"]}],
        "tags": [{"group": "T", "items": [{"id": "t1", "name": "One"}, "Two"]}],
        "links": [{"category": "a", "tag": "t1", "notes": ["x", "y"]}]}


def test_xref_payload_and_warnings():
    page = build(XREF)
    d = payload(page.html)
    assert [c["label"] for c in d["C"]] == ["A", "B"]
    assert d["L"] == {"0,0": {"n": 2, "notes": ["x", "y"]}}
    assert any("Two" in w for w in page.warnings)


def test_xref_bad_link():
    bad = {**XREF, "links": [{"category": "a", "tag": "nope"}]}
    with pytest.raises(SpecError, match="no tag called 'nope'"):
        build(bad)


def test_mindmap_short_forms_and_branch_colours():
    page = build({"kind": "mindmap", "open": 1, "root": {"label": "R", "children": [{"Left": ["l1", "l2"]}, "Right"]}})
    n = payload(page.html)["N"]
    assert [x["label"] for x in n] == ["R", "Left", "l1", "l2", "Right"]
    assert n[2]["c"] == n[1]["c"] != n[4]["c"]
    assert n[0]["open"] and not n[1]["open"]


def test_mindmap_needs_root():
    with pytest.raises(SpecError, match="root"):
        build({"kind": "mindmap"})


def test_graph_edges():
    page = build({"kind": "graph", "nodes": {"a": "A", "b": "B", "c": "C"},
                  "edges": ["a -> b: calls", "b <--> c", "a -- c"]})
    e = payload(page.html)["E"]
    assert e[0] == {"s": 0, "t": 1, "label": "calls", "w": 1, "both": False, "dash": False, "dir": True}
    assert e[1]["both"] and e[1]["dash"]
    assert e[2]["dir"] is False


def test_graph_unknown_node():
    with pytest.raises(SpecError, match="no node called 'z'"):
        build({"kind": "graph", "nodes": {"a": "A"}, "edges": ["a -> z"]})


def test_script_close_tag_is_escaped():
    page = build({**XREF, "title": "</script><b>x"})
    assert "</script><b>" not in page.html.split("<script>", 1)[1].rsplit("</script>", 1)[0]
