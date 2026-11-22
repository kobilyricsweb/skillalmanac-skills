"""srt_check.py: validate an SRT subtitle file and optionally write a repaired copy.

Checks each cue for: start earlier than a previous cue (out_of_order), start
before an earlier cue has ended (overlap), end not after start
(non_positive_duration), duration under 1.0 s (too_short) or over 7.0 s
(too_long), reading speed over 20 characters per second (too_fast), a line
over 42 characters (line_too_long), and more than 2 lines (too_many_lines).
A block without a valid timing line is reported as unparseable_block.

With --fix, a repaired copy is written to a NEW path. The only repairs are:
sort cues by start time (stable), trim each cue end to the next cue start when
it overlaps, renumber from 1. Every other problem is reported, not changed.
The input file is never written.

Usage:
  python -I scripts/srt_check.py INPUT.srt
  python -I scripts/srt_check.py INPUT.srt --fix [--out OUTPUT.srt] [--force]

Exit codes: 0 no issues, 1 issues found (also when --fix ran), 2 usage or input error.
Output: one JSON document on stdout. Errors are one JSON line with keys error and detail.
Stdlib only. No network, no subprocess, no eval. The script reads SRT text only and
parses no JSON, so there is no nesting to cap.
"""
import argparse
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_CPS = 20.0
MIN_DUR_S = 1.0
MAX_DUR_S = 7.0
MAX_LINE_CHARS = 42
MAX_LINES = 2

TIME_RE = re.compile(
    r"^\s*(\d{1,3}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*(\d{1,3}):(\d{2}):(\d{2})[,.](\d{1,3})"
)
INDEX_RE = re.compile(r"^\s*\d+\s*$")


class InputError(Exception):
    def __init__(self, code, detail):
        super().__init__(code)
        self.code = code
        self.detail = detail


def read_input(path):
    if not os.path.exists(path):
        raise InputError("file_not_found", "no such file")
    if not os.path.isfile(path):
        raise InputError("not_a_file", "path is not a regular file")
    if os.path.getsize(path) > MAX_BYTES:
        raise InputError("input_too_large", "limit is %d bytes" % MAX_BYTES)
    with open(path, "rb") as fh:
        raw = fh.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise InputError("input_too_large", "limit is %d bytes" % MAX_BYTES)
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("invalid_utf8", "bad byte at offset %d" % exc.start)


def to_ms(h, m, s, frac):
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(frac.ljust(3, "0")[:3])


