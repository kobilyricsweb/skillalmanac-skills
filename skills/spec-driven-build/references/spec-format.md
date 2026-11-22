## Contents

1. The four tests for a buildable requirement
2. Rewrites: vague to testable
3. Splitting a requirement
4. Acceptance shapes that work
5. Naming tests per language
6. Spec change after the build starts

## 1. The four tests for a buildable requirement

1. One observable behaviour. If the sentence has "and" joining two outcomes, split it.
2. A comparable value: a number with its unit, an exact message, a status code, a stored state.
3. A named trigger or precondition: who or what starts it, in which state.
4. An acceptance check a stranger could run and judge pass or fail without asking you.

## 2. Rewrites: vague to testable

| Vague | Testable |
|---|---|
| The page should load quickly | The product list page shall return its first byte within 800 ms at the 95th percentile with 50 concurrent users on the staging data set |
| Users can easily reset their password | A user who submits a registered email shall receive one reset email within 60 seconds |
| Handle errors appropriately | When the payment provider returns 5xx the checkout shall show "Payment failed, you were not charged" and create no order |
| Support large files | Uploads up to 25 MB shall succeed; a 25 MB + 1 byte upload shall be rejected with HTTP 413 |
| Secure the endpoint | Requests without a valid bearer token shall receive 401 and no body data |
| Show recent items | The sidebar shall list the 5 most recently opened items, newest first |

When the number is not known, do not invent it as fact: propose it to the user marked as a proposal and wait for a yes.

## 3. Splitting a requirement

Signs a requirement is two: "and" between outcomes; an acceptance check with two thens that could fail independently; a title you cannot say in four words. Split into REQ-nnn pairs with new ids at the end of the list. Never renumber the old ones, because tests and commits already cite them.

## 4. Acceptance shapes that work

- Given/when/then with exact values: `Given a link issued 31 minutes ago, when it is used, then the response is 410.`
- Table of input to output for pure functions: three rows minimum including one boundary.
- Negative case written as its own requirement or its own acceptance line: what must NOT happen (no email sent, no row created).
- Boundary pair: the last accepted value and the first rejected value (100 passes, 101 gets 429).

Shapes that do not work: "works as expected", "is user friendly", "passes review", "done when the PM is happy".

## 5. Naming tests per language

The script matches the text `REQ-` followed by digits, anywhere in a file of a scanned type.

- Python: `def test_req_004_link_single_use():` plus a comment or docstring containing `REQ-004`.
- JavaScript/TypeScript: `it("returns 410 on second use [REQ-004]", ...)`.
- Go: a `// REQ-004` comment above `func TestResetLinkSingleUse`.
- Java/Kotlin: a `@DisplayName("REQ-004 single use")` or a comment.
- Gherkin: a tag line `@REQ-004` above the scenario.

## 6. Spec change after the build starts

A requirement that has code and tests behind it is changed by adding a new id that supersedes it and marking the old one `[dropped]` in the heading, so history stays readable and the script stops demanding tests for it. Tell the user which tests to delete; do not delete them without agreement.
