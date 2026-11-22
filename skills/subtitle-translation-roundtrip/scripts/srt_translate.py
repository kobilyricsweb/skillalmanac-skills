"""Prepare SRT subtitle cues for translation and rebuild the SRT afterwards.

Commands:
  extract <input-srt> <output-json>
      Writes the cue texts, timings removed, as numbered JSON for translation.
  rebuild <original-srt> <translated-json> <output-srt>
      Puts translated text back onto the original timings. The SRT is written
      only when no findings exist; otherwise nothing is written and the
      findings are printed.

Output: one JSON object on stdout. Errors: one JSON object on stderr.
Exit codes: 0 ok, 1 findings (no file written), 2 usage or input error.
Stdlib only. No network, no subprocess. Inputs are read-only. Output files
are created with exclusive mode ("x") and are never overwritten.
"""
import argparse
import json
import pathlib
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_LINES = 2  # working value
MAX_LINE_CHARS = 42  # working value
MAX_CPS = 21.0  # working value, characters per second
FORMAT = "srt-cues-v1"
TIMING_RE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


class InputError(Exception):
    """Bad usage or bad input. Maps to exit code 2."""


class Cue(object):
    def __init__(self, cue, timing, start, end, text):
        self.cue = cue
        self.timing = timing
        self.start = start
        self.end = end
        self.text = text


def emit(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def fail(message):
    sys.stderr.write(json.dumps({"error": message}, ensure_ascii=False) + "\n")
    return 2


def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_INPUT_BYTES + 1)
    except OSError:
        raise InputError("input file missing or unreadable")
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input file is larger than 2 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("input file is not valid UTF-8")


def to_seconds(parts):
    h, m, s, ms = [int(x) for x in parts]
    return h * 3600 + m * 60 + s + ms / 1000.0


def parse_srt(text):
    body = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not body:
        raise InputError("SRT file has no cues")
    cues = []
    for block in re.split(r"\n\s*\n", body):
        lines = block.split("\n")
        timing_at = None
        for i, line in enumerate(lines):
            if "-->" in line:
                timing_at = i
                break
        number = len(cues) + 1
        if timing_at is None:
            raise InputError("cue %d has no timing line" % number)
        timing = lines[timing_at].strip()
        match = TIMING_RE.match(timing)
        if not match:
            raise InputError("cue %d has an invalid timing line" % number)
        groups = match.groups()
        start = to_seconds(groups[0:4])
        end = to_seconds(groups[4:8])
        if end <= start:
            raise InputError("cue %d has a zero or negative duration" % number)
        cues.append(Cue(number, timing, start, end, "\n".join(lines[timing_at + 1:])))
    return cues


def load_translation(path):
    text = read_text(path)
    try:
        data = json.loads(text)
    except ValueError:
        raise InputError("translated file is not valid JSON")
    if not isinstance(data, dict) or not isinstance(data.get("cues"), list):
        raise InputError("translated JSON needs a cues list")
    entries = []
    for n, item in enumerate(data["cues"], 1):
        cue_no = item.get("cue") if isinstance(item, dict) else None
        text_value = item.get("text") if isinstance(item, dict) else None
        if not isinstance(cue_no, int) or isinstance(cue_no, bool) or not isinstance(text_value, str):
            raise InputError("cue entry %d needs an integer cue and a string text" % n)
        entries.append((cue_no, text_value.replace("\r", "")))
    return entries


def write_new(path, content, inputs):
    target = pathlib.Path(path).resolve()
    for src in inputs:
        if pathlib.Path(src).resolve() == target:
            raise InputError("output path is the same as an input path")
    try:
        with open(str(target), "x", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    except FileExistsError:
        raise InputError("output file already exists; choose a new path")
    except OSError:
        raise InputError("output path cannot be written")


def check_cues(original, translated):
    findings = []
    if len(translated) != len(original):
        findings.append({
            "cue": None,
            "code": "COUNT_MISMATCH",
            "detail": "translated has %d cues, original has %d"
            % (len(translated), len(original)),
        })
        return findings
    for pos, (orig, (cue_no, text)) in enumerate(zip(original, translated), 1):
        if cue_no != pos:
            findings.append({
                "cue": pos,
                "code": "INDEX_MISMATCH",
                "detail": "expected cue %d at position %d, found %d" % (pos, pos, cue_no),
            })
        if text.strip() == "":
            findings.append({"cue": pos, "code": "EMPTY_CUE", "detail": "translated text is empty"})
            continue
        lines = text.strip("\n").split("\n")
        if any(line.strip() == "" for line in lines):
            findings.append({"cue": pos, "code": "BLANK_LINE", "detail": "text contains an empty line"})
            continue
        if len(lines) > MAX_LINES:
            findings.append({
                "cue": pos,
                "code": "TOO_MANY_LINES",
                "detail": "%d lines, limit %d" % (len(lines), MAX_LINES),
            })
        for idx, line in enumerate(lines, 1):
            if len(line) > MAX_LINE_CHARS:
                findings.append({
                    "cue": pos,
                    "code": "LINE_TOO_LONG",
                    "detail": "line %d has %d characters, limit %d"
                    % (idx, len(line), MAX_LINE_CHARS),
                })
        chars = len(text.replace("\n", ""))
        cps = chars / (orig.end - orig.start)
        if cps > MAX_CPS:
            findings.append({
                "cue": pos,
                "code": "READING_SPEED",
                "detail": "%.1f characters per second, limit %.1f" % (cps, MAX_CPS),
            })
    return findings


def cmd_extract(args):
    cues = parse_srt(read_text(args.input))
    payload = {
        "format": FORMAT,
        "cue_count": len(cues),
        "cues": [{"cue": c.cue, "text": c.text} for c in cues],
    }
    write_new(args.output, json.dumps(payload, ensure_ascii=False, indent=2) + "\n", [args.input])
    emit({"status": "ok", "cue_count": len(cues)})
    return 0


def cmd_rebuild(args):
    original = parse_srt(read_text(args.original))
    translated = load_translation(args.translated)
    findings = check_cues(original, translated)
    report = {
        "status": "findings" if findings else "ok",
        "cue_count_original": len(original),
        "cue_count_translated": len(translated),
        "findings": findings,
    }
    if findings:
        emit(report)
        return 1
    blocks = []
    for pos, (orig, (_, text)) in enumerate(zip(original, translated), 1):
        blocks.append("%d\n%s\n%s\n" % (pos, orig.timing, text.strip("\n")))
    write_new(args.output, "\n".join(blocks), [args.original, args.translated])
    emit(report)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="SRT translation roundtrip helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("extract", help="SRT to numbered cue JSON")
    ex.add_argument("input")
    ex.add_argument("output")
    rb = sub.add_parser("rebuild", help="translated cue JSON back to SRT")
    rb.add_argument("original")
    rb.add_argument("translated")
    rb.add_argument("output")
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            return cmd_extract(args)
        return cmd_rebuild(args)
    except InputError as exc:
        return fail(str(exc))


if __name__ == "__main__":
    sys.exit(main())
