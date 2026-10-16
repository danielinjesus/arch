"""archdraw: colourful cartoon architecture diagrams from a small YAML spec."""
from __future__ import annotations

from dataclasses import dataclass

from . import layout as _layout
from . import render, route
from .spec import Spec, SpecError, load, parse

__all__ = ["Drawing", "draw", "load", "parse", "Spec", "SpecError"]


@dataclass
class Drawing:
    spec: Spec
    svg: str            # interactive: links, hover, flowing arrows
    static_svg: str     # for the PNG
    html: str
    width: float
    height: float
    warnings: list[str]


def draw(spec: Spec) -> Drawing:
    lay = _layout.layout(spec)
    routes, route_warnings = route.route_all(spec, lay)
    live = render.svg(spec, lay, routes, interactive=True)
    still = render.svg(spec, lay, routes, interactive=False)
    w, h = (float(v) for v in _size(still))
    return Drawing(spec, live, still, render.page(spec, live), w, h,
                   spec.warnings + lay.warnings + route_warnings)


def _size(svg_text: str) -> tuple[str, str]:
    import re
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', svg_text)
    return m.group(1), m.group(2)
