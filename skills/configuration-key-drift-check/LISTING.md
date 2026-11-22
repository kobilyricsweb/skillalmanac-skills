# configuration-key-drift-check

Unpublished original; editorial tier: free. No public score or release approval.

## What and when

Use when comparing supplied required and optional configuration key-name declarations against named configuration key arrays. Do not use for reading environment files, inspecting secrets or runtime values, proving semantic compatibility, modifying configuration, or checking live services.

## Task boundary

config-file-validator checks one configuration file for syntax, types, missing keys, placeholders, and masked secrets. configuration-key-drift-check only compares supplied case-sensitive key-name arrays with named configurations; it neither reads configuration files nor examines values or semantic compatibility.

## Try the independent synthetic example

The interpreter is unavailable. Provide a labeled manual, unexecuted assessment of this exact JSON input without running or editing the bundled script: {"required_keys":["PORT","DB"],"optional_keys":["DEBUG"],"configurations":[{"name":"prod","keys":["PORT","DEBUG","DEBUG","EXTRA"]}]}. Apply exact, case-sensitive key comparison. Report the input scope, findings, execution mode, and untested limits; do not inspect any environment or secret values.

Observed inline supplied-skill output (tools unavailable; not native discovery), job `aggregate_isolated_84a601e773dc5ad9`:

```text
Manual and unexecuted assessment

Scope: Only the supplied JSON extract was assessed using exact, case-sensitive key-name comparison. Required keys: PORT, DB. Optional key: DEBUG. Configuration assessed: prod, preserving all supplied entries: PORT, DEBUG, DEBUG, EXTRA.

Result: {"ok":false,"errors":[],"configuration_count":1,"findings":[{"configuration":"prod","code":"DUPLICATE_CONFIG_KEY","keys":["DEBUG"]},{"configuration":"prod","code":"MISSING_REQUIRED_KEY","keys":["DB"]},{"configuration":"prod","code":"UNEXPECTED_KEY","keys":["EXTRA"]}]}

Execution mode: manual and unexecuted. The interpreter and bundled script were not run, so no exit code or exact script stdout is claimed.

Untested limits: No environment files, configuration values, secrets, services, deployments, or live runtime state were inspected. This assessment does not establish semantic compatibility or infer runtime behavior.
```

## Verify locally

Run `python evals/run_fixtures.py` from this package directory. See [verification](VERIFICATION.md) for actual results and outstanding gates.
