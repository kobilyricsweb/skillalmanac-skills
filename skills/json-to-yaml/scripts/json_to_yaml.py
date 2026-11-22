"""Convert a JSON document to block-style YAML with safe quoting.

Usage:
    python -I scripts/json_to_yaml.py <input-json> <output-yaml>

The input must be a UTF-8 JSON file of at most 2 MiB whose top level is an
object or an array. The YAML uses 2-space block style. Before anything is
written, the YAML text is parsed again by a built-in subset parser and compared
with the input (type- and order-aware). The output file is created only when
that check passes, using exclusive-create mode, so an existing file is never
overwritten and the input path is never used as the output path.

Standard library only. No network, no subprocess, no eval or exec.

Exit codes: 0 written and round trip equal; 1 findings, nothing written;
2 usage or input error, reported as one JSON line on stderr.
"""

import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_DEPTH = 100
RESERVED_WORDS = frozenset(
    ["true", "false", "yes", "no", "on", "off", "y", "n", "null", "~", "=", "<<"]
)
INDICATOR_START = frozenset("-?:,[]{}#&*!|>'\"%@`+.<")
DQ_ESCAPES = {'"': '\\"', "\\": "\\\\", "\n": "\\n", "\t": "\\t", "\r": "\\r"}
DQ_UNESCAPES = {'"': '"', "\\": "\\", "n": "\n", "t": "\t", "r": "\r"}
INT_RE = re.compile(r"-?[0-9]+")
FLOAT_RE = re.compile(r"-?[0-9]+(\.[0-9]+)?([eE][-+]?[0-9]+)?")
HEX4_RE = re.compile(r"[0-9A-Fa-f]{4}")


class InputError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message


class SubsetError(Exception):
    """The built-in subset parser cannot read the emitted text."""


def _unsafe(ch):
    o = ord(ch)
    return (
        o < 32
        or 127 <= o <= 159
        or o in (0x2028, 0x2029, 0xFEFF, 0xFFFE, 0xFFFF)
        or 0xD800 <= o <= 0xDFFF
    )


def _needs_quote(s):
    if s == "" or s.lower() in RESERVED_WORDS:
        return True
    first = s[0]
    if first in INDICATOR_START or first == " " or first.isdigit():
        return True
    if s[-1] == " " or ":" in s or "#" in s:
        return True
    return any(_unsafe(c) for c in s)


def _dq(s):
    out = ['"']
    for c in s:
        if c in DQ_ESCAPES:
            out.append(DQ_ESCAPES[c])
        elif _unsafe(c):
            out.append("\\u%04X" % ord(c))
        else:
            out.append(c)
    out.append('"')
    return "".join(out)


def _literal_lines(s):
    """Return (body lines, chomping indicator) when s can be a literal block."""
    if "\n" not in s or s.endswith("\n\n"):
        return None
    if s.endswith("\n"):
        body, chomp = s[:-1], ""
    else:
        body, chomp = s, "-"
    lines = body.split("\n")
    if lines[0] == "" or lines[-1] == "":
        return None
    for c in body:
        if c != "\n" and _unsafe(c):
            return None
    for ln in lines:
        if ln[:1] in (" ", "\t"):
            return None
        if ln and not ln.strip():
            return None
    return lines, chomp


