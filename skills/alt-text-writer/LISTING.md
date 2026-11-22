# Listing page content: alt-text-writer

**One line:** Writes and checks image alt text and long descriptions in HTML and Markdown, per image function.

## What it does

The skill gives an agent a seven-step procedure: inventory the images with a script, ask the user once what each flagged image shows and why it is there, classify each image as informative, decorative, functional, complex or text-in-image, write alt text by the rule for that function, write long descriptions for charts and diagrams, verify, and report. A decision table, a length table, nine context rules and a list of phrases to avoid carry the editorial knowledge. The script `scripts/alt_text_review.py` scans HTML and Markdown for twelve problems and can validate proposed alt text for images the user has described. It never describes pixels and the skill tells the agent to ask rather than guess.

## Capabilities

- JSON inventory of every `<img>`, `<input type=image>`, `<area href>` and Markdown image: file, line, alt, guessed function, flags, and the question to ask the user
- Twelve flags: missing alt, empty alt in a link, title without alt, file-name alt, generic alt, "image of" prefix, over-long alt, repeated alt, caption duplicate, decorative candidate, presentation role with alt, chart without a long description
- `--described` validation of proposed alt text per function (decorative must be empty, functional must name an action, text-in-image must be verbatim, complex needs a long description location)
- A fixed report: what changed, long descriptions, what the author still has to answer, what was not checked

## When to use

You ask for alt text, an alt text review, image descriptions for accessibility, or say screen reader users cannot tell what an image is, and you can tell the agent what each image shows.

## When not to use

A whole-page WCAG audit (use an accessibility audit skill), caption writing, image generation prompts, or asking the agent to describe an image it has not been told about. It cannot see the picture.

Difference from `accessibility-audit`: that skill audits a whole page against WCAG; this one makes a per-image decision and writes and verifies the text.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the flag table by hand.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs come from a saved fixture run (`python evals/run_fixtures.py`, 8/8 cases passed).

1. `python scripts/alt_text_review.py evals/fixtures/bad_page.html`: 15 images, all 15 flagged, exit code 1. Flags by line include `filename_alt` for `IMG_4821.jpg`, `missing_alt` four times (an image, a title-only image, an image input and an area), `empty_alt_in_link` for an arrow icon inside a link, `complex_no_long_description` for `revenue-chart.png`, `caption_duplicate` for a figure whose alt equals its caption, and `repeated_alt` on two different products both called "Product photo".
2. Same page with `--described evals/fixtures/described.json`: of 6 proposals, 2 fail (`image of the office lobby` gets `redundant_prefix`; the chart proposal gets `complex_without_long_description` because no long description location was given) and 1 description names an image that is not on the page, listed under `unmatched_descriptions`.

## Limits

- Checks form, not accuracy: it cannot tell whether an alt text is true.
- Decorative, complex and function guesses come from file names, classes and nearby words.
- Long description detection is wording-based.
- SVG, CSS background images, icon fonts and live pages are not scanned.
- 125 characters and 0.85 caption similarity are working values.
- English wording lists only.

## Evidence

See `VERIFICATION.md`. In short: static lint with 0 FAIL and 0 WARN, and 8 script fixture cases pass. Not tested: efficacy against a baseline, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Run the script on a page with 15 problem images: 15 flagged, with the questions to ask.
2. The agent asks one batch of questions; the user answers in a few lines.
3. The agent proposes alt text and validates it with `--described`; two proposals fail and are fixed.
4. Re-run on the edited page: clean. Show the report, including what was not checked.

## FAQ seeds

1. Does it need network? No.
2. Can it write alt text from the picture itself? No. It asks you what the image shows; it cannot see it.
3. How is it different from an accessibility audit skill? It works image by image and writes the text; an audit covers whole pages.
4. Does it edit my files? The script is read-only. The agent edits your page only as part of the task you gave it.
5. Why is 125 characters the limit? It is a common working limit, not a WCAG number; change it with `--max-length`.
6. Does it handle Markdown? Yes, including reference-style images; code blocks are skipped.
7. What about React or template alt values? Template placeholders are marked `dynamic_alt` and skipped; spot-check real output.
8. How do I uninstall? Delete the skill folder.

## Changelog

- 0.1.0, 2026-11-21: first draft, fixtures only, not re-verified.

## License and authorship

Apache-2.0. Copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
