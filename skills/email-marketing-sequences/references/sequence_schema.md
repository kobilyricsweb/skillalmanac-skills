## Contents

- Field rules
- Check table (every code the script can emit)
- Reading the timeline

## Field rules

Sequence object:

| Field | Rule |
|---|---|
| `name` | non-empty string |
| `type` | `onboarding`, `nurture`, `winback` or `other`; selects the minimum gap (1, 2, 3, 2 days) |
| `trigger` | one detectable event, e.g. `account_created`; not "when the customer seems ready" |
| `goal` | one event with a window, e.g. "first order within 14 days" |
| `consent_basis` | `express_consent`, `double_opt_in`, `existing_customer`, `legitimate_interest`, `other`. `purchased_list`, `rented_list`, `scraped`, `unknown` are rejected |
| `consent_evidence` | where, when and how consent is stored (field, timestamp, source form). Expected for the two consent bases |
| `regions` | optional list such as `["US","UK","EU","CA"]` |
| `sender` | `from_name`, `from_email` (monitored mailbox), `postal_address` (physical address for the footer) |
| `exit_conditions` | list of strings; at least one should mention the goal being reached |
| `min_gap_days` | optional number; lowers or raises the type default; a value below the default raises a warning |

Email object: `id` (unique), `day` (number, days after trigger, non-decreasing down the list), `job`, `subject`, `preheader`, `cta` (`label`, `url`), `unsubscribe` (must be `true` unless `transactional` is `true`), `list_unsubscribe_header` (`true` when the one-click header is set in the sending tool), optional `exit_conditions` (overrides the sequence list for this email), optional `sender` (overrides the sequence sender, must then be complete), optional `transactional` (receipts and security notices only; promotional content in a transactional email defeats the exemption, so do not use it for sequence emails).

## Check table

| Code | Level | Meaning and fix |
|---|---|---|
| `schema-sequence`, `schema-emails`, `schema-email` | FAIL | a required object or list is missing; add it |
| `sequence-type` | FAIL | type not in the list |
| `sequence-name-missing`, `sequence-trigger-missing`, `sequence-goal-missing` | FAIL | fill the field |
| `consent-basis-missing` | FAIL | choose a listed basis |
| `consent-basis-unacceptable` | FAIL | list was bought, rented, scraped or unknown; do not send; see compliance reference |
| `consent-evidence-missing` | WARN | record where consent is stored |
| `legitimate-interest-eu-uk` | WARN | needs a documented balancing test; verify with counsel |
| `sender-missing` | FAIL | no sender on the sequence or email |
| `sender-field-missing` | FAIL | from_name, from_email or postal_address empty |
| `sender-email-invalid` | FAIL | not an address |
| `sender-noreply` | WARN | no-reply address; use a real mailbox |
| `min-gap-invalid` | FAIL | not a number of days |
| `min-gap-lowered` | WARN | override below the type default |
| `sequence-long` | WARN | more than 10 emails |
| `exit-no-goal` | WARN | no exit mentions the goal |
| `exit-missing` | FAIL | an email has no exit list of its own and the sequence has none |
| `exit-invalid` | FAIL | exit_conditions is not a list |
| `email-id-missing`, `email-id-duplicate` | FAIL | ids must be unique |
| `day-invalid` | FAIL | day not a number of 0 or more |
| `order-wrong` | FAIL | emails not in day order |
| `gap-too-short` | FAIL | gap below the minimum for the type |
| `gap-too-long` | WARN | gap over 30 days; add a context line or a reminder email |
| `burst` | WARN | more than 4 emails in the first 7 days |
| `job-missing` | FAIL | no one-sentence job |
| `job-multiple` | WARN | job reads like several jobs |
| `subject-missing` | FAIL | empty subject |
| `subject-too-long` | FAIL | over 78 characters |
| `subject-long` | WARN | over 60 characters |
| `subject-whitespace` | WARN | leading or trailing spaces |
| `subject-fake-reply` | FAIL | starts with Re: or Fwd: |
| `subject-money-symbols`, `subject-urgency`, `subject-free-claims`, `subject-prize`, `subject-click-here`, `subject-guarantee` | WARN | phrase families common in spam filters; rewrite plainly unless the claim is true and necessary |
| `subject-all-caps` | WARN | a word of 4 or more letters in capitals |
| `subject-exclamations` | WARN | more than one `!` |
| `subject-duplicate` | WARN | same subject as an earlier email |
| `preheader-missing`, `preheader-long`, `preheader-repeats-subject` | WARN | write one, under 130 characters, not the subject |
| `cta-missing` | FAIL | label and url both required |
| `cta-multiple` | WARN | `ctas` list present; one primary action |
| `cta-not-https` | WARN | use HTTPS |
| `cta-label-vague` | WARN | "Click here", "Read more" and similar |
| `cta-duplicate-url`, `cta-duplicate-label` | WARN | the same destination or label in two emails; each email earns a different step |
| `unsubscribe-missing` | FAIL | marketing email without `unsubscribe: true` |
| `list-unsubscribe-header` | WARN | one-click header not declared |

## Reading the timeline

`timeline` has one object per email: `day`, `gap_days` (null for the first), `id`, `subject`, `cta` (label), `job` and `exits` (`own`, `sequence` or `none`). Copy it into the plan note as it is; do not retype it. A strictly increasing day column with gaps of at least the minimum and no `none` in `exits` is the shape of a finished sequence.
