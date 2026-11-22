---
name: review-reply-writer
description: Writes one calm public reply to a customer review for a business owner, after classifying the review and checking every fact the reply will state. Use when a 1 to 5 star review needs a reply that thanks the reviewer, restates one specific detail, owns what the business controls, and offers one off-platform next step. Covers praise, mixed, factual error, complaint, and abusive reviews. Do not use for private support messages, legal or press responses, posting or deleting reviews, or replies for a different business.
license: Apache-2.0
compatibility: None beyond a text-capable agent; the procedure needs no network access and no scripts.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Review Reply Writer

This skill drafts one public reply to one customer review. It never posts anything. The owner reads the output, clears any blocking items, and posts the reply.

Shipped files: [LICENSE.txt](LICENSE.txt).

## Workflow

1. **Intake.** Collect four facts: (a) the review text exactly as posted, (b) the star rating as an integer from 1 to 5, (c) the business name as the owner wants it written, (d) the owner's statement of what the business controls and what it will do about it. Facts a to c are required. Fact d is optional; without it, the owned sentence is dropped. Output: the four facts, each marked present or missing. Never invent a missing fact.

2. **Classify.** Apply the rules below from top to bottom. The first row that matches decides the class. Output: one class label.

| Order | Class | Match rule (working value) |
|---|---|---|
| 1 | abusive | Main content is an insult, slur, or personal attack with no readable service complaint |
| 2 | factual_error | The review states a checkable fact (date, charge, item, staff action) and the owner confirms the business record shows otherwise |
| 3 | complaint | Rating 1 or 2, or names a failure the business controls |
| 4 | mixed | Rating 3, or rating 4 or 5 that also names a complaint |
| 5 | praise | Rating 4 or 5 with no named complaint |

A factual claim the owner has not checked does not qualify for factual_error. Classify such a review by rating.

3. **Verify.** Mark each item confirmed, not confirmed, or not applicable. The reply may state only confirmed facts.

| Code | Item | Pass rule |
|---|---|---|
| V1 | Restated detail matches the owner's record | The date, item, or service named in the reply appears in the owner's record |
| V2 | Business controls the issue | The owner confirms the failure was the business's own step, or confirms the business will follow up. Never name a carrier, supplier, or other party |
| V3 | Remedy is authorized | Any refund, credit, or replacement in the reply is one the owner named. Default: no remedy, so V3 is not applicable |
| V4 | Contact channel exists | The owner named the phone line, email address, or form that the next step points to |
| V5 | No customer identifier | The reply contains no reviewer name, order number, address, or account ID, and no phone number or email address except the one the owner named as `{channel}` |

4. **Draft.** Fill the template for the class. Keep the template sentences in order and fill only the braces.

| Class | Template |
|---|---|
| praise | Thank you for taking the time to write this review. We are glad {praised_detail}. If you need anything on your next visit, please contact {channel}. |
| mixed | Thank you for the feedback, and we are glad {praised_detail}. We are sorry {complaint_detail}. {owned_sentence} Please contact {channel} so we can {next_action}. |
| complaint | Thank you for telling us about your experience. We are sorry {complaint_detail}. {owned_sentence} Please contact {channel} so our team can look into this for you. |
| factual_error | Thank you for writing. Our record for {confirmed_item} shows {confirmed_fact}. If you have a receipt or confirmation, please contact {channel} and our team will review it with you. |
| abusive | We are sorry you had a poor experience with {business}. We will not respond to the language in the review. If you have a specific concern, please contact {channel}. |

Slot rules:
- `{owned_sentence}` has the form "{business} is responsible for {controlled_item}, and {owner_action}." The owner must supply `{owner_action}`. If the owner supplies none, delete the sentence and set status to partial.
- `{channel}` is the off-platform contact the owner named (V4). Exactly one next step appears in each reply.
- Target 40 to 90 words for the whole reply. If the count is outside that range, shorten or lengthen the fills (`{complaint_detail}`, `{praised_detail}`). Do not change the template sentences.

5. **Check.** Run four checks in order. If one fails, fix the reply and run the checks again. After two fix passes, set status to partial and list the failing check as a blocking item.

| Check | Pass rule |
|---|---|
| C1 Length | 40 to 90 words, counted as whitespace-separated tokens |
| C2 Next step | Exactly one sentence names the contact channel |
| C3 Banned phrases | None of: lying, liar, fake, untrue, "never happened", "you are wrong", "should have", "your fault", "policy states" |
| C4 Identifiers | No reviewer name, order number, address, or account ID, and no phone number or email address except the one the owner named as `{channel}` |

## Output contract

Return exactly this block, with these labels in this order:

```
## Review reply
Status: complete | partial | needs_intake | escalate
Class: praise | mixed | factual_error | complaint | abusive | none
Word count: <integer, or 0 when no reply is drafted>
Verification: V1=<value>, V2=<value>, V3=<value>, V4=<value>, V5=<value>
Blocking items: none | <numbered list>

Reply:
<one paragraph, or none>
```

Each V value is confirmed, not confirmed, or not applicable. When status is needs_intake or escalate, Class is none, Verification reads "not run", Word count is 0, and Reply is none.

Status meanings:
- complete: C1 to C4 pass, and V1 to V5 are each confirmed or not applicable.
- partial: a reply is drafted, but a V item is not confirmed, an owned sentence was dropped, or a check still fails. Remove every sentence whose fact is unconfirmed. Blocking items lists each open item by code.
- needs_intake: one of facts a to c is missing. Blocking items is a numbered question list, one question per missing fact. No reply is drafted.
- escalate: a stop rule below applies. Blocking items gives the reason. No reply is drafted.

## Refuse / stop when

- Escalate: the review states a threat of violence, a health or safety injury, a legal action, or harassment based on a protected trait.
- Refuse the wording, keep the class template, and set status to partial: the owner asks to name the reviewer, quote order or account data, call the reviewer a liar, fake, or competitor, or argue the facts in public.
- Set status to partial: the owner asks for a refund, credit, or discount that the owner did not name (V3 not confirmed).
- Refuse with one line and no output block: the request is to write or post a review, to reply as a different business, or to reply to a review the business did not receive.
