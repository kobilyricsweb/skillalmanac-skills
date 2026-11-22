The PRD is in prd.md in this folder. It covers SMS-only reminders with a confirm or cancel link, and leaves the timing and cost questions open because the notes disagree.

Decisions needed before build:
- 24 hours (Noor) or 48 hours (Gwen) before the appointment, or both, which doubles SMS cost. Felix decides with Gwen and Noor.
- Who pays for the SMS. Felix said "figure out later", and no owner is named.
- How opt-in is collected for clients who booked by phone. Legal (Idris) requires a dated opt-in record before any text.
- A no-show target. Baseline is 18%, but nobody set a goal, so it is [needs data].

Marked as proposed or assumed: 2 lines. A quarterly check cadence for the no-show metric ([proposed]) and an assumption that existing clients have no recorded opt-in.

Left out on purpose: WhatsApp (SMS only in version one, no business account approval, per Pavel), clients with no mobile number (about 70% have one), and a double reminder unless the team decides it.

Check: PASS (prd_check.py with notes.md).
