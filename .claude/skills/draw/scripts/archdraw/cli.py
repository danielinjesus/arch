"""Command line: python draw.py spec.yaml [-o out] [--formats html,svg,png]."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import draw, icons, load, parse
from .png import svg_to_png
from .spec import SpecError

FORMATS = ("html", "svg", "png")


def gallery_spec():
    names = icons.names()
    per_row = 8
    nodes = {}
    for i, name in enumerate(names):
        aliases = sorted(a for a, n in icons.ALIASES.items() if n == name)
        nodes[name] = {"icon": name, "label": name, "role": ", ".join(aliases[:4]), "at": [i % per_row, i // per_row]}
    return parse({"title": "archdraw icons", "subtitle": f"{len(names)} icons; aliases under each name",
                  "nodes": nodes})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="draw.py", description="Colourful cartoon architecture diagrams.")
    ap.add_argument("spec", nargs="?", help="diagram spec (.yaml or .json)")
    ap.add_argument("-o", "--out", help="output path without extension (default: next to the spec)")
    ap.add_argument("--formats", default="html,svg,png", help="any of html,svg,png (default: all three)")
    ap.add_argument("--scale", type=float, default=2.0, help="PNG pixel scale (default 2)")
    ap.add_argument("--browser", help="Chrome/Edge/Chromium for the PNG (default: found automatically)")
    ap.add_argument("--icons", action="store_true", help="list icon names and aliases")
    ap.add_argument("--gallery", action="store_true", help="draw every icon (use with -o)")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # a Windows console may not take every character
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    if args.icons:
        for name in icons.names():
            aliases = sorted(a for a, n in icons.ALIASES.items() if n == name)
            print(f"{name:10} {', '.join(aliases)}")
        return 0
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    bad = [f for f in formats if f not in FORMATS]
    if bad:
        ap.error(f"unknown format(s): {', '.join(bad)}")

    try:
        if args.gallery:
            spec = gallery_spec()
            base = Path(args.out or "icons")
        elif args.spec:
            spec = load(args.spec)
            base = Path(args.out) if args.out else Path(args.spec).with_suffix("")
        else:
            ap.error("give a spec file, --icons or --gallery")
        d = draw(spec)
    except (SpecError, OSError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2

    base.parent.mkdir(parents=True, exist_ok=True)
    written = []
    if "html" in formats:
        p = base.with_suffix(".html")
        p.write_text(d.html, encoding="utf-8")
        written.append(p)
    if "svg" in formats:
        p = base.with_suffix(".svg")
        p.write_text(d.svg, encoding="utf-8")
        written.append(p)
    if "png" in formats:
        p = base.with_suffix(".png")
        try:
            svg_to_png(d.static_svg, d.width, d.height, p, args.scale, args.browser)
            written.append(p)
        except RuntimeError as e:
            print(f"WARN {e}", file=sys.stderr)
    for w in d.warnings:
        print(f"WARN {w}", file=sys.stderr)
    for p in written:
        print(f"wrote {p}")
    print(f"{len(d.warnings)} warning(s)")
    return 0
