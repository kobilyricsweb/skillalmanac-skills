# CI parallelism, retries and artifacts

Read this when setting up or tuning a CI job for browser tests. Config key names are Playwright's; the idea carries to other runners.

## Settings table

| Setting | Recommended value | Reason |
|---|---|---|
| Workers on a shared CI runner | About half the CPU count (a 4-core runner: 2) | Browsers are CPU and memory hungry; more workers than cores makes tests slow and then flaky from timeouts |
| Workers locally | Runner default | Fast feedback |
| Parallelism unit | One test file per worker by default; fully parallel inside a file only when tests are independent | Independence is what the isolation rules guarantee; do not enable it first and hope |
| Sharding | Split across machines when one runner exceeds 10 minutes (`--shard=i/n`) | Wall time falls close to 1/n; merge the reports afterwards |
| Retries | 1 in CI, 0 locally; never above 2 | Retries report a flake, they do not cure it |
| Trace | Record on the first retry (`on-first-retry`) | Full replay for exactly the tests that flaked, without paying for every run |
| Screenshot | On failure | Cheap, instant evidence |
| Video | Keep on failure only | Large; keep only when a failure needs it |
| Forbid focus markers | `forbidOnly: true` when running in CI | A stray `.only` otherwise makes the build green while running one test |
| Test timeout | Keep the default (about 30 s); expect timeout about 5 s | Raising them globally hides the cause of slowness |
| Browser versions | Pin the browser build with the runner version; cache the download between runs | Silent browser updates are a source of sudden red builds |
| Viewport, locale, timezone | Set explicitly in config | The CI machine's defaults differ from developers' machines |
| Dependencies the app needs | Start them in the job and wait on a health endpoint before the first test | Cold-start timeouts on the first test are the most common false alarm |

## Artifact rules

1. Upload the report, traces, screenshots and videos from a step that runs even when the tests fail (`if: always()` in GitHub Actions, `when: always` in GitLab CI). Artifacts uploaded only on success are useless.
2. Keep artifacts 7 to 14 days; they are large.
3. Name the artifact with the shard index so shards do not overwrite each other.
4. In the failure summary, print the one command that opens the trace locally.
5. Never let tests write secrets into traces: traces capture network calls and page content. Use test accounts and test tokens only, and scrub or avoid logging tokens in requests.

## Reading a trace for a flake

1. Open the failing action; look at the screenshot taken before and after it.
2. Check the action's own log lines: "waiting for element to be visible", "element intercepts pointer events" and "element is not stable" each name a different cause (see the triage table in SKILL.md).
3. Check the network panel for a request that failed or finished after the assertion ran.
4. Check the console panel for application errors thrown just before the failure.
5. Compare with a passing trace of the same test; the first divergence is the lead.

## Quarantine procedure

Quarantine means moving a test out of the blocking run, not deleting it. Record the test name, the owner, the last 50-run failure count and a deadline (14 days is the working default). On the deadline either fix and restore it, or delete it and note which lower-level test now covers the behaviour. A quarantine list that only grows is a finding.

## Sources (read in 2026-11; not re-fetched while writing this file)

- Playwright retries, parallelism and sharding: https://playwright.dev/docs/test-retries , https://playwright.dev/docs/test-parallel , https://playwright.dev/docs/test-sharding
- Playwright trace viewer: https://playwright.dev/docs/trace-viewer
- Playwright CI guidance: https://playwright.dev/docs/ci
