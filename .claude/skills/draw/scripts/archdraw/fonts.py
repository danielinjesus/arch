"""Text widths and the embedded font (BM Jua, SIL OFL 1.1).

The font is subset to the characters a diagram uses and embedded as base64 WOFF2, so the SVG,
the HTML and the PNG look the same on any machine. Without fontTools (+ brotli) the diagram still
renders: widths are estimated and the viewer's own fonts are used.
"""
from __future__ import annotations

import base64
import io
import unicodedata
from functools import lru_cache
from pathlib import Path

FONT_PATH = Path(__file__).parent / "fonts" / "Jua.woff2"
FAMILY = "ArchJua"
STACK = f"{FAMILY}, 'Jua', 'Comic Sans MS', 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif"


@lru_cache(maxsize=1)
def _font():
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(str(FONT_PATH))
        font.getBestCmap()
        return font
    except Exception:  # fontTools or brotli missing, or the file is gone
        return None


@lru_cache(maxsize=1)
def _metrics():
    font = _font()
    if font is None:
        return None
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upem = font["head"].unitsPerEm
    return {cp: hmtx[g][0] / upem for cp, g in cmap.items()}


def _estimate(ch: str) -> float:
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 1.0
    if ch == " ":
        return 0.3
    return 0.58


ARROW = "→"
ARROW_EM = 1.15  # an arrow drawn between words, with its own spacing


def split_arrows(text: str) -> list[str]:
    """'A → B' -> ['A', 'B']: the renderer draws the arrows (the font has none)."""
    return [p.strip() for p in text.split(ARROW)]


def _plain_width(text: str) -> float:
    m = _metrics()
    total = 0.0
    for ch in text:
        w = m.get(ord(ch)) if m else None
        total += w if w is not None else _estimate(ch)
    return total


def text_width(text: str, size: float) -> float:
    if ARROW not in text:
        return _plain_width(text) * size
    pieces = split_arrows(text)
    return (sum(_plain_width(p) for p in pieces) + ARROW_EM * (len(pieces) - 1)) * size


def embedded() -> bool:
    return _font() is not None


def font_face(chars: str) -> str:
    """@font-face rule with the font subset to chars, or "" when fontTools is unavailable."""
    return _font_face("".join(sorted(set(chars))))


@lru_cache(maxsize=8)
def _font_face(chars: str) -> str:
    font = _font()
    if font is None:
        return ""
    try:
        from fontTools import subset
        sub = subset.Subsetter(subset.Options(flavor="woff2", layout_features=["*"], name_IDs=["*"]))
        sub.populate(text=chars)
        from fontTools.ttLib import TTFont
        f = TTFont(str(FONT_PATH))
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
    except Exception:
        return ""
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return (f"@font-face{{font-family:{FAMILY};src:url(data:font/woff2;base64,{data}) format('woff2');"
            "font-weight:normal;font-style:normal}")
