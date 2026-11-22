---
name: llm-json-output-validator
description: Validates LLM replies against a JSON Schema subset and tallies failures by class and field. Use when model output breaks json.loads, or for a structured-output failure rate, a repair policy (fences, leading prose, trailing commas, single quotes) or a retry message. Stdlib script with a logged repair ladder and a one-retry contract. Do not use for building eval test sets, writing the prompt, designing tool schemas, or calling a model.
license: Apache-2.0
compatibility: The script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, follow the manual fallback at the end of the workflow.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# LLM JSON output validator

Measure how often real model replies survive a strict parser and a schema, name the failure classes, and set a repair policy that is written down instead of improvised in code. The script never calls a model.

## Inputs

1. Outputs: a JSONL file (one record per line) or a folder of `.txt .json .md .out` files (one record per file). A JSONL line may be a JSON string holding the reply, an object with the reply under `--field` (default `output`), or the raw reply on one line.
2. Expected shape: `--schema schema.json` (supported subset below) or `--example example.json` (a schema is inferred: every key required, no extra keys, array items typed from the first element; ranges and enums need a schema file).
3. At least 50 records; 200 or more is better. The report prints a 95% Wilson interval (`rate_ci95`); with 16 records a 3/16 rate is only known to lie between 6.6% and 43%.

Real model replies may hold user data. Keep them local; do not paste them into issues or prompts.

## Supported schema subset

`type` (one name or a list), `properties`, `required`, `additionalProperties` (true or false only), `enum`, `const`, `minimum`, `maximum`, `items` (one schema), `minItems`, `maxItems`, `minLength`, `maxLength`, `pattern` (searched, not anchored, as the standard says). Annotation keys (`title`, `description`, `default`, `examples`, `$schema`, `$id`, `$comment`) are skipped.

Anything else (`format`, `oneOf`, `anyOf`, `$ref`, `exclusiveMinimum`, `multipleOf`, `uniqueItems`, tuple `items`, schema-valued `additionalProperties`) is listed under `unsupported_keywords` and the run is refused with exit 2. `--allow-unsupported` validates the rest and keeps the list in the report. Never read a passing run as proof for a keyword on that list.

## Repair ladder

Rungs run cheapest first. Every record's log row names the rungs that changed its text. Default is `fence,prose`.

| Rung | Fixes | Default | Risk |
|---|---|---|---|
| fence | reply wrapped in a triple-backtick block, closed or cut off | on | none: text is unchanged inside |
| prose | text before or after the value ("Here is the JSON:") | on | medium: takes the first parseable value; a `second_json_candidate_after_first` note is logged |
| trailing_commas | `[1, 2,]`, `{"a": 1,}` | off | low |
| comments | `// ...` and `/* ... */` outside strings | off | low |
| python_literals | `True False None` outside strings | off | low |
| single_quotes | `{'a': 'b'}` | off | higher: apostrophes and double quotes inside are re-escaped, but check a sample |

Never repaired, always a failure: `truncated` (closing the brackets would invent data), `empty_output`, `no_json_found`, NaN/Infinity, duplicate keys, and every schema violation. Repair changes syntax; it never changes a value. Coercing `"4"` to `4` is a code decision, made only for fields documented as lenient.

Enable a rung with `--allow fence,prose,trailing_commas`, `--allow all`, or `--allow none` for pure strict parsing. A failed record whose text a disallowed rung would have rescued says so (`would parse with rung: ...`), which tells you what the policy would buy.

## Workflow

```
- [ ] 1 Check inputs and schema subset
- [ ] 2 Run with the default ladder
- [ ] 3 Read the report in fixed order
- [ ] 4 Pick the remedy per class
- [ ] 5 Set the repair policy
- [ ] 6 Fix, re-run on the same records
- [ ] 7 Report
```

