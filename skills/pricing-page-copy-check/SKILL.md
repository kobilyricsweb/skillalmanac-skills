---
name: pricing-page-copy-check
description: Checks pricing page copy for clarity, hidden costs and unanswered buyer questions by scoring 20 buyer questions as answered, partial or missing and flagging vague terms such as unlimited. Use when a marketer, founder or product owner pastes pricing page text and asks what is unclear, what buyers will ask, or what must be fixed before launch, or when a plan table uses words like fair use or starting at. Do not use for setting or inventing prices, limits or terms, for legal review of contract or refund wording, or for layout and conversion testing of the page design.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B), with no script, no network and no file writes outside the report.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Pricing page copy check

Use this procedure on text the user pastes from a pricing page. Work only from that text. Every finding must cite the pasted copy, and every gap is reported as a gap, never filled with a guessed value.

## Inputs

- Required: the pasted pricing copy, including plan names and at least one price or the words that replace a price (for example "contact sales").
- Optional: the product name, the currency the buyer sees, and the page's call-to-action labels.

## Workflow

1. **Intake.** Confirm that plan names and at least one price-like phrase are present. Output: a one-line statement of plan count and currency, or a stop (see Refuse / stop when).
2. **Plan inventory.** List every plan in order of appearance. For each plan record the price as written, the billing period shown, and the number of feature lines. Output: the Plan inventory table.
3. **Naming and anchor check.** Compare each plan name across the headline, the table, the call-to-action and the footnotes. A name that differs in any place is a naming finding. Apply the anchor rules in the table below. Output: the Anchor and naming findings list.
4. **Scan vague wording.** Search the copy for the trigger phrases in the Vague wording table. Record each occurrence once with its location. Output: the Vague wording table.
5. **Score 20 buyer questions.** Score each question in the Buyer questions list as A, P or M using the scoring rule below. Quote at most 12 words of evidence per row. Output: the Buyer question scorecard table.
6. **Compute the verdict.** Score = (A count x 1 + P count x 0.5) / N x 100, rounded to one decimal place. N is the count of applicable questions: 20 on a tiered page, 7 on a single-price page (see Refuse / stop when). Rows marked "not applicable" are not counted. Apply the verdict thresholds. Output: the Summary block.
7. **Write rewrite suggestions.** For each row scored P or M, write one suggested sentence of 25 words or fewer. Use bracket placeholders such as [PRICE], [LIMIT], [TRIAL_DAYS] and [CANCEL_STEPS] instead of numbers. Output: the Rewrite suggestions table.
8. **List missing inputs.** Collect every placeholder used in step 7 and ask the owner to supply it. Output: the Missing inputs list.

## Buyer questions (scored 20)

Q01 What is included in each plan | Q02 Which features are excluded from each plan | Q03 Usage limits per seat, month or project | Q04 What happens when a limit is reached | Q05 Overage charges and rate | Q06 Billing periods offered | Q07 Price difference between monthly and annual | Q08 Currency shown and whether it includes tax | Q09 Taxes added at checkout | Q10 Free trial length | Q11 Card needed for trial and auto-conversion | Q12 How to cancel | Q13 Refund policy | Q14 What happens to data after cancellation | Q15 Seat rules and minimum seats | Q16 Upgrade and downgrade timing and proration | Q17 Support level per plan | Q18 Contract length or commitment | Q19 Discount eligibility (annual, nonprofit, student) | Q20 Route to a custom quote

## Scoring rule

- **A (answered):** the value is stated for every plan on the page.
- **P (partial):** the topic appears, but for only some plans, or the value carries an undefined word such as unlimited, up to, or as needed.
- **M (missing):** the topic does not appear in the pasted copy.
- **Contact sales plans:** a plan priced only as "contact sales" (or similar) has no stated price, so it does not count as a stated value for Q06, Q07 or Q08. Those rows score P when other plans state the value and M when none does. Q20 scores A only when the copy names how to reach sales in words; a bare label scores P.

## Evidence rule

- Quote the pasted words exactly, with punctuation, and cut the quote at 12 words.
- A value that appears only in a footnote counts as stated, but add "footnote only" to the Gap column.
- A value that appears only in a chat or FAQ link label, without its text, counts as missing.
- Count each question once. Two plans stating the same value still count as one answer per question.
- When two rows conflict (for example two different trial lengths), score the row P and quote both values.

## Verdict thresholds (working values)

| Score | Verdict | Action |
|---|---|---|
| 90.0 to 100.0 | Ready | Wording fixes only |
| 60.0 to 89.9 | Fix before launch | Rewrite every P and M row |
| 0.0 to 59.9 | Hold launch | Copy rewrite and owner input required |

These cut-offs are working values chosen for this check. They are not an industry standard.

## Vague wording

| Trigger phrase | Required condition | Flag when |
|---|---|---|
| unlimited | A stated cap or a stated fair-use rule | Neither is in the copy |
| fair use | A numeric threshold and the action above it | No number follows |
| flexible | The named thing that flexes | Nothing is named |
| starting at | The lowest plan price and what it excludes | Exclusions not stated |
| save up to | The comparison base and the period | Base or period missing |
| as needed | A trigger or a price | Always flag |
| most popular or best | The basis for the claim | No basis given |

## Anchor and naming rules

- A strikethrough price must show its period and its date. Flag it when either is missing.
- Only one plan may carry a recommended badge. Flag a second badge.
- A plan name must match in every location. Flag a mismatch, including a changed capitalization of a product term.
- A comparison of more than 4 plans is a complexity finding. Working value.

## Output contract

Return one Markdown report with these headings in this order:

1. `## Summary`: plan count, currency, score, verdict, and the count of A, P and M rows, and the denominator N.
2. `## Plan inventory`: table with columns Plan | Price as written | Billing period shown | Feature lines.
3. `## Buyer question scorecard`: table with columns ID | Question | Status | Evidence (12 words or fewer, quoted) | Gap.
4. `## Vague wording`: table with columns Phrase | Location | Problem | Required fix.
5. `## Anchor and naming findings`: bullet list, one bullet per finding, or the line "None found".
6. `## Rewrite suggestions`: table with columns ID | Suggested sentence (25 words or fewer, placeholders only).
7. `## Missing inputs`: bullet list of placeholders the owner must fill.

## Refuse / stop when

- The pasted text has no plan name and no price-like phrase: stop and ask for the pricing copy.
- The user asks for a price, limit, discount, trial length, refund window or contract term that is not in the copy: refuse to invent it and use a placeholder.
- The user asks whether a refund, auto-renewal or limit clause is legally enforceable: state that this is not legal advice and recommend review by counsel.
- The user asks how competitors price their plans: refuse to answer from memory; work only from pasted text.
- The page has a single price and no tiers: state "not a tiered page", then score only Q01, Q02, Q06, Q10, Q11, Q12 and Q13, and mark the other rows "not applicable".
