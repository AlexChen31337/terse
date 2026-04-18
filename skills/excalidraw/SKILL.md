---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'excalidraw')"
---


# excalidraw

Generate `.excalidraw` files (JSON format) that can be opened directly in [Excalidraw](https://excalidraw.com/) or any compatible editor.

## When to Use

Invoke this skill when the user asks for:
- Architecture diagrams (system design, microservices, cloud)
- Flowcharts and process flows
- Entity-relationship diagrams
- Sequence diagrams (simplified)
- Mind maps
- Any visual diagram or drawing

## Procedure

1. **Understand the request** — Identify: nodes, connections, layout direction (LR / TB), labels, element types needed.
2. **Plan the layout** — Assign `x, y` coordinates. Use a grid: 200px between boxes horizontally, 150px vertically. Typical box: 160×60 for rectangles, 120×60 for diamonds.
3. **Generate elements** — Each element is a JSON object. See `references/element-schema.json` for the full schema. Key types:
   - `rectangle` — boxes, services, components
   - `ellipse` — start/end nodes in flowcharts
   - `diamond` — decision nodes
   - `text` — standalone labels
   - `arrow` — directed connections (use `startBinding` / `endBinding` to attach to elements)
   - `line` — undirected connections
4. **Wire arrows** — Set `startBinding: {elementId, focus, gap}` and `endBinding: {elementId, focus, gap}`. Use `focus: 0` and `gap: 1` as defaults.
5. **Add text labels to shapes** — Set `text` property on rectangles/ellipses/diamonds directly (they render text inside).
6. **Save the file:**
   ```bash
   # Save to workspace or user-specified path
   write_file("diagram.excalidraw", json.dumps(excalidraw_doc, indent=2))
   ```
7. **Tell the user** the file path and that they can open it at https://excalidraw.com/ (File → Open) or in VS Code with the Excalidraw extension.

### Excalidraw Document Structure
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [ /* array of element objects */ ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

### Element Quick Reference

| Type | Key extra fields |
|---|---|
| `rectangle` | `text`, `fontSize`, `fontFamily` |
| `ellipse` | `text`, `fontSize`, `fontFamily` |
| `diamond` | `text`, `fontSize`, `fontFamily` |
| `text` | `text` (required), `fontSize`, `fontFamily`, `textAlign` |
| `arrow` | `points`, `startBinding`, `endBinding`, `startArrowhead`, `endArrowhead` |
| `line` | `points`, `startArrowhead`, `endArrowhead` |

Arrow `points` is relative to the element's `x,y` origin, e.g. `[[0,0],[200,0]]` for a horizontal arrow.

## Pitfalls

- **IDs must be unique** — Use distinct strings like `"elem_001"`, `"elem_002"`. Duplicate IDs cause elements to overwrite each other silently.
- **Arrow binding references** — `startBinding.elementId` must exactly match the `id` of the target element. A typo makes the arrow float freely.
- **Arrow points are relative** — The `points` array is relative to the arrow's own `x,y`. The arrow's `x,y` should be the start point in canvas space.
- **Text in shapes** — Shapes (rectangle, ellipse, diamond) render `text` centered inside. Don't add a separate text element on top unless you need a label outside the shape.
- **Font family codes** — `1` = Virgil (handwritten), `2` = Helvetica, `3` = Cascadia (monospace).
- **Large diagrams** — Keep element count under ~200 for smooth performance in the browser.

## Verification

Open the generated `.excalidraw` file at https://excalidraw.com/ and confirm:
- All boxes appear in correct positions
- Arrows connect correctly between elements
- Text is readable and correctly placed
- No floating/disconnected arrows

Or validate the JSON structure:
```bash
python3 -c "import json; d=json.load(open('diagram.excalidraw')); print(f'OK: {len(d[\"elements\"])} elements')"
```
