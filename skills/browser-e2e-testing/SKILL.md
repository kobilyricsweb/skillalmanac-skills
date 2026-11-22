---
name: browser-e2e-testing
description: Writes, repairs and audits end-to-end browser tests (Playwright, Cypress, Selenium). Use when the user asks for e2e or browser tests, a flaky or intermittent UI test, Playwright help, tests that pass locally but fail in CI, or an audit of spec files for sleeps, brittle selectors, missing assertions, shared state or a leftover .only. Applies a selector policy, a no-sleep wait policy, per-test isolation, a flake triage table, CI parallelism and trace artifacts, and a static audit script. Do not use for unit tests, API-only tests, visual-regression services, load testing or scraping.
license: Apache-2.0
compatibility: The optional audit script needs Python 3.9 or newer, standard library only, and no network. Without Python, run the grep fallback in step 6.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Browser end-to-end testing

An end-to-end (E2E) test drives a real browser through a user journey against a running app. It is slow and costly, so each one must earn its place, be independent of every other, and fail only when the product is broken. Unit-level tests (one function or component, no browser) belong to `test-first-development`; this skill covers the browser layer only.

## Workflow

```
- [ ] 1 Read the project's setup before writing anything
- [ ] 2 Decide what belongs at E2E level
- [ ] 3 Write the test: selectors, waits, data
- [ ] 4 Run it alone, then repeated and in parallel
- [ ] 5 Prove it can fail
- [ ] 6 Audit with the script
- [ ] 7 Report
```

1. **Read the setup.** Find the runner config (`playwright.config.*`, `cypress.config.*`, `conftest.py`, a Selenium base class), the existing page objects or helpers, how the app is started, how test data is created and how auth is handled. Follow the project's conventions and language; do not introduce a second framework. Note the base URL, the timeout values and whether `forbidOnly`-style protection is set.
2. **Decide the level** with the table below. If the behaviour can be checked without a browser, write that test instead and say so.
3. **Write the test** under the three policies below. One test = one user journey with a name that states the outcome ("guest can pay by card and sees the receipt"), not the mechanics.
4. **Run it** alone with the project's own command, then repeated (Playwright: `--repeat-each=10`; others: a shell loop of 10) and with the parallel worker count CI uses. Require 10 of 10 passes in both. A test that needs a retry to pass is not done.
5. **Prove it can fail.** Break the behaviour it covers (comment out the handler, change the expected text, point it at a wrong id) and confirm the test goes red at the intended assertion, then restore. A test never seen failing is unproven.
6. **Audit.** Run `python scripts/audit_e2e.py <test file or folder>` and fix every `error`; justify or fix every `warn`. Fix the test, not the script, and do not add `e2e-audit-ignore` comments to get a pass unless the finding is a false positive you can explain in the report. Without Python, search the files for: `waitForTimeout|sleep\(|setTimeout|cy\.wait\(\d`, `\.only\(`, `nth-child|nth\(|css-[a-z0-9]{5}`, `networkidle`, `force: true`, `page.pause|debugger`, and read each test for a final assertion.
7. **Report** in the fixed format at the end of this file.

## What to test at E2E level

| Behaviour | Level | Why |
|---|---|---|
| Revenue or sign-up journey (register, log in, search, pay, publish) | E2E | Crosses UI, API, auth and data; nothing lower proves it works together |
| Wiring: a form posts to the right endpoint and the result renders | E2E, one happy path | Integration failure is the E2E layer's unique catch |
| Validation rules, edge cases, error messages, formatting | Unit or component test | Dozens of cases; at 5 to 30 seconds each in a browser they cost minutes |
| Every permutation of a filter or a table sort | Component test, or API test | Same reason; keep one E2E path through the filter |
| Backend business rules (pricing, permissions matrix) | API or service test | No browser needed, 100 times faster |
| Layout and pixel appearance | Visual test, separate tool | Assertions on text do not catch it |
| Third-party widgets (payment iframe, captcha, OAuth consent) | Mock at the network edge, plus one scheduled check against the real sandbox | Provider outages must not fail your build |

House target: E2E tests are under about 10 percent of all tests, one journey each, under 60 seconds each (a test over 60 seconds or over about 15 user actions is two tests), and the whole suite under 10 minutes of wall time in CI by adding workers or shards. These are working values, not measured optima.

## Selector policy

Locate elements the way a user or an assistive technology finds them. In order of preference:

1. Role plus accessible name: `getByRole('button', { name: 'Pay now' })`. Cypress: Testing Library `findByRole`. Selenium: no native equivalent; use the label or test id rows.
2. Label or placeholder for form fields: `getByLabel('Email')`.
3. Visible text for static content, matched exactly or by a stable fragment, never by a position.
4. Test id attribute (`data-testid`) when the element has no accessible name or the text changes by locale. Agree the attribute name with the team; never use ids generated by the framework.
5. CSS or xpath only inside an already scoped container, and only on attributes the team controls (`[data-state="open"]`).

