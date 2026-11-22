# PRD: Appointment reminders by SMS

Status: Draft. Source: raw notes and the planning meeting (Felix, Gwen, Noor, Idris, Pavel). Author: not stated in the notes.

## Decisions needed
1. Send the reminder 24 hours or 48 hours before the appointment, or both? Both doubles SMS cost (Felix). Decider: Felix (PM), with Gwen and Noor.
2. Who pays for the SMS, us or the salon? Felix said "figure out later". Decider: not named in the notes; needs a business owner.
3. How is opt-in collected for clients who booked by phone and have no number on file? Legal requires recorded opt-in before any text (Idris). Decider: Idris with Felix.
4. What no-show rate do we want to reach? Nobody set a target. Decider: Felix with Noor.

## Problem
Owners of hair and beauty salons using our booking app keep asking for reminders. The no-show rate across all salons last quarter was 18% of appointments (Noor, data team). Evidence that reminders reduce no-shows is not in the notes; Noor refers to studies that use a 24-hour reminder, but they are not cited.

## Users
- Salon owners and staff, who turn reminders on or off for their salon.
- Salon clients who have a mobile number on file and have opted in. About 70% of clients have a mobile number on file; the rest booked by phone and the salon never entered it.
- Not for this version: clients with no mobile number, and clients who have not opted in.

## Success metrics
- No-show rate: baseline 18% of appointments last quarter (Noor), target [needs data] (nobody set one), measured by the data team on the same definition, checked quarterly [proposed].
- SMS cost per message: baseline $0.012 with the current provider, target is to stay at the current figure; total cost depends on the 24 versus 48 hours decision and on who pays.
- Share of reminders where the client confirms or cancels via the link: [needs data].

## Non-goals
- WhatsApp. Felix wants it, but Pavel says SMS only in the first version because WhatsApp needs a business account approval we do not have.
- Both a 24-hour and a 48-hour reminder, unless decided: "both" doubles SMS cost (Felix); see Open questions.
- Reminders for clients without a mobile number on file.
- Salons' own reminder tools: salons that send their own can switch ours off.

## Requirements
- **R1 (Must)** The system sends an SMS reminder before the appointment to each client who has a mobile number on file and a recorded opt-in. The lead time is not decided (see Open questions). Accept: see Open questions for timing; with an opted-in client booked, the SMS arrives at the decided time, and a client with no opt-in receives nothing.
- **R2 (Must)** The client's opt-in is recorded with its date before any text is sent. Accept: opt in a test client; the record shows the date. For a client with no opt-in record, no SMS is sent.
- **R3 (Must)** Each reminder contains a link to confirm or cancel the appointment. Accept: open the link from a received SMS; the client can choose confirm or cancel.
- **R4 (Must)** When the client cancels through the link, the slot is freed in the salon calendar right away. Accept: cancel through the link, then open the salon calendar; the slot shows as free.
- **R5 (Must)** A salon can switch reminders off for the whole salon. Accept: switch reminders off, book an opted-in client; no SMS is sent for that salon. Switch them on again; the next booking gets a reminder.
- **R6 (Should)** The salon can see whether a client confirmed, cancelled or did not respond. Accept: see Open questions (not in the notes; included so the team decides if confirm status is shown to salons).

## Risks and assumptions
- Risk: legal (Idris) says opt-in is not optional. Any send without a dated opt-in record breaks that rule.
- Risk: only about 70% of clients have a mobile number on file, so a large share of appointments get no reminder; the no-show gain is bounded by that coverage.
- Risk: 48 hours may be too early and clients may forget again (Noor); 24 hours leaves salons less time to fill a cancelled slot (Gwen).
- Risk: the cost of SMS has no owner yet; running with unclear payment can stall launch.
- [assumption] Existing clients have no recorded opt-in; the notes do not say whether any exists.

## Open questions
- Reminder timing: 24 hours or 48 hours, or both? Positions: 48 hours so salons can fill a cancelled slot (Gwen) / 24 hours, because the studies use it and 48 is too early (Noor) / both, which doubles SMS cost (raised in the room, costed by Felix). Decider: Felix with Gwen and Noor.
- Who pays for the SMS, us or the salon? Positions: undecided; Felix said "figure out later". Decider: not named in the notes.
- How is opt-in collected for phone-booked clients, and what does the client see? Decider: Idris with Felix.
- What no-show target do we set? Decider: Felix with Noor.
- Should salons see the client's confirm or cancel status (R6)? Decider: Felix with Gwen.
