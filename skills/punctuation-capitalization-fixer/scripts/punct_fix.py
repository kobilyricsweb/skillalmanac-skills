"""Fix spacing, punctuation and sentence capitalization in a plain text file.

Usage:
    python -I scripts/punct_fix.py <input-file> <output-file>

Reads <input-file> (UTF-8, at most 2 MB) and writes the corrected text to
<output-file>. The output file is created exclusively: an existing path is
refused and never overwritten. Prints one JSON line listing every change with
its line number.

Exit codes: 0 no changes, 1 changes made, 2 usage or input error (one-line
JSON error on stderr).

Standard library only. No network, no subprocess, no eval or exec.
Code spans, URLs and email addresses are protected and never changed.
"""
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
CONTEXT = 12
PH_OPEN = ""
PH_CLOSE = ""
PH_RE = re.compile(PH_OPEN + r"(\d+)" + PH_CLOSE)

PROTECT_RE = re.compile(
    r"`[^`\n]*`"
    r"|\b(?:https?://|www\.)[^\s<>\"']+"
    r"|[\w.+-]+@[\w-]+(?:\.[\w-]+)+"
)

# Working value: abbreviations after which a period does not end a sentence.
ABBREVIATIONS = {
    "e.g", "i.e", "etc", "vs", "approx", "mr", "mrs", "ms", "dr", "st",
    "jr", "sr", "no", "inc", "ltd", "co", "al", "cf", "fig", "vol", "ex", "et",
}


def protect(line, store):
    def repl(m):
        store.append(m.group(0))
        return PH_OPEN + str(len(store) - 1) + PH_CLOSE
    return PROTECT_RE.sub(repl, line)


def restore(text, store):
    return PH_RE.sub(lambda m: store[int(m.group(1))], text)


def _fn_delete(m, work):
    return ""


def _fn_single_space(m, work):
    return " "


def _fn_repeated(m, work):
    if m.group(1) is not None:
        return m.group(1)
    s = m.group(0)
    if len(s) == 2:
        return "."
    return "..."


def _fn_add_space(m, work):
    return m.group(0) + " "


def _fn_capitalize(m, work):
    pre = m.group("pre")
    word = m.group("word")
    if pre and m.start("pre") > 0:
        prev = work[:m.start("pre")]
        tok = re.search(r"(\S*)\.$", prev)
        if tok and tok.group(1).lower() in ABBREVIATIONS:
            return None
    return pre + word[0].upper() + word[1:]


def _fn_standalone_i(m, work):
    return "I"


RULES = [
    ("space_before_punct",
     re.compile(r"(?<=[^\d\s])[ ]+(?=[,.;:!?])"), _fn_delete),
    ("double_space",
     re.compile(r"(?<=\S)[ ]{2,}(?=\S)"), _fn_single_space),
    ("repeated_punct",
     re.compile(r"([!?,;:])\1+|\.{4,}|(?<!\.)\.\.(?!\.)"), _fn_repeated),
    ("missing_space_after",
     re.compile(r"(?<=[^\W\d_])[,;:](?=[^\W\d_])"), _fn_add_space),
    ("missing_space_after_terminal",
     re.compile(r"(?<=[a-z])\.(?=[A-Z][a-z])|(?<=[^\W\d_])[!?](?=[^\W\d_])"),
     _fn_add_space),
    ("capitalize_sentence",
     re.compile(r"(?P<pre>^[ \t]*|(?<=[.!?])[ ]+)(?P<word>[a-z]+)"
                r"(?![\w'\-])(?=[ ]+(?:[^\W\d_]|)|[.,;:!?]|$)"),
     _fn_capitalize),
    ("standalone_i",
     re.compile(r"(?<![\w'.\-/@])i(?![\w\-/@]|\.[A-Za-z])"), _fn_standalone_i),
]


def run_rule(work, name, regex, fn, line_no, store, events):
    pieces = []
    last = 0
    for m in regex.finditer(work):
        new = fn(m, work)
        if new is None or new == m.group(0):
            continue
        pieces.append(work[last:m.start()])
        pieces.append(new)
        last = m.end()
        lo = max(0, m.start() - CONTEXT)
        before = work[lo:m.end() + CONTEXT]
        after = work[lo:m.start()] + new + work[m.end():m.end() + CONTEXT]
        events.append({
            "line": line_no,
            "rule": name,
            "before": restore(before, store),
            "after": restore(after, store),
        })
    pieces.append(work[last:])
    return "".join(pieces)


def fix_line(line, line_no, events):
    store = []
    work = protect(line, store)
    for name, regex, fn in RULES:
        work = run_rule(work, name, regex, fn, line_no, store, events)
    return restore(work, store)


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def main(argv):
    if len(argv) != 3:
        fail("usage: punct_fix.py <input-file> <output-file>")
    in_path, out_path = argv[1], argv[2]
    if not os.path.isfile(in_path):
        fail("input file not found")
    try:
        with open(in_path, "rb") as fh:
            raw = fh.read(MAX_BYTES + 1)
    except OSError:
        fail("cannot read input file")
    if len(raw) > MAX_BYTES:
        fail("input exceeds 2 MB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    if PH_OPEN in text or PH_CLOSE in text:
        fail("input contains reserved private-use characters U+E000 or U+E001")
    if os.path.abspath(out_path) == os.path.abspath(in_path):
        fail("output path must differ from input path")
    if os.path.exists(out_path):
        fail("output file already exists; refusing to overwrite")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    if not os.path.isdir(out_dir):
        fail("output folder does not exist")

    parts = re.split(r"(\r\n|\n|\r)", text)
    events = []
    rebuilt = []
    for i in range(0, len(parts), 2):
        content = parts[i]
        sep = parts[i + 1] if i + 1 < len(parts) else ""
        rebuilt.append(fix_line(content, i // 2 + 1, events))
        rebuilt.append(sep)
    out_text = "".join(rebuilt)

    try:
        with open(out_path, "x", encoding="utf-8", newline="") as fh:
            fh.write(out_text)
    except FileExistsError:
        fail("output file already exists; refusing to overwrite")
    except OSError:
        fail("cannot write output file")

    result = {
        "status": "changed" if events else "unchanged",
        "change_count": len(events),
        "output": out_path,
        "changes": events,
    }
    sys.stdout.write(json.dumps(result) + "\n")
    return 1 if events else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
