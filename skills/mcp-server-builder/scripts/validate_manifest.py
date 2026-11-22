#!/usr/bin/env python3
"""Validate a tool manifest for a Model Context Protocol server.

Usage:
    python scripts/validate_manifest.py MANIFEST.json [--max-desc N] [--min-desc N] [--strict]

Input: a JSON file holding either an array of tools, or an object with a
"tools" array (the shape a tools/list result has). Each tool should have
"name", "description" and "inputSchema".

Reads only the file it is given. Writes nothing. No network.
Prints exactly one JSON object on stdout (strict JSON, ASCII only).

Exit codes:
    0  no errors (warnings allowed unless --strict)
    1  at least one error (or any warning with --strict)
    2  usage problem: missing, empty or unparseable file, wrong top-level shape
"""
import json
import re
import sys

# Working values chosen by the skill authors, not protocol limits.
DEFAULT_MAX_DESC = 600   # long descriptions burn context on every request that lists tools
DEFAULT_MIN_DESC = 40    # below this a description cannot hold both what and when
MAX_NAME_LEN = 64        # keeps names short; many clients prefix server names

SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
# "when to use" cue: phrases a model can match against a user request.
WHEN_CUE = re.compile(
    r"\b(use this (tool )?(when|to|for)|use when|use it when|use for|when to use|"
    r"call this (tool )?(when|to)|call when|call to)\b",
    re.IGNORECASE,
)
# Name tokens that signal a destructive or hard-to-undo action.
DESTRUCTIVE_VERBS = {
    "delete", "remove", "drop", "destroy", "purge", "wipe", "erase", "truncate",
    "kill", "revoke", "terminate", "overwrite", "reset", "format",
}


