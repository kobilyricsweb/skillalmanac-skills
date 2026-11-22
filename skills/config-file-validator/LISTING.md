# Listing page content: config-file-validator

**One line:** Checks one JSON, TOML, INI or .env config file (and simple YAML) for syntax, types, keys, ports, placeholders and secrets.

## What it does

The agent runs `scripts/validate_config.py` on the file, optionally with a small JSON schema the user owns. The script parses the file with the standard library, reports the first syntax error with line and column (trailing comma, comment, single quotes), and then checks duplicate keys, types, required and empty keys, enums, ranges, patterns, unknown or misspelled keys, ports outside 1 to 65535, unresolved `${VAR}` placeholders, quoted booleans and secrets in plain text. Secret values are never printed; they appear masked. A decision table tells the agent the repair order: syntax, then types, then semantics, and never to invent a missing secret.

## Capabilities

- JSON, TOML (Python 3.11 or newer), INI, .env, and a documented YAML subset; anything outside the subset is refused rather than guessed
- Optional schema: type, required, enum, min, max, pattern, array item type
- Optional `--env-file` to decide whether `${VAR}` is resolvable, and `--check-paths` to see whether named paths exist
- Strict JSON output with `line`, `col`, `class`, `severity`, `fix` per finding and a `masked_values` list
- Optional `--report` file, which can never overwrite an input

## When to use

You say check my config, validate my .env, is this settings.json valid, why will it not load, or you suspect a typo, a bad port or a key left in the file.

## When not to use

- Comparing environments or explaining drift: the Codex skills `configuration-key-drift-check` and `configuration-drift-explainer` do that; this skill looks at one file at a time.
- Kubernetes manifests and full YAML (anchors, tags, multiple documents).
- Writing a config from scratch, or editing it without being asked.

## Requirements

Python 3.11 or newer, standard library only. No network. Without Python the agent follows the class table by hand with the language's own loader.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real fixture runs (not agent sessions):

1. `python scripts/validate_config.py evals/fixtures/secrets.json` exits 1. Findings: `secret_plaintext` (error) on line 2 for an AWS-style key id, shown as `AK***(len 20)`; `secret_plaintext` (warning) on line 3 for `db_password`, shown as `hu***(len 14)`; `unresolved_placeholder` (warning) on line 4 for `${API_TOKEN}`; `secret_plaintext` (error) on line 5 for a password inside a database URL. `token_file` and `max_tokens` are not flagged.
2. `python scripts/validate_config.py --schema evals/fixtures/schema.json evals/fixtures/types.json` exits 1: `server.port` is the string `"8080"` (fix: write 8080 without quotes), `mode` is `test` (allowed dev, staging, prod), `debug` is the string `"true"`, `timeout_seconds` is 900 (max 300), `timout` is unknown, `tags` item 1 is not a string, `server.host` is missing.
3. `python scripts/validate_config.py evals/fixtures/anchor.yaml` exits 1 with `unsupported_yaml` on line 1, instead of pretending to validate it.

## Limits

- It checks against the schema you supply, not the application's real rules.
- JSON and TOML schema findings carry a line only when the key name is unambiguous.
- YAML is a subset; .env follows the common single-line grammar.
- Secret detection is pattern based and can miss unusual formats or flag test values.
- It never reads real environment variables, so placeholders are judged by text only.

## Evidence

See `VERIFICATION.md`. In short: lint passes with 0 FAIL and 0 WARN, and 28 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Differentiation

Nearest existing skills: `configuration-key-drift-check` and `configuration-drift-explainer` (Codex), `record-contract-audit`. Those compare keys across environments or explain drift. This one validates a single file's syntax, types and schema, and finds secrets in its contents.

## Demo script (60 to 90 seconds)

To be recorded from a real agent run. Planned beats: paste a broken `settings.json`; the script points at the trailing comma on line 4; fix it and re-run to see the quoted port and boolean; a `.env` run shows a masked key and an unresolved placeholder; a YAML file with anchors is refused honestly.

## FAQ seeds

- Does it need network access? No.
- Does it send my secrets anywhere? No, and it masks them in its own output.
- Can it validate YAML? Only a simple subset; otherwise it says so.
- Does it fix the file? It proposes fixes; it applies them only if you ask.
- How is it different from comparing two environments? It reads one file, not two.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

0.1.0: first draft, static and fixture checks only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
