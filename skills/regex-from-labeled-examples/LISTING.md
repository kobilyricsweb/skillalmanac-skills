# regex-from-labeled-examples

## One line

Proposes a Python regex from labeled match and non-match strings and tests it against every example in a proof table.

## What it does

The skill takes a short list of strings marked MATCH and strings marked NON-MATCH. It splits them into two columns with stable IDs, then states in one sentence the feature that all matches share and the non-matches lack. From that sentence it writes one anchored Python regex, evaluated with re.fullmatch so that a trailing newline never counts as a match. Every example, including the non-matches, goes into a proof table with the expected label, the actual label, the captured groups, and a pass or fail flag.

The skill also lists two to five strings the user did not supply that the pattern decides only by an arbitrary choice, such as trailing whitespace or a full-width digit. Each one comes with the example the user should label to settle it. The output ends with a status value and an explicit line that the regex is proven only on the supplied examples.

The pattern rules are deliberate. The skill refuses nested quantifiers such as (a+)+, alternations whose branches overlap, and patterns above six quantifiers or 120 characters. Those limits are working values chosen for readable examples, not a published standard.

## When to use

Use it when someone has a handful of strings that should match and a handful that should not, for example order IDs, product codes, invoice numbers, or log lines, and needs a regex that separates them. It also fits a case where an existing regex needs checking against labeled cases before it goes into a validator or a search filter.

## When not to use

Do not use it for a regex written from a prose spec with no examples, because the proof table has nothing to prove against. Do not use it to tune a pattern against a large file or a live log stream, since the skill works from the pasted examples only. It is not a substitute for testing on real traffic, and it does not decide what counts as a correct label.

## Requirements

A text-capable agent. No network, no script, and no Python run is needed, because the proof table is worked out by hand from the pattern and each example.

## Example

The following is the complete output for the offline smoke set of ten labeled order IDs, shown as the skill delivers it.

````markdown
## Status

Status: partial

Passed 10 of 10 examples.
Rewrites used: 0 of 2.
The regex is proven only on these 10 supplied examples and makes no claim about other inputs.

## Columns

| ID | Label | Example |
|---|---|---|
| E01 | MATCH | ORD-100234 |
| E02 | MATCH | ORD-998877 |
| E03 | MATCH | ORD-000001 |
| E04 | MATCH | ORD-471120 |
| E05 | MATCH | ORD-555000 |
| E06 | NON-MATCH | ORD-12345 |
| E07 | NON-MATCH | ord-100234 |
| E08 | NON-MATCH | ORD100234 |
| E09 | NON-MATCH | ORD-1002345 |
| E10 | NON-MATCH | INV-100234 |

## Plain-words rule

Every MATCH string starts with the fixed uppercase prefix ORD- followed by exactly six digits, and every NON-MATCH string breaks that shape through its prefix, its case, its missing hyphen, its digit count, or its letters.

## Regex

```
^ORD-([0-9]{6})$
```

Flags: none

## Proof table

| ID | Label | Example | Expected | Actual | Groups | Pass |
|---|---|---|---|---|---|---|
| E01 | MATCH | ORD-100234 | MATCH | MATCH | ['100234'] | yes |
| E02 | MATCH | ORD-998877 | MATCH | MATCH | ['998877'] | yes |
| E03 | MATCH | ORD-000001 | MATCH | MATCH | ['000001'] | yes |
| E04 | MATCH | ORD-471120 | MATCH | MATCH | ['471120'] | yes |
| E05 | MATCH | ORD-555000 | MATCH | MATCH | ['555000'] | yes |
| E06 | NON-MATCH | ORD-12345 | NON-MATCH | NON-MATCH | - | yes |
| E07 | NON-MATCH | ord-100234 | NON-MATCH | NON-MATCH | - | yes |
| E08 | NON-MATCH | ORD100234 | NON-MATCH | NON-MATCH | - | yes |
| E09 | NON-MATCH | ORD-1002345 | NON-MATCH | NON-MATCH | - | yes |
| E10 | NON-MATCH | INV-100234 | NON-MATCH | NON-MATCH | - | yes |

## Ambiguous cases

| Candidate | Pattern decides | Example to label |
|---|---|---|
| "ORD-100234 " (trailing space) | NON-MATCH | Label a trailing-space ID to confirm whether padding is allowed |
| "ORD-１00234" (full-width first digit) | NON-MATCH | Label a full-width digit ID to confirm whether non-ASCII digits count |
| "" (empty string) | NON-MATCH | Label the empty string to confirm whether a blank field is a valid ID |

## Open questions

1. Candidate "ORD-100234 " (trailing space): is it a MATCH or a NON-MATCH?
2. Candidate "ORD-１00234" (full-width first digit): is it a MATCH or a NON-MATCH?
3. Candidate "" (empty string): is a blank field a MATCH or a NON-MATCH?
````

## Limits

The skill works only from the examples it is given. It does not know the business rule behind the IDs, so a pattern can pass every row and still accept or reject real orders the user never showed it. It does not check that the labels themselves are right, does not run the pattern against a live system, and does not test performance on large inputs. The backtracking rules are checked by reading the pattern, not by timing it. Ambiguous candidates are listed by reasoning about the pattern, not by an exhaustive search of inputs.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
