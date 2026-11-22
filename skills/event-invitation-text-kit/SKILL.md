---
name: event-invitation-text-kit
description: Writes invitation text and a two-message reminder sequence for a club meetup, party, workshop, or similar event, after checking a required-facts list. Use when a host needs an invitation or reminders and the date, place, start time, RSVP date, dress or bring details, or contact must be confirmed before sending. Missing facts are marked TO-CONFIRM and never invented. Do not use for ticket sales, collecting payments, bulk marketing email, or notices that claim to come from a real organization or official body.
license: Apache-2.0
compatibility: Requires no tools beyond a text-capable agent (type B); no scripts and no network.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# Event Invitation Text Kit

Use this procedure to turn a host's event facts into an invitation of 50 to 100 words and two reminders of 15 to 50 words each. Facts the host did not give stay as TO-CONFIRM. The kit writes text only. It sends nothing.

Shipped files: [LICENSE.txt](LICENSE.txt). This skill has no scripts.

## Workflow

1. **Intake the facts.** Read the host's message. Output: the Facts table (see Output contract), one row per required fact, with GIVEN or TO-CONFIRM.
2. **Set the send date.** Use the send date the host gives. If none is given, use today's date and record it as ASSUMED. Output: one line `Send date used: YYYY-MM-DD`.
3. **Count days to the event.** Output: `Days from send date to event: N`, computed from the send date and the event date.
4. **Choose the run status and reminders.** Apply the Decision table. Output: the Status line and the reminder plan (both, Reminder 2 only, or none).
5. **Draft the invitation.** Use the line order in the Invitation template below. Output: invitation text and `Words: N`.
6. **Draft the reminders.** Reminder 1 is sent 7 days before the event. Reminder 2 is sent 1 day before. Output: each reminder with `Words: N`, or `Not needed: <reason>`.
7. **Run the nine checks.** Output: the Checks line. If a check fails, fix the text once and run the checks again. If a check still fails, keep the text, set `Checks: failed <check numbers>`, and say which check failed.
8. **List the open questions.** Output: a numbered list with one question for each TO-CONFIRM row.

## Required facts

| Fact | Format rule | If missing |
|---|---|---|
| What (event name or type) | 2 to 8 words, for example "monthly chess club meetup" | blocked |
| Date | Weekday, month day, year | blocked |
| Place | Venue name, street address, city | blocked |
| Start time and time zone | Clock time plus ET, CT, MT, PT, or a named zone | TO-CONFIRM |
| RSVP date | Weekday, month day, on or before the day before the event | TO-CONFIRM |
| Contact | Name plus one email or phone number the host gives | TO-CONFIRM |
| Dress or bring | One line, or "None" if the host says so | TO-CONFIRM |
| Cost | Written only if the host gives a price or says "free". If the host says the event is paid but gives no price, the row is TO-CONFIRM. | OMITTED (no line, no question) |
| Send date | Given, or today's date | ASSUMED |

## Decision table

| Condition | Action | Run status |
|---|---|---|
| What, date, or place missing | Stop. Output the Status, Facts table, and questions for those facts only. No invitation, no reminders. | blocked |
| All required rows GIVEN, no TO-CONFIRM rows | Write the full set. | complete |
| Date, place, and what are GIVEN, one or more rows TO-CONFIRM | Write with TO-CONFIRM markers in place of the missing values. | partial |
| Days from send date to event is 8 or more | Write Reminder 1 and Reminder 2. | per above |
| Days from send date to event is 2 to 7 | Write Reminder 2 only. Reminder 1 reads `Not needed: event is under 8 days after the send date`. | per above |
| Days from send date to event is 0 or 1 | Write no reminders. Each reminder reads `Not needed: event is under 2 days after the send date`. | per above |

Working values: the 8-day and 2-day thresholds are working values, not a published rule.

## Length and wording limits

| Piece | Minimum words | Maximum words |
|---|---|---|
| Invitation | 50 | 100 |
| Reminder 1 | 15 | 50 |
| Reminder 2 | 15 | 50 |

A word is any run of characters separated by spaces. The marker is the literal token `TO-CONFIRM`, with no added description, and counts as one word each time it appears.

Banned phrases (working list, zero allowed): "don't miss", "unforgettable", "amazing", "exciting", "epic", "can't wait", "huge". Exclamation marks are not allowed in any piece.

## Invitation template (line order)

1. Opening line: `You are invited to the <what>.`
2. When: `When: <weekday>, <month> <day>, <year>, at <start time and zone>.`
3. Where: `Where: <place>.`
4. Dress or bring: `Dress or bring: <value>.`
5. RSVP: `RSVP by <date> to <contact name>, <contact email or phone>.`
6. Accessibility and dietary line, exactly: `If you need an accommodation or have a dietary need, tell us when you RSVP.`
7. Closing line: `We look forward to seeing you.`

Reminder 1 states the event is one week away. Reminder 2 states the event is tomorrow. Both repeat the date, time, and place, and include the contact line.

## Output contract

Use these headings in this order. No other headings.

- `## Status`: lines `Status: complete | partial | blocked`, `Send date used: YYYY-MM-DD`, `Days from send date to event: N`, `Missing: N TO-CONFIRM items`, `Checks: N of 9 passed`.
- `## Facts`: a table with columns Fact | Value | Status. Status is GIVEN, TO-CONFIRM, OMITTED, or ASSUMED.
- `## Invitation`: the text, then `Words: N`.
- `## Reminder 1 (7 days before)`: the text and `Words: N`, or `Not needed: <reason>`.
- `## Reminder 2 (1 day before)`: the text and `Words: N`, or `Not needed: <reason>`.
- `## Questions for the host`: a numbered list, one question per TO-CONFIRM row, in table order. Omit the heading when there are none.

For blocked runs, output only `## Status`, `## Facts`, and `## Questions for the host`. Each question names the missing fact, for example "1. What is the date of the meetup?"

## Checks

| No. | Check | Pass rule |
|---|---|---|
| 1 | Invitation length | 50 to 100 words |
| 2 | Reminder length | Each reminder 15 to 50 words, or marked Not needed |
| 3 | Time zone | A stated start time carries a zone abbreviation or named zone; a TO-CONFIRM start time passes |
| 4 | Weekday | The weekday matches the calendar date |
| 5 | No invented values | Every date, time, place, name, price, and contact is GIVEN, ASSUMED, or TO-CONFIRM |
| 6 | Banned phrases | None from the list |
| 7 | Punctuation | No exclamation marks |
| 8 | Accessibility line | Present in the invitation, exact wording |
| 9 | Question match | TO-CONFIRM rows in the Facts table equal the items in the questions list |

## Refuse or stop when

- The host gives no what, date, or place. Return the blocked output.
- The host asks for a venue, start time, price, host name, or phone number that was not given. Write TO-CONFIRM, never the value.
- The text would claim to be an official notice or endorsement from a government office, school, employer, company, charity, or public official.
- The invitation would collect payment, bank details, government ID numbers, or passwords.
- The host asks the kit to send, schedule, or deliver the messages. Return the text only.
- The host asks for a ticket sales campaign or bulk marketing email.
