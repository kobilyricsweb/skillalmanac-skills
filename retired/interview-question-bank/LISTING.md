# Interview question bank

## One line

Builds one fixed interview question set for one role, tied to that role's outcomes and scored on four-point anchors.

## What it does

The skill takes three intake facts: a role title, three or more outcomes the hire must deliver in the first 12 months, and a level (individual contributor, lead, or manager). It turns the outcomes into four or five competencies and writes two past-behavior questions for each. Every question carries one follow-up probe, three strong-answer markers, three weak-answer markers, and four scoring anchors. Any question that touches age, family, health, religion, national origin, sexual orientation, or political affiliation is rewritten on the same competency, and the removal is listed in a Removed items table. The headings are fixed, so two interviewers can run the same bank and compare scores. When the intake is incomplete, the skill returns a partial status and a numbered list of questions instead of guessing the missing facts.

## When to use

A hiring manager is preparing a panel for one open role and wants the same questions for every candidate. Interviews for the role have drifted into small talk, and the panel needs something concrete to hold to. A team needs scoring anchors written before the first interview, so that scores from different interviewers mean the same thing.

## When not to use

Do not use it to write the job description, screen resumes, rank candidates, or score a finished interview. The skill produces the bank and nothing else. It does not read candidate answers, and it does not decide who advances.

## Requirements

A text-capable agent. No scripts, no network access, and no files beyond the skill folder. The intake must be typed into the conversation by the user.

## Example

The example is a complete bank for a customer support lead, built by following the procedure in the skill. All five outcomes were one sentence each, so the status is complete, and the bank has five competencies, ten questions, and a maximum score of 40.

