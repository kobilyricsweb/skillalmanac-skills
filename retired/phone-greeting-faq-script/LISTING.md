# phone-greeting-faq-script

## One line

Writes a receptionist's phone greeting, a routing menu of up to four options, an after-hours message, eight FAQ answers and three escalation rules from facts the owner supplies.

## What it does

The skill starts from five facts a small business owner already knows: the business name, weekday hours, the street address, what callers should do after hours, and two to four reasons people call. From those it produces a script set that a receptionist or an automated phone menu can read aloud. Each part has a fixed shape so that two businesses using the skill get comparable output. The greeting is one template line of eleven words or fewer. The routing menu lists the call reasons in the owner's order, with the desk that handles each one. The after-hours message repeats the hours and asks the caller for a name, a callback number and a reason. The FAQ table always has the same eight questions in the same order, and each answer is limited to thirty words and drawn only from supplied facts. A missing fact is written as TO-CONFIRM and listed once at the end, so the owner sees exactly what is still open. Escalation rules are three fixed rows, emergency, complaint and billing, each triggered by plain words the caller uses. The skill never judges how serious a medical problem is.

## When to use

- A practice or shop answers calls inconsistently, and staff give different hours or addresses.
- An owner is setting up a phone menu or an automated receptionist and needs the spoken lines first.
- A new front-desk hire needs one approved set of answers to read from during the first weeks.

## When not to use

- The caller needs triage, a diagnosis, or a judgment about whether a symptom is serious.
- The owner wants prices, insurance plans or policies written in without supplying them. The skill marks them TO-CONFIRM and does not fill them in.
- The call is a billing dispute, a legal question or an insurance coverage question, which need a person to decide.

## Requirements

A text-capable agent. No scripts, no network access and no files beyond the skill itself. The owner must supply the five required intake facts before the skill writes anything. If any is missing, the skill returns a numbered question list instead of a script.

## Example

Input the owner supplied for this run (Maple Dental Care is a fictional test name): hours Monday to Friday 8:00 AM to 5:00 PM, Saturday 9:00 AM to 1:00 PM, closed Sunday; address 412 Elm Street, Suite 2, Springfield, IL 62701; after hours callers leave a message and staff returns calls the next business day; call reasons appointments, billing questions, records requests and new patients, routed to the front desk except billing; new patients welcome; 24 hours notice requested for cancellations; emergencies go to an on-call line whose number was not given. Insurance plans, fees and parking were not given.

Output:

## Status

partial

## Greeting

Thank you for calling Maple Dental Care, how can I help?

## Routing menu

| Key | Option wording | Routes to |
|---|---|---|
| 1 | Appointments | Front desk |
| 2 | Billing questions | TO-CONFIRM: billing desk |
| 3 | Records requests | Front desk |
| 4 | New patients | Front desk |

## After-hours message

Thank you for calling Maple Dental Care. We are closed now. Hours: Monday to Friday, 8:00 AM to 5:00 PM; Saturday, 9:00 AM to 1:00 PM. Please leave your name, callback number, and reason for calling. We return calls the next business day.

## FAQ

| # | Question | Answer | Words |
|---|---|---|---|
| 1 | What are your hours? | We are open Monday to Friday, 8:00 AM to 5:00 PM, and Saturday, 9:00 AM to 1:00 PM. We are closed Sunday. | 22 |
| 2 | Where are you located? | We are at 412 Elm Street, Suite 2, Springfield, IL 62701. | 11 |
| 3 | Are you accepting new patients? | Yes, we welcome new patients. Call the front desk to book your first visit. | 14 |
| 4 | Do you accept my insurance? | TO-CONFIRM: list of insurance plans accepted. | 6 |
| 5 | How much does a visit cost? | TO-CONFIRM: fees for common visits and cleanings. | 7 |
| 6 | How do I cancel or reschedule? | Please give us at least 24 hours notice to cancel or reschedule. Call the front desk to change your appointment. | 20 |
| 7 | Do you handle emergencies? | TO-CONFIRM: on-call number for emergencies | 5 |
| 8 | Where can I park? | TO-CONFIRM: parking options near the office. | 6 |

## Escalation rules

| Trigger | Action | Route |
|---|---|---|
| Emergency: caller says emergency, severe pain, swelling, or bleeding | Transfer the call to the on-call line now. Do not book an appointment. | TO-CONFIRM: on-call number |
| Complaint: caller says complaint, unhappy, or upset | Take name, callback number, and a one-line summary. Do not argue, promise refunds, or resolve the issue. | TO-CONFIRM: complaint desk |
| Billing: caller says balance, invoice, or payment | Take name and callback number. Do not quote balances. | TO-CONFIRM: billing desk |

## TO-CONFIRM

1. Insurance plans accepted (FAQ 4).
2. Fees for common visits (FAQ 5).
3. On-call number for emergencies (FAQ 7 and Emergency row).
4. Parking options near the office (FAQ 8).
5. Billing desk name (routing menu row 2 and Billing row).
6. Complaint desk (Complaint row).

## Limits

- The word counts are whitespace-token counts. A word processor may count times, hyphenated words or addresses differently, so the Words column is only as exact as the rule it follows.
- The 6-word option limit and the 50-word after-hours limit are working values, not published standards. The 11-word greeting limit and the 30-word answer limit are fixed rules of this skill.
- The skill writes English scripts with US conventions only. It does not translate and does not handle other phone systems' special codes.
- It does not check whether the owner's facts are true. It only refuses to add facts the owner did not give.
- Escalation triggers are exact keyword matches. A caller who describes an emergency without the listed words will not fire the row. The trigger words are working values that the owner confirms before use.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
