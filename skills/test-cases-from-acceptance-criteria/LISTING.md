# Test cases from acceptance criteria

## One line

Turns a list of acceptance criteria into numbered test cases, a coverage table and an UNTESTABLE list, with every expected result traced to the criterion text.

## What it does

The skill takes the acceptance criteria a team has written for a feature and produces a structured test-case set. It numbers the criteria, classifies each one as testable or untestable, and writes positive, negative and boundary cases from fixed rules. A criterion with a limit such as a count or a duration gets two boundary cases, one at the limit and one just outside it. A criterion with a required field, permission or state the user can violate gets one negative case. A vague criterion such as "user-friendly" or "loads quickly" gets no cases and is listed as untestable with the reason.

Every expected result must be traceable. The Trace column quotes a phrase from the criterion, and a result that the criteria do not state is dropped and recorded as an open question. The output ends with a coverage table that lists each criterion, its case IDs and its coverage status, so a reviewer can see at a glance which criterion has no case. The skill writes text only. It does not write automated test code and it does not give a pass or fail verdict on the software.

## When to use

Use it when a product owner or analyst has pasted acceptance criteria, user stories or a numbered requirements list and asks for test cases, test scenarios or a test plan. It fits a login form, a checkout step, a settings page or any feature whose criteria name observable outcomes and limits.

## When not to use

Do not use it for load or performance test plans, for writing test code, or for criteria that describe internal design rather than observable behavior. It is not a substitute for a tester's judgment about risk, and it cannot tell whether the criteria themselves are correct.

## Requirements

No tools beyond a text-capable agent. The input is the criteria text pasted into the conversation. No files, network access or scripts are needed.

## Example

Input: four acceptance criteria for a login form, as pasted by the requester.

```
1. The Sign in button is enabled only when both the email field and the password field contain text.
2. After five consecutive failed sign-in attempts, the form locks sign-in for 15 minutes.
3. The password field masks typed characters.
4. The login form is user-friendly and loads quickly.
```

Output:

## Summary

- Status: complete
- Feature: Login form
- Criteria total: 4
- Testable: 3
- Untestable: 1
- Test cases: 5
- Open questions: 2

## Criteria

| Criterion ID | Criterion (verbatim) | Status | Reason |
|---|---|---|---|
| AC-01 | The Sign in button is enabled only when both the email field and the password field contain text. | TESTABLE | Observable button state tied to two named fields |
| AC-02 | After five consecutive failed sign-in attempts, the form locks sign-in for 15 minutes. | TESTABLE | Numeric limits: 5 attempts, 15 minutes |
| AC-03 | The password field masks typed characters. | TESTABLE | Observable field state; no violable condition |
| AC-04 | The login form is user-friendly and loads quickly. | UNTESTABLE | Vague terms: user-friendly, quickly |

## Test cases

| Case ID | Criterion ID | Type | Preconditions | Steps | Expected result | Trace (verbatim phrase) |
|---|---|---|---|---|---|---|
| TC-01 | AC-01 | positive | Login form open | 1. Type a valid email address in the email field. 2. Type a password in the password field. | The Sign in button is enabled. | is enabled only when both the email field and the password field contain text |
| TC-02 | AC-01 | negative | Login form open | 1. Type a valid email address in the email field. 2. Leave the password field empty. | The Sign in button is disabled. | enabled only when both the email field and the password field contain text |
| TC-03 | AC-02 | boundary | Account exists; no failed attempts yet | 1. Enter the account email and a wrong password, then select Sign in. 2. Repeat step 1 until there are 5 failed attempts. | The form locks sign-in after the fifth consecutive failed attempt. | After five consecutive failed sign-in attempts, the form locks sign-in |
| TC-04 | AC-02 | boundary | Account exists; no failed attempts yet | 1. Enter the account email and a wrong password, then select Sign in. 2. Repeat step 1 until there are 4 failed attempts. | The form does not lock sign-in after the fourth consecutive failed attempt. | After five consecutive failed sign-in attempts |
| TC-05 | AC-03 | positive | Login form open | 1. Type abc123 in the password field. | The typed characters in the password field are masked. | The password field masks typed characters. |

## Coverage

| Criterion ID | Case IDs | Positive | Negative | Boundary | Coverage |
|---|---|---|---|---|---|
| AC-01 | TC-01, TC-02 | 1 | 1 | 0 | COVERED |
| AC-02 | TC-03, TC-04 | 0 | 0 | 2 | COVERED |
| AC-03 | TC-05 | 1 | n/a | 0 | COVERED |
| AC-04 | none | 0 | 0 | 0 | UNTESTABLE |

## UNTESTABLE criteria

- AC-04: "user-friendly" and "quickly" have no pass or fail threshold, so no case can be written.

## Open questions

1. AC-02: The criterion does not state when the 15-minute lock ends, or whether the lock applies per account or per browser. No expected result is written for either point.
2. AC-02: The criterion does not state whether a successful sign-in resets the count of consecutive failed attempts.

## Limits

The skill works only on the text it is given. It does not check the criteria against the product, against a design file or against a bug history, so an expected result is only as correct as the criterion it quotes. It does not verify that a criterion is complete, consistent or achievable. It cannot judge whether a boundary value is the right one for the business, and it does not weigh risk or priority between cases. Its count and threshold values (4 cases per criterion, 2 to 5 steps per case) are working values chosen by the author, not a published standard. It does not check whether a case is executable in a given environment, and it does not test for accessibility, security or visual layout beyond what a criterion states.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