Never use: `:nth-child`, `.nth(N)` on a list whose order is not the point of the test, class names that carry a hash (`css-1a2b3c`, `Button_root__3xK2a`, `sc-` prefixes), generated ids (`#:r1:`, `#radix-...`), absolute or indexed xpath (`//div[2]/span`), long `>` chains, or `[class*=...]` matching. To pick one of many identical rows, filter by its content (`row.filter({ hasText: 'Order 1042' })`) or scope to a container found by role, not by index.

A locator must match exactly one element. If it matches several, fix the locator; do not take `.first()` to silence the error unless "any one of them" is genuinely what the test means.

## Wait policy

Never wait for a fixed time. Wait for the condition the next step needs:

| The test needs | Use |
|---|---|
| An element to appear, change or disappear | A retrying assertion: `await expect(locator).toBeVisible()`, `toHaveText`, `toBeHidden` (Cypress `.should(...)`, Selenium explicit `WebDriverWait`) |
| A click target to be ready | Nothing: the runner already checks visible, stable, enabled and unobscured before acting. Do not add `force: true`; it turns those checks off and hides real overlays |
| A navigation | `expect(page).toHaveURL(...)` or an assertion on the next page's heading |
| A specific network result | Register the wait before the action that triggers it, then await it (`waitForResponse`, `cy.intercept` plus `cy.wait('@alias')`) |
| A value computed after several steps | `expect.poll(...)` or `toPass()` around one idempotent check |
| Time itself (a countdown, a session expiry, "today") | Control the clock in the test; never sleep |

Do not use `networkidle` as a ready signal: polling, analytics and websockets keep a page "busy" forever or let it pass too early. Keep the runner's default timeouts (about 5 s per assertion and 30 s per test) unless a measured slow step justifies a larger value on that one assertion; raising the global timeout to fix flakiness hides the cause.

## Isolation and data

Each test must pass alone, in any order, in parallel with every other test, and twice in a row.

- Fresh browser context per test (cookies, storage and cache empty). Do not share a page or a logged-in session created in a `beforeAll`; log in through a stored auth state that tests only read, produced once by a setup step.
- Create the data a test needs through the API or a seed helper, not by clicking through the UI; click through the UI only for the journey under test.
- Make created data unique per test and per worker (a random or worker-indexed suffix on names and emails) so parallel tests and reruns cannot collide.
- Clean up in `afterEach` or a fixture teardown, or run against a database reset between runs. Cleanup failure must not fail the test, but must be logged.
- Mutating tests never share one user account. A read-only test may share a seeded account.
- No module-level variable written by one test and read by another; no `serial` mode or ordered test chain unless the order is the product behaviour (an onboarding wizard split into several tests is still better as one test).
- Block or mock third parties the test does not own; keep one scheduled test per integration against the real sandbox.

## Flakiness triage

Start from the failure artifact (trace, screenshot, video, log), not from a rerun. Reproduce with 20 repeats before and after the fix.

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| Passes locally, fails only in CI | Slower machine, smaller viewport, different locale or timezone, missing fonts | Compare viewport, locale, timezone, browser version in the CI trace | Pin viewport, locale, timezone and browser version in config; remove any sleep that hid slowness |
| Fails only when run in parallel | Shared account, shared records, unique-constraint clash | Run with 1 worker; failure disappears | Per-test data with unique suffix; no shared mutable account |
| Fails only after another specific test | Order dependence, leaked state or cookies | Run the failing test alone, then after its predecessor | Fresh context; create data inside the test; remove `serial` |
| "Element is not stable / intercepts pointer events" | Animation, spinner, cookie banner or toast covering the target | Trace screenshot at the failing action shows the overlay | Wait for the overlay to be hidden by assertion; dismiss the banner in setup; disable animations in test mode. Not `force: true` |
| "Element detached from DOM" | Re-render between locate and act | Locator was stored from a handle, not re-queried | Use locators (lazy, re-resolved), not element handles |
| Strict-mode violation (several matches) | Locator too loose | Count matches in trace | Scope to a container or filter by content |
| Assertion fails then passes on retry | Assertion made before async data arrived, or a non-retrying check | Assertion reads a value once (`expect(await el.innerText())`) | Use the retrying form (`await expect(el).toHaveText`) |
| Timeout on first test of the run only | Cold start of server or database, lazy compilation | First test slow in every CI run | Warm up in a global setup step; wait for a health endpoint before the suite |
| Fails near midnight, month end, or on a given weekday | Real clock in the test or the app | Failure times cluster | Fixed clock in the test; relative dates built from it |
| Intermittent on a third-party call | Real external service | Failing request in network log | Mock at the network edge; scheduled sandbox check separately |
| Passes, but a later test sees leftovers | Missing cleanup | Records from earlier runs in the database | Teardown or reset; unique data |
| Random locale, text or sort mismatch | Data generated with random content the assertion assumes | Seed differs per run | Seed the generator; assert on values the test created |

