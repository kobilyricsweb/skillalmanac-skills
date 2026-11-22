## Contents

- Versions implemented
- Templates per style and type
- Author-count rules
- Required fields per style and type
- AI tools
- Input field map (BibTeX and CSL-JSON)
- Sources to confirm against

Written in the editors' own words from the public style guides. The rules were not re-checked against the live manuals when this file was written; treat the template column as the implemented behaviour and confirm with the current manual. `*x*` means italic (Markdown asterisks in the output; `--plain` removes them).

## Versions implemented

| Style | Implemented |
|---|---|
| APA | 7th edition rules |
| MLA | 9th edition rules |
| Chicago | author-date, 17th edition rules (18th edition differences not implemented) |
| IEEE | reference guide form, numbered `[n]` in input order |

## Templates per style and type

Missing parts are skipped, never replaced by a guess. A work with no author starts with its title (APA, Chicago) or goes straight to the title (MLA).

| Type | APA | MLA |
|---|---|---|
| article | `Author. (Y). Title. *Journal*, *V*(I), pages. DOI` | `Author. "Title." *Journal*, vol. V, no. I, Y, pp. P, DOI.` |
| book | `Author. (Y). *Title* (2nd ed.). Publisher.` | `Author. *Title*. 2nd ed., Publisher, Y.` |
| chapter | `Author. (Y). Title. In Eds (Eds.), *Book* (pp. P). Publisher.` | `Author. "Title." *Book*, edited by Eds, Publisher, Y, pp. P.` |
| web | `Author. (Y, Month D). *Title*. Site. URL` | `Author. "Title." *Site*, D Mon. Y, URL.` (protocol dropped; "Accessed D Mon. Y." only if given) |
| report | `Author. (Y). *Title* (Report No. N). Publisher. URL` | `Author. *Title*. Report no. N, Publisher, Y, URL.` |
| software, AI | `Developer. (Y). *Tool* (Version or "X version") [Descriptor]. URL` | `"Prompt text" prompt. *Tool*, version, Publisher, D Mon. Y, URL.` |

| Type | Chicago author-date | IEEE |
|---|---|---|
| article | `Author. Y. "Title." *Journal* V (I): P. DOI.` | `A. Author, "Title," *Journal*, vol. V, no. I, pp. P, Mon. Y, doi: D.` |
| book | `Author. Y. *Title*. 2nd ed. Place: Publisher.` | `A. Author, *Title*, 2nd ed. Place: Publisher, Y.` |
| chapter | `Author. Y. "Title." In *Book*, edited by Eds, P. Place: Publisher.` | `A. Author, "Title," in *Book*, Eds, Eds. Place: Publisher, Y, pp. P.` |
| web | `Author. Y. "Title." Site. Accessed Month D, Y. URL.` | `A. Author, "Title," Site. Accessed: Mon. D, Y. [Online]. Available: URL` |
| report | `Author. Y. *Title*. Report No. N. Place: Publisher. URL.` | `A. Author, "Title," Publisher, Place, Rep. N, Y.` |
| software, AI | `Developer. Y. *Tool*. Version V. URL.` (warning: confirm) | `Developer, "Tool," version, Y. [Online]. Available: URL` (warning: confirm) |

Details that the table hides:

- Pages: a hyphen range becomes an en dash. A single token such as `e0234` is treated as an article number, printed bare (IEEE: `Art. no. e0234`).
- Edition: a number becomes an ordinal (`2` becomes `2nd ed.`); edition 1 is omitted; text is kept with `ed.` appended.
- Report number: a bare number gets the style's label (`Report No. 7`, MLA `Report no. 7`, IEEE `Rep. 7`); text that already has a label is kept.
- Publisher equal to the author (a corporate author) is dropped from the entry.
- Same first-author list and same year, APA and Chicago: the year gets a, b, c in title order (`2022a`). Duplicates are not counted.
- Sort order: APA, MLA, Chicago alphabetical by first author's family name (title without a leading A, An, The when there is no author), then year, then title. IEEE keeps input order.
- Chicago repeated-author 3-em dash is not applied; names repeat.
- Titles are used as typed. Quotation marks are straight. Case is never changed; for APA the script only warns when an article or chapter title looks like title case.
- DOI: `https://doi.org/` form in APA, MLA and Chicago; `doi:` in IEEE. A value that does not match `10.NNNN/suffix` is left out and flagged.

