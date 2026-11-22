# cli-help-example-designer

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when designing valid and invalid command examples from a supplied CLI grammar and target-shell constraints, including token and rendered command forms. Do not use to execute commands, invent flags, infer undocumented behavior, or write a general CLI manual.

## Task boundary

technical-docs-writer authors broader documentation and api-error-example-builder builds documented API error examples; this creates valid and rejected command examples from supplied CLI grammar, not a full manual.

## Try the independent synthetic example

Design a command-example suite without executing commands. Grammar: command `pack build`; required positional SOURCE has supplied example value `demo`; required `--format VALUE` accepts `zip` or `tar`; optional `--sign` requires `--key VALUE`; `--key VALUE` may appear only with `--sign`, and supplied example key is `K1`. No shell is named, so use token arrays. Prerequisite: SOURCE exists. Documented result: creates a package in the selected format. Include valid paths, one rejected example, option coverage, and acceptance checks.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `factory100_execute_1aee4012a0c1`:

```text
{"schema_interpretation":{"command":["pack","build"],"positionals":["SOURCE is required; supplied example: demo"],"options":["--format VALUE is required; VALUE is zip or tar","--sign is optional","--key VALUE is conditional on --sign; supplied example: K1"],"relations":["--sign requires --key VALUE","--key VALUE may appear only with --sign"],"rendering":"token_array","shell":null},"prerequisites":[{"requirement":"SOURCE exists","status":"supplied"}],"valid_examples":[{"purpose":"Build a zip package without signing","tokens":["pack","build","demo","--format","zip"],"expected_result":{"status":"supplied","text":"Creates a package in the selected format."},"shell":null,"rendered_command":null},{"purpose":"Build a tar package with signing","tokens":["pack","build","demo","--format","tar","--sign","--key","K1"],"expected_result":{"status":"supplied","text":"Creates a package in the selected format."},"shell":null,"rendered_command":null}],"rejected_example":{"status":"available","tokens":["pack","build","demo","--format","zip","--key","K1"],"violated_rule":"--key VALUE may appear only with --sign","reason":"The example supplies --key without --sign.","shell":null,"rendered_command":null},"option_coverage":[{"option":"--format","status":"demonstrated","example_purpose_or_reason":"Shown with zip and tar."},{"option":"--sign","status":"demonstrated","example_purpose_or_reason":"Shown in the signed example."},{"option":"--key","status":"demonstrated","example_purpose_or_reason":"Shown with --sign and K1."}],"assumptions_or_conflicts":[],"acceptance_checks":[{"check":"Declared-token compliance","outcome":"pass","basis":"Only supplied commands, values, and flags are used."},{"check":"Constraint coverage","outcome":"pass","basis":"Both format values and signing dependency rules are represented."},{"check":"Non-execution","outcome":"pass","basis":"These are token-array designs only."}]}
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