Retry policy: allow 1 retry in CI (2 at most) and record every test that passed only on retry as a defect, because a retry reports a flake, it does not fix one. House default for quarantine: a test that fails without a product change in 2 or more of its last 50 runs (4 percent or more) is moved out of the blocking run with an owner and a 14-day deadline to fix or delete it.

## CI parallelism and artifacts

Read [references/ci-and-artifacts.md](references/ci-and-artifacts.md) when asked to set up or tune CI, sharding, retries or reports. Minimum contract: run tests in parallel across files; use about half the CPU count as workers on shared runners; shard across machines when one runner exceeds 10 minutes; fail the build if a focus marker (`.only`) is present; capture a trace on the first retry, a screenshot and video on failure; upload the artifacts even when the job fails.

For the equivalent API names in Playwright, Cypress and Selenium (locator, wait, intercept, clock, isolation), read [references/framework-map.md](references/framework-map.md) when working in a framework you were not shown an example of.

## The audit script

`scripts/audit_e2e.py`: run it, do not edit it.

```
python scripts/audit_e2e.py <file-or-folder> [more paths] [--disable RULE,RULE] [--fail-on error|warn|never]
```

Scans `.spec.*`, `.test.*`, `.e2e.*` (JS/TS) and `test_*.py`, `*_test.py` files; a file passed by name is always scanned. Prints one strict JSON object. Exit 0 when nothing at the `--fail-on` level (default `error`), 1 when something is, 2 on a usage problem or when no test file is found.

Top-level fields: `tool`, `version`, `ok` (true when no `error` finding), `files_scanned`, `tests_found`, `counts_by_severity`, `counts_by_rule`, `suppressed_by_comment`, `findings`, `skipped_files`, `limits`. Each finding: `file`, `line`, `rule`, `severity`, `message`, `snippet`.

| Rule | Severity | Flags |
|---|---|---|
| `hard-sleep` | error | `waitForTimeout`, `setTimeout`, `sleep(`, `cy.wait(<number>)`, `browser.pause` |
| `only-left-in` | error | `.only`, `fit`, `fdescribe` (JS/TS) |
| `debug-leftover` | error | `page.pause()`, `debugger`, `breakpoint()`, `pdb.set_trace()` |
| `test-without-assertion` | error | A test body with no assertion call |
| `brittle-selector` | warn | Positional pseudo-classes, `.nth(N)`, hashed classes, generated ids, indexed xpath, `[class*=]`, deep chains |
| `shared-mutable-state` | warn | A value declared outside tests, written in one test, used by two or more |
| `missing-isolation-hooks` | warn | Tests that create data in a file with no teardown, cleanup or fixture-with-cleanup |
| `shared-browser-state` | warn | `beforeAll` that opens a page or logs in; module/session-scoped page fixtures |
| `serial-order-dependence` | warn | `mode: 'serial'`, `describe.serial`, ordering markers |
| `networkidle-wait` | warn | `networkidle` |
| `force-action` | warn | `force: true`, `force=True` |

A line, or the line above it, containing `e2e-audit-ignore: <rule>` silences that rule there; the count is reported in `suppressed_by_comment`. Every `skipped_files` entry has a `reason`.

Treat the output as a list of questions. The script reads text, not meaning: it reports patterns, and cannot tell whether a test is worth having.

## Report format

```
Scope: <files written or changed, framework, base URL>
Level check: <what was kept at E2E level, what was moved or left to lower levels>
Runs: <alone N/N, repeated N/N, parallel N/N; command used>
Proven to fail: <the change made to break it, the assertion that went red>
Audit: <ok true/false, counts by rule, suppressions with reasons>
Residual risk: <warn findings kept and why; shared data; third-party dependence>
Not checked: <browsers or viewports not run, CI not run, a11y or visual coverage>
```

## Limits

- The audit is a line and block heuristic. It is not a parser: regex literals and unusual quoting can confuse its comment masking, and it sees only selectors written as string literals.
- `test-without-assertion` treats helper calls named `expect...`, `assert...`, `verify...`, `ensure...`, `validate...` and `check` followed by a capital as assertions. A helper with a misleading name hides a gap; a helper with another name causes a false report.
- `missing-isolation-hooks` cannot see unique per-test data or an environment reset done outside the file; `shared-mutable-state` cannot see state held in other modules or in the application.
- A clean audit does not prove a test is reliable or useful. Reliability comes from the repeat, parallel and must-fail runs in steps 4 and 5.
- The numeric thresholds (10 percent, 60 seconds, 15 actions, 10 minutes, 4 percent over 50 runs, 14 days) are working values, not measured optima; follow the project's own numbers where it has them.
- Written for web apps in desktop or mobile-emulated browsers. Native mobile apps, desktop apps and extensions need other tools.
- Do not point tests at production systems you do not own or at accounts holding real customer data, and do not store real credentials in test files.
