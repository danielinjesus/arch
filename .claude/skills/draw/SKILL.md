---
name: draw
description: Draw a colourful, cartoon-style architecture diagram of a codebase or cloud deployment, with the core entities as icons (bold 1-2 word name above, product tag and role below), arrows labelled with what each one does to the other, group boxes for places such as "home PC" or "Azure", and icons that open their documentation. Writes HTML (clickable, animated), SVG and PNG (for LinkedIn or slides).
when_to_use: The user asks for an architecture diagram, system map, "how the pieces fit", a picture of a repo or Azure resource group, or a diagram that proves they understand a system.
argument-hint: "[repo path, resource group, or what to draw]"
---

# Cartoon architecture diagram

The diagram shows only the **core entities**, the **relationships** between them and each one's **role**. It is a
proof of understanding, not an inventory: 5-10 nodes, every arrow a verb.

## 1. Understand the system first

Read before drawing: README, entry points (`main.py`, `app/`, `server.js`), config (`.env.example`, settings), package
lists (`requirements.txt`, `package.json`), deploy and infra files (`*.bat`/`*.sh`, Bicep, Terraform, GitHub
workflows). For a live Azure system: `az resource list -g <group> -o table`.

Answer in your head:
- Who uses it, and through what (browser, phone, CLI)?
- Where does each part run (home PC, Azure, Cloudflare, a SaaS API)? These become **groups**.
- What does each part do, in one short line? That is its **role**.
- What flows between parts, and in what order? These are **edges** with verbs, and **steps** for the main flow.

## 2. Write the spec

Save it as `docs/architecture.yaml` in the target repo unless the user names a place. Full format, every icon and the
rules for good labels: [reference.md](reference.md). Short form:

```yaml
title: Live Translator
subtitle: YouTube link → live subtitles + dubbing
groups:
  foundry: {label: Microsoft Foundry, color: purple}
nodes:
  server:
    label: Home server          # 1-2 bold words above the icon
    icon: house                 # see reference.md
    tech: FastAPI · Windows PC  # product / service name, in a tag under the icon
    role: runs one pipeline per viewer   # short, under the tag
    doc: https://fastapi.tiangolo.com/   # the icon opens this in the HTML
  speech: {label: Speech, icon: mic, tech: Azure Speech, role: speech → sentences → 3 languages, group: foundry,
           doc: https://learn.microsoft.com/azure/ai-services/speech-service/speech-translation}
edges:
  - server <-> speech: {label: audio → text, step: 1}
```

Links: use official documentation pages and check each one exists (search or fetch) before writing it.
Microsoft docs: prefer `https://learn.microsoft.com/...` without the locale.

## 3. Render

```bash
pip install -r "${CLAUDE_SKILL_DIR}/scripts/requirements.txt"   # once: pyyaml, fonttools[woff]
python "${CLAUDE_SKILL_DIR}/scripts/draw.py" docs/architecture.yaml
```

This writes `architecture.html`, `.svg` and `.png` next to the spec (`-o path/name` to change, `--formats png` for
one). The PNG needs Chrome, Edge or Chromium; it is found automatically, or set `ARCH_BROWSER`.
`python "${CLAUDE_SKILL_DIR}/scripts/draw.py" --icons` lists icons and aliases.

## 4. Look, then fix

Open the PNG with the Read tool and check it like a reviewer would:
- every `WARN` line is fixed (an edge through a node, a crowded label, an unknown icon);
- labels are readable, nothing overlaps, the main flow reads left to right;
- the picture says what the system does to someone who has never seen the code.

Fixes, in order of preference: shorten labels, merge minor nodes, pin a node's column with `col:`, and only then
`layout: manual` with `at: [col, row]` on every node. Re-render until clean.

## 5. Hand over

Give the paths of the PNG (for posts and slides) and the HTML (icons open their docs). Show the PNG to the user.
