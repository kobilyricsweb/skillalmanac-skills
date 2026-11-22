---
name: test-first-development
description: Runs strict test-first development, red-green-refactor, when the user says TDD, test first, write the test before the code, or the agent's tests pass without proving anything. Covers the failing test, minimal code, refactor, a test naming contract, what to mock and never mock, an edge-case checklist, and a script that audits a pytest or JavaScript test file as strict JSON for zero-assertion tests, assert-True tests, duplicate bodies, skips without a reason and weak names. Do not use for adding tests to existing code after the fact, refactors, or UI snapshot work.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, use the manual audit in step 7.
metadata:
  license: Apache-2.0
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Test-first development

One behaviour at a time: a test that fails for the right reason, the least code that makes it pass, then cleanup with the tests green. A test you never saw fail proves nothing.

## The loop and what each phase must produce

Work on exactly one test at a time. Keep a cycle log (one row per cycle) and show it in the report.

| Phase | Do | Required evidence | Stop and fix if |
|---|---|---|---|
| RED | Write one test for one behaviour. Add only enough stub (a function that raises `NotImplementedError` or returns a wrong placeholder) for the file to import. Run it. | The failing output, and one line saying why it fails | It errors on import, name or syntax (a broken test, not a red). It passes (the test is vacuous or the behaviour exists: delete or sharpen the test). It fails for a reason other than the missing behaviour |
| GREEN | Write the smallest code that passes this test. A hard-coded return is allowed while only one test exists. | Test run showing this test and all earlier ones pass | You changed more than about 15 lines or touched a second function: the test was too big, revert and write a smaller one |
| REFACTOR | Rename, extract, remove duplication in code and tests. No new behaviour, no new test. | A full test run after each single change | A test goes red: undo the last change, do not debug forward |

Rules that keep the loop honest:

1. **Right red.** The failure message must name the behaviour you are about to add ("expected 3, got 0"), not a typo.
2. **Triangulate.** A second test with different data is what forces the hard-coded return to become real logic. Do not generalise before it exists.
3. **One failing test at a time.** Never write a second red test while one is red. Commit only on green.
4. **Mutation check after green.** Break the code you just wrote (flip a comparison, change a constant, delete a line) and confirm a test fails. If none fails, the test does not guard that code: strengthen it, then restore the code. Do this for every new branch, not for every line.
5. **Bug fixes start red.** First write a test that reproduces the bug and watch it fail, then fix. A bug fix without a failing test first is not done.
6. **Never edit a test to make it pass.** Change a test only when the requirement changed, and say so.
7. **No test, no code.** Code that no failing test demands is speculative: leave it out.

## Naming contract

| Language | Form | Passes | Fails |
|---|---|---|---|
| Python | `test_<unit>__<condition>__<outcome>`, lowercase snake_case, double underscore between the three parts | `test_total__empty_cart__returns_zero` | `test_total_works`, `test_total__basic__ok` |
| JavaScript or TypeScript | `'<unit> <outcome> when <condition>'`: at least 4 words and one of when, if, given, with, without, after, before, for, on | `'total returns zero when the cart is empty'` | `'works'`, `'should work'` |

A reader must learn the rule from the name alone, so a failing test name is the bug report. A different house style is fine if stated once; pass `--name-regex` to the script instead of fighting it.

## What to mock

| Dependency | Decision | Why |
|---|---|---|
| Network, third-party API, payment, email, SMS | Fake at the boundary you own (an adapter class or function); never hit the real service | Slow, flaky, costs money, leaks data |
| Clock, randomness, UUIDs, environment | Inject or freeze | Otherwise the test is nondeterministic |
| Filesystem, database | Real temporary directory or a real or in-memory test database where cheap; fake only when slow or shared | Mocks hide path, encoding and query bugs |
| Your own pure functions and classes | Never mock | You would test the mock |
| The unit under test | Never mock any part of it | Same reason |
| A collaborator in your own module | Use the real one; replace only if it needs the network, clock or disk | Keeps tests free of implementation detail |
| Types you do not own (HTTP client, ORM session) | Wrap them in a thin adapter, fake the adapter, test the adapter once against the real thing | Mocking another team's API freezes your guess about it |

Assert on outcomes (return values, stored state, emitted messages) before calls. A call assertion (`assert_called_once_with`) is acceptable only when the call is the behaviour, such as "sends exactly one email". A test that spends most of its lines on mock setup is testing the wiring: move the logic out so it can be tested without mocks. Fake, stub and spy differences and the adapter pattern are in [references/mocks-and-edge-cases.md](references/mocks-and-edge-cases.md).

## Edge-case checklist

Before leaving a unit, walk this list for each input and write a test or the words "N/A because ...". Do not skip silently.

