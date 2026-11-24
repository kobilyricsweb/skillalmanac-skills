---
name: ieee-citation-format
description: "Formats IEEE references and in-text numbers from structured source data, and checks a pasted IEEE reference list against the current IEEE Reference Guide. Use when the user says format my references in IEEE style, number my citations in order of first citation, is this IEEE reference correct, or fix my reference list. Do not use for other styles such as ACS, Vancouver, AMA or Harvard, BibTeX or LaTeX files, finding sources, or checking that a source exists."
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  tier: free
  author_model: claude-sonnet-5-5
  accountable_editor: Kobi Eliraz (Global Media Holdings)
  version: "0.1.0"
  network: none
---

# IEEE citation format

Produce a numbered IEEE reference list and the matching in-text numbers from source data, or audit a pasted list. Rules come from the IEEE Reference Style Guide for Authors, version V 3.28.2025, read 2026-11-24 (details and URL in [references/ieee-rules.md](references/ieee-rules.md)). The guide changed in 2025: a run of citations is no longer written with a dash.

## Boundary rule

The skill formats what the user supplies. It does not look up sources, confirm that a DOI resolves, or invent journal or conference abbreviations: abbreviations are used only when the user supplies them. Other styles are out of scope; name the right style and stop.

## Workflow

```
- [ ] 1 Collect the sources and the order in which the manuscript cites them
- [ ] 2 Write the input JSON (never retype data from memory)
- [ ] 3 Run format (new list) or verify (pasted list)
- [ ] 4 Resolve every error; read every warning
- [ ] 5 Deliver the list and the in-text text, then report
```

1. **Collect.** For each source: type (`journal`, `book`, `chapter`, `conference`, `web`), every author with given and family names, title, year, and the type fields in [references/input-and-codes.md](references/input-and-codes.md). Ask for what is missing: journal abbreviations, conference names as printed in abbreviated form, volume, issue, pages or article number, DOI, accessed date for web pages. Output of the step: one record per source.
2. **Cited order.** List the in-text citations in manuscript order, each as a group of source ids. Output: the `citations` array. Numbers follow first citation, not alphabet; a source cited again keeps its number.
3. **Run** from the skill folder:

```bash
python scripts/ieee_format.py format <input-file> --text-out <list-file> --output <report-file>
python scripts/ieee_format.py verify <list-file> --manuscript <manuscript-file> --output <report-file>
```

   Add `--ascii` to get straight quotes and hyphen page ranges. Both output paths must not exist and must not be the input. Exit 0 no error, 1 at least one error, 2 usage or input problem.
4. **Resolve.** Fix every `error` in the input (or the pasted list) and re-run. Never edit the script to pass. For warnings, apply the table below.
5. **Deliver** the numbered list, and the manuscript with citation markers replaced when asked, then the report below.

## Rules the script applies (full table with sources in references/ieee-rules.md)

| Topic | Rule |
|---|---|
| In-text | `[3]` inside punctuation; a run of consecutive numbers is written out: `[2], [3], [4]`, never `[2]-[4]`; locator inside the brackets: `[3, pp. 5-10]` |
| Narrative | `Smith [4]`; two names `Brown and Jones [5]`; three or more names `Wood et al. [7]` |
| Authors | initials before surname: `J. K. Author`; no comma before Jr.; two: `A and B`; three to six: `A, B, and C`; more than six: first author plus `et al.` |
| Journal | `"Title," Abbrev., vol. 36, no. 4, pp. 3101-3112, Jul. 2021, doi: 10.x/y.`; one page `p.`; no pages and an article number: `Aug. 2007, Art. no. 061103.`; one-word titles are not abbreviated |
| Months | Jan. Feb. Mar. Apr. May Jun. Jul. Aug. Sep. Oct. Nov. Dec.; two months `Jul./Aug.` |
| Status | `to be published` (never `to appear in`); `submitted for publication` |
| Book | `Title, 2nd ed. City, ST, USA: Publisher, year.`; non-U.S.: `City, Country: Publisher`; state only for U.S. places |
| Chapter | `"Chapter," in Book, J. S. Brake, Ed., City, ST, USA: Publisher, year, ch. 6, pp. 55-70.`; `Eds.` for several editors |
| Conference | `"Title," in Proc. 4th Annu. Conf., City, ST, USA, Mar. 20-22, 2005, pp. 124-129.`; unpublished talk: `presented at the Conf., ...` |
| Web | `Name, "Title," Site. Accessed: Mar. 14, 2025. [Online]. Available: URL` (no period after URL); dated post: `Site, Oct. 9, 2024. [Online]. Available: URL` |
| Ending | every reference ends with a period unless it ends with a URL; DOI written `doi: 10...` |
| Missing date | `(n.d.)` |

## Triage of findings

| Finding | Severity | Action |
|---|---|---|
| `missing_field`, `bad_*`, `elided_pages` | error | Get the real value from the user; do not guess or expand `2787-93` |
| `journal_abbreviation_missing` | warning | Ask for the abbreviation; do not supply one from memory |
| `conference_name_unabbreviated`, `ordinal_not_numeric` | warning | Ask for the abbreviated name; ordinals become numerals (4th) |
| `uncited_entry` | warning | Left out of the list; tell the user |
| `possible_duplicate_source` | warning | Confirm and reuse one number |
| `us_state_missing`, `missing_location` | warning | Ask; the guide prints city, state, USA |
| verify errors (`label_format`, `doi_format`, `range_dash`, ...) | error | Correct the line, change nothing that was not flagged |
| `given_name_spelled_out`, `us_state_form`, `combined_numbers_in_bracket` | warning | Pattern-based; confirm by eye |

Code list with meanings: [references/input-and-codes.md](references/input-and-codes.md).

## Output contract

Stdout is strict JSON (ASCII-escaped, `schema_version` 1). `format`: `in_text` (one `text` and `numbers` per citation), `references` (`number`, `id`, `text`), `issues` (`severity`, `code`, `ref`, `message`), `summary` (`citations`, `references`, `errors`, `warnings`, `verdict` of `pass`, `review` or `fail`). `verify`: `issues`, `first_appearance_order`, `summary`. A bad input prints one JSON line with `error` and exits 2. `--text-out` writes `[n] text` lines.

## Report format

```
Style: IEEE Reference Guide V 3.28.2025
References: <n> listed in order of first citation; <n> citation groups
Errors: <ref, code, what was changed or what is needed>
Warnings: <same shape>
Not checked: that sources exist, DOI correctness, journal abbreviations (used as supplied), title capitalization (printed as supplied)
```

## Refuse / stop when

- The user wants another style, a BibTeX or LaTeX bibliography, or new sources found.
- A journal or conference abbreviation is needed and not supplied: ask, do not guess.
- Authors, year, or the title is missing and the user cannot supply it: report the gap, do not fill it.
- Asked to confirm a citation is real or that a DOI works.

## Script

`scripts/ieee_format.py`: reads one UTF-8 file of at most 2 MB, never the network, writes only to the new files named by `--output` and `--text-out`. Run it, do not edit it.

## Limits

- Hyphenated given names print as `J.-P.` with a warning; the guide gives no rule.
- Title capitalization is printed as supplied (the guide's examples are mixed).
- Reports, standards, patents, theses, datasets, software and video are not formatted; handle them by hand from the guide or tell the user.
- A first edition is printed only if the user supplies an edition number.
- Verify is pattern-based: it finds the listed error classes, not every deviation, and cannot judge abbreviations.
- Without Python: apply the table above by hand and say so in the report.
