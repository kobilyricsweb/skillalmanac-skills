# JSON Schema from samples

## One line

Infers a draft JSON Schema from one or more example JSON files, using a
standard-library Python script that marks a property as required only when
every sample contains it.

## What it does

The skill runs one script, `scripts/infer_schema.py`, over the sample files
you name. The script reads each file without changing it, merges every value
it finds at each position in the document, and prints a schema built from
2020-12 keywords: `type`, `format`, `properties`, `required`, and `items`.

Three decisions are the point of the tool. A key is required only if it
appears in every object instance at that position, so a key missing from one
sample becomes optional. Types are merged: an integer and a float at the same
position give `number`, and a null alongside another type gives a type list
with `null`. A string format such as `date-time` or `email` is kept only when
every string at that position matches it. Where two non-null types disagree,
the script still writes the schema, lists each conflict on stderr, and exits 1.

Output goes to stdout, or to a new file given with `-o`. The script refuses
an output path that already exists or that is one of the input paths.

## When to use

- You have a few example API payloads or config files and need a first draft
  schema to edit by hand.
- A payload has changed and you want to see which fields became optional or
  gained a second type across the saved samples.
- You want a quick check of whether a set of samples agree on types before
  writing validation code.

## When not to use

- To check data against an existing schema. The script infers only.
- For OpenAPI documents, XML schemas, or schemas written from a spec or prose.
- With samples you have not been allowed to share, if the schema itself would
  reveal their content to someone else.

## Requirements

- Python 3.9 or newer, standard library only. No packages, no network access.
- Run with `python -I` from the skill folder, so no local module can shadow the standard library.
- Inputs up to 2 MB per file, up to 100 files, nesting up to 32 levels.

## Example

Smoke run on the two fixtures in this package (verbatim stdout, exit 0):

```
{
  "type": "object",
  "properties": {
    "contact": {
      "type": "string",
      "format": "email"
    },
    "created": {
      "type": "string",
      "format": "date-time"
    },
    "id": {
      "type": "integer"
    },
    "name": {
      "type": "string"
    },
    "nickname": {
      "type": "string"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "required": [
    "contact",
    "created",
    "id",
    "name",
    "tags"
  ]
}
```

`nickname` is absent from `required` because `sample_b.json` does not contain it.

## Limits

- Inference sees only the samples given. A field that never appears in them is
  invisible, and a rare optional field can be missed.
- The script does not emit `additionalProperties`, `enum`, numeric bounds, or
  length limits, so the output is a starting point that needs editing.
- Format hints are shape checks only. `date` does not reject 2024-13-45, and
  `email` accepts many strings that are not valid addresses.
- Thresholds such as the 2 MB size cap, the 32-level depth cap, and the 40-digit
  integer cap are working values chosen for this script, not published standards.
- The script writes no `$schema` keyword. Validators will apply their own default dialect.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
