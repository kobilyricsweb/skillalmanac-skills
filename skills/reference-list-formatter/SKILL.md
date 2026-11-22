---
name: reference-list-formatter
description: Formats reference list entries in APA 7, MLA 9, Chicago author-date or IEEE from BibTeX or CSL-JSON fields, flags the required fields each style needs that are missing, and never invents data, with a script that builds the formatted list plus an in-text string per entry. Use when the user asks to format references, make a bibliography or works cited, convert BibTeX to APA or MLA, fix citation format, cite a book, article, web page, report or ChatGPT, or check which fields are missing. Do not use for managing citations inside a manuscript, finding sources, verifying a source exists, or writing the paper.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual procedure in step 4 using references/style_rules.md.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Reference list formatter

Turn structured source fields into reference entries in one named style, and say exactly which fields are missing. The job is formatting and field validation. It is not looking sources up, and it is not placing citations inside a manuscript.

## Never-invent rule

Every value in an entry must come from the user's fields. If a field is missing, leave it out and report it. Do not complete an author from memory, guess a year, derive a DOI from a title, or "fix" a volume. Do not state that a source exists. If the user wants the gap filled, tell them to look at the source itself (title page, the journal's page, the DOI landing page) and give you the value.

## Workflow

```
- [ ] 1 Fix the style and its manual edition
- [ ] 2 Collect fields (BibTeX, CSL-JSON, or ask)
- [ ] 3 Run the script
- [ ] 4 Resolve every incomplete entry and warning
- [ ] 5 Deliver the list and the report
```

1. **Style.** Ask which of apa, mla, chicago (author-date) or ieee, unless the user named one. The script states the edition it implements in `style_version`; show that line to the user and tell them to confirm it matches their institution's current manual.
2. **Fields.** Best input is a `.bib` file or a CSL-JSON file. If the user pasted formatted references or loose details, write a CSL-JSON file from only what they gave (field map in [references/style_rules.md](references/style_rules.md), section "Input field map"). Supported types: article, book, chapter, web page, report, software including AI tools. Anything else is reported unsupported; do not force it into a nearby type.
3. **Run:**

```bash
python scripts/format_refs.py format sources.json --style apa --out references.txt
```

   Run it, do not edit it to make a check pass. Without `--out` nothing is written. `--out` equal to the source file is refused (exit 2). `--plain` drops the Markdown italics. `python scripts/format_refs.py rules --style apa` prints the required-field table. Exit 0 all complete; 1 something incomplete, unsupported or duplicated; 2 unreadable or empty input.
4. **Resolve.** For each entry in the JSON `entries`:
   - `status: incomplete`: the entry is printed without the missing parts and prefixed `[INCOMPLETE: missing ...]` in `references.txt`. Ask the user for the listed fields. Do not remove the prefix until they are supplied and the script is re-run.
   - `status: error`: unsupported type. Ask for a supported type or tell the user to format it by hand from the manual.
   - `warnings`: act on each (table below).
   - `duplicates`: the later entry is dropped from the list; ask which one is right if the fields differ.
   - `missing_recommended`: mention, do not block.
5. **Deliver** in the fixed shape below. Only after the final run may you call a list complete, and only as "complete as to the fields supplied".

## Warning meanings

| Warning | What to do |
|---|---|
| `invalid-doi` | The DOI was left out of the entry. Ask the user to check it; a valid one is `10.` + 4 to 9 digits + `/` + suffix. |
| `implausible-year` | Year outside 1400 to 2100 or not four digits; ask. |
| `latex-residue` | A backslash survived in the source field; ask for clean text. |
| `title-case` (APA) | Article and chapter titles take sentence case in APA. The script does not change case, because it cannot know proper nouns. Tell the user which titles to lower-case by hand. |
| `no-author`, `no-date` | The style rule for missing author or date was applied (title moves forward, `n.d.`). Confirm that the work really has none. |
| `apa-N-authors`, `chicago-N-authors`, `ieee-N-authors` | The long-list rule was applied; say so. |
| `chicago-ai`, `ieee-software`, `mla-ai-date` | Guidance for AI tools is thin or still changing; see the next section. |
| `article-number` | MLA label for article numbers not verified; ask the user. |

## AI tools

Collect: developer (author), year, tool name, version or date of use, descriptor such as "Large language model" (`genre`), address, and for MLA the prompt text (`description`) and a full date. Use type `software`. Tell the user three things: the manuals' guidance on generated text changes and some prefer an in-text or note acknowledgement to a reference entry; their institution or instructor may set its own rule; and the tool is not a source of facts, so the claims need primary sources. The script gives a pattern, not a ruling.

## Report format

```
Style: <style and style_version from the script>
Entries: <total>, complete <n>, incomplete <n>, unsupported <n>, duplicates <n>
Incomplete: <id: missing fields>, or none
Warnings acted on: <list>, or none
References: <the lines from references.txt, in order>
In-text: <id -> string, for the entries the user will cite>
Not checked: <existence of sources, accuracy of values, italics and hanging indent in the final document, current manual>
```

## Script contract

`scripts/format_refs.py format <source> --style apa|mla|chicago|ieee [--out file] [--plain]` prints one JSON object: `command`, `style`, `style_version`, `input`, `summary` (total, ok, incomplete, error, duplicates, warnings), `ok`, `entries` (id, type, status, formatted, in_text, missing_required, missing_recommended, warnings, optionally duplicate_of), `duplicates`, `references` (final lines in order), `not_checked`. It reads only the source file and writes only `--out`. If Python is not available, build each entry by hand from the template table and the required-field table in [references/style_rules.md](references/style_rules.md), apply the same never-invent rule, and say in the report that the checks were done by eye.

Read the reference file for the template for a type you must write by hand, for the author-count rules, or for the field map. Do not read it in full when the script ran cleanly.

## Limits

- Implements the editions named in `style_version`; manuals change, and this skill does not re-read them. The rule tables were written from the public guides and checked only against the fixtures.
- Chicago notes-bibliography and other styles are out of scope. Chicago 18th edition differences, repeated-author dashes, MLA page numbers in in-text strings, and journals' own house styles are not handled.
- Titles are not re-cased, quotation marks are straight, italics are Markdown asterisks, and hanging indents are for the word processor.
- Name parsing for plain `First Last` BibTeX names assumes the last word is the family name, except for lower-case particles (`van der`); give `Family, Given` when unsure.
- It does not check that sources exist, that values are correct, or that a manuscript cites each entry. For in-text and list reconciliation inside a manuscript use a writing workflow skill instead.
- Languages other than English are formatted with English connectors ("and", "et al.", "ed.").
