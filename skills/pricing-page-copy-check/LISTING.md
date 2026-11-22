# pricing-page-copy-check

## One line

Scores a pasted pricing page against 20 buyer questions and flags words like "unlimited" that leave a buyer guessing.

## What it does

The skill takes pricing page text that the user pastes and produces one report. It lists each plan with its price as written, its billing period and its feature count. It then scores 20 fixed buyer questions as answered, partial or missing. The questions cover included features, usage limits, overage, billing periods, monthly versus annual differences, currency and tax, trial length, card requirements, cancellation, refunds, data retention after cancellation, seat rules, proration, support levels, contract length, discount eligibility and the route to a custom quote. Each score comes with a short quote from the pasted text, so the owner can check the evidence.

The skill also scans for vague wording. Trigger phrases such as "unlimited", "fair use", "save up to" and "as needed" each get a required condition. A phrase that misses its condition is flagged with the fix it needs. The report ends with rewrite suggestions that use bracket placeholders such as [PRICE_LIMIT] in place of numbers, plus a list of the inputs the owner must supply. The skill never fills a placeholder with a guessed value.

## When to use

Use it before a pricing page goes live, after a plan change, or when a page gets questions from buyers that the copy should have answered. It fits a marketer or product owner who has the page text in hand and wants a list of gaps rather than a rewrite.

## When not to use

Do not use it to set prices, choose limits or write contract terms. It does not review refund or renewal clauses for legal force. It does not test layout or conversion, and it does not compare competitor pricing from memory.

## Requirements

A text-capable agent. No script, no network access and no files beyond the report. The pasted copy must include plan names and at least one price or a substitute such as "contact sales".

## Example

Excerpt from the smoke run, where the input was three plans with three undefined uses of "unlimited" (fixtures/smoke_input.txt):

```
## Summary

- Plan count: 3 (Starter, Pro, Team)
- Currency: $ shown, currency code not stated
- Score: 25.0 (A 0, P 10, M 10)
- Verdict: Hold launch. Copy rewrite and owner input required.
```

```
| Q03 | Usage limits | P | "Unlimited projects" (Pro) | Only Starter has numeric limits |
| Q09 | Taxes added at checkout | M | none | Not stated |
```

## Limits

- The 20 questions are a fixed list. A page that needs a different question set must be checked by hand.
- The verdict cut-offs (90, 60) are working values. They are not an industry standard.
- Scores depend on the pasted text only. A value stated on a linked page is not seen and scores as missing.
- The skill cannot tell whether a stated value is correct, current or legally sufficient.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
