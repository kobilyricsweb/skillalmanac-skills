# html-to-markdown

## One line

Converts an HTML fragment or page to Markdown offline, keeping headings, links, lists, code and simple tables, and reports each tag it dropped or kept as plain text.

## What it does

Give it one HTML file and a new output path. The script parses the markup with the standard library HTML parser and drops script, style, navigation, head and title content together with everything inside them. Headings become ATX headings. Anchors become Markdown links, and spaces in their targets are written as percent-encoded spaces. Nested ordered and unordered lists keep their order and indentation. Simple tables become pipe tables whose first row is the header row, and a literal pipe inside a cell is escaped. Pre blocks become fenced code, and blockquotes keep their markers. Any tag outside the mapping keeps its text, is listed with a count, and makes the run exit 1 so the caller notices. Plain text is escaped for the characters Markdown reads as syntax. Nothing is fetched: links and images are written as they appear in the source. The output file is created in exclusive mode, so an existing file is never overwritten and the input file is never written.

## When to use

Use it when copied web content has to land in a Markdown note, a README draft, or a knowledge base, and the headings, links and tables must survive the move. It suits saved pages where a deterministic result matters more than fidelity to the original layout, and where the list of lost tags is useful to the person reviewing the output.

## When not to use

Do not use it to fetch a page by URL, to resolve relative links or images, to sanitize HTML for display on a web page, or to convert spreadsheets, Word files or PDFs. Do not use it for pages whose meaning depends on nested tables, lists inside table cells, or column and row spans, because those are flattened or not applied.

## Requirements

Python 3.9 or newer. No third-party packages, no network access, and no subprocess calls. The input must be UTF-8 text no larger than 2,097,152 bytes.

## Example

Run on the shipped fixture, a short release-notes page that contains a nav, a nested list, a table, a link, an image and a code block. The command was run from the skill folder with the output written to a scratch location outside the skill.

Summary line (stdout):

```
{"bytes_written": 406, "code_blocks": 1, "dropped": {"head": 1, "nav": 1, "script": 1}, "headings": 3, "links": 1, "lists": 2, "status": "findings", "tables": 1, "unsupported": {"img": 1}}
```

Markdown output:

````markdown
# Release notes

Version **2.4** ships with *faster* search. See the [setup guide](docs/setup%20guide.html).

## Changes

- Search results load in half the time
- Export supports `CSV` files
  1. Headers are optional
  2. Dates use ISO format

## Known limits

| Plan | Seats |
| --- | --- |
| Team | 25 |
| Business \| Plus | 100 |

> Thanks to the beta group for testing.

```
npm run build
npm test
```
````

## Limits

- Relative links and images are not resolved, and image alt text is not kept.
- Dropped content is not reproduced. The report gives only tag names and counts, and only for the outermost dropped element.
- Nested tables, lists inside table cells, and column or row spans are flattened or not applied.
- A code block is always fenced with three backticks, so a block that already contains three backticks renders incorrectly.
- Indentation inside code blocks that sit within lists is not preserved.
- Hrefs are copied as written and are not sanitized.
- The script does not check that links resolve, that the output renders like the source page, that the content is accurate, or that it is safe to display.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
