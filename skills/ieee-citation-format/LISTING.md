# Listing page content: ieee-citation-format

## One line

Formats IEEE numbered references and in-text citations from your source data, and checks a pasted IEEE list against the current guide.

## Summary

Give the skill your sources and the order your manuscript cites them, and a script numbers them by first citation, reuses the number when a source returns, and prints each in-text citation. A run of consecutive numbers is written out in full, as the 2025 guide requires, not as a dash range. It formats journal articles, books, chapters, conference papers and web pages: initials first, et al. after six authors, abbreviated months, Art. no., edition, city and state, DOI and URL endings. Journal names are abbreviated only if you supply the abbreviation. A second mode audits a pasted list and your manuscript numbers.

## What it does

- `format`: JSON sources and citation groups in, numbered reference list and in-text strings out (curly quotes and en dashes, or `--ascii`).
- `verify`: pasted `[n]` list, optionally with the manuscript, in; findings out (surname-first names, more than six authors, month and label forms, DOI form, final period and URL period, to appear in, dash ranges, first-citation order, gaps).
- Rules come from the IEEE Reference Style Guide for Authors V 3.28.2025, read 2026-11-24, listed with sections in `references/ieee-rules.md`.

## When to use

You need an IEEE reference list built from structured data, in-text numbers that follow first citation, or a check of a list someone else made.

## When not to use

Other styles, BibTeX or LaTeX bibliographies, finding sources, confirming a source or DOI exists, reports, standards, patents, theses, datasets and software (not formatted).

How it differs from nearby skills: `acs-citation-format` and `vancouver-citation-format` cover other styles; this one covers IEEE numbering, ranges and the IEEE reference forms.

## Requirements

Python 3.9 or newer, standard library only. No network. Without Python the agent applies the rule table by hand.

## Example

Real output from `python scripts/ieee_format.py format evals/fixtures/basic.json` (a fixture of four cited sources and one uncited):

```
in-text: [1] | [2], [3], [4] | Rafferty [1] | [2, pp. 5–10] | Stein [3] and One et al. [4]

[1] W. Rafferty, “Ground antennas in NASA's deep space telecommunications,” Proc. IEEE, vol. 82, no. 5, pp. 636–640, May 1994.
[2] B. Klaus and P. Horn, Robot Vision. Cambridge, MA, USA: MIT Press, 1986.
[3] L. Stein, “Random patterns,” in Computers and You, J. S. Brake, Ed., New York, NY, USA: Wiley, 1994, pp. 55–70.
[4] A. One et al., “Seven authors here,” J. Things, vol. 3, p. 5, Sep. 2020.

issues: warning uncited_entry (unused); summary: errors 0, warnings 1, verdict review
```

## Limits

Uses supplied abbreviations only; hyphenated given names carry a warning; title capitalization printed as supplied; verify is pattern-based and cannot judge abbreviations or whether a source exists.

## Status

Provisional. Lint-clean, fixture-tested. Not independently verified.
