import re
import xml.etree.ElementTree as ET

from archdraw import draw, fonts, icons, parse, render

SVG = "{http://www.w3.org/2000/svg}"


def small():
    return parse({
        "title": "작은 그림", "subtitle": "a → b",
        "nodes": {"a": {"label": "사용자", "icon": "user", "tech": "Chrome → Edge", "role": "누른다",
                        "doc": "https://example.com/a"},
                  "b": {"label": "서버", "icon": "house"}},
        "edges": [{"a -> b": {"label": "요청 → 응답", "step": 1}}],
    })


def test_svg_is_valid_xml_with_links_only_when_interactive():
    d = draw(small())
    live = ET.fromstring(d.svg)
    still = ET.fromstring(d.static_svg)
    assert len(live.findall(f".//{SVG}a")) == 1
    assert live.find(f".//{SVG}a").get("href") == "https://example.com/a"
    assert still.findall(f".//{SVG}a") == []
    assert 'class="flow"' in d.svg and 'class="flow"' not in d.static_svg


def test_html_page():
    d = draw(small())
    assert d.html.startswith("<!doctype html>")
    assert "<title>작은 그림</title>" in d.html
    assert 'lang="ko"' in d.html
    assert "아이콘을 누르면" in d.html  # hint shows because a node has a doc


def test_arrows_are_drawn_not_typed():
    d = draw(small())
    texts = re.findall(r"<text[^>]*>([^<]*)</text>", d.static_svg)
    assert not any("→" in t for t in texts)
    assert "요청" in texts and "응답" in texts


def test_font_is_embedded_and_subset():
    css = fonts.font_face("가나다abc")
    assert css.startswith("@font-face{font-family:ArchJua")
    assert len(css) < 60_000
    assert fonts.text_width("가나다", 20) > fonts.text_width("abc", 20) > 0


def test_every_icon_renders():
    for name in icons.names():
        frag = icons.markup(name, "#4CB8FF")
        ET.fromstring(f'<g xmlns="http://www.w3.org/2000/svg">{frag}</g>')
        assert "{" not in frag, name


def test_chars_used_covers_text():
    chars = render.chars_used(small())
    for s in ("작은 그림", "사용자", "누른다", "요청"):
        assert all(c in chars for c in s)
