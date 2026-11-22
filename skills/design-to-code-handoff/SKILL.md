---
name: design-to-code-handoff
description: Turns a design export into faithful front-end code. Reads design-tool node JSON (the REST node shape that design tools export) or a written spec, translates auto layout, sizing, text styles, strokes and effects into CSS with a bundled script, maps every value to the project's existing tokens and components, and reports each deviation. Use when the user wants a design, mockup, frame or component implemented exactly, mentions design handoff, design-to-code, redlines or a design file export, or says the build does not match the design. Do not use for designing a new interface without a spec, or for editing the design file itself.
license: Apache-2.0
compatibility: The translation script needs Python 3.9 or newer (standard library only). No network access is used and no design-tool account is contacted, so the node JSON must already be in the workspace. Without Python, translate by hand with the mapping reference and say so.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Design to code handoff

A handoff goes wrong in predictable ways: values are retyped approximately, existing tokens and components are bypassed with raw values, hidden layers get built, artboard sizes become fixed widths, and states that were never drawn are never built. `scripts/node_to_css.py` removes the retyping; the workflow removes the rest.

## Workflow

Copy this checklist into the reply and tick items as they are done:

```
- [ ] 1. Inputs located (node JSON or spec, tokens, existing components)
- [ ] 2. Script run with --tokens; output read in full
- [ ] 3. Reuse decided: existing components and tokens first
- [ ] 4. Structure decided: semantic elements, what flexes, what is fixed
- [ ] 5. Built from the script output, flags resolved one by one
- [ ] 6. States and breakpoints that were not drawn are handled or listed
- [ ] 7. Fidelity table checked against the spec
- [ ] 8. Report: deviations, open questions, what was not verified
```

### 1. Locate the inputs

Find, in the project: the design export (node JSON in the REST shape that Figma and compatible tools produce; a written spec also works, by hand); the token source (CSS custom properties, theme file, or utility config); the existing components the design uses (buttons, inputs, icons); and one finished screen to match conventions (naming, file layout, units). This skill does not fetch from a design tool: if the JSON is not in the workspace, ask for the export.

### 2. Run the script

```bash
python scripts/node_to_css.py design/card.json --tokens src/tokens.css
python scripts/node_to_css.py design/page.json --tokens src/tokens.css --node "Checkout / Summary"
python scripts/node_to_css.py design/page.json --tokens src/tokens.css --diff "Hero / Desktop" "Hero / Mobile"
```

It prints, per layer: the CSS declarations the layer's properties mean, with exact token matches as `var(--name)`; the text content; an element hint; and `!` flags for everything that needs a decision. `--diff` prints only the declarations that change between two frames of the same design, which are the breakpoint overrides. Read the whole output before writing code. Do not edit the script to change its output.

Without the script, use the mapping tables in [references/property-mapping.md](references/property-mapping.md). Read that file also when a flag or a property is unclear.

### 3. Reuse before writing

- A layer of type `INSTANCE` is a use of a design component. Find the code component with the same name and use it with the matching variant props. Do not restyle it locally; if the instance differs from the code component, report the difference.
- A value that matches a token is written as the token, never as the raw value. Prefer semantic tokens over palette tokens when both match.
- **Off-token values** (flagged by the script): never keep silently and never snap silently. Use the nearest token when the difference is small and nothing structural depends on it; keep the spec value when a fixed size depends on it (for example padding that produces a 44px control height). List every one in the report with the choice made.

### 4. Decide the structure

The layer tree is not the DOM tree.

- Choose elements by meaning: headings by document outline (not by font size), `button` for actions, `a` for navigation, lists for repeated items, `label` with every input. Use the script's hints as a start.
- Drop wrapper layers that exist only for the design tool; add wrappers only where layout needs them.
- The top-level frame width is the artboard. Turn it into `max-width` or a container, never a fixed `width`.
- Fixed heights on containers that hold text become `min-height` unless the spec says to clip.
- Layers with no auto layout are positioned by coordinates in the export: infer the intended flow from the offsets and build it with flex or grid. Absolute positioning is only for layers marked absolute (badges, overlays).
- Hidden layers (`visible: false`) are not built. The script lists what it skipped.
- Vector layers are assets: use the project's icon set or export SVG; never redraw with CSS.
- Text in the export is sample content. Build for longer text, wrapping and translation; keep the source text in its natural case and apply `text-transform` in CSS.

### 5. Build

Write the styles from the script output in the project's conventions (class naming, file placement, units). Keep `gap` on the parent rather than margins on children. Keep line-height unitless and letter-spacing in `em` as printed. Resolve each `!` flag: act on it or record why not.

### 6. States and breakpoints

The export shows only what was drawn.

- Variants (layers named like `State=Hover`) map to real selectors: `:hover`, `:focus-visible`, `:active`, `:disabled`, `[aria-invalid="true"]`, `[aria-expanded="true"]`, never to classes that someone must toggle by hand unless the project does that. Build only the differences between the variant and the default.
- When a variant changes border width, avoid layout shift: draw the extra width with `outline` or `box-shadow`, or reserve the space.
- States that were not drawn (focus above all, then hover, disabled, loading, error, empty) are still required: reuse the project's existing state styles and list them in the report as "not in the design".
- With two frames, use `--diff`: write one as the base and the differences inside a media or container query. Pick the breakpoint where the layout stops fitting, not the artboard width. Between the frames the layout must flex: no fixed widths.
- With one frame, make it fluid and state that narrower and wider layouts were not specified.

### 7. Fidelity check

Before reporting, build a table for the main layers and verify each row against the script output: `layer | property | spec | code | match`. Cover at least: spacing (gap, padding), size, colours, radius, border, shadow, font size, weight, line height, letter spacing, alignment. A row that does not match is fixed or becomes a listed deviation.

### 8. Report

End with: files changed; components and tokens reused; the deviations table (off-token decisions, anything rounded, anything not built and why); states and breakpoints not in the design; open questions for the designer; and what was not verified (rendering in a browser, pixel comparison, fonts actually loading, real content).

## Limits

- Works from an exported file. It does not connect to any design tool, read comments or prototypes, or export images.
- The script translates auto layout, sizing, solid and linear-gradient fills, strokes, radii, shadows, blurs and text styles. Grid auto layout, masks, blend modes, image crops and component property logic are flagged, not translated.
- Token matching is exact for colours and lengths; composite tokens match only when their value is written the same way.
- Nothing is rendered: fidelity is checked value by value, not visually.
