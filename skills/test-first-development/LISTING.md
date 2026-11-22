# Listing page content: test-first-development

**One line:** A strict red-green-refactor loop for agents, plus a script that catches tests that cannot fail.

## What it does

The skill makes an agent build one behaviour at a time: write a test, run it and record why it fails, write the least code that passes, refactor only on green. A phase table states the evidence each step must produce and when to stop (a test that errors on import is not a red; a test that passes at once is vacuous; a green step over about 15 lines means the test was too big). It adds a mutation check after green, a bug-fix-starts-red rule, a naming contract, a mock decision table (what to fake, what never to mock, how to wrap types you do not own), an edge-case checklist by input type, and a fixed report with a cycle log.

A script, `scripts/test_audit.py`, audits one pytest or JavaScript test file and prints strict JSON: zero-assertion tests, tests whose only assertions are trivially true (`assert True`, `expect(x).toBe(x)`), duplicated bodies, skips and expected failures without a written reason, a left-in `.only`, names that break the contract, and tests with more than 6 assertions.

## Capabilities

- Strict loop with required evidence per phase and a cycle log
- Naming contract for Python and JavaScript, overridable with `--name-regex`
- Mock decision table and test-double vocabulary
- Edge-case checklist for numbers, strings, collections, time, failure, state and limits
- `scripts/test_audit.py check <file>`: JSON report with per-test assertion counts and findings; exit 0 clean, 1 errors, 2 unreadable input

## When to use

You say TDD, test first, red green refactor, write the test before the code, or the agent's tests all pass but prove nothing. Also when you want an existing test file checked for worthless tests.

## When not to use

Adding tests to code that already exists and ships (characterisation work), refactoring, UI snapshot updates, end-to-end browser tests, and debugging a failing test.

## How it differs from nearby skills

- `spec-driven-build` starts from a written spec with numbered requirements and traces every requirement to a test and an acceptance check; its script checks requirement-to-test coverage. This skill has no spec: it governs the inner loop for each behaviour (red evidence, minimal green, mutation check) and audits test quality. The two combine well: the spec says what to build, this skill says how each piece is built.
- `simplify-and-refactor` changes existing code without changing behaviour, writing characterisation tests of current behaviour first and comparing before and after versions. This skill creates new behaviour from a failing test, and refactors only inside the green step of its loop.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent follows the manual audit in step 7.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Invocation: "Audit tests/test_cart.py with the test-first-development skill and fix every error."

Real output of `python scripts/test_audit.py check evals/fixtures/bad_tests.py` (trimmed to the summary and first findings), exit code 1:

```json
{"tool": "test_audit", "file": "bad_tests.py", "language": "python", "ok": false,
 "summary": {"tests": 10, "skipped": 2, "errors": 7, "warnings": 0,
   "by_rule": {"DUPLICATE_BODY": 1, "NAME_CONTRACT": 1, "NO_ASSERTION": 1, "SKIP_NO_REASON": 2, "TRIVIAL_ASSERT": 2}},
 "findings": [
   {"rule": "NAME_CONTRACT", "test": "test_total_works", "line": 7},
   {"rule": "NO_ASSERTION", "test": "test_total__empty_cart__returns_zero", "line": 11},
   {"rule": "TRIVIAL_ASSERT", "test": "test_total__single_item__returns_price", "line": 15}]}
```

The JavaScript fixture `bad_tests.test.js` gives 8 errors, including `ONLY_LEFT` at line 33 and `SKIP_NO_REASON` at line 24. The good fixtures exit 0 with no findings.

## Limits

- The audit checks syntax, not whether an assertion is right; the mutation check covers that.
- Custom assertion helpers count only when named `assert...`.
- JavaScript support is a subset: `it`, `test`, `.skip`, `.only`, `xit`, `xtest`, `fit`; `it.each` and generated tests are not seen.
- Duplicate detection is exact-body only.
- Thresholds (6 assertions, 15 lines, 4 title words) are working values, not measured optima.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 8 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Run the audit on an agent-written test file: 7 errors, each with a line number.
2. Ask for a fix test-first: the agent shows a red run, a minimal green and the mutation check.
3. Re-run the audit: `ok` true.
4. Show the cycle log and the "Not tested" line in the report.

## FAQ seeds

- Does it work with unittest? Yes for classes deriving from a `TestCase`; `self.assert*` calls count as assertions.
- Can I use my own naming style? Yes: pass `--name-regex` and state the style once.
- Does a clean audit mean my tests are good? No. It means they are not obviously worthless; the mutation check is the guard for meaning.
- Does it need network access? No.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
