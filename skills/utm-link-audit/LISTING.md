# UTM Link Audit

## One line

Checks a list of campaign links for UTM parameter mistakes and reports each one with its line number.

## What it does

The skill runs a small read-only checker over a text file that holds one campaign URL per line. The checker looks for seven problems: a URL with no scheme or host, a required utm_source, utm_medium or utm_campaign parameter that is missing, uppercase letters in a utm key or value, spaces or encoded spaces inside a value, a utm_medium that is not on the allowed list, a campaign name that mixes underscores and hyphens or differs from an earlier campaign only by separator, and a URL that repeats an earlier one once its parameters are sorted and lowercased. The output is a JSON report with a count per problem code and one entry per finding. The agent then turns the findings into a fix table with a fix for each row.

## When to use

Use it before a launch, when a marketing team has a spreadsheet of tracked links to clear. It is also useful when a campaign report shows the same campaign as two rows because one link wrote its source in capitals or used a space where a hyphen belonged.

## When not to use

Do not use it to build new UTM links, to test whether a page loads, or to explain attribution results from an analytics tool. It makes no network calls, so it cannot tell whether a redirect or a live page is correct.

## Requirements

Python 3.9 or newer, standard library only. No packages, no network, and no write access to the input file. The input must be UTF-8 text with at most 2 MB and 4096 characters per line.

## Example

Output from the smoke run on the 8-line fixture in this package (exit code 1):

```json
{
  "input": "fixtures/campaign_urls.txt",
  "lines_read": 8,
  "urls_checked": 8,
  "allowed_mediums": [
    "cpc",
    "email",
    "social",
    "referral",
    "display",
    "affiliate",
    "organic"
  ],
  "summary": {
    "UPPERCASE": 1,
    "SPACE": 1,
    "MISSING_PARAM": 1,
    "DUPLICATE": 1
  },
  "findings": [
    {
      "line": 2,
      "code": "UPPERCASE",
      "detail": "utm_source=Newsletter",
      "url": "https://www.example.com/pricing?utm_source=Newsletter&utm_medium=email&utm_campaign=spring-launch"
    },
    {
      "line": 4,
      "code": "SPACE",
      "detail": "utm_campaign has a space",
      "url": "https://www.example.com/blog/post-1?utm_source=partner&utm_medium=referral&utm_campaign=spring%20launch"
    },
    {
      "line": 5,
      "code": "MISSING_PARAM",
      "detail": "utm_medium",
      "url": "https://www.example.com/contact?utm_source=google&utm_campaign=search-brand"
    },
    {
      "line": 8,
      "code": "DUPLICATE",
      "detail": "same as line 1",
      "url": "https://www.example.com/landing?utm_medium=cpc&utm_source=google&utm_campaign=spring-launch"
    }
  ]
}
```

## Limits

- The allowed utm_medium list and the 2 MB and 4096-character caps are working values chosen for this package. They are not industry standards.
- The checker compares campaign names as written. It cannot know that two different names mean the same campaign.
- The checker has no JSON or spreadsheet input. Export a spreadsheet column to a text file first.
- A link can pass every check and still be the wrong destination. The checker does not open the page.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