1. Confirm the record count and that the schema uses only the subset. Rewrite the schema if it lists unsupported keywords.
2. Run `python scripts/validate_outputs.py --schema S --input O --report report.json --log log.jsonl --retry-out retries.jsonl`. Output paths that resolve to any input are refused even with `--force`; an existing file needs `--force`. Run `--allow none` as well to get the strict baseline.
3. Read in this order: `n`, `rate` with `rate_ci95`, `clean_valid` against `valid_after_repair`, `repairs_applied`, `failures_by_class`, `failures_by_field`, `notes`, then `examples`. A class count is records affected, not violations; a record with two missing fields counts once under `missing_field` and twice under two fields.
4. Choose the remedy per class from [references/failure_classes.md](references/failure_classes.md) (15 classes, each with cause, remedy and what not to do; it also lists the standards the rules follow). Read only the rows for classes in the report.
5. Set the policy from the strict clean rate (working values, not measured optima):

| Strict clean rate (`--allow none`) | Policy |
|---|---|
| 99% or more | Strict parse only. No repair code in production |
| 95% to under 99% | Allow `fence,prose`; one retry; log repairs |
| 80% to under 95% | Fix the prompt first (schema in the prompt, one valid example, "JSON only"), re-run, then decide. Do not add syntax rungs to hide a prompt problem |
| under 80% | Prompt, model or decoding mode is wrong. Use the provider's structured-output or constrained-decoding mode if one exists; repairs will not save it |

   If one class holds 50% or more of the failing records, fix that class alone and change one thing per run, so the next report shows its effect. Syntax rungs are justified only when the report shows that exact class repeating (for example `invalid_syntax` with the same `would parse with rung` hint on 5 or more records).
6. For retries follow [references/retry_contract.md](references/retry_contract.md): at most one retry per record, built from `retries.jsonl` (the script writes the message), logged with the first failure classes. Retry load is about `n x (1 - rate)` extra calls; if more than 1% still fail after the retry, route them to a dead-letter queue and treat it as an incident.
7. Re-run on the same records after a prompt change and compare `rate` and the Wilson intervals. If the intervals overlap, say the change is not shown to help; do not claim an improvement.

Report in this shape:

```
Records: <n>, strict clean <x%> (CI <lo>-<hi>), with ladder <y%>
Top failure classes: <class: records, field>
Policy: <rungs allowed, retry count, dead-letter rule>
Unsupported schema keywords: <none or list>
Not checked: <what the schema cannot express, sample bias, other models>
```

Manual fallback without Python: take 20 replies, parse each with the language's strict parser, and tally by hand using the class table; apply the same policy table, and note that the rate is a rough one.

## Report contract

Stdout is one strict JSON object: `tool`, `version`, `schema_source`, `allowed_repairs`, `n`, `valid`, `rate`, `rate_ci95`, `clean_valid`, `valid_after_repair`, `repairs_applied`, `failures_by_class`, `failures_by_field` (array indices shown as `[]`), `notes`, `blank_lines_skipped`, `unsupported_keywords`, `examples[]` (`record`, `class`, `field`, `message`, `excerpt`; one per class and field pair, up to `--max-examples`). `valid` counts records with no failure after the allowed rungs. Exit 0 all valid, 1 some invalid, 2 usage or schema problem.

## Scripts

`scripts/validate_outputs.py`: run it; do not edit it to make a check pass. Reads the schema and outputs; writes only `--report`, `--log` and `--retry-out`.

## Limits

- The schema subset is small on purpose. Cross-field rules, formats, unions and references need your own code after this check.
- `prose` takes the first value that parses, so a citation like `[1]` before the real object is taken as the answer; the schema then flags a wrong type, and a `second_json_candidate_after_first` note appears when more JSON follows.
- A valid reply can still be wrong. This checks shape, not truth.
- Thresholds are working values. Replies from one model and one prompt do not predict another.
- Float 3.0 counts as an integer, as the standard allows. Numbers are not range-checked beyond `minimum` and `maximum`.
