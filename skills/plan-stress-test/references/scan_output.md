# Scan output and finding kinds

## Contents
- What gets parsed
- Output fields
- Finding kinds
- Known misfires

## What gets parsed

- Headings at any level. A heading, or a line such as `Owner: Dana` or `Due: 2026-06-01` directly under it, gives a default owner or date to the steps below it until the next heading of the same or higher level.
- A step is a checklist item (`- [ ]` or `- [x]`), a numbered item (`1.` or `1)`), or a table row whose header has a step-like column (Step, Task, Action, Milestone, Deliverable, Item, Activity) and optionally Owner, Due, Verification (or Done when), Depends on columns.
- Indented plain bullets and indented lines under a step belong to that step, so `- Verify: ...` under a step counts as its done criterion.
- Fenced code blocks are skipped. A step ticked `[x]` is counted as done and is not checked for gaps.
- Plain bullets that are not steps are ignored, except under a heading that mentions dependencies, prerequisites, inputs or external parties: those bullets define dependencies.

Step ids come from a leading id such as `A1:`, `S-3:` or `[B2]`; otherwise `L<line>`. A number typed at the start of a checklist item (`- [ ] 4. Do it`) is also recorded so "step 4" can be resolved.

## Output fields

| Field | Meaning |
|---|---|
| `summary.verdict` | `sound` (no high finding, under 20% of open steps with a gap), `weak` (50% or more with a gap), `gaps` (otherwise), `unstructured` (no steps found) |
| `summary.gap_rate` | open steps missing an owner, a date or a done criterion, divided by open steps |
| `plan_level` | whether the plan has a goal or success wording, a risks or assumptions heading, rollback wording, an out-of-scope statement, with the first line number |
| `owner_load` | open steps per owner, names matched without regard to case |
| `steps[]` | id, line, section, title, status, owners and where they came from (`step` or `section`), date text and ISO form when parseable, `date_kind` (exact, approximate, none), `has_verification`, dependencies with `resolved`, `target` and `how` |
| `findings[]` | kind, severity, line (0 for whole-plan findings), step_id, detail; sorted high, medium, low, then by line |

## Finding kinds

| Kind | Severity | Meaning |
|---|---|---|
| `no_owner` | high | open step with no owner on the step or its section |
| `owner_placeholder` | high | owner is TBD, someone, unassigned and the like |
| `overdue` | high | open step dated before `--today` |
| `dependency_cycle` | high | steps wait on each other in a loop |
| `date_before_dependency` | high | step dated earlier than a step it depends on (both dates fully written) |
| `no_steps` | high | nothing parsed as a step |
| `no_success_criteria` | high | no goal, objective or success-criteria wording anywhere |
| `no_date` | medium | no date or time marker |
| `vague_date` | medium | only a word such as soon, later, ongoing, TBD |
| `no_verification` | medium | no done criterion or check named |
| `undefined_dependency` | medium | a dependency is named but no step, heading or dependency item defines it, or a referenced id or number does not exist |
| `multiple_owners` | medium | more than one owner on a step |
| `owner_concentration` | medium | one owner holds 40% or more of at least 4 open steps |
| `open_placeholder` | medium | TBD, TODO, ??? left in a step |
| `duplicate_id` | medium | the same explicit id on two steps |
| `no_rollback` | medium | no rollback, fallback or contingency wording anywhere |
| `group_owner` | low | owner is a team or department rather than a person |
| `ambiguous_reference` | low | "step 3" matches numbered items in several sections |
| `no_risk_section` | low | no heading about risks, assumptions or open questions |

## Known misfires

- A person named only in prose ("Dana will handle this") is not detected; the step shows as unowned. Check the text before citing `no_owner`.
- A verb such as "needs", "requires" or "after" in a step title is read as a dependency. When the phrase is really a description, the finding is a false positive; say so in the report.
- A step titled "Run the load test" is not credited with a done criterion because testing is the work, not the check; if the next words say what counts as passing, it is.
- Dependency matching is by shared words. A dependency can be marked defined because a heading uses similar words, or undefined because the plan uses different words for the same thing.
- Table cells that are empty or a dash count as absent. A table with no step-like column is not read as steps.
- Dates without a year are treated as approximate and are never compared.
