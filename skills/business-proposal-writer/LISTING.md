# business-proposal-writer

## One line

Drafts a client proposal from a brief, a scope and a price, with every missing input marked TO-CONFIRM.

## What it does

The skill takes a short intake: the client's problem in their own words, the outcome, the scope in and out, the timeline, the price and any proof the user owns. It checks that intake first. It then drafts eight sections in a fixed order: summary, problem, approach, deliverables table, timeline table, price and terms table, scope boundaries and next step. Each section has a word limit or table shape, so the proposal does not drift into long background text before the client's problem is stated.

Win themes are limited to two or three, and each one must cite a sentence from the brief. Factual claims must trace to the brief, and superlatives are removed. Any figure, name, credential or price the user did not supply is written as TO-CONFIRM and collected in a closing Open items table, so the user can see exactly what remains open before sending.

## When to use

Use it when you have a clear client problem and a defined piece of work, such as a website audit, a process review or a six-week diagnostic, and need a first draft of the proposal in a consistent layout. It suits freelancers and small agencies that write one proposal at a time and want the price and scope boundaries stated in plain table form.

## When not to use

Do not use it for legal contracts, indemnities, liability terms or warranties; the skill refuses those lines and points to counsel. It does not write invoices, grant applications, cold sales emails or any advice on money or investments. It does not invent case studies, references or team credentials.

## Requirements

A text-capable agent. No scripts, no network access and no extra tools are needed. The package has four files: SKILL.md, LICENSE.txt, LISTING.md and VERIFICATION.md.

## Example

Excerpt from the smoke run on a six-week website audit brief for a regional clinic group, where the price was not supplied. Section 6 and the Open items table, verbatim:

```
## 6. Price and terms

| Item | Value |
|---|---|
| Fee | TO-CONFIRM |
| Currency | TO-CONFIRM |
| Payment schedule | TO-CONFIRM: payment schedule |
| Validity | 30 days (default, TO-CONFIRM) |
| Expenses | TO-CONFIRM |

## Open items

| Marker | Section | Why it is needed | Owner |
|---|---|---|---|
| Fee | 6 Price and terms | Price not in brief | user |
| Payment schedule | 6 Price and terms | No schedule given | user |
```

## Limits

The word limits and the clause table are working values chosen for this skill, not published industry standards. The skill cannot check whether a client problem is accurate; it only checks that the claims in the draft trace back to the brief. Tone is plain and direct by design, which may read as too terse for some sales audiences. The output is a draft that a human must review before sending.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
