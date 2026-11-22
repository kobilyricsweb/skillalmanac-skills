"""Convert XML to JSON and JSON to XML under one stated mapping.

Usage:
  python -I scripts/xml_json.py xml2json <input-file> <output-file>
  python -I scripts/xml_json.py json2xml <input-file> <output-file>

Exit codes: 0 converted and the data structure round-trips equal;
1 converted but the round trip differs (findings); 2 usage or input error,
reported as one line of JSON on stderr.

Reads the input only. Writes one new output file, opened with mode "x", so an
existing file is never overwritten. Uses only the Python standard library:
no network, no subprocess, no eval or exec. DOCTYPE declarations are refused.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
TEXT_KEY = "#text"
ATTR_PREFIX = "@"
NAME_RE = re.compile(r"^[^\W\d][\w.\-]*$")
INVALID_XML_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
BOM_PREFIXES = (
    b"\xff\xfe",
    b"\xfe\xff",
    b"\x00\x00\xfe\xff",
    b"\xff\xfe\x00\x00",
)


def _any_case_pattern(text, codec):
    """Byte pattern for text in one encoding, matching any ASCII letter case."""
    parts = []
    for ch in text:
        upper = ch.upper().encode(codec)
        lower = ch.lower().encode(codec)
        parts.append(b"(?:" + re.escape(upper) + b"|" + re.escape(lower) + b")")
    return b"".join(parts)


# Raw-byte scan run before any parse: <!DOCTYPE and <!ENTITY in UTF-8,
# UTF-16 LE and UTF-16 BE, in any letter case, so no encoding hides them.
DECLARATION_RE = re.compile(b"|".join(
    _any_case_pattern(word, codec)
    for word in ("<!DOCTYPE", "<!ENTITY")
    for codec in ("utf-8", "utf-16-le", "utf-16-be")
))

RULES = [
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
    "R11 JSON to XML: null becomes an empty element; booleans become true or false; numbers become text.",
]

class Fail(Exception):
    """A usage or input error that ends the run with exit code 2."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def read_input(path_str):
    path = Path(path_str)
    try:
        if path.stat().st_size > MAX_BYTES:
            raise Fail("input_too_large", "input exceeds 2 MB")
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        raise Fail("input_missing", "input file cannot be read")
    if len(data) > MAX_BYTES:
        raise Fail("input_too_large", "input exceeds 2 MB")
    return data


def parse_xml(data):
    if DECLARATION_RE.search(data):
        raise Fail("doctype_refused", "DOCTYPE and entity declarations are refused")
    if data.startswith(BOM_PREFIXES):
        raise Fail("unsupported_encoding", "UTF-16 or UTF-32 input is not supported; save as UTF-8")
    try:
        return ET.fromstring(data)
    except ET.ParseError:
        raise Fail("parse_error", "input is not well-formed XML")


def element_to_value(el):
    if el.tag.startswith("{"):
        raise Fail("namespace_refused", "namespaced element names are refused")
    children = list(el)
    attrs = dict(el.attrib)
    pieces = []
    if el.text and el.text.strip():
        pieces.append(el.text.strip())
    for child in children:
        if child.tail and child.tail.strip():
            pieces.append(child.tail.strip())
    text = " ".join(pieces)
    if not children and not attrs:
        return text
    obj = {}
    for name, value in attrs.items():
        if name.startswith("{"):
            raise Fail("namespace_refused", "namespaced attribute names are refused")
        obj[ATTR_PREFIX + name] = value
    groups = {}
    for child in children:
        groups.setdefault(child.tag, []).append(child)
    for tag, items in groups.items():
        values = [element_to_value(item) for item in items]
        obj[tag] = values if len(values) > 1 else values[0]
    if text:
        obj[TEXT_KEY] = text
    return obj


def check_name(name):
    if not NAME_RE.match(name):
        raise Fail("invalid_name", "a key cannot be used as an XML name")


