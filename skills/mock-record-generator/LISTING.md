# Mock Record Generator

## One line

Generates seeded mock records as CSV or JSON from a JSON field list or a small TypeScript interface, with a refusal to overwrite existing files.

## What it does

The script reads one spec file and writes one new output file. A `.json` spec is a field list with typed entries: integers and floats within a range, booleans, dates within a span, enum strings, UUID-shaped identifiers, person names, example.com email addresses, and short sentences. A `.ts` spec is a single interface written on one header line, with `string`, `number`, `boolean`, optional `?` markers, and string literal unions. Every run is driven by a seed, so the same spec, row count, and seed reproduce the same file. Fields the script cannot read are skipped and listed in a JSON report on stdout, and the exit code then reports the partial result.

## When to use

Use it when a test fixture, seed script, or UI prototype needs a few hundred rows of plausible shape and the team would otherwise type them by hand. It fits when reruns must match, because a failing test can be traced to a fixed file. The output format is chosen at the command line, so the same spec can feed a CSV loader or a JSON API stub.

## When not to use

Do not use it for production or real customer data, for real email addresses, for load testing beyond 10000 rows, or for inserting rows into a live database. The generator does not model relations between records, so it is the wrong tool for foreign keys or for data that must satisfy business rules across fields.

## Requirements

Python 3.9 or newer, standard library only. No network access, no packages to install, and no write access beyond the single output path. The spec must be UTF-8 and at most 2 MB.

## Example

Run from a workspace folder, with the skill folder shown as `<skill-folder>`:

```
python -I <skill-folder>/scripts/mock_data.py <skill-folder>/fixtures/spec_fields.json --count 5 --seed 7 --format csv --out example.csv
```

Stdout (exit 0):

```
{"status": "ok", "rows": 5, "format": "csv", "out": "example.csv", "fields": ["id", "full_name", "email", "age", "score", "plan"], "unsupported": []}
```

Contents of `example.csv`:

```
id,full_name,email,age,score,plan
5226a612-895d-4e81-896f-11176cd31f39,Hiro Lopez,grace.evans978@example.com,20,0.86,free
241e4ed0-2e94-435f-8c10-0f34ae6d5095,Farid Dubois,jomo.ito319@example.com,45,0.53,team
ba49fa1e-6bc1-467d-8aab-c392e050b198,Grace Fischer,kai.lopez526@example.com,49,0.06,team
a5fed248-62ab-4576-ab1d-0fc4213f64df,Ada Fischer,grace.khan837@example.com,59,0.28,pro
5be2f526-2d3b-4b7c-9643-016b5e90f3b0,Grace Haddad,ines.alvarez909@example.com,55,0.87,team
```

A partial run with the unsupported-fields fixture (exit 1) prints this report and still writes the file:

```
{"status": "partial", "rows": 2, "format": "csv", "out": "example_partial.csv", "fields": ["orderId"], "unsupported": [{"field": "tags", "line": 4, "type": "string[]", "reason": "unsupported_type"}, {"field": "shipping", "line": 5, "type": "{", "reason": "unsupported_type"}]}
```

## Limits

The script does not check that generated values are realistic, unique, or consistent with each other. Email addresses can repeat across rows, names are drawn from short fixed lists, and text is random word combinations. It does not verify that a generated file loads into a particular database, parser, or UI, and it does not check the output against the spec beyond its own generation rules. Identifiers are random, not guaranteed unique. TypeScript support covers only the forms in the skill table; generics, extends clauses, arrays, nested objects, and methods are skipped and reported. Dates accept only ISO YYYY-MM-DD. The script does not verify security properties of the output file or any downstream system.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
