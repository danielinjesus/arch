"""Shared bits for the interactive kinds: reading a spec, colours, and the HTML page around a view."""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from archdraw import palette
from archdraw.spec import SpecError

__all__ = ["Page", "SpecError", "read", "colour", "auto_colour", "text", "korean", "shell", "esc"]


@dataclass
class Page:
    html: str
    width: int = 1400      # window size for the PNG screenshot
    height: int = 900
    warnings: list[str] = field(default_factory=list)


def read(path: str | Path) -> dict:
    """YAML or JSON file -> mapping (no kind-specific checks)."""
    path = Path(path)
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise SpecError(f"{path.name}: not valid JSON ({e})") from e
    else:
        try:
            import yaml
        except ImportError as e:
            raise SpecError("PyYAML is needed for .yaml specs: pip install pyyaml (or write the spec as .json)") from e
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise SpecError(f"{path.name}: not valid YAML ({e}). Quote labels that contain ': '.") from e
    if not isinstance(data, dict):
        raise SpecError(f"{path.name}: the spec must be a mapping")
    return data


def colour(v, where: str) -> str | None:
    try:
        return palette.resolve(v)
    except ValueError as e:
        raise SpecError(f"{where}: {e}") from None


def auto_colour(i: int) -> str:
    return palette.COLORS[palette.AUTO_ORDER[i % len(palette.AUTO_ORDER)]]


def text(v) -> str:
    return "" if v is None else str(v).strip()


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def korean(*parts) -> bool:
    return any(re.search(r"[가-힣]", json.dumps(p, ensure_ascii=False)) for p in parts)


BASE_CSS = """
:root{--bg:#f7f5ef;--card:#fff;--ink:#1e1b2e;--sub:#5f6472;--line:#e3dfd5;--soft:#efece4;--accent:#3a5bd9}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#17151f;--card:#211f2b;--ink:#efeae0;--sub:#a9a6b4;--line:#34313f;--soft:#2a2835;--accent:#8fa8ff}}
:root[data-theme="dark"]{--bg:#17151f;--card:#211f2b;--ink:#efeae0;--sub:#a9a6b4;--line:#34313f;--soft:#2a2835;--accent:#8fa8ff}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font:15px/1.55 "Pretendard","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif}
header{max-width:1440px;margin:0 auto;padding:22px 24px 6px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:-.3px}
.lead{color:var(--sub);margin:0;font-size:14px}
.lead a,.panel a{color:var(--accent)}
.bar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;max-width:1440px;margin:10px auto 0;padding:0 24px}
.bar button,.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:6px 13px;border-radius:999px;cursor:pointer;font:inherit;font-size:13.5px}
.bar button.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.bar input{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:6px 13px;font:inherit;font-size:13.5px;min-width:180px}
.chip b{font-weight:600;margin-left:4px;color:var(--sub)}
.chip:hover,.bar button:hover{border-color:var(--ink)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.wrap{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:16px;max-width:1440px;margin:12px auto 40px;padding:0 24px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;min-width:0}
.panel{position:sticky;top:12px;max-height:calc(100vh - 24px);overflow:auto}
.panel h2{font-size:17px;margin:0 0 2px}
.meta{color:var(--sub);font-size:13px;margin-bottom:8px}
.empty{color:var(--sub);font-size:14px;margin:0}
.note{font-size:12.5px;color:var(--sub);border-top:1px solid var(--line);margin-top:12px;padding-top:8px}
.legend{display:flex;flex-wrap:wrap;gap:10px;font-size:13px;color:var(--sub);margin:0 0 10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
.foot{max-width:1440px;margin:-28px auto 30px;padding:0 24px;color:var(--sub);font-size:12.5px}
@media (max-width:900px){
  .wrap{grid-template-columns:minmax(0,1fr);padding:0 16px}
  header,.bar,.foot{padding-left:16px;padding-right:16px}
  .panel{position:static;max-height:none}
}
"""


def shell(*, title: str, subtitle: str = "", lead_html: str = "", ko: bool, css: str, body: str, script: str,
          payload: dict, foot: str = "") -> str:
    """One self-contained page: no CDN, data inlined as JSON."""
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    sub = f'<p class="lead">{esc(subtitle)}{" · " if subtitle and lead_html else ""}{lead_html}</p>' \
        if (subtitle or lead_html) else ""
    return f"""<!doctype html>
<html lang="{'ko' if ko else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{BASE_CSS}{css}</style>
</head>
<body>
<header><h1>{esc(title)}</h1>{sub}</header>
{body}
{f'<p class="foot">{esc(foot)}</p>' if foot else ''}
<script>
const D = {data};
{script}
</script>
</body>
</html>
"""