def _scalar_token(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    return repr(value)


def _leaf_lines(value, indent, prefix):
    if isinstance(value, dict):
        return [prefix + "{}"]
    if isinstance(value, list):
        return [prefix + "[]"]
    if isinstance(value, str):
        literal = _literal_lines(value)
        if literal is not None:
            lines, chomp = literal
            pad = indent + "  "
            return [prefix + "|" + chomp] + [pad + ln if ln else "" for ln in lines]
        if _needs_quote(value):
            return [prefix + _dq(value)]
        return [prefix + value]
    return [prefix + _scalar_token(value)]


def _key_text(key):
    return _dq(key) if _needs_quote(key) else key


def _emit_block(value, indent, out):
    if isinstance(value, dict):
        for key, item in value.items():
            head = indent + _key_text(key)
            if isinstance(item, (dict, list)) and item:
                out.append(head + ":")
                _emit_block(item, indent + "  ", out)
            else:
                out.extend(_leaf_lines(item, indent, head + ": "))
    else:
        for item in value:
            if isinstance(item, (dict, list)) and item:
                sub = []
                _emit_block(item, indent + "  ", sub)
                sub[0] = indent + "- " + sub[0][len(indent) + 2:]
                out.extend(sub)
            else:
                out.extend(_leaf_lines(item, indent, indent + "- "))


def _emit(data):
    if not data:
        return ("{}" if isinstance(data, dict) else "[]") + "\n"
    out = []
    _emit_block(data, "", out)
    return "\n".join(out) + "\n"


def _indent_of(line):
    return len(line) - len(line.lstrip(" "))


def _parse_dq(text, pos):
    out = []
    i = pos + 1
    while True:
        if i >= len(text):
            raise SubsetError("unterminated double-quoted scalar")
        c = text[i]
        if c == '"':
            return "".join(out), i + 1
        if c != "\\":
            out.append(c)
            i += 1
            continue
        nxt = text[i + 1:i + 2]
        if nxt == "u":
            hex4 = text[i + 2:i + 6]
            if not HEX4_RE.fullmatch(hex4):
                raise SubsetError("bad unicode escape")
            out.append(chr(int(hex4, 16)))
            i += 6
        elif nxt in DQ_UNESCAPES:
            out.append(DQ_UNESCAPES[nxt])
            i += 2
        else:
            raise SubsetError("unsupported escape")


def _split_key(text):
    if text.startswith('"'):
        key, end = _parse_dq(text, 0)
        if text[end:end + 1] != ":":
            return None
        after = text[end + 1:]
    else:
        pos = text.find(":")
        if pos < 0:
            return None
        key, after = text[:pos], text[pos + 1:]
    if after == "":
        return key, ""
    if after[:1] == " ":
        return key, after[1:]
    return None


def _parse_scalar(tok):
    if tok == "null":
        return None
    if tok == "true":
        return True
    if tok == "false":
        return False
    if tok == "{}":
        return {}
    if tok == "[]":
        return []
    if tok.startswith('"'):
        value, end = _parse_dq(tok, 0)
        if end != len(tok):
            raise SubsetError("text after quoted scalar")
        return value
    if INT_RE.fullmatch(tok):
        return int(tok)
    if FLOAT_RE.fullmatch(tok):
        return float(tok)
    return tok


def _parse_literal(lines, j, cind, clip):
    start = j
    last = j - 1
    while j < len(lines):
        ln = lines[j]
        if ln == "":
            j += 1
            continue
        if _indent_of(ln) < cind:
            break
        j += 1
        last = j - 1
    content = [lines[k][cind:] if lines[k] else "" for k in range(start, last + 1)]
    text = "\n".join(content)
    if clip:
        text += "\n"
    return text, last + 1


def _parse_leaf(lines, i, tok, parent_indent):
    if tok in ("|", "|-"):
        return _parse_literal(lines, i + 1, parent_indent + 2, tok == "|")
    return _parse_scalar(tok), i + 1


def _parse_map(lines, i, indent):
    result = {}
    while i < len(lines) and _indent_of(lines[i]) == indent:
        body = lines[i][indent:]
        if body == "-" or body.startswith("- "):
            break
        parsed = _split_key(body)
        if parsed is None:
            raise SubsetError("line is not a mapping entry")
        key, rest = parsed
        if key in result:
            raise SubsetError("duplicate key")
        if rest == "":
            if i + 1 >= len(lines) or _indent_of(lines[i + 1]) != indent + 2:
                raise SubsetError("missing nested block")
            value, i = _parse_block(lines, i + 1, indent + 2)
        else:
            value, i = _parse_leaf(lines, i, rest, indent)
        result[key] = value
    return result, i


def _parse_seq(lines, i, indent):
    items = []
    while i < len(lines) and _indent_of(lines[i]) == indent:
        body = lines[i][indent:]
        if not (body == "-" or body.startswith("- ")):
            break
        rest = body[2:]
        if rest == "":
            raise SubsetError("empty sequence item")
        if rest == "-" or rest.startswith("- ") or _split_key(rest) is not None:
            lines[i] = " " * (indent + 2) + rest
            item, i = _parse_block(lines, i, indent + 2)
        else:
            item, i = _parse_leaf(lines, i, rest, indent)
        items.append(item)
    return items, i


def _parse_block(lines, i, indent):
    if i >= len(lines) or _indent_of(lines[i]) != indent:
        raise SubsetError("unexpected indentation")
    body = lines[i][indent:]
    if body == "-" or body.startswith("- "):
        return _parse_seq(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_yaml(text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if lines in (["{}"], ["[]"]):
        return _parse_scalar(lines[0])
    if not lines:
        raise SubsetError("empty output")
    value, end = _parse_block(lines, 0, 0)
    if end != len(lines):
        raise SubsetError("unparsed trailing content")
    return value


def _first_difference(a, b, path):
    if type(a) is not type(b):
        return path
    if isinstance(a, dict):
        if list(a.keys()) != list(b.keys()):
            return path
        for key in a:
            diff = _first_difference(a[key], b[key], path + "." + key)
            if diff is not None:
                return diff
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return path
        for idx in range(len(a)):
            diff = _first_difference(a[idx], b[idx], "%s[%d]" % (path, idx))
            if diff is not None:
                return diff
        return None
    return None if a == b else path


def _no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InputError("DUPLICATE_KEY", "an object repeats a key")
        obj[key] = value
    return obj


def _reject_constant(name):
    raise InputError("BAD_JSON", "NaN and Infinity are not valid JSON")


def _check_depth(value, depth):
    if isinstance(value, (dict, list)):
        if depth > MAX_DEPTH:
            raise InputError("NESTING_TOO_DEEP", "nesting is deeper than 100 levels")
        children = value.values() if isinstance(value, dict) else value
        for child in children:
            _check_depth(child, depth + 1)


def _load_input(path):
    if not os.path.isfile(path):
        raise InputError("FILE_MISSING", "input is not an existing regular file")
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE", "input is larger than 2 MiB")
    with open(path, "rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE", "input is larger than 2 MiB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("NOT_UTF8", "input is not valid UTF-8")
    try:
        data = json.loads(
            text, object_pairs_hook=_no_duplicates, parse_constant=_reject_constant
        )
    except InputError:
        raise
    except (ValueError, RecursionError):
        raise InputError("BAD_JSON", "input is not valid JSON")
    if not isinstance(data, (dict, list)):
        raise InputError("NOT_CONTAINER", "top level must be a JSON object or array")
    _check_depth(data, 1)
    return data


def _check_output(input_path, output_path):
    if os.path.normcase(os.path.realpath(input_path)) == os.path.normcase(
        os.path.realpath(output_path)
    ):
        raise InputError("SAME_PATH", "output path must differ from the input path")
    if os.path.lexists(output_path):
        raise InputError("OUTPUT_EXISTS", "output path already exists; nothing written")
    if not os.path.isdir(os.path.dirname(os.path.abspath(output_path))):
        raise InputError("OUTPUT_DIR_MISSING", "output directory does not exist")


def _error(code, message):
    sys.stderr.write(
        json.dumps({"status": "error", "code": code, "message": message}) + "\n"
    )
    return 2


def main(argv):
    if len(argv) != 3:
        return _error("BAD_USAGE", "usage: json_to_yaml.py <input-json> <output-yaml>")
    input_path, output_path = argv[1], argv[2]
    try:
        data = _load_input(input_path)
        _check_output(input_path, output_path)
    except InputError as err:
        return _error(err.code, err.message)
    yaml_text = _emit(data)
    try:
        echoed = _parse_yaml(yaml_text)
    except SubsetError as err:
        finding = {"code": "SELFCHECK_UNSUPPORTED", "detail": str(err)}
        print(json.dumps({"status": "findings", "written": False, "findings": [finding]}))
        return 1
    diff = _first_difference(data, echoed, "$")
    if diff is not None:
        finding = {"code": "ROUNDTRIP_MISMATCH", "path": diff}
        print(json.dumps({"status": "findings", "written": False, "findings": [finding]}))
        return 1
    try:
        with open(output_path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(yaml_text)
    except FileExistsError:
        return _error("OUTPUT_EXISTS", "output path appeared during the run; nothing written")
    except OSError:
        return _error("OUTPUT_WRITE_FAILED", "could not create the output file")
    summary = {
        "status": "ok",
        "written": True,
        "top_level_entries": len(data),
        "output_lines": yaml_text.count("\n"),
        "round_trip": "equal",
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
