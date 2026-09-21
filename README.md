# Trazo

**Diagrams as data.** You write a small JSON spec; Trazo validates it and builds a self-contained HTML page
with a minimal editorial style and an interactive viewer. It ships as an agent skill (Claude Code plugin)
and as a plain Python command with no dependencies.

- **Validation that fails before you ship.** Crossings, lines passing behind unrelated nodes, labels covering
  nodes or lines, overlapping nodes, over-budget diagrams and legend overflow are errors, each with a
  suggested fix. A failed build writes nothing.
- **Diagrams that cannot go stale.** Bind a node to a file, a line and a snippet of text. If the code changes,
  the build fails with the exact line instead of shipping a diagram that lies.
- **A viewer that explains.** Hover a node to see who it talks to (its relations light up, the rest dims).
  Click it for a detail panel with its description, neighbors and verified sources. Search across every
  diagram, switch light/dark/auto, zoom and pan, export any diagram as a standalone SVG.
- **Today vs target.** A section can hold two views side by side with summary cards underneath.
- **Offline and self-contained.** CSS, JS, SVG and the typeface (Latin Modern Mono, LaTeX's typewriter
  face) are inline. Without JavaScript the diagrams still render completely.

Open `examples/pipeline.html` in a browser to see it: Trazo's own pipeline, drawn with Trazo and bound to
its own source code.

## Install

**Claude Code (plugin):**

```
/plugin marketplace add totokerby/trazo
/plugin install trazo@trazo
```

**Any agent that reads skills:** copy or symlink `skills/trazo/` into its skills directory
(for Claude Code, `~/.claude/skills/trazo` or `.claude/skills/trazo` in a project).

**Without an agent:** Python 3 with the standard library is all it needs.

```bash
git clone https://github.com/totokerby/trazo.git
python3 trazo/skills/trazo/trazo.py test
```

## Use

```bash
python3 skills/trazo/trazo.py validate examples/pipeline.trazo.json
python3 skills/trazo/trazo.py build    examples/pipeline.trazo.json out.html
python3 skills/trazo/trazo.py capture  out.html shots/        # PNGs, light and dark (needs Chrome/Chromium)
python3 skills/trazo/trazo.py test                            # sources self-test
```

`build` prints a receipt with the sha256 and size of both the spec and the page.

## A minimal spec

```json
{
  "trazo": 1,
  "lang": "en",
  "title": "Checkout",
  "sections": [{
    "id": "checkout",
    "views": [{
      "diagram": {
        "id": "checkout",
        "type": "flow",
        "title": "Checkout",
        "description": "The web app sends the order to the API, which stores it.",
        "size": [760, 260],
        "nodes": [
          {"id": "web", "x": 40,  "y": 60, "kind": "person",  "name": "Web app"},
          {"id": "api", "x": 300, "y": 60, "kind": "focus",   "name": "Orders API", "detail": "Validates and prices the order."},
          {"id": "db",  "x": 560, "y": 60, "kind": "state",   "name": "Database"}
        ],
        "edges": [
          {"from": "web", "from_side": "right", "to": "api", "to_side": "left", "label": "ORDER"},
          {"from": "api", "from_side": "right", "to": "db",  "to_side": "left", "label": "WRITES"}
        ]
      }
    }]
  }]
}
```

The full schema, the rules the validator enforces and the recommended workflow are in
[`skills/trazo/SKILL.md`](skills/trazo/SKILL.md).

- **Types and budgets** (nodes / edges): `architecture` 9/12, `flow` 9/12, `org` 12/14, `layers` 6/0.
- **Kinds**: `focus`, `process`, `state`, `external`, `person`, `pending`, `gate`.
- **Edge styles**: `flow`, `main`, `external`, `pending`, `main-pending`.
- **Languages**: the viewer and legend speak English (`"lang": "en"`) or Spanish (`"lang": "es"`); Spanish
  schema keys are accepted as aliases.

## Design principles

The highest-quality move is usually deletion. Every node is a distinct idea and every edge carries
information; past the budget, split into an overview plus detail. The accent is editorial: one or two
elements per diagram. Positions are explicit on purpose: automatic graph layout tends to produce the
generic look this style avoids, so Trazo tells you what to fix instead of guessing.

## Credits

Trazo was inspired by [archify](https://github.com/tt-a1i/archify) by tt-a1i (diagrams as typed data,
validation, source binding, the viewer) and [diagram-design](https://github.com/cathrynlavery/diagram-design)
by Cathryn Lavery (the editorial style, connector rules and complexity budget). It is an independent
implementation; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

MIT. The bundled Latin Modern Mono fonts are under the GUST Font License.
