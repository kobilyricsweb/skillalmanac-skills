---
name: config-file-validator
description: Validates one config file (JSON, TOML, INI, .env, simple YAML) with a script. Use when the user says check my config, validate my .env or config.toml, why won't this config load, is settings.json valid, or asks about a typo, bad port or secret in a config. Reports syntax errors with line and column, duplicate keys, wrong types, missing or unknown keys, out-of-range values, unresolved ${VAR} placeholders and plain-text secrets (masked), optionally against the user's schema. Do not use for comparing environments, explaining drift, Kubernetes or full YAML, or silent edits.
license: Apache-2.0
compatibility: Needs Python 3.11 or newer (tomllib), standard library only. No network access. Without Python, follow the manual passes in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Config file validator

Check one config file the way its parser would, plus the mistakes a parser accepts silently. Report; do not rewrite the file unless the user asks, and never invent a missing value.

## Workflow

```
- [ ] 1 Identify the file and its format
- [ ] 2 Get or write a schema (optional but better)
- [ ] 3 Run the validator
- [ ] 4 Fix in order: syntax, then types, then semantics
- [ ] 5 Re-run until no errors
- [ ] 6 Report
```

1. **Format.** Chosen by extension: `.json`, `.toml`, `.ini` or `.cfg`, `.env` (also `.env.local`), `.yaml` or `.yml`. Pass `--format` when the name is unusual. For YAML read the subset limits in [references/format-notes.md](references/format-notes.md) first; outside the subset the script says "unsupported_yaml" and stops, so tell the user a full YAML parser is needed. Do not guess.
2. **Schema.** If the user has one, use it. If not, offer to draft a small one from the keys they care about (format in [references/schema-format.md](references/schema-format.md)); a schema the user did not confirm is a guess, so say it is a draft. Without a schema the script still checks syntax, duplicates, ports, placeholders, secrets and quoted booleans.
3. **Run:**

```bash
python scripts/validate_config.py [--schema schema.json] [--env-file resolved.env] [--check-paths] [--base-dir DIR] [--report out.json [--force]] FILE...
```

   Prints JSON; exit 0 no errors, 1 errors, 2 usage or I/O problem (plain message on stderr). The script refuses to write `--report` over any input, with or without `--force`. Run it; do not edit it to make a check pass.
4. **Fix order.** Syntax first (nothing else is reliable until the file parses; JSON reports one syntax error at a time, so re-run). Then duplicates and types. Then semantics (enum, range, paths, placeholders, secrets). Manual fallback without Python: parse with the language's own loader, then walk the class table below by hand.
5. **Re-run** after each batch of fixes. Offer the fixes as edits; apply them only when asked.
6. **Report** in the fixed shape below.

## Output contract

```
{"tool": "validate_config", "schema_used": bool,
 "files": [{"file", "format", "parsed": bool,
            "errors": [{"line": int|null, "col": int|null, "class", "severity": "error"|"warning",
                        "key": str|null, "message", "fix"}]}],
 "masked_values": [{"file", "key", "line", "masked", "reason"}],
 "summary": {"files", "errors", "warnings"}, "not_checked": [..]}
```

`line` is null when the key is missing or its name occurs more than once in a JSON or TOML file (the script does not guess). INI, .env and YAML lines are exact.

## Decision table: finding classes

| class | meaning | severity | repair rule |
|---|---|---|---|
| syntax | file does not parse | error | fix first; nothing else is trusted |
| duplicate_key | same key twice in one object, table, section or file | error | keep one; ask which value is intended, the later one is not automatically right |
| wrong_type | value type differs from schema (including `"8080"` for an int, `"true"` for a bool) | error | remove the quotes or change the value |
| missing_required / empty_value | schema key absent, or present but null, empty or blank | error | ask the owner; never fill in a secret, host or token |
| bad_enum / bad_pattern / out_of_range | outside allowed values, regex (full match) or min/max | error | pick an allowed value |
| unknown_key | key not in schema (warning); likely typo when a close schema key exists | warning | rename the typo, or add the key to the schema if intended |
| unresolved_placeholder | `${VAR}` with no default and no definition; `{{ x }}`, `<NAME>`, `changeme`, `your_..._here` | warning; error when `--env-file` is given and lacks the variable | define the variable or give `${VAR:-default}`; fill template values with real ones |
| secret_plaintext | key or token pattern, private key block, password inside a URL, or a secret-named key holding a literal | error for patterns, warning for name-only | move to environment or a secrets store; rotate if the file was ever committed or shared |
| path_missing | path value does not exist with `--check-paths` | error for schema `path`, warning for `*_path`, `*_file`, `*_dir` names | create it or correct it; paths starting with `~` are not checked |
| suspicious_value | quoted boolean, YAML 1.1 boolean word (`no`, `yes`, `on`, `off`, `y`, `n`), inline comment kept as part of an INI value, whitespace padding, byte order mark | warning | usually fix; the user decides |
| unsupported_yaml | construct outside the YAML subset | error | use a full parser |

Port rule: any key named `port` or ending in `_port` that is outside 1 to 65535 is out_of_range even without a schema.

## Secrets

Never print a secret in the report, the chat or a suggested edit: use the masked form from `masked_values` (first two characters and the length). Detection reads values, not file names: AWS key ids, private key blocks, `sk-` tokens, GitHub, Slack and Google keys, JSON web tokens, and `user:password@` URLs; plus key names containing password, secret, token, api key or credential when the value is a literal of 8 or more characters. Names ending `_file`, `_path`, `_env`, `_ttl`, `_url` and similar are exempt. A hit is a lead, not proof the secret is live; do not test it against any service.

## Report format

```
File: <name> (<format>), parsed: yes/no
Errors: <n> (<classes>)   Warnings: <n>
Fix first: <the syntax or top error, with line>
Needs the owner: <missing or empty values, secrets to rotate>
Not checked: <what the schema does not cover, whether the app accepts these keys, runtime values>
```

## Limits

- Validates against the schema the user supplied; it does not know the application's real rules.
- JSON and TOML line numbers for schema findings come from key-name search and are omitted when ambiguous.
- Duplicate TOML keys carry only the parser's position, with no key name.
- YAML is a subset (see the reference); lists of mappings, anchors, tags, block scalars, flow mappings and multi-document files are refused.
- INI uses strict parsing with no interpolation; `%(name)s` references are not expanded.
- `.env` dialects differ (multiline values, variable expansion); the script follows the common single-line grammar only.
- Placeholders are judged by text only; the script never reads real environment variables.
- Secret detection is pattern based: it misses unusual formats and can flag test values.
- It does not compare files across environments or explain why two files differ.
