# Scheduling rules used by critical_path.py

## Offsets and dates

- Time is counted in whole working units from 0. A task with earliest start `es` and duration `d` occupies units `es` to `es + d - 1`; `ef` is `es + d` (the first unit after it).
- With unit `days` and a start date, unit n is the nth working day on or after the start date. `start_date` of a task is the date of unit `es`; `finish_date` is the date of unit `ef - 1`, the last day worked.
- A milestone (duration 0) gets the date of unit `es`: it is reached at the start of the first working day after its predecessors finish. Its `start_date` and `finish_date` are equal.
- `project_duration` is the largest `ef`. The project `finish_date` is the last day worked, not the day after.
- `deadline_days` for a date deadline is the count of working days from the start date through the deadline date inclusive. `deadline_gap` is `deadline_days - project_duration`: positive is spare, negative is late.

## Slack

- Total slack = `ls - es` on the plan's own length. It is shared by all tasks on the path.
- Free slack = (smallest `es` among successors, or the project length) minus `ef`.
- `deadline_slack` = total slack + `deadline_gap`, so it shows the true margin against the deadline.
- A critical path is a chain of zero-slack tasks in which each link is tight (`ef` of one equals `es` of the next). Ties give several paths; the script lists up to 50.

## Worked example (the kitchen fixture)

Eight tasks, 14 working days from Monday 2026-03-02. Cabinets (10 days, no predecessor) then Install (3) then Final clean (1) is the only zero-slack chain, finishing on 2026-03-19. Plaster has 1 day of slack even though it sits on a long chain, because the cabinet order, not the building work, sets the pace. The deadline of 2026-03-27 is 20 working days out, so 6 spare. One owner is on two tasks on days 2 to 3 and on day 9, which the overload list reports.

## Sources (facts restated in my own words)

- https://en.wikipedia.org/wiki/Critical_path_method : forward and backward pass, float, critical activities.
- https://en.wikipedia.org/wiki/Float_(project_management) : total float against free float; float is shared along a path.
- https://en.wikipedia.org/wiki/Brooks%27s_law : adding people to a late software project tends to delay it; basis of the caution in the compression table.
- https://en.wikipedia.org/wiki/Critical_chain_project_management : buffer placed at the end of a chain instead of inside each task.
