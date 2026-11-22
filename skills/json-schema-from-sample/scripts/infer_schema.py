"""Infer a JSON Schema from one or more sample JSON files.

Usage:
    python -I scripts/infer_schema.py [-o NEW_FILE] SAMPLE [SAMPLE ...]

Each SAMPLE is read only. The observed values are merged into one schema
using draft 2020-12 keywords (type, format, properties, required, items).
The schema goes to stdout, or to NEW_FILE when -o is given. NEW_FILE must
not exist and must not resolve to any SAMPLE path.

Exit codes:
    0  schema written, no findings
    1  schema written, findings printed on stderr (conflicting types)
    2  usage or input error; one JSON error line on stderr, no schema written
"""
import argparse
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 32
MAX_FILES = 100
MAX_INT_DIGITS = 40
MAX_FLOAT_CHARS = 40
MAX_STRING_FOR_FORMAT = 2048

FORMATS = (
    ("date-time", re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})")),
    ("date", re.compile(r"\d{4}-\d{2}-\d{2}")),
    ("email", re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")),
    ("uri", re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://\S+")),
)


class InputError(Exception):
    """Usage or input problem; main() turns it into a one-line JSON error."""


def _cap_int(text):
    if len(text.lstrip("-")) > MAX_INT_DIGITS:
        raise ValueError("integer literal too long")
    return int(text)


def _cap_float(text):
    if len(text) > MAX_FLOAT_CHARS:
        raise ValueError("float literal too long")
    return float(text)


class Node:
    """Accumulates every value seen at one position in the samples."""

    __slots__ = ("types", "obj_total", "prop_counts", "props",
                 "item", "str_total", "fmt_counts")

    def __init__(self):
        self.types = set()
        self.obj_total = 0
        self.prop_counts = {}
        self.props = {}
        self.item = None
        self.str_total = 0
        self.fmt_counts = {}


def add(node, value, depth):
    if depth > MAX_DEPTH:
        raise InputError("nesting deeper than %d levels" % MAX_DEPTH)
    if value is None:
        node.types.add("null")
    elif isinstance(value, bool):
        node.types.add("boolean")
    elif isinstance(value, int):
        node.types.add("integer")
    elif isinstance(value, float):
        node.types.add("number")
    elif isinstance(value, str):
        node.types.add("string")
        node.str_total += 1
        if len(value) <= MAX_STRING_FOR_FORMAT:
            for name, rx in FORMATS:
                if rx.fullmatch(value):
                    node.fmt_counts[name] = node.fmt_counts.get(name, 0) + 1
    elif isinstance(value, list):
        node.types.add("array")
        for element in value:
            if node.item is None:
                node.item = Node()
            add(node.item, element, depth + 1)
    elif isinstance(value, dict):
        node.types.add("object")
        node.obj_total += 1
        for key, child_value in value.items():
            node.prop_counts[key] = node.prop_counts.get(key, 0) + 1
            child = node.props.get(key)
            if child is None:
                child = Node()
                node.props[key] = child
            add(child, child_value, depth + 1)
    else:
        raise InputError("unsupported value type")


def render(node, path, findings):
    base = set(node.types)
    nonnull = base - {"null"}
    if {"integer", "number"} <= nonnull:
        nonnull.discard("integer")
    if len(nonnull) > 1:
        findings.append((path, sorted(base)))

    types = sorted(nonnull)
    if "null" in base:
        types.append("null")
    out = {}
    if len(types) == 1:
        out["type"] = types[0]
    elif types:
        out["type"] = types

    if "string" in nonnull and node.str_total:
        for name, _rx in FORMATS:
            if node.fmt_counts.get(name, 0) == node.str_total:
                out["format"] = name
                break

    if "object" in nonnull and node.props:
        props_out = {}
        required = []
        for key in sorted(node.props):
            props_out[key] = render(node.props[key], path + "." + key, findings)
            if node.prop_counts.get(key, 0) == node.obj_total:
                required.append(key)
        out["properties"] = props_out
        if required:
            out["required"] = required

    if "array" in nonnull and node.item is not None:
        out["items"] = render(node.item, path + "[]", findings)
    return out


def load_sample(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc.strerror))
    if len(raw) > MAX_BYTES:
        raise InputError("%s is larger than 2 MB" % path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("%s is not valid UTF-8" % path)
    try:
        return json.loads(text, parse_int=_cap_int, parse_float=_cap_float)
    except (ValueError, RecursionError, MemoryError) as exc:
        raise InputError("%s is not parseable JSON (%s)" % (path, type(exc).__name__))


def run(args):
    if len(args.samples) > MAX_FILES:
        raise InputError("more than %d sample files" % MAX_FILES)
    input_keys = {os.path.normcase(os.path.realpath(p)) for p in args.samples}
    output_path = None
    if args.output is not None:
        output_path = os.path.realpath(args.output)
        if os.path.normcase(output_path) in input_keys:
            raise InputError("output path is one of the input paths")
        if os.path.lexists(output_path):
            raise InputError("output path already exists")

    root = Node()
    for path in args.samples:
        add(root, load_sample(path), 0)

    findings = []
    schema = render(root, "$", findings)
    text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    if output_path is None:
        sys.stdout.write(text)
    else:
        try:
            with open(output_path, "x", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except FileExistsError:
            raise InputError("output path already exists")
        except OSError as exc:
            raise InputError("cannot write output: %s" % exc.strerror)

    for path, kinds in findings:
        sys.stderr.write("FINDING %s: conflicting types %s\n" % (path, ", ".join(kinds)))
    return 1 if findings else 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Infer a JSON Schema from one or more sample JSON files.")
    parser.add_argument("-o", "--output", default=None,
                        help="new file to write the schema to; must not exist")
    parser.add_argument("samples", nargs="+",
                        help="sample JSON files (1 to %d)" % MAX_FILES)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}) + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
