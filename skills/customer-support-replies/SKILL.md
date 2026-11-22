---
name: customer-support-replies
description: Drafts replies to customer support tickets, emails or chats only from the company's policy text, answering every question, promising nothing the policy does not state, and routing anything it does not cover to a human. Each draft carries an internal note of approvals needed, and a bundled script flags unbacked amounts, time frames and promises. Use when the user pastes a ticket, complaint, refund or delivery request and asks for a reply, response or macro for a customer. Do not use for sales outreach, marketing emails, writing the policy itself, or replies to legal claims.
license: Apache-2.0
compatibility: The check script needs Python 3.9 or newer (standard library only). No network access is used. Without Python, apply the checklist in the Verify step by hand.
metadata:
  author: Skill Almanac Editorial
  version: "0.1.0"
  network: none
---

# Customer support replies

Draft the reply a careful senior agent would send: it answers what was asked, says only what the company has actually committed to, and hands the rest to the right person. A warm reply that promises a refund the policy does not allow costs more than a blunt one.

The draft is for a person to approve and send. This skill never sends anything.

## Ground rules

1. **The policy text is the only source of commitments.** Amounts, percentages, time frames, eligibility and exceptions come from the policy document or the ticket. General knowledge of "how stores usually do it" is not a source.
2. **Three answers exist for each request**: the policy says yes; the policy says no (then offer what the policy does allow); the policy does not say, or it requires approval. In the third case do not decide. Tell the customer it is being passed to a person, and put it under `Needs a human`.
3. **Never promise an outcome that someone else decides**, or a time the policy does not give. "I have asked our team to review this" is true; "you will get the credit" is not, until it is approved.
4. **Check conditions with arithmetic.** Count the days between the dates in the ticket and compare them with the policy's limits. Write the calculation in the internal note. If a needed date or fact is missing, ask the customer for it instead of assuming.
5. **Answer every question**, in the order of what matters most to the customer, including the ones with unwelcome answers.
6. **One apology, no blame, no lecture.** Acknowledge the specific problem once. Do not quote policy numbers at the customer as a rebuke, and do not explain what they should have done.
7. **Without a policy document**, ask for it. If none can be supplied, draft only an acknowledgement and the questions needed, and mark every commitment as needing confirmation.

## Workflow

### 1. Set up

Save the customer's message as `ticket.txt` and the policy as `policy.md`. Note today's date if the ticket needs day counts.

### 2. Break the ticket down

List, before writing:

```
request or question | facts given (dates, order status, condition) | policy line that applies | answer: yes / no + alternative / needs a human | missing fact
```

Include requests that are implied ("I want this fixed"), and claims the customer makes about the company's promises; check each claim against the policy.

### 3. Draft

Follow the reply shapes in [references/reply-patterns.md](references/reply-patterns.md); read the section that matches the case (yes, no, mixed, needs a human). Order:

1. Greeting with the customer's name.
2. One sentence that shows the specific problem was understood.
3. The answer to their main question, plainly.
4. What they need to do, as numbered steps if more than one.
5. What happens next, by whom, with a time only if the policy gives one.
6. Remaining questions, each answered in a sentence or two.

Write the draft in this exact structure and save it as `draft.md`:

```markdown
## Reply
<customer-facing text>

## Internal note
Policy used: <each policy line relied on, quoted or referenced>
Day counts: <calculation, or "not needed">
Needs a human: <what must be approved or decided, by which role; or "nothing">
Assumptions: <anything taken from the ticket without proof; or "none">
```

### 4. Verify

```bash
python scripts/reply_check.py draft.md --ticket ticket.txt --policy policy.md
```

- `FAIL UNBACKED NUMBER`: an amount or time frame in the reply is in neither the policy nor the ticket. Remove it or replace it with the policy's wording.
- `FAIL PROMISE WORD`: rewrite as a plain statement of what will happen.
- `FAIL placeholder`: fill it or cut it.
- `WARN` items: fix unless there is a reason not to.
- Tick the printed list of the customer's questions against the reply by eye.
- Re-run until PASS. Do not edit the script or the policy to make the check pass.

Then re-read the reply as the customer: is the answer to their main question in the first three sentences, and is there any sentence that commits someone else?

If the script cannot run, check by hand that every number in the reply appears in the policy or the ticket, and say so in the internal note.

### 5. Deliver

Give `draft.md` content, then one line: `Check: PASS` (or `manual`), and the items under Needs a human repeated so they are not missed.

## Limits

- The script confirms that numbers and promise words are backed by the policy text. It cannot confirm that the right policy line was applied; a person approves each reply.
- Policies with tables of exceptions, regional rules or account-specific terms need the relevant part pasted in. The skill does not look anything up.
- It does not read order systems. Order status, dates and amounts are taken from the ticket as written and listed under Assumptions.
- Formal complaints, chargebacks, injury reports and threats of legal action are routed to a human with an acknowledgement only.
