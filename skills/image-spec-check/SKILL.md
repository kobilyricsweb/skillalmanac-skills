---
name: image-spec-check
description: Checks exported image files against a spec table the user supplies (exact pixels or aspect ratio, allowed formats, max file size, minimum print DPI) by reading PNG, JPEG, GIF, WebP and SVG headers with a standard-library script, and returns strict JSON with a pass, resize, crop-or-pad or re-export verdict and a concrete fix per file. Use when the user asks whether images fit a size or ratio, says check my exports, off by a pixel, file too big, wrong format, wrong aspect ratio, or what to resize to. Do not use for designing artwork, editing or resizing the images, stating a platform's current size rules from memory, or judging image quality.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in the last section.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Image spec check

Verify finished image files against numbers the user gives you. You measure and report; you never edit, resize or re-save an image, and you never invent a destination's rules.

## Rules

1. The spec is the user's. If no spec table or numbers were given, ask for them (or for the destination's own upload page text). Do not quote a width, height, ratio or size limit from memory as current. A guess goes in a row named `guess-<destination>` and is marked unverified in the report.
2. Run the script. Do not eyeball dimensions, and never edit `scripts/image_spec_check.py` to make a check pass.
3. A file that cannot be read (`unreadable`) is reported as such; do not guess its size.

## Workflow

```
- [ ] 1 Get the spec table and the files
- [ ] 2 Run the checker
- [ ] 3 Read each verdict and its issues
- [ ] 4 Report fixes grouped by action
- [ ] 5 Re-run after the user re-exports
```

1. Build the CSV from the user's numbers (columns and formats in [references/spec-table.md](references/spec-table.md); a template is `assets/specs_example.csv`). Save it next to the images, never over an existing file. One row per destination.
2. Run, with the folder or files as arguments:

```bash
python scripts/image_spec_check.py --specs specs.csv exports/
python scripts/image_spec_check.py --specs specs.csv --spec site-hero --recursive exports/ --out report.json
```

3. Read `files[].results[spec]`: `status`, `issues` (codes), `fix` (sentences) and `suggest` (numbers you can pass to the user's editor). Read [references/header-facts.md](references/header-facts.md) only when a reported size, DPI or format looks wrong.
4. Report with the fixed shape below. Group the fixes: one list per action, so the user can batch the work in an editor.
5. After re-export, run again. Done means exit code 0 (`"ok": true`).

## Decision tables

Verdict per file and spec (worst wins; every issue is still listed):

| Verdict | Cause | Action |
|---|---|---|
| `pass` | All checks hold | None |
| `resize` | Pixels differ but the ratio gap is under 3 percent (even one pixel off counts) | Scale to the target; between 0.5 and 3 percent also trim the overflow |
| `crop_or_pad` | Ratio gap over 3 percent | Crop to `suggest.crop_box` or pad to `suggest.pad_canvas` |
| `reexport` | Wrong format or extension, over the size limit, DPI missing or low, or an upscale over 5 percent | Export again from the source, not from this file |
| `unreadable` | Empty, truncated, corrupt or unknown header | Replace the file |

Crop or pad: the crop box is the safe area, a centred box of the target ratio. Crop when the trimmed edges hold nothing important (`kept_percent` shows how much stays; below about 70 percent, look at the picture first). Pad when the subject touches an edge or the file is a logo, chart or text.

Format advice (`advice`, only on a format or size violation): photographs go to JPEG or WebP; flat graphics, logos and text go to PNG or lossless WebP; if the file is already in the best allowed format the advice is `keep_format_tune` (lower quality in steps, then colours, then pixels). The photo-or-flat guess comes from bytes per pixel and can be wrong, so say it is a guess.

DPI: it lives in PNG pHYs, JPEG JFIF or EXIF. `dpi: null` means none was found, not that it is low. Setting a density never adds pixels; use `suggest.max_print_size_in` to tell the user the largest print the pixels support at the spec's minimum.

## Script contract

`python scripts/image_spec_check.py --specs CSV PATH [PATH ...] [--spec NAME ...] [--recursive] [--out FILE] [--force]`

Run it; do not read it. Reads the CSV and image headers only. The one write is the optional `--out` copy of the report, which is refused if it resolves to the CSV or to any input image, even with `--force`. Exit 0 all pass, 1 a violation, 2 usage or spec error (stdout is then `{"ok": false, "error": "..."}`).

Strict JSON on stdout:

```
{"tool", "version", "ok", "specs": [name],
 "files": [{"path", "name", "format", "w", "h", "bytes", "aspect", "dpi": {"x","y","source"} | null,
            "vector", "animated", "warnings": [], "read_error"?: {"code","detail"},
            "results": {spec: {"status", "issues": [code], "fix": [text], "advice"?, "suggest"?}}}],
 "summary": {"files", "specs", "checks", "files_passing_all_specs", "by_status": {...}, "by_spec": {...}}}
```

`suggest` may hold `target {w,h}`, `op` (scale, scale_cover_then_trim, scale_to_fit), `crop_box {x,y,w,h}`, `kept_percent`, `pad_canvas {w,h}`, `then_scale`, `max_print_size_in`.

## Report format

```
Spec used: <table name, rows, who supplied the numbers; guesses marked unverified>
Result: <n files, n pass, n resize, n crop_or_pad, n reexport, n unreadable>
Fixes: <one list per action: resize / crop or pad / re-export / replace, with file names and numbers>
Not checked: <colour profile, visual quality, transparency, animation frames, DPI outside pHYs/JFIF/EXIF>
```

## Limits

- It reads headers and file size only; it does not decode pixels, so it cannot see blur, banding, colour profile, transparency or a subject cut by a crop.
- Animated files are checked at canvas size. SVG is checked by aspect ratio only.
- The photo-or-flat advice is a heuristic from file size.
- Spec numbers are only as current as what the user supplied.

## Manual fallback

Without Python: read width, height and size from the file's properties in the operating system, compare them with the spec row by hand using the decision table (ratio gap = width/height divided by target ratio, minus 1; 3 percent is the crop line), and say in the report that format, DPI and truncation were not verified.
