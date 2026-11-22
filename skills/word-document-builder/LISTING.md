# Listing page content: word-document-builder

**One line:** Builds a structured .docx report, memo or proposal from notes, then checks the saved file against a style contract.

## What it does

The skill fixes a style contract first (title, heading depth and numbering, table style and header rows, captions, alt text, paper size, margins, properties, page numbers), splits the work into what the user must supply and what the agent may generate, and builds the file with styles instead of manual formatting. The generator is the agent's choice (Pandoc, python-docx, docx for JavaScript, a template, and others are compared in a reference). After saving, `scripts/docx_inspect.py` opens the .docx as a zip of XML, measures it, compares it with the contract and prints strict JSON. Missing facts become `[NEEDED: ...]` markers and are listed in a fixed report; nothing is invented.

## Capabilities

- `scripts/docx_inspect.py FILE.docx [--contract C.json]`: JSON with properties, page setup, heading hierarchy (with numbering kind), empty sections, tables (rows, columns, style, header row, caption), images (alt text, decorative, caption), contents field, footer page number, placeholders, tracked changes, findings, and contract violations
- 20 contract keys, unknown keys rejected; exit 0 pass, 1 violations, 2 unreadable input
- A contract template, default values per document type, a Markdown-to-Word mapping table and a list of gaps each generator typically leaves
- A fixed report: built from the user, built by the agent, gaps left, not checked

## When to use

You ask for a Word document, .docx, report, memo or proposal, or for notes or Markdown to become Word, or you want a generated .docx checked for heading order, header rows, alt text, captions and properties.

## When not to use

PDFs, Google Docs, slide decks, spreadsheets, and editing tracked changes in an existing file. Difference from a general Word-file skill: this one centres on a written contract and a read-only verification script, not on editing arbitrary existing documents.

## Requirements

Python 3.9 or newer for the inspector (standard library only, no network). A generator for the file itself: Pandoc, python-docx, docx (npm) or another listed option. Without Python the agent follows the manual Word checks in the skill.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both are saved fixture runs of the inspector (`python evals/run_fixtures.py`), not agent runs; no with-skill agent run exists yet.

1. A conforming document: `docx_inspect.py good.docx --contract assets/contract.example.json` gives exit 0, `ok: true`, no violations, 4 numbered headings, 1 table (3 rows, 2 columns, style "Table Grid", header row, caption), 1 image with alt text and caption, paper A4, contents field and footer page number present.
2. A broken one: `docx_inspect.py bad.docx --contract assets/contract.example.json` gives exit 1 and 14 violations: title_required, author_required, numbered_headings, allow_empty_sections, table_header_row, table_styles_allowed, table_captions, figure_captions, alt_text, paper, margin_min_cm, footer_page_numbers, toc, no_placeholders. Findings also flag a skipped heading level (Heading 1 then Heading 3), the empty "Results" section, and Letter paper with 1.27 cm margins.

## Limits

- XML only: no rendering, fonts, page breaks, or judgement of alt-text quality.
- Heading detection needs Title or Heading N style names or outline levels.
- Contents field is detected, not its freshness.
- Caption detection is by style name or leading "Table N" / "Figure N" text next to the object.
- Fixtures are minimal packages; behaviour on large real-world documents is untested.
- Contract defaults are conventions and working values, not a standard.

## Evidence

See `VERIFICATION.md`. Static lint: 0 FAIL, 0 WARN. Script fixtures: 9 of 9 cases pass. Not tested: any agent run with or without the skill, trigger behaviour, native discovery, cross-tool use, opening the output in Word, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste notes with a title, three sections, a table and a picture; the agent asks paper size and who the author is, writes `contract.json`.
2. The agent generates the .docx with styles; first inspector run exits 1 (picture has no alt text, header row missing).
3. The agent fixes the generator, re-runs: exit 0.
4. The report shows what came from the notes, what the agent built, and one `[NEEDED: ...]` gap for a missing date.

## FAQ seeds

- Does it need Word installed? No. The script reads the file's XML; checking how it looks in Word is listed as not checked.
- Which library should I use? The skill names options and when each fits; any can pass the contract.
- Does it work with my company template? Yes if the template's style names are used; the contract's table style list can be set to the template's.
- Will it make up numbers or dates? The rule is no; gaps become `[NEEDED: ...]` markers. Efficacy has not been measured.
- Does it send my document anywhere? No network is used.
- Can it check a document I did not generate? Yes, the inspector reads any .docx; fixing it is outside this skill's tested scope.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet; accountable editor: Global Media Holdings.
