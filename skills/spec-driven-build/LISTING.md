# Listing page content: spec-driven-build

**One line:** Builds a feature from an agreed spec, one numbered requirement at a time, and proves each one with a test.

## What it does

The skill gives an agent a seven-step build discipline for a spec whose requirements carry ids like `REQ-004`: lint the spec, apply a stop rule to anything ambiguous, plan requirement to test to file, write each test before its code, route anything outside the spec into a change request, run the whole suite, and trace. A script parses the spec and a test directory and reports requirements with no referencing test, tests that cite unknown requirements, tests that are skipped, and requirements with no acceptance criteria, as strict JSON. The stop rule is a table of seven situations (TBD markers, conflicting requirements, untestable wording, missing acceptance, gaps, contradiction with passing code, deferred items) with one action each.

## Capabilities

- `scripts/spec_trace.py SPEC.md [TESTS_DIR] [--src DIR]`: JSON with `no_acceptance`, `open_markers`, `duplicate_ids`, `deferred`, `vague_terms`, `no_test`, `only_skipped_tests`, `unknown_in_tests`, `traceability`, `no_code`, `ok`
- A spec template with numbered requirements and acceptance checks
- A reference of vague-to-testable rewrites and test naming per language
- A change-request format and a fixed final report that lists what was stopped, assumed and not checked

## How it differs from `prd-writer`

`prd-writer` (batch 01) helps decide what to build and why: problem, users, goals, scope. This skill starts after the spec is agreed and is about build discipline: tests named after requirements, no work outside the spec, a stop on ambiguity and a coverage trace. Use `prd-writer` to produce the document; use this skill to implement it. It also differs from `plan-stress-test` (attacks a plan before work) and `scope-change-brief` (communicates a scope change): here, scope changes are only recorded as change requests while building.

## When to use

You hand over a written spec, ticket or numbered requirement list and say build this exactly, implement from the spec, stay in scope, or check every requirement has a test.

## When not to use

Writing the product requirements document, estimating or scoping, reviewing a pull request, adding tests to code with no spec, or work with nothing written down.

## Requirements

Python 3.9 or newer for the script (standard library only). No network. Without Python the agent compares the `REQ-` ids by text search.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved build to show. What exists is the script on the saved fixtures.

1. `python scripts/spec_trace.py evals/fixtures/spec_bad/SPEC.md evals/fixtures/spec_bad/tests` returns exit code 1 and, among other fields:
   `no_acceptance: ["REQ-002"]`, `open_markers: [{"id": "REQ-002", "line": 10, "marker": "TBD"}]`, `duplicate_ids: ["REQ-003"]`, `no_test: ["REQ-002", "REQ-004"]`, `only_skipped_tests: ["REQ-003"]`, `unknown_in_tests: REQ-4 and REQ-099`, `ok: false`.
2. `python scripts/spec_trace.py evals/fixtures/spec_good/SPEC.md evals/fixtures/spec_good/tests --src evals/fixtures/spec_good/src` returns exit code 0 with `ok: true`, 5 requirements (one deferred), a `traceability` map from each of REQ-001 to REQ-004 to its test file, and `no_code: []`.

## Limits

- The script matches text: a test that cites an id but checks nothing passes it.
- It does not run tests.
- Acceptance lines must start with `Acceptance`, `AC`, `Given`, `Verify` or `Accept`.
- Thresholds in the stop rule are working values, not measured optima.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and the 5 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Hand over a rate-limiter spec with one `TBD`; the script lint shows `open_markers` on REQ-002.
2. The agent asks one question with a proposed answer and builds REQ-001, 003 and 004 test-first.
3. Mid-build a request for an extra feature becomes a change request, not code.
4. `spec_trace.py` returns `ok: true` except REQ-002 listed as awaiting an answer.

## FAQ seeds

- Does it need network access? No.
- Does it work with specs that have no ids? Step 1 adds ids without changing wording and tells you.
- Does it run my tests? No; the agent runs them, the script only traces ids.
- Can it check that tests are good? No; it checks that tests cite requirements, and the agent reads them for substance.
- How is it different from a PRD skill? See the section above.
- Will it refuse to touch code outside the spec? It will not build it unasked; it writes a change request and continues.
- Which languages? Any: the script matches `REQ-nnn` text in common code and test file types.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
