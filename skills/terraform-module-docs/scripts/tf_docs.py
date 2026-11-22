#!/usr/bin/env python3
"""Generate Markdown documentation for a Terraform module from its .tf files.

Usage:
    python -I scripts/tf_docs.py <module-dir> <output-file.md>

Reads the *.tf files directly inside <module-dir> (not recursive) with
documented regular expressions and a brace matcher. This is NOT a full HCL
parser: it does not evaluate expressions, does not follow module calls, and
does not read heredoc bodies or .tf.json files.

Writes a new Markdown file at <output-file.md>, opened in exclusive-create
mode. An existing path (including any input file) is refused. Default values
of variables whose names look like secrets are written as (redacted).

Exit codes: 0 = documented, no findings; 1 = documented, findings reported;
2 = usage or input error. Errors are one line of JSON on stdout and no file
is written. Success prints one line of JSON with counts and findings.
"""

import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
REDACT_NAME = re.compile(r"(?i)(password|passwd|secret|token|api_?key|private_key)")
BLOCK_RE = re.compile(r'^[ \t]*(variable|output)[ \t]+"([^"]+)"[ \t]*\{', re.M)
RESOURCE_RE = re.compile(r'^[ \t]*resource[ \t]+"([^"]+)"[ \t]+"([^"]+)"[ \t]*\{', re.M)
PROVIDER_RE = re.compile(r"\brequired_providers[ \t]*\{")
ENTRY_RE = re.compile(r"^[ \t]*([A-Za-z_][A-Za-z0-9_-]*)[ \t]*=[ \t]*\{", re.M)
STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
FINDING_TEXT = {
    "VAR_NO_DESCRIPTION": "has no description attribute",
    "VAR_NO_TYPE": "has no type attribute",
}


def fail(message):
    sys.stdout.write(json.dumps({"status": "error", "error": message}) + "\n")
    sys.exit(2)


def read_tf(path, name):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            fail("input file exceeds 2 MB: " + name)
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        fail("cannot read input file: " + name)
    if len(raw) > MAX_BYTES:
        fail("input file exceeds 2 MB: " + name)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input file is not valid UTF-8: " + name)
    return text.replace("\r\n", "\n")


