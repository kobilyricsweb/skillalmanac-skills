# event-invitation-text-kit

## One line

Writes an invitation and up to two reminders for a meetup, workshop, or small party, and marks every fact the host did not give as TO-CONFIRM.

## What it does

The kit takes the facts a host has about an event and checks them against a fixed list: what the event is, the date, the place, the start time with a time zone, the RSVP date, a contact, and dress or bring. A missing date, place, or event type stops the run and returns a numbered list of questions, so no invitation is written for an event nobody can locate. When the core facts are present but others are missing, the kit writes an invitation of 50 to 100 words and reminders of at most 50 words each, leaving TO-CONFIRM where the host's answer belongs. It never fills in a venue, time, price, or name.

Every run ends with nine checks: word counts, a zone on any stated time, a weekday that matches the calendar, banned phrases, exclamation marks, the accessibility and dietary line, and a match between open facts and questions. The reminder plan depends on how many days separate the send date from the event. Eight or more days gives two reminders, two to seven gives one, and fewer gives none.

## When to use

Use it for a club, class, workshop, or small party invitation when the host has a date and a place and wants wording that does not drop details. It suits a host who will paste the text into an email or group chat and fill the TO-CONFIRM spots by hand before sending.

## When not to use

Do not use it for ticket sales, paid registration, payment collection, bulk marketing, or any notice meant to read as an official announcement from a company, school, or public office. The kit does not send anything. The host sends the text.

## Requirements

A text-capable agent. There are no scripts, no network calls, and no files beyond the instruction file and the license. The host supplies the facts in chat. The agent must work out the weekday for the event date itself, because the weekday check depends on it.

## Example

Input given: "Monthly chess club meetup, Saturday January 16 2027, Room 2, Cedar Hall, 418 Cedar Lane, Riverton. Nothing else given."

Output, recomputed from SKILL.md after the fix round (the marker is the literal token TO-CONFIRM; word counts are whitespace counts; no new smoke run):

```text
## Status
Status: partial
Send date used: 2026-11-21
Days from send date to event: 56
Missing: 4 TO-CONFIRM items
Checks: 9 of 9 passed

## Facts
| Fact | Value | Status |
|---|---|---|
| What | Monthly chess club meetup | GIVEN |
| Date | Saturday, January 16, 2027 | GIVEN |
| Place | Room 2, Cedar Hall, 418 Cedar Lane, Riverton | GIVEN |
| Start time and time zone | TO-CONFIRM | TO-CONFIRM |
| RSVP date | TO-CONFIRM | TO-CONFIRM |
| Contact | TO-CONFIRM | TO-CONFIRM |
| Dress or bring | TO-CONFIRM | TO-CONFIRM |
| Cost | Not given | OMITTED |
| Send date | 2026-11-21 | ASSUMED |

## Invitation
You are invited to the monthly chess club meetup.
When: Saturday, January 16, 2027, at TO-CONFIRM.
Where: Room 2, Cedar Hall, 418 Cedar Lane, Riverton.
Dress or bring: TO-CONFIRM.
RSVP by TO-CONFIRM to TO-CONFIRM, TO-CONFIRM.
If you need an accommodation or have a dietary need, tell us when you RSVP.
We look forward to seeing you.
Words: 56

## Reminder 1 (7 days before)
One week until the monthly chess club meetup: Saturday, January 16, 2027, at TO-CONFIRM, in Room 2, Cedar Hall, 418 Cedar Lane, Riverton. RSVP by TO-CONFIRM to TO-CONFIRM, TO-CONFIRM.
Words: 29

## Reminder 2 (1 day before)
Tomorrow is the monthly chess club meetup, Saturday, January 16, 2027, at TO-CONFIRM, Room 2, Cedar Hall, 418 Cedar Lane, Riverton. Bring: TO-CONFIRM. Accommodation needs: contact TO-CONFIRM at TO-CONFIRM.
Words: 29

## Questions for the host
1. What is the start time, and in which time zone is it?
2. What is the RSVP date?
3. What is the contact name, and which email or phone number should guests use?
4. Should guests dress a certain way or bring anything?
```

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
