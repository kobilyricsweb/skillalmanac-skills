# Audit checks: meaning and usual fix

Read this after running `scripts/guardrail_audit.py`, for the ids that did not pass. Statuses: `fail` must be fixed, `warn` should be fixed or consciously accepted, `info` means nothing to declare.

## Contents

- gitignore checks
- Instruction and enforcement checks
- Project checks

## gitignore checks

| id | Meaning | Fix |
|---|---|---|
| `gitignore-present` | no `.gitignore` at the repo root | add one; nested ones are not read by the audit |
| `gitignore-env` | `.env` or `.env.local` would not be ignored | add `.env*` and `!.env.example` |
| `gitignore-keys` | `*.pem`, `*.key` or `id_rsa` not ignored | add `*.pem`, `*.key`, `id_rsa*` |
| `gitignore-credentials` | `credentials.json` not ignored | add it, and any service-account file name the project uses |
| `secret-values-in-files` | a non-ignored text file contains an AWS key id, private key block, `sk-` or GitHub token, or a `password=` style assignment (the detail lists file:line:kind) | remove the value, load it from the environment, and treat it as exposed and rotate it if the file was ever committed |
| `secret-files-exposed` | a secret-looking file exists and no pattern ignores it | add the ignore line; if the file is already tracked, removing it from the index is a change to ask about, and its values should be treated as exposed |

## Instruction and enforcement checks

| id | Meaning | Fix |
|---|---|---|
| `instructions-present` | no `AGENTS.md`, `CLAUDE.md`, Cursor, Copilot or Windsurf instruction file | add a short file: test command, protected paths, what never to run |
| `protected-paths-declared` | no "do not edit" or "protected" list in an instruction file and no deny rules | list generated, vendored, migration and lockfile paths |
| `enforcement-configured` | no deny rules or hooks in `.claude/settings*.json` | add deny rules for the protected paths; add hooks only for logic a rule cannot express |
| `settings-valid-json` | a settings file does not parse | fix the JSON first; a broken file can silently disable every rule in it |

## Project checks

| id | Meaning | Fix |
|---|---|---|
| `test-command` | a manifest exists but no test command is declared (an npm placeholder that says "no test specified" does not count) | add the real command to the manifest and name it in the instruction file |
| `lockfile` | a dependency manifest has no lockfile next to it | generate and commit one; the agent should then treat it as protected |
| `generated-dirs` | a folder such as `dist` or `vendor` exists and is not ignored, marked with a "DO NOT EDIT" header, or named in an instruction file or `.gitattributes` | ignore it if it is build output; otherwise add a header or list it as protected |
