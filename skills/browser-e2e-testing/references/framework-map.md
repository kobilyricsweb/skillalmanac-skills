# Framework map: the same policy in three runners

The policies in SKILL.md are vendor-neutral. This table maps each one to the call names in Playwright, Cypress and Selenium (Python or Java bindings). Names were written from the public documentation listed at the end; confirm against the version installed in the project before relying on a name.

| Need | Playwright | Cypress | Selenium |
|---|---|---|---|
| Find by role and name | `getByRole('button', { name })` | `findByRole('button', { name })` (Testing Library plugin) | No native role query; use label, text or test id |
| Find by label | `getByLabel(text)` | `findByLabelText(text)` | `By.cssSelector` on the labelled control, or XPath `label` lookup |
| Find by test id | `getByTestId(id)` (attribute name is configurable) | `cy.get('[data-testid="x"]')` | `By.cssSelector("[data-testid='x']")` |
| Narrow to a container | `parent.getByRole(...)`, `locator.filter({ hasText })` | `cy.within(...)`, `.contains(selector, text)` | Find the container element first, then search inside it |
| Retrying assertion | `await expect(locator).toBeVisible()` | `.should('be.visible')` | `WebDriverWait(driver, timeout).until(condition)` |
| Wait for a response | `page.waitForResponse(...)` registered before the click | `cy.intercept(...).as('x')` then `cy.wait('@x')` | No built-in network layer; poll the DOM, or use a proxy or the browser's devtools protocol |
| Poll a computed value | `expect.poll(fn)`, `expect(fn).toPass()` | `cy.should(callback)` | `WebDriverWait` with a custom condition |
| Fixed clock | `page.clock` API | `cy.clock()` / `cy.tick()` | Inject a fake-timers script, or set the system under test's time via a test hook |
| Mock or block a request | `page.route(url, handler)` | `cy.intercept(url, stub)` | Proxy or devtools protocol; or a test double in the app |
| Fresh state per test | New context per test (default) | `cy.session` plus clearing state between tests (test isolation is on by default in recent versions) | New driver or `delete_all_cookies()` plus storage clear per test; prefer a new browser profile |
| Stored login state | `storageState` file from a setup project | `cy.session(id, setup)` | Save and load cookies, or log in through an API call and add the cookie |
| Parallel run | Workers per file by default; `--shard=1/4` | Parallelisation needs a runner or paid dashboard; split spec files across CI jobs yourself | Test runner level (pytest-xdist, TestNG, JUnit) plus a grid or one browser per worker |
| Trace on failure | `trace: 'on-first-retry'` in config | Screenshots and video on failure by default in run mode; no trace viewer equivalent | Screenshot on failure in a teardown hook; browser logs saved |
| Forbid `.only` in CI | `forbidOnly: !!process.env.CI` | Lint rule or a grep step | Not applicable to most runners; use a marker check in CI |

## Notes that change behaviour

- Playwright locators are lazy: they are looked up again at every action, which is why storing an element handle is a flakiness source and storing a locator is not.
- Playwright and Cypress retry assertions for you; Selenium does not. In Selenium, every read of a page value needs an explicit wait, and implicit waits mixed with explicit waits add unpredictable delays, so use one style.
- Cypress commands are queued, not awaited like normal promises; do not wrap them in `async/await` and do not store their return values in variables.

## Sources (read in 2026-11; not re-fetched while writing this table)

- Playwright locators and best practices: https://playwright.dev/docs/locators and https://playwright.dev/docs/best-practices
- Playwright actionability checks: https://playwright.dev/docs/actionability
- Cypress best practices: https://docs.cypress.io/app/core-concepts/best-practices
- Selenium waits: https://www.selenium.dev/documentation/webdriver/waits/
