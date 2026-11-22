## Contents

- Columns
- Value formats
- How rules combine
- Getting the spec from the user
- Issue codes and verdicts

# Spec table reference

Read this when you build or fix the spec CSV, or when a result code is unclear. `assets/specs_example.csv` is a working example with made-up destination names; its numbers are placeholders, not anyone's current rules.

## Columns

The header row may use only these names (a typo such as `hieght` is a hard error, on purpose). Only `name` is required.

| Column | Meaning |
|---|---|
| `name` | Destination label, unique. Used as the key in the JSON results. |
| `width`, `height` | Pixels, whole numbers 1 to 100000. Either or both. |
| `aspect` | Target ratio as `W:H`, `W/H` or a decimal (`1.91:1`, `16/9`, `1.7778`). |
| `size_rule` | `exact` (default when a width or height is given), `min` (at least), `max` (at most). |
| `formats` | Allowed formats separated by `|`, `;` or spaces: jpg, png, gif, webp, svg. Blank means any. |
| `max_kb` | File size limit. 1 KB is counted as 1000 bytes, the stricter reading, so a pass also holds under 1024. |
| `max_bytes` | The same limit in bytes. Give `max_kb` or `max_bytes`, not both. |
| `min_dpi` | Print density. Blank for screen destinations. |

## Value formats

- With `exact` and both a width and a height, the aspect ratio is derived. If you also give `aspect` and it disagrees by more than 0.5 percent, the table is rejected.
- `min` and `max` check only the dimensions given. They check the aspect ratio only when the `aspect` column is filled.
- An aspect-only row (no width or height) checks the ratio and nothing about pixel size.
- A row with only `formats` or `max_kb` checks only those.

## How rules combine

All checks for one file and one spec run together; the verdict is the worst one, in this order: unreadable, reexport, crop_or_pad, resize, pass. Every issue is still listed in `issues`, in the order the checks run: extension, format, file size, DPI, geometry.

## Getting the spec from the user

The user owns the spec. A destination's rules change, so never fill in a number from memory and present it as current. Ask for the numbers, or ask the user to copy them from the destination's own upload page or brief. If the user insists on a guess, put it in a spec row named `guess-<destination>` and say in the report that it is unverified.

## Issue codes and verdicts

| Code | Verdict | Meaning |
|---|---|---|
| `empty_file`, `unreadable_header`, `truncated`, `corrupt`, `unreadable_file`, `svg_no_dimensions` | unreadable | The header cannot be read or the file ends early. Nothing else is checked. |
| `extension_mismatch` | reexport | The extension names a different format from the header (a PNG saved as `.jpg`). |
| `format_not_allowed` | reexport | The real format is not in the allowed list. |
| `over_size` | reexport | Bytes above the limit. |
| `dpi_missing`, `dpi_low` | reexport | No density found in PNG pHYs, JFIF or EXIF, or below the minimum (0.5 dpi slack for rounding). |
| `too_small` | reexport | Reaching the target needs an upscale of more than 5 percent, which blurs. Export from a larger source. |
| `aspect_mismatch` | crop_or_pad | Aspect-ratio gap over 3 percent. |
| `size_mismatch`, `below_minimum`, `too_large` | resize | Pixel size differs from the target but the ratio is close enough to scale. |
| `aspect_drift` | resize | Ratio gap between 0.5 and 3 percent. |
