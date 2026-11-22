# Floor plan clearance check

## One line

Checks a furniture layout in one rectangular room against working-value walkway, door-swing and overlap rules, and reports each violation with its distance in inches.

## What it does

You describe one rectangular room in inches: its width and length, the position and size of each piece of furniture, and each door's wall, offset and width. The bundled script, scripts/clearance.py, reads that JSON file and reports six kinds of problem: pieces outside the room, pieces that overlap, pieces inside a door's swing zone, pieces that enter the 36 inch corridor in front of a door, gaps under 36 inches between facing pieces when the gap sits inside that corridor, and gaps under 24 inches everywhere else. Each finding names the codes, the items involved, the door number, the measured distance and the required value.

The script writes one JSON object to standard output. Errors go to standard error and exit with code 2. The skill turns the findings into a table and proposes one move per finding, sized from the measured distance, so the user can see which piece to shift and by how many inches.

The check is a geometry check on the layout as entered. It does not know what the furniture looks like, so legs, cushions and cabinet doors are not modeled.

## When to use

- A user has measured a room and listed the furniture, and wants to know whether a sofa, bed or desk blocks a door.
- A user wants to confirm that a walkway between two pieces is at least 24 inches, or at least 36 inches where it leads from a door.
- A layout review needs a repeatable list of overlaps and tight gaps before a person walks the room.

## When not to use

- Questions about building codes, fire egress or accessibility standards. The output states that it is not a code check, and the skill refuses to decide compliance.
- Rooms with curved or irregular walls, doors on a diagonal, or rooms that are not rectangles.
- Generating a floor plan from a prompt or a photo.

## Requirements

Python 3.9 or later, standard library only. No network access and no installed packages. The input file must be UTF-8 JSON of at most 2 MB, with at most 300 items and 20 doors. Dimensions are in inches.

## Example

Command, run on the smoke fixture that ships with the skill (a 144 by 120 inch room, a sofa over a north door, an overlapping coffee table and an armchair):

```
python -I scripts/clearance.py fixtures/smoke_room.json
```

Output, verbatim from the run, exit code 1:

```
{
  "scope": "working-value layout check, not a building-code check",
  "status": "findings",
  "room": {
    "width": 144.0,
    "length": 120.0
  },
  "violation_count": 5,
  "violations": [
    {
      "code": "overlap",
      "items": [
        "sofa",
        "coffee_table"
      ],
      "door": null,
      "distance_in": 0.0,
      "required_in": 0.0,
      "depth_in": 6.0,
      "message": "sofa and coffee_table overlap by 6.0 in"
    },
    {
      "code": "door_swing_blocked",
      "items": [
        "sofa"
      ],
      "door": 1,
      "distance_in": 0.0,
      "required_in": 0.0,
      "depth_in": 22.0,
      "message": "sofa sits in the swing zone of door 1"
    },
    {
      "code": "main_path_blocked",
      "items": [
        "sofa"
      ],
      "door": 1,
      "distance_in": 0.0,
      "required_in": 36.0,
      "depth_in": 24.0,
      "message": "sofa intrudes 24.0 in into the main path of door 1"
    },
    {
      "code": "secondary_gap_narrow",
      "items": [
        "sofa",
        "armchair"
      ],
      "door": null,
      "distance_in": 14.0,
      "required_in": 24.0,
      "depth_in": null,
      "message": "sofa and armchair leave 14.0 in between them (24 in needed)"
    },
    {
      "code": "secondary_gap_narrow",
      "items": [
        "coffee_table",
        "armchair"
      ],
      "door": null,
      "distance_in": 4.0,
      "required_in": 24.0,
      "depth_in": null,
      "message": "coffee_table and armchair leave 4.0 in between them (24 in needed)"
    }
  ]
}
```

Reading the output: the sofa overlaps the swing zone of the north door by 22 inches, so the door cannot open freely. The coffee table overlaps the sofa by 6 inches. The 14 inch gap between the sofa and the armchair and the 4 inch gap between the table and the armchair are both under the 24 inch secondary minimum.

## Limits

- The 36 inch main-path corridor and the 24 inch secondary gap are working values set by this skill. They are not published specifications.
- Every item is an axis-aligned rectangle. The script does not see shapes, legs, cushions or the clearance under a bed frame.
- Gaps are measured only between two items that overlap in one axis and face each other across the other axis. Diagonal pairs and item-to-wall distances are not reported.
- The door swing zone is modeled as the opening span by a depth equal to the door width. Real swing arcs and hardware are not modeled.
- Units are inches only. Metric figures need a user-confirmed conversion first.
- Each violation is a single pair or single item. The script does not rank fixes, and moves suggested by the skill are not rechecked unless the user reruns the script.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
