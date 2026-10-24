---
name: vis
description: Use when the user wants a cross-reference map of categories and tags (rules or knowledge spread over many chapters), a mind map, an interactive network graph, or a quick cartoon sketch of a repo. Architecture and relationship diagrams go to the arch skill. Triggers "시각화", "그림으로", "도식", "도표", "마인드맵", "그래프로", "네트워크", "교차 참조", "카테고리와 태그", "지식 지도", "vis", "visualize", "mind map", "network graph", "cross reference map", "knowledge map".
argument-hint: "[what to draw, or a spec file]"
---

vis: pictures from a short spec

One command draws four kinds of picture. The spec's kind: picks one.

	arch      cartoon architecture diagram: core entities as icons, arrows that say what each does. HTML + SVG + PNG
	xref      categories down the side x tags across the top: matrix, relation graph, category tree, tag list. HTML + PNG
	mindmap   collapsible tree, left to right, with notes and search. HTML + PNG
	graph     network laid out by forces: drag, pan, zoom, click for links, hide groups. HTML + PNG

All HTML is one self-contained file (no CDN), light and dark, works at phone width. Spec formats: reference.md in this folder.


1. Pick the kind

	- Parts of a system and what flows between them: arch
	- One body of knowledge with a hierarchy (chapters) and cross-cutting labels (tags) that must be reviewed together: xref
		- vertical knowledge = the category tree; horizontal knowledge = tags; the matrix and relation graph show the cross references
	- An outline, a course map, a brainstorm with depth: mindmap
	- Things with no above or below, only connections (people, modules, services, concepts): graph
	- If two fit, do not ask: make both and show both


2. Understand the material first

	- arch: read README, entry points, config, deploy files. For Azure: az resource list -g <group> -o table
	- xref: take the categories from the source's own table of contents, then the tag groups, and write one line of criteria per tag (what counts, what does not). Notes on a link are the actual sentences, with their article number or page
	- mindmap and graph: one short label per node. Detail goes in note:, not in the label
	- Facts in labels and notes come from the source. Links (doc:, url:) are checked to exist before writing them


3. Write the spec

	- Default place: next to the material, named <topic>-<kind>.yaml (or .json for generated data)
	- Big generated data (hundreds of links): write it as JSON from a script, not by hand
	- Exact keys and one example per kind: reference.md


4. Render

	python "${CLAUDE_SKILL_DIR}/scripts/vis.py" <spec> [-o path/name] [--formats html,png]

	- Once per machine: pip install -r "${CLAUDE_SKILL_DIR}/scripts/requirements.txt"
	- Writes <name>.html and <name>.png next to the spec (arch also writes .svg)
	- The PNG needs Chrome, Edge or Chromium. Set VIS_BROWSER if it is not found
	- arch only: --icons lists icons, --gallery draws them


5. Look, then fix

	- Fix every WARN line (unknown key, tag with no link, node with no edge, edge through a node)
	- Open the PNG with Read and check it as a reviewer would: nothing overlaps, labels readable, the point comes across in 3 seconds
	- For the HTML kinds, also click through once: serve the folder with python -m http.server, open it in the browser tool, click a cell, a tag, a node, try search
	- arch fixes, in order: shorter labels, merge minor nodes, pin col:, then layout: manual
	- xref: over about 25 tags makes the matrix wide. Merge tags or split the map
	- Re-render until clean


6. Hand over

	- Give the full paths of the HTML and the PNG. Show the PNG
	- If the page does not say what colours, sizes and lines mean, say it in one sentence


7. Architecture diagrams go to the arch skill (2026-10-25)

	- A real architecture or relationship diagram (start, end, groups, arrows, official icons, hover box, docs in a new tab) is drawn with C:\Users\aidan\.claude\skills\arch\SKILL.md
	- kind: arch here is only a quick cartoon sketch of a repo. The cartoon look was an early improvisation, not a requirement


Common mistakes

	- Sentences as labels. Labels are 1-4 words; detail goes to role:, note: or notes:
	- YAML flow mappings with a comma or ': ' inside a value: quote the value
	- Calling auto-extracted tag mappings facts. Label them as a first draft in note:
	- Publishing private material: the HTML embeds all of its data