def text_of(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if INVALID_XML_CHARS.search(value):
            raise Fail("mapping_error", "text contains a character XML 1.0 cannot carry")
        return value
    raise Fail("mapping_error", "text must be a string, number, boolean or null")


def build_element(tag, value):
    check_name(tag)
    el = ET.Element(tag)
    if isinstance(value, dict):
        for key, child in value.items():
            if key == TEXT_KEY:
                el.text = text_of(child)
            elif key.startswith(ATTR_PREFIX):
                name = key[len(ATTR_PREFIX):]
                check_name(name)
                if child is None or isinstance(child, (dict, list)):
                    raise Fail("mapping_error", "attribute value must be a string, number or boolean")
                el.set(name, text_of(child))
            else:
                items = child if isinstance(child, list) else [child]
                for item in items:
                    if isinstance(item, list):
                        raise Fail("mapping_error", "nested arrays cannot be represented in XML")
                    el.append(build_element(key, item))
    elif isinstance(value, list):
        raise Fail("mapping_error", "nested arrays cannot be represented in XML")
    else:
        el.text = text_of(value)
    return el


def json_root_element(obj):
    if not isinstance(obj, dict) or len(obj) != 1:
        raise Fail("root_shape", "top-level JSON must be an object with exactly one key")
    (tag, value), = obj.items()
    if isinstance(value, list):
        raise Fail("root_shape", "the root value must not be an array")
    return build_element(tag, value)


def serialize(root):
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def first_difference(a, b, path="$"):
    if a == b:
        return None
    if isinstance(a, dict) and isinstance(b, dict):
        for key in list(a.keys()) + [k for k in b if k not in a]:
            if key not in a or key not in b:
                return path + "." + key
            found = first_difference(a[key], b[key], path + "." + key)
            if found:
                return found
        return path
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            found = first_difference(x, y, "%s[%d]" % (path, index))
            if found:
                return found
    return path


def reject_constant(name):
    raise Fail("json_error", "NaN and Infinity are not valid JSON")


def write_new(path_str, text):
    try:
        with open(path_str, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        raise Fail("output_exists", "output path already exists; choose a new file name")
    except OSError:
        raise Fail("output_error", "output file cannot be created")
    return len(text.encode("utf-8"))


def run(mode, in_path, out_path):
    if Path(in_path).resolve() == Path(out_path).resolve():
        raise Fail("output_is_input", "output path must differ from the input path")
    data = read_input(in_path)
    try:
        if mode == "xml2json":
            root = parse_xml(data)
            original = {root.tag: element_to_value(root)}
            out_text = json.dumps(original, indent=2, ensure_ascii=False) + "\n"
            xml_text = serialize(build_element(root.tag, original[root.tag]))
        else:
            try:
                original = json.loads(data.decode("utf-8"), parse_constant=reject_constant)
            except UnicodeDecodeError:
                raise Fail("input_not_utf8", "JSON input must be UTF-8")
            except ValueError:
                raise Fail("json_error", "input is not valid JSON")
            xml_text = serialize(json_root_element(original))
            out_text = xml_text
        reparsed = parse_xml(xml_text.encode("utf-8"))
        back = {reparsed.tag: element_to_value(reparsed)}
    except RecursionError:
        raise Fail("too_deep", "nesting is too deep to convert")
    diff = first_difference(original, back)
    out_bytes = write_new(out_path, out_text)
    report = {
        "mode": mode,
        "input_bytes": len(data),
        "output_bytes": out_bytes,
        "round_trip_equal": diff is None,
        "first_difference": diff,
        "rules": RULES,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if diff is None else 1


def main(argv):
    if len(argv) != 3 or argv[0] not in ("xml2json", "json2xml"):
        sys.stderr.write(json.dumps({
            "error": "usage",
            "message": "usage: xml_json.py xml2json|json2xml <input-file> <output-file>",
        }) + "\n")
        return 2
    try:
        return run(argv[0], argv[1], argv[2])
    except Fail as failure:
        sys.stderr.write(json.dumps({"error": failure.code, "message": failure.message}) + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
