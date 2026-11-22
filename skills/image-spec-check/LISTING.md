# Listing page content: image-spec-check

**One line:** Checks exported images against your own spec table and says exactly what to resize, crop, re-export or replace.

## What it does

The agent builds a small CSV from the numbers you give it (pixel size or aspect ratio, allowed formats, size limit, minimum print DPI), then runs a standard-library script over your image folder. The script reads PNG, JPEG, GIF, WebP and SVG headers, takes file size from the filesystem, and reads density from PNG pHYs, JPEG JFIF or EXIF when present. Each file gets a verdict per spec: pass, resize (ratio gap under 3 percent, even one pixel off), crop or pad (over 3 percent, with a crop box and a padded canvas size), re-export (wrong format or extension, over the size limit, DPI missing or low, upscale over 5 percent), or unreadable (empty, truncated, corrupt). The output is strict JSON. The skill never edits images and never supplies a platform's rules from memory.

## Capabilities

- Exact-pixel, minimum, maximum and aspect-ratio-only checks, per destination
- Extension versus real header check (a PNG saved as `.jpg`)
- File size against a limit, with a format hint (photograph or flat graphic, by bytes per pixel)
- DPI from PNG, JFIF and EXIF; largest print size the pixels support
- Truncated and corrupt file detection
- Strict JSON report, optional `--out` copy that can never overwrite an input

## When to use

You have exported images and a spec (yours or your printer's or client's) and want to know which files fail and what to do about each one: "check my exports", "off by a pixel", "file too big", "wrong aspect ratio", "what do I resize this to".

## When not to use

Designing the artwork, resizing or re-saving the images, compressing for page speed, judging blur or colour, writing alt text, or looking up what a platform currently requires. Related skills (logo and poster design, brand guidelines) design the artwork; this one verifies finished files against numbers.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent compares sizes by hand and says the other checks were skipped.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet. What exists is the script on generated sample images (`python evals/make_samples.py OUT hero`), spec `hero` = 1600x900 exact, jpg or webp, 300 KB maximum:

1. `python scripts/image_spec_check.py --specs evals/fixtures/specs.csv --spec hero OUT`: 7 files, exit 1. `hero_ok.jpg` pass; `hero_1px.jpg` (1599x900) resize, `size_mismatch`, "scale to 1600x900"; `hero_wide.jpg` (2400x900) crop_or_pad, crop box x=400 y=0 1600x900 keeping 66.7 percent, or pad to 2400x1350; `hero_big.jpg` (400000 bytes) reexport, `over_size`, 100000 bytes over; `hero_wrongext.jpg` (a PNG named .jpg) reexport, `extension_mismatch` and `format_not_allowed`, advice `flat_use_webp`; `hero_small.webp` (800x450) reexport, `too_small` (2.00x upscale); `hero_trunc.jpg` unreadable, `truncated`.
2. Print: spec 1748x2480, png or jpg, 300 dpi minimum. A PNG with pHYs 300 dpi passes and reports a maximum print size of 5.83 x 8.27 inches; a PNG with no density reports `dpi_missing`; one at 72 dpi reports `dpi_low`.

## Limits

- Headers and file size only: it cannot see blur, banding, colour profile, transparency or a subject cut by a crop.
- Animated files are checked at canvas size; SVG by aspect ratio only.
- The photograph-or-flat hint comes from file size and can be wrong.
- Spec numbers are only as current as what you supply.

## Evidence

Static lint and script fixtures only (12 cases). See `VERIFICATION.md`. No with-skill against baseline run, no trigger test, no cross-tool test, no human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Check the hero exports against my spec table and tell me what to fix."
2. The agent shows the spec CSV it built from your numbers and runs the checker on the folder.
3. The summary comes back: 7 files, 1 pass, 1 resize, 1 crop or pad, 3 re-export, 1 unreadable.
4. The agent lists fixes by action: scale `hero_1px.jpg` to 1600x900; crop `hero_wide.jpg` to the 1600x900 box at x=400 or pad to 2400x1350; re-export the three files; replace the truncated one.
5. After re-export, one more run exits 0.

## FAQ seeds

- Does it need network access? No.
- Does it change my images? Never; it only reads them. The optional report file refuses to overwrite any input.
- Which sizes does it know for each platform? None. You supply the spec; the numbers change and the skill will not guess.
- Does it work on SVG? Aspect ratio only; pixel-exact checks do not apply to vectors.
- Why does it say DPI is missing when my image is high resolution? Density metadata and pixel count are separate; the result shows the print size your pixels support.
- How is it different from a design skill? Those make the artwork; this verifies exported files against numbers.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
