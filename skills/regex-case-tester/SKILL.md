---
name: regex-case-tester
description: Writes a regular expression from a spec by building a table of strings that must match and strings that must not match first, then runs the table with Python re, reports failing cases, flags catastrophic-backtracking shapes (nested quantifiers, overlapping alternation) and anchoring or Unicode traps, and marks other flavours as indicative only. Use when the user needs a regex for a field, asks why a regex matches too much or hangs, or wants a pattern proven with test cases. Do not use for text parsing that needs a grammar, HTML or JSON parsing, or log analysis.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only, and uses no network. Without Python, follow the manual procedure in step 5 and the reference tables.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Regex case tester

A regex is not done when it looks right. It is done when a written table of cases agrees with it. Write the table first, then the pattern.

## Workflow

```
- [ ] 1 Get the spec: intent, flavour, full-match or search
- [ ] 2 Write the case table (3+ match, 3+ no-match)
- [ ] 3 Draft the pattern
- [ ] 4 Save the spec file and run the script
- [ ] 5 Fix, re-run until verdict is pass
- [ ] 6 Report
```

1. **Spec.** Ask for, or state as an assumption: what the text means in words, the target flavour (default Python `re`), and the semantics. Field validation means fullmatch; finding something inside text means search. Never leave this implicit; the same pattern gives different answers under each.
2. **Case table before the pattern.** At least 3 strings that must match and 3 that must not. Include the boundary values: shortest and longest valid, one char too short, one char too long, a valid value with a trailing space, with a trailing newline, with the wrong separator. Take the "must not" cases from what real bad input looks like, not from random text. If the user gives fewer, add cases and label them as yours.
3. **Draft** the narrowest pattern that satisfies the table. Prefer explicit classes (`[0-9]`, `[^,]*`) over `.`; escape literal dots; avoid a repeat wrapped around a repeat; use `(?:...)` unless a capture is needed.
4. **Run.** Save a JSON spec (fields below) to a file and run `python scripts/test_regex.py spec.json`. For a quick change, re-run with `--no-probe` to skip the growth probe.
5. **Fix.** For each `verdict: "fail"` case, decide whether the pattern or the case is wrong and say which. Never delete a case to make the run pass. Then read `static_flags`, `probe` and every adversarial case with `verdict: "review"` (inputs that probably should not match but did). Without Python, walk each case by hand and read `references/backtracking-risks.md` against the pattern.
6. **Report** in the fixed shape under "Report".

## Spec file

```json
{"pattern": "\\d{5}(-\\d{4})?", "flavour": "python", "mode": "fullmatch", "flags": ["a"],
 "match": ["12345", "12345-6789", "00501"], "no_match": ["1234", "123456", "12345-"]}
```

`flavour`: python, js, pcre, re2, java, dotnet, go or other. `mode`: fullmatch or search. `flags`: any of i m s x a. Patterns inside JSON need doubled backslashes.

## Script output

`python scripts/test_regex.py spec.json` prints one JSON object and writes nothing. Run it; do not edit it to make a check pass.

| Field | Meaning |
|---|---|
| `compile` | `ok`, or `error`, `position`, `line`, `column` of the syntax error |
| `cases[]` | `input`, `kind` (user or adversarial:...), `expected`, `actual`, `verdict` (pass, fail, skipped, observed, review), `groups`, `named`, `span`, `ms`, `alt_semantics`, `note` |
| `static_flags[]` | `id`, `severity` (high, medium, low), `message`; ids are defined in `references/backtracking-risks.md` |
| `probe[]` | growth test on short strings built from a flagged shape: `verdict` is `exponential_growth_seen`, `polynomial_growth_seen`, `no_blowup_seen` or `not_run_exponential_risk` |
| `untestable_constructs[]` | syntax Python `re` cannot test (`\p{..}`, `(?<name>`, possessive on old Python) |
| `warnings[]`, `summary` | plain-language notes; counts per case verdict |
| `verdict` | pass, fail, risky, incomplete, invalid_pattern, untestable or indicative_only |

Exit code 0 only for `pass`; 1 for any other verdict; 2 when the spec is missing or malformed.

Verdict rules, in order: pattern does not compile gives invalid_pattern (untestable if the flavour is not Python or an untestable construct is present); any user case failing gives fail; a user case skipped or fewer than 3 cases of either kind gives incomplete; a high-severity flag or growth seen in the probe gives risky; a non-Python flavour gives indicative_only; otherwise pass.

Adversarial cases are generated, never counted as failures: empty string, the first match case with a trailing newline, a leading and trailing space, Arabic-Indic digits in place of ASCII digits, a case flip, a non-ASCII letter, and in search mode junk before and after. They show `review` when something that probably should not match did. Decide each one with the user.

## Reference files

- [references/backtracking-risks.md](references/backtracking-risks.md): read when a `static_flags` id appears or the pattern has a loop; it holds the documented risk list with safer shapes, and the correctness pitfalls.
- [references/flavour-differences.md](references/flavour-differences.md): read when the target is not Python, or a pattern uses lookbehind, named groups, possessive or atomic syntax, `\d` or `$`; it holds the construct table, anchor rules and the translation steps.

## Report

```
Pattern: <final pattern> (<flavour>, <fullmatch|search>, flags <...>)
Cases: <n match> must-match, <n no-match> must-not-match (<k> added by me); all pass: yes/no
Flags: <static flags with ids and what was done>
Reviewed adversarial cases: <which matched, and the decision>
Not checked: <other flavours, input over the length cap, anything the script cannot see>
```

For a non-Python flavour the report states "not tested in the target engine" and lists what must be re-run there.

## Limits

- The script tests Python `re` only. For any other flavour the verdict is never pass, and a pattern using syntax Python lacks is reported as untestable.
- There is no preemptive time limit. The guard is a length cap: inputs over 2000 characters are skipped, and over 16 characters when a high-severity risk was found. The probe stops growing after one run over 0.05 seconds. A catastrophic pattern the static scan misses, run against a long input outside the script, can still hang.
- The static scan is a heuristic over Python's parsed pattern. It misses bounded repeats around unbounded ones (`(.*,){11}`), backreference blow-ups and some lookaround loops, and can flag a delimited loop that is safe. A clean scan is not proof of safety; a probe that shows no growth is not proof either.
- Thresholds (cap 16 and 2000, 0.05 second stop, growth ratios 2.5 and 3.0) are working values, not measured optima.
- A case table proves only the cases in it. Say so in the report.
- The skill does not validate that a string is a real email address, phone number or URL; a regex checks shape only.
