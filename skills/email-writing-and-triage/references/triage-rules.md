## Contents

1. Category order and rules
2. Constants
3. Flags
4. Deadline detection and date resolution
5. Suspicious signals
6. Known false positives and misses
7. Formats and sources

# Triage rules

What `scripts/triage_mailbox.py` does, so a person can reproduce or override any result.

## 1. Category order and rules

Every message gets exactly one category. Rules run top to bottom; the first that applies wins.

1. Message is from an address in `--me`: `waiting_on_them` if it is the latest message of its thread (same subject after removing leading Re:, Fwd:, Fw:, Aw:, Sv: and case) and it asks something; otherwise `sent`.
2. Suspicious score 2 or more: `suspicious`. Signals include a lookalike sender domain (weight 2: not a known domain, but within edit distance 2 of one, or the same after swapping digits for letters, or containing a commonly faked brand name without being that brand's domain; known domains are yours plus every domain you wrote to or copied), a URL-shortener link (1), and urgency wording with a credential request (1 extra). The known-domain list needs `--me`; without it only the brand check runs.
3. Any automated marker: `automated`.
4. `--me` given and you are not in To: `fyi` with reason `cc_only` or `not_addressed_to_me`.
5. Asks something and a deadline is 2 days away or less, overdue, or an immediate word is present: `urgent_reply`.
6. Asks something: `reply`.
7. Otherwise `fyi`.

"Asks something" means, in the new text of the message (quoted lines, the quoted tail and the signature are removed): a question mark followed by space or end of line, or one of these phrases: can you, could you, would you, will you, are you able, do you have, let me know, need you to, need your, send me, send over, kindly, get back to me, your thoughts, waiting for your, action required, please confirm, reply by, please reply, please send; or the word "please" unless it is followed by find, see, note, be advised, disregard or ignore.

Automated markers: sender local part starts with no-reply, do-not-reply, notification(s), mailer-daemon, postmaster, newsletter(s), alert(s), digest, bounce(s) or automated; a List-Unsubscribe or List-Id header; Precedence bulk, list or junk; Auto-Submitted other than no; the word "unsubscribe" in the last 12 non-empty lines.

Without `--me`, every message counts as addressed to you, and rules 1 and 4 never fire.

## 2. Constants

| Name | Value | Reason |
|---|---|---|
| URGENT_DAYS | 2 | a "by Thursday" mail read on Tuesday surfaces before it is overdue |
| STALE_FOLLOWUP_DAYS | 3 | the shortest wait that is not pushy for a plain question |
| MASS_RECIPIENTS | 10 | above this many To and Cc addresses it is a broadcast |
| REPLY_ALL_OTHERS | 2 | two other people on a thread is where reply-all leaks recipients |
| CUE_WINDOW | 40 characters | how far before a date the cue word may sit |
| SUSPICIOUS_SCORE | 2 | one strong signal, or two weak ones |
| MAX_DEADLINES | 5 | per message |

## 3. Flags

| Flag | Meaning |
|---|---|
| `deadline` | at least one deadline mention (deadlines list not empty) |
| `overdue` | a resolved deadline is before the reference date |
| `immediate` | ASAP, urgent or time-sensitive wording |
| `money_mentioned` | currency symbol with a number, an amount with a currency word, or one of invoice, quote, price, pricing, refund, discount, budget, payment. A keyword hit, not a proof of an amount |
| `reply_all_risk` | 2 or more people besides the sender and you are on To or Cc |
| `mass_recipient` | more than 10 To and Cc addresses |
| `attachment` | the words attached, attachment or enclosed, or the export lists attachments |
| `bcc_header` | the export carries a Bcc header; never name those people |
| `no_date` | the message date is missing or unparseable; relative deadlines stay unresolved |
| `stale_followup` | your question has waited 3 days or more |
| `own_deadline_commitment` | your own sent message names a deadline; you promised something |

Flags always come out in this fixed order.

## 4. Deadline detection and date resolution

A mention is kept only when it has a cue: one of by, before, until, till, due (not "due to"), deadline, no later than, on or before, expires, closes, cutoff, latest, found earlier in the same sentence within 40 characters, or "at the latest", "is the deadline", "is due" right after. Self-contained mentions need no cue: ASAP, as soon as possible, urgent, time-sensitive (kind `immediate`, no date), EOD, COB, end of day, close of business (the message date), and "within N hours, days, business days, weeks".

Resolution is against the message's own date:

| Wording | Resolves to |
|---|---|
| ISO date | that date |
| Month and day, with or without year | that day; with no year, the message year, or next year if the date would be more than 30 days before the message |
| today, tonight | the message date |
| tomorrow | message date plus 1 |
| a weekday name | the first such day on or after the message date |
| next + weekday | the first such day after the message date, plus 7 if that lands in the same ISO week as the message |
| end of week, EOW | the Friday of that week (the next Friday if the message is on a weekend) |
| end of month, EOM | last day of the message month |
| within N days / weeks | message date plus N days / 7N days |
| within N hours | message date plus N divided by 24, whole days |
| within N business days | N Monday-to-Friday days later; holidays ignored |
| EOD next to another date ("by EOD tomorrow") | the other date; the EOD token is dropped |

`days_left` is resolved date minus the reference date. The reference date is `--today`, or the newest message date when the flag is absent. Times of day and time zones are ignored; a date is taken as written.

## 5. Suspicious signals

Weight 2: gift card; new, updated or changed bank, account or payment details; a verb of sending or sharing next to password, passcode, one-time code, verification code or 2FA code; bitcoin, crypto or USDT next to pay, send or transfer; wire next to today, urgent, immediately or asap.
Weight 1: account suspended, locked, disabled or closed; verify your account, identity or email; click the link or click here; act now, within 24 hours, final notice, last warning; a Reply-To address on a different domain from the sender.

A real bank notice can reach 2 by wording alone. The category means "do not act from this email", not "this is fraud".

## 6. Known false positives and misses

- "May 5" as a verb phrase ("may 5 people join") reads as a date when a cue precedes it.
- A cue word and a day name in one sentence unrelated to a deadline ("I stand by Monday's notes") is counted.
- A quoted reply in a client format the script does not recognise leaves old text in; old deadlines then reappear.
- A question inside a forwarded block counts as a question to you.
- Cc-only detection needs exact addresses in `--me`; aliases and distribution lists are not known.
- Thread grouping by subject merges unrelated mails that share a bare subject such as "Hello".

## 7. Formats and sources

JSON input: a list, or an object with a `messages` list; fields in the script docstring. mbox-like input: each message begins with a line starting "From " (the mbox separator, which follows a blank line), then headers, a blank line and the body; lines starting ">From " are unescaped. Subjects and names in encoded-word form are decoded.

Background facts, in my own words:
- RFC 4155 (https://www.rfc-editor.org/rfc/rfc4155) registers the mbox media type and the "From " separator line convention.
- RFC 3834 (https://www.rfc-editor.org/rfc/rfc3834) defines the Auto-Submitted header whose value other than "no" marks machine-generated mail.
- RFC 2369 (https://www.rfc-editor.org/rfc/rfc2369) defines List-Unsubscribe and related list headers.
- RFC 5322 (https://www.rfc-editor.org/rfc/rfc5322) defines the header and date formats parsed here.
