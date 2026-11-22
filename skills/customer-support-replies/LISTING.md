## תקציר

- תוכן עמוד ה-skill: מנסח טיוטת תשובה לפניית לקוח רק על סמך מסמך המדיניות של העסק.
- עונה על כל שאלה, לא מבטיח דבר שהמדיניות לא קובעת, ומעביר לאדם את מה שאינו מכוסה.
- לכל טיוטה מצורפת הערה פנימית: סעיפי המדיניות, חישוב ימים, ומה דורש אישור.
- כולל script שמסמן סכומים, זמנים ומילות הבטחה שאין להם כיסוי. בלי רשת. אינו שולח דבר.
- טיוטה: לא לפרסום לפני סקירה אנושית.

---

# Listing page content: customer-support-replies

**One line:** Draft the reply to a customer from your own policy document: every question answered, nothing promised that the policy does not say, and a note of what needs a person's approval.

## What it does

You paste the customer's message and your policy. The skill lists each thing the customer asked for, finds the policy line that applies, and gives one of three answers: yes, no with the alternative the policy allows, or "this needs a person". It counts days against the policy's limits and writes the calculation down. The reply comes with an internal note for whoever sends it. A script flags any amount, time frame or promise word in the reply that is not in the policy or the ticket. It never sends anything.

## Capabilities

- A reply ready to send, plus an internal note: policy lines used, day counts, what needs a human, assumptions.
- A checklist of the customer's questions to tick against the reply.
- `reply_check.py`: unbacked numbers, promise words, unfilled placeholders, blame phrases, repeated apologies.
- Reply patterns for yes, no, mixed and hand-off cases.

## When to use

A refund, return, delivery or warranty ticket needs an answer and you have a written policy; a new agent needs a safe first draft; a customer is angry and you want a reply that does not over-promise.

## When not to use

Sales outreach, marketing email, writing the policy, replies to lawyers or formal claims, analysing ticket volumes.

## Before and after (from saved test runs)

**Without the skill.** A customer says a 45-day-old blender smells of burning and that "your website says satisfaction guaranteed". The plain assistant correctly refused the refund and pointed to the warranty, but never addressed the guarantee claim and decided on its own to tell the customer to unplug the product.

**With the skill.** With the skill: "I can't find it in our customer service policy, so I can't confirm what it covers. I've asked a colleague to check the page you saw." The internal note lists three items for a human: who pays warranty shipping, the website wording, and whether to give safety advice about the burning smell.

## Requirements

Python 3.9 or newer for the script (standard library only). No network access. English wording is assumed by the script.

## Install

To be generated at publication: one pinned command per tool.

## Examples (from saved test runs)

1. Prompt: "Draft a reply to this ticket. Our policy is in policy.md." Result: `evals/runs/c2-blender-45-days/with_skill/draft.md`. 7 of 7 assertions; blind score 9 against 7.
2. Prompt: "Draft a reply to this ticket. Our policy is in policy.md." Result: `evals/runs/c1-broken-lamp/with_skill/draft.md`. 7 of 7; the 20% discount request is passed to the supervisor with no outcome promised.

## Limits

- The plain assistant also made no forbidden promise in these tests. The gain is in routing uncovered questions to a person and in the internal note.
- Replies can read flat. One test reply gave a computed date that falls on a public holiday.
- The script checks that numbers and promise words are backed, not that the right policy line was used. A person approves every reply.
- It does not look up orders; it trusts the ticket.

## Evidence

See `VERIFICATION.md`. In short: 3 tasks, one run each way, one model, Claude Code only, 2026-11-20. Blind grader: with skill preferred in 3 of 3. Static check: 0 fails. Token overhead about +8%. Not tested: other tools, real triggering, repeated runs, human review.

## Demo script (60 to 90 seconds)

1. Show the ticket: broken lamp, wants a refund and 20% off.
2. Show the policy line: agents cannot offer discounts; a supervisor decides goodwill credit.
3. With the skill: the reply (refund yes, discount passed on, no outcome promised) and the internal note with "Needs a human".
4. Run `reply_check.py`: RESULT PASS, and the two customer questions printed as a checklist.

## FAQ seeds

- Does it send the reply? No. It writes a draft for a person to approve.
- What if I have no written policy? It drafts an acknowledgement and questions only, and marks everything as needing confirmation. Not tested.
- Can it offer a discount to calm a customer down? Only if your policy says agents can.
- Does customer data leave my machine? The skill and script use no network. The assistant you run it in has its own data handling.
- Does it connect to my helpdesk? No.
- Does it work in other languages? The method does; the script's word lists are English.

## Changelog

- 0.1.0 (2026-11-20): first version, batch 01.

## License and authorship

Apache-2.0 (proposed; owner decision pending). Drafted and tested by an AI agent on 2026-11-20. No human editor has reviewed it yet.
