"""visdraw: one command for several kinds of picture.

sketch   cartoon sketch diagram (HTML, SVG, PNG)
xref     categories x tags cross-reference: matrix, relation graph, tree, tag list (HTML)
mindmap  collapsible tree, left to right (HTML)
graph    force-laid network with drag, zoom, search (HTML)
"""
from __future__ import annotations

from . import graph, mindmap, xref
from .common import Page, SpecError, read

BUILDERS = {"xref": xref.build, "mindmap": mindmap.build, "graph": graph.build}
KINDS = ("sketch", *BUILDERS)

__all__ = ["BUILDERS", "KINDS", "Page", "SpecError", "build", "read"]


def build(data: dict) -> Page:
    kind = str(data.get("kind") or "sketch").strip().lower()
    if kind not in BUILDERS:
        raise SpecError(f"kind {kind!r}: use one of {', '.join(KINDS)}")
    return BUILDERS[kind](data)