def strip_comments(src):
    """Blank # and // line comments and /* */ block comments outside strings."""
    out = []
    i, n = 0, len(src)
    while i < n:
        ch = src[i]
        if ch == '"':
            j = i + 1
            while j < n and src[j] != '"' and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            end = j + 1 if (j < n and src[j] == '"') else j
            out.append(src[i:end])
            i = end
            continue
        if ch == "#" or src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append("\n" * src.count("\n", i, j))
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def block_end(text, open_idx):
    """Index of the brace that closes the brace at open_idx, or -1."""
    depth, in_str, esc = 0, False, False
    for i in range(open_idx, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def top_level(body):
    """Return body with the contents of nested {...} blocks blanked (same length)."""
    out, depth, in_str, esc = [], 0, False, False
    for ch in body:
        if ch == "\n":
            out.append(ch)
            continue
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            out.append(" " if depth else ch)
            continue
        if ch == '"':
            in_str = True
        if ch == "{":
            depth += 1
            out.append(" ")
            continue
        if ch == "}":
            depth -= 1
            out.append(" ")
            continue
        out.append(" " if depth else ch)
    return "".join(out)


def attr_expr(body, top, name):
    """Raw expression of a top-level attribute, whitespace collapsed, or None."""
    m = re.search(r"^[ \t]*" + name + r"[ \t]*=[ \t]*", top, re.M)
    if m is None:
        return None
    start = m.end()
    depth, in_str, esc, i = 0, False, False, start
    while i < len(body):
        ch = body[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "\n" and depth <= 0:
            break
        i += 1
    return " ".join(body[start:i].split())


def display_text(expr):
    """Unquote a plain string literal; any other expression is returned as written."""
    if expr is None:
        return None
    m = STRING_RE.fullmatch(expr)
    return m.group(1).replace('\\"', '"') if m else expr


def iter_blocks(text, fname):
    pos = 0
    while True:
        m = BLOCK_RE.search(text, pos)
        if m is None:
            return
        end = block_end(text, m.end() - 1)
        if end < 0:
            fail("unbalanced braces in " + fname)
        yield m.group(1), m.group(2), text[m.end():end]
        pos = end + 1


def parse_providers(text, fname):
    found = []
    m = PROVIDER_RE.search(text)
    if m is None:
        return found
    end = block_end(text, m.end() - 1)
    if end < 0:
        fail("unbalanced braces in " + fname)
    inner = text[m.end():end]
    pos = 0
    while True:
        e = ENTRY_RE.search(inner, pos)
        if e is None:
            break
        close = block_end(inner, e.end() - 1)
        if close < 0:
            fail("unbalanced braces in " + fname)
        body = inner[e.end():close]
        top = top_level(body)
        source = display_text(attr_expr(body, top, "source")) or "-"
        version = display_text(attr_expr(body, top, "version")) or "-"
        found.append((e.group(1), source, version))
        pos = close + 1
    return found


def code_cell(value):
    if value is None:
        return "-"
    return "`" + str(value).replace("|", "\\|").replace("`", "'") + "`"


def text_cell(value):
    if value is None:
        return "-"
    return str(value).replace("|", "\\|")


def build_markdown(module_name, file_count, variables, outputs, providers, resource_counts, findings):
    lines = [
        "# Module " + module_name,
        "",
        "Generated by scripts/tf_docs.py from " + str(file_count) + " .tf file(s). "
        "Regular-expression parsing: compare with the source before publishing.",
        "",
        "## Variables",
        "",
    ]
    if variables:
        lines += ["| Name | Type | Default | Required | Description |", "| --- | --- | --- | --- | --- |"]
        for v in variables:
            lines.append("| {} | {} | {} | {} | {} |".format(
                code_cell(v["name"]), code_cell(v["type"]), code_cell(v["default"]),
                "yes" if v["required"] else "no", text_cell(v["description"])))
    else:
        lines.append("None.")
    lines += ["", "## Outputs", ""]
    if outputs:
        lines += ["| Name | Description |", "| --- | --- |"]
        for o in outputs:
            lines.append("| {} | {} |".format(code_cell(o["name"]), text_cell(o["description"])))
    else:
        lines.append("None.")
    lines += ["", "## Providers", ""]
    if providers:
        lines += ["| Name | Source | Version |", "| --- | --- | --- |"]
        for name, source, version in providers:
            lines.append("| {} | {} | {} |".format(code_cell(name), code_cell(source), code_cell(version)))
    else:
        lines.append("None.")
    lines += ["", "## Resources", ""]
    if resource_counts:
        lines += ["| Type | Count |", "| --- | --- |"]
        for rtype in sorted(resource_counts):
            lines.append("| {} | {} |".format(code_cell(rtype), resource_counts[rtype]))
    else:
        lines.append("None.")
    lines += ["", "## Findings", ""]
    if findings:
        for f in findings:
            lines.append("- {}: variable `{}` in `{}` {}.".format(
                f["code"], f["name"], f["file"], FINDING_TEXT[f["code"]]))
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) != 3:
        fail("usage: tf_docs.py <module-dir> <output-file.md>")
    module_dir, out_path = argv[1], argv[2]
    if not os.path.isdir(module_dir):
        fail("module directory not found")
    names = sorted(
        n for n in os.listdir(module_dir)
        if n.endswith(".tf") and os.path.isfile(os.path.join(module_dir, n))
    )
    if not names:
        fail("no .tf files in module directory")
    if os.path.lexists(out_path):
        fail("output file already exists")
    if not os.path.isdir(os.path.dirname(os.path.abspath(out_path))):
        fail("output parent directory not found")

    variables, outputs, findings, providers = [], [], [], []
    resource_counts = {}
    for n in names:
        text = strip_comments(read_tf(os.path.join(module_dir, n), n))
        for kind, name, body in iter_blocks(text, n):
            top = top_level(body)
            desc_expr = attr_expr(body, top, "description")
            if kind == "variable":
                type_expr = attr_expr(body, top, "type")
                default_expr = attr_expr(body, top, "default")
                shown = None
                if default_expr is not None:
                    shown = "(redacted)" if REDACT_NAME.search(name) else default_expr
                variables.append({
                    "name": name, "file": n, "type": type_expr, "default": shown,
                    "required": default_expr is None,
                    "description": display_text(desc_expr),
                })
                if desc_expr is None:
                    findings.append({"code": "VAR_NO_DESCRIPTION", "name": name, "file": n})
                if type_expr is None:
                    findings.append({"code": "VAR_NO_TYPE", "name": name, "file": n})
            else:
                outputs.append({"name": name, "file": n, "description": display_text(desc_expr)})
        providers.extend(parse_providers(text, n))
        for rm in RESOURCE_RE.finditer(text):
            resource_counts[rm.group(1)] = resource_counts.get(rm.group(1), 0) + 1

    module_name = os.path.basename(os.path.abspath(module_dir))
    content = build_markdown(module_name, len(names), variables, outputs, providers,
                             resource_counts, findings)
    try:
        with open(out_path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    except FileExistsError:
        fail("output file already exists")
    except OSError:
        fail("cannot write output file")

    summary = {
        "status": "findings" if findings else "ok",
        "files": len(names),
        "variables": len(variables),
        "outputs": len(outputs),
        "providers": len(providers),
        "resources": sum(resource_counts.values()),
        "resource_types": resource_counts,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(summary) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
