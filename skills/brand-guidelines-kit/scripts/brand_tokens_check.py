#!/usr/bin/env python3
"""Validate a brand tokens JSON file and print a strict-JSON report.

Usage:
    python brand_tokens_check.py check <tokens.json>

Reads the one file given. Writes nothing. No network.
Exit codes: 0 no errors (warnings allowed), 1 at least one error, 2 file or JSON problem.

Input shape (see SKILL.md for the full contract):
    {"brand": "Name",
     "colors": [{"name": "Ink", "hex": "#14213D", "role": "text"}, ...],
     "pairs": [{"foreground": "Ink", "background": "Paper", "size": "normal"}],   (optional)
     "type_scale": [{"name": "caption", "size": 12}, ...],   (smallest to largest)
     "spacing": [4, 8, 16, 24]}                              (optional, ascending)
"""
import json
import math
import re
import sys

# Roles every palette must define; without them nothing else can be paired or checked.
REQUIRED_ROLES = ("primary", "background", "text")
# Roles accepted by the checker. Anything else is reported as a warning (typo guard).
KNOWN_ROLES = ("primary", "secondary", "accent", "background", "surface", "text",
               "text-muted", "on-primary", "success", "warning", "danger", "border")
# WCAG 2.x success criterion 1.4.3: 4.5:1 for normal text, 3:1 for large text.
MIN_NORMAL = 4.5
MIN_LARGE = 3.0
# Linearisation breakpoint exactly as printed in the WCAG 2.x definition of relative luminance.
SRGB_BREAK = 0.03928
# Steps closer than a minor second (1.067) are hard to tell apart on screen.
MIN_STEP_RATIO = 1.067
# Below 16 px, body text fails common mobile readability guidance.
MIN_BODY_PX = 16
# A 4 px base grid is the common denominator of the major UI systems.
GRID = 4

HEX_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def normalize_hex(value):
    """Return '#RRGGBB' uppercase, or None when value is not a valid 3 or 6 digit hex."""
    if not isinstance(value, str) or not HEX_RE.match(value):
        return None
    digits = value[1:].upper()
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    return "#" + digits


