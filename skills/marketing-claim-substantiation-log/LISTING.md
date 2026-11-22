# marketing-claim-substantiation-log

## One line

Turns a marketing blurb into a claim log that marks each number, ranking, testimonial, guarantee and absence-of-risk claim as supported, needs-evidence, or remove or soften.

## What it does

The user supplies the copy and any evidence items they have. Each evidence item must carry a label, a source name and a date. The procedure splits the copy into numbered sentences, pulls out each checkable claim with its verbatim quote, and assigns one of six classes: quantitative, comparative, superlative, testimonial, guarantee, or absence-of-risk. For each claim it states the evidence that class requires, then matches only the pasted evidence to that claim's exact scope. A fixed first-match table decides the status. Claims that cannot be backed receive a rewrite that deletes the unsupported number or ranking, or narrows the wording to a feature the user can confirm. Any rewrite that states a fact not present in the pasted evidence is marked for user confirmation. The output is a claim table, a four-line count summary, a list of rewrites, and a notes section that records refusals and ignored instructions.

## When to use

- Before a landing page, ad set or launch email goes out, when it contains figures such as 3x or 40%.
- When copy says "#1", "best" or "trusted by thousands" and the team needs to see which of those phrases any evidence on hand can back.
- When a refund or money-back promise appears and the author wants it checked against the written terms rather than against memory.

## When not to use

- For a legal opinion, a compliance ruling, or a judgment on whether a claim is permitted in a given country.
- For health, product-safety, investment-return or tax claims. The log marks them but cannot clear them.
- For drafting new copy from scratch. The procedure only audits copy that already exists.

## Requirements

A text-capable agent. No script, no network access, and no files beyond the copy and the user's pasted evidence.

## Example

Excerpt from the smoke run. The input and the full output are in VERIFICATION.md. The evidence items in that run are invented test inputs, not real records.

| id | sentence | quote | class | evidence required | evidence supplied | status | rewrite |
|---|---|---|---|---|---|---|---|
| C1 | S1 | "#1 invoicing app for small teams" | superlative | named ranking or award with issuing body, year and scope | none | remove or soften | Built for small-team invoicing |
| C2 | S2 | "Send invoices 3x faster than spreadsheets" | comparative | head-to-head test naming the comparator, same conditions, date | E1 | needs-evidence | Create invoices with saved templates |
| C4 | S5 | "Every plan comes with a 30-day money-back guarantee" | guarantee | the written terms that state the guarantee and its conditions | E2 | supported | - |

Summary: claims total 5; supported 1; needs-evidence 1; remove or soften 3. The C2 status is needs-evidence because E1 times invoice creation and the copy claims sending.

## Limits

- The class triggers, the 24-month evidence age and the 3,000-word cap are working values chosen for this procedure. They are not industry standards.
- Scope matching depends on the agent reading the claim and the evidence closely. Borderline cases need a human decision.
- The procedure accepts pasted evidence at face value. It cannot tell whether a document is genuine or current beyond the date written on it.
- It is not a legal review and produces no regulatory finding.
- Only one smoke run has been done.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
