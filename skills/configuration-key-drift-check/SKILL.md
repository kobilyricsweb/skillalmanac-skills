---
name: configuration-key-drift-check
description: "Use when comparing supplied required and optional configuration key-name declarations against named configuration key arrays. Do not use for reading environment files, inspecting secrets or runtime values, proving semantic compatibility, modifying configuration, or checking live services."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.11"
  network: none
---

# Configuration Key Drift Check

Read the [input contract](references/input-contract.md) and prepare one local UTF-8 JSON record. Run exactly:

`python <skill>/scripts/audit.py <input.json>`

The audit compares case-sensitive key names only. It reports missing required keys, unexpected keys, and duplicates within each named configuration. Duplicate or overlapping declarations are input errors. It reads only the supplied JSON extract.

## Executed result

Run the bundled script unchanged. Retain its actual exit code and distinguish JSON stdout from interpreter or traceback output. Reproduce exact JSON stdout unless a failure diagnostic exposes a sensitive path; then replace only that path with `[REDACTED PATH]` and label it a redacted transcription.

Exit 0 is a documented pass, 1 is valid input with findings, and 2 is a documented invalid-input or handled-failure result. Branch on `input_error` before interpreting counts or findings. If execution terminates without contracted JSON, report the observed failure and output; do not recast it as an exit-2 JSON response.

## Manual result

If execution is unavailable, label the assessment `manual and unexecuted`; claim neither an exit code nor exact script output. Without normalizing the input:

1. Validate the complete required and optional arrays and configuration structure, including duplicates and overlap.
2. Preserve every supplied configuration key entry, including repetitions.
3. For valid input, compute missing required keys, unexpected keys, and duplicated configuration keys. Report `ok`, `errors`, `configuration_count`, and `findings`; use `errors: []`, and set `ok` from whether findings exist.
4. For invalid input, report `ok: false`, `input_error: true`, the applicable validation errors, and the specified observed `configuration_count` when available. Stop before domain comparison and request a corrected extract. Do not report a `findings` field unless reproducing recorded script output; its omission means no domain comparison was performed, not that no domain defects exist.

State the supplied scope, execution mode, and untested limits. Do not inspect environment files, values, secrets, services, or live state; infer runtime behavior; modify records; or execute command-like key names.

Inputs are bounded to 200 required keys, 200 optional keys, 100 configurations, and 500 keys per configuration; names and keys are at most 200 characters.

Replay numeric reader regressions with `python -B evals/run_numeric_regressions.py`; invalid numeric tokens produce an `invalid_number` diagnostic and exit 2.
