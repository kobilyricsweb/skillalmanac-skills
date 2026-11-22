## Contents

- How spans work
- three-act
- save-the-cat
- heros-journey
- seven-point
- Sources

# Structure templates

Spans are percentages of the planned word total, as encoded in `scripts/check_outline.py`. The first scene of each beat is the turn the beat is named for; the rest of the span is its fallout. Budget words = target x (end minus start) / 100. Names are the exact strings used in the `beat` field.

## How spans work

A beat that starts more than 10 points away from its span start is reported as `BEAT_DRIFT`. A beat with under half or over one and a half times its budget is `BEAT_BUDGET`. These are planning checks; a deliberate cold open or a long denouement is a valid choice the author can keep after recording the reason.

## three-act

Acts run 25 / 50 / 25 percent: act one is hook plus inciting_incident, act two is first_plot_point plus midpoint, act three is second_plot_point, climax and resolution.

| Beat | Span % | What the first scene must do |
|---|---|---|
| hook | 0-10 | Show the protagonist in a normal that already has a flaw or pressure; promise the kind of story |
| inciting_incident | 10-25 | Something disrupts the normal and creates the problem the story will answer |
| first_plot_point | 25-50 | The protagonist commits; there is no easy way back to the opening situation |
| midpoint | 50-75 | A reveal or reversal changes what the protagonist believes the fight is about |
| second_plot_point | 75-90 | The worst loss or the last piece of information; the protagonist must change to continue |
| climax | 90-98 | The decisive confrontation, won or lost by the choice the arc has prepared |
| resolution | 98-100 | The new normal; show what the change cost and kept |

## save-the-cat

Eleven beats condensed from the fifteen-beat commercial-genre outline.

| Beat | Span % | Purpose |
|---|---|---|
| opening_image | 0-2 | Snapshot of the flawed starting state |
| setup | 2-10 | Introduce hero, world and what is missing |
| catalyst | 10-20 | The event that breaks the status quo, plus the hero's hesitation |
| break_into_two | 20-25 | The hero chooses to enter the new world |
| fun_and_games | 25-50 | The promise of the premise delivered |
| midpoint | 50-55 | False victory or false defeat; stakes rise |
| bad_guys_close_in | 55-75 | Pressure from outside and from the hero's flaw |
| all_is_lost | 75-80 | A loss that feels final |
| break_into_three | 80-85 | The hero finds the answer that combines lessons |
| finale | 85-98 | The plan is executed against the strongest opposition |
| final_image | 98-100 | Mirror of the opening showing the change |

## heros-journey

Twelve stages, useful for quest and coming-of-age plots.

| Beat | Span % |
|---|---|
| ordinary_world | 0-8 |
| call_to_adventure | 8-15 |
| refusal | 15-20 |
| meeting_mentor | 20-25 |
| crossing_threshold | 25-30 |
| tests_allies_enemies | 30-45 |
| approach | 45-50 |
| ordeal | 50-60 |
| reward | 60-70 |
| road_back | 70-80 |
| resurrection | 80-95 |
| return_with_elixir | 95-100 |

A stage may be a single scene or several; none may be missing. Skipping `refusal` is the commonest valid choice, in which case say so in the report.

## seven-point

Built backwards from the resolution, so write the end first.

| Beat | Span % | Purpose |
|---|---|---|
| hook | 0-25 | Starting state, the opposite of the end state |
| plot_turn_1 | 25-37 | The conflict arrives and the hero commits |
| pinch_1 | 37-50 | Pressure applied by the antagonist |
| midpoint | 50-62 | The hero moves from reaction to action |
| pinch_2 | 62-75 | The strongest pressure; allies lost or plan broken |
| plot_turn_2 | 75-88 | The last piece of information that lets the hero win |
| resolution | 88-100 | Ending state, the opposite of the start |

## Sources

These are public descriptions of the structures; the tables above are written for this skill and the span percentages are this skill's planning values.

- Three-act structure: https://en.wikipedia.org/wiki/Three-act_structure (checked by title only; page text not re-read during authoring)
- Hero's journey: https://en.wikipedia.org/wiki/Hero%27s_journey (same note)
- Save the Cat: the beat names come from Blake Snyder's book "Save the Cat!" (2005); the percentages here are condensed and rounded.
- Seven-point structure: popularised by Dan Wells in a talk of the same name; no URL checked.
