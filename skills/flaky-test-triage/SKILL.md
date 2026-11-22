---
name: flaky-test-triage
description: Classifies a failing automated test as flaky or genuinely broken from five or more run results, names the cause class from observable evidence, and prescribes one isolation experiment with quarantine rules. Use when a test passes on some reruns and fails on others, a team is retrying a job until it goes green, a timeout appears at the same step across runs, or a proposal raises a timeout or retry count. Do not use for writing new tests, choosing a test framework, load testing, or diagnosing a production incident.
license: Apache-2.0
compatibility: Needs none beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Flaky test triage

This skill decides whether one failing test is flaky or broken, names the cause class from evidence, and picks one isolation experiment. Every threshold below is a working value chosen for this procedure. None is an industry standard. Change a value only by writing the change and its reason into the quarantine record or triage note.

## Inputs

Required fields for each run, one row per run: run_id, commit, result (pass or fail), failing step name, first line of the error, elapsed milliseconds of the failing step, configured timeout in milliseconds, last URL or resource seen, runner host, random seed or test order, start time in UTC.

Minimum: 5 runs of the same test on the same commit. Runs from another commit are listed as excluded and are not counted.

## Workflow

1. Normalise the runs.
   Output: the run table (see Output contract). Exclude a run that lacks a required field and list each excluded run_id with the missing field name.
2. Compute the pass rate.
   Output: pass_rate as passes/N, for example 3/5.
3. Pick the verdict row from the table below.
   Output: verdict and next step.

Verdict table

| Observed pattern | Verdict | Next step |
|---|---|---|
| N of N fail, same step, same error text | deterministic | stop triage, hand to fix |
| N of N pass | stable-pass | no triage |
| mixed, pass_rate below 0.5 | leans-broken | run experiment A first |
| mixed, pass_rate 0.5 or above, at least 2 fail | flaky | go to step 4 |
| exactly 1 fail, N of 10 or more | suspected-flake | run experiment A, then go to step 4 |
| exactly 1 fail, N of 5 to 9 | insufficient | add runs until N is 10 |

4. Classify the cause.
   Count the failing runs that show each class's evidence. Record every class with at least 2 matching failing runs, ranked by count. If a class ties, list all tied classes. If no class reaches 2, the class is unknown.

Cause table

| Class | Evidence in the failing runs |
|---|---|
| timing | failing elapsed equals the timeout AND the largest passing elapsed on that step is 70 percent of the timeout or more |
| hang | failing elapsed equals the timeout AND the largest passing elapsed on that step is below 30 percent of the timeout |
| shared-state | error or last URL names a leftover session, cookie, lock, port in use, duplicate key, or existing file |
| order-dependent | failures occur only with seeds where a named other test ran before the target |
| network | error is connection reset, DNS failure, TLS failure, or HTTP 502, 503 or 504 from a host outside the test fixtures |
| clock-timezone | error names a date, expiry or UTC offset, or the failure count changes when the timezone changes |
| resource | failures cluster on one runner host, or an out-of-memory or CPU throttle line appears in the log |
| deterministic | the same error in every failing run, and the test fails when run alone (experiment A) |

Failing elapsed equals the timeout but the largest passing elapsed is between 30 and 70 percent of the timeout: record the class as unknown and add elapsed logging to the step.

A hang means the page or service never reached the expected state. Slow code does not produce fast passes followed by a timeout, so a hang is not fixed by a longer timeout.

5. Run the fixed rerun protocol.
   Run A first on every flaky verdict. Then run the experiment that separates any tied classes: B for shared-state against order-dependent, D for resource against the others. Stop at the first experiment that gives a result.

| Experiment | Procedure | Result rule |
|---|---|---|
| A isolate | run only this test 20 times, sequentially, retries 0, on the host that held the failures when the run table shows one | 1 or more fails: cause is in the test body or its fixture, use the step 4 classes. 0 of 20 fail: go to B. 20 of 20 fail: deterministic |
| B order | run the full suite 4 times with the seeds of the failing runs first, then 2 new seeds | failures appear only with one seed: record the test that ran before the target |
| C clock | 10 runs with the clock frozen to 2026-03-01T00:00:00Z in UTC, 10 runs with the same frozen clock and TZ set to Asia/Kolkata | the failure counts of the two arms differ by 4 or more |
| D resource | 10 runs with one worker, 10 runs with default workers | the failure counts of the two arms differ by 4 or more |

6. Choose the action.

| Result | Action |
|---|---|
| deterministic | fix the test or the product, no quarantine, no retries |
| class known, fix available | fix the cause |
| class known, fix not ready | quarantine (step 7) |
| class tied or unknown before experiments A to D are done | action more-runs, run the next experiment |
| class unknown after experiments A to D | quarantine (step 7) and add logging for the missing field |

7. Set quarantine rules.
   Required fields: owner (one named person), tracker ID, cause class, date opened, expiry date. Expiry is 14 days after the date opened. One extension is allowed and needs new evidence in the record. A quarantined test runs in a non-blocking job and is reported as skipped with its reason. It is never deleted. If quarantined tests exceed 5 percent of the suite, stop adding records and escalate.

Retries: triage runs use retries 0. A retry count of 1 is allowed only inside an open quarantine record and must be listed there.

Timeouts: change a timeout only for the timing class. New value = largest passing elapsed x 2, rounded up to the next 5000 ms (working value). For every other class the timeout stays as it is.

## Output contract

Use these headings in this order. Keys are exact. Do not add other keys.

## Verdict
pass_rate: 3/5
verdict: deterministic | flaky | leans-broken | stable-pass | suspected-flake | insufficient
class: one class name, or unknown with tied names in parentheses
confidence: high when one class has 4 or more failing runs, medium for 2 or 3, low for unknown or tied

## Run table
| run | result | failing step | elapsed ms | timeout ms | last URL or error | host | seed |
|---|---|---|---|---|---|---|---|

## Next experiment
experiment: A | B | C | D
run count and variable: copied from step 5
stop when: copied from the result rule in step 5

## Action
action: fix | quarantine | more-runs
retries: 0 (1 only inside an open quarantine record)
quarantine: owner, tracker ID, opened, expires, or none
timeout change: none, or the new value in ms with the rule used

## Refuse / stop when
- Fewer than 5 runs, or the runs cannot be tied to one commit.
- A failing run has no failing step name or no error text.
- The request asks for blanket retries, a longer timeout without timing-class evidence, or removing the test to get green.
- The verdict is deterministic: stop triage and say so.
- The request is about writing new tests, choosing a framework, load testing, or a production incident.
