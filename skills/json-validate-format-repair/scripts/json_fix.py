#!/usr/bin/env python3
"""Validate, pretty-print and repair JSON text, listing every repair made.

Command line:
    python -I scripts/json_fix.py <input-file> [--repair] [--sort-keys] [--output <new-file>]

Behavior:
    - Reads <input-file> once: at most 2 MB, UTF-8; a leading BOM is ignored.
    - Prints one JSON report object on stdout.
    - --repair applies only the fixes listed in SKILL.md and refuses anything ambiguous.
    - --output writes the pretty-printed result (2-space indent) to a new file.
      The path must not exist and must not be the input path. No other file is written.

Exit codes: 0 valid with no repair needed; 1 repaired or invalid; 2 usage or input error.
Standard library only. No network access.
"""

import argparse
import json
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
TOKEN_CAP = 40
CLOSER_FOR = {"}": "{", "]": "["}
OPENER_CLOSER = {"{": "}", "[": "]"}
JSON_LITERALS = ("true", "false", "null")
PY_LITERALS = {"True": "true", "False": "false", "None": "null"}


class Refusal(Exception):
    def __init__(self, line, reason):
        Exception.__init__(self, reason)
        self.line = line
        self.reason = reason


def fail(code, detail):
    sys.stderr.write(json.dumps({"error": code, "detail": detail}) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("usage", message)


def read_input(path):
    if not os.path.isfile(path):
        fail("file_not_found", "input is missing or is not a file")
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError as exc:
        fail("read_error", type(exc).__name__)
    if len(raw) > MAX_BYTES:
        fail("input_too_large", "input is over 2097152 bytes")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("invalid_utf8", "input is not valid UTF-8")


def _no_constant(name):
    raise ValueError("non-standard constant " + name)


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key: " + key[:TOKEN_CAP])
        result[key] = value
    return result


def try_parse(text):
    """Return (object, None) when valid, or (None, error dict) when not."""
    try:
        return json.loads(text, parse_constant=_no_constant,
                          object_pairs_hook=_reject_duplicate_keys), None
    except json.JSONDecodeError as exc:
        return None, {"line": exc.lineno, "column": exc.colno, "message": exc.msg}
    except ValueError as exc:
        return None, {"line": None, "column": None, "message": str(exc)}


def repair(text):
    """Return (repaired_text, repairs). Raise Refusal on anything ambiguous."""
    out = []
    repairs = []
    stack = []
    last = ""           # "" at start, "{" or "[" after an opener, "," , ":", "v" after a value or key
    comma_slot = None   # (index into out, line) of the most recent comma
    i = 0
    n = len(text)
    line = 1

    def add(fix, at_line, detail):
        repairs.append({"line": at_line, "fix": fix, "detail": detail})

    def drop_comma():
        index, comma_line = comma_slot
        out[index] = ""
        add("trailing_comma", comma_line, "trailing comma removed")

    while i < n:
        ch = text[i]
        if ch == "\n":
            out.append(ch)
            line += 1
            i += 1
        elif ch in " \t\r":
            out.append(ch)
            i += 1
        elif ch == '"':
            j = i + 1
            while j < n and text[j] not in '"\n':
                j += 2 if text[j] == "\\" else 1
            if j >= n or text[j] == "\n":
                raise Refusal(line, "unterminated string")
            out.append(text[i:j + 1])
            i = j + 1
            last = "v"
        elif ch == "'":
            j = i + 1
            parts = ['"']
            while True:
                if j >= n or text[j] == "\n":
                    raise Refusal(line, "unterminated single-quoted string")
                cur = text[j]
                if cur == "'":
                    break
                if cur == "\\":
                    if text[j + 1:j + 2] != "'":
                        raise Refusal(line, "backslash escape in single-quoted string")
                    parts.append("'")
                    j += 2
                    continue
                parts.append('\\"' if cur == '"' else cur)
                j += 1
            parts.append('"')
            out.append("".join(parts))
            add("single_quotes", line, "single-quoted string converted to double quotes")
            i = j + 1
            last = "v"
        elif ch == "/" and text[i + 1:i + 2] == "/":
            end = text.find("\n", i)
            i = n if end == -1 else end
            add("comment", line, "line comment removed")
        elif ch == "/" and text[i + 1:i + 2] == "*":
            end = text.find("*/", i + 2)
            if end == -1:
                raise Refusal(line, "unterminated block comment")
            block = text[i:end + 2]
            newlines = block.count("\n")
            out.append("\n" * newlines)
            add("comment", line, "block comment removed")
            line += newlines
            i = end + 2
        elif ch in "{[":
            stack.append(ch)
            out.append(ch)
            last = ch
            i += 1
        elif ch in "}]":
            if not stack:
                raise Refusal(line, "closing bracket without opener")
            if stack[-1] != CLOSER_FOR[ch]:
                raise Refusal(line, "mismatched closing bracket")
            if last == ",":
                drop_comma()
            stack.pop()
            out.append(ch)
            last = "v"
            i += 1
        elif ch == ",":
            if last in ("", "{", "[", ",", ":"):
                raise Refusal(line, "comma without a preceding value")
            comma_slot = (len(out), line)
            out.append(ch)
            last = ","
            i += 1
        elif ch == ":":
            out.append(ch)
            last = ":"
            i += 1
        elif ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            word = text[i:j]
            k = j
            while k < n and text[k] in " \t":
                k += 1
            if last in ("{", ",") and text[k:k + 1] == ":":
                out.append('"' + word + '"')
                add("unquoted_key", line, "unquoted key quoted: " + word[:TOKEN_CAP])
            elif word in JSON_LITERALS:
                out.append(word)
            elif word in PY_LITERALS:
                out.append(PY_LITERALS[word])
                add("python_literal", line, word + " replaced with " + PY_LITERALS[word])
            else:
                raise Refusal(line, "unknown bare word: " + word[:TOKEN_CAP])
            i = j
            last = "v"
        elif ch in "-0123456789":
            j = i + 1
            while j < n and text[j] in "0123456789+-.eE":
                j += 1
            out.append(text[i:j])
            i = j
            last = "v"
        else:
            raise Refusal(line, "unexpected character " + repr(ch))

    if last == "," and stack:
        drop_comma()
    end_line = text.count("\n", 0, len(text.rstrip())) + 1
    while stack:
        closer = OPENER_CLOSER[stack.pop()]
        out.append(closer)
        add("missing_closer", end_line, closer + " appended at end of input")
    return "".join(out), repairs


def emit(report):
    sys.stdout.write(json.dumps(report, ensure_ascii=True) + "\n")


def main(argv=None):
    parser = _Parser(prog="json_fix.py", description="Validate, pretty-print and repair JSON.")
    parser.add_argument("input", help="existing JSON file to read")
    parser.add_argument("--repair", action="store_true", help="apply the listed repairs")
    parser.add_argument("--sort-keys", action="store_true", help="sort object keys in --output")
    parser.add_argument("--output", help="new file to write pretty-printed JSON to")
    args = parser.parse_args(argv)

    if args.output is not None:
        out_abs = os.path.normcase(os.path.abspath(args.output))
        if out_abs == os.path.normcase(os.path.abspath(args.input)):
            fail("output_is_input", "output path must differ from the input path")
        if os.path.exists(args.output):
            fail("output_exists", "output path already exists; choose a new name")
        if not os.path.isdir(os.path.dirname(out_abs)):
            fail("output_dir_missing", "output folder does not exist")

    text = read_input(args.input)
    report = {"status": "invalid", "first_error": None, "repairs": [],
              "refused": None, "output": None}

    obj, error = try_parse(text)
    if error is None:
        report["status"] = "valid"
    else:
        report["first_error"] = error
        if args.repair:
            try:
                fixed, repairs = repair(text)
            except Refusal as refusal:
                report["refused"] = {"line": refusal.line, "reason": refusal.reason}
                emit(report)
                sys.exit(1)
            obj, error = try_parse(fixed)
            if error is not None:
                report["refused"] = {"line": error["line"],
                                     "reason": "still invalid after repairs: " + error["message"]}
            else:
                report["repairs"] = repairs
                report["status"] = "repaired" if repairs else "valid"

    if args.output is not None and report["status"] != "invalid":
        pretty = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=args.sort_keys) + "\n"
        try:
            data = pretty.encode("utf-8")
        except UnicodeEncodeError:
            fail("unencodable_text", "result has characters that cannot be written as UTF-8")
        try:
            with open(args.output, "xb") as fh:
                fh.write(data)
        except FileExistsError:
            fail("output_exists", "output path was created during the run")
        except OSError as exc:
            fail("write_error", type(exc).__name__)
        report["output"] = args.output

    emit(report)
    sys.exit(0 if report["status"] == "valid" else 1)


if __name__ == "__main__":
    main()
