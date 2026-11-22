# List Fuzzy Matcher

## One line

Matches each item in one CSV list to its closest item in another, and flags weak, tied, and unmatched pairs for review.

## What it does

The skill runs a small Python script that reads two CSV files, each with a header row. It picks one item column from each file, by header name or position. Every item is normalized: letters are casefolded, punctuation becomes a space, and repeated spaces collapse. The normalized left item is then scored against each distinct normalized right item using the difflib ratio, a character-level similarity between 0 and 1.

The script writes one row per left item to a new CSV. Each row names the best right candidate, its score, the runner-up, and a status. Four statuses exist: ok, weak, tie, and unmatched. A tie means two different right names share the top score, so the script cannot choose. An unmatched row has no candidate above a low floor. The agent then reads the flagged rows and records a decision for each: accept, no match, or needs source check. The report keeps those decisions visible, so a reviewer can see why each pair was accepted.

The script never writes over an existing file and never changes its inputs. It exits 2 with a one-line JSON error on bad input, so a calling agent can stop cleanly.

## When to use

Use it when two lists describe the same things but spell them differently: company names exported from two systems, product titles with different punctuation, or a supplier list typed by hand against an official list. It fits lists of up to 1000 rows per side, since the flagged rows are the part a person must review.

## When not to use

Do not use it for exact joins on IDs, for merging database tables, or for free-text paragraphs. Do not use it to decide which record wins without a person checking the flagged rows. It does not query the web or any service, so it cannot confirm that a name is real.

## Requirements

Python 3.9 or later, standard library only. No network access, no subprocess calls, and no third-party packages. Inputs must be UTF-8 with an optional byte-order mark, 2 MB or smaller per file, and at most 1000 data rows each.

## Example

Command, run from the skill folder, with placeholders for the user's files:

```
python -I scripts/fuzzy_match.py --left <left-file> --right <right-file> --output <output-file>
```

Real output from one run on the shipped fixtures (eight left names, eight right names):

```
{"exit": 1, "left_items": 8, "right_items": 8, "skipped_blank": {"left": 0, "right": 0}, "status_counts": {"ok": 4, "weak": 1, "tie": 1, "unmatched": 2}}
left_item,status,best_match,best_score,runner_up_match,runner_up_score
Acme Corporation,ok,ACME Corporation,1.0000,Waine Enterprises,0.4242
Globex Inc.,ok,Globex Inc,1.0000,Pied Piper Inc,0.4167
Initech LLC,weak,Initek Ltd,0.6667,Pied Piper LLC,0.5600
Umbrella Corp,unmatched,ACME Corporation,0.4828,Bluth Company,0.3846
Stark Industries,ok,Stark Industry,0.8667,Waine Enterprises,0.4848
Wayne Enterprises,ok,Waine Enterprises,0.9412,ACME Corporation,0.4242
Hooli,unmatched,ACME Corporation,0.2857,Globex Inc,0.2667
Pied Piper,tie,Pied Piper Inc,0.8333,Pied Piper LLC,0.8333
```

The exit code is 1 because four items are flagged (one weak, one tie, two unmatched). The "Pied Piper" row is a tie, and the agent should record needs source check for it.

## Limits

- The score measures spelling similarity only. It does not know that two names refer to the same company. "Intl" and "International" score poorly even when they are the same firm.
- Word order is not normalized, so reordered names score lower than they should.
- Only casefold and punctuation handling are applied. Accented characters are kept as typed, so composed and decomposed forms of the same accent are not treated as equal.
- Matching is not one-to-one. Two left items can both pick the same right name.
- On a tie, the output shows the alphabetically first normalized candidate as best_match. The tie flag is the reason to review it, not the choice itself.
- The thresholds 0.85 and 0.60 are working values chosen for short names. They are not calibrated against any labeled data. Run time was not measured at the 1000-row limit.
- Output cells are not guarded against spreadsheet formula text, so a name beginning with an equals sign will be read as a formula if the CSV is opened in a spreadsheet.
- The tool does not check deliverability, semantic equality, legal identity, or whether a name is current.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
