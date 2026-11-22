# Listing page content: simplify-and-refactor

**One line:** Makes agent cleanups behaviour-preserving: tests first, one named change per commit, and a script that catches API drift.

## What it does

The skill gives an agent a seven-step refactoring discipline: define scope, record a baseline, write characterisation tests that pin down what the code does today (quirks included), apply one transformation from a named catalogue per commit, and compare the result with the starting version. A script, `refactor_diff.py`, parses the before and after versions of a Python file with `ast` and reports changed public signatures, removed names, added and removed imports, whether the top-level definitions are preserved, and which bodies changed. A list of what never belongs in a refactor (bug fixes, public renames, formatting churn, dependency bumps) keeps the cleanup small, and the agent reports those items as found, not fixed.

## Capabilities

- `scripts/refactor_diff.py BEFORE AFTER`: strict JSON; exit 0 when the public surface is preserved, 1 when it changed, 2 on an unreadable file or syntax error
- A 12-entry catalogue of safe transformations, each with preconditions, steps and a check
- A list of Python behaviour traps (mutable defaults, laziness, truthiness, exceptions, evaluation order, numbers, imports)
- A characterisation-test procedure and a fixed final report (goal, commits, behaviour, public surface, found not fixed, not checked)

## When to use

You say clean up this code, simplify, refactor, tidy, split this big function or reduce duplication, and the behaviour must stay the same. Also when an agent's earlier cleanup renamed things, changed a signature or reformatted half the file.

## When not to use

Bug fixes, new features, performance tuning, framework or dependency migrations, and rewrites in another language. The skill reports bugs it finds but does not fix them inside a refactor.

Difference from the nearby catalogue entries: it does not review pull requests in general (see `reviewing-code-changes`) and it does not write tests as a goal in itself; the tests exist to protect the refactor.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent compares `def`, `class`, `import` and `__all__` lines by hand from `git diff -U0`. The procedure itself applies to any language; the script handles Python files only.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so no saved refactor transcript is shown. What exists is the script on saved fixtures (`evals/fixtures/`), run on 2026-11-21:

1. A tidy refactor (`before.py` to `good_after.py`: a loop became `sum`, a helper was extracted, an unused import was removed). Command: `python scripts/refactor_diff.py evals/fixtures/before.py evals/fixtures/good_after.py`. Output (abridged): `"verdict": "surface_preserved"`, `"changed_signatures": []`, `"imports": {"added": [], "removed": ["import sys"]}`, `"bodies_changed": ["Order.total", "summarize"]`. Exit code 0.
2. A refactor that drifted (`bad_after.py`: a rename, a deleted function, a new required keyword argument, a new base class). Output (abridged): `"verdict": "surface_changed"`, `"removed_public_names": ["legacy_total", "summarize"]`, `"possible_renames": [{"from": "summarize", "to": "summarise"}]`, and a `changed_signatures` entry for `Order.total` with `"before": "(self, include_tax=True)"`, `"after": "(self, include_tax=True, *, rounding)"`, `"changes": ["required_param_added:rounding"]`, `"breaking": true`. Exit code 1.
3. A formatting-only change (`reformatted_after.py`): `"verdict": "ast_identical"`, exit code 0.

## Limits

- The script sees one file; it cannot find callers elsewhere, dynamic access or monkeypatching.
- `surface_preserved: true` does not prove behaviour is preserved; only the tests do, and they cover the inputs chosen.
- The script handles Python only.
- The catalogue is not exhaustive and does not decide whether a refactor is worth doing.
- Code with randomness, clocks, concurrency or external services needs fakes and may stay partly untested.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 6 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A 60-line function with no tests; the user says "clean this up, keep it working".
2. The agent writes characterisation tests, runs them green, and notes a mutable default argument as found, not fixed.
3. Two commits, "refactor: guard clauses on build_invoice" and "refactor: extract function _line_total"; after each, the script prints `surface_preserved: true`.
4. The final report, ending with the found-not-fixed and not-checked lines.

## FAQ seeds

- Does it need network access? No.
- Does it work for JavaScript or Go? The procedure and catalogue do; the comparison script is Python only, and for other languages the agent compares signatures by hand.
- Will it fix the bugs it finds? No. It lists them so you can decide; mixing fixes into a refactor is what the skill exists to prevent.
- Does `surface_preserved: true` mean it is safe? It means no public name or signature in that file moved. The tests are what show behaviour is the same.
- Why write tests for code I only want tidied? Because the tests record today's behaviour, quirks included, which is the only reliable definition of "unchanged".
- Will it reformat my files? Not unless you ask; formatting churn is on the not-a-refactor list.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.

## Differentiators (fix round 2026-11-21)

- Versus the built-in /simplify command: that reviews a diff and applies cleanups; this skill is a procedure (characterisation tests first, one named transformation per commit) with a before/after signature comparison.
- Versus `reviewing-code-changes` and tech-debt skills: those judge or inventory; this one changes code while preserving behaviour.
