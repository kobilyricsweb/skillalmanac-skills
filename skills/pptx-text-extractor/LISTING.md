# pptx-text-extractor

## One line

Reads a .pptx deck and prints each slide's title, body text, table cells and speaker notes in slide order, with counts and a flag for empty slides.

## What it does

The script opens the .pptx as a zip package and reads only the parts it needs: the presentation part, its relationship file, each slide part and the notes part linked from each slide. Slides are taken in the order listed in the presentation's slide list, so a slide moved in the editor keeps its new position. Within a slide, the title is the first title placeholder with text. Every other text shape, including text boxes and grouped shapes, is body text, except footer, date and slide-number placeholders, which are skipped. Table cells are joined per cell and each table is kept only when at least one cell has text. Speaker notes come from the body placeholder of the linked notes part.

The output is Markdown by default, with one heading per slide, labeled Body, Table and Notes blocks, and an explicit (none) marker so an empty section is visible. A plain-text variant drops the heading marks and the table separator row. Output can go to stdout or to a new file that the script creates exclusively, so an existing file is never replaced.

The script also reports the slide count, the numbers of empty slides, the number of tables and the number of slides with notes. A slide with notes but no title, body or table text is counted as empty.

## When to use

Use it when a deck's text is needed as editable text for a summary, a transcript, a review or a search index, and the deck is an ordinary .pptx under 2 MB. It is also useful for checking a deck for slides that have no content before it is shared.

## When not to use

Do not use it to change, create or re-export a deck. Do not use it for text inside pictures, charts, SmartArt or embedded objects, which the script does not read. Older or related formats such as .ppt, .key and .odp are not handled. Encrypted decks and decks with a DTD are refused.

## Requirements

Python 3.9 or newer. The standard library only. No network access, no subprocess calls and no installed packages. The skill folder includes a smoke-test helper that builds a small deck in a temporary folder at run time.

## Example

Summary line on stderr for the smoke-test deck (exit code 0):

```
{"slide_count": 3, "empty_slides": [], "table_count": 1, "slides_with_notes": 2}
```

Rendered text on stdout, pasted from the same run:

```
# Slide text: smoke_deck.pptx

## Slide 1: Quarterly review

Body:
Prepared for the sales team
Q3 results

Notes:
Open with the Q3 summary.

## Slide 2: Regional sales

Body:
North grew fastest

Table 1:
| Region | Sales |
| --- | --- |
| North | 120 |
| South | 95 |

Notes:
Mention the South dip.

## Slide 3: Next steps

Body:
Confirm Q4 targets
Review hiring plan

Notes:
(none)
```

## Limits

The script reads text in XML order inside each slide, which is not always the visual reading order on the page. Hidden slides are read like any other slide and are not flagged. A slide with its title in a plain text box is reported as having no title, because only title placeholders count. Text in pictures, charts, SmartArt, embedded workbooks and comments is not read. Markdown output escapes only the pipe character in table cells; other Markdown syntax in the deck text is copied as written. The script does not check whether the deck's content is accurate, current or appropriate, does not verify the deck against its original on screen, and does not detect personal data. Input is capped at 2 MB, the package at 400 entries and 20 MB uncompressed, and each XML part at 5 MB; decks above these caps are refused rather than partly read.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
