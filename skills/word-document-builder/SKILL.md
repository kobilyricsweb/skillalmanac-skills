---
name: word-document-builder
description: Builds a finished-looking .docx (report, memo, proposal, minutes, guide, price list, letter) from notes or Markdown, then verifies the saved file with a stdlib script that reads the .docx XML (A4/Letter, title and author properties, heading levels, header rows, captions, alt text, page numbers). Use when the user wants a Word file or .docx to print or send. Do not use for PDFs, Google Docs, slide decks, spreadsheets, accepting or editing tracked changes in an existing file, or when the user only wants text in chat.
license: Apache-2.0
compatibility: The inspector script needs Python 3.9 or newer, standard library only, and no network. Generating the .docx needs one of the libraries named in references/generators.md, or Pandoc. Without Python, use the manual checks in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.2.0"
  network: none
---

# Word document builder

Goal: a .docx that looks finished when opened (real styles, set properties) and a saved-file check. Facts come only from the user.

## 0. Decide the size of the job

- User wants text, an outline or an answer, not a file: answer plainly in chat; skip this skill.
- Short single-page note or memo: do steps 2-3 and 5 only; skip the contract file and contents list. Inspector is optional.
- Existing .docx to audit: run the inspector (step 5) and report findings; do not rewrite or save over the file unless asked.
- Otherwise do all steps.

## 1. Inputs (ask once, only what is missing)

Type, paper (default A4 unless the user writes in US context or says Letter), title, author. If the author is unknown leave Author empty or use the name the user gave; never invent a person. Optionally copy [assets/contract.example.json](assets/contract.example.json) to `contract.json` and edit. Defaults per type: [references/style-contract.md](references/style-contract.md) (read the chosen type only).

| Rule | Report / proposal | Memo / minutes / letter |
|---|---|---|
| Title paragraph (style Title) + Title/Author properties | yes | yes |
| Max heading depth | 3 | 2 |
| Numbered headings | only if source numbers them, or doc over 8 pages | no |
| Contents field | only if over 8 pages | no |
| Tables: header row repeating, caption above, one style | yes | yes |
| Figures: alt text, caption below | yes | yes |
| Footer PAGE field | yes | yes |

Working values: margins at least 2.0 cm, body 11 pt, headings 16/13/12 pt, headings at most 12 words, alt text under 125 characters, tables at most 7 columns in portrait.

## 2. Normalise the source

One title only. No level jumps (H1 then H3 becomes H1 then H2). Never add numbers, sections or claims the source lacks. Keep the user's own lead-in lines and wording; do not replace them with captions of your own, add a caption beside them.

## 3. Missing facts: two different cases

- File will be sent or printed as is (default): fill gaps with plain wording that reads as finished: owner cell "Unassigned", missing value "Not provided", date "TBD". Never guess.
- User asked for a draft, or will edit: use `[NEEDED: what]` markers.
- Either way, list every gap in your reply. Conflicting figures: keep the user's figures, show both, flag the conflict in the reply, do not pick one silently.

## 4. Generate

Use styles (Title, Heading 1-3, Caption, a table style), never bold-plus-size. python-docx or Pandoc; gaps per library are in [references/generators.md](references/generators.md). Set Title and Author properties (python-docx defaults leave author "python-docx": overwrite it). Set page size explicitly (python-docx defaults to Letter). Footer with a PAGE field. Header row marked repeating. Real bullets via list styles. No empty spacer paragraphs; use paragraph spacing. Code: monospace 9-10 pt in a keep-together bordered paragraph or table cell.

Save to disk, then check the saved file, not the in-memory object.

## 5. Inspect

```bash
python scripts/docx_inspect.py out.docx --contract contract.json
```

Without a contract it still prints findings. Exit 0 = pass, 1 = violations (listed), 2 = unreadable. Fix the generator and re-run until 0. Do not loosen the contract to pass unless the user changed the requirement. Do not read the script. Note the check reads XML only; it cannot see rendering, so do not claim page fit.

## 6. Reply (obey the user's word limit first)

If the user gave a length limit for the reply or notes (for example 200 words), stay under it: count words and cut the "Not checked" and "Built by me" lines before exceeding it. Default shape, short:

```
File: <path>  Type: <type>  Paper: <A4|Letter>  Inspector: exit <n>
From the source: <1 line>   Added by me: <1 line>
Gaps / conflicts: <each one and where>
Not checked: rendering in Word, fonts, alt-text accuracy
```

## Limits

- Heading detection uses style names and outline levels; custom heading styles with neither are invisible.
- Contents field is detected, not refreshed. Paper size matches within 60 twips.
- Tested on English LTR documents; right-to-left or merged documents are untested.
