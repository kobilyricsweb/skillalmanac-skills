"""Render an OpenAPI 3 JSON document as a Markdown API reference.

Usage:
    python -I scripts/openapi_md.py <input-file> <output-file>

The input is read once and never modified. The output is created with
exclusive-create mode, so an existing file is never overwritten, and the
output path may not be the input path. Standard library only; no network,
no subprocess, no eval.

Exit codes: 0 written with no gaps; 1 written with gaps (fields rendered as
"not documented"); 2 usage or input/output error, with a one-line JSON error
object on stderr.
"""

import json
import os
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")
ND = "not documented"
MAX_ARRAY_DEPTH = 3
SLUG_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789-_"


class CliError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


def fail(code, message):
    raise CliError(code, message)


def text_value(value):
    if isinstance(value, str) and value.strip():
        return value
    return None


def cell(value):
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text.replace("|", "\\|").strip()


def fill(value, gaps, label):
    if value is None or str(value).strip() == "":
        gaps.append(label)
        return ND
    return cell(value)


def resolve(doc, node):
    """Return the dict for node, following one local $ref hop; None if unusable."""
    if not isinstance(node, dict):
        return None
    if "$ref" not in node:
        return node
    ref = node["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return None
    target = doc
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or part not in target:
            return None
        target = target[part]
    if not isinstance(target, dict) or "$ref" in target:
        return None
    return target


def type_of(doc, schema, depth=0):
    s = resolve(doc, schema)
    if s is None:
        return None
    t = s.get("type")
    if isinstance(t, list):
        t = " or ".join(x for x in t if isinstance(x, str)) or None
    if t == "array":
        if depth >= MAX_ARRAY_DEPTH:
            return "array"
        inner = type_of(doc, s.get("items"), depth + 1)
        return "array of " + inner if inner else "array"
    if isinstance(t, str) and t:
        return t
    if isinstance(s.get("properties"), dict):
        return "object"
    if any(k in s for k in ("oneOf", "anyOf", "allOf")):
        return "composed"
    return None


def anchor_for(heading, used):
    base = []
    for ch in heading.lower():
        if ch in SLUG_CHARS:
            base.append(ch)
        elif ch == " ":
            base.append("-")
    slug = "".join(base) or "section"
    count = used.get(slug, 0)
    used[slug] = count + 1
    return slug if count == 0 else slug + "-" + str(count)


def collect_params(doc, item, op):
    """Path-level parameters, overridden by operation-level ones with the same name and location."""
    merged = []
    index = {}
    for source in (item.get("parameters"), op.get("parameters")):
        if not isinstance(source, list):
            continue
        for raw in source:
            p = resolve(doc, raw)
            if p is None or not isinstance(p.get("name"), str) or not isinstance(p.get("in"), str):
                key = ("unusable", len(merged))
            else:
                key = (p["name"], p["in"])
            if key in index:
                merged[index[key]] = p
            else:
                index[key] = len(merged)
                merged.append(p)
    return merged


def param_row(doc, p, gaps, counts):
    counts["parameters"] += 1
    if p is None:
        gaps.append("parameter entry")
        return "| " + ND + " | - | - | - | - |"
    raw_name = text_value(p.get("name")) or "unnamed"
    label = "parameter `" + raw_name + "`"
    name_cell = fill(text_value(p.get("name")), gaps, "parameter name")
    where_cell = fill(text_value(p.get("in")), gaps, "parameter location")
    required = "yes" if p.get("required") is True or p.get("in") == "path" else "no"
    type_cell = fill(type_of(doc, p.get("schema")), gaps, label + " type")
    desc_cell = fill(text_value(p.get("description")), gaps, label + " description")
    return "| " + " | ".join([name_cell, where_cell, required, type_cell, desc_cell]) + " |"


def render_body(doc, raw, gaps, counts, lines):
    body = resolve(doc, raw)
    schema = None
    if body is not None and isinstance(body.get("content"), dict) and body["content"]:
        first = next(iter(body["content"].values()))
        if isinstance(first, dict):
            schema = first.get("schema")
    top = resolve(doc, schema)
    if top is None or not (isinstance(top.get("properties"), dict) and top["properties"]):
        btype = fill(type_of(doc, schema), gaps, "request body schema type")
        lines += ["Body schema type: " + btype + ".", ""]
        return
    required_names = top.get("required") if isinstance(top.get("required"), list) else []
    lines += ["Body schema type: object.", "",
              "| Field | Type | Required | Description |", "|---|---|---|---|"]
    for field_name, field_schema in top["properties"].items():
        counts["request_body_fields"] += 1
        label = "request field `" + str(field_name) + "`"
        fs = resolve(doc, field_schema) or {}
        ftype = fill(type_of(doc, field_schema), gaps, label + " type")
        fdesc = fill(text_value(fs.get("description")), gaps, label + " description")
        required = "yes" if field_name in required_names else "no"
        lines.append("| " + " | ".join([cell(field_name), ftype, required, fdesc]) + " |")
    lines.append("")


def render_responses(doc, responses, gaps, counts, lines):
    lines += ["| Code | Description | Content type | Schema type |", "|---|---|---|---|"]
    for code, raw in responses.items():
        counts["responses"] += 1
        label = "response " + str(code)
        resp = resolve(doc, raw)
        if resp is None:
            gaps.append(label)
            lines.append("| " + cell(code) + " | " + ND + " | - | - |")
            continue
        desc = fill(text_value(resp.get("description")), gaps, label + " description")
        content = resp.get("content")
        if isinstance(content, dict) and content:
            ctype_key, media = next(iter(content.items()))
            ctype = cell(ctype_key)
            schema = media.get("schema") if isinstance(media, dict) else None
            stype = fill(type_of(doc, schema), gaps, label + " schema type")
        else:
            ctype = "none"
            stype = "none"
        lines.append("| " + " | ".join([cell(code), desc, ctype, stype]) + " |")
    lines.append("")


def render_operation(doc, item, op, heading, gaps, counts):
    lines = ["### " + heading, ""]
    summary = fill(text_value(op.get("summary")), gaps, "summary")
    description = fill(text_value(op.get("description")), gaps, "description")
    lines += ["**Summary:** " + summary, "", "**Description:** " + description, ""]

    lines += ["#### Parameters", ""]
    params = collect_params(doc, item, op)
    if not params:
        lines += ["None defined.", ""]
    else:
        lines += ["| Name | In | Required | Type | Description |", "|---|---|---|---|---|"]
        for p in params:
            lines.append(param_row(doc, p, gaps, counts))
        lines.append("")

    lines += ["#### Request body", ""]
    if "requestBody" not in op:
        lines += ["None defined.", ""]
    else:
        render_body(doc, op["requestBody"], gaps, counts, lines)

    lines += ["#### Responses", ""]
    responses = op.get("responses")
    if not isinstance(responses, dict) or not responses:
        gaps.append("responses")
        lines += [ND + ".", ""]
    else:
        render_responses(doc, responses, gaps, counts, lines)
    return lines


def render(doc):
    info = doc.get("info") if isinstance(doc.get("info"), dict) else {}
    doc_gaps = []
    title = text_value(info.get("title"))
    if title is None:
        doc_gaps.append("info title")
    title_line = cell(title) if title is not None else "Untitled API"
    version = fill(text_value(info.get("version")), doc_gaps, "info version")

    counts = {"operations": 0, "parameters": 0, "request_body_fields": 0, "responses": 0}
    toc = []
    anchors = {}
    op_sections = []
    op_gap_lines = []
    all_gaps = len(doc_gaps)
    for path, raw_item in doc["paths"].items():
        item = resolve(doc, raw_item)
        if item is None:
            fail("unsupported_structure", "a path item is not an object or uses an unusable reference")
        for method in METHODS:
            if method not in item:
                continue
            op = item[method]
            if not isinstance(op, dict):
                fail("unsupported_structure", "an operation is not an object")
            counts["operations"] += 1
            heading = method.upper() + " " + path
            gaps = []
            op_sections.extend(render_operation(doc, item, op, heading, gaps, counts))
            all_gaps += len(gaps)
            toc.append("- [" + cell(heading) + "](#" + anchor_for(heading, anchors) + ")")
            if gaps:
                op_gap_lines.append("- `" + heading + "`: " + "; ".join(gaps))

    gap_lines = []
    if doc_gaps:
        gap_lines.append("- Document: " + "; ".join(doc_gaps))
    gap_lines.extend(op_gap_lines)
    counts["not_documented"] = all_gaps

    coverage = ["| Measure | Count |", "|---|---|"]
    for key in ("operations", "parameters", "request_body_fields", "responses", "not_documented"):
        coverage.append("| " + key + " | " + str(counts[key]) + " |")

    out = ["# " + title_line, "",
           "Spec version: " + cell(doc["openapi"]) + ". API version: " + version + ".", "",
           "## Coverage", ""] + coverage + [""]
    out += ["## Table of contents", ""] + (toc or ["None."]) + [""]
    out += ["## Gaps", ""] + (gap_lines or ["None."]) + [""]
    out += ["## Operations", ""] + (op_sections or ["None."])
    text = "\n".join(out).rstrip("\n") + "\n"
    return text, counts


def check_output(in_path, out_path):
    same = os.path.abspath(out_path) == os.path.abspath(in_path)
    if not same and os.path.exists(out_path) and os.path.exists(in_path):
        same = os.path.samefile(in_path, out_path)
    if same:
        fail("output_is_input", "output path is the input file")
    if os.path.exists(out_path):
        fail("output_exists", "output path already exists; choose a new file name")
    parent = os.path.dirname(os.path.abspath(out_path))
    if not os.path.isdir(parent):
        fail("output_dir_missing", "output folder does not exist")


def load_spec(path):
    if not os.path.isfile(path):
        fail("input_missing", "input file is missing or is not a regular file")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        fail("input_missing", "input file cannot be read")
    if len(raw) > MAX_INPUT_BYTES:
        fail("input_too_large", "input file is larger than 2097152 bytes")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input is not valid UTF-8")
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        fail("invalid_json", "input is not valid JSON")
    if not isinstance(doc, dict):
        fail("not_openapi3", "root value must be a JSON object")
    version = doc.get("openapi")
    if not isinstance(version, str) or not version.startswith("3."):
        fail("not_openapi3", "root openapi field must be a string starting with 3.")
    if not isinstance(doc.get("paths"), dict):
        fail("not_openapi3", "root paths field must be an object")
    return doc


def write_output(out_path, text):
    try:
        with open(out_path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except FileExistsError:
        fail("output_exists", "output path already exists; choose a new file name")
    except OSError:
        fail("output_write_failed", "output file could not be written")


def main(argv):
    if len(argv) != 3 or not argv[1] or not argv[2]:
        fail("usage", "usage: openapi_md.py <input-file> <output-file>")
    in_path, out_path = argv[1], argv[2]
    check_output(in_path, out_path)
    doc = load_spec(in_path)
    text, counts = render(doc)
    write_output(out_path, text)
    summary = {
        "status": "findings" if counts["not_documented"] else "ok",
        "operations": counts["operations"],
        "parameters": counts["parameters"],
        "request_body_fields": counts["request_body_fields"],
        "responses": counts["responses"],
        "not_documented": counts["not_documented"],
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if counts["not_documented"] else 0


if __name__ == "__main__":
    try:
        code = main(sys.argv)
    except CliError as err:
        sys.stderr.write(json.dumps({"status": "error", "code": err.code, "message": err.message}) + "\n")
        code = 2
    sys.exit(code)
