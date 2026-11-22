# Listing page content: reference-list-formatter

**One line:** Formats references in APA, MLA, Chicago or IEEE from BibTeX or CSL-JSON and flags missing fields without inventing any.

## What it does

The skill gives an agent a five-step procedure: fix the style, collect structured fields, run a script, resolve every incomplete entry, deliver the list with a fixed report. `scripts/format_refs.py` reads a `.bib` or CSL-JSON file and prints one JSON report: a formatted line and an in-text string per entry, the required fields each style needs for that source type that are absent, warnings (invalid DOI, implausible year, title case in APA, long author lists), duplicates, and the final sorted list. A documented rule table in `references/style_rules.md` shows every template, the author-count rules and the field map. Missing values are never filled in: an incomplete entry is printed without the part and prefixed `[INCOMPLETE: missing ...]`.

## Capabilities

- Five source types plus AI tools: journal article, book, chapter, web page, report, software
- Four styles: APA 7, MLA 9, Chicago author-date (17th edition rules), IEEE
- Required-field table per style and type (`rules` command), recommended fields reported separately
- Et al. and ellipsis rules by author count, alphabetical order (IEEE keeps input order), a, b year suffixes in APA and Chicago
- DOI check (`10.NNNN/suffix`), duplicate detection by DOI or author, year and title
- `references.txt` written only when `--out` is given

## When to use

You say format my references, make a works cited, convert this BibTeX to APA, how do I cite ChatGPT, or which fields am I missing.

## When not to use

Finding sources, checking that a source exists, placing or reconciling citations inside a manuscript, notes-bibliography footnotes, LaTeX or biblatex compile problems, writing the paper. Neighbouring skills: `academic-paper-workflow` covers the writing flow and `cited-deep-research` ties claims to sources; this one only formats and validates entries from structured fields.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent builds entries by hand from the template table.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both come from the saved fixture runs.

1. `python scripts/format_refs.py format evals/fixtures/good.bib --style apa` (5 entries, all complete):

```
Lee, H., Okafor, C. M., & van der Berg, A. (2020). Sleep timing and exam performance in first-year students. *Journal of Student Health*, *12*(3), 45–67. https://doi.org/10.1000/jsh.2020.045
Moreno, L. (2018). *Field Methods for Small Teams* (2nd ed.). Harbor Press.
Park, M.-J. (2019). Writing the methods section. In A. Silva & T. Brown (Eds.), *Handbook of Applied Research Writing* (pp. 101–118). Meridian Books.
*Tips for better sleep*. (2022, May 12). Health Library. https://example.org/sleep-tips
World Health Organization. (2021). *Global sleep health report* (Report No. 7). https://example.org/reports/sleep-2021
```

2. `python scripts/format_refs.py format evals/fixtures/t2_chatgpt.json --style mla`:

```
"Describe the main causes of the 1929 stock market crash" prompt. *ChatGPT*, Mar 14 version, OpenAI, 8 Mar. 2023, chat.openai.com/chat.
```

In-text string for that entry: `("Describe the main causes...")`. A `bad.bib` run exits 1 and reports: missing volume (Diaz), missing author and year, a thesis as unsupported, one duplicate dropped, an invalid DOI left out.

## Limits

- Implements the editions named in the report; manuals change and are not re-read by the script.
- No Chicago notes-bibliography, no Chicago 18th edition differences, no repeated-author dashes.
- Titles are not re-cased; quotation marks are straight; italics are Markdown asterisks.
- It does not check that a source exists or that a value is correct.
- AI-tool guidance is thin and changing; the entry is a pattern, flagged for confirmation.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL and 0 WARN, 10 script fixture cases pass with expected outputs read by hand. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, human review, comparison against the live manuals.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Paste a BibTeX file with five entries; ask for APA.
2. Run the script: three complete lines, one flagged `[INCOMPLETE: missing year]`.
3. The agent asks for the year instead of reading it from the key.
4. Re-run with the year supplied; show the final list and the in-text strings.
5. Switch to MLA with `--style mla`; show the ChatGPT entry and the confirm-with-your-manual note.

## FAQ seeds

- Will it look up my sources or fill in missing details? No. It only formats what you give it and lists what is missing.
- Does it check that a DOI or source is real? It checks the DOI shape only.
- Does it work with Zotero or Mendeley exports? If they export BibTeX or CSL-JSON, yes.
- How do I cite ChatGPT? It prints a pattern for the style and tells you to confirm with your manual and instructor.
- How is it different from academic-paper-workflow? That skill covers the writing process; this one formats and validates reference entries.
- Does it need network access? No.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
