---
name: ad-copy-length-checker
description: Checks ad headlines, descriptions and paths against character limits you supply, and flags duplicate headlines, all-caps text, forbidden trailing characters and excess exclamation marks. Use when ad copy must be checked before upload, when a truncated or rejected headline or description needs its overruns located, or when a batch needs one pass against the same limits. Do not use for writing new ad copy, predicting click-through or performance, keyword research, or limits you have not checked against current platform rules.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Ad Copy Length Checker

This skill runs one fixed script over a JSON file of ad copy and reports every
text that breaks a limit or rule. The script counts characters, it does not
judge the copy. Limits come from the user. The defaults shown below are
working examples only.

## Inputs you need before starting

- A JSON file with `limits` (headline and description are required, path is
  optional).
- The ad texts as lists of strings under `ads`.
- Optional `rules` for trailing characters, exclamation marks and all-caps.
- The platform limits, written down by the user with the date they were read
  from the platform. If the user cannot supply them, stop (see Refuse / stop).

## Workflow

1. **Confirm limits.** Ask the user for the headline, description and path
   limits and the date they were checked. Required output: a three-line list
   `headline=N, description=N, path=N, checked=YYYY-MM-DD`. Do not fill in
   limits from memory.
2. **Set rules.** Use the table in "Limits and rules". Required output: the
   `rules` object you will write, with every key present.
3. **Write the input file.** Keep one file per campaign. Use the layout in
   "Input layout". Required output: the path of the file you wrote and the
   number of ads in it. Stop if the file would exceed 2 MB or 2000 ads and
   split it instead.
4. **Run the script.** Required command:
   `python -I scripts/ad_limits.py <input.json>`
   Record the exit code. Required output: the exit code and the
   `findings_count` value.
5. **Read the findings.** Sort them with the decision table. Required output:
   one row per finding in the "Report table" format.
6. **Fix and rerun.** Edit the ad texts, not the limits, unless the user
   changes the limits. Rerun from step 4. Stop after three reruns that still
   leave findings and report what is left. Required output: the final exit
   code and the number of reruns.

## Limits and rules

| Key | Where | Default | Allowed | Checks |
| --- | --- | --- | --- | --- |
| headline | limits | 30 (example) | 1 to 10000 | Characters per headline |
| description | limits | 90 (example) | 1 to 10000 | Characters per description |
| path | limits | 15 (example) | 1 to 10000 | Characters per path entry, only if `path` lists are present |
| forbid_trailing | rules | empty string (off) | up to 20 characters | Last non-space character of headline or description |
| max_exclamation | rules | 1 | 0 to 50 | Exclamation marks per headline or description |
| all_caps_min_letters | rules | 4 | 2 to 50 | Cased letters needed before the all-caps test applies |

The defaults marked "example" are not platform rules. The `all_caps_min_letters`
value of 4 is a working value chosen for this skill, not a published standard.

## Input layout

```
{
  "limits": {"headline": 30, "description": 90, "path": 15},
  "rules": {"forbid_trailing": ".", "max_exclamation": 1, "all_caps_min_letters": 4},
  "ads": [
    {"headline": ["..."], "description": ["..."], "path": ["..."]}
  ]
}
```

Unknown keys at any level are an input error. The sample at
`fixtures/smoke_input.json` uses this layout.

## Decision table

| Check value | Condition | Action |
| --- | --- | --- |
| `length` | `excess` > 0 | Shorten by at least `excess` characters. Keep the offer and the product name. |
| `duplicate_headline` | Same headline as `duplicate_of_ad` after case folding and whitespace collapse | Rewrite the later headline so it names a different angle. |
| `trailing_punctuation` | Last character is in `forbid_trailing` | Remove the character. |
| `exclamation` | `excess` > 0 | Remove the extra marks until the count equals `max_exclamation`. |
| `all_caps` | Cased letters at least `all_caps_min_letters`, none lowercase | Rewrite in sentence case. |

Length is counted after Unicode NFC normalization, one code point per count.
A combined emoji or a letter with several combining marks can count as more
than one character, so leave a margin of one character when the copy has them.

## Report table

| Ad | Field | Slot | Check | Detail | Action |
| --- | --- | --- | --- | --- | --- |

Fill one row per entry in `findings`. `Detail` is the `message` value.
`Action` is the decision-table row.

## Output contract

The script prints one JSON object to stdout with these top-level keys, in
this order: `ok`, `findings_count`, `counts_by_check`, `checked`, `limits`,
`rules`, `findings`, `note`.

- `checked` holds `ads` and `texts` counts.
- Each entry in `findings` holds `ad` (1-based), `field`, `slot` (1-based),
  `check`, `message`, and then `length`, `limit` and `excess` for `length`
  findings, `excess` for `exclamation` findings, or `duplicate_of_ad` for
  `duplicate_headline` findings.
- Ad text is never echoed back. Read the copy from your own input file.

## Script contract

- Command: `python -I scripts/ad_limits.py <input.json>`
- One positional argument: the path to the input JSON file.
- Reads the file only. It writes no files and makes no network calls.
- Limits: input at most 2 MB, nesting at most 20 levels, at most 2000 ads.
- Exit code 0: no findings. The stdout JSON has `ok` true.
- Exit code 1: findings reported. The stdout JSON lists them.
- Exit code 2: usage or input error. One line of JSON `{"error": "..."}` is
  written to stderr. Errors cover a missing file, invalid UTF-8, invalid
  JSON, an unknown key, a value outside its allowed range, or a wrong type.

## Refuse / stop when

- The user has no platform limits and asks for the check to run on guessed
  values. Stop and ask for the limits with their check date.
- The input file is over 2 MB, nests deeper than 20 levels, or has more than
  2000 ads. Split the file first.
- The user asks the skill to fetch current platform rules, submit ads, or
  call an ad platform. This skill has no network access and does not upload.
- The user asks for new headlines or descriptions to be written to fit the
  limits. This skill checks copy. Ask the user to write the replacement and
  then rerun the check.
- The user asks what the ads will earn or how they will rank. This skill
  reports character and format findings only.

## Files in this package

- `SKILL.md`, this file.
- `LICENSE.txt`, the Apache-2.0 license text.
- `scripts/ad_limits.py`, the checker described above.
- `fixtures/smoke_input.json`, a three-ad sample with four length overruns.
