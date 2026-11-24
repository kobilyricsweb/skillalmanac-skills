# IEEE rules used by this skill

Source for every row: IEEE Reference Style Guide for Authors, version stamp "V 3.28.2025, (c) 2025 IEEE", read 2026-11-24.
URL: https://docs.google.com/document/d/1j1L96U2NagwWI9MEVDNVKt9pXxRzTH7h3krI3Mb6wZE (the IEEE Author Center "Reference Guide" PDF links now redirect to this document). A search on 2026-11-24 found no newer revision. Section names are the guide's own: I.1 References in Text, II.B Books, II.C Conferences and Conference Proceedings, II.M Periodicals, II.T Websites, II.A Blogs, II.J News Articles, II.S Unpublished.
Facts below are in our own words; example strings are short fragments of the guide's own examples.

## In-text (I.1)

| Rule | Detail |
|---|---|
| Form | Number in square brackets, inside punctuation: `[3]`. Numbers are assigned in order of first citation; the list is numbered, not alphabetical. |
| Ranges | No dash. Write every number: `[1], [2], [3], [4]`, never `[1]-[4]` (this changed in the 2025 version; the 2022 PDF still showed ranges). |
| Several sources | Each in its own brackets, separated by a comma and a space: `[2], [5]`. |
| Narrative use | Number used like a noun: `Smith [4]`, `Brown and Jones [5]`. Three or more names for the source: first surname plus `et al.`, as in `Wood et al. [7]`. |
| Part of a source | Location inside the same brackets after a comma: `[3, Thm. 1]`, `[3, pp. 5-10]` (en dash in print). |
| Reuse | A source cited again keeps its first number. |

## Names and list-wide rules (II, Style)

| Rule | Detail |
|---|---|
| Names | Given names reduced to initials, placed before the surname: `J. K. Author`. No comma before Jr., Sr. or III: `W. P. Pratt Jr., and J. Bass`. |
| Count | List up to six names. With more than six give the first (primary) author followed by `et al.`: `J. Yanamadala et al.,`. |
| Two / three or more | Two: `A and B`. Three or more: `A, B, and C` (comma before and). |
| Final period | Every reference ends with a period, including one that ends with a DOI. A reference that ends with a URL has no period after the URL. |
| DOI and URL | `doi: 10.1109/TBME.2011.2158315` (lowercase doi, colon, space). If an accessed date or DOI and a URL both appear, the date or DOI comes first, then a period, then the URL. |
| Missing date | `(n.d.)` where the date would go. |
| Online items | `[Online]. Available: URL`, with the period after `[Online]` and the colon after `Available`. |
| Months | Abbreviated with a period: Jan. Feb. Mar. Apr. May Jun. Jul. Aug. Sep. Oct. Nov. Dec. (May has none). Two months for one issue are joined with a slash: `Jul./Aug.`. |

## Periodicals (II.M)

Base form: `J. K. Author, "Title of paper," Abbrev. Title, vol. x, no. x, pp. xxx-xxx, Abbrev. Month, year, doi: xxx.`

| Case | Rule and example fragment |
|---|---|
| Journal title | Abbreviated (italic in print) from the guide's lists, not by guess; a one-word title is not abbreviated. This skill prints only the abbreviation the user supplies. |
| Page range | `pp. 2787-2793` (en dash in print; the guide's own examples also show a hyphen). |
| Single page | `p.`: `vol. 53, p. 475, 1935`. |
| Article number | No pages; `Art. no.` after the date: `vol. 91, no. 6, Aug. 2007, Art. no. 061103.` An article ID is never put in the page slot. |
| Early access | `IEEE Commun. Lett., early access, Dec. 11, 2018, doi: ...` |
| Accepted | `to be published` (not `to appear in`): `IEEE Trans. Antennas Propag., to be published.` |
| Not accepted | `submitted for publication`: `"Title," submitted for publication.` |

## Books and chapters (II.B)

| Case | Rule and example |
|---|---|
| Book | `B. Klaus and P. Horn, Robot Vision. Cambridge, MA, USA: MIT Press, 1986.` Title in italic in print; place is city, state (U.S. only), country; colon then publisher. |
| Edition | After the title, numeral plus `ed.`, then a period before the city: `Title, 2nd ed. New York, NY, USA: ...`. |
| Non-U.S. place | City and country only: `Rijeka, Croatia: InTech, 2012`. |
| Chapter | `L. Stein, "Random patterns," in Computers and You, J. S. Brake, Ed., New York, NY, USA: Wiley, 1994, pp. 55-70.` `Ed.` for one editor, `Eds.` for several. Chapter number: `..., Cullompton, U.K.: Willan, 2006, ch. 13, pp. 270-295.` |
| Publisher names | The guide abbreviates words such as University to `Univ.` (publisher list, IV.B). |

## Conferences (II.C)

| Case | Rule and example fragment |
|---|---|
| In proceedings | `"Title," in Proc. 37th Southeastern Symp. Syst. Theory, Tuskegee, AL, USA, Mar. 20-22, 2005, pp. 124-129.` Year may stand without month. |
| Presented only | `"Title," presented at the IEEE Summer Power Meeting, Dallas, TX, USA, Jun. 22-27, 1990, Paper 90 SM 690-0 PWRS.` |
| Name | Abbreviated from the guide's list (Proceedings = Proc., International = Int., Conference = Conf., Symposium = Symp., Annual = Annu., Technical Digest = Tech. Dig.); ordinals as numerals (4th, not Fourth); the words of the and on are dropped. This skill prints the name as supplied and warns on the full words above. |
| With DOI | `pp. 612-617, doi: 10.1109/ICHR.2006.321337.` |

## Web (II.T, II.A, II.J)

| Case | Rule and example |
|---|---|
| Website | `J. Smith, "Obama inaugurated as President," CNN.com. Accessed: Feb. 1, 2009. [Online]. Available: URL` (no final period). The guide's own site examples vary slightly in punctuation between the site name and `Accessed:`; this skill prints a period. |
| Dated blog or news item | `A. Clark, "Title," CBS News, Aug. 30, 2024. [Online]. Available: URL` |

## Not used (no readable rule)

Omitting a first edition; hyphenated given names (the script warns and prints `J.-P.`); capitalization of titles (the guide's examples are mixed, so titles are printed as supplied); publisher abbreviations beyond University; the guide's periodical abbreviation lists (supply abbreviations in the input).
