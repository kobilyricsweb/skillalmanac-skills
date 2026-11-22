## Contents

- Why styles, not formatting
- Page setup
- Heading hierarchy and numbering
- Report, memo and proposal skeletons
- Tables
- Figures, captions and alt text
- Properties, footers, contents field
- Markdown to Word mapping

## Why styles, not formatting

A Word file is read by three audiences that all depend on styles: the Navigation pane and contents field (headings), screen readers (headings, header rows, alt text) and the next editor (change one style, change every paragraph). A paragraph that merely looks like a heading (bold, 16 pt, Normal style) is invisible to all three. The inspector therefore treats only style names and outline levels as headings.

## Page setup

| Item | Default | Note |
|---|---|---|
| Paper | A4 outside the US and Canada; Letter inside | Ask once; never mix within a file |
| Orientation | Portrait; landscape only for a section holding a wide table | Section break before and after |
| Margins | 2.54 cm (1 in) all sides; floor 2.0 cm | Below 2.0 cm printers clip and readers tire |
| Body | 11 pt, line spacing about 1.15, 6-8 pt after | Sans-serif or a screen-friendly serif; font must exist on the reader's machine or Word substitutes it |
| Headings | 16 / 13 / 12 pt, bold, keep-with-next on | Keep-with-next stops a heading alone at a page bottom |
| Table text | 9-10 pt | Smaller is unreadable on print |

## Heading hierarchy and numbering

- Title is a separate style, used once, on the first page. It is not Heading 1.
- Heading 1 is a main section. No skipped levels (1 then 3). Depth 3 for most documents, 4 only for long manuals.
- Headings are noun phrases or plain statements, at most 12 words, no trailing full stop.
- Every heading has content before the next heading of the same or higher level. A heading directly followed by its first subheading is fine.
- Numbering: "1", "1.1", "1.1.1". Best done by the template's multilevel list tied to Heading 1-3, so numbers follow reordering. Typed numbers work and are detected (`numbering: text`), but renumbering is manual. Do not number Title, front matter or appendices without saying so. Use all or none: mixed numbering is a finding.

## Report, memo and proposal skeletons

Report: Title, author/date line, contents field (over 8 pages), 1 Summary (half a page, findings and recommendation first), numbered body sections, N Conclusions or Recommendations, Appendices.

Memo: no contents, no numbering, depth 2 at most. Header block as four lines (To, From, Date, Subject), then the decision or request in the first paragraph, then background, then options or next steps. One to two pages.

Proposal: Title, short cover block (client, date, version), 1 Summary of the offer, 2 Problem and scope, 3 Approach, 4 Timeline, 5 Price (a table), 6 Terms, 7 Next step. Prices, terms and legal wording come only from the user; unknown items stay `[NEEDED: ...]`.

## Tables

- Style: one table style across the document, from the template. "Table Grid" is the safe built-in default when the template has nothing better.
- First row marked as a repeating header row (`w:tblHeader` in the row properties). Without it a table that crosses a page loses its column labels and screen readers lose the header association.
- Caption directly above, text starting "Table N". Keep the caption paragraph with the table (keep-with-next).
- At most 7 columns in portrait. Wider: split, transpose, or give that section landscape.
- Align numbers right, text left. Same number of decimals per column. Units in the header, not in each cell.
- No merged cells in data tables; they break navigation for assistive technology.
- Do not use a table for layout.

## Figures, captions and alt text

- Picture in its own paragraph, caption directly below, text starting "Figure N".
- Alt text lives in the `descr` attribute of the picture's `wp:docPr` element. Describe what the picture shows and why it is there, under about 125 characters, no "image of". A chart's alt text states its main takeaway.
- A purely decorative picture is marked decorative (an `a14:decorative` extension on `docPr`), which the inspector accepts instead of alt text.
- The agent can write alt text only from what it was told or can see; mark it as a draft in the report.

## Properties, footers, contents field

- Core properties Title and Author set to real values (not "Document1", not the tool name). Subject and keywords optional.
- Footer with a PAGE field; "Page X of Y" uses PAGE and NUMPAGES fields. A confidentiality marking goes in the header or footer only if the user supplied it.
- Contents field: levels 1-3. Word fills it on field update; a generator that inserts the field usually leaves it empty until the user updates (right-click > Update Field, or F9). Say so in the report.

## Markdown to Word mapping

| Markdown | Word |
|---|---|
| Front matter title | Title style and Title property |
| `#`, `##`, `###` | Heading 1, 2, 3 (after normalising, see workflow step 2) |
| Paragraph | Normal (or Body Text) |
| `-` / `1.` lists | List Bullet / List Number styles, not typed characters |
| Pipe table | Table with header row; caption from the line above if present |
| `![alt](file)` | Picture with the alt text carried to `descr`; empty alt means ask or mark decorative |
| Fenced code | Monospace style, 9-10 pt, no syntax colours needed |
| `[text](url)` | Hyperlink with the same visible text |
| Footnote | Real Word footnote if the library supports it; otherwise endnote section |
| Horizontal rule | Dropped, or a page break if the user meant a break |
