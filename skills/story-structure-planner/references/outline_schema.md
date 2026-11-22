## Contents

- Top level
- Character
- Scene
- Defect codes
- Date and id rules

# Outline schema and defect codes

Strict JSON: no comments, no trailing commas, no duplicate keys, no NaN. Unknown fields are `SCHEMA` errors, so a misspelt key is caught instead of ignored. Scenes appear in narrative order.

## Top level

| Field | Type | Required | Notes |
|---|---|---|---|
| title | string | no | |
| structure | string | yes | `three-act`, `save-the-cat`, `heros-journey`, `seven-point` |
| word_target | integer > 0 | yes | planned length of the finished text |
| tense | string | yes | `past`, `present`, `future`: the narrative default |
| person | string | no | `first`, `second`, `third`; enables person-drift checks |
| pov_mode | string | no | `single`, `multiple` (default), `omniscient` (skips POV checks) |
| characters | list | yes | see below |
| scenes | list | yes | non-empty |
| setups | list of {id, ...} | no | declared setups; each must be planted in a scene |

## Character

| Field | Type | Notes |
|---|---|---|
| id | string | required, unique; used in `pov`, `characters`, arcs |
| name | string | free text |
| role | string | required: `protagonist`, `antagonist`, `ally`, `mentor`, `love_interest`, `minor`. All but `minor` are major |
| introduced_in | scene id | appearing earlier than this scene is `CHAR_BEFORE_INTRO` |
| exit_scene | scene id | declares the last scene; silences `CHAR_VANISHES` |
| dies_on | date | later non-flashback appearances are `CHAR_AFTER_DEATH` |
| arc | object | `want`, `need`, `turning_points` (scene ids), `end_state` |

## Scene

| Field | Type | Notes |
|---|---|---|
| id | string | required, unique |
| beat | string | required; a beat name of the chosen structure |
| chapter | number or string | a change from the previous scene counts as a marked POV change |
| pov | string | character id; required unless `pov_mode` is `omniscient` |
| tense, person | string | override the defaults for this scene |
| goal, conflict, outcome | string | required in substance; empty, `none`, `tbd`, `n/a`, `-` count as missing |
| outcome_type | string | `yes`, `no`, `yes-but`, `no-and` |
| change | {from, to} | what value moves; equal texts mean no change |
| stakes_change | boolean | true when a stake is raised, lowered or revealed |
| date | string | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM`, no time zone |
| location | string | free text |
| characters | list of ids | who is present besides the POV character |
| words | integer > 0 | planned words; if every scene has it, budgets use real weights |
| requires | list of scene ids | scenes that must have happened first |
| plants, pays_off | list of ids | setup ids planted or paid off here |
| flashback | boolean | exempts the scene from date order, tense, intro and death checks |
| pov_marked, tense_marked | boolean | declares a deliberate switch |

## Defect codes

| Code | Severity | Meaning | Usual fix |
|---|---|---|---|
| SCHEMA | error | wrong type, unknown field, bad enum or date | fix the field |
| DUPLICATE_SCENE_ID | error | two scenes share an id | rename |
| MISSING_BEAT | error | no scene carries a beat of the template | add or reassign a scene |
| UNKNOWN_BEAT | warn | scene beat not in the template | use a template beat name |
| BEAT_ORDER | warn | beats start out of template order | reorder |
| BEAT_DRIFT | warn | beat starts over 10 points from its span | move the turn or rebalance |
| BEAT_BUDGET | warn | beat under 0.5 or over 1.5 times budget | add, trim or change target |
| TARGET_MISMATCH | warn | planned total differs from target by over 15 percent | rescale |
| NO_WORD_COUNTS | info | some scenes lack words | add planned words |
| MISSING_FIELD | error | goal, conflict, outcome or pov missing | fill it |
| NO_CHANGE | error | change missing or from equals to | find the shift or cut the scene |
| MIDDLE_NO_STAKE_CHANGE | warn | middle-third scene without stakes_change true | raise, lower or reveal a stake |
| RUN_OF_SUCCESS | warn | three plain yes outcomes in a row | add yes-but or no-and |
| POV_UNKNOWN | error | pov is not a character id | fix id |
| POV_DRIFT | error | unmarked viewpoint change | new chapter, marker or retell |
| TENSE_DRIFT, PERSON_DRIFT | error | scene differs from outline default, unmarked | rewrite or mark |
| TIMELINE_CONTRADICTION | error | scene dated before a scene it requires | fix dates |
| TIMELINE_BACKWARDS | warn | dated earlier than the previous scene | fix, reorder or flashback |
| REQUIRES_ORDER | warn | scene precedes a prerequisite in narrative order | reorder or flashback |
| REQUIRES_UNKNOWN | error | required id is not a scene | fix id |
| CHAR_UNKNOWN | error | scene lists an id not in characters | fix id |
| CHAR_AFTER_DEATH | error | appears after dies_on | change a date or the death |
| CHAR_BEFORE_INTRO | error | appears before introduced_in | move intro or cut the appearance |
| CHAR_INTRO_UNKNOWN, CHAR_EXIT_UNKNOWN | error | id is not a scene | fix id |
| CHAR_VANISHES | warn | major character last seen before 75 percent, no exit | bring back or set exit_scene |
| CHAR_NEVER_APPEARS | warn | major character in no scene | add scenes or cut |
| SETUP_NO_PAYOFF | warn | planted, never paid off | add payoff or cut the plant |
| PAYOFF_NO_SETUP | error | payoff with no plant | plant earlier |
| PAYOFF_BEFORE_SETUP | error | payoff at or before the plant | reorder |
| SETUP_NEVER_PLANTED | warn | declared in setups, planted nowhere | plant or delete |
| ARC_MISSING | error | protagonist has no arc | add arc |
| ARC_INCOMPLETE | warn | arc lacks want or need | state both |
| ARC_NO_TURNING_POINT | error | arc has an empty turning_points list | name the scenes |
| ARC_TURN_UNKNOWN | error | turning point is not a scene id | fix id |
| ARC_TURN_ABSENT | warn | character not present in own turning-point scene | add them or move it |
| ARC_FEW_TURNS | warn | protagonist has under 2 distinct turning points | add one near midpoint, one late |

## Date and id rules

Ids are compared exactly and case-sensitively. Dates are compared as local date-times; a date without a time is midnight. The previous-scene date comparison skips flashback scenes.
