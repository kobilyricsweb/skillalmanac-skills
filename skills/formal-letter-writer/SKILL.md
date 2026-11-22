---
name: formal-letter-writer
description: Drafts a formal letter for a complaint, request or notice, using a fixed structure, a three-level tone ladder and only facts the user supplies. Use when the user needs a formal letter about a faulty product, a refund, a billing error or a service failure, or a request to an employer or landlord, or a notice with a deadline, and asks how to write it or wants a draft. Do not use for legal advice, threats of legal action or regulatory reports made on the user's behalf, cover letters, personal or condolence letters, or any letter that needs invented facts.
license: Apache-2.0
compatibility: None beyond a text-capable agent (type B).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Formal letter writer

Drafts one formal letter from intake answers. Run the steps in order. Do not skip the intake: a letter written without a reference number and a stated outcome rarely gets a useful reply.

## Step 1: Choose the letter type

Output: one line `Type: complaint`, `Type: request` or `Type: notice`.

| Type | Use it when | Outcome usually asked for | Starting tone level |
|---|---|---|---|
| Complaint | a product, service or charge did not match what was agreed | repair, replacement, refund, credit, correction | 1 Neutral |
| Request | the user wants a decision, a copy of a record or a confirmation | approval, copy, correction, written confirmation | 1 Neutral |
| Notice | the user must state a change, a breach or a deadline | one specific action by a calendar date | 2 Firm |

If a case fits two rows, use the row that matches the outcome the user named first.

## Step 2: Intake

Ask for every missing field in one single list, not one question at a time. R means required, O means optional.

| Field | Level | Example of a usable answer |
|---|---|---|
| Sender name and postal address | R | Jane Doe, 12 Example Street, Town, Postcode |
| Recipient name, role and address | R | Customer Services, Example Ltd, same format |
| Reference numbers (order, invoice, account, case) | R | Order 48213 |
| Letter date (day month year) | R | 14 March 2026 |
| Key dates (purchase, fault found, each contact) | R | Bought 3 March 2026; fault found 5 March 2026 |
| Facts in date order | R | Blender stopped after two uses |
| Desired outcome | R | Full refund of 89.99 |
| Deadline in days | O | 14 |
| Enclosures | O | Receipt, photo of the fault |
| Earlier letters or replies | O | Email of 12 March 2026, no reply |

Working defaults when O fields are missing: deadline 14 days at Level 1, 10 days at Level 2, 7 days at Level 3.

If an R field is still missing after the single question round, write the letter with a bracketed placeholder such as `[order number]` and list it under Missing items. Do not guess a value.

## Step 3: Build the structure

Assemble the letter in this exact order. The body (purpose to request) must be 120 to 300 words and at most four paragraphs.

1. Sender block: name, address, date written as day month year.
2. Recipient block: name, role, address.
3. Reference line: `Re:` followed by the reference numbers and a subject of eight words or fewer.
4. Salutation: `Dear` plus title and surname. Use `Dear Sir or Madam` only when no name is known.
5. Purpose sentence: first body sentence states what the letter concerns and what is asked.
6. Facts: one fact per sentence, in date order, each sentence containing its date.
7. Request: one sentence stating the desired outcome.
8. Deadline: `Please reply by [calendar date].` Add a next step only if the user authorised it.
9. Enclosures line, if any items were listed.
10. Closing: `Yours faithfully` after `Dear Sir or Madam`, `Yours sincerely` after a named salutation, then the sender's name.

## Step 4: Set the tone level

| Level | Name | Use when | Opening pattern | Deadline (working value) | Next step allowed |
|---|---|---|---|---|---|
| 1 | Neutral | first letter on this matter | `I am writing about [subject].` | 14 days | request the outcome only |
| 2 | Firm | no reply to a letter sent 14 or more days ago | `I wrote on [date] and have had no reply.` | 10 days | the escalation the user named |
| 3 | Final notice | no reply to a Level 2 letter after 10 days | `This is my final request before I [user's step].` | 7 days | one defined step only |

Rules per level:
- Level 1: no adjectives about the recipient, and no words such as unacceptable or shocking. Describe events only.
- Level 2: the reference numbers appear in the first sentence.
- Level 3: no more than two sentences come before the request.

Escalation options are limited to a complaints procedure or regulator the user names. Do not suggest any other step on the user's behalf.

## Step 5: Apply the facts-only rule

Write the fact ledger before the letter. Each fact gets one row: an ID (F1, F2, ...), the fact as it will appear, and the intake field it came from. A sentence in the letter with no ledger row is deleted.

Copy dates, amounts, reference numbers and names exactly as given. Do not round amounts or change their currency. Quote the user's own words only when the user supplied the exact wording.

## Step 6: Run the checks

| Check | Pass condition | Fix if failed |
|---|---|---|
| Purpose | stated within the first two sentences of the body | move it up |
| Dates | every date written as day month year | rewrite the date |
| Money | currency and figure both present | ask, or use a placeholder |
| Deadline | a calendar date, not `soon` or `shortly` | add the day count to the letter date |
| One request | exactly one outcome sentence | cut the extra request |
| Length | body 120 to 300 words | trim or merge paragraphs |
| Placeholders | every bracket appears under Missing items | add it to the list |

## Step 7: Output contract

Reply with exactly these four headings, in this order, and nothing before the first heading.

```
## Letter
(full letter as plain text: no bold, no tables)

## Fact ledger
ID | Fact in letter | Intake field
(one row per fact, F1 onward)

## Missing items
- [placeholder] (one bullet per bracket) or the single word None

## Tone level
Level N: name, deadline D days (working value).
```

## Refuse or stop when

- The user asks for a threat of legal action, a criminal complaint or a regulatory report written in the user's name. Decline that wording, state that a qualified lawyer or the named regulator is the right channel, and offer a Level 1 letter without the threat.
- The dispute involves more than 1,000 in the user's currency (working value) or a statutory right. Draft the Level 1 letter only and state that a professional adviser should review it before it is sent.
- The user asks for facts, dates, amounts or reference numbers to be invented or made stronger than the intake answers.
- The user asks for a letter written as another person without that person's authority.
- The letter targets a named private individual with the aim of shaming, pressuring or exposing them. Stop and explain why.
- The sender, the recipient or the desired outcome is still missing after the single question round. Stop and ask for it.

A refusal is one short paragraph stating the reason, followed by the closest permitted alternative. Do not produce a partial letter that contains the refused content.

## Notes

No scripts and no network access. Licence Apache-2.0, see LICENSE.txt in this folder.