def fmt(ms):
    h, rem = divmod(ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, milli = divmod(rem, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, milli)


def issue(cue, code, detail):
    return {"cue": cue, "code": code, "detail": detail}


def parse(text):
    """Return (cues, bad). Cue numbers are 1-based block ordinals in file order."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks, current = [], []
    for line in text.split("\n"):
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    cues, bad = [], []
    for ordinal, block in enumerate(blocks, start=1):
        lines = block
        if len(lines) > 1 and INDEX_RE.match(lines[0]):
            lines = lines[1:]
        m = TIME_RE.match(lines[0])
        if not m:
            bad.append(issue(ordinal, "unparseable_block", "no valid timing line"))
            continue
        g = m.groups()
        if any(int(g[i]) >= 60 for i in (1, 2, 5, 6)):
            bad.append(issue(ordinal, "unparseable_block", "minutes or seconds of 60 or more"))
            continue
        cues.append({
            "cue": ordinal,
            "start": to_ms(g[0], g[1], g[2], g[3]),
            "end": to_ms(g[4], g[5], g[6], g[7]),
            "lines": lines[1:],
        })
    return cues, bad


def check(cues):
    issues = []
    prev = None
    max_end, max_end_cue = None, None
    for c in cues:
        k = c["cue"]
        if prev is not None and c["start"] < prev["start"]:
            issues.append(issue(k, "out_of_order", "starts %s, earlier than cue %d which starts %s"
                                % (fmt(c["start"]), prev["cue"], fmt(prev["start"]))))
        if max_end is not None and c["start"] < max_end:
            issues.append(issue(k, "overlap", "starts %s, before cue %d ends %s"
                                % (fmt(c["start"]), max_end_cue, fmt(max_end))))
        if max_end is None or c["end"] > max_end:
            max_end, max_end_cue = c["end"], k

        dur = c["end"] - c["start"]
        if dur <= 0:
            issues.append(issue(k, "non_positive_duration", "end %s is not after start %s"
                                % (fmt(c["end"]), fmt(c["start"]))))
        else:
            secs = dur / 1000.0
            if secs < MIN_DUR_S:
                issues.append(issue(k, "too_short", "%.3f s, minimum 1.000 s" % secs))
            elif secs > MAX_DUR_S:
                issues.append(issue(k, "too_long", "%.3f s, maximum 7.000 s" % secs))
            chars = sum(len(x) for x in c["lines"])
            cps = chars / secs
            if cps > MAX_CPS:
                issues.append(issue(k, "too_fast", "%.1f characters per second, maximum 20.0" % cps))

        long_lines = [str(i) for i, x in enumerate(c["lines"], start=1) if len(x) > MAX_LINE_CHARS]
        if long_lines:
            issues.append(issue(k, "line_too_long", "line(s) %s over 42 characters" % ", ".join(long_lines)))
        if len(c["lines"]) > MAX_LINES:
            issues.append(issue(k, "too_many_lines", "%d lines, maximum 2" % len(c["lines"])))
        prev = c
    return issues


def repair(cues):
    ordered = sorted(cues, key=lambda c: c["start"])
    reordered = [c["cue"] for c in cues] != [c["cue"] for c in ordered]
    fixed = [dict(c) for c in ordered]
    trimmed = 0
    for i in range(len(fixed) - 1):
        nxt_start = fixed[i + 1]["start"]
        if fixed[i]["end"] > nxt_start:
            fixed[i]["end"] = nxt_start
            trimmed += 1
    for n, c in enumerate(fixed, start=1):
        c["cue"] = n
    return fixed, reordered, trimmed


def default_out(path):
    root, _ = os.path.splitext(path)
    return root + ".fixed.srt"


def check_output_path(inp, out, force):
    if os.path.isdir(out):
        raise InputError("output_is_directory", "--out must be a file path")
    if os.path.normcase(os.path.realpath(out)) == os.path.normcase(os.path.realpath(inp)):
        raise InputError("output_equals_input", "refusing to write over the input file")
    if os.path.exists(out) and os.path.samefile(out, inp):
        raise InputError("output_equals_input", "refusing to write over the input file")
    if not os.path.isdir(os.path.dirname(os.path.abspath(out))):
        raise InputError("output_dir_missing", "parent folder of --out does not exist")
    if os.path.exists(out) and not force:
        raise InputError("output_exists", "file exists; pass --force to replace it (never the input)")


def write_srt(path, cues, force):
    parts = []
    for c in cues:
        parts.append("%d\n%s --> %s\n%s\n\n" % (c["cue"], fmt(c["start"]), fmt(c["end"]), "\n".join(c["lines"])))
    data = "".join(parts)
    try:
        with open(path, "w" if force else "x", encoding="utf-8", newline="\n") as fh:
            fh.write(data)
    except FileExistsError:
        raise InputError("output_exists", "file exists; pass --force to replace it (never the input)")


def run(argv):
    ap = argparse.ArgumentParser(description="Validate an SRT file; --fix writes a repaired copy.")
    ap.add_argument("input", help="path to the .srt file (read only)")
    ap.add_argument("--fix", action="store_true", help="write a repaired copy")
    ap.add_argument("--out", help="new output path for --fix (default: INPUT.fixed.srt)")
    ap.add_argument("--force", action="store_true", help="allow replacing an existing output file, never the input")
    args = ap.parse_args(argv)
    if (args.out or args.force) and not args.fix:
        raise InputError("options_need_fix", "--out and --force only apply with --fix")

    text = read_input(args.input)
    cues, bad = parse(text)
    if not cues:
        raise InputError("no_cues", "no cue with a valid timing line found")

    issues = sorted(bad + check(cues), key=lambda d: d["cue"])
    result = {
        "input": args.input,
        "block_count": len(cues) + len(bad),
        "cue_count": len(cues),
        "issue_count": len(issues),
        "issues": issues,
        "fix": None,
    }

    if args.fix:
        out = args.out or default_out(args.input)
        check_output_path(args.input, out, args.force)
        if bad:
            raise InputError("fix_refused_unparseable",
                             "%d unparseable block(s); --fix needs a fully parseable file" % len(bad))
        fixed, reordered, trimmed = repair(cues)
        remaining = check(fixed)
        write_srt(out, fixed, args.force)
        result["fix"] = {
            "output": out,
            "cue_count": len(fixed),
            "reordered": reordered,
            "overlaps_trimmed": trimmed,
            "renumbered": True,
            "remaining_issue_count": len(remaining),
            "remaining_issues": remaining,
        }

    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    return 1 if issues else 0


if __name__ == "__main__":
    try:
        sys.exit(run(sys.argv[1:]))
    except InputError as exc:
        sys.stdout.write(json.dumps({"error": exc.code, "detail": exc.detail}) + "\n")
        sys.exit(2)
    except OSError as exc:
        sys.stdout.write(json.dumps({"error": "io_error", "detail": str(exc.strerror or "I/O error")}) + "\n")
        sys.exit(2)
