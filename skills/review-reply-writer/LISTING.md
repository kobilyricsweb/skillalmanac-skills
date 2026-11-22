# Review Reply Writer

## One line

Drafts one calm public reply to one customer review, after classifying the review and checking each fact the reply would state.

## What it does

The skill takes a review, its star rating, the business name, and the owner's own account of what the business controls. It sorts the review into one of five classes: praise, mixed, factual error, complaint, or abusive. The class decides which sentence pattern the reply follows, so a two-star complaint about a late parcel gets a different structure from a five-star note that mentions one small issue.

Before any wording is written, the skill marks five facts as confirmed, not confirmed, or not applicable. These cover whether the restated detail matches the owner's record, whether the business actually controls the failure, whether any refund or credit is one the owner has authorized, whether the off-platform contact the reply points to exists, and whether the reply contains any customer identifier. A reply can state only confirmed facts, so an unverified claim is removed rather than repeated.

The drafted reply runs 40 to 90 words and contains exactly one next step, a phone line, email address, or form the owner has named. Four checks run on every draft: length, the single next step, a list of combative phrases, and identifiers. The output block reports a status of complete, partial, needs_intake, or escalate, so the owner can see at once whether the reply is ready to post.

## When to use

Use it when a business owner has a specific review open and wants a reply that is neither defensive nor generic. It fits small retailers, service firms, and local businesses that answer reviews themselves and want a consistent structure across different star ratings.

## When not to use

Do not use it for private support messages, for legal or press responses, for requests to post or delete reviews, or for replies on behalf of a different business. It does not write the reviews themselves and it does not decide what remedy a business should offer.

## Requirements

A text-capable agent. No network access, no scripts, and no files beyond the skill itself. The owner must supply the review text, the star rating, and the business name, plus any owned action they want stated.

## Example

The output below comes from the smoke run: a fictional two-star review about a desk that arrived late. The owner confirmed the delay came from the warehouse and said customers are now emailed when dispatch slips. The owner named the customer care phone line, 555-0142 on weekdays, as the contact channel, and named no refund.

```
## Review reply
Status: complete
Class: complaint
Word count: 73
Verification: V1=confirmed, V2=confirmed, V3=not applicable, V4=confirmed, V5=confirmed
Blocking items: none

Reply:
Thank you for telling us about your experience. We are sorry your desk arrived about two weeks later than the date we quoted and that no one told you about the delay. Maple Court Furniture is responsible for the warehouse dispatch delay, and we now email customers whenever dispatch slips. Please contact our customer care team by phone at 555-0142 during weekday business hours so our team can look into this for you.
```

## Limits

The skill cannot check a record. It relies on the owner's statement that a detail matches the business's own system, and it marks a fact unconfirmed when the owner has not said so. It writes in one fixed voice per class, so a business with a distinct tone must edit the output before posting. The 40 to 90 word range and the banned phrase list are working values set by the authoring team, not an external standard. The skill does not judge whether a review is fair, and it does not handle reviews that threaten violence, injury, or legal action; those return an escalate status.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
