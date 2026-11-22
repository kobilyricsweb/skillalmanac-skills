# Page Title and Meta Description Checker

## One line

Runs a stdlib-only script over a CSV of page titles and meta descriptions and reports empty tags, length limits, a pixel-width proxy, duplicates across rows and titles that repeat their description.

## What it does

The skill takes one CSV file with a header row that includes the columns url, title and description. Other columns are ignored. The script trims each value, measures character length, adds up an approximate pixel width from a fixed per-character table, and compares every row with every other row for repeated titles and repeated descriptions. Each broken rule becomes one finding with the row number, the URL as written in the file, a code and a short detail string. The output is JSON by default or a fixed-width table, and the exit code says whether anything was found. The script never fetches a page and never writes a file, so an audit of an export can be repeated without changing the export. The agent then turns the findings into a list of rows that need a new title or description, with one fix hint per finding. It does not write replacement tag text, which stays with the person who owns the page.

## When to use

Use it on a spreadsheet or crawler export before a batch of pages goes live, or after a template change that may have altered many titles at once. It is useful when the same title appears on several URLs, when a description field is empty, or when a title is too short to say what the page is.

## When not to use

Do not use it to crawl a live site, to see the snippet a search engine will show, or to judge keyword choice. The pixel figure is a proxy, and the length limits are working values chosen for this skill, so they are not a search engine specification. It also does not write new titles or descriptions.

## Requirements

Python 3.9 or later, standard library only. No network access, no extra packages. The input must be UTF-8 CSV, at most 2 MB, with the three required columns in the header row.

## Example

Run on the 8-row smoke fixture with the table format, the output is:

```
row   code                     url                                          detail
1     DUPLICATE_TITLE          /guides/home-buyers                          title shared with rows 2
1     DUPLICATE_DESCRIPTION    /guides/home-buyers                          description shared with rows 8
2     DUPLICATE_TITLE          /guides/first-time-buyers                    title shared with rows 1
3     EMPTY_DESCRIPTION        /tools/mortgage-calc                         description is empty
4     TITLE_TOO_LONG           /blog/everything-about-buying                90 chars, limit 60
4     TITLE_PIXELS_OVER        /blog/everything-about-buying                about 693 px, limit 580
5     TITLE_TOO_SHORT          /blog/rates                                  5 chars, minimum 25
6     DESCRIPTION_TOO_LONG     /blog/closing-costs                          207 chars, limit 160
6     DESCRIPTION_PIXELS_OVER  /blog/closing-costs                          about 1523 px, limit 920
7     DESCRIPTION_TOO_SHORT    /about                                       29 chars, minimum 70
7     TITLE_EQUALS_DESCRIPTION /about                                       title and description are the same text
8     DUPLICATE_DESCRIPTION    /contact                                     description shared with rows 1
rows: 8  findings: 12  status: findings
```

## Limits

- Length limits (60, 25, 160 and 70 characters) and pixel limits (580 and 920 px) are working values, not published search engine specifications.
- The pixel width is an approximation from a fixed character table. It does not model real fonts, kerning or the rendering used in search results.
- Duplicate checks compare only rows inside the one file. A title that is unique in the file may still repeat on another site section.
- Input over 2 MB, invalid UTF-8 or a missing required column stops the run with exit code 2.
- Blank records are skipped, so row numbers count data records only.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
