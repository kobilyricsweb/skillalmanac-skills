# Text entity extractor

## One line

Lists the URLs, hashtags, @mentions and dates in a plain text file, with counts and line numbers.

## What it does

The skill runs one Python script on a plain UTF-8 text file. The script finds web addresses that start with http, https or www, trims trailing sentence punctuation, and drops hosts without a dot. It then finds hashtags and @mentions in the same text, with the web addresses hidden so that a fragment such as "#section" inside a link is not counted as a tag. Email addresses are not treated as mentions. Dates are found in two forms: ISO dates such as 2026-03-14, and slash dates with a four-digit year. Each slash date is read in US month/day order unless one part is above 12, which fixes the order. When both parts are 12 or less and differ, the date is flagged as ambiguous and both readings are reported. Impossible dates, such as February 30, are listed apart so they are not silently dropped.

Every unique entity comes with its first line, its occurrence count and the list of line numbers where it appears. The output is a single JSON object, so the same run can be checked by a person or pasted into a report. The script exits 1 when an ambiguous date is present, which tells the agent to ask the user before the list is final.

## When to use

Use it when a list of links, tags, handles or dates must be complete and countable, for example from meeting notes, a draft article, a transcript export or a chat log saved as text. Hand-reading a long file misses links that wrap or tags placed next to punctuation, and the script gives the same answer every time it runs on the same file.

## When not to use

Do not use it for names of people or organizations, which the script does not attempt to find. Do not use it to check whether links still work, to fetch pages or to follow redirects. It does not read Word, PDF or spreadsheet files, and it does not handle inputs over 2 MB. It is not a sentiment or topic tool.

## Requirements

Python 3.9 or later, standard library only. No network access and no packages to install. The input must be one UTF-8 text file. The script writes nothing to disk.

## Example

Run on the shipped fixture, a 25-line notes file, with the command `python -I scripts/extract_entities.py fixtures/sample_notes.txt`. Exit code 1, because one date is ambiguous.

```json
{
  "input": "sample_notes.txt",
  "summary": {
    "lines_scanned": 25,
    "url_unique": 6,
    "hashtag_unique": 4,
    "mention_unique": 2,
    "date_unique": 5,
    "ambiguous_date_unique": 1,
    "rejected_date_candidates": 1
  },
  "urls": [
    {
      "value": "https://example.com/tour/schedule",
      "count": 2,
      "first_line": 2,
      "lines": [
        2,
        10
      ]
    },
    {
      "value": "https://example.net/tips/travel?ref=newsletter",
      "count": 1,
      "first_line": 4,
      "lines": [
        4
      ]
    },
    {
      "value": "www.example.org/maps/venues",
      "count": 1,
      "first_line": 4,
      "lines": [
        4
      ]
    },
    {
      "value": "https://example.com/archive/2025/index.html",
      "count": 1,
      "first_line": 9,
      "lines": [
        9
      ]
    },
    {
      "value": "www.example.org/faq",
      "count": 1,
      "first_line": 11,
      "lines": [
        11
      ]
    },
    {
      "value": "https://example.com/lineup",
      "count": 1,
      "first_line": 12,
      "lines": [
        12
      ]
    }
  ],
  "hashtags": [
    {
      "value": "#ReleaseNotes",
      "count": 1,
      "first_line": 5,
      "lines": [
        5
      ]
    },
    {
      "value": "#SpringTour",
      "count": 2,
      "first_line": 5,
      "lines": [
        5,
        14
      ]
    },
    {
      "value": "#Tour2026",
      "count": 1,
      "first_line": 14,
      "lines": [
        14
      ]
    },
    {
      "value": "#Tickets",
      "count": 1,
      "first_line": 20,
      "lines": [
        20
      ]
    }
  ],
  "mentions": [
    {
      "value": "@Photo_Lead",
      "count": 1,
      "first_line": 7,
      "lines": [
        7
      ]
    },
    {
      "value": "@editor_desk",
      "count": 2,
      "first_line": 7,
      "lines": [
        7,
        15
      ]
    }
  ],
  "dates": [
    {
      "iso": "2026-03-14",
      "alt_iso": null,
      "ambiguous": false,
      "as_written": [
        "2026-03-14"
      ],
      "count": 1,
      "first_line": 1,
      "lines": [
        1
      ]
    },
    {
      "iso": "2026-01-02",
      "alt_iso": "2026-02-01",
      "ambiguous": true,
      "as_written": [
        "01/02/2026"
      ],
      "count": 1,
      "first_line": 3,
      "lines": [
        3
      ]
    },
    {
      "iso": "2026-12-25",
      "alt_iso": null,
      "ambiguous": false,
      "as_written": [
        "12/25/2026"
      ],
      "count": 1,
      "first_line": 8,
      "lines": [
        8
      ]
    },
    {
      "iso": "2026-11-22",
      "alt_iso": null,
      "ambiguous": false,
      "as_written": [
        "2026-11-22"
      ],
      "count": 1,
      "first_line": 16,
      "lines": [
        16
      ]
    },
    {
      "iso": "2026-06-01",
      "alt_iso": null,
      "ambiguous": false,
      "as_written": [
        "2026-06-01"
      ],
      "count": 1,
      "first_line": 21,
      "lines": [
        21
      ]
    }
  ],
  "rejected_dates": [
    {
      "as_written": "2026-02-30",
      "line": 13
    }
  ]
}
```

## Limits

The script finds only the four entity types named above, in the forms listed in the rules table of the skill. It does not find bare domains such as example.com without a scheme, two-digit years, month names written in words, or dates with dashes other than ISO order. Thresholds for hashtag length, mention length, the 2 MB cap and the US reading of ambiguous dates are working values, not published specifications. It does not verify that a link resolves, that a page exists, or that a date is correct for the context. It does not judge whether a mention refers to a real account, and it cannot tell a tag from a word in a quotation that happens to start with a hash sign.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
