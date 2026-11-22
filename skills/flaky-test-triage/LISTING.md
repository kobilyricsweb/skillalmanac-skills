# flaky-test-triage

## One line

Sorts a failing automated test into flaky or broken from five or more reruns, names the likely cause from the logs, and picks the single next experiment to run.

## What it does

The skill takes the result of at least five runs of one test on one commit. Each run is reduced to a short row: pass or fail, the failing step, the elapsed time of that step against the configured timeout, the last page or resource seen, the runner host, and the random seed. From those rows it computes a pass rate and applies a fixed verdict table. A mixed record is then checked against a cause table with eight classes, including timing, hang, shared state, order dependence, network, clock and timezone, and resource pressure. Each class needs visible evidence in at least two failing runs before it is recorded.

When the cause is still unclear, the skill prescribes a fixed rerun protocol with four experiments, in a set order, each with a stop rule. It also sets quarantine rules: a named owner, a tracker ID, and a 14-day expiry. It refuses blanket retries and timeout increases that the evidence does not justify.

## When to use

Use it when a test passes on some reruns and fails on others, when a CI job is being rerun until it turns green, or when the same step times out across several runs. It also fits a review of a proposal to raise a timeout or add a retry, because the skill states the exact conditions under which a timeout may change.

## When not to use

Do not use it to write new tests, to choose a test framework, to plan load tests, or to investigate a production incident. A test that fails the same way on every run is reported as deterministic and handed to a fix; the skill does not try to make it pass.

## Requirements

Any text-capable agent. No scripts, no network access, and no test runner needs to be installed. The agent needs the run logs pasted into the conversation with the fields listed in the Inputs section of the skill.

## Example

Five runs of a login test, three passing and two timing out at the dashboard wait, were pasted into the conversation. The output below was produced by following the skill's output contract for that input.

```
## Verdict
pass_rate: 3/5
verdict: flaky
class: unknown (tied: hang, shared-state, resource)
confidence: low

## Run table
| run | result | failing step | elapsed ms | timeout ms | last URL or error | host | seed |
|---|---|---|---|---|---|---|---|
| 1 | pass | wait_dashboard | 2400 | 30000 | /dashboard | runner-a | 1041 |
| 2 | fail | wait_dashboard | 30000 | 30000 | /login?error=session_exists | runner-b | 1042 |
| 3 | pass | wait_dashboard | 2900 | 30000 | /dashboard | runner-a | 1043 |
| 4 | fail | wait_dashboard | 30000 | 30000 | /login?error=session_exists | runner-b | 1044 |
| 5 | pass | wait_dashboard | 3100 | 30000 | /dashboard | runner-a | 1045 |

## Next experiment
experiment: A
run count and variable: 20 sequential runs of login_valid_user, retries 0, on runner-b (the host that held both failures)
stop when: 0 of 20 fail: go to B. 1 or more fail: cause is in the test body or fixture, use the step 4 classes. 20 of 20 fail: deterministic

## Action
action: more-runs
retries: 0 (1 only inside an open quarantine record)
quarantine: none
timeout change: none (the timing class is not recorded, so the timeout stays at 30000 ms)
```

The two failures ran on one host and stopped on a leftover session page, while the passing runs finished in about three seconds against a 30-second timeout. That pattern points at a hang with a session carried over from another test, not at slowness, so the skill does not recommend a longer timeout.

## Limits

The verdict table and the cause table use working values, not published standards, so a team may need to adjust the thresholds. The skill only reads the evidence it is given. Without elapsed times, host names or last-URL fields, most classes cannot be recorded and the output falls back to unknown. The skill does not inspect source code, so it cannot confirm which test wrote the leftover session.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
