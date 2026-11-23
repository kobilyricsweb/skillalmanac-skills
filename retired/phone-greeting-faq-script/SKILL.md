---
name: phone-greeting-faq-script
description: Writes a phone greeting, a routing menu of up to four options, an after-hours message, eight FAQ answers and three escalation rules for a small business receptionist, using only facts the owner supplies. Use when a business answers calls inconsistently, sets up a phone menu or automated receptionist, or needs front-desk staff to give the same answers. Any fact the owner did not supply is marked TO-CONFIRM, never guessed. Do not use for medical or dental triage, billing disputes, insurance or legal answers, or prices the owner has not supplied.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Phone greeting, menu and FAQ script

This skill turns the facts a small business owner gives into a call script for a receptionist or phone menu. It writes no facts of its own. Shipped file: [LICENSE.txt](LICENSE.txt).

## Required intake facts

Five facts are required. If any one is missing, stop (see the stop rule in step 1).

1. Business name (3 words or fewer).
2. Weekday hours: each open day with open and close times, and each closed day.
3. Street address, as the caller should hear it.
4. After-hours handling: what callers should do and when staff returns calls.
5. Two to four call reasons, in menu order, each with the desk that handles it.

Optional facts: insurance plans accepted, fees, cancellation terms, new-patient policy, parking, and an on-call number for emergencies. A missing optional fact becomes TO-CONFIRM in the FAQ or escalation table. Never guess it.

## Workflow

1. Check intake. Count the call reasons. Two to four: continue. Zero or one: stop. Five or more: stop and ask which four to keep. A business name of more than three words: stop and ask for a shorter name. Output at this step: the go-ahead, or the stop output.
2. Write the greeting from this fixed template and nothing else: `Thank you for calling <business name>, how can I help?` Output: one line. Word count must be 11 or fewer.
3. Build the routing menu. Make one row per call reason, in the order the owner gave. Option wording is 6 words or fewer (working value). Each row routes to the desk the owner named; if the owner named no desk for a reason, the Routes to cell is exactly `TO-CONFIRM: <desk>`. Output: a table with 2 to 4 rows.
4. Write the after-hours message from this template: `Thank you for calling <business name>. We are closed now. Hours: <open days and times>. Please leave your name, callback number, and reason for calling. <after-hours handling in one sentence>.` Output: one paragraph of 50 words or fewer (working value). List only open days in the hours line.
5. Write the FAQ. Use exactly these eight questions, in this order: (1) What are your hours? (2) Where are you located? (3) Are you accepting new patients? (4) Do you accept my insurance? (5) How much does a visit cost? (6) How do I cancel or reschedule? (7) Do you handle emergencies? (8) Where can I park? You may adjust a question's noun to fit the business type, but keep its meaning. Each answer uses only supplied facts and is 30 words or fewer. If the fact is missing, the answer is exactly `TO-CONFIRM: <what the owner must supply>`. Never answer yes or no to a question whose fact is missing.
6. Write the escalation rules. Use exactly three rows in this order: Emergency, Complaint, Billing. Use the trigger words in the table below and the fixed action wording in the Escalation actions table. The skill decides only from those words and never judges medical severity. The Route comes only from the owner's facts; if the owner did not supply it, the Route cell is exactly `TO-CONFIRM: <route>`.
7. Count words. Count whitespace-separated tokens, so `8:00` and `AM,` each count as one. Shorten any line over its limit before output. Copy the counts into the Words column; do not estimate them.
8. Set the status and collect TO-CONFIRM. Status is `complete` if no TO-CONFIRM appears anywhere, `partial` if one or more does. Write one TO-CONFIRM list item per distinct missing fact, even if the fact appears in two places.
9. Write the output in the contract below.

## Decision and threshold table

