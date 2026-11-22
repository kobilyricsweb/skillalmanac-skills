# resume-ats-format-check

## One line

Runs a stdlib Python checker on a plain-text or Markdown resume and lists the lines that use layouts, headings, bullets, symbols or date formats that applicant tracking systems often misread.

## What it does

The skill calls `scripts/ats_check.py` on one resume file. The script reads the file as UTF-8, rejects binary input, and checks it line by line against eleven fixed rules. It flags a tab or a run of three or more spaces between text, which is how two-column layouts usually survive a copy-paste. It flags any pipe character, which often marks a table. It flags heading-like lines whose name is outside a fixed list of standard section names, and it reports the Experience, Education and Skills sections that have no standard heading at all. It flags bullet glyphs other than hyphen, asterisk and plus, and non-ASCII symbols inside a line. It compares date formats across the file and reports each line that uses a minority format, so a resume that mixes month names with slash dates shows which lines to change. It also reports the file-level gaps: no email pattern, no phone pattern, and no line that holds a date range. Every finding carries a line number, a code and a fixed detail sentence. The script never prints resume text, so the report can be shared without exposing a name or contact detail.

## When to use

Use it when a user wants a quick, repeatable pass over a resume before sending it through an online application, or when a resume they wrote in a word processor came back looking wrong after pasting into a form. It is also useful for a second pass after edits, because the same file always produces the same findings.

## When not to use

Do not use it to score a resume, to predict a pass rate, or to compare a candidate with others. It does not rewrite bullets, judge the quality of the experience described, or read PDF and Word files. It does not model any particular tracking system.

## Requirements

Python 3.9 or later, standard library only. No network access and no install step. The input must be a UTF-8 text file of at most 2 MB. The skill needs a text-capable agent to read the JSON and write the report in the output contract.

## Example

The command was run on the shipped fixture, a 40-line text resume, and the output is pasted verbatim. The exit code was 1.

```
{
  "lines_scanned": 40,
  "total": 14,
  "counts": {
    "DATE_FORMAT_MIXED": 2,
    "LONG_LINE": 1,
    "MISSING_SECTION": 1,
    "NONSTANDARD_HEADING": 2,
    "SPECIAL_SYMBOL": 1,
    "TABLE_PIPE": 2,
    "TAB_OR_SPACE_RUN": 3,
    "UNUSUAL_BULLET": 2
  },
  "findings": [
    {
      "line": 0,
      "code": "MISSING_SECTION",
      "detail": "no standard heading found for Education"
    },
    {
      "line": 2,
      "code": "TABLE_PIPE",
      "detail": "pipe character, usually a table or column separator"
    },
    {
      "line": 4,
      "code": "NONSTANDARD_HEADING",
      "detail": "heading-like line that is not a standard section name"
    },
    {
      "line": 10,
      "code": "UNUSUAL_BULLET",
      "detail": "bullet glyph outside the hyphen, asterisk and plus set"
    },
    {
      "line": 14,
      "code": "DATE_FORMAT_MIXED",
      "detail": "minority date format 'numeric_slash'; most common format in file is 'month_name'"
    },
    {
      "line": 19,
      "code": "DATE_FORMAT_MIXED",
      "detail": "minority date format 'iso'; most common format in file is 'month_name'"
    },
    {
      "line": 20,
      "code": "LONG_LINE",
      "detail": "line longer than 200 characters"
    },
    {
      "line": 23,
      "code": "TAB_OR_SPACE_RUN",
      "detail": "tab or run of three or more spaces between text"
    },
    {
      "line": 24,
      "code": "TAB_OR_SPACE_RUN",
      "detail": "tab or run of three or more spaces between text"
    },
    {
      "line": 25,
      "code": "TAB_OR_SPACE_RUN",
      "detail": "tab or run of three or more spaces between text"
    },
    {
      "line": 26,
      "code": "UNUSUAL_BULLET",
      "detail": "bullet glyph outside the hyphen, asterisk and plus set"
    },
    {
      "line": 27,
      "code": "TABLE_PIPE",
      "detail": "pipe character, usually a table or column separator"
    },
    {
      "line": 29,
      "code": "SPECIAL_SYMBOL",
      "detail": "non-ASCII symbol or bullet glyph inside the text"
    },
    {
      "line": 32,
      "code": "NONSTANDARD_HEADING",
      "detail": "heading-like line that is not a standard section name"
    }
  ]
}
```

## Limits

The checker reads plain text only. It does not see fonts, images, headers, footers, text boxes or colors, so a resume that looks clean on screen can still carry a problem the check cannot see. Its thresholds are working values: a line of more than 200 characters, a phone pattern of 10 to 15 digits, and a three-space gap. A capitalized name on a line after the first can be reported as a heading, and a span of years with numbers after it can be read as a phone number. A heading in title case with no colon and no `#` (for example 'Career Summary') is not recognized as heading-like and is never flagged. The fixed list of standard names is English only. The output lists patterns; it does not say whether any system will extract the candidate's data correctly.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
