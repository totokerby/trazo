---
name: trazo
description: Diagrams as data. Use for any architecture map, flow, process, org chart, control-layer stack or current-vs-target comparison. Writes a typed JSON spec, validates it (blocks crossings, lines behind nodes, covered labels, over-budget diagrams and stale code references) and builds a self-contained HTML page with inline SVG, a minimal editorial style and a viewer with per-node detail, hover that shows who each node talks to, search, light/dark theme, zoom and SVG export.
license: MIT
---

# Trazo

A diagram is data: a JSON spec that is validated and built. Never hand-write the SVG.

```bash
python3 <skill-dir>/trazo.py validate <doc.trazo.json>          # errors with a suggested fix
python3 <skill-dir>/trazo.py build    <doc.trazo.json> <out.html> # only if it validates; prints a sha256 receipt
python3 <skill-dir>/trazo.py export   <doc.trazo.json> <id> <out.svg> [--theme dark]  # standalone SVG, fonts embedded
python3 <skill-dir>/trazo.py capture  <out.html> <dir>            # one PNG per diagram, light and dark
python3 <skill-dir>/trazo.py test                                 # sources self-test
```

Complete example: `examples/pipeline.trazo.json` in the repository.

## Before drawing
- **The highest-quality move is usually deletion.** Every node is a distinct idea; two nodes that always
  travel together are one. Every edge carries information; if the layout already says it, delete it.
- **If a three-column table says the same thing, use the table.**
- **Target density 4/10.** Past the type's budget, split into an overview plus detail.
- **The accent is editorial**: 1 or 2 elements per diagram (`focus` nodes plus `main` edges).
- Long explanations go in each node's `detail` and in the cards, not in the drawing.

## Document
```json
{"trazo": 1, "lang": "en", "repository": ".", "eyebrow": "...", "title": "...", "intro": "...", "footer": "...",
 "sections": [{"id": "flow", "eyebrow": "Part 1", "title": "...", "nav": "1. ...", "lead": "...",
   "views": [{"label": "Today", "diagram": {...}}, {"label": "Target", "diagram": {...}}],
   "cards": [{"eyebrow": "...", "title": "...", "accent": false, "items": ["..."]}]}]}
```
`lang` (`en` or `es`) sets the viewer and legend language. `repository` is the root that sources are
checked against, relative to the JSON file. A section with one view and no cards is a single diagram.

## Diagram
```json
{"id": "api-today", "type": "architecture", "title": "...", "description": "one sentence: what it shows",
 "size": [1000, 560],
 "zones": [{"x": 20, "y": 160, "w": 740, "h": 320, "label": "PRIVATE NETWORK", "label_x": 12}],
 "nodes": [{"id": "api", "x": 232, "y": 360, "w": 160, "h": 80, "kind": "focus", "tag": "SERVICE",
            "name": "API", "sub": ["mono line 1", "mono line 2"],
            "detail": "Text for the detail panel.",
            "sources": [{"path": "src/api.py", "line": 42, "contains": "def handle"}]}],
 "edges": [{"from": "api", "from_side": "right", "to": "db", "to_side": "left", "label": "WRITES",
            "style": "flow", "mid": 640, "pos": "below", "t": 0.5, "segment": 1, "detail": "..."}]}
```
- **type** and its budget (nodes / edges): `architecture` 9/12, `flow` 9/12, `org` 12/14, `layers` 6/0
  (layers: wide nodes, `w` about 920 and `h` 56, no edges).
- **kind**: `focus` (1-2), `process`, `state` (data, storage), `external` (cloud, third parties), `person`,
  `pending` (conditional or not built yet, dashed), `gate` (control or approval).
- **style**: `flow`, `main` (accent), `external` (blue), `pending` (dashed), `main-pending`.
- **sides**: `left`, `right`, `top`, `bottom`. Routes are orthogonal with rounded corners: straight when both
  ends share an axis, L when orientation changes, Z otherwise. `mid` fixes the middle segment of a Z.
  Several edges on the same side spread out automatically.
- **label**: 14 characters or fewer, uppercase. `pos` (`above`/`below` on horizontal segments, `left`/`right`
  on vertical ones), `t` (0-1 along the segment) and `segment` (index) move it.
- **4px grid** for x, y, w, h. The legend takes the last 60px of the canvas.
- **sources**: `path` relative to `repository`; `line` and `contains` are optional. With both, that line must
  contain the text: when the code changes, the diagram stops building instead of lying.

## Workflow
1. Write or edit the JSON. Positions are explicit: there is no automatic layout, on purpose.
2. `validate`. Fix only what is diagnosed, following the suggested fix. Repeat until 0 errors.
3. `build`. If it does not validate, nothing is written: the previous output stays intact.
4. `capture` and **look at the images**. The validator does not approve the design; a reviewed capture does.
5. Call it done citing the receipt (errors, warnings, sha256) and which captures were reviewed.

## What the validator blocks
Type budget, too much accent, overlapping or off-canvas nodes, lines passing behind an unrelated node,
crossings and parallel overlaps closer than 12px, labels covering a node, a line, another label or a zone
label, legend overflow, sources that do not resolve, and invalid kinds, styles and sides. It warns (does not
block) on the 4px grid and on text close to a node border.

## Viewer (built into the HTML)
Hover a node: its relations light up, the rest dims, and a tooltip lists who it talks to. Click or Enter:
a panel with the tag, detail, who it sends to and receives from (clickable) and verified sources. Hover an
edge: its label and detail. Global search, auto/light/dark theme, drag-to-pan zoom and per-diagram SVG
export. Without JavaScript the diagram still renders completely. `#solo=<id>&theme=dark` isolates one
diagram (used by `capture`).

## Output
One self-contained HTML file that works offline: CSS, JS, SVG and the typeface are inline. The typeface is
Latin Modern Mono, LaTeX's typewriter face, embedded from `lib/fonts/` (GUST Font License).