| Item | Rule | Value |
|---|---|---|
| Required intake facts | Missing any one | Status `stopped` |
| Call reasons | Count | 2 to 4 (0 or 1 stops; 5 or more stops) |
| Business name | Words | 3 or fewer |
| Greeting | Words, whole line | 11 or fewer |
| Option wording | Words per row | 6 or fewer (working value) |
| After-hours message | Words | 50 or fewer (working value) |
| FAQ entries | Count | Exactly 8 |
| FAQ answer | Words | 30 or fewer |
| Escalation rows | Count | Exactly 3 |
| Emergency trigger (working values; owner confirms) | Caller words | `emergency`, `severe pain`, `swelling`, `bleeding` |
| Complaint trigger (working values; owner confirms) | Caller words | `complaint`, `unhappy`, `upset` |
| Billing trigger (working values; owner confirms) | Caller words | `balance`, `invoice`, `payment` |
| Status `complete` | TO-CONFIRM count | 0 |
| Status `partial` | TO-CONFIRM count | 1 or more |

## Output contract

For status `complete` or `partial`, write these headings in this order and nothing else:

- `## Status`: one word, `complete` or `partial`.
- `## Greeting`: one line.
- `## Routing menu`: table with columns `Key | Option wording | Routes to`, keys 1 to N, N from 2 to 4.
- `## After-hours message`: one paragraph.
- `## FAQ`: table with columns `# | Question | Answer | Words`, rows 1 to 8.
- `## Escalation rules`: table with columns `Trigger | Action | Route`, rows Emergency, Complaint, Billing.
- `## TO-CONFIRM`: numbered list, or the word `None` when status is `complete`.

For status `stopped`, write only `## Status` with the word `stopped`, then `## Questions for the owner` with a numbered list of one question per missing fact or failed check. Do not write a partial script.

## Status values

- `complete`: all five required intake facts supplied and zero TO-CONFIRM in the output.
- `partial`: all five required intake facts supplied and one or more TO-CONFIRM in the output.
- `stopped`: any stop condition from step 1 or the stop list below. Write no script.

## Escalation actions

Use this fixed action wording for each escalation row. Do not reword it.

| Row | Action wording | Route |
|---|---|---|
| Emergency | Transfer the call to the on-call line now. Do not book an appointment. | Owner's on-call number, else `TO-CONFIRM: on-call number` |
| Complaint | Take name, callback number, and a one-line summary. Do not argue, promise refunds, or resolve the issue. | Owner's complaint desk, else `TO-CONFIRM: complaint desk` |
| Billing | Take name and callback number. Do not quote balances. | Owner's billing desk, else `TO-CONFIRM: billing desk` |

## Trigger matching

- Match trigger words case-insensitively, as whole words. `emergency` matches `Emergency` and `an emergency`, but not `emergencies`.
- If a caller uses a trigger word in any position, the row fires. If two rows fire, route to Emergency first, then Complaint, then Billing.
- Trigger words are the only basis for an escalation. Do not add triggers beyond this list.

## Final check before output

Run these checks in order and fix the first failure before you write anything:

1. Greeting is 11 words or fewer and uses the template in step 2 exactly.
2. Routing menu has 2 to 4 rows, keys 1 to N in order, and every Routes to cell names a desk the owner supplied or is exactly `TO-CONFIRM: <desk>`.
3. After-hours message is 50 words or fewer and includes the sentence about leaving a name, callback number, and reason.
4. FAQ has exactly 8 rows, in the order listed in step 5, and every Words value equals the count of whitespace-separated tokens in the Answer cell.
5. No FAQ answer is over 30 words.
6. Escalation table has exactly 3 rows: Emergency, Complaint, Billing.
7. Every TO-CONFIRM in the body has one matching item in the TO-CONFIRM list.
8. Status matches the TO-CONFIRM count rule in the status values.
9. No hour, price, fee, insurance plan, policy, or callback time appears that the owner did not supply.

## Refuse or stop when

- A required intake fact is missing, a call-reason count is outside 2 to 4, or the business name exceeds 3 words. Stop and return the numbered questions.
- The owner asks for an hour, price, fee, insurance plan, policy, refund, callback time, or same-day visit that was not supplied. Refuse to invent it and mark it TO-CONFIRM.
- The caller script would need medical or dental triage, a diagnosis, or a judgment that a symptom is an emergency. Use only the trigger words in step 6.
- The script would ask callers for a Social Security number, card number, bank number, or password.
- A promise of outcome would be written, such as "we will fix it" or "you will get a refund." Replace it with the supplied action or TO-CONFIRM.
