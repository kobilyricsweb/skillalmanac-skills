## Contents

1. Is this an ADR at all
2. The five decidability tests
3. Option block shape
4. Status lifecycle, with the exact edits
5. Retroactive and unfinished decisions
6. Scanner rules and the fix for each

## 1. Is this an ADR at all

Write one when at least one of these holds. These cut-offs are working values, not standards.

| Trigger | Example |
|---|---|
| Reversal would cost more than about two engineer-weeks | database engine, message broker, auth provider |
| It binds more than one team or service | shared schema, wire format, API versioning rule |
| People will ask why it was done this way in six months | an unusual choice that looks like a mistake |
| It sets a rule others must follow | all money is integer minor units |

Do not write one for a library bump, a naming nit, or a reversible choice inside one module. A pull request description is enough.

## 2. The five decidability tests

An ADR is decidable when a reader who was not in the room can answer all five from the text alone. Check each before running the scanner.

1. **Forced**: Context names the constraint that made a decision necessary now, preferably with a number (events per second, monthly cost, team size, deadline). "We need scalability" fails.
2. **Real alternatives**: at least two options that a sensible person could choose. "Do nothing" counts as an option only if its cost is stated. A straw option written to lose fails.
3. **Costed**: every option, including the chosen one, states one downside. A downside with a figure or a named failure ("two months before we trust it", "no replay") passes; "more complex" alone fails.
4. **Traceable**: the Decision sentence names the chosen option and one reason that points back to a fact in Context. The reason must not be a property all options share.
5. **Owned**: Consequences lists what gets worse and who carries it, plus follow-up work and the trigger that reopens the decision. An accepted ADR whose consequences are all positive has not finished the analysis.

## 3. Option block shape

Three lines are enough: what it is; where it wins; its cost. A comparison table is allowed only when two or more options share three or more measurable criteria. Never score options with invented numbers; if a figure is an estimate, say "estimated" and give the unit.

## 4. Status lifecycle, with the exact edits

| From | To | When | Edits |
|---|---|---|---|
| (new) | proposed | drafted, not yet agreed | `Status: proposed` |
| proposed | accepted | deciders agreed | status and date; fill Consequences fully |
| proposed | rejected | deciders turned it down | status; one line in Decision saying why |
| accepted | superseded | a newer ADR replaces it | see below |
| accepted | deprecated | no longer applies, nothing replaces it | status; one line saying why |

Accepted ADRs are history. After acceptance change only the status line and the supersede links. If the reasoning was wrong, supersede; do not rewrite.

Superseding, in this order (the scanner checks the end state):

1. Create the new ADR with the next free number and `Supersedes: <old number>`.
2. In the old ADR set `Status: superseded` and `Superseded by: <new number>`.
3. The new ADR's Context says what changed since the old decision, with a fact (date, load, cost).
4. Run the scanner: no `missing-backlink`, `broken-link` or `successor-status-mismatch`.

Numbers are never reused and never renumbered. A deleted file leaves a gap, and the scanner reports gaps as warnings so someone can explain them.

## 5. Retroactive and unfinished decisions

- Retroactive: add `Recorded retroactively on <date>` under Date. List only options the people actually weighed. If nobody weighed an alternative, write one option and say "no alternative was evaluated"; the scanner reports `few-options`, which is the honest signal. Do not invent a comparison to quiet it.
- Not yet decided: status `proposed`; Decision starts with "Proposed:". Put the open question first in Context. Never mark an ADR accepted on the author's own authority.
- Reasons the user did not give stay blank or are asked for; do not infer motives.

## 6. Scanner rules and the fix for each

| Rule | Severity | Fix |
|---|---|---|
| bad-filename | warning | rename to `NNNN-slug.md` |
| duplicate-number | error | renumber the newer file to the next free number and fix links to it |
| numbering-gap | warning | explain it in an index, or accept it; never renumber to close it |
| bad-title, title-number-mismatch | error | H1 like `# 0007. Title`, number equal to the file name |
| duplicate-title | warning | retitle so each names its own choice, or supersede one |
| missing-status, bad-status | error | one of proposed, accepted, rejected, deprecated, superseded |
| missing-section, empty-section | error | add the section from the template and fill it |
| few-options | error | add the option actually considered, or record "no alternative evaluated" and have a human accept the gap |
| option-no-downside | warning | add the real cost; heuristic, so confirm by reading |
| accepted-no-consequences, thin-consequences | error, warning | write benefits, costs, follow-up; under 15 words counts as empty |
| placeholder-text | error unless proposed | replace TBD, TODO and template brackets |
| broken-link, unparsable-link | error | point to an existing ADR number or remove the claim |
| missing-backlink | error | add the reverse `Supersedes` or `Superseded by` line |
| superseded-without-successor | error | add `Superseded by: NNNN` or change the status |
| successor-status-mismatch | error | a record with a Superseded by link must have status superseded |
| successor-not-accepted | warning | the replacement is still proposed or rejected; fix one side |
| self-reference | error | remove the link |
