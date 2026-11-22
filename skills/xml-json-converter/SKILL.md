---
name: xml-json-converter
description: Converts XML to JSON and JSON back to XML under one stated mapping, with attributes as @keys, mixed text as #text, and repeated siblings as arrays. Use when the user asks to convert XML to JSON, convert JSON to XML, or confirm that an XML file and a JSON file hold the same data structure. Do not use for XSLT, XPath, schema validation, documents with DOCTYPE or entity declarations, namespaced XML, or inputs over 2 MB.
license: Apache-2.0
compatibility: Python 3.9+ standard library only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# XML to JSON converter

This skill runs [scripts/xml_json.py](scripts/xml_json.py) in one of two modes. XML and JSON do not map one to one, so the script applies the 11 mapping rules R1 to R11 and reports whether the data structure survives a full round trip. The script never changes its input, and it never overwrites an output file.

## Workflow

1. Confirm the mode. Use `xml2json` when the input is XML. Use `json2xml` when the input is a JSON object. If the user gave neither, ask which direction they need. Output: the mode name.
2. Check the input against the limits in the decision table below. Output: "input ok" or the first failing limit.
3. Choose a new output file name in the same folder as the user's file. The name must not exist yet and must differ from the input. Output: the output path.
4. Run the command below. Output: the stdout JSON report and the exit code.
5. Read the exit code with the decision table. Exit 1 still writes the output file, so report the `first_difference` path to the user. Output: the decision (deliver, deliver with findings, or stop).
6. Write the reply using the output contract. Output: the four headings in that contract.

## Command

```
python -I scripts/xml_json.py xml2json <input-file> <output-file>
python -I scripts/xml_json.py json2xml <input-file> <output-file>
```

Use `<input-file>` and `<output-file>` as placeholders for the user's paths. Do not run the script on the bundled fixture unless the user asks for a smoke test. The fixture is [fixtures/sample-catalog.txt](fixtures/sample-catalog.txt). It holds XML text under a `.txt` name so the package stays text-only, and the converter reads it the same way. The license is in [LICENSE.txt](LICENSE.txt).

## Mapping examples

| XML input | JSON output |
| --- | --- |
| `<a/>` | `{"a": ""}` |
| `<a id="1"/>` | `{"a": {"@id": "1"}}` |
| `<a>x</a>` | `{"a": "x"}` |
| `<a id="1">x</a>` | `{"a": {"@id": "1", "#text": "x"}}` |
| `<a><b>1</b></a>` | `{"a": {"b": "1"}}` |
| `<a><b>1</b><b>2</b></a>` | `{"a": {"b": ["1", "2"]}}` |
| `<n>P <i>q</i> r</n>` | `{"n": {"i": "q", "#text": "P r"}}` |

Every XML value is a string. The `P r` row shows that the spaces around a child are joined with one space, so the original spacing is not kept.

## Decision table

| Condition | Value | Result |
| --- | --- | --- |
| Input size cap (working value) | 2,097,152 bytes | Above the cap: exit 2, code `input_too_large` |
| Converted and `round_trip_equal` is true | none | Exit 0: deliver the output file |
| Converted and `round_trip_equal` is false | `first_difference` path | Exit 1: deliver the file and list the path as a finding |
| Any error on stderr | error code | Exit 2: stop and report the code |

Check these JSON features before running `json2xml`. Each one causes a finding (exit 1) or a refusal (exit 2):

| JSON feature | XML result | Outcome |
| --- | --- | --- |
| Number such as `7` | text `7` | Exit 1: type changes to string |
| `true` or `false` | text `true` or `false` | Exit 1: type changes to string |
| `null` | empty element | Exit 1: comes back as `""` |
| Array with one object | one element | Exit 1: comes back as an object at the array path |
| Empty array `[]` | no element | Exit 1: key is missing on the way back |
| Array inside an array | none | Exit 2, code `mapping_error` |
| Top-level value with more than one key | none | Exit 2, code `root_shape` |
| Attribute with `null`, object, or array value | none | Exit 2, code `mapping_error` |

## Output contract

The reply to the user has these four headings, in this order:

1. `## Result`: mode, exit code, output path, input bytes, output bytes.
2. `## Round trip`: the value of `round_trip_equal`, and `first_difference` when it is not null.
3. `## Mapping rules`: the 11 rule lines R1 to R11 copied from the `rules` key of the report.
4. `## Open questions`: each refused or lost item, one per line, with the error code or the `first_difference` path.

The script stdout is a JSON object with exactly these keys: `mode`, `input_bytes`, `output_bytes`, `round_trip_equal`, `first_difference`, `rules`. The stderr error line is a JSON object with exactly two keys: `error` and `message`.

## Error codes

Every code below can appear on stderr with exit 2:

| Code | Meaning |
| --- | --- |
| `usage` | Wrong number of arguments or unknown mode |
| `input_missing` | Input file cannot be read |
| `input_too_large` | Input exceeds the 2 MB cap |
| `unsupported_encoding` | UTF-16 or UTF-32 byte order mark found |
| `doctype_refused` | `<!DOCTYPE` or `<!ENTITY` found in the raw bytes as UTF-8, UTF-16 LE or UTF-16 BE, in any letter case |
| `parse_error` | XML is not well formed |
| `input_not_utf8` | JSON input is not UTF-8 |
| `json_error` | JSON is invalid, or contains NaN or Infinity |
| `too_deep` | Nesting exceeds what the converter can recurse through |
| `namespace_refused` | Element or attribute name uses Clark notation |
| `root_shape` | JSON top level is not one object with one key, or its value is an array |
| `invalid_name` | A JSON key is not a valid XML name |
| `mapping_error` | A value cannot be represented in XML |
| `output_is_input` | Output path equals input path |
| `output_exists` | Output path already exists; nothing is overwritten |
| `output_error` | Output file cannot be created |

## Refuse or stop when

- The input is over 2 MB, or the user asks for a bigger file to be split and converted in parts.
- The XML contains `<!DOCTYPE` or `<!ENTITY`, even inside a comment or CDATA section.
- The XML uses namespaces. Ask the user for a non-namespaced copy.
- The file starts with a UTF-16 or UTF-32 byte order mark. Ask the user to re-save it as UTF-8.
- The user asks to overwrite an output file. Choose a new name and say so.
- The user asks for XSLT, XPath, schema validation, or repair of malformed XML. This skill does none of those.
- The user needs byte-identical XML back. Explain that only the data structure is compared, and continue only if they accept that.

## Limits

- The round trip compares the data structure only. It does not compare XML byte order, attribute order, whitespace, the XML declaration, comments, or processing instructions.
- Comments and processing instructions are dropped silently by the parser.
- Object key order is not compared. Sibling elements with different names are regrouped by first appearance, so their document order can change.
- Scalar types are not preserved. XML text is always a string, so JSON numbers and booleans always produce a finding.
- On the JSON side, a key must start with a letter or underscore and then use letters, digits, underscores, dots, or hyphens. Colons are refused, so prefixed names fail with `invalid_name`.
- The script does not validate XML against a schema, and it does not check that the data is correct, complete, or meaningful.

## Files shipped with this skill

- [SKILL.md](SKILL.md): this workflow.
- [scripts/xml_json.py](scripts/xml_json.py): the converter, standard library only.
- [fixtures/sample-catalog.txt](fixtures/sample-catalog.txt): a 12-line XML document with attributes, repeated elements, and mixed text, for smoke tests.
- [LICENSE.txt](LICENSE.txt): Apache License 2.0.