def name_tokens(name):
    """Lowercase word tokens of a tool name, splitting camelCase, snake_case, kebab-case, dots and spaces."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [t for t in re.split(r"[^A-Za-z0-9]+", spaced.lower()) if t]


def finding(tool_name, index, rule, severity, message):
    return {"tool": tool_name, "index": index, "rule": rule, "severity": severity, "message": message}


def check_schema(schema, tool_name, index, out):
    """Checks on inputSchema. Appends findings to out."""
    if not isinstance(schema, dict):
        out.append(finding(tool_name, index, "schema-missing", "error",
                           "inputSchema is missing or not an object; add {\"type\": \"object\", \"properties\": {}, \"required\": [], \"additionalProperties\": false}"))
        return None
    if schema.get("type") != "object":
        out.append(finding(tool_name, index, "schema-type-not-object", "error",
                           "inputSchema.type must be \"object\""))
    props = schema.get("properties")
    if not isinstance(props, dict):
        out.append(finding(tool_name, index, "schema-no-properties", "error",
                           "inputSchema.properties is missing; declare every argument, or use an empty object for a tool with none"))
        props = {}
    required = schema.get("required")
    if required is None:
        out.append(finding(tool_name, index, "schema-no-required", "warning",
                           "inputSchema.required is unset; list required arguments (an empty array is fine)"))
    elif not isinstance(required, list) or not all(isinstance(r, str) for r in required):
        out.append(finding(tool_name, index, "schema-required-invalid", "error",
                           "inputSchema.required must be an array of strings"))
    else:
        for r in required:
            if r not in props:
                out.append(finding(tool_name, index, "schema-required-unknown", "error",
                                   "required lists '%s' but it is not in properties" % r))
    if "additionalProperties" not in schema:
        out.append(finding(tool_name, index, "schema-additional-properties-unset", "warning",
                           "additionalProperties is unset; set it to false so unknown arguments are rejected"))
    for pname, pdef in props.items():
        if not isinstance(pdef, dict):
            out.append(finding(tool_name, index, "property-invalid", "error",
                               "property '%s' is not a schema object" % pname))
            continue
        if not pdef.get("description"):
            out.append(finding(tool_name, index, "property-no-description", "warning",
                               "property '%s' has no description" % pname))
        if pdef.get("type") == "array" and "maxItems" not in pdef:
            out.append(finding(tool_name, index, "array-unbounded", "warning",
                               "array property '%s' has no maxItems" % pname))
    return props


def check_tool(tool, index, max_desc, min_desc, seen, out):
    if not isinstance(tool, dict):
        out.append(finding(None, index, "tool-not-object", "error", "entry %d is not a JSON object" % index))
        return
    name = tool.get("name")
    label = name if isinstance(name, str) else None
    if not isinstance(name, str) or not name:
        out.append(finding(label, index, "name-missing", "error", "tool has no name"))
    else:
        if not SNAKE_CASE.match(name):
            out.append(finding(name, index, "name-not-snake-case", "error",
                               "name must be lowercase snake_case (letters, digits, single underscores, starts with a letter)"))
        if len(name) > MAX_NAME_LEN:
            out.append(finding(name, index, "name-too-long", "error",
                               "name is %d chars; keep it at %d or fewer" % (len(name), MAX_NAME_LEN)))
        if name in seen:
            out.append(finding(name, index, "name-duplicate", "error",
                               "name already used by entry %d" % seen[name]))
        else:
            seen[name] = index
    desc = tool.get("description")
    if not isinstance(desc, str) or not desc.strip():
        out.append(finding(label, index, "description-missing", "error", "description is missing or empty"))
    else:
        if len(desc) > max_desc:
            out.append(finding(label, index, "description-too-long", "error",
                               "description is %d chars; limit is %d" % (len(desc), max_desc)))
        elif len(desc) < min_desc:
            out.append(finding(label, index, "description-too-short", "warning",
                               "description is %d chars; under %d cannot hold what and when" % (len(desc), min_desc)))
        if not WHEN_CUE.search(desc):
            out.append(finding(label, index, "description-no-when-to-use", "error",
                               "description has no 'Use when ...' sentence; say when the model should pick this tool"))
    props = check_schema(tool.get("inputSchema"), label, index, out)
    if isinstance(name, str) and name:
        verbs = sorted(set(name_tokens(name)) & DESTRUCTIVE_VERBS)
        if verbs:
            if props is None or "confirm" not in props:
                out.append(finding(label, index, "destructive-no-confirm", "error",
                                   "name contains destructive verb '%s' but inputSchema has no 'confirm' property" % verbs[0]))
            else:
                cdef = props["confirm"] if isinstance(props["confirm"], dict) else {}
                if cdef.get("type") != "boolean":
                    out.append(finding(label, index, "confirm-not-boolean", "warning",
                                       "'confirm' should be type boolean"))
                req = tool.get("inputSchema", {}).get("required")
                if not isinstance(req, list) or "confirm" not in req:
                    out.append(finding(label, index, "confirm-not-required", "warning",
                                       "'confirm' should be listed in required"))


def validate(data, max_desc, min_desc):
    tools = data["tools"] if isinstance(data, dict) and isinstance(data.get("tools"), list) else data
    if not isinstance(tools, list):
        return None
    out, seen = [], {}
    for i, tool in enumerate(tools):
        check_tool(tool, i, max_desc, min_desc, seen, out)
    return tools, out


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=True, indent=2) + "\n")


def fail_usage(message):
    emit({"command": "validate", "ok": False, "error": message})
    return 2


def parse_args(argv):
    path, max_desc, min_desc, strict = None, DEFAULT_MAX_DESC, DEFAULT_MIN_DESC, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--strict":
            strict = True
        elif a in ("--max-desc", "--min-desc"):
            if i + 1 >= len(argv) or not argv[i + 1].isdigit():
                raise ValueError("%s needs a whole number" % a)
            if a == "--max-desc":
                max_desc = int(argv[i + 1])
            else:
                min_desc = int(argv[i + 1])
            i += 1
        elif a.startswith("--"):
            raise ValueError("unknown option %s" % a)
        elif path is None:
            path = a
        else:
            raise ValueError("only one manifest file is accepted")
        i += 1
    if path is None:
        raise ValueError("usage: validate_manifest.py MANIFEST.json [--max-desc N] [--min-desc N] [--strict]")
    return path, max_desc, min_desc, strict


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        path, max_desc, min_desc, strict = parse_args(argv)
    except ValueError as exc:
        return fail_usage(str(exc))
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        return fail_usage("cannot read %s: %s" % (path, exc.strerror or exc))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return fail_usage("file is not valid UTF-8")
    if not text.strip():
        return fail_usage("file is empty")
    try:
        data = json.loads(text)
    except ValueError as exc:
        return fail_usage("file is not valid JSON: %s" % exc)
    result = validate(data, max_desc, min_desc)
    if result is None:
        return fail_usage("top level must be an array of tools or an object with a 'tools' array")
    tools, findings = result
    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    ok = errors == 0 and (warnings == 0 or not strict)
    emit({
        "command": "validate",
        "file": path,
        "tools": len(tools),
        "max_desc": max_desc,
        "strict": strict,
        "ok": ok,
        "errors": errors,
        "warnings": warnings,
        "findings": findings,
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
