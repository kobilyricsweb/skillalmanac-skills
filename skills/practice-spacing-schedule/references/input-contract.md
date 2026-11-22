Required fields:
- Complete item list with stable item IDs.
- Skill tag for each item.
- Prerequisite order or explicit statement that none exists.
- Number of sessions and capacity per session.
- Review obligation for each item or item class: how many reviews are mandatory and their timing, or an explicit statement that no review is required.
- Allowed review intervals, including whether intervals count sessions or elapsed time.

Optional fields may define mixing preferences or fixed placements. If an item, prerequisite, capacity, review obligation, or interval is missing, identify the gap and schedule only what can be checked. Do not infer a mandatory review merely because an interval is permitted. Defer affected non-fixed introductions when their constraints cannot be checked. If constraints conflict, report the conflict and show deferred or unplaced items rather than silently relaxing a rule.

Output fields:
- Session schedule with activity type and reasons.
- New, review, mixed, and deferred labels.
- Unused-capacity report.
- Constraint audit and assumptions.

The result is a feasible or partial proposal, not an optimality claim or a prediction of learning outcomes.
