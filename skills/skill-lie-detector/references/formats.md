# File formats

All files live in one working folder, `lie-detector/` by default.

## tasks.json

```json
{
  "skill": "path/to/skill-folder",
  "reps": 2,
  "tasks": [
    {
      "id": "t1-invoice-total",
      "prompt": "Full task text exactly as both arms receive it.",
      "files": ["optional/input/file.csv"],
      "checks": [
        "The total stated in the answer is 1,240.00",
        "Names the duplicated line (line 14)",
        "Does not invent a tax rate that is not in the file"
      ]
    }
  ]
}
```

- `id`: letters, digits and dashes only. It becomes a folder name.
- `checks`: 3 to 5 strings, each decidable from the output alone.
- `void` (optional): `true` when a check turned out to be broken after the runs. verdict.py leaves the task out and lists it under `void_tasks`. Do not edit the checks instead.
- `reps`: a record for the report. The scripts count the files that exist.

## runs/

`runs/<task_id>/with_1.md`, `with_2.md`, `without_1.md`, `without_2.md`, and so on. One final answer per file.

## key.json (written by blind.py; do not open before verdict.py)

```json
{"t1-invoice-total": {"k3f9a2": "with", "q81c0d": "without"}}
```

## grades.json (written from the grader answers)

```json
[
  {"task": "t1-invoice-total", "id": "k3f9a2",
   "checks": [
     {"pass": true, "quote": "Total: 1,240.00"},
     {"pass": false, "quote": ""},
     {"pass": true, "quote": "No tax was applied"}
   ]}
]
```

The `checks` list must have one entry per check in tasks.json, in the same order. `pass` must be `true` or `false` (verdict.py stops on anything else). A pass is counted as failed when its quote is empty, has a fragment under 4 characters or under 6 characters in all, or is not found in the blinded output (case, spacing and markdown marks are ignored; use "..." to skip text between fragments).
