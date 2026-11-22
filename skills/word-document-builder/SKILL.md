---
name: word-document-builder
description: Builds a well-structured .docx (report, memo, proposal) from Markdown or notes using a written style contract (heading hierarchy, numbered sections, table style, captions, alt text, page setup, properties), then verifies the saved file with a script that reads the .docx XML and prints JSON. Use when the user asks for a Word document, .docx, report, memo or proposal file, or wants notes or Markdown turned into Word. Do not use for PDFs, Google Docs, slide decks, spreadsheets, or editing tracked changes in an existing file.
license: Apache-2.0
compatibility: The inspector script needs Python 3.9 or newer, standard library only, and no network. Generating the .docx needs one of the libraries named in references/generators.md, or Pandoc. Without Python, use the manual checks in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Word document builder

Turn notes or Markdown into a .docx that has real structure (styles, not look-alike formatting), then prove the saved file matches a contract. The generator library is a free choice; the contract and the check are not.

## Who supplies what

| The user supplies | The agent generates | The agent never invents |
|---|---|---|
| Content, claims, figures, names, dates | Heading structure, numbering, contents list, captions | Numbers, quotations, citations, names, dates |
| Document type, audience, language | Table layout and header rows, page numbers, properties | Legal wording, signatures, approvals |
| Paper size (A4 or Letter), template or brand file | Alt-text drafts for images (flag them as drafts) | Pictures or data for a gap |
| Title and author for the properties | A list of every gap found | A fix for a gap the user can answer |

Missing facts become `[NEEDED: what is missing]` in the text, never a guess. Ask for paper size and template once, up front; everything else has a default below.

## Contract

Fix the contract before generating. Start from [assets/contract.example.json](assets/contract.example.json), edit it, save it next to the output as `contract.json`. Defaults by document type, rationale and style names are in [references/style-contract.md](references/style-contract.md); read the section for the chosen type only.

| Rule | Report | Memo | Proposal |
|---|---|---|---|
| Title style paragraph + Title/Author properties | yes | yes | yes |
| Heading depth (max) | 3 | 2 | 3 |
| Numbered headings | yes | no | yes |
| Contents field | yes, if over 8 pages | no | yes, if over 6 pages |
| Tables: repeating header row, caption above, one style | yes | yes | yes |
| Figures: alt text, caption below | yes | yes | yes |
| Footer page number | yes | yes | yes |
| Length target | any | 1-2 pages | any |

Working values, not measured optima: margins at least 2.0 cm, body 11 pt, headings 16/13/12 pt, no heading longer than 12 words, alt text under about 125 characters.

## Workflow

```
- [ ] 1 Collect missing inputs and write the contract
- [ ] 2 Normalise the source structure
- [ ] 3 Generate with styles, never manual formatting
- [ ] 4 Save and re-open the file as a file
- [ ] 5 Run the inspector against the contract
- [ ] 6 Fix, re-run, then report
```

1. **Inputs.** Document type, audience, paper size, template (if any), title, author. Write `contract.json`.
2. **Normalise.** Exactly one document title. Markdown `#` is Heading 1 only if the title is separate (front matter or first line); otherwise promote it to Title and shift the rest up. No level jumps: a `###` after `#` becomes `##`. Split headings over 12 words. A heading with no body gets text or is removed.
3. **Generate.** Use paragraph styles (Title, Heading 1-3, Caption, a table style from the template), not bold-plus-size. Number headings with the template's multilevel list when the library can; typed numbers ("2.1 Scope") are accepted by the checker but break on reorder, so say which you used. Tables: header row marked as repeating, caption above, no table wider than 7 columns in portrait (switch that section to landscape or split). Figures: alt text, caption below. Code blocks: a monospace style at 9-10 pt. Links keep readable text, not "click here". Set Title and Author properties. Add a footer with a PAGE field. Library choices and the gaps each one leaves (alt text and header rows usually need a small XML tweak) are in [references/generators.md](references/generators.md).
4. **Save and re-open.** Write the file to disk, then run the next step on the saved file, not on the in-memory object.
5. **Inspect.**

```bash
python scripts/docx_inspect.py report.docx --contract contract.json
```

   Exit 0 means every rule passed; 1 means violations (listed under `contract.violations`); 2 means the file or contract could not be read. Do not edit the script or loosen the contract to make it pass, unless the user changed the requirement.
6. **Fix, report.** Fix the generator, regenerate, re-run until exit 0. Then do the checks the script cannot do. Without Python run these by hand in Word: Navigation pane (headings nest as intended), Review > Check Accessibility, File > Info (Title, Author), Print Preview (tables do not split badly), right-click the contents field > Update Field.

Report in this fixed shape:

```
File: <path>  Type: <report|memo|proposal>  Paper: <A4|Letter>
Contract: <path>  Inspector: exit <0|1>, violations <n>
Built from the user: <what came from the source>
Built by me: <structure, captions, alt-text drafts>
Gaps left: <every [NEEDED: ...] with its location>
Not checked: <rendering in Word, contents field page numbers, fonts present, alt-text accuracy>
```

## Inspector output contract

`scripts/docx_inspect.py` prints one JSON object (ASCII, indent 2) and nothing else on stdout; errors go to stderr with exit 2. Run it; do not read it unless a result looks wrong.

| Key | Content |
|---|---|
| `schema_version`, `tool`, `file`, `ok` | `ok` is false only when a contract rule failed |
| `contract` | `null`, or `{rules_checked, violations: [{rule, severity, detail}]}` |
| `properties` | `title`, `author` from core properties |
| `sections[]` | `paper` (A4, Letter, Legal, A3, custom), `orientation`, `width_cm`, `height_cm`, `margins_cm` |
| `headings[]` | `element`, `level`, `text`, `style`, `numbered`, `numbering` (field, text, none); Title excluded |
| `empty_sections[]` | heading with no content before the next heading of the same or higher level |
| `tables[]` | `rows`, `cols`, `style`, `header_row`, `caption` |
| `images[]` | `alt`, `has_alt`, `decorative`, `caption`, `kind` |
| `captions[]`, `toc`, `footer_page_numbers`, `placeholders[]`, `tracked_changes`, `words` | as named |
| `findings[]` | `{code, severity: warn, detail}` always produced, with or without a contract |

Contract keys (all optional; unknown keys are rejected): `title_required`, `author_required`, `max_heading_depth`, `h1_min`, `h1_max`, `numbered_headings`, `heading_max_words`, `allow_empty_sections`, `table_header_row`, `table_styles_allowed`, `table_captions`, `figure_captions`, `alt_text`, `paper`, `orientation`, `margin_min_cm`, `footer_page_numbers`, `toc`, `no_placeholders`, `no_tracked_changes`.

## Limits

- The script reads XML only. It cannot see rendering, fonts, page breaks, whether a picture is meaningful, or whether alt text is accurate.
- Heading detection uses style names (Title, Heading 1-9 in any case or spacing) and outline levels, following `basedOn` chains. Custom heading styles with neither are invisible to it.
- A contents field is detected, not its freshness; page numbers inside it update only when Word updates fields.
- Caption detection is a style name containing "caption", or text starting "Table 3", "Figure 2" and similar, directly before or after the table or picture.
- Pictures inside tables get alt-text checks but no caption check. Legacy VML pictures are checked for `alt` only.
- Paper sizes match within 60 twips. Margins are read from every section; headers and footers are checked only for a PAGE field.
- Fixtures are minimal packages; behaviour on large or unusual files (documents merged from several sources, right-to-left text, content controls beyond basic) is untested.
- Written for English-language report, memo and proposal layouts; contract defaults are conventions, not a standard.
