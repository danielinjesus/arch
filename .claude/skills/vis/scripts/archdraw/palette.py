"""Colours: a bright cartoon palette plus the ink and paper it sits on."""
from __future__ import annotations

import re

INK = "#1E1B2E"
PAPER = "#FFF6E3"
DOTS = "#F3E1BC"
WHITE = "#FFFFFF"

COLORS = {
    "red": "#FF5A5F",
    "orange": "#FF9F1C",
    "yellow": "#FFD23F",
    "lime": "#8FD14F",
    "green": "#2BC48A",
    "teal": "#14B8C4",
    "sky": "#4CB8FF",
    "blue": "#5B6CFF",
    "purple": "#9B5DE5",
    "pink": "#FF6FB5",
    "brown": "#C98A58",
}

# Order used when a node has neither a colour nor an icon with a default colour.
AUTO_ORDER = ["sky", "orange", "pink", "lime", "purple", "yellow", "teal", "red", "blue", "green"]

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def resolve(value: str | None) -> str | None:
    """A palette name or #RRGGBB -> #RRGGBB. None stays None; anything else raises ValueError."""
    if value is None:
        return None
    v = str(value).strip()
    if v.lower() in COLORS:
        return COLORS[v.lower()]
    if _HEX.match(v):
        return v.upper()
    raise ValueError(f"unknown colour {value!r}: use one of {', '.join(COLORS)} or #RRGGBB")


def mix(a: str, b: str, t: float) -> str:
    """Blend colour a toward b by t (0 = a, 1 = b)."""
    ra, ga, ba = (int(a[i:i + 2], 16) for i in (1, 3, 5))
    rb, gb, bb = (int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#{:02X}{:02X}{:02X}".format(
        round(ra + (rb - ra) * t), round(ga + (gb - ga) * t), round(ba + (bb - ba) * t))


def shades(c: str) -> dict[str, str]:
    """The colour slots an icon is drawn with."""
    return {
        "c": c,                    # main
        "d": mix(c, INK, 0.28),    # dark
        "l": mix(c, WHITE, 0.55),  # light
        "k": INK,
        "w": WHITE,
        "y": COLORS["yellow"],
        "r": COLORS["red"],
        "g": COLORS["lime"],
        "s": "#FFD3A8",            # skin
    }


def tile(c: str) -> str:
    return mix(c, WHITE, 0.7)


def zone(c: str) -> str:
    return mix(c, WHITE, 0.86)


def readable_on(c: str) -> str:
    """Ink or white text, whichever reads better on c."""
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return INK if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else WHITE
