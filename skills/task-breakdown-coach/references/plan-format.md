## Contents

- JSON format
- Markdown format
- Finding codes

## JSON format

```json
{
  "goal": "File the annual tax return",
  "first_action": "Open the tax folder on the desk",
  "first_action_minutes": 5,
  "limits": {"max_step_minutes": 45, "daily_capacity_minutes": 180},
  "next_action": "s1",
  "steps": [
    {"id": "s1", "title": "List the missing tax forms from last year's checklist",
     "minutes": 20, "energy": "low", "context": "desk", "day": "mon", "done": false}
  ]
}
```

`limits` is optional: `max_step_minutes` defaults to 45; without `daily_capacity_minutes` the overbooking check is skipped and a warning says so. `id` defaults to `s<position>`. `done` steps do not count towards a day's load. The file name must end in `.json`.

## Markdown format

Any other file name is read as Markdown. Header lines may appear anywhere; step lines are checklist items with fields separated by `|`.

```
Goal: Get the garage ready for winter
First action: Carry the two bike helmets to the kitchen table | 5m
Capacity: 90
Max step: 45
Next action: g1

- [ ] Clear the shelf by the door and stack the boxes | 30m | energy:medium | context:garage | day:sat | id:g1
- [x] Photograph the shelf before and after | 15m | energy:low | context:garage | day:fri | id:g3
```

The first field is the title; `30m`, `30 min` or `30 minutes` sets minutes; `energy:`, `context:`, `day:` and `id:` may come in any order. `[x]` marks a done step.

## Finding codes

Errors make `ok` false and the exit code 1.

| Code | Meaning |
|---|---|
| missing_first_action | No first action text |
| first_action_not_concrete | First action has no filmable verb plus object |
| first_action_too_long | `first_action_minutes` over 10 |
| no_steps | Empty step list |
| step_over_limit | Step minutes above the limit (default 45) |
| step_not_concrete | Title starts with a vague verb or phrase, or has no object |
| missing_minutes | No positive minutes on a step |
| missing_energy, bad_energy | Energy absent, or not low, medium or high |
| missing_context | No context tag |
| day_overbooked | Open steps on one day sum above stated capacity |
| duplicate_id | Same step id twice |
| bad_next_action | `next_action` matches no step, or the step is done |

Warnings do not change the exit code.

| Code | Meaning |
|---|---|
| first_action_minutes_missing | First action has no minutes, so the 10-minute rule is unchecked |
| step_under_min | Step under 15 minutes |
| verb_not_recognized | Leading verb not on the known concrete list: confirm by eye |
| day_tight | Day above 80% of capacity |
| day_too_many_steps | More than 3 open steps on one day |
| capacity_missing | Days assigned but no capacity stated |
| too_many_steps | More than 12 steps |
| no_next_action | No `next_action` set |
