"""Cartoon icons drawn in a 100x100 box.

Each icon is SVG markup with colour slots: {c} main, {d} dark, {l} light, {k} ink, {w} white,
{y} yellow, {r} red, {g} lime, {s} skin. The caller wraps it in a group that strokes with ink,
so shapes only set their fill (or stroke="none").
"""
from __future__ import annotations

import math

from . import palette


def _gear(cx: float, cy: float, r_out: float, r_in: float, teeth: int) -> str:
    pts = []
    step = 2 * math.pi / teeth
    for i in range(teeth):
        a = i * step
        for da, r in ((-0.30, r_in), (-0.17, r_out), (0.17, r_out), (0.30, r_in)):
            pts.append((cx + r * math.cos(a + da * step * 1.6), cy + r * math.sin(a + da * step * 1.6)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def _person(dx: float, dy: float, s: float, body: str, hair: str) -> str:
    return (
        f'<g transform="translate({dx} {dy}) scale({s})">'
        f'<path d="M18 92 C18 70 32 60 50 60 C68 60 82 70 82 92 Z" fill="{body}"/>'
        '<circle cx="50" cy="36" r="20" fill="{s}"/>'
        f'<path d="M30 35 C29 20 40 13 51 13 C63 14 71 22 70 35 C62 31 53 27 45 22 C41 28 36 32 30 35 Z" fill="{hair}"/>'
        '<circle cx="43" cy="39" r="2.6" fill="{k}" stroke="none"/>'
        '<circle cx="57" cy="39" r="2.6" fill="{k}" stroke="none"/>'
        '<path d="M44 46 Q50 51 56 46" fill="none" stroke-width="3"/>'
        '<circle cx="37.5" cy="45" r="3.2" fill="{r}" opacity=".35" stroke="none"/>'
        '<circle cx="62.5" cy="45" r="3.2" fill="{r}" opacity=".35" stroke="none"/>'
        "</g>"
    )


_ICONS: dict[str, tuple[str, str]] = {
    # name: (default colour, markup)
    "house": ("orange", """
<rect x="64" y="16" width="11" height="22" rx="2" fill="{d}"/>
<rect x="20" y="44" width="60" height="44" rx="3" fill="#FFF1D0"/>
<path d="M8 50 L50 13 L92 50 Z" fill="{c}"/>
<path d="M42 88 V68 a8 8 0 0 1 16 0 V88 Z" fill="{d}"/>
<rect x="26" y="57" width="12" height="12" rx="2" fill="{y}"/>
<rect x="62" y="57" width="12" height="12" rx="2" fill="{y}"/>
<path d="M22 38 L50 20" fill="none" stroke="{w}" stroke-width="3" opacity=".7"/>"""),
    "server": ("blue", """
<rect x="20" y="10" width="60" height="80" rx="9" fill="{c}"/>
<rect x="28" y="19" width="44" height="17" rx="4" fill="{w}"/>
<rect x="28" y="42" width="44" height="17" rx="4" fill="{w}"/>
<rect x="28" y="65" width="44" height="17" rx="4" fill="{w}"/>
<circle cx="36" cy="27.5" r="3.4" fill="{g}" stroke-width="2"/>
<circle cx="36" cy="50.5" r="3.4" fill="{y}" stroke-width="2"/>
<circle cx="36" cy="73.5" r="3.4" fill="{g}" stroke-width="2"/>
<path d="M46 27.5 H64 M46 50.5 H64 M46 73.5 H64" fill="none" stroke-width="3"/>"""),
    "browser": ("sky", """
<rect x="8" y="16" width="84" height="68" rx="9" fill="{w}"/>
<path d="M8 25 a9 9 0 0 1 9 -9 h66 a9 9 0 0 1 9 9 v9 h-84 Z" fill="{c}"/>
<circle cx="18" cy="25" r="3" fill="{r}" stroke-width="2"/>
<circle cx="28" cy="25" r="3" fill="{y}" stroke-width="2"/>
<circle cx="38" cy="25" r="3" fill="{g}" stroke-width="2"/>
<rect x="18" y="43" width="36" height="8" rx="4" fill="{l}" stroke="none"/>
<rect x="18" y="57" width="46" height="7" rx="3.5" fill="{l}" stroke="none"/>
<rect x="18" y="70" width="28" height="7" rx="3.5" fill="{l}" stroke="none"/>
<path d="M66 48 L66 78 L72.5 72 L77.5 83 L83 80.5 L78 70 L86.5 69.5 Z" fill="{w}" stroke-width="3.5"/>"""),
    "user": ("pink", _person(0, 0, 1, "{c}", "{d}")),
    "users": ("pink", _person(26, 4, 0.78, "{l}", "{d}") + _person(-10, 8, 0.86, "{c}", "{k}")),
    "phone": ("purple", """
<rect x="27" y="7" width="46" height="86" rx="10" fill="{c}"/>
<rect x="33" y="17" width="34" height="60" rx="4" fill="{w}"/>
<rect x="44" y="11" width="12" height="2.4" rx="1.2" fill="{k}" stroke="none"/>
<circle cx="50" cy="85" r="3.6" fill="{w}" stroke-width="2.5"/>
<path d="M38 28 h20 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-12 l-6 5 v-5 h-2 a4 4 0 0 1 -4 -4 v-8 a4 4 0 0 1 4 -4 Z" fill="{l}" stroke-width="2.5"/>
<rect x="38" y="56" width="24" height="5" rx="2.5" fill="{l}" stroke="none"/>
<rect x="38" y="65" width="16" height="5" rx="2.5" fill="{l}" stroke="none"/>"""),
    "cloud": ("sky", """
<path d="M28 78 C14 78 8 68 10 59 C12 50 20 46 27 47 C28 33 40 24 53 26 C64 27 71 35 73 44 C84 43 92 51 91 61 C90 71 82 78 72 78 Z" fill="{l}"/>
<path d="M30 54 C31 44 40 37 50 37" fill="none" stroke="{w}" stroke-width="5"/>"""),
    "globe": ("teal", """
<circle cx="50" cy="50" r="38" fill="{l}"/>
<path d="M28 28 C37 31 35 39 44 41 C51 43 48 51 42 55 C36 59 27 55 20 51 C17 41 21 33 28 28 Z" fill="{c}" stroke-width="3"/>
<path d="M60 58 C67 54 77 58 82 63 C78 74 70 82 61 85 C58 76 54 64 60 58 Z" fill="{c}" stroke-width="3"/>
<path d="M58 17 C68 19 77 26 82 35 C72 38 63 33 58 17 Z" fill="{c}" stroke-width="3"/>
<circle cx="50" cy="50" r="38" fill="none"/>"""),
    "database": ("blue", """
<path d="M18 24 V76 A32 10 0 0 0 82 76 V24 Z" fill="{c}"/>
<path d="M18 42 A32 10 0 0 0 82 42 M18 59 A32 10 0 0 0 82 59" fill="none"/>
<ellipse cx="50" cy="24" rx="32" ry="10" fill="{l}"/>
<path d="M27 50 V54 M27 67 V71" fill="none" stroke="{w}" stroke-width="5" opacity=".75"/>"""),
    "folder": ("yellow", """
<path d="M10 28 a6 6 0 0 1 6 -6 h22 l8 8 h38 a6 6 0 0 1 6 6 v44 a6 6 0 0 1 -6 6 h-68 a6 6 0 0 1 -6 -6 Z" fill="{d}"/>
<rect x="20" y="31" width="58" height="30" rx="3" fill="{w}"/>
<path d="M10 45 h80 v33 a6 6 0 0 1 -6 6 h-68 a6 6 0 0 1 -6 -6 Z" fill="{c}"/>"""),
    "document": ("sky", """
<path d="M24 8 H62 L80 26 V88 a4 4 0 0 1 -4 4 H24 a4 4 0 0 1 -4 -4 V12 a4 4 0 0 1 4 -4 Z" fill="{w}"/>
<path d="M62 8 V26 H80" fill="{l}"/>
<rect x="30" y="40" width="40" height="6" rx="3" fill="{c}" stroke="none"/>
<rect x="30" y="53" width="40" height="6" rx="3" fill="{c}" stroke="none"/>
<rect x="30" y="66" width="28" height="6" rx="3" fill="{c}" stroke="none"/>
<rect x="30" y="79" width="34" height="6" rx="3" fill="{l}" stroke="none"/>"""),
    "robot": ("purple", """
<path d="M50 22 V13" fill="none"/>
<circle cx="50" cy="10" r="5.5" fill="{y}"/>
<rect x="9" y="40" width="11" height="20" rx="4" fill="{d}"/>
<rect x="80" y="40" width="11" height="20" rx="4" fill="{d}"/>
<path d="M33 76 h34 v7 a7 7 0 0 1 -7 7 h-20 a7 7 0 0 1 -7 -7 Z" fill="{d}"/>
<rect x="18" y="22" width="64" height="55" rx="17" fill="{c}"/>
<rect x="27" y="33" width="46" height="31" rx="11" fill="{w}"/>
<circle cx="40" cy="47" r="5.5" fill="{k}" stroke="none"/>
<circle cx="60" cy="47" r="5.5" fill="{k}" stroke="none"/>
<circle cx="41.8" cy="45.2" r="1.8" fill="{w}" stroke="none"/>
<circle cx="61.8" cy="45.2" r="1.8" fill="{w}" stroke="none"/>
<path d="M44 56 Q50 60.5 56 56" fill="none" stroke-width="3"/>"""),
    "sparkle": ("purple", """
<path d="M44 8 C47 33 54 40 79 43 C54 46 47 53 44 78 C41 53 34 46 9 43 C34 40 41 33 44 8 Z" fill="{c}"/>
<path d="M76 56 C77 67 80 70 91 71 C80 72 77 75 76 86 C75 75 72 72 61 71 C72 70 75 67 76 56 Z" fill="{y}" stroke-width="3"/>
<circle cx="79" cy="20" r="5" fill="{y}" stroke-width="3"/>
<path d="M36 34 C38 30 40 28 42 27" fill="none" stroke="{w}" stroke-width="4"/>"""),
    "mic": ("sky", """
<path d="M27 46 C27 69 73 69 73 46" fill="none" stroke-width="5"/>
<path d="M50 66 V82" fill="none" stroke-width="5"/>
<path d="M35 86 H65" fill="none" stroke-width="6"/>
<rect x="34" y="9" width="32" height="51" rx="16" fill="{c}"/>
<path d="M40 27 H60 M40 36 H60 M40 45 H60" fill="none" stroke-width="3"/>
<path d="M41 17 V20" fill="none" stroke="{w}" stroke-width="4"/>"""),
    "speaker": ("green", """
<path d="M14 37 H30 L53 19 V81 L30 63 H14 a4 4 0 0 1 -4 -4 V41 a4 4 0 0 1 4 -4 Z" fill="{c}"/>
<path d="M65 37 C72 43 72 57 65 63" fill="none" stroke-width="5"/>
<path d="M75 27 C87 39 87 61 75 73" fill="none" stroke-width="5"/>
<path d="M17 45 V48" fill="none" stroke="{w}" stroke-width="4"/>"""),
    "video": ("red", """
<rect x="8" y="20" width="84" height="60" rx="18" fill="{c}"/>
<path d="M42 36 L64 50 L42 64 Z" fill="{w}" stroke-width="3.5"/>
<path d="M17 37 C17 30 21 28 28 28" fill="none" stroke="{w}" stroke-width="4" opacity=".7"/>"""),
    "tunnel": ("orange", """
<path d="M5 86 C9 50 29 20 50 20 C71 20 91 50 95 86 Z" fill="{c}"/>
<path d="M26 86 V62 C26 47 37 38 50 38 C63 38 74 47 74 62 V86" fill="none" stroke="{w}" stroke-width="3" stroke-dasharray="7 5"/>
<path d="M32 86 V63 C32 52 40 45 50 45 C60 45 68 52 68 63 V86 Z" fill="{k}"/>
<ellipse cx="50" cy="72" rx="9" ry="11" fill="{y}" stroke="none"/>
<path d="M3 86 H97" fill="none"/>"""),
    "lock": ("yellow", """
<path d="M32 46 V32 C32 20 41 14 50 14 C59 14 68 20 68 32 V46" fill="none" stroke-width="12"/>
<path d="M32 46 V32 C32 20 41 14 50 14 C59 14 68 20 68 32 V46" fill="none" stroke="{w}" stroke-width="5"/>
<rect x="19" y="42" width="62" height="46" rx="10" fill="{c}"/>
<circle cx="50" cy="60" r="6" fill="{k}" stroke="none"/>
<path d="M47 62 L45 76 H55 L53 62 Z" fill="{k}" stroke="none"/>"""),
    "key": ("yellow", """
<path d="M46 44 H88 V56 H81 V65 H71 V56 H46 Z" fill="{c}"/>
<circle cx="31" cy="50" r="19" fill="{c}"/>
<circle cx="27" cy="50" r="6.5" fill="{w}"/>"""),
    "gear": ("teal", f"""
<path d="{_gear(50, 50, 42, 31, 8)}" fill="{{c}}"/>
<circle cx="50" cy="50" r="13" fill="{{w}}"/>"""),
    "bolt": ("orange", """
<circle cx="50" cy="50" r="41" fill="{c}"/>
<path d="M56 13 L29 55 H48 L42 87 L71 43 H52 Z" fill="{y}"/>"""),
    "queue": ("lime", """
<rect x="27" y="14" width="46" height="22" rx="6" fill="{w}"/>
<rect x="20" y="31" width="60" height="25" rx="6" fill="{l}"/>
<rect x="13" y="51" width="74" height="33" rx="7" fill="{c}"/>
<path d="M14 55 L50 72 L86 55" fill="none"/>"""),
    "chat": ("green", """
<path d="M14 20 h72 a8 8 0 0 1 8 8 v36 a8 8 0 0 1 -8 8 h-40 l-16 14 v-14 h-16 a8 8 0 0 1 -8 -8 v-36 a8 8 0 0 1 8 -8 Z" fill="{c}"/>
<circle cx="31" cy="46" r="5.5" fill="{w}" stroke-width="2.5"/>
<circle cx="50" cy="46" r="5.5" fill="{w}" stroke-width="2.5"/>
<circle cx="69" cy="46" r="5.5" fill="{w}" stroke-width="2.5"/>"""),
    "translate": ("blue", """
<path d="M16 8 h38 a9 9 0 0 1 9 9 v26 a9 9 0 0 1 -9 9 h-24 l-10 10 v-10 h-4 a9 9 0 0 1 -9 -9 v-26 a9 9 0 0 1 9 -9 Z" fill="{c}"/>
<text x="35" y="41" text-anchor="middle" font-size="30" fill="{w}" stroke="none" font-family="ArchJua, sans-serif">A</text>
<path d="M46 42 h38 a9 9 0 0 1 9 9 v26 a9 9 0 0 1 -9 9 h-4 v10 l-10 -10 h-24 a9 9 0 0 1 -9 -9 v-26 a9 9 0 0 1 9 -9 Z" fill="{y}"/>
<text x="65" y="76" text-anchor="middle" font-size="28" fill="{k}" stroke="none" font-family="ArchJua, sans-serif">가</text>"""),
    "search": ("teal", """
<path d="M61 61 L85 85" fill="none" stroke-width="15"/>
<path d="M61 61 L85 85" fill="none" stroke="{d}" stroke-width="7"/>
<circle cx="42" cy="42" r="27" fill="{l}" stroke-width="5"/>
<path d="M28 37 C30 30 34 26 41 25" fill="none" stroke="{w}" stroke-width="5"/>"""),
    "chart": ("purple", """
<path d="M50 76 V87 M35 89 H65" fill="none" stroke-width="5"/>
<rect x="9" y="13" width="82" height="63" rx="8" fill="{w}"/>
<rect x="21" y="47" width="13" height="19" rx="2" fill="{y}" stroke-width="3"/>
<rect x="43.5" y="35" width="13" height="31" rx="2" fill="{c}" stroke-width="3"/>
<rect x="66" y="24" width="13" height="42" rx="2" fill="{g}" stroke-width="3"/>"""),
    "git": ("orange", """
<path d="M33 24 V76 M33 62 C33 46 67 50 67 33" fill="none" stroke-width="7"/>
<circle cx="33" cy="22" r="10" fill="{c}"/>
<circle cx="33" cy="78" r="10" fill="{c}"/>
<circle cx="67" cy="30" r="10" fill="{y}"/>"""),
    "clock": ("red", """
<path d="M22 22 L31 13 M78 22 L69 13" fill="none" stroke-width="7"/>
<circle cx="50" cy="54" r="40" fill="{c}"/>
<circle cx="50" cy="54" r="30" fill="{w}"/>
<path d="M50 54 V34 M50 54 L64 62" fill="none" stroke-width="5"/>
<circle cx="50" cy="54" r="3.5" fill="{r}" stroke-width="2"/>"""),
    "mail": ("red", """
<rect x="9" y="22" width="82" height="58" rx="8" fill="{c}"/>
<path d="M12 27 L50 56 L88 27" fill="{l}"/>"""),
    "plug": ("lime", """
<rect x="34" y="12" width="9" height="26" rx="3.5" fill="{w}"/>
<rect x="57" y="12" width="9" height="26" rx="3.5" fill="{w}"/>
<path d="M50 76 V93" fill="none" stroke-width="7"/>
<path d="M25 37 h50 v15 a25 25 0 0 1 -50 0 Z" fill="{c}"/>
<path d="M33 48 V53" fill="none" stroke="{w}" stroke-width="4"/>"""),
    "code": ("blue", """
<rect x="9" y="16" width="82" height="68" rx="11" fill="{c}"/>
<path d="M36 37 L23 50 L36 63 M64 37 L77 50 L64 63 M56 31 L44 69" fill="none" stroke="{w}" stroke-width="7"/>"""),
    "shield": ("green", """
<path d="M50 8 L84 20 V46 C84 68 70 82 50 92 C30 82 16 68 16 46 V20 Z" fill="{c}"/>
<path d="M50 8 L84 20 V46 C84 68 70 82 50 92 Z" fill="{d}" stroke="none" opacity=".35"/>
<path d="M50 8 L84 20 V46 C84 68 70 82 50 92 C30 82 16 68 16 46 V20 Z" fill="none"/>
<path d="M34 50 L46 62 L67 38" fill="none" stroke="{w}" stroke-width="8"/>"""),
    "terminal": ("purple", """
<rect x="8" y="16" width="84" height="68" rx="10" fill="#2E2A45"/>
<path d="M8 26 a10 10 0 0 1 10 -10 h64 a10 10 0 0 1 10 10 v6 h-84 Z" fill="{c}"/>
<path d="M22 45 L34 55 L22 65" fill="none" stroke="{g}" stroke-width="6"/>
<path d="M42 67 H62" fill="none" stroke="{g}" stroke-width="6"/>"""),
    "chip": ("teal", """
<path d="M36 24 V12 M50 24 V12 M64 24 V12 M36 88 V76 M50 88 V76 M64 88 V76 M24 36 H12 M24 50 H12 M24 64 H12 M88 36 H76 M88 50 H76 M88 64 H76" fill="none" stroke-width="5"/>
<rect x="24" y="24" width="52" height="52" rx="9" fill="{c}"/>
<rect x="37" y="37" width="26" height="26" rx="4" fill="{l}"/>"""),
    "arm": ("orange", """
<rect x="14" y="78" width="44" height="12" rx="4" fill="{d}"/>
<path d="M36 76 L48 42 L76 31" fill="none" stroke-width="19"/>
<path d="M36 76 L48 42 L76 31" fill="none" stroke="{c}" stroke-width="10"/>
<circle cx="36" cy="76" r="8" fill="{y}"/>
<circle cx="48" cy="42" r="8" fill="{y}"/>
<path d="M79 27 L89 18 L94 24 M82 36 L93 41 L89 47" fill="none" stroke-width="5"/>
<circle cx="77" cy="31" r="6" fill="{w}"/>"""),
    "box": ("brown", """
<path d="M14 34 L50 48 V90 L14 76 Z" fill="{c}"/>
<path d="M86 34 L50 48 V90 L86 76 Z" fill="{d}"/>
<path d="M14 34 L50 20 L86 34 L50 48 Z" fill="{l}"/>
<path d="M32 27 L68 41" fill="none" stroke="{y}" stroke-width="7"/>"""),
    "bell": ("yellow", """
<circle cx="50" cy="12" r="5" fill="{d}"/>
<circle cx="50" cy="80" r="8" fill="{d}"/>
<path d="M50 16 C32 16 26 31 26 47 V62 L17 73 H83 L74 62 V47 C74 31 68 16 50 16 Z" fill="{c}"/>
<path d="M35 34 C37 28 41 25 46 24" fill="none" stroke="{w}" stroke-width="4"/>"""),
    "camera": ("pink", """
<path d="M32 30 L38 17 H62 L68 30 Z" fill="{d}"/>
<rect x="8" y="28" width="84" height="57" rx="11" fill="{c}"/>
<circle cx="50" cy="57" r="20" fill="{w}"/>
<circle cx="50" cy="57" r="10.5" fill="{k}" stroke="none"/>
<circle cx="46" cy="53" r="3" fill="{w}" stroke="none"/>
<rect x="72" y="36" width="11" height="7" rx="2" fill="{y}" stroke-width="2.5"/>"""),
    "rocket": ("red", """
<path d="M42 74 C42 86 50 95 50 95 C50 95 58 86 58 74 Z" fill="{y}"/>
<path d="M35 60 L19 80 L37 76 Z" fill="{d}"/>
<path d="M65 60 L81 80 L63 76 Z" fill="{d}"/>
<path d="M50 5 C67 18 71 41 66 76 H34 C29 41 33 18 50 5 Z" fill="{w}"/>
<path d="M50 5 C58 11 63 19 65.5 28 H34.5 C37 19 42 11 50 5 Z" fill="{c}"/>
<circle cx="50" cy="47" r="9" fill="{l}" stroke-width="4"/>"""),
    "audio": ("sky", "".join(
        f'<rect x="{x}" y="{50 - h / 2}" width="8" height="{h}" rx="4" fill="{{c}}" stroke-width="3"/>'
        for x, h in zip(range(10, 90, 12), (20, 44, 66, 82, 58, 36, 18)))),
}

ALIASES = {
    "home": "house", "homeserver": "house", "pc": "house",
    "rack": "server", "vm": "server",
    "web": "browser", "webapp": "browser", "frontend": "browser", "site": "browser", "page": "browser",
    "person": "user", "viewer": "user", "customer": "user",
    "team": "users", "people": "users",
    "mobile": "phone",
    "internet": "globe", "cdn": "globe", "dns": "globe",
    "db": "database", "sql": "database", "cosmos": "database",
    "storage": "folder", "files": "folder", "blob": "folder",
    "doc": "document", "file": "document", "docs": "document",
    "agent": "robot", "bot": "robot",
    "ai": "sparkle", "llm": "sparkle", "model": "sparkle", "openai": "sparkle",
    "speech": "mic", "stt": "mic", "microphone": "mic",
    "tts": "speaker", "voice": "speaker", "dubbing": "speaker",
    "youtube": "video", "stream": "video", "media": "video",
    "proxy": "tunnel", "gateway": "tunnel",
    "auth": "lock", "security": "shield", "secret": "key", "keyvault": "key",
    "settings": "gear", "worker": "gear", "process": "gear", "pipeline": "gear",
    "function": "bolt", "serverless": "bolt", "event": "bolt",
    "message": "chat", "websocket": "chat", "realtime": "chat",
    "bus": "queue", "inbox": "queue",
    "language": "translate", "translator": "translate",
    "find": "search",
    "monitor": "chart", "metrics": "chart", "insights": "chart", "dashboard": "chart",
    "github": "git", "repo": "git",
    "schedule": "clock", "cron": "clock", "timer": "clock",
    "email": "mail",
    "api": "plug", "integration": "plug", "connector": "plug", "mcp": "plug",
    "app": "code",
    "cli": "terminal", "shell": "terminal",
    "cpu": "chip", "gpu": "chip", "iot": "chip", "device": "chip",
    "robotarm": "arm", "machine": "arm",
    "package": "box", "container": "box", "docker": "box",
    "notification": "bell", "alert": "bell",
    "photo": "camera", "vision": "camera",
    "deploy": "rocket", "release": "rocket",
    "sound": "audio", "wave": "audio", "pcm": "audio",
}

FALLBACK = "box"


def names() -> list[str]:
    return sorted(_ICONS)


def resolve(name: str | None) -> str | None:
    """Canonical icon name, or None if unknown."""
    if not name:
        return None
    n = str(name).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    if n in _ICONS:
        return n
    return ALIASES.get(n)


def default_color(name: str) -> str:
    return palette.COLORS[_ICONS[name][0]]


def markup(name: str, color: str) -> str:
    """Icon markup (100x100 box) filled with colour slots derived from color."""
    return _ICONS[name][1].format(**palette.shades(color))


# Characters drawn as text inside icons; the embedded font must include them.
ICON_TEXT = "A가"
