"""Build a small palette from one seed color and check WCAG text contrast.

Reads one hex seed (argument or first non-empty line of a text file), keeps the
seed hue and saturation, and emits five lightness steps (15, 30, 50, 70, 90
percent) plus a complement and an analogous color (+30 degrees), all at the
seed's own lightness for the two harmony colors. For each color it reports the
WCAG 2.x contrast ratio against white and against black and a label.

Usage:
  python -I scripts/palette.py <hex-seed> [--format table|json] [--min-ratio N]
  python -I scripts/palette.py --seed-file <input-file> [--format table|json] [--min-ratio N]

Exit codes: 0 ok, 1 findings (a color has no text pairing at or above
--min-ratio), 2 usage or input error. Errors go to stderr as one line of JSON.
The script reads its input only and writes nothing to disk.
"""

import argparse
import colorsys
import json
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
STEPS = (15, 30, 50, 70, 90)  # HSL lightness in percent; working values
HARMONY = (("complement", 180.0), ("analogous-30", 30.0))  # hue offsets in degrees
DEFAULT_MIN_RATIO = 7.0  # working value for the finding threshold (AAA)
HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


class PaletteError(Exception):
    """Raised for any usage or input problem; main() turns it into exit 2."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class JsonArgParser(argparse.ArgumentParser):
    """Argument parser that reports problems as PaletteError instead of usage text."""

    def error(self, message):
        raise PaletteError("E_USAGE", message)


def parse_hex(text):
    match = HEX_RE.match(text.strip())
    if not match:
        raise PaletteError("E_BAD_HEX", "seed must be 6 hex digits with an optional leading #")
    digits = match.group(1)
    return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#%02x%02x%02x" % rgb


def to_int_rgb(rgb_unit):
    out = []
    for value in rgb_unit:
        scaled = int(round(value * 255))
        out.append(min(255, max(0, scaled)))
    return tuple(out)


def build_palette(seed_rgb):
    h, _l, s = colorsys.rgb_to_hls(*(c / 255.0 for c in seed_rgb))
    colors = []
    for pct in STEPS:
        colors.append(("step-%d" % pct, to_int_rgb(colorsys.hls_to_rgb(h, pct / 100.0, s))))
    seed_l = colorsys.rgb_to_hls(*(c / 255.0 for c in seed_rgb))[1]
    for name, degrees in HARMONY:
        hue = (h + degrees / 360.0) % 1.0
        colors.append((name, to_int_rgb(colorsys.hls_to_rgb(hue, seed_l, s))))
    return colors


def channel_linear(value):
    c = value / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
    r, g, b = (channel_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(lum_a, lum_b):
    hi, lo = max(lum_a, lum_b), min(lum_a, lum_b)
    return (hi + 0.05) / (lo + 0.05)


def label_for(ratio):
    # WCAG 2.x published thresholds.
    if ratio >= 7.0:
        return "AAA"
    if ratio >= 4.5:
        return "AA"
    if ratio >= 3.0:
        return "AA-large"
    return "fail"


def read_seed_file(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_INPUT_BYTES + 1)
    except FileNotFoundError:
        raise PaletteError("E_FILE_NOT_FOUND", "seed file does not exist")
    except OSError:
        raise PaletteError("E_FILE_READ", "seed file cannot be read")
    if len(data) > MAX_INPUT_BYTES:
        raise PaletteError("E_FILE_TOO_LARGE", "seed file is larger than 2 MB")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise PaletteError("E_FILE_ENCODING", "seed file is not valid UTF-8")
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    raise PaletteError("E_FILE_EMPTY", "seed file has no non-empty line")


def analyse(seed_text, min_ratio):
    seed_rgb = parse_hex(seed_text)
    rows = []
    findings = []
    for name, rgb in build_palette(seed_rgb):
        lum = relative_luminance(rgb)
        white = contrast_ratio(lum, 1.0)
        black = contrast_ratio(lum, 0.0)
        best_text = "white" if white >= black else "black"
        best = max(white, black)
        if best < min_ratio:
            findings.append(name)
        rows.append({
            "name": name,
            "hex": to_hex(rgb),
            "white_ratio": round(white, 2),
            "white_label": label_for(white),
            "black_ratio": round(black, 2),
            "black_label": label_for(black),
            "best_text": best_text,
            "best_ratio": round(best, 2),
        })
    return {
        "seed": to_hex(seed_rgb),
        "min_ratio": min_ratio,
        "colors": rows,
        "findings": findings,
    }


def render_table(result):
    lines = []
    lines.append("seed %s  min-ratio %.2f" % (result["seed"], result["min_ratio"]))
    lines.append("%-14s %-8s %6s %-9s %6s %-9s %-6s" % (
        "name", "hex", "white", "label", "black", "label", "best"))
    for row in result["colors"]:
        lines.append("%-14s %-8s %6.2f %-9s %6.2f %-9s %-6s" % (
            row["name"], row["hex"], row["white_ratio"], row["white_label"],
            row["black_ratio"], row["black_label"], row["best_text"]))
    if result["findings"]:
        lines.append("findings: " + ", ".join(result["findings"]))
    else:
        lines.append("findings: none")
    return "\n".join(lines) + "\n"


def main(argv):
    parser = JsonArgParser(prog="palette.py", description="Palette from one seed color.")
    parser.add_argument("seed", nargs="?", help="hex seed, for example #2a6fdb")
    parser.add_argument("--seed-file", help="text file; its first non-empty line is the seed")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--min-ratio", type=float, default=DEFAULT_MIN_RATIO,
                        help="finding threshold, 1 to 21 (default 7.0)")
    args = parser.parse_args(argv)

    if (args.seed is None) == (args.seed_file is None):
        raise PaletteError("E_USAGE", "give exactly one of <hex-seed> or --seed-file")
    if not 1.0 <= args.min_ratio <= 21.0:
        raise PaletteError("E_USAGE", "--min-ratio must be between 1 and 21")

    seed_text = args.seed if args.seed is not None else read_seed_file(args.seed_file)
    result = analyse(seed_text, args.min_ratio)

    if args.format == "json":
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
    else:
        sys.stdout.write(render_table(result))
    return 1 if result["findings"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except PaletteError as exc:
        sys.stderr.write(json.dumps({"error": exc.message, "code": exc.code}) + "\n")
        sys.exit(2)
