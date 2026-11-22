# Listing page content: browser-e2e-testing

**One line:** Helps an agent write reliable browser end-to-end tests and audits spec files for flakiness patterns.

## What it does

The skill gives an agent a seven-step procedure for browser tests: read the project setup, decide what belongs at E2E level, write the test under a selector policy (role and label first), a no-sleep wait policy and per-test isolation, run it alone, repeated and in parallel, prove it can fail, audit it and report. A decision table separates E2E work from unit, component and API work. A twelve-row triage table maps flaky symptoms to causes and fixes. A bundled script statically audits Playwright, Cypress and Selenium-style test files (.spec/.test/.e2e JS or TS, and Python test files) and prints strict JSON.

## Capabilities

- `scripts/audit_e2e.py`: eleven rules (hard-sleep, only-left-in, debug-leftover, test-without-assertion, brittle-selector, shared-mutable-state, missing-isolation-hooks, shared-browser-state, serial-order-dependence, networkidle-wait, force-action), per-finding line numbers, severity and message, per-line suppression comments, exit code by severity
- Reference: the same policies mapped to Playwright, Cypress and Selenium call names
- Reference: CI settings table (workers, shards, retries, trace, screenshot, video), artifact rules, trace-reading steps, quarantine procedure
- A fixed report: scope, level check, run counts, proof of failure, audit result, residual risk, not checked

## When to use

You ask for e2e or browser tests, a flaky or intermittent UI test, Playwright help, tests that pass locally but fail in CI, or an audit of test files for sleeps, brittle selectors, missing assertions, shared state or a leftover `.only`.

## When not to use

Unit or component tests (see `test-first-development` for unit-level work), API-only tests, visual-regression services, load testing, scraping or form automation, native mobile apps.

## How it differs from nearby skills

`test-first-development` is about the red-green-refactor loop at unit level. This skill starts where a real browser begins: selectors, waits, isolation, flake triage and CI artifacts. It does not teach test-driven design.

## Requirements

Python 3.9 or newer for the audit script (standard library only, no network, reads only the paths given, writes nothing). Without Python the agent uses the grep fallback in SKILL.md step 6.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs come from `python evals/run_fixtures.py` runs saved in `evals/fixtures/RESULTS.txt`, and from the audit script on the saved task input.

1. `python scripts/audit_e2e.py evals/files/t1-flaky-checkout/checkout.spec.ts` (the flaky spec used by eval task t1): `ok` false, 3 tests, 10 findings: `shared-mutable-state` line 3, `test-without-assertion` line 5, `hard-sleep` lines 7 and 15, `brittle-selector` lines 8, 9, 16 and 23, `only-left-in` line 20, `force-action` line 23. Exit code 1.
2. `python scripts/audit_e2e.py evals/fixtures/good.spec.ts`: `ok` true, 4 tests, no findings, exit code 0. The file mentions `waitForTimeout` and `.only` only in a comment, uses a helper named `expectCartTotal`, and has a conditional `test.skip`; none of these are reported.

## Limits

- Line and block heuristic, not a parser; regex literals and unusual quoting can confuse the masking.
- Assertion detection trusts helper names; a misleadingly named helper hides a gap, and an assertion helper with another name is reported falsely.
- Brittle-selector detection sees string-literal selectors only.
- Isolation rules cannot see unique per-test data or resets done outside the file.
- A clean audit does not prove a test is reliable or worth having.
- Numeric thresholds are working values, not measured optima.

## Evidence

See `VERIFICATION.md`. In short: static lint passed with 0 FAIL and 0 WARN, and 9 of 9 script fixture cases pass with expected values derived by hand. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review, and a run of the audit on a real project's tests.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A flaky spec (the t1 input): run the audit, 10 findings, exit 1.
2. The agent replaces sleeps with retrying assertions and the positional selectors with role locators, and gives each test its own cart.
3. Repeat 10 times in parallel; break the behaviour once to see the test go red.
4. Re-run the audit: `ok` true; show the report with "Not checked".

## FAQ seeds

- Does it need network access? No.
- Does it work with Cypress or Selenium? The policies apply and the audit reads those files; the API name map covers them. Only Playwright-style tests have been used as fixtures, and no runner was executed.
- Will it run my tests? The agent runs them with your project's own command. The audit script never executes a test.
- Is a clean audit enough? No; it only means none of the documented patterns matched.
- How is it different from `test-first-development`? That skill is unit-level; this one is the browser layer.
- Does it add a lint rule to my repo? No. It reads files and prints JSON.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures run on this version; no other evidence.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet.