- **Numbers:** zero, one, negative, maximum and minimum, off-by-one at each boundary, float rounding, NaN or infinity if reachable.
- **Strings:** empty, one character, whitespace only, very long, non-ASCII and combining characters, embedded quotes or newlines.
- **Collections:** empty, one element, duplicates, unsorted, already sorted, null elements, a collection mutated while read.
- **Dates and time:** midnight, month end, leap day, daylight-saving change, time zones, past versus future.
- **Absence and failure:** missing key, null argument, dependency raising, timeout, partial result, retry.
- **State:** called twice, called in the wrong order, called after close, concurrent callers.
- **Permissions and limits:** not allowed, over the quota, exactly at the quota.

Worked prompts and one full cycle are in [references/mocks-and-edge-cases.md](references/mocks-and-edge-cases.md).

## Workflow

```
- [ ] 1 List the behaviours, simplest first
- [ ] 2 Pick the first behaviour; write its test
- [ ] 3 RED: run, record the failure and why
- [ ] 4 GREEN: minimal code, run all tests
- [ ] 5 REFACTOR on green, run after each change
- [ ] 6 Repeat 2 to 5 per behaviour; walk the edge-case checklist
- [ ] 7 Audit the test file
- [ ] 8 Report
```

1. List behaviours first, simplest to hardest (empty input, single case, general case, errors). The list is the plan; add to it as cycles reveal more.
2. Write the test with arrange, act, assert in that order and a name from the contract. One behaviour per test, so normally one to three assertions.
3. Run only that test and read the output before touching code.
4. Run the whole file after green, not only the new test.
5. Refactor test code too: extract fixtures, remove duplicated setup. Never refactor with a red test.
6. Before finishing, apply the mutation check to each new branch and the edge-case checklist to each input.
7. Audit the test file with the script below. Fix every `error` finding; a `warning` needs a reason in the report. Without Python, check by hand: every test has an assert; none asserts only a constant; no two tests share a body; every skip has a written reason; every name passes the contract.
8. Report in this shape:

```
Cycles: <n> (table: behaviour | red reason | green change | refactor)
Mutation checks: <branches checked, any that survived and what you did>
Edge cases: <checklist items covered, each N/A with reason>
Audit: ok true/false, errors, warnings
Not tested: <what no test covers, honestly>
```

## Test audit script

`python scripts/test_audit.py check <test-file> [--lang python|javascript] [--name-regex REGEX]` prints one JSON object and changes nothing.

Output contract:

```json
{"tool": "test_audit", "schema_version": 1, "file": "x.py", "language": "python", "ok": false,
 "summary": {"tests": 3, "skipped": 0, "errors": 1, "warnings": 0, "by_rule": {"NO_ASSERTION": 1}},
 "tests": [{"name": "...", "line": 7, "assertions": 1, "trivial_assertions": 0, "skipped": false}],
 "findings": [{"rule": "NO_ASSERTION", "severity": "error", "test": "...", "line": 11, "message": "..."}]}
```

Rules: NO_TESTS, NO_ASSERTION, TRIVIAL_ASSERT, DUPLICATE_BODY, SKIP_NO_REASON, ONLY_LEFT, NAME_CONTRACT (all errors) and ASSERT_HEAVY (warning, more than 6 assertions). Exact definitions: [references/audit-rules.md](references/audit-rules.md). Exit 0 when there are no errors, 1 when any error, 2 with `{"ok": false, "error": "..."}` for a missing, empty or unparsable file or a bad argument. Run it; do not edit the script or the test to silence a finding. A skip is valid only with `reason=` in Python or a `// skip: <reason>` comment in JavaScript.

## Boundaries

- Tests for code that already exists and is already shipped are characterisation work: use a refactoring skill for that, not this loop.
- A requirement document drives scope in a spec-driven workflow; this skill only governs how each behaviour is built.
- Tests never call real networks or production systems.

## Limits

- The audit sees syntax, not meaning: a test can pass every rule and still assert the wrong thing. The mutation check is the only guard against that.
- Python assertions are counted from `assert` statements, `self.assert*`, `mock.assert_*` and `pytest.raises` or `warns`. A custom helper counts only if its name starts with `assert`; otherwise a test that relies on it is reported as having no assertion.
- JavaScript is scanned with a subset scanner: `it`, `test`, their `.skip` and `.only` forms, `xit`, `xtest`, `fit`. Tests built with `it.each`, loops or dynamic registration are not seen.
- Duplicate detection compares exact bodies; near-duplicates are not found.
- The numbers (6 assertions, 15 lines, 4 words) are working values, not measured optima.
- Strict test-first pays off most for logic with clear inputs and outputs. For exploratory spikes and UI layout, write a throwaway spike, delete it, then redo it test first.
