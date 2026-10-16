import re
import struct
from pathlib import Path

import pytest

from archdraw import cli, icons
from archdraw.png import find_browser

ROOT = Path(__file__).resolve().parents[1]


def test_writes_html_and_svg(tmp_path):
    out = tmp_path / "t"
    assert cli.main([str(ROOT / "examples" / "translator.yaml"), "-o", str(out), "--formats", "html,svg"]) == 0
    assert (tmp_path / "t.html").exists() and (tmp_path / "t.svg").exists()


def test_bad_spec_exit_code(tmp_path, capsys):
    p = tmp_path / "bad.yaml"
    p.write_text("nodes: {a: {}}\nedges: [a -> nope]\n", encoding="utf-8")
    assert cli.main([str(p), "--formats", "svg"]) == 2
    assert "no node called 'nope'" in capsys.readouterr().err


def test_icons_list(capsys):
    assert cli.main(["--icons"]) == 0
    assert "house" in capsys.readouterr().out


@pytest.mark.skipif(not find_browser(), reason="no Chrome/Edge/Chromium")
def test_png_size(tmp_path):
    out = tmp_path / "t"
    assert cli.main([str(ROOT / "examples" / "translator.yaml"), "-o", str(out), "--formats", "svg,png",
                     "--scale", "1"]) == 0
    svg = (tmp_path / "t.svg").read_text(encoding="utf-8")
    w, h = (float(v) for v in re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups())
    data = (tmp_path / "t.png").read_bytes()
    pw, ph = struct.unpack(">II", data[16:24])
    assert (pw, ph) == (round(w), round(h))


def test_reference_lists_every_icon():
    ref = (ROOT / ".claude" / "skills" / "draw" / "reference.md").read_text(encoding="utf-8")
    section = ref.split("## Icons", 1)[1].split("##", 1)[0]
    table = {}
    for m in re.finditer(r"^\| (\w+) \| ([^|]*)\|", section, re.M):
        if m.group(1) != "Icon":
            table[m.group(1)] = sorted(a.strip() for a in m.group(2).split(",") if a.strip())
    real = {n: sorted(a for a, t in icons.ALIASES.items() if t == n) for n in icons.names()}
    assert table == real