## Author-count rules

| Style | Reference list | In-text string |
|---|---|---|
| APA | up to 20 names; from 21: first 19, ellipsis, last | 1: `(A, Y)`; 2: `(A & B, Y)`; 3 or more: `(A et al., Y)` |
| MLA | 1 or 2 names; 3 or more: first author, et al. | 1: `(A)`; 2: `(A and B)`; 3 or more: `(A et al.)`; page numbers are not known to the script |
| Chicago | up to 10 names; 11 or more: first 7, et al. | 1 to 3 names listed `(A, B, and C Y)`; 4 or more: `(A et al. Y)` |
| IEEE | up to 6 names; 7 or more: first author, et al. | `[n]` |

Name shapes: APA `Family, I. I.`; MLA and Chicago first author inverted with full given names, the rest natural order; IEEE `I. I. Family`. A hyphenated given name keeps the hyphen in initials (`J.-W.`). A corporate author is printed as given.

## Required fields per style and type

Run `python scripts/format_refs.py rules --style <style>` for the live table. Summary:

| Type | APA, Chicago | MLA | IEEE |
|---|---|---|---|
| article | author, year, title, container, volume | author, title, container, year | author, title, container, year, volume |
| book | author or editor, year, title, publisher | author or editor, title, publisher, year | same as MLA |
| chapter | author, year, title, container, publisher | author, title, container, publisher, year | same as MLA |
| web | title, url | title, url | title, url, accessed |
| report | author or publisher, year, title | author or publisher, title, year | same |
| software | author or publisher, year, title (APA also url) | title, description, author or publisher, year | author or publisher, title, year, url, accessed |

Recommended only (reported, not blocking): article pages and DOI or URL; chapter pages and editors; web author and year; report url; software version; APA software genre (the bracket descriptor); MLA software url; Chicago and IEEE book place.

## AI tools

The brief for an AI tool entry: developer or company, year, tool name, version or date of use, a short descriptor, the address, and for MLA the prompt text. The guidance for generated text is still moving, and some manuals prefer an in-text or note acknowledgement over a reference entry. The script prints an entry in the pattern above and adds a warning for Chicago and IEEE. Tell the user to confirm against their institution's current manual and, for graded work, the course policy on AI use. An AI tool is not a source of facts: the user should cite the primary sources behind any claim.

Version text: a value that looks like a number becomes `Version 4.0`; any other value gets ` version` appended (`Mar 14` becomes `Mar 14 version`).

## Input field map (BibTeX and CSL-JSON)

| Meaning | BibTeX | CSL-JSON |
|---|---|---|
| type | article, book, incollection or inbook, online or misc, techreport, software | article-journal, book, chapter, webpage, report, software |
| authors | `author` split on `and`; `{Corporate Name}` in braces is one literal name | `author` list of `family` and `given`, or `literal` |
| editors | `editor` | `editor` |
| date | `year`, `month`, `day`, or `date = {YYYY-MM-DD}` | `issued.date-parts` |
| container | `journal`, `journaltitle`, `booktitle`; web: `website` or `organization` | `container-title` |
| volume, issue, pages | `volume`, `number` (articles), `pages` | `volume`, `issue`, `page` |
| publisher, place | `publisher` (reports: `institution`), `address` or `location` | `publisher`, `publisher-place` |
| report number | `number` | `number` |
| identifiers | `doi`, `url` | `DOI`, `URL` |
| accessed | `urldate` | `accessed` |
| AI descriptor, prompt, version | `genre`, `description` (or `prompt`), `version` | `genre`, `description`, `version` |

Other BibTeX types (thesis, proceedings, patent, and so on) are reported as unsupported; none is guessed into another type.

## Sources to confirm against

- APA Style: https://apastyle.apa.org/style-grammar-guidelines/references
- MLA Style Center: https://style.mla.org/works-cited/
- Chicago Manual of Style, author-date quick guide: https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-2.html
- IEEE reference guide: https://ieeeauthorcenter.ieee.org/wp-content/uploads/IEEE-Reference-Guide.pdf
- CSL-JSON schema: https://github.com/citation-style-language/schema