```markdown
# Interview question bank: Customer Support Lead

## Status

Status: complete

## Intake check

| Fact | Value |
|------|-------|
| R1 | Customer Support Lead |
| R2 | Five outcomes, one sentence each (listed in Competencies) |
| R3 | Lead |

## Competencies

| # | Competency | Outcome it maps to |
|---|------------|--------------------|
| C1 | Queue performance under pressure | Keep first-response time under four hours on every queue |
| C2 | Root-cause problem solving | Reduce repeat contacts on the same issue |
| C3 | Coaching agents | Coach and schedule a team of six agents |
| C4 | Escalation management | Own the escalation path to engineering and product |
| C5 | Metrics reporting | Report weekly queue metrics to the operations director |

## Questions

**C1-Q1** Describe a time your queue backlog grew faster than your team could clear it. What did you do in the first hour?
Probe: What did you personally change in the schedule?
Strong answer contains:
- Specific backlog size and the target it missed
- A staffing or schedule change the candidate made
- Response time after the change, compared with target
Weak answer contains:
- Team-effort language with no personal action
- No numbers for backlog, time, or result
- Blame for leadership or headcount decisions
Score 1: No backlog example, or no action by the candidate.
Score 2: Candidate acted but gives no response-time figure.
Score 3: Candidate acted and reports response time against the four-hour target.
Score 4: As 3, plus a staffing rule the team kept after the backlog cleared.

**C1-Q2** Tell me about a time you had to hit a service target while your team was short-staffed. How did you decide what to drop?
Probe: What did you tell the team?
Strong answer contains:
- Named the priority queues and the reason for each
- A stated trade-off, such as a delayed low-priority queue
- The target result, with the number and the date
Weak answer contains:
- Every queue treated as equally urgent
- Says the team "pulled through" without numbers
- Dropped work with no notice to anyone
Score 1: No example, or no decision by the candidate.
Score 2: Candidate made a trade-off but reports no result.
Score 3: Trade-off made, and the target result is reported with numbers.
Score 4: As 3, plus a rule for short-staffed days that the team adopted.

**C2-Q1** Describe a recurring customer problem you traced to its source. What evidence did you collect before changing anything?
Probe: How did you check that repeat contacts fell?
Strong answer contains:
- Ticket sample size or time window used for the analysis
- The root cause stated as a process or product fact
- Repeat-contact count before and after the fix
Weak answer contains:
- Fixed the symptom with a canned reply only
- No data gathered before the change
- Cause given as "the customer was confused" with no check
Score 1: No example, or the candidate changed nothing.
Score 2: Candidate made a fix but gives no before and after count.
Score 3: Fix made, with repeat contacts counted before and after.
Score 4: As 3, plus the fix checked again after one full month.

**C2-Q2** Tell me about a process change you made that another team resisted. How did you win them over?
Probe: What data did you show them?
Strong answer contains:
- The other team's specific objection, stated in their terms
- Data or a pilot shown to that team
- The agreed result, with dates and owners
Weak answer contains:
- Mandated the change without talking to the other team
- Describes the objection as ignorance
- No agreement or follow-through named
Score 1: No example, or no attempt to involve the other team.
Score 2: Candidate persuaded the team but names no agreed result.
Score 3: Team agreed to the change, with a named owner and date.
Score 4: As 3, plus a review the two teams kept after launch.

**C3-Q1** Describe a team member whose quality scores dropped. What did you do in the next two weeks?
Probe: What did you observe on calls or tickets before you spoke with them?
Strong answer contains:
- Specific quality metric and the size of the drop
- Observed sample of calls or tickets before the talk
- A written plan with a checkpoint date
Weak answer contains:
- Talked to the person without looking at their work
- Blames the person's attitude for the scores
- No plan and no checkpoint
Score 1: No example, or no action by the candidate.
Score 2: Candidate talked to the agent, with no plan or checkpoint.
Score 3: Plan and checkpoint set, with the score result reported.
Score 4: As 3, plus a coaching habit applied to the rest of the team.

**C3-Q2** Tell me about a time you had to give feedback that the person did not want to hear. What happened next?
Probe: What did you say in the first minute?
Strong answer contains:
- The specific behavior named, with an example
- The expectation stated, with a date
- The person's response and the follow-up that happened
Weak answer contains:
- Feedback given as general personality comments
- Avoided the conversation until the problem grew
- No follow-up after the meeting
Score 1: No example, or the candidate avoided giving feedback.
Score 2: Feedback given, but no specific behavior or follow-up named.
Score 3: Specific feedback with an expectation and a follow-up date.
Score 4: As 3, plus the person's measured improvement afterward.

**C4-Q1** Tell me about an escalation you handed to engineering that came back unresolved. How did you manage it?
Probe: How often did you update the customer while you waited?
Strong answer contains:
- The escalation ticket content the candidate wrote
- Customer updates sent on a fixed schedule
- The next step agreed with engineering, with a date
Weak answer contains:
- Forwarded the ticket with no added detail
- Customer left without an update for days
- Blamed engineering in the account record
Score 1: No example, or the candidate handed off without follow-up.
Score 2: Candidate followed up, with no schedule or next step.
Score 3: Updates on a fixed schedule and a dated next step with engineering.
Score 4: As 3, plus a repeatable handoff template the team adopted.

**C4-Q2** Describe a time a customer threatened to cancel over a bug you could not fix. What did you do in the next hour?
Probe: Did you keep the follow-up you promised?
Strong answer contains:
- Acknowledged the bug and the customer's loss
- A specific workaround or credit offered within policy
- A follow-up time the candidate kept
Weak answer contains:
- Promised a fix date the team could not meet
- Offered a credit beyond policy limits without approval
- No follow-up after the first call
Score 1: No example, or the candidate made no offer or follow-up.
Score 2: Offer made, but the promised follow-up is not described.
Score 3: Offer within policy, and the promised follow-up was kept.
Score 4: As 3, plus a policy change so the next case moves faster.

**C5-Q1** Describe a weekly report that leadership stopped reading. What did you change about it?
Probe: Which numbers did you keep in the report?
Strong answer contains:
- Asked the readers what decisions they need from it
- A short list of metrics tied to those decisions
- Read-rate or reply change after the new format
Weak answer contains:
- Added more charts without asking readers
- Kept every metric the old report had
- No evidence the readers changed their habits
Score 1: No example, or the candidate did not change the report.
Score 2: Report changed, with no reader input named.
Score 3: Readers consulted and the metric list cut to a short set.
Score 4: As 3, plus evidence that leadership used the report afterward.

**C5-Q2** Tell me about a metric that looked good but hid a real problem. How did you find out?
Probe: What did you change in the report?
Strong answer contains:
- The metric's definition and why it misled
- The second data cut that revealed the problem
- Director told, with date and the change made
Weak answer contains:
- Metric defended after the problem surfaced
- Problem found by a customer complaint only
- No change to the report or definition
Score 1: No example, or the candidate defended the misleading metric.
Score 2: Problem found, but the report or director is not updated.
Score 3: Problem found from a second data cut, and director told with a date.
Score 4: As 3, plus a metric definition changed and documented.

## Removed items

| Removed item | Topic | Replacement |
|--------------|-------|-------------|
| None | n/a | n/a |

## Scoring

Each question scores 1 to 4, each competency maximum is 8, and the bank maximum is 40 for five competencies.
```

## Limits

The counts (four or five competencies, two questions each, four anchors) and the word limits are working values chosen for this skill. They are not a published standard. The skill screens against its own topic table; it does not check the law of any jurisdiction, so an employer should still have a lawyer review sensitive roles. Anchors describe answer content and never personality. The skill cannot tell whether a question actually predicts job performance. The example covers one customer-support role only, and it shows no removed items, so the replacement path is not demonstrated here. Long intake lists are not merged: an intake with more than five outcomes still produces five competencies.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
