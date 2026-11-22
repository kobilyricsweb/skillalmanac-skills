# LLM JSON output validator

**Summary:** For developers whose program parses model replies as JSON: measures how many survive, names why the rest fail, and sets a logged repair and retry policy.

## What it does

The skill walks you through a batch check of real model replies. A standard-library Python script pulls one JSON value out of each reply (stripping a code fence or leading prose and recording that it did), parses it strictly, and validates it against a stated JSON Schema subset. It tallies failures by class and by field, prints a 95% interval for the success rate, and writes an optional per-record log and one retry message per failed record. The skill adds a repair ladder with a risk rating per rung, a policy table keyed on the strict success rate, and a retry contract. It never calls a model.

## Capabilities

- 15 named failure classes (empty output, no JSON, truncated, invalid syntax, duplicate key, wrong type, number as string, missing field, extra field, out of range, enum, pattern, length, empty array, array size), each with a remedy and a "do not".
- Repair ladder: fence, prose by default; trailing commas, comments, Python literals, single quotes only when you allow them; truncation is never repaired. A failed record says which disallowed rung would have saved it.
- Schema keywords the script cannot check are listed and the run is refused, never silently ignored.
- Schema from a file or inferred from an example object.
- Strict JSON report, JSONL log, JSONL retry messages. Outputs that resolve to an input are refused even with `--force`.

## When to use / when not to

Use it when replies break `json.loads` or fail a schema, when you need a failure rate before and after a prompt change, or when you must decide between a tolerant parser and a retry. Do not use it to build eval test sets (see `llm-eval-test-sets`), to write the prompt (`prompt-writing`), to design tool input schemas (`mcp-server-builder`), or to call a model. Those neighbours build tests, prompts and tool definitions; this one checks real outputs you already have and counts what breaks.

## Requirements

Python 3.9 or newer, standard library only. No network. Tested here on Python 3.11, Windows 11.

## Install

Copy the folder to `.claude/skills/llm-json-output-validator/` or `.agents/skills/llm-json-output-validator/`. No pinned release exists yet.

## Example

Prompt: "These 10 replies from my review-summary prompt are in outputs.jsonl, schema in schema.json. What is the failure rate and what fails most?"

Real output of `python scripts/validate_outputs.py --schema schema.json --input outputs.jsonl` on `evals/files/t1-batch-diagnosis` (abridged):

```
n 10, valid 4, rate 0.4, rate_ci95 [0.1682, 0.6873]
clean_valid 2, valid_after_repair 2, repairs_applied {"fence": 2}
failures_by_class {"invalid_syntax": 3, "enum_violation": 1, "number_as_string": 1, "truncated": 1}
failures_by_field {"$": 4, "$.rating": 1, "$.sentiment": 1}
example: line 4 invalid_syntax "... (would parse with rung: trailing_commas)"
```

With `--allow none` the same batch gives 2 of 10 (interval 0.0567 to 0.5098). The skill then reports a strict rate under 80%, says the sample is too small to justify a trailing-comma rung on 3 records, and points at the prompt first.

Second prompt: "Validate outputs.jsonl against schema.json and tell me if all replies are good." With a schema using `format`, the script exits 2 naming `format at $.when`; with `--allow-unsupported` it reports 5 of 6 valid and lists the keyword, and the skill says the date-time requirement was not checked.

## Limits

- Small schema subset; no formats, unions or references.
- `prose` takes the first value that parses (a `[1]` citation can be taken; a note is logged when more JSON follows).
- Checks shape, not truth. Thresholds are working values, not measured optima.

## Evidence

Script fixtures only (see `VERIFICATION.md`): 15 of 15 cases pass, lint 0 FAIL / 0 WARN. Not tested: efficacy against a baseline, triggering, other tools, human review.

## Demo script (60 to 90 seconds)

1. Prompt: "Here are 10 replies and my schema. How bad is it?" Show the folder.
2. The agent runs the script; the JSON report appears: 4 of 10, strict 2 of 10.
3. The agent reads `failures_by_class`: three trailing-comma failures, one string rating, one truncated, one bad enum. It declines to auto-close the truncated record.
4. It prints the policy row ("strict rate under 80%: fix the prompt first") and the retry message for the string rating.
5. After the prompt change, the same command runs again and the intervals are compared.

## FAQ seeds

- Does it need network or a model key? No.
- Does it work with my provider's native structured-output mode? It checks any text you have; with such a mode the strict rate should be near 100%.
- Why does it refuse my schema? A keyword it cannot check was found; rewrite the schema or use `--allow-unsupported` and accept that those rules are unchecked.
- Does it fix my data? No. Repairs change syntax only, never values.
- How is it different from `llm-eval-test-sets`? That builds test cases; this checks the outputs you already have.
- How do I uninstall? Delete the folder; it writes nothing unless you pass an output path.

## Changelog

0.1.0, 2026-11-21: first draft; script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5 as Skill Almanac Editorial; accountable publisher Global Media Holdings. No human review has taken place yet.
