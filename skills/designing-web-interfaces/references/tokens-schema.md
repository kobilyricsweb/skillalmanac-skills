# Design tokens file format

Read this when writing or fixing `tokens.json` for `scripts/ui_audit.py`.

All sections are optional, but the script warns when `colors`, `font_sizes` or `spacing` is missing. Unknown top-level keys are reported as info and ignored.

```json
{
  "colors": {"text": "#1f2933", "background": "#ffffff", "primary": "#0b5cad", "on-primary": "#ffffff"},
  "contrast_pairs": [["text", "background"], ["on-primary", "primary"], ["text-muted", "background", "large"]],
  "font_sizes": [14, 16, 20, 24, 32, 40],
  "spacing": [4, 8, 12, 16, 24, 32, 48, 64],
  "radius": [4, 8, 9999],
  "line_heights": {"body": 1.5, "heading": 1.2},
  "breakpoints": [640, 1024, 1280]
}
```

- `colors`: name to hex, `rgb()` or `hsl()` string; or an object with `value` or `$value`. Translucent colours cannot be checked for contrast.
- `contrast_pairs`: `[foreground, background]` names; a third item `"large"` applies the 3:1 limit. When omitted, `text` on `background` and `text-muted` on `background` are used if those names exist.
- `font_sizes`, `spacing`, `radius`, `breakpoints`: numbers (px) or strings in px, rem or em (1rem = 16px).
- `radius`: values of 999 or more (pill, circle) are not counted.
- `line_heights`: unitless numbers under `body` and `heading`.

Checks and thresholds: 4 to 8 type sizes, smallest at least 12, a 16 step present, neighbour ratio between 1.1 and 1.7; spacing on the 4px grid with 5 to 12 steps; at most 4 radii; at most 14 colours and 4 hue families; contrast per pair; body line height 1.4 to 1.8, heading at most 1.4; at most 5 ascending breakpoints.

For a dark theme keep a second file such as `tokens.dark.json` and audit it separately; pairs are checked per file.
