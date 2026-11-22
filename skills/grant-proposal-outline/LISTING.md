# grant-proposal-outline

## One line

Turns a funder's pasted guidelines and your own program data into a grant proposal outline with word budgets that add up to the limit, a criteria map, a need-claims table, an outcomes table, and a budget skeleton that marks every missing figure TO-CONFIRM.

## What it does

The skill reads the funder's criteria and word limit first. It lists each criterion with the guideline heading it came from, then splits the limit across the seven standard sections: Summary, Need, Program, Outcomes and measures, Organizational capacity, Evaluation, and Budget narrative. Each criterion lands in one primary section. The section budgets use fixed default shares, so a 1,500-word limit gives 120, 270, 330, 225, 180, 195 and 180 words, which sum to exactly 1,500.

For the need and outcomes parts, the skill accepts only figures you supply. Each figure carries a source tag (USER-DATA or PUBLIC with a citation), and anything untagged is removed. Missing targets, counts and budget amounts stay as TO-CONFIRM rather than being estimated. If your line items do not add up to the requested total, the skill reports the gap and changes neither number.

The result ends with a status line (complete, partial or stopped) and a numbered list of open items, so you know exactly what to fill in before drafting prose.

## When to use

- You have a funder's guidelines in hand, with a criteria list and a word limit, and want the outline before writing.
- A draft exists and you want to check whether every criterion has a home and whether the section budgets fit the limit.
- You have program figures from an intake log or attendance record and want them placed in the need and outcomes sections with their sources shown.

## When not to use

- You want finished proposal prose. The skill produces skeleton sentences and tables only.
- You need funder research, a list of funders, or eligibility checks against a foundation's public profile.
- The limit is in pages and the guidelines give no words-per-page figure.
- You need the skill to invent a statistic, partner, past result or testimonial. It refuses and leaves TO-CONFIRM.

## Requirements

A text-capable agent. No scripts, no network, no files beyond the pasted guidelines and your own notes. The intake needs the guideline text with at least three criteria, the word limit as a number, a program name, and at least one outcome figure with its source. A requested total is optional.

## Example

The output below is the complete result of one smoke run. The guidelines were fictional, with five criteria and a 1,500-word limit. The program figures and the budget were also fictional test values. The input is described in VERIFICATION.md.

# Grant outline: Reading Circles for Adult Learners
Status: partial
Limit: 1,500 words

## 1. Criteria map
| ID | Criterion | Guideline heading | Section |
|---|---|---|---|
| C1 | Serves adults with low literacy in the county | Eligibility and need | 2 Need |
| C2 | Describes program design with a weekly schedule | Program design | 3 Program |
| C3 | Reports measurable outcomes with targets | Outcomes | 4 Outcomes and measures |
| C4 | Shows organizational capacity and partners | Organization | 5 Organizational capacity |
| C5 | Shows a budget with cost per participant | Budget | 7 Budget narrative |

## 2. Word budgets
| Section | Words |
|---|---|
| 1 Summary | 120 |
| 2 Need | 270 |
| 3 Program | 330 |
| 4 Outcomes and measures | 225 |
| 5 Organizational capacity | 180 |
| 6 Evaluation | 195 |
| 7 Budget narrative | 180 |
| Total | 1,500 |

## 3. Need statement
| Claim | Value | Source tag |
|---|---|---|
| Adults enrolled in 2025 | 412 | USER-DATA: 2025 intake log |
| Sessions per week | 3 | USER-DATA: program manual, 2025 |
| Session length | 90 minutes | USER-DATA: program manual, 2025 |
| Adults on the waitlist | TO-CONFIRM | TO-CONFIRM |
| County adults with low literacy | TO-CONFIRM | TO-CONFIRM: public estimate with source and date |

Adults with limited reading skills need a regular place to practice with peers. Reading Circles enrolled 412 adults in 2025 [USER-DATA: 2025 intake log]. Each group met 3 sessions a week for 90 minutes [USER-DATA: program manual, 2025]. The current waitlist is [TO-CONFIRM: waitlist count]. The county share of adults with low literacy is [TO-CONFIRM: public estimate with source and date].

## 4. Outcomes and measures
| Outcome | Measure | Target | Timeframe | Source |
|---|---|---|---|---|
| Adults who finish the program | Attendance log, sessions attended | TO-CONFIRM | 12 weeks [USER-DATA: program manual, 2025] | 287 of 412 completed in 2025 [USER-DATA: 2025 attendance log] |
| Reading level gain | Placement test score, before and after | TO-CONFIRM | TO-CONFIRM | TO-CONFIRM: test name and score scale not supplied |

## 5. Budget narrative skeleton (proposal section 7)
| Line item | Amount | Basis | Status |
|---|---|---|---|
| Facilitator salary | 30,000 | USER-DATA: 2026 budget sheet | supplied |
| Materials | 4,500 | USER-DATA: 2026 budget sheet | supplied |
| Space rental | 6,000 | USER-DATA: 2026 budget sheet | supplied |
| Evaluation | 3,500 | USER-DATA: 2026 budget sheet | supplied |
| Transportation | 2,000 | USER-DATA: 2026 budget sheet | supplied |
| Line-item sum | 46,000 | computed | n/a |
| Requested total | 48,000 | USER-DATA: 2026 budget sheet | mismatch: 2,000 |

## 6. Open items
1. Section 2: waitlist count (TO-CONFIRM).
2. Section 2: county share of adults with low literacy, with public source and date (TO-CONFIRM).
3. Section 4: target for adults who finish the program (TO-CONFIRM).
4. Section 4: target, timeframe, test name and score scale for reading level gain (TO-CONFIRM).
5. Section 7: the five line items sum to 46,000; the requested total is 48,000. Difference of 2,000 not resolved.

## Limits

- Type B: the skill depends on the agent following the tables exactly. It was checked on one smoke run only.
- Section 6 (Evaluation) gets a word budget only. The skill drafts no evaluation skeleton, so a data source or reporting plan must come from the user's own draft.
- Default shares are working values. A funder that sets its own per-section limits overrides them, and the skill then recalculates the remaining budgets.
- The criteria range (3 to 12) and the outcomes range (2 to 5) are working values, not published standards.
- The skill does not check whether a funder's guidelines are current or whether a foundation still accepts applications.
- Source tags show where a figure came from. They do not verify that the source is accurate.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
