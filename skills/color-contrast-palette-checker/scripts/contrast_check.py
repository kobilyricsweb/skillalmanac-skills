#!/usr/bin/env python3
"""Check foreground/background colour pairs against WCAG 2.x contrast thresholds.

Reads a text file with one colour pair per line in the form
    foreground,background[,label]
where each colour is a hex value written as #rgb or #rrggbb. Blank lines are
skipped. For every pair the script computes the WCAG 2.x contrast ratio and
reports pass/fail for normal text (4.5), large text (3), UI components (3)
and AAA normal text (7). For each pair that fails normal text it also suggests
the nearest foreground colour, found by moving HSL lightness in small steps
while keeping hue and saturation, that reaches 4.5.

Standard library only. No network access, no subprocess, no eval or exec.
The input file is opened read-only and never written.

Exit codes: 0 all pairs pass normal text, 1 at least one pair fails normal
text, 2 usage or input error (a single JSON line is printed on stdout).
"""

import argparse
import colorsys
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_PAIRS = 500
MAX_LABEL_CHARS = 80
LIGHTNESS_STEP = 0.002

THRESHOLD_AA_NORMAL = 4.5
THRESHOLD_AA_LARGE = 3.0
THRESHOLD_UI = 3.0
THRESHOLD_AAA_NORMAL = 7.0

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


class InputError(Exception):
    def __init__(self, message, line=None):
        super().__init__(message)
        self.message = message
        self.line = line


def parse_hex(text, line_no):
    if not HEX_RE.match(text):
        raise InputError("invalid hex colour: %r (use #rgb or #rrggbb)" % text, line_no)
    body = text[1:]
    if len(body) == 3:
        body = "".join(ch * 2 for ch in body)
    return (int(body[0:2], 16), int(body[2:4], 16), int(body[4:6], 16))


def to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def _channel(value):
    c = value / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = (_channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    l1 = relative_luminance(fg)
    l2 = relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _walk(fg, bg, direction):
    """Walk HSL lightness from the foreground in one direction.

    Returns (rgb, distance) for the first colour reaching AA normal text, or
    None when the walk hits the end of the lightness range first.
    """
    h, lightness, s = colorsys.rgb_to_hls(*(v / 255.0 for v in fg))
    start = lightness
    current = lightness
    while True:
        current += direction * LIGHTNESS_STEP
        if current < 0.0:
            current = 0.0
        if current > 1.0:
            current = 1.0
        r, g, b = colorsys.hls_to_rgb(h, current, s)
        rgb = (round(r * 255), round(g * 255), round(b * 255))
        if contrast_ratio(rgb, bg) >= THRESHOLD_AA_NORMAL:
            return rgb, abs(current - start)
        if current in (0.0, 1.0):
            return None


def suggest_foreground(fg, bg):
    """Return (hex, ratio) for the nearest passing foreground, or (None, None)."""
    fg_lum = relative_luminance(fg)
    bg_lum = relative_luminance(bg)
    # Darker foreground increases contrast when the background is lighter.
    preferred = -1 if bg_lum >= fg_lum else 1
    candidates = []
    for direction in (preferred, -preferred):
        found = _walk(fg, bg, direction)
        if found is not None:
            candidates.append(found)
    if not candidates:
        return None, None
    rgb, _distance = min(candidates, key=lambda item: item[1])
    return to_hex(rgb), round(contrast_ratio(rgb, bg), 2)


def read_pairs(path):
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise InputError("cannot read input file: %s" % exc.strerror)
    if size > MAX_INPUT_BYTES:
        raise InputError("input file exceeds 2 MB limit (%d bytes)" % size)
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise InputError("cannot read input file: %s" % exc.strerror)
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("input file exceeds 2 MB limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("input file is not valid UTF-8")
    bom = chr(0xFEFF)
    if text.startswith(bom):
        text = text[1:]

    pairs = []
    for line_no, raw_line in enumerate(text.split("\n"), start=1):
        line = raw_line.rstrip("\r")
        if not line.strip():
            continue
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in line):
            raise InputError("control character in line", line_no)
        parts = [p.strip() for p in line.split(",", 2)]
        if len(parts) < 2:
            raise InputError("expected foreground,background[,label]", line_no)
        fg = parse_hex(parts[0], line_no)
        bg = parse_hex(parts[1], line_no)
        label = parts[2] if len(parts) == 3 and parts[2] else "pair %d" % (len(pairs) + 1)
        if len(label) > MAX_LABEL_CHARS:
            raise InputError("label longer than %d characters" % MAX_LABEL_CHARS, line_no)
        pairs.append({"line": line_no, "label": label, "fg": fg, "bg": bg})
        if len(pairs) > MAX_PAIRS:
            raise InputError("more than %d pairs in one file" % MAX_PAIRS, line_no)
    if not pairs:
        raise InputError("no colour pairs found")
    return pairs


def check(pairs):
    results = []
    fail_count = 0
    for item in pairs:
        ratio = contrast_ratio(item["fg"], item["bg"])
        aa_normal = ratio >= THRESHOLD_AA_NORMAL
        suggestion = None
        suggestion_ratio = None
        if not aa_normal:
            fail_count += 1
            suggestion, suggestion_ratio = suggest_foreground(item["fg"], item["bg"])
        results.append({
            "line": item["line"],
            "label": item["label"],
            "foreground": to_hex(item["fg"]),
            "background": to_hex(item["bg"]),
            "ratio": round(ratio, 2),
            "aa_normal": aa_normal,
            "aa_large": ratio >= THRESHOLD_AA_LARGE,
            "ui_component": ratio >= THRESHOLD_UI,
            "aaa_normal": ratio >= THRESHOLD_AAA_NORMAL,
            "suggestion": suggestion,
            "suggestion_ratio": suggestion_ratio,
        })
    summary = {
        "pairs": len(results),
        "fail_aa_normal": fail_count,
        "pass_aa_normal": len(results) - fail_count,
    }
    return results, summary


def build_parser():
    parser = argparse.ArgumentParser(
        description="Check colour pairs against WCAG 2.x contrast thresholds."
    )
    parser.add_argument("input", help="text file with foreground,background[,label] lines")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        pairs = read_pairs(args.input)
    except InputError as exc:
        error = {"status": "error", "message": exc.message}
        if exc.line is not None:
            error["line"] = exc.line
        sys.stdout.write(json.dumps(error) + "\n")
        return 2
    results, summary = check(pairs)
    report = {
        "status": "ok",
        "thresholds": {
            "aa_normal": THRESHOLD_AA_NORMAL,
            "aa_large": THRESHOLD_AA_LARGE,
            "ui_component": THRESHOLD_UI,
            "aaa_normal": THRESHOLD_AAA_NORMAL,
        },
        "pairs": results,
        "summary": summary,
    }
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 1 if summary["fail_aa_normal"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
