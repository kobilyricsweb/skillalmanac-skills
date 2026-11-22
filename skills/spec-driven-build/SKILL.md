---
name: spec-driven-build
description: Builds a feature from an agreed written spec without drifting, using numbered REQ-nnn requirements, acceptance checks, tests named after each requirement, a stop rule for ambiguous specs, and a script that lists requirements with no test, tests citing unknown requirements and requirements with no acceptance criteria as JSON. Use when the user says build from this spec, implement this spec, spec-driven, stay in scope, trace requirements to tests, or hands over a spec or ticket and wants it built exactly. Do not use for writing the product requirements document itself, scoping or estimating, or work with no written spec.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual trace in step 7.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Spec-driven build

Build exactly what an agreed spec says, prove each requirement with a test, and stop when the spec cannot be tested. The spec is the contract: you do not improve it silently, and you do not build outside it.

## Spec format this skill works with

One requirement per block, starting with an id at the beginning of a line (heading, list item or bold): `### REQ-004 Single use`. Ids are `REQ-` plus at least three digits and are never reused or renumbered. Each block has the requirement sentence and an acceptance check. Copy [assets/spec-template.md](assets/spec-template.md) when the user has no template. If the user's spec has no ids, add them first (see step 1).

A requirement is buildable only if all four hold: one observable behaviour; a number, message, status or state that a test can compare; a named trigger or precondition; an acceptance check starting `Acceptance:`, `AC1:` or `Given ...`. Rewrite examples for each failure are in [references/spec-format.md](references/spec-format.md); read it when a requirement fails one of the four.

## Workflow

```
- [ ] 1 Number and lint the spec
- [ ] 2 Apply the stop rule
- [ ] 3 Plan: requirement -> test -> file
- [ ] 4 Per requirement: test first, then code
- [ ] 5 Handle anything outside the spec
- [ ] 6 Full test run
- [ ] 7 Trace and report
```

1. **Number and lint the spec.** Run `python scripts/spec_trace.py SPEC.md` (no test directory yet). It reports `no_acceptance`, `open_markers`, `duplicate_ids`, `deferred` and advisory `vague_terms`. If the spec has no ids, add them in order without changing any wording, then tell the user the ids you added. Do not run the build against a spec that fails this step.
2. **Apply the stop rule** (table below) to every requirement before writing code. Stop only the affected requirements; build the independent ones.
3. **Plan.** Write a table: requirement id, test file and test name, source file expected to change. A requirement with no row has no work. A file you expect to change that maps to no requirement is a red flag: remove it from the plan or go to step 5.
4. **Per requirement, in id order:** write the test from the acceptance check, run it and see it fail for the right reason, then write the smallest code that passes it, then run the whole suite. Put the id in the test name or a comment beside it (`test_req_004_...`, `// REQ-004`) and in a comment at the code that implements it. One commit per requirement if the user wants commits.
5. **Outside the spec** (see table): a behaviour you find you need, a bug nearby, a better design. Do not build it. Record it as a spec change request and continue with the agreed spec.
6. **Full test run.** The whole suite, not only new tests. Failing tests that you did not touch are reported, never skipped, deleted or loosened to get green.
7. **Trace and report.** Run:

```bash
python scripts/spec_trace.py SPEC.md tests/ --src src/
```

   Fix every item in `no_test`, `only_skipped_tests`, `unknown_in_tests`, `no_acceptance`, `open_markers` and `duplicate_ids` or put it in the report as an open item with the reason. Never edit the script or the spec to make a check pass; spec edits need the user's agreement. Without Python, list the ids by hand with a text search for `REQ-` in the spec, the tests and the source, and compare the three lists.

## Stop rule

| Situation | Action |
|---|---|
| Requirement has `TBD`, `TODO`, `??`, `[NEEDS CLARIFICATION]` or "to be decided" | Stop on that requirement. Ask. |
| Two requirements cannot both pass (one says 30 minutes, another says 1 hour) | Stop on both. Quote both and ask which wins. |
| No observable pass/fail (`fast`, `easy`, `robust`, `appropriate`) | Stop. Offer one concrete number or message as a proposal and ask. Build only after a yes. |
| Acceptance check missing | Stop. Propose a check in the Given/when/then shape; build only after a yes. |
| Behaviour the code needs is not in the spec (error case, limit, default) | Pick nothing silently. Ask, or implement the narrowest option and list it under `Assumptions` in the report only when the user said to proceed without asking. |
| Spec contradicts the existing code or a test that passes today | Stop. Show both. The spec does not automatically win over a passing test. |
| Requirement marked `[deferred]` | Skip, do not test, list as deferred. |

