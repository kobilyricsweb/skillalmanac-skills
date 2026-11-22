---
name: cli-help-example-designer
description: "Use when designing valid and invalid command examples from a supplied CLI grammar and target-shell constraints, including token and rendered command forms. Do not use to execute commands, invent flags, infer undocumented behavior, or write a general CLI manual."
license: Apache-2.0
metadata:
  author: Skill Almanac Editorial
  author_model: "gpt-5.6-luna"
  license: Apache-2.0
  version: "0.1.1"
  network: none
---

# CLI Help Example Designer

Use this skill when maintainers provide a CLI command schema and need examples that obey its declared syntax and constraints. The artifact is a command-example suite, not an executable script or general manual.

Parse the supplied command hierarchy, positionals, options, defaults, required flags, conflicts, dependencies, value domains, shell, and prerequisites. When no shell is named, render examples as token arrays. When a shell is named, retain the semantic token array and also provide the shell name and a rendered command string whose quoting and escaping follow that shell.

Create prerequisite notes; valid examples covering meaningful options and constraint combinations; a rejected example only when a supplied rejectable rule exists; an option-coverage table; expected results only when supplied or schema-specified; and acceptance checks. Required, exclusive, and dependent options must be handled exactly as stated. Do not add conventional flags, filenames, URLs, credentials, output, exit codes, or side effects. Use labeled symbolic placeholders when a required value lacks a supplied concrete value.

If grammar and prose conflict, show the conflict and do not present the affected command as valid. Missing prerequisites remain unresolved. Do not execute commands.

Return JSON matching the input contract and output schema. For named-shell output, every rendered example must expose both semantic tokens and the shell-specific rendered command. See the synthetic worked example.

Resources: [input contract](references/input-contract.md), [worked example](references/worked-example.md).

Return JSON matching the [domain output contract](references/output-schema.json); the [synthetic shape example](references/schema-example.json) is an illustration, not executed evidence.

Run `python scripts/check_output.py artifact.json` from the package directory to check JSON structure against the bundled schema (Python 3 standard library; offline). Exit0 means structural validity,1 contract violations,2 invalid input or unsupported contract. This bounded schema-profile checker reads at most2MiB/50000 nodes/depth100, rejects duplicate keys/nonfinite or oversized numbers, and checks no facts or task judgment. Replay synthetic structural cases with `python evals/run_fixtures.py`; behavioral quality is assessed separately.
