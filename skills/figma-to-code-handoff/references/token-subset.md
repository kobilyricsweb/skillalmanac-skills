## Contents

1. The subset the script reads
2. Supported types and literal forms
3. Figma variable to token conversion
4. Manual check list

## 1. The subset the script reads

- Top level is one JSON object. Keys starting with `$` at any level are metadata, never tokens.
- A token is an object that has `$value`. Any other object is a group and may nest.
- `$type` can sit on a token or on any parent group; the nearest one wins.
- An alias is the whole string `{group.token}`: a dotted path from the root to a token. It cannot point to a group or into the fields of a composite value.
- `$modes` at the root lists the modes, for example `["light", "dark"]`. Without it the script uses every mode name it finds and reports `modes_declared: false`.
- A token that changes by mode carries `$extensions.modes`: an object with one value per mode. Its `$value` is the mode-independent default and is what `:root` receives. A token without `$extensions.modes` is the same in every mode and appears only in `:root`.
- Only one modes list per file.

The `$modes` list and the `$extensions.modes` object are conventions of this skill, not fields of the published format; most exports need a small conversion to reach them.

## 2. Supported types and literal forms

| `$type` | Accepted literal | CSS output |
|---|---|---|
| `color` | `#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, or `{colorSpace: "srgb", components: [r,g,b] each 0-1, alpha 0-1 optional}` | the hex text as written, or hex built from the object |
| `dimension` | `"16px"`, `"1.5rem"`, or `{value, unit}` with unit px or rem | `16px` |
| `duration` | `"200ms"`, `"0.2s"`, or `{value, unit}` with unit ms or s | same text |
| `number` | a JSON number | the number |
| `fontWeight` | number 1-1000 or a keyword such as `bold` | as written |
| `fontFamily` | string, or list of strings | comma list; names with spaces are quoted |
| `cubicBezier` | four numbers, x values within 0-1 | `cubic-bezier(a, b, c, d)` |
| `string` | a string (may embed aliases) | as written |
| `boolean` | true or false | not emitted |
| `shadow`, `typography`, `border`, `gradient`, `transition`, `strokeStyle` | not validated | not emitted |

A dimension with no unit (`"16"`) is an error on purpose: Figma floats carry no unit, and the unit is a decision someone must make.

Name rules: each path segment uses letters, digits, hyphen, underscore only (else error), lower-case kebab is the house style (else warning), at most 5 levels. The CSS name is `--` plus the path with dots turned into hyphens.

## 3. Figma variable to token conversion

| Figma variable | Token | Notes |
|---|---|---|
| Collection | top-level group or one file per collection | Keep the collection level only when names would collide without it; `css_name_collision` tells you |
| Group separator `/` in the name | `.` in the path | `Brand/Primary Blue` becomes `brand.primary-blue` |
| Spaces, capitals | lower-case, spaces to hyphens | record each rename in the report |
| Variable type Color (RGBA 0-1) | `color` | convert to hex; alpha below 1 goes to 8-digit hex |
| Variable type Number used for spacing, radius, size, stroke | `dimension` in px | the unit is your decision; ask when unsure |
| Number used for opacity, line-height multiplier, z-index | `number` | confirm the scale first; if opacity is stored 0-100, divide by 100 |
| Number used for font weight | `fontWeight` | |
| String used for a font name | `fontFamily` | add the fallback stack |
| Other String | `string` | |
| Boolean | `boolean` | logic flags for components; no CSS |
| Alias to a variable | `{path}` of the converted target | a collection prefix may change the path; re-resolve every alias after renaming |
| Modes of a collection | root `$modes` plus `$extensions.modes` | mode names such as `Mode 1` are a smell: ask for real names (`light`, `dark`) |
| Variable with the same value in every mode | no `$extensions.modes` | do not copy one value into each mode |
| Collection with its own modes (theme and density together) | split into two files | one `$modes` per file |

Layering that survives modes: primitives (raw palette and scales, no modes), semantic (role names, modes, aliases only), component (optional, aliases only). Literals in the semantic layer are the usual source of `duplicate_value`.

## 4. Manual check list (no Python)

- Every `{alias}` resolves to a token, and the target has the same type.
- No chain of aliases returns to its start, in any mode.
- Every token that uses modes has a non-empty value for every listed mode.
- Every segment is lower-case kebab; no two paths give the same joined name.
- No two tokens of the same type share the same literal; normalise case and `#abc` against `#aabbcc` first.
- Every dimension has px or rem; every colour is hex.
