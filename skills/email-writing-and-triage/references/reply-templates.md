## Contents

1. How to fill a template
2. Decline
3. Delay
4. Ask
5. Confirm
6. Follow-up nudge
7. Worked slot example

# Reply templates

Templates are skeletons. Replace `<angle brackets>` with words from the thread. A value that is not in the thread or in the user's chat becomes `[[NEEDS FROM YOU: <what>]]`; never fill it with a guess. Delete any sentence you cannot fill honestly.

## 1. How to fill a template

1. Greeting: first name if the sender signed with one; otherwise "Dear <title> <surname>". No greeting line longer than 4 words.
2. Sentence 1 is the decision or the answer.
3. Every date, amount, name of a product or a person that appears in the body must be listed on the `Basis:` line with its source (thread or user chat).
4. Sign-off: "Best regards," or the register the sender used, then the user's name.
5. Address the draft to the sender only. If the thread has other people, do not mention them, even as "cc'ing".

## 2. Decline

```
Hi <name>,

Thank you for <what they offered or asked>. I'm not able to <the request in their words>.

<One reason, only if the user gave one or the thread makes it obvious.> <Alternative, only if the user gave one: "[[NEEDS FROM YOU: alternative or none]]".>

Best regards,
<user>
```

Rules: no "unfortunately" stacks, no "maybe later" unless the user said so, no counter-offer with new numbers, 90 words or fewer. A decline never apologises more than once.

## 3. Delay

```
Hi <name>,

I've received <what>, and I need <what is pending, e.g. input from X> before I can answer.

I'll get back to you by [[NEEDS FROM YOU: reply date]].

Best regards,
<user>
```

Rules: the reply date comes only from the user. If the user gives none, keep the slot; do not write "soon", "this week" or "shortly" as a substitute, because each reads as a promise. Name the pending item generically if it involves a third party ("some input from my side"); do not name people from Cc.

## 4. Ask

```
Hi <name>,

Thanks for <what>. To <move forward>, I need to check:

1. <Question one, one fact asked for.>
2. <Question two, only if the thread truly lacks it.>

Once I have this I can <next step in the thread's own words>.

Best regards,
<user>
```

Rules: at most 3 numbered questions; no question the thread already answers (re-read first); no question that asks the sender to commit to a price or date on the user's behalf.

## 5. Confirm

```
Hi <name>,

Confirming <the thing>: <facts exactly as written in the thread: date, time, place>.

<One line on what happens next, if the thread says so.>

Best regards,
<user>
```

Rules: copy facts character for character from the thread, including the time zone if given. If two messages in the thread disagree on a fact, do not confirm; use ask. Confirming a payment amount follows the same rule.

## 6. Follow-up nudge

```
Hi <name>,

Following up on <subject in plain words>: I'm still waiting for <the one thing>.

Could you send it by [[NEEDS FROM YOU: date]]? If it's easier to talk, say so and I'll call.
```

Rules: one nudge per thread by the user; a second goes to the user as a note ("escalate or let go?"). 60 words or fewer. No guilt wording ("as I mentioned", "again").

## 7. Worked slot example

Thread (from the sender, 2026-11-17): "Can you do 10 cases at 5% off, delivered the week of the 23rd?" The user typed in chat: "Tell him yes to the week, no to the discount."

```
DRAFT pricing-2027 | to: sender only | intent: confirm + decline
Hi Mo,

Yes, the week of the 23rd works. The 5% discount isn't something I can offer on this order.

[[NEEDS FROM YOU: unit price or "as per last quote" - the thread states no price]]

Best regards,
[[NEEDS FROM YOU: sign-off name]]
Basis: "week of the 23rd" (thread, sender); decline of discount (user chat); "10 cases" omitted because no unit price is known
Slots: price line, sign-off name
```

Note what the draft does not do: it does not restate 10 cases with a total, does not invent a delivery day inside the week, and does not suggest a smaller discount.
