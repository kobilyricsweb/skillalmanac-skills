# Splitting and criteria: patterns and reasons

Read this when a criterion keeps failing validation, or when you must explain a split.

## Contents
- Why the limits are what they are
- Weak and strong criteria
- Non-goals that earn their place
- Splitting examples
- Sources

## Why the limits are what they are

These are working values, not measured optima.

- **3 engineer-days.** Past this a ticket usually outlives one review cycle and hides partial progress. Teams with a weekly cadence may raise it with `--max-size-days`, never above 5.
- **6 criteria.** Each criterion is at least one test. Above six, the ticket mixes outcomes in nearly every case; the usual fix is to group the criteria and split by group.
- **3 dependencies.** A ticket waiting on four others is rarely one coherent unit.
- **One `when` per criterion.** Two triggers hide which one failed.

## Weak and strong criteria

| Weak | Why it fails | Strong |
|---|---|---|
| Login handles wrong passwords | "handles" is not observable | Given a registered user, when they submit a wrong password, then the form shows "Incorrect email or password" and no session cookie is set |
| Search is fast | no number | Given 10,000 products, when the user searches "shoe", then the first results render in under 400 ms at the 95th percentile |
| It works as expected | restates nothing | name the status, text, row count or state |
| Given a user, when they log in and change their name, then ... | two triggers | two criteria |
| Then the system sends an email | no check on content or time | then an email with subject "Reset your password" arrives within 60 seconds and contains one link |

Invented numbers must be marked `ASSUMED:` so the stakeholder sees them.

## Non-goals that earn their place

A non-goal belongs in the ticket when a reasonable engineer could assume it is included. Good: "Password change itself (T2)". Useless: "World peace". If the neighbour ticket exists, cite its id; if the item is deferred without a ticket, write "later, not planned".

## Splitting examples

- "Users can reset their password" becomes: request link (S), set new password from link (M), rate limit requests (S). Each ships and can be tested alone; T2 and T3 depend on T1.
- "Add reporting" has no stateable `then` for the chart. Add the spike "Decide report metrics and layout with finance" (output: a one-page decision, 2 days); the chart tickets depend on it.
- "Export invoices as CSV and PDF" is two tickets: CSV, then PDF. A shared button, if any, is its own small ticket that depends on whichever export lands first.

## Sources

- Meaning of Given, When, Then: https://cucumber.io/docs/gherkin/reference/
- Small, independent, testable stories (the INVEST checklist, behind several split rows): https://xp123.com/articles/invest-in-good-stories-and-smart-tasks/
