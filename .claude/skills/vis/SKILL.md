---
name: vis
description: Use when the user wants a picture of how things relate - an architecture diagram of a repo or cloud system, a cross-reference map of categories and tags (rules or knowledge spread over many chapters), a mind map, or an interactive network graph. Triggers "시각화", "그림으로", "도식", "도표", "아키텍처 그림", "구성도", "마인드맵", "관계도", "그래프로", "네트워크", "교차 참조", "카테고리와 태그", "지식 지도", "vis", "visualize", "diagram", "architecture diagram", "mind map", "network graph", "cross reference map", "knowledge map".
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


7. Overview map of a whole course or platform (owner's rules, 2026-10-25)

	- Use when one page must show the whole flow of a course or platform so a non-specialist gets it at a glance
	- arch cannot do this (cartoon icons only, no hover box). Hand-write one HTML: copy examples/gcp-data-pipeline (build.py fills template.html)
	- Title = the purpose of the whole thing in one sentence, e.g. "데이터 파이프라인: 흩어진 데이터를 모아, 다듬고, 쌓아, 쓰게 만든다"
	- Stages of the flow as columns, left to right, joined by one flowing pipe. Cross-cutting concerns (orchestration, governance) as bands underneath
	- Only the big pieces, about 4 per stage. Intuitive first: the reader is not a specialist
	- Every item: bold name above the icon (nobody knows what an icon means), the original abbreviation or former name under it, a short pill with where it sends data or its role ("→ BigQuery 전용", "→ 어디로든")
	- What it does and why it is needed: on screen only if there is room. Otherwise a yellow box that appears on hover (shown inline on touch screens)
	- Official product icons, embedded as data URIs. Google Cloud: C:\Users\aidan\OneDrive - Daun Lee\커리어\GCP\Google Architecture
	- Hover: the item comes slightly closer and sparkles. Click: the official doc opens in a new tab (target=_blank rel=noopener)
	- Check every doc URL returns 200 and write the final URL after redirects. Use current official product names from the docs
	- Fits one 1920x1080 screen, shrinks to fit a laptop, stacks on a phone. White background; dark only by a button
	- Check: screenshots at 1920, 1440 and 390 wide, a hover state, and one click that opens a new tab


Common mistakes

	- Sentences as labels. Labels are 1-4 words; detail goes to role:, note: or notes:
	- YAML flow mappings with a comma or ': ' inside a value: quote the value
	- Calling auto-extracted tag mappings facts. Label them as a first draft in note:
	- Publishing private material: the HTML embeds all of its data
