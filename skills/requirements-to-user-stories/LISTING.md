# requirements-to-user-stories

## One line

Turns a numbered requirements list into user stories, Given/When/Then acceptance criteria, and a traceability table, with vague requirements listed separately instead of guessed at.

## What it does

The skill reads a requirements document and gives every requirement an ID in document order. Each requirement is tested for three gaps: no measurable outcome, a pronoun with no clear antecedent, and no role named in the document. A requirement that passes all three becomes one user story in the form "As a role, I want capability, so that result", with two to four Given/When/Then criteria. A requirement that fails any test is listed under Uncovered with a reason code and the single missing fact that would make it testable.

The output is a fixed set of sections: status and totals, a requirements table, the stories, a traceability table, the uncovered table, and open questions. Every story ID appears in the traceability table, so a reviewer can check each story against the requirement it came from.

## When to use

Use it when a product owner or analyst has a short requirements list and needs a first backlog in story form, with the gaps flagged rather than filled in. It suits short feature requests, with a working size of up to 99 requirements, where the goal is to see which requirements are testable as written.

## When not to use

Do not use it to write the requirements themselves, to add features or roles the document does not mention, to estimate story points, or to produce a full test plan. It does not rank priorities and does not check the requirements against any company policy or regulation.

## Requirements

- The requirements text pasted into the chat. No files, network access, scripts, or other tools are needed.
- A text-capable agent that can follow a numbered procedure and fill tables.

## Example

Input: a 12-line expense tracker requirements text with five requirement lines, one of which says the app "should feel fast and be easy to use". The full input is in VERIFICATION.md.

```
## Status
partial
Totals: requirements 5, covered 4, uncovered 1, stories 4, criteria 8.

## Requirements
| ID | Text | Result | Code |
|---|---|---|---|
| R-01 | An employee can submit an expense report with a date, an amount in dollars, and a receipt photo. | COVERED | none |
| R-02 | An approver can approve or reject a submitted expense report. | COVERED | none |
| R-03 | The system emails the employee when an expense report is approved or rejected. | COVERED | none |
| R-04 | An employee can see the status of each expense report they submitted. | COVERED | none |
| R-05 | The app should feel fast and be easy to use. | UNCOVERED | VAGUE_OUTCOME |

## User stories
### S-01 (covers R-01)
As an employee, I want to submit an expense report with a date, an amount in dollars, and a receipt photo, so that my expense is recorded for approval.
- AC1: Given an employee is submitting an expense report, When they enter a date, an amount in dollars, and attach a receipt photo, Then the report is saved with all three.
- AC2: Given the employee has saved the report, When the report is viewed, Then it shows the date, the amount in dollars, and the receipt photo.

### S-02 (covers R-02)
As an approver, I want to approve or reject a submitted expense report, so that each submitted report receives a decision.
- AC1: Given a submitted expense report, When the approver chooses approve, Then the report is marked approved.
- AC2: Given a submitted expense report, When the approver chooses reject, Then the report is marked rejected.

### S-03 (covers R-03)
As an employee, I want to receive an email when my expense report is approved or rejected, so that I am told the outcome of each report.
- AC1: Given an expense report has been approved, When the approval is saved, Then an email is sent to the employee who submitted the report.
- AC2: Given an expense report has been rejected, When the rejection is saved, Then an email is sent to the employee who submitted the report.

### S-04 (covers R-04)
As an employee, I want to see the status of each expense report I submitted, so that I can tell where each report stands.
- AC1: Given an employee has submitted an expense report, When the employee views their expense reports, Then each report shows its status.
- AC2: Given an employee has submitted an expense report, When the employee views the report again, Then it shows the current status.

## Traceability
| Requirement | Story IDs | Criteria | Result |
|---|---|---|---|
| R-01 | S-01 | 2 | COVERED |
| R-02 | S-02 | 2 | COVERED |
| R-03 | S-03 | 2 | COVERED |
| R-04 | S-04 | 2 | COVERED |
| R-05 | none | 0 | UNCOVERED |

## Uncovered
| Requirement | Code | Missing fact |
|---|---|---|
| R-05 | VAGUE_OUTCOME | A measurable target for fast, and a checkable test for easy to use. |

## Open questions
1. What measurable target counts as fast for R-05, and how will easy to use be checked?
2. The document states no benefits, so each so-that clause restates its requirement. Should the owner supply real benefits?
```

## Limits

- The three tests catch vague wording and missing roles. They do not judge whether a requirement is correct, complete, or wanted.
- Benefits in the so-that clause restate the requirement because the document rarely states them. Stories written this way are accurate but thin.
- No check is made for conflicts between requirements, duplicate requirements, or missing requirements.
- Criteria are checked for invented numbers and actors only. They are not checked for whether they would pass in a real system.
- The skill does not read attachments, linked tickets, or prior versions of the document.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
