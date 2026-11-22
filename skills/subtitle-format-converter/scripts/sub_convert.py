"""Convert a WebVTT or SRT caption file to WebVTT, SRT, or a plain transcript.

Command line:
  python -I scripts/sub_convert.py --input <input-file> --to {srt,vtt,txt} --output <output-file> [--merge-rolling]

Reads one caption file of at most 2,097,152 bytes and writes a new output file.
The output path must not exist yet. Stdlib only; no network, no subprocess.
Exit codes: 0 ok, 1 findings (output is still written), 2 usage or input error.
A success report is one JSON line on stdout; an error is one JSON line on stderr.
"""

import argparse
import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
TS_RE = re.compile(r"^(?:(\d+):)?([0-5]\d):([0-5]\d)[.,](\d{3})$", re.ASCII)
TIMING_RE = re.compile(r"^(\S+)\s+-->\s+(\S+)(?:\s.*)?$")
NON_CUE_RE = re.compile(r"^(NOTE|STYLE|REGION)(\s|$)")
TAG_RE = re.compile(r"<(/?)([^>]*)>")
BR_RE = re.compile(r"<br\s*/?>", re.IGNORECASE)
KEPT_TAG_NAMES = ("b", "i", "u")
SPACE_RE = re.compile(r"\s+")


def fail(code, message, **extra):
    payload = {"error": message, "code": code}
    payload.update(extra)
    sys.stderr.write(json.dumps(payload) + "\n")
    sys.exit(2)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        fail("USAGE", message)


def read_text(path):
    if not os.path.exists(path):
        fail("FILE_NOT_FOUND", "input file does not exist")
    if not os.path.isfile(path):
        fail("NOT_A_FILE", "input path is not a regular file")
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError:
        fail("READ_ERROR", "input file cannot be read")
    if len(data) > MAX_BYTES:
        fail("FILE_TOO_LARGE", "input is larger than 2,097,152 bytes")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("NOT_UTF8", "input is not valid UTF-8")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def split_blocks(text):
    blocks, current = [], []
    for line in text.split("\n"):
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def parse_ts(value, block_no):
    match = TS_RE.match(value)
    if not match:
        fail("BAD_TIMING", "timestamp is malformed", block=block_no)
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int(match.group(4))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + millis


def parse(text):
    blocks = split_blocks(text)
    if not blocks:
        fail("NO_CUES", "file has no caption blocks")
    source_format = "vtt" if blocks[0][0].lstrip().startswith("WEBVTT") else "srt"
    cues, dropped = [], 0
    for index, block in enumerate(blocks):
        block_no = index + 1
        if source_format == "vtt" and index == 0:
            continue  # WEBVTT header block
        if source_format == "vtt" and NON_CUE_RE.match(block[0].strip()):
            dropped += 1
            continue
        timing = None
        for line_index, line in enumerate(block):
            if "-->" in line:
                timing = line_index
                break
        if timing is None:
            fail("BAD_BLOCK", "block has no timing line", block=block_no)
        match = TIMING_RE.match(block[timing].strip())
        if not match:
            fail("BAD_TIMING", "timing line is malformed", block=block_no)
        cues.append({
            "start": parse_ts(match.group(1), block_no),
            "end": parse_ts(match.group(2), block_no),
            "raw": block[timing + 1:],
        })
    if not cues:
        fail("NO_CUES", "no cue timing lines found")
    return source_format, cues, dropped


def _tag_repl(match, keep_biu):
    if keep_biu and match.group(2) in KEPT_TAG_NAMES:
        return match.group(0)
    return ""


def clean(line, keep_biu):
    stripped = TAG_RE.sub(lambda m: _tag_repl(m, keep_biu), line)
    return SPACE_RE.sub(" ", stripped).strip()


def cue_lines(cue, keep_biu):
    # A <br> tag is a line break: split on it before tag removal so that
    # adjacent words are not joined.
    lines = []
    for raw in cue["raw"]:
        for piece in BR_RE.split(raw):
            lines.append(clean(piece, keep_biu))
    return [line for line in lines if line]


def fmt_ts(ms, sep):
    hours, rest = divmod(ms, 3600000)
    minutes, rest = divmod(rest, 60000)
    seconds, millis = divmod(rest, 1000)
    return "%02d:%02d:%02d%s%03d" % (hours, minutes, seconds, sep, millis)


def render(cues, target, merge):
    """Return (body, cues_written)."""
    if target in ("srt", "vtt"):
        sep = "," if target == "srt" else "."
        blocks = []
        for cue in cues:
            lines = cue_lines(cue, True)
            if not lines:
                continue
            timing = "%s --> %s" % (fmt_ts(cue["start"], sep), fmt_ts(cue["end"], sep))
            body_text = "\n".join(lines)
            if target == "srt":
                blocks.append("%d\n%s\n%s" % (len(blocks) + 1, timing, body_text))
            else:
                blocks.append("%s\n%s" % (timing, body_text))
        if not blocks:
            return "", 0
        joined = "\n\n".join(blocks) + "\n"
        if target == "vtt":
            joined = "WEBVTT\n\n" + joined
        return joined, len(blocks)
    emitted, previous_last = [], None
    for cue in cues:
        lines = cue_lines(cue, False)
        if not lines:
            continue
        last = lines[-1]
        if merge and previous_last is not None and lines[0] == previous_last:
            lines = lines[1:]
        previous_last = last
        if lines:
            emitted.append(" ".join(lines))
    if not emitted:
        return "", 0
    return "".join(line + "\n" for line in emitted), len(emitted)


def find_problems(cues):
    findings = []
    for number, cue in enumerate(cues, start=1):
        if cue["end"] < cue["start"]:
            findings.append({
                "code": "END_BEFORE_START",
                "cue": number,
                "start": fmt_ts(cue["start"], "."),
                "end": fmt_ts(cue["end"], "."),
            })
    return findings


def write_new(path, body, input_path):
    if os.path.realpath(path) == os.path.realpath(input_path):
        fail("OUTPUT_IS_INPUT", "output path is the input file")
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(parent):
        fail("OUTPUT_DIR_MISSING", "output folder does not exist")
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(body)
    except FileExistsError:
        fail("OUTPUT_EXISTS", "output path already exists; choose a new name")
    except OSError:
        fail("WRITE_ERROR", "output file cannot be written")


def main(argv=None):
    parser = _Parser(description="Convert WebVTT or SRT captions to WebVTT, SRT or plain text.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--to", required=True, choices=["srt", "vtt", "txt"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--merge-rolling", action="store_true")
    args = parser.parse_args(argv)
    if args.merge_rolling and args.to != "txt":
        fail("USAGE", "--merge-rolling applies only with --to txt")
    text = read_text(args.input)
    source_format, cues, dropped = parse(text)
    if source_format == args.to:
        fail("SAME_FORMAT", "input is already in the requested format")
    body, written = render(cues, args.to, args.merge_rolling)
    if written == 0:
        fail("NO_CUES", "no cue has text to write")
    write_new(args.output, body, args.input)
    findings = find_problems(cues)
    report = {
        "input_format": source_format,
        "output_format": args.to,
        "cues_read": len(cues),
        "cues_written": written,
        "blocks_dropped": dropped,
        "output": args.output,
        "findings": findings,
    }
    sys.stdout.write(json.dumps(report) + "\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