def luminance(hex6):
    """WCAG relative luminance of a normalised '#RRGGBB' string."""
    channels = []
    for i in (1, 3, 5):
        c = int(hex6[i:i + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= SRGB_BREAK else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(hex_a, hex_b):
    la, lb = luminance(hex_a), luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


class Report:
    def __init__(self):
        self.findings = []

    def add(self, severity, code, path, message):
        self.findings.append({"severity": severity, "code": code, "path": path, "message": message})


def check_colors(data, rep):
    colors = data.get("colors")
    resolved = {}      # name (lower) -> normalised hex
    by_role = {}       # role -> list of (name, hex)
    if not isinstance(colors, list) or not colors:
        rep.add("error", "missing_colors", "colors", "colors must be a non-empty list of {name, hex, role}")
        return resolved, by_role
    seen_hex = {}
    seen_names = set()
    for i, entry in enumerate(colors):
        path = "colors[%d]" % i
        if not isinstance(entry, dict):
            rep.add("error", "bad_color_entry", path, "each colour must be an object with name, hex and role")
            continue
        name = entry.get("name")
        role = entry.get("role")
        if not isinstance(name, str) or not name.strip():
            rep.add("error", "missing_color_name", path, "colour has no name")
            name = "colors[%d]" % i
        hx = normalize_hex(entry.get("hex"))
        if hx is None:
            rep.add("error", "invalid_hex", path + ".hex",
                    "%r is not a hex colour; use #RGB or #RRGGBB" % (entry.get("hex"),))
        key = name.strip().lower()
        if key in seen_names:
            rep.add("error", "duplicate_name", path + ".name", "colour name %r is used twice" % name)
        seen_names.add(key)
        if hx is not None:
            resolved[key] = hx
            if hx in seen_hex and seen_hex[hx] != key:
                rep.add("error", "duplicate_color", path + ".hex",
                        "%s is already used by %r; merge the two or make them different" % (hx, seen_hex[hx]))
            seen_hex.setdefault(hx, key)
        if not isinstance(role, str) or not role.strip():
            rep.add("error", "missing_color_role", path + ".role", "colour %r has no role" % name)
        else:
            r = role.strip().lower()
            if r not in KNOWN_ROLES:
                rep.add("warning", "unknown_role", path + ".role",
                        "role %r is not one of: %s" % (role, ", ".join(KNOWN_ROLES)))
            if hx is not None:
                by_role.setdefault(r, []).append((key, hx))
    for role in REQUIRED_ROLES:
        if role not in by_role:
            rep.add("error", "missing_role", "colors", "no valid colour has the required role %r" % role)
    return resolved, by_role


def default_pairs(by_role):
    """Pairs checked when the file lists none: every text role on every surface role."""
    pairs = []
    backgrounds = [(n, h) for r in ("background", "surface") for (n, h) in by_role.get(r, [])]
    for r in ("text", "text-muted"):
        for fg in by_role.get(r, []):
            for bg in backgrounds:
                pairs.append((fg[0], bg[0], "normal", "%s on %s" % (r, "background/surface")))
    for fg in by_role.get("on-primary", []):
        for bg in by_role.get("primary", []):
            pairs.append((fg[0], bg[0], "normal", "on-primary on primary"))
    return pairs


def check_pairs(data, resolved, by_role, rep):
    results = []
    raw = data.get("pairs")
    pairs = []
    if raw is None:
        pairs = default_pairs(by_role)
    elif not isinstance(raw, list):
        rep.add("error", "bad_pairs", "pairs", "pairs must be a list of {foreground, background, size}")
    else:
        for i, p in enumerate(raw):
            path = "pairs[%d]" % i
            if not isinstance(p, dict) or not isinstance(p.get("foreground"), str) or not isinstance(p.get("background"), str):
                rep.add("error", "bad_pair", path, "pair needs string foreground and background colour names")
                continue
            size = p.get("size", "normal")
            if size not in ("normal", "large"):
                rep.add("error", "bad_pair_size", path + ".size", "size must be 'normal' or 'large'")
                size = "normal"
            pairs.append((p["foreground"].strip().lower(), p["background"].strip().lower(), size, str(p.get("use", ""))))
    for fg, bg, size, use in pairs:
        if fg not in resolved or bg not in resolved:
            missing = fg if fg not in resolved else bg
            rep.add("error", "pair_unknown_color", "pairs", "pair uses %r, which is not a valid colour in colors" % missing)
            continue
        ratio = contrast_ratio(resolved[fg], resolved[bg])
        need = MIN_LARGE if size == "large" else MIN_NORMAL
        ok = ratio >= need
        results.append({"foreground": fg, "background": bg, "size": size, "use": use,
                        "ratio": round(ratio, 2), "required": need, "pass": ok})
        if not ok:
            rep.add("error", "low_contrast", "pairs",
                    "%s on %s is %.2f:1, needs %.1f:1 for %s text" % (fg, bg, ratio, need, size))
    return results


def check_type_scale(data, rep):
    scale = data.get("type_scale")
    if not isinstance(scale, list) or len(scale) < 3:
        rep.add("error", "missing_type_scale", "type_scale", "type_scale must list at least 3 {name, size} steps, smallest first")
        return
    prev = None
    for i, step in enumerate(scale):
        path = "type_scale[%d]" % i
        if not isinstance(step, dict) or not is_number(step.get("size")) or step["size"] <= 0:
            rep.add("error", "bad_type_step", path, "each step needs a name and a positive numeric size")
            prev = None
            continue
        size = step["size"]
        name = str(step.get("name", ""))
        if name.strip().lower() == "body" and size < MIN_BODY_PX:
            rep.add("warning", "body_too_small", path + ".size", "body is %s; use %d or larger" % (size, MIN_BODY_PX))
        if prev is not None:
            if size <= prev:
                rep.add("error", "type_scale_not_monotonic", path + ".size",
                        "%s is not larger than the step before it (%s); list sizes smallest to largest" % (size, prev))
            elif size / prev < MIN_STEP_RATIO:
                rep.add("warning", "type_step_too_close", path + ".size",
                        "ratio %.3f to the previous step is under %.3f; the steps look the same" % (size / prev, MIN_STEP_RATIO))
        prev = size


def check_spacing(data, rep):
    sp = data.get("spacing")
    if sp is None:
        return
    if not isinstance(sp, list) or not sp or not all(is_number(v) and v > 0 for v in sp):
        rep.add("error", "bad_spacing", "spacing", "spacing must be a non-empty list of positive numbers")
        return
    for i in range(1, len(sp)):
        if sp[i] <= sp[i - 1]:
            rep.add("error", "spacing_not_ascending", "spacing[%d]" % i, "%s is not larger than %s" % (sp[i], sp[i - 1]))
    for i, v in enumerate(sp):
        if v % GRID != 0:
            rep.add("warning", "spacing_off_grid", "spacing[%d]" % i, "%s is not a multiple of %d" % (v, GRID))


def build_report(data):
    rep = Report()
    resolved, by_role = check_colors(data, rep)
    pairs = check_pairs(data, resolved, by_role, rep)
    check_type_scale(data, rep)
    check_spacing(data, rep)
    errors = sum(1 for f in rep.findings if f["severity"] == "error")
    warnings = len(rep.findings) - errors
    return {"command": "check", "ok": errors == 0, "errors": errors, "warnings": warnings,
            "findings": rep.findings, "contrast_pairs": pairs}


def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def fail(message):
    emit({"command": "check", "ok": False, "error": message})
    return 2


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "check":
        return fail("usage: brand_tokens_check.py check <tokens.json>")
    try:
        with open(argv[1], "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        return fail("cannot read %s: %s" % (argv[1], exc))
    if not text.strip():
        return fail("%s is empty" % argv[1])
    try:
        data = json.loads(text)
    except ValueError as exc:
        return fail("%s is not valid JSON: %s" % (argv[1], exc))
    if not isinstance(data, dict):
        return fail("top level of %s must be a JSON object" % argv[1])
    report = build_report(data)
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
