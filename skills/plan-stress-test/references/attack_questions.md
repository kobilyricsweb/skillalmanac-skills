# Attack questions by pass

## Contents
- Pass 1: Goal and done criteria
- Pass 2: Hidden assumptions
- Pass 3: Dependencies and sequence
- Pass 4: Ownership and single points of failure
- Pass 5: Schedule realism
- Pass 6: Failure and reversal
- Pre-mortem prompts
- Wording a finding

Read only the section for the pass you are on. A question that does not apply to this plan is skipped, not answered with "n/a" in the register.

## Pass 1: Goal and done criteria

- Is there a sentence a stranger could check on the last day with yes or no? "Improve onboarding" cannot be checked; "median time to first report under 10 minutes for new accounts" can.
- Is the goal a result or an activity? "Roll out the new tool" is an activity; the result is what people can do afterwards.
- Does every step end in something observable (a record, a test result, a sign-off by a named role)? A step whose only end is "completed" cannot be seen failing.
- Who decides "done" for the whole plan, and is that the same person who benefits from calling it done?
- Do the goal and the steps agree? Look for a goal about quality with steps only about delivery, or a goal with a date earlier than the last step.
- Is a number in the goal supported by a baseline? A target such as "reduce churn by 20%" with no current value cannot be scored.

## Pass 2: Hidden assumptions

An assumption is a fact the plan needs and does not state. Find them by asking, of each step: what has to already be true for this to start, and for this to work?

Classes that hide most often:
- Access: accounts, licences, admin rights, VPN, physical entry, API quotas.
- Capacity: the same people are free in the same weeks; test, staging or build capacity exists; a vendor can take the volume.
- Data: the data is complete, clean, in the expected format and legally movable.
- Behaviour of users: people will read the notice, attend the training, switch on their own.
- Approvals: someone with authority will say yes, within the time shown, without conditions.
- Environment: no freeze periods, outages, audits, peak seasons or leave overlaps in the window.
- Stability of the target: the requirement, price, regulation or partner does not change while the plan runs.
- Reversibility: copies, snapshots or old systems stay available as long as the plan assumes.

For each assumption you record, name the first step that breaks if it is false and how that would be noticed. An assumption with no early warning sign is worth a higher likelihood score.

## Pass 3: Dependencies and sequence

- For every dependency the scan reports as undefined: is it a missing step (someone must do it), an external party (someone outside must do it, needs a date and a named contact) or just wording? Only the first two are risks.
- Draw the order from the dates: does any step start before something it needs is finished? The scan reports dated cases; look for undated ones too.
- Find the longest chain of waits. If one link slips a week, which later dates move? A plan with no slack on its longest chain has its whole deadline on that link.
- Circular waits: A waits for B's approval and B waits for A's output. The scan reports cycles that use step ids; look for cycles through people or teams.
- External parties: vendor, regulator, customer, another team. Is the date they control written down, and who has confirmed it?
- Shared resources: two steps that both need the same environment, person or maintenance window on the same days.
- Inputs from earlier work that nobody verifies on arrival ("the design is final").

## Pass 4: Ownership and single points of failure

- One accountable name per step. Two names, a team or a department means each can assume the other acts.
- Count what each person owns. If one person is on a large share of open steps, ask what happens when they are ill or unreachable for a week. The scan reports the share.
- Names are not the only single points. Check for: one account or credential, one vendor with no alternative, one approver, one machine or environment, one person who holds undocumented knowledge, one calendar slot (a window that cannot be moved).
- For each single point, is there a named backup and has the backup done the task before?
- Owner versus time: is the owner also on leave, on another plan or at another deadline in the same weeks? Only say so when the plan text shows it.
- Handoffs: where responsibility moves from one owner to another, who checks that the handoff was understood?

## Pass 5: Schedule realism

- Do durations include waiting (reviews, approvals, procurement, lead times), or only effort?
- Is there any buffer before the fixed date, and is it at the end where everything has already been spent, or in front of the risky step?
- Do many steps share the same due date or sit in the final week? Bunching means a slip in any one is a slip in the plan.
- Is first-time work estimated like repeated work? A step done for the first time, or with a new tool or vendor, takes longer and fails more.
- Does the plan rehearse the riskiest step (a trial import, a dry run, a pilot) early enough to change the plan if the rehearsal fails?
- Are tasks that must be sequential shown as parallel to hit the date?
- Do the plan's own numbers fit: steps that add up to more days than the calendar allows between two dates.

Only judge dates the plan states. Do not add holiday or weekend claims you cannot see in the text.

## Pass 6: Failure and reversal

- Detection: for each irreversible or expensive step, what signal says it went wrong, who watches it, and how soon?
- Point of no return: name the step after which the old way no longer works. Is everything that must be verified done before it, not after?
- Rollback: written, owned, rehearsed, with a trigger (a threshold or a time limit) so that nobody has to decide under pressure whether to use it?
- Partial failure: what if half of something completes? Is the half-done state safe, and who cleans it?
- Communication: who tells affected people, and does that step exist in the plan?
- Cost of the way back: a rollback that loses the data written since the switch is a different risk than one that does not.
- Stop rule: what evidence would make the owner stop the plan instead of pushing on?

## Pre-mortem prompts

Use after the passes, in this order, one line each: (1) it failed because of a person or approval; (2) it failed because of something outside the team; (3) it failed because an early step looked done and was not. Compare with your list; add only what is new.

## Wording a finding

- Scenario: say what happens, to whom, and what it costs, in the plan's own vocabulary. "Step A5 has no owner" is the evidence; "the night of the switch nobody is accountable and a failed switch waits for a volunteer" is the scenario.
- Mitigation: the smallest change to the plan text that would contain the risk (add a step, name an owner, add a trigger), not a new programme.
- Detection: something observable before the damage, with a time or a place to look.
- Avoid words that cannot be checked later: "ensure", "monitor closely", "align", "as needed".
