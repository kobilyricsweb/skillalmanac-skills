---
name: pptx-slide-density-audit
description: Audits a .pptx deck for text-heavy slides, missing title placeholders and missing speaker notes, reporting per-slide word and bullet counts as JSON. Use when a .pptx deck arrives with long slides and needs a density check before it is presented, or when every slide must be checked for a title and for speaker notes. Do not use for editing or rewriting slide text, for .ppt, .key or .odp files, or for judging visual design, colour, layout or image quality.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# pptx-slide-density-audit

This skill runs one read-only script over a .pptx file and turns its JSON into a short density report. The script does the counting. The agent's job is to run it with the right limits, check the input, and report the flagged slides in the fixed format below.

Files in this package: `scripts/pptx_density.py` (the audit script), `LICENSE.txt`.

## Workflow

1. **Confirm the input.** Required output: the path of one `.pptx` file. If the file has any other extension (`.ppt`, `.key`, `.odp`, `.potx`), stop and say so. Do not rename or convert it.
2. **Check the size.** Required output: the file size in bytes. The script refuses anything above 2 MB (2,097,152 bytes). If the deck is larger, stop and report the size. Do not split or strip the deck.
3. **Set the limits.** Required output: the two thresholds actually used. Use the defaults (`--max-words 60 --max-bullets 7`) unless the user named other values. Record the values in the report even when they are the defaults.
4. **Run the script.** Use the exact command in the Script contract section. Required output: the exit code and the full JSON from stdout (exit 0 or 1), or the one-line error from stderr (exit 2).
5. **Map the result.** Required output: one table row per slide from the `slides` array, in the order the script returns (ascending slide file number). Add a `flags` column that joins the flag names with commas, or writes `none`.
6. **Write the summary.** Required output: the four summary lines in the Output contract. Use the values from `summary` and `slide_count`. Do not estimate.
7. **State what was not checked.** Required output: a line saying that slide order is by file number, not by presentation order, and that a bullet is a counting rule, not a judgement of the text.

## Threshold table (working values, not an industry standard)

| Check | Condition | Flag name | Default |
|---|---|---|---|
| Text density | total words on the slide (all text runs, title included) greater than the limit | `dense_text` | 60 words |
| Bullet count | bullet paragraphs on the slide greater than the limit | `too_many_bullets` | 7 paragraphs |
| Title | no title placeholder (type `title` or `ctrTitle`) with non-blank text | `missing_title` | required |
| Notes | notes body text missing | not a flag; reported as `notes_present` and counted in `slides_without_notes` | reported only |

Exit code: 1 when `findings_count` is above 0, which means at least one of the three flags fired. A slide without notes alone does not change the exit code.

Bullet paragraph rule: a paragraph counts as a bullet when it sits in a shape that is not the title placeholder, it has non-blank text, and its paragraph properties do not contain `a:buNone`. A plain text-box paragraph without `buNone` is counted too. Table cells, field text (slide numbers, dates) and speaker notes are not counted.

## Output contract

Summary block (exact headings, in this order):

```
## Density report: <input file name>
Thresholds: max_words=<n>, max_bullets=<n>
Slides: <slide_count>   Findings: <findings_count>   Slides flagged: <summary.slides_flagged>   Slides without notes: <summary.slides_without_notes>
```

Table (exact columns, one row per slide):

```
| Slide | Words | Bullets | Title | Notes | Flags |
|---|---|---|---|---|---|
| 2 | 190 | 10 | no | no | dense_text, too_many_bullets, missing_title |
```

The `Title` and `Notes` cells contain `yes` or `no`, from `title_present` and `notes_present`. The `Slide` cell is the `slide` key.

Error block, used only when the exit code is 2: one line `Error: <message from stderr>`, with no table.

## Script contract (type A)

- Path: `scripts/pptx_density.py`, relative to the skill folder.
- Command: `python -I scripts/pptx_density.py <deck.pptx> [--max-words N] [--max-bullets N]`
- Arguments: one positional path. `--max-words` and `--max-bullets` are integers of 1 or more; default 60 and 7. Anything else is a usage error.
- Stdout on exit 0 or 1: one JSON document with keys `tool`, `input` (file name only), `thresholds` (`max_words`, `max_bullets`), `slide_count`, `slides` (each with `slide`, `words`, `bullets`, `title_present`, `notes_present`, `flags`), `findings_count`, and `summary` (`slides_flagged`, `slides_without_notes`).
- Stderr on exit 2: one line of JSON, `{"error": "<message>"}`.
- Exit codes: 0 no findings. 1 one or more findings. 2 usage or input error.
- Caps (working values): input file 2 MB; 300 zip entries; 20 MB total uncompressed; 4 MB per entry; compression ratio 100 to 1; 200 slides; XML nesting depth 64.
- The script writes no files. It opens the input read only, makes no network calls and runs no subprocess.

## Refuse or stop when

- The file is not a zip container, or `ppt/presentation.xml` is missing.
- The file is larger than 2 MB, or has more than 300 zip entries, or more than 20 MB uncompressed.
- Any entry expands beyond 4 MB, or has a compression ratio above 100 to 1.
- Any slide or notes XML contains a `<!DOCTYPE` or `<!ENTITY` declaration.
- The XML is malformed, not UTF-8, or nested deeper than 64 levels.
- The package has no `ppt/slides/slideN.xml` entries, or more than 200 slides.
- The user asks you to edit, repair, translate or rewrite the slides. This skill only reports.
- The user asks you to judge design, images or colour. Say that the audit covers text and structure only.

## Notes on reading the result

- A slide number is the file number in `ppt/slides/slideN.xml`. It can differ from the presentation order if slides were moved. Say so when a reader will use the numbers to find slides.
- The notes check reads the body placeholder of the notes page linked from each slide. A notes page with only a slide image and a slide number counts as no notes.
- Word counts split on whitespace, so a CJK or Thai paragraph without spaces counts as one word per run. Flag this in the report when the deck is not in a space-separated language.
- On exit 2 there is no table and no JSON. Report the stderr line under the Error block and stop; do not retry with other limits.
- A deck with zero flags still gets the full table and the summary block, with `Findings: 0`.
