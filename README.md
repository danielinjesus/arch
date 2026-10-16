# arch

A Claude Code skill that draws **colourful, cartoon-style architecture diagrams**: the core entities as icons, what each
one does (its role), and arrows that say what they do to each other. Icons open their documentation.

![Live Translator architecture](examples/translator.png)

*[examples/translator.yaml](examples/translator.yaml) → `translator.png`, `translator.svg`, and `translator.html`
(clickable icons, flowing arrows).*

## Use it in Claude Code

```text
/plugin marketplace add danielinjesus/arch
/plugin install arch@arch
/arch:draw this repo
```

Or just ask: "draw the architecture of this repo". Claude reads the code, writes a small YAML spec, renders it,
looks at the PNG, and fixes what overlaps. In a session that has this repo open, the skill is there already.

## Use it by hand

```bash
pip install -r .claude/skills/draw/scripts/requirements.txt     # pyyaml, fonttools[woff]
python .claude/skills/draw/scripts/draw.py examples/translator.yaml
python .claude/skills/draw/scripts/draw.py --icons               # 40 icons and their aliases
```

A spec is short:

```yaml
title: Live Translator
groups:
  foundry: {label: Microsoft Foundry, color: purple}
nodes:
  server: {label: Home server, icon: house, tech: FastAPI, role: runs one pipeline per viewer,
           doc: https://fastapi.tiangolo.com/}
  speech: {label: Speech, icon: mic, tech: Azure Speech, group: foundry,
           doc: https://learn.microsoft.com/azure/ai-services/speech-service/speech-translation}
edges:
  - server <-> speech: {label: audio → text, step: 1}
```

Everything else (dashed and two-way arrows, numbered steps, pinned columns, manual layout, all icons) is in
[reference.md](.claude/skills/draw/reference.md).

The PNG is taken with headless Chrome, Edge or Chromium (found automatically; `ARCH_BROWSER` overrides). Without a
browser you still get the HTML and SVG.

## How it works

| Path | What |
|---|---|
| `.claude/skills/draw/SKILL.md` | What Claude does: understand the system, write the spec, render, look, fix |
| `.claude/skills/draw/scripts/archdraw/spec.py` | YAML/JSON spec → nodes, edges, groups, with friendly errors |
| `.../layout.py` | Columns by flow, groups kept in boxes no other node enters, neighbours pulled level |
| `.../route.py` | S-curves between columns, free lanes around nodes, label spots that avoid collisions |
| `.../render.py`, `icons.py` | The cartoon look: ink outlines, hard shadows, tilted stickers, 40 hand-made icons |
| `.../png.py` | Headless browser screenshot, cropped to the diagram |
| `.claude-plugin/` | Makes the repo an installable plugin and marketplace |

The font is [BM Jua](https://github.com/google/fonts/tree/main/ofl/jua) (SIL Open Font License 1.1, see
`archdraw/fonts/OFL.txt`), subset and embedded so the diagram looks the same everywhere.

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
```
