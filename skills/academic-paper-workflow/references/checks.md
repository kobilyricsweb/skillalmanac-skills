# What the script checks and how

## Contents
- Citation recognition
- Required fields by entry type
- Suspect values
- Numeric claims
- Sources used

## Citation recognition

- Pandoc: `[@key]`, `[@a; @b, p. 3]`, `[see @key]`, `[-@key]`, narrative `@key`. A key starts with a letter, digit or underscore, may contain `: . # $ % & + ? < > ~ / -` inside, and does not end in punctuation.
- LaTeX: `\cite`, `\citep`, `\citet`, `\citealp`, `\citealt`, `\citeauthor`, `\citeyear`, `\parencite`, `\textcite`, `\autocite`, `\footcite`, `\nocite`, with comma-separated keys.
- Ignored: front matter, fenced code, inline code, HTML comments, maths, and addresses such as `me@host.example`.
- `nocite` in the front matter or `\nocite{...}` counts as citing those keys; a wildcard (`@*` or `*`) switches off the uncited-sources check.
- Key lookup is case-sensitive, as in Pandoc. A key that differs only in case gets a `hint`. Duplicate detection is case-insensitive, as in BibTeX.

## Required fields by entry type

A name pair `a|b` means one of the two. Items marked house are stricter than classic BibTeX.

| BibTeX type | Required |
|---|---|
| article | author, title, journal or journaltitle, year or date |
| book | author or editor, title, publisher, year or date |
| inbook | author or editor, title, chapter or pages, publisher, year or date |
| incollection | author, title, booktitle, publisher, year or date |
| inproceedings, conference | author, title, booktitle, year or date |
| phdthesis, mastersthesis, thesis | author, title, school or institution, year or date |
| techreport, report | author, title, institution, year or date |
| unpublished | author, title, note |
| booklet, manual | title |
| proceedings | title, year or date |
| misc (house) | title, year or date |
| online (house) | title, author or editor or organization, year or date, url or doi |
| any other type (house) | title, year or date |

| CSL-JSON type | Required |
|---|---|
| article-journal, article-magazine | author, title, container-title, issued |
| article-newspaper | title, container-title, issued |
| article | author, title, issued |
| book | author or editor, title, publisher, issued |
| chapter | author, title, container-title, publisher, issued |
| paper-conference | author, title, container-title, issued |
| thesis, report | author, title, publisher, issued |
| webpage | title, author or container-title or publisher, issued, URL |
| dataset | title, author, issued |
| any other type | title, issued |

A CSL-JSON `issued` with only null date parts counts as missing. An empty or whitespace value counts as missing.

## Suspect values

Any string field matching placeholder text (TODO, TBD, unknown, question marks, lorem ipsum, XXX, FIXME, n/a, anonymous, a lone dash), and a BibTeX year that is not four digits (a trailing letter such as 2020a is allowed).

## Numeric claims

- Text is cut into sentences inside each paragraph; list items and block quotes are their own paragraphs. Headings, tables, code and the reference list are skipped.
- A number is a digit run that is a percentage, has a decimal point or thousands comma, or has two or more digits. Single plain digits are ignored. Labels such as Table 2, Figure 3, Section 4, Eq. 5, ordinals (21st) and names like H1N1 are removed first.
- Default skipped sections (the author's own data): methods and materials, participants, procedure, results, findings, appendix, acknowledgements, references, data availability. Subsections under a skipped heading are skipped too.
- A numeric sentence passes when a citation sits in the same sentence, in the next `--window-after` sentences of the paragraph (default 1), or in the previous `--window-before` (default 0). Sentences that pass only through a neighbour are listed separately.

## Sources used

- BibTeX entry types and required fields: <https://www.bibtex.org/Format/>
- CSL-JSON item types and fields: <https://docs.citationstyles.org/en/stable/specification.html#appendix-iii-types>
- Pandoc citation syntax: <https://pandoc.org/MANUAL.html#extension-citations>
