# Listing page content: regex-case-tester

**One line:** Builds a regex from a table of must-match and must-not-match strings and proves it, including backtracking risk.

## What it does

The skill makes an agent write the case table before the pattern: at least three strings that must match and three that must not, plus a stated full-match or search semantics. A script then compiles the pattern with Python `re`, runs every case, shows captures and timings, and adds generated adversarial cases (empty string, trailing newline, padded values, non-ASCII digits, junk around a match). It scans the parsed pattern for nested quantifiers, overlapping alternation, adjacent overlapping repeats and correctness traps such as `$` accepting a trailing newline or `[A-z]`. Flagged patterns get a short growth probe whose timings show whether time really explodes. Other regex flavours get a warning and an "indicative only" verdict, never a pass.

## Capabilities

- `scripts/test_regex.py`: strict JSON report (`pattern`, `compile`, `cases[]`, `static_flags[]`, `probe[]`, `untestable_constructs[]`, `verdict`)
- A documented list of backtracking shapes with safer rewrites, and a correctness pitfall table
- A flavour table (Python, JavaScript, PCRE, RE2/Go) with unconfirmed cells marked
- A fixed report: final pattern, cases, flags, reviewed adversarial cases, what was not checked

## When to use

You need a regex for a field and want proof, a pattern matches too much or hangs, or a pattern must move to another flavour and you want the traps listed.

## When not to use

Parsing HTML or JSON, grammars, log clustering, or checking that an email address or phone number is real. A regex checks shape only.

## Requirements

Python 3.9 or newer, standard library only, no network. Without Python the agent walks the cases by hand with the reference tables.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real runs of `python scripts/test_regex.py` on the saved fixtures:

1. `evals/fixtures/risky_email.json`, pattern `^([a-zA-Z0-9]+[._-]?)+@example\.com$` in search mode: all 6 user cases pass, but the verdict is `risky`. Flags: `nested_quantifier` (high) and `dollar_allows_trailing_newline` (medium); the probe reports `exponential_growth_seen`; the generated case `ann@example.com` plus a newline matches and is marked `review`; two longer generated cases are skipped under the 16-character cap. Exit code 1.
2. `evals/fixtures/search_vs_full.json`, pattern `\d{3}-\d{4}` in search mode: verdict `pass`, but `call 555-1234` and `555-12345` are noted as passing only because search accepts a substring, and six generated cases (padded values, a trailing newline, Arabic-Indic digits, junk before and after) are marked `review`.

## Limits

- Python `re` only; other flavours are never a pass.
- No preemptive time limit: a length cap and an early-stopping probe, so an unflagged catastrophic pattern on a long input can still hang.
- The static scan is heuristic: it can miss bounded repeats around unbounded ones and flag safe delimited loops.
- A case table proves only the cases in it.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 9 of 9 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. The user asks for a username validator; the agent writes six cases first.
2. The first draft `^([a-z0-9]+[._-]?)+$` passes every case but the script says `risky` and the probe shows exponential time.
3. The agent rewrites with a mandatory separator; the script says `pass`.
4. The report lists the adversarial cases reviewed and what was not checked.

## FAQ seeds

- Does it need network? No.
- Does it test JavaScript or PCRE patterns? No; it runs them through Python `re` as a stand-in, labels the result indicative only, and lists constructs it cannot test.
- Will it catch every catastrophic regex? No; the scan is a heuristic and the guard is a length cap, not a clock.
- How is it different from asking for a regex and a few examples? It fixes the order (cases first), runs them, adds adversarial inputs and checks backtracking. No comparison run exists yet.
- Does it write files? No; it reads a spec and prints JSON.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.
- Nearest skills: test-first-development, python-practices and validation-rule-conflict-map discuss testing or validation in general; this one executes labelled match and non-match cases against a pattern.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
