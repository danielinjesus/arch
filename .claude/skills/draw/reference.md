# Spec reference

A spec is YAML (or JSON). Only `nodes` is required.

```yaml
title: Name of the system            # big, top left
subtitle: what it does in one line
note: one footnote line, bottom left (optional)
layout: auto                         # auto (default) or manual

groups:                              # boxes for places / trust boundaries
  <id>: {label: Shown on the tab, color: purple}
  <id>: Just a label                 # colour picked for you

nodes:
  <id>:                              # letters, digits, _ or . (no hyphens)
    label: 1-2 bold words            # default: the id
    icon: house                      # default: the id if it is an icon name, else a box
    tech: product or service name    # tag under the icon
    role: what it does, one short line   # wraps to at most 3 lines
    doc: https://...                 # the icon links here in the HTML and SVG
    color: orange                    # default: the icon's own colour
    group: <group id>
    col: 2                           # auto layout: pin to a column (0 = left)
    at: [col, row]                   # manual layout only, on every node (fractions allowed)
  <id>: Label only                   # short form

edges:
  - a -> b                           # arrow
  - a -> b: verb phrase              # with a label
  - a <-> b: both ways               # arrowheads at both ends
  - a --> b: optional or async       # dashed
  - a <--> b: dashed, both ways
  - a -> b: {label: send audio, step: 1, color: red}   # step = numbered badge for the main flow
  - {from: a, to: b, label: ..., both: true, dashed: true, step: 2}
```

Quote a label that contains `: `, e.g. `- a -> b: "time: 3s"`.

Colours: `red orange yellow lime green teal sky blue purple pink brown` or `#RRGGBB`. An arrow takes the colour of
the node it points to.

## Writing good labels

| Field | Good | Too much |
|---|---|---|
| label | `Home server` | `Windows desktop home server running FastAPI` |
| tech | `FastAPI · Windows PC` | the whole requirements.txt |
| role | `runs one pipeline per viewer` | a paragraph |
| edge | `audio → text`, `fix sentences` | `the server sends PCM audio frames over the websocket` |

- One node per thing a reader must know about. Libraries live in `tech`, not in their own node.
- An edge label is what the source does to the target (a verb), or what flows (a noun → noun).
- Use `step:` on the 4-8 edges of the main flow so the reader can follow it in order.
- Write `→` freely: it is drawn as an arrow.
- Korean and English both work (the embedded font covers the common 2,350 Hangul syllables).

## Icons

| Icon | Aliases |
|---|---|
| arm | machine, robotarm |
| audio | pcm, sound, wave |
| bell | alert, notification |
| bolt | event, function, serverless |
| box | container, docker, package |
| browser | frontend, page, site, web, webapp |
| camera | photo, vision |
| chart | dashboard, insights, metrics, monitor |
| chat | message, realtime, websocket |
| chip | cpu, device, gpu, iot |
| clock | cron, schedule, timer |
| cloud | |
| code | app |
| database | cosmos, db, sql |
| document | doc, docs, file |
| folder | blob, files, storage |
| gear | pipeline, process, settings, worker |
| git | github, repo |
| globe | cdn, dns, internet |
| house | home, homeserver, pc |
| key | keyvault, secret |
| lock | auth |
| mail | email |
| mic | microphone, speech, stt |
| phone | mobile |
| plug | api, connector, integration, mcp |
| queue | bus, inbox |
| robot | agent, bot |
| rocket | deploy, release |
| search | find |
| server | rack, vm |
| shield | security |
| sparkle | ai, llm, model, openai |
| speaker | dubbing, tts, voice |
| terminal | cli, shell |
| translate | language, translator |
| tunnel | gateway, proxy |
| user | customer, person, viewer |
| users | people, team |
| video | media, stream, youtube |

`draw.py --gallery -o icons` draws them all.

## Layout

Auto layout puts the flow left to right: a node's column is the longest chain of arrows leading to it (arrows that
close a loop are ignored), then each column is ordered so arrows cross as little as possible. A group is kept in one
box that no other node enters. An arrow that would cross a node takes a free lane with rounded corners.

When auto layout cannot avoid a problem, the renderer prints a `WARN` line. Pin columns with `col:` first; use
`layout: manual` only for full control.