Ask all open questions in one message: at most 5, each with your proposed answer, numbered by requirement id. While waiting, continue every requirement the question does not touch. If the user is unreachable, stop that requirement and say so in the report; do not guess.

## Drift control

A change request is allowed to exist; building it unasked is not. Write it as:

```
CHANGE REQUEST CR-1: <one line>
Why needed: <the requirement or test that cannot pass without it, or the bug>
Proposed text: <the new or edited REQ with Acceptance>
Effect if refused: <what stays broken or unbuilt>
```

Rules: a diff line that no requirement explains is reverted or turned into a change request; refactors that no requirement needs are not done; an extra safeguard you think is wise (logging, a retry, a new option) is a change request, not a quiet addition. Tests are written for requirements only; extra tests for your own additions would be drift too.

## Test naming and traceability

- The id appears in the test name or a comment on the test, written exactly `REQ-004`. Lower-case `req_004` in a function name is fine for readability only if the id also appears in a comment, because the script matches `REQ-` followed by digits.
- One requirement can have several tests; one test can cite several ids, but a test that cites more than two ids is probably testing too much.
- A reference inside a skipped, expected-fail or todo test (`@pytest.mark.skip`, `xit(`, `.skip(`, `@Disabled` within two lines above) does not count as coverage: the script lists it as `only_skipped_tests`.
- A test that only asserts `true` or only checks that code runs satisfies the script and not the spec. Before step 7, read each new test and confirm it compares the value, message or state named in the acceptance check.

## Script

`scripts/spec_trace.py SPEC.md [TESTS_DIR] [--src DIR] [--ext .py,.ts] [--require-code]`: run it, do not edit it. Strict JSON on stdout:

| Field | Meaning |
|---|---|
| `requirements`, `requirements_total` | ids found, in spec order |
| `no_acceptance` | ids with no acceptance line that has content |
| `open_markers` | `{id, line, marker}` for TBD-style markers |
| `duplicate_ids` | ids defined twice |
| `deferred` | ids tagged `[deferred]`, `[out-of-scope]` or `[dropped]`; exempt from the checks below |
| `vague_terms` | advisory `{id, line, term}`; never fails the run |
| `no_test` | ids no test file mentions (only with TESTS_DIR) |
| `only_skipped_tests` | ids mentioned only in skipped tests |
| `unknown_in_tests` | `{id, at}` for ids in tests that the spec does not define; `REQ-4` shows up here |
| `traceability` | id to the test files that cite it |
| `no_code` | ids absent from `--src` (a failure only with `--require-code`) |
| `ok` | true when nothing above except `vague_terms` and a plain `no_code` is non-empty |

Exit 0 pass, 1 problems, 2 bad input (missing path, no ids in the spec).

## Report

```
Spec: <file>, <n> requirements, <n> deferred
Built and traced: <ids>
Stopped, awaiting answer: <ids with the question>
Change requests: <CR list or none>
Assumptions made: <list or none>
Trace result: ok true/false; <remaining items>
Not checked: <e.g. test quality beyond naming, behaviour not in the spec, performance>
```

## Limits

- The script matches text. A test that names an id but checks nothing passes it; test quality is your reading, not the script.
- It does not run tests and does not know whether a cited test passes.
- Ids in a requirement's prose (for example "see REQ-002") are ignored in the spec but counted as references in the tests directory.
- Acceptance detection looks for lines starting with `Acceptance`, `AC`, `AC1`, `Given`, `Verify` or `Accept`; a spec that says "Done when" is reported as missing.
- Spec blocks end at the next requirement id or a heading of the same or higher level; free text after the last requirement belongs to it.
- Text files over 1 MB and binary files are skipped; the count is reported as `files_skipped_too_large`.
- Thresholds in the stop rule (5 questions, 2 ids per test, 2 lines of skip look-back) are working values, not measured optima.
