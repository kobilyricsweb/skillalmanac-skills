# formal-letter-writer

## One line

Drafts a complaint, request or notice letter from intake answers, with a fixed layout, a three-level tone ladder and a fact ledger that ties each sentence to something the user said.

## What it does

The skill walks the agent through seven fixed steps. It first sorts the matter into complaint, request or notice, then collects a short intake: sender and recipient details, reference numbers, dates, the facts in date order, the outcome wanted and a deadline. Missing required fields are asked for once, in a single list. If they stay missing, the letter carries bracketed placeholders and those placeholders are listed at the end.

The letter is built in a set order: sender block, date, recipient block, reference line, salutation, a purpose sentence, facts, one request, one deadline, enclosures and a closing. The body is held between 120 and 300 words. A tone level (neutral, firm or final notice) sets the opening wording, the working deadline and how far the next step may go.

Every factual sentence must trace to a row in a fact ledger. Sentences without a ledger row are removed before the letter is returned. The reply uses four headings only: the letter, the fact ledger, the missing items and the tone level.

## When to use

Use it when a person has a faulty purchase, a disputed charge or a service that failed, and needs a letter to a company or agency that sets out the reference, the timeline and a clear request. It also fits a formal request to a landlord or employer, or a notice that states a deadline, when the user already knows the facts and wants them arranged properly.

## When not to use

Do not use it for legal advice, for letters that threaten court action or a regulatory complaint in the user's name, for cover letters, for personal or condolence letters, or for any letter that needs facts the user has not supplied. The skill refuses those requests or narrows them to a neutral draft, and it sends disputes over a sizeable sum to a professional adviser.

## Requirements

A text-capable agent. No scripts, no installed packages and no network access are needed. The user must supply at least the sender, the recipient, the desired outcome and the letter date.

## Example

Excerpt from the smoke letter produced by following SKILL.md, for a refund on a blender that stopped working:

```
Re: Order 48213, refund for faulty blender

Dear Sir or Madam

I am writing about a faulty blender bought from Example Ltd and a refund for it.

I bought the blender under order 48213 on 3 March 2026 for 89.99. I used it for the first time on 4 March 2026 and it worked. On 5 March 2026 it stopped during its second use, and the motor would not start again.
```

## Limits

The skill does not check whether a claim is true, and it cannot verify the recipient's address or complaints process. Deadlines and word ranges are working values chosen by the editor, not published standards. The skill does not handle languages other than English, and it does not produce documents in Word, PDF or other file formats. Output is plain text for the user to copy into their own system.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
