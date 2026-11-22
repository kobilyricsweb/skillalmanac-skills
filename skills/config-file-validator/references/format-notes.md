# Format notes and traps

Facts below are stated in my own words from the public specifications, listed at the end. They were not re-fetched in the authoring session.

## Contents
- JSON
- TOML
- INI
- .env
- YAML subset
- Sources

## JSON
- No comments, no trailing commas, no single quotes, no NaN or Infinity. Python's parser accepts NaN and Infinity; other parsers do not, so the script warns.
- A parser stops at the first problem, and a missing comma is reported at the token after it. Look one line above the reported position.
- Duplicate keys are legal for the standard parser and the last one silently wins, which is why the script reports them.
- A UTF-8 byte order mark makes some parsers fail.

## TOML
- Strings must be quoted; `debug = "false"` is a string, not a boolean.
- Defining a key or a table twice is an error. Reported position is where the parser noticed.
- Dates and times are their own type; the schema type `datetime` covers them.

## INI
- Parsed strictly: duplicate sections and keys are errors; key case is kept.
- A trailing `; note` or `# note` on a value line is part of the value unless the application enables inline comments. The script warns.
- `%(name)s` is an interpolation only if the application turns it on; the script does not expand it.

## .env
- Line grammar checked: `KEY=value`, optional `export `, `#` comment lines, quoted values, ` #` after an unquoted value.
- Spaces around `=` are accepted by some loaders and rejected by shells.
- An unquoted value with spaces breaks when the file is sourced by a shell.
- Variable references: `${VAR}` has no default; `${VAR:-x}` falls back to x. The script treats a variable defined anywhere in the same file, or in `--env-file`, as defined.

## YAML subset
Supported: block mappings by indentation (spaces only), block lists of scalars, flow lists of scalars on one line, quoted and plain scalars, `#` comments, an optional leading `---`.

Refused with `unsupported_yaml`: anchors and aliases (`&`, `*`, `<<`), tags (`!`), block scalars (`|`, `>`), flow mappings (`{...}`), lists of mappings, complex keys, more than one document.

Trap warned about: YAML 1.1 loaders read `yes`, `no`, `on`, `off`, `y`, `n` as booleans, so a country code `NO` can become false. YAML 1.2 loaders read them as strings. Quote the value when it is text.

## Sources
- JSON: https://www.rfc-editor.org/rfc/rfc8259 and https://docs.python.org/3/library/json.html
- TOML: https://toml.io/en/v1.0.0 and https://docs.python.org/3/library/tomllib.html
- INI: https://docs.python.org/3/library/configparser.html
- YAML booleans: https://yaml.org/type/bool.html and https://yaml.org/spec/1.2.2/
