# Schema file format

A schema is a small JSON file the user owns. It is strict: unknown fields make the script exit 2 with a message.

```json
{
  "allow_unknown": false,
  "keys": {
    "server.port": {"type": "int", "required": true, "min": 1, "max": 65535},
    "mode": {"type": "string", "required": true, "enum": ["dev", "staging", "prod"]},
    "data_dir": {"type": "path"},
    "tags": {"type": "array", "items": "string"}
  }
}
```

- Key path: dotted. JSON, TOML and YAML use nesting (`server.port`); INI uses `section.key`; `.env` uses the bare name.
- `type`: `string`, `int`, `float`, `bool`, `array`, `object`, `path`, `datetime`. `float` accepts ints. `bool` never accepts a number. In INI and `.env` every value is text, so `int`, `float` and `bool` are parsed from it (bool words: true, false, 1, 0, yes, no, on, off). `array` and `object` cannot be used for INI or `.env`.
- `required`: the key must exist and must not be null, empty or blank.
- `enum`: list of allowed values, compared after parsing, case sensitive.
- `min`, `max`: inclusive, for `int` and `float`.
- `pattern`: regular expression that must match the whole string value.
- `items`: element type for `array`.
- `allow_unknown`: default false, which reports every key not listed (a type `object` key covers everything under it).
- `description`: free text, ignored.

Drafting rule: write schema entries only for keys the user named or the file already contains; mark `required` only when the user says the application cannot start without it.
