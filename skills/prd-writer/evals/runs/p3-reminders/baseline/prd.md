# PRD: Appointment Reminders (SMS)

Status: Draft v1 | Date: 2026-11-20 | Source: raw notes + planning meeting

## 1. Problem
Salon owners using our booking app keep asking for reminders. The no-show rate across all salons last quarter was 18% of appointments (Noor, data team).

## 2. Goal
Reduce no-shows by sending clients an SMS reminder with a confirm/cancel link.

Success metric: **no target was set.** Baseline is 18%. A target needs to be chosen; none is proposed here, since nothing in the notes supports a number.

## 3. Scope
### In v1
- SMS reminder before the appointment with a link to confirm or cancel.
- Cancelling via the link frees the slot in the calendar immediately (Pavel).
- Per-salon switch to turn reminders off (Gwen; some salons send their own).
- Client opt-in required before any text, recorded with a date. Legal requirement (Idris), not optional.

### Out of v1
- WhatsApp. It needs a business account approval we do not have (Pavel). Felix wants it later.

## 4. Requirements
| # | Requirement |
|---|---|
| R1 | Send an SMS reminder at a set time before each appointment (timing: open question 1) |
| R2 | The SMS includes a link to confirm or cancel |
| R3 | Cancelling via the link releases the calendar slot immediately |
| R4 | Never send to a client without recorded opt-in; store the opt-in with its date |
| R5 | Salon-level setting to disable reminders |
| R6 | Clients with no mobile number get no reminder |

Not specified in the notes: what "confirm" does to the appointment, message wording, how opt-in is collected (in the booking flow? for existing clients?), and how existing bookings without recorded opt-in are handled. Flagged for design and legal.

## 5. Constraints and numbers
- SMS cost: $0.012 per message with the current provider. For scale, 10,000 reminders cost $120.
- Coverage: about 70% of clients have a mobile number on file; the rest booked by phone and were never entered. The opt-in requirement may reduce the reachable share further, so coverage caps the achievable drop in no-shows.

## 6. Open questions
1. **48h vs 24h.** Gwen (salons): 48h gives time to refill a cancelled slot. Noor: studies she has seen use 24h, and 48h may be forgotten. Sending both doubles SMS cost (Felix). Undecided.
2. **Who pays for SMS?** Us or the salon; currently "figure out later". It affects pricing, so it should be settled before launch.
3. **Success target** (section 2).
4. **Opt-in collection method** (section 4).
