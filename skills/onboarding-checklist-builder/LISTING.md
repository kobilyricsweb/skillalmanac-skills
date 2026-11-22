# Onboarding checklist builder

## One line

Turns a role, team and start date into a dated onboarding checklist with an owner, a due date and checkable done-evidence for every item.

## What it does

The skill walks an agent through one new-hire plan in a fixed order. It first collects an intake block: role title, team, manager role, start date, team tools, location and buddy. It then computes the calendar dates for the period before day 1, week 1, and days 30, 60 and 90. Each item is assigned to a default owner from a short decision table, so access requests go to the IT administrator, buddy introductions go to the manager, and reading assignments go to the new hire. Every item carries an ID, a due date in ISO format, and a done-evidence field that a third party can check, such as a ticket number or a saved log.

The output is a single Markdown document with fixed sections and table columns. Access and equipment come first because those items have the longest lead time. Success outcomes at day 30, 60 and 90 name the manager as the confirmer. Anything that touches HR or legal compliance is moved to a Routed to HR list instead of being written out.

## When to use

Use it when a manager needs a checklist for one specific hire and has a start date but no written plan. It also fits a team lead who keeps onboarding notes in chat or email and wants them turned into one table that can be pasted into a tracker. The thresholds in the skill, such as 15 to 26 total items, are working values that keep a plan short enough to finish and long enough to cover the first 90 days.

## When not to use

Do not use it for policy acknowledgements, tax or visa steps, background checks, or labor-law wording. Those belong to HR, and the skill routes them to a list instead of drafting them. It is also not for offboarding, performance reviews, or a multi-person hiring cohort in one file. It does not send messages, open tickets, or update accounts.

## Requirements

Any text-capable agent that can read the intake fields and produce Markdown. There is no script, no package, and no network access. The skill file is the only input.

## Example

Excerpt from the smoke run for a junior data analyst starting on 2027-01-11 (the full output is in VERIFICATION.md):

```
## Access and equipment
| ID | Item | Owner | Due (YYYY-MM-DD) | Done evidence |
|---|---|---|---|---|
| ACC-01 | Warehouse SQL client account, read access to analytics schemas | IT administrator | 2027-01-06 | Access ticket number filed; test login logged |
| ACC-02 | BI dashboard tool seat, viewer plus author | IT administrator | 2027-01-06 | Seat assignment in admin console |
| ACC-03 | Ticketing tool and team chat accounts | IT administrator | 2027-01-06 | Account email confirmed by new hire in ticket |
| ACC-04 | Laptop with spreadsheet suite and SQL client installed; shipped to remote address | IT administrator | 2027-01-04 | Asset tag logged to new hire record |

## Week 1
| ID | Item | Owner | Due (YYYY-MM-DD) | Done evidence |
|---|---|---|---|---|
| W1-01 | Team tool first-login check | Manager | 2027-01-11 | Login log in ticket |
| W1-02 | Read team metric definitions document | New hire | 2027-01-15 | Questions list sent to buddy |
| W1-03 | Walk-through of current dashboards | Buddy | 2027-01-15 | Dashboard list annotated in team folder |
| W1-04 | Introduction meeting with a data consumer; manager invites | New hire | 2027-01-15 | Meeting notes in team folder |
```

## Limits

Business-day due dates do not consult a holiday calendar, so a due date can land on a public holiday. The skill flags a holiday in Open questions only when the agent knows about it. Default owners are role titles from a fixed table; a team with different ownership needs the table edited before use. The thresholds are working values chosen for a single-hire plan and are not drawn from any published standard. The skill does not check whether the tools named in the intake exist or whether the team can grant access to them.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
