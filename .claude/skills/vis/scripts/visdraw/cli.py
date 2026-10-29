"""Command line: python vis.py spec.yaml [-o out] [--formats html,png]. The spec's `kind:` picks the picture."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from archdraw import cli as arch_cli
from archdraw.png import html_to_png

from . import KINDS, build, read
from .common import SpecError


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(prog="vis.py", description=f"Pictures from a short spec. kind: {', '.join(KINDS)}.")
    ap.add_argument("spec", nargs="?", help="spec file (.yaml or .json) with kind: " + "|".join(KINDS))
    ap.add_argument("-o", "--out", help="output path without extension (default: next to the spec)")
    ap.add_argument("--formats", help="sketch: html,svg,png (default all) · other kinds: html,png (default both)")
    ap.add_argument("--scale", type=float, default=2.0, help="PNG pixel scale (default 2)")
    ap.add_argument("--browser", help="Chrome/Edge/Chromium for the PNG (default: found automatically)")
    ap.add_argument("--icons", action="store_true", help="sketch: list icon names and aliases")
    ap.add_argument("--gallery", action="store_true", help="sketch: draw every icon (use with -o)")
    args = ap.parse_args(argv)

    if args.icons or args.gallery:
        return arch_cli.main(argv)
    if not args.spec:
        ap.error("give a spec file")
    try:
        data = read(args.spec)
    except (SpecError, OSError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    kind = str(data.get("kind") or "sketch").strip().lower()
    if kind == "sketch":
        return arch_cli.main(argv)

    formats = [f.strip().lower() for f in (args.formats or "html,png").split(",") if f.strip()]
    bad = [f for f in formats if f not in ("html", "png")]
    if bad:
        ap.error(f"kind {kind} writes html and png only, not {', '.join(bad)}")
    try:
        page = build(data)
    except SpecError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2

    base = Path(args.out) if args.out else Path(args.spec).with_suffix("")
    base.parent.mkdir(parents=True, exist_ok=True)
    written = []
    if "html" in formats:
        p = base.with_suffix(".html")
        p.write_text(page.html, encoding="utf-8")
        written.append(p)
    if "png" in formats:
        p = base.with_suffix(".png")
        try:
            html_to_png(page.html, page.width, page.height, p, args.scale, args.browser)
            written.append(p)
        except RuntimeError as e:
            print(f"WARN {e}", file=sys.stderr)
    for w in page.warnings:
        print(f"WARN {w}", file=sys.stderr)
    for p in written:
        print(f"wrote {p}")
    print(f"{len(page.warnings)} warning(s)")
    return 0
