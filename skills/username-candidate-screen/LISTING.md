# Username candidate screen

## One line

Flags weak handle options in a candidate list (length, characters, edge separators, digit runs, lookalike characters, repeats, near-duplicates) and ranks them.

## What it does

The skill takes a plain-text file with one username candidate per line and runs a local Python script over it. The script checks each line against nine rules: length below 3 or above 20 characters, characters outside letters, digits, underscore, period and hyphen, a separator at the start or end, a run of four or more digits, lookalike mixes such as capital I with lowercase l and the digit 1, lookalike mixes of 0 with o, the pair rn, a character repeated three times in a row, an exact duplicate, and a pair that differs by a single edit. Each candidate gets a list of rule codes and a findings count. The output is a table sorted with the fewest findings first, so the cleanest options appear at the top.

The script reads the file and writes nothing. It makes no network calls and does not ask any platform whether a name is free. The thresholds are working values chosen for this skill and are labelled as such in its decision table.

## When to use

Use it when a person has a short list of handle options, perhaps ten to a few hundred, and wants the ones that will be hard to read, hard to type or easy to confuse flagged before they choose. It is also useful when several people are proposing names for the same account and the list needs a quick consistency pass.

## When not to use

Do not use it to check whether a name is registered, available or safe from trademark claims. Those questions need a platform lookup or legal review, which this skill does not do. Do not use it to invent new names, rate how memorable a name is, or handle lists larger than 2000 candidates or files larger than 2 MB.

## Requirements

Python 3.9 or newer. The script uses only the standard library. No packages, no network access and no write permission beyond the terminal are needed.

## Example

The shipped smoke fixture contains ten candidates, each with one planted problem. Output of the run, pasted unchanged:

```
username-candidate-screen 0.1.0 (length 3-20)
rank  line   candidate                            length  findings  codes
1     1      ab                                   2       1         LEN_SHORT
2     2      wordsmith_studio_daily_brew_club_hq  35      1         LEN_LONG
3     3      _nightowl                            9       1         EDGE_SEP
4     4      kai2024                              7       1         DIGIT_RUN
5     5      Il1ness                              7       1         CONFUSABLE
6     6      pro0fan                              7       1         CONFUSABLE
7     7      cool@fox                             8       1         CHARSET
8     8      sooo_fresh                           10      1         REPEAT
9     9      maplefox                             8       1         NEAR_DUP
10    10     maplefix                             8       1         NEAR_DUP
candidates=10 flagged=10 clean=0
```

## Limits

- Thresholds (length 3 to 20, four digits, three repeats, two lookalikes) are working values, not a platform specification.
- Maximum 2000 candidates and 2 MB per file. Larger files exit with code 2.
- Only ASCII letters, digits and the three separators are treated as allowed; any non-ASCII letter is flagged, even when a platform would accept it.
- The rn rule also fires inside ordinary words such as burn, so a reviewer should read the codes rather than trust them blindly.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
