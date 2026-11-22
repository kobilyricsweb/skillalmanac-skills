# XML to JSON converter

## One line

Converts an XML document to JSON and back again, using a fixed mapping for attributes, mixed text, and repeated elements, and reports whether the data structure survives the round trip.

## What it does

The skill runs one standard-library Python script in one of two modes. In `xml2json` mode it reads a well-formed XML file, maps the root element to the single top-level key of a JSON object, and writes that object to a new file. Attributes become keys prefixed with `@`. An element that has attributes or children and also has text keeps that text under `#text`. Several sibling elements with the same name become one array in document order. In `json2xml` mode the script reads a JSON object with exactly one top-level key, rebuilds an XML tree from it, and writes the XML to a new file.

After each conversion the script parses its own output again and compares the result with the original data structure. The stdout report gives `round_trip_equal`, the first path where the two structures differ, and the eleven mapping rules that were applied. A mismatch exits with code 1 and still leaves the file in place, so the user can see exactly which key lost information. The script never overwrites an output file, never writes to the input path, and refuses any input with a DOCTYPE declaration or a namespaced name.

## When to use

Use it when a user has an XML feed, export, or configuration file and needs JSON for a script, a web API, or a spreadsheet import. It also fits the reverse case, where a JSON payload must be turned into XML for a system that accepts only XML. Because the report names the first differing path, it is a practical check that a conversion did not silently change repeated items into a single value.

## When not to use

Do not use it for XSLT, XPath queries, schema validation, or repair of malformed XML. Do not use it for documents that carry a DOCTYPE or entity declarations, for namespaced XML, or for files larger than 2 MB. It is also the wrong tool when the user needs byte-identical XML back, because the round trip compares only the data structure, not whitespace, attribute order, comments, or the XML declaration.

## Requirements

Python 3.9 or later, using only the standard library. No network access, no subprocess call, and no third-party package. The script is run with `python -I`, which ignores the user's environment and current directory when it imports modules.

## Example

The command below was run on the bundled 12-line catalog file. The output file was then converted back to XML in a second run. Both runs exited with code 0.

```
python -I scripts/xml_json.py xml2json <input-file> <output-file>
```

Stdout of the XML to JSON run:

```
{
  "mode": "xml2json",
  "input_bytes": 264,
  "output_bytes": 398,
  "round_trip_equal": true,
  "first_difference": null,
  "rules": [
    "R1 The root element name is the single top-level key of the JSON object.",
    "R2 An attribute becomes a key prefixed with @ and a string value.",
    "R3 Text of an element with no attributes and no child elements becomes a string.",
    "R4 Text of an element with attributes or children becomes the #text key.",
    "R5 Text pieces are stripped, empty pieces are dropped, and the rest are joined with one space.",
    "R6 Repeated sibling names become an array in document order; one occurrence stays a single value.",
    "R7 Comments and processing instructions are dropped by the parser.",
    "R8 Namespaced names (Clark notation) are refused; DOCTYPE declarations are refused.",
    "R9 JSON to XML: the top-level object has exactly one key; @ keys set attributes, #text sets text.",
    "R10 JSON to XML: array items become repeated sibling elements; nested arrays are refused.",
    "R11 JSON to XML: null becomes an empty element; booleans become true or false; numbers become text."
  ]
}
```

The JSON file written by that run:

```
{
  "catalog": {
    "@region": "US",
    "book": [
      {
        "@id": "b1",
        "@lang": "en",
        "title": "Dune",
        "tag": [
          "sci-fi",
          "classic"
        ]
      },
      {
        "@id": "b2",
        "@lang": "en",
        "title": "Emma",
        "tag": "romance"
      }
    ],
    "note": {
      "b": "may",
      "#text": "Prices change."
    }
  }
}
```

The `note` element shows the mixed-content rule. The words "Prices" and "change." are joined with one space, and the child `<b>` element becomes a key. The position of "may" inside the sentence is not kept, which is why the round trip compares structure and not text order.

## Limits

The round trip compares the data structure only. XML byte order, attribute order, whitespace in mixed content, the XML declaration, comments, and processing instructions are not compared, and comments and processing instructions are dropped by the parser. Scalar types are not preserved: every XML value is text, so JSON numbers, booleans, and nulls produce a finding on the way back. Sibling elements with different names are regrouped by first appearance. The script does not validate the XML against any schema, and it does not check that the data is correct, complete, or meaningful for the user's system.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
