# Ad Copy Length Checker

## One line

Counts headline, description and path characters against limits you supply, and reports each overrun with its excess count.

## What it does

The skill runs one stdlib Python script over a JSON file that holds your ad copy and your limits. For every headline, description and optional path entry, it counts characters after Unicode NFC normalization and reports any text that is longer than its limit, with the number of characters over. It also checks three format rules that you configure: a character that must not end a headline or description, a cap on exclamation marks, and a test for all-caps text that uses a minimum letter count you choose. Headlines are compared with each other after case folding and whitespace collapse, so repeated headlines are reported with the first ad that used the same text.

The script prints one JSON object. Ad text is not echoed back, so the output can be pasted into a log without repeating the copy. Exit codes separate a clean run, a run with findings, and an input error.

## When to use

Use it when a set of ads has to pass one check before upload, when a truncated or rejected headline needs its overrun located, or when several campaigns share one set of limits and need one consistent pass.

## When not to use

Do not use it to write new copy, to predict click-through or performance, to research keywords, or to judge tone. It does not know the current rules of any ad platform, so its limits are only as good as the values you enter.

## Requirements

Python 3.9 or newer, standard library only. No network access, no packages to install, and no write access is needed beyond the terminal output.

## Example

Run on the three-ad sample in the package (`fixtures/smoke_input.json`), with the sample limits of 30 for headlines, 90 for descriptions and 15 for paths:

```
{
  "ok": false,
  "findings_count": 4,
  "counts_by_check": {
    "length": 4
  },
  "checked": {
    "ads": 3,
    "texts": 14
  },
  "limits": {
    "headline": 30,
    "description": 90,
    "path": 15
  },
  "rules": {
    "forbid_trailing": ".",
    "max_exclamation": 1,
    "all_caps_min_letters": 4
  },
  "findings": [
    {
      "ad": 1,
      "field": "headline",
      "slot": 2,
      "check": "length",
      "message": "35 characters, limit 30",
      "length": 35,
      "limit": 30,
      "excess": 5
    },
    {
      "ad": 2,
      "field": "description",
      "slot": 1,
      "check": "length",
      "message": "126 characters, limit 90",
      "length": 126,
      "limit": 90,
      "excess": 36
    },
    {
      "ad": 3,
      "field": "headline",
      "slot": 1,
      "check": "length",
      "message": "34 characters, limit 30",
      "length": 34,
      "limit": 30,
      "excess": 4
    },
    {
      "ad": 3,
      "field": "path",
      "slot": 2,
      "check": "length",
      "message": "25 characters, limit 15",
      "length": 25,
      "limit": 15,
      "excess": 10
    }
  ],
  "note": "Limits and rules are the values supplied in the input file. They are working values, not verified against any platform."
}
```

The process exits with code 1.

## Limits

The default limits are examples. Check them against the platform you publish to before you rely on a clean run. The all-caps letter count of 4 and the exclamation cap of 1 are working values chosen for this skill. The script counts code points, so combined emoji and multi-mark letters can differ from a platform's own count by a character or more. The script does not check spelling, grammar, brand rules, prohibited claims or policy wording.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
