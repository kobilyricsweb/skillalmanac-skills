#!/usr/bin/env python3
"""Check exported image files against a spec table the user supplies.

Usage:
    python image_spec_check.py --specs specs.csv PATH [PATH ...]
        [--spec NAME ...] [--recursive] [--out report.json] [--force]

PATH is an image file or a folder of images (folders are not searched
recursively unless --recursive is given). The spec table is a CSV file; see
references/spec-table.md for the columns.

Reads: the spec CSV and the image files (headers only, plus the file tail for
a truncation check). Writes: nothing, except an optional copy of the JSON
report to --out. --out is refused when it resolves to the spec file or to any
input file, even with --force. Images are never edited or re-saved.

Output: one JSON document on stdout. Exit codes: 0 every file passes every
named spec, 1 at least one violation, 2 usage or spec error (stdout then holds
{"ok": false, "error": "..."}).

Python 3.9+, standard library only, no network.
"""
import argparse
import csv
import json
import os
import re
import struct
import sys

TOOL_VERSION = "0.1.0"

# An aspect-ratio gap under this share is a resize, over it a crop or pad.
# Under 3 percent a stretch or a trim of a few edge pixels is hard to see.
CROP_GAP = 0.03
# Gaps under this are rounding (1200x628 against 1.91:1 is 0.04 percent).
PASS_TOL = 0.005
# Scaling a raster up by more than this blurs it, so the file must be re-exported.
UPSCALE_OK = 1.05
# Bytes per pixel at or above these suggest photographic content (heuristic).
PHOTO_BPP_PNG_GIF = 1.0
PHOTO_BPP_WEBP = 0.3
# Spec "KB" is 1000 bytes: the stricter reading, so a pass holds for 1024 too.
KB = 1000
# DPI metadata is rounded to one decimal; allow this much below the minimum.
DPI_SLACK = 0.5

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
EXT_FORMAT = {".jpg": "jpeg", ".jpeg": "jpeg", ".png": "png", ".gif": "gif", ".webp": "webp", ".svg": "svg"}
FORMAT_ALIASES = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp", "svg": "svg"}
SPEC_COLUMNS = ("name", "width", "height", "aspect", "size_rule", "formats", "max_kb", "max_bytes", "min_dpi")
RULES = ("exact", "min", "max")
SOF_MARKERS = (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF)
SVG_UNITS = {"": 1.0, "px": 1.0, "pt": 4.0 / 3.0, "pc": 16.0, "in": 96.0, "cm": 96.0 / 2.54, "mm": 96.0 / 25.4}

STATUS_ORDER = ("unreadable", "reexport", "crop_or_pad", "resize", "pass")
ISSUE_STATUS = {
    "extension_mismatch": "reexport", "format_not_allowed": "reexport", "over_size": "reexport",
    "dpi_missing": "reexport", "dpi_low": "reexport", "too_small": "reexport",
    "aspect_mismatch": "crop_or_pad",
    "size_mismatch": "resize", "below_minimum": "resize", "too_large": "resize", "aspect_drift": "resize",
}
READ_FIX = {
    "empty_file": "the file is 0 bytes; export it again",
    "unreadable_header": "not a PNG, JPEG, GIF, WebP or SVG header; open it in an editor and export it again",
    "truncated": "the file ends early (incomplete export or interrupted copy); export or copy it again",
    "corrupt": "the header is damaged; export it again from the source",
    "unreadable_file": "the file could not be read (permissions or a locked file)",
    "svg_no_dimensions": "the SVG has no usable width, height or viewBox; add a viewBox",
}


class SpecError(Exception):
    pass


# --------------------------------------------------------------------------
# Spec table
# --------------------------------------------------------------------------

def parse_ratio(text):
    t = text.strip()
    m = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*[:/]\s*([0-9]*\.?[0-9]+)", t)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a <= 0 or b <= 0:
            raise SpecError("aspect '%s' must be positive" % text)
        return a / b
    if re.fullmatch(r"[0-9]*\.?[0-9]+", t) and float(t) > 0:
        return float(t)
    raise SpecError("aspect '%s' is not W:H, W/H or a decimal ratio" % text)


def parse_int(text, label, row_name):
    t = text.strip()
    if not re.fullmatch(r"[0-9]+", t) or not (0 < int(t) <= 100000):
        raise SpecError("spec '%s': %s '%s' must be a whole number from 1 to 100000" % (row_name, label, text))
    return int(t)


def load_specs(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise SpecError("spec file '%s' is empty" % path)
            header = [(h or "").strip().lower() for h in reader.fieldnames]
            unknown = [h for h in header if h not in SPEC_COLUMNS]
            if unknown or "name" not in header:
                raise SpecError("spec file columns must come from %s and include name; got %s"
                                % (", ".join(SPEC_COLUMNS), ", ".join(header)))
            specs, seen = [], set()
            for raw in reader:
                row = {}
                for key, value in raw.items():
                    if key is None:
                        raise SpecError("a spec row has more cells than the header")
                    row[key.strip().lower()] = (value or "").strip()
                if not any(row.values()):
                    continue
                specs.append(build_spec(row))
                if specs[-1]["name"] in seen:
                    raise SpecError("duplicate spec name '%s'" % specs[-1]["name"])
                seen.add(specs[-1]["name"])
    except OSError as exc:
        raise SpecError("cannot read spec file '%s': %s" % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise SpecError("spec file '%s' is not UTF-8 text" % path)
    if not specs:
        raise SpecError("spec file '%s' has no rows" % path)
    return specs


def build_spec(row):
    name = row.get("name", "")
    if not name:
        raise SpecError("a spec row has no name")
    tw = parse_int(row["width"], "width", name) if row.get("width") else None
    th = parse_int(row["height"], "height", name) if row.get("height") else None
    rule = row.get("size_rule", "").lower()
    if rule and rule not in RULES:
        raise SpecError("spec '%s': size_rule must be exact, min or max" % name)
    if rule and tw is None and th is None:
        raise SpecError("spec '%s': size_rule needs a width or a height" % name)
    if not rule and (tw is not None or th is not None):
        rule = "exact"
    ratio = parse_ratio(row["aspect"]) if row.get("aspect") else None
    if ratio is None and rule == "exact" and tw and th:
        ratio = tw / float(th)
    elif ratio is not None and rule == "exact" and tw and th and abs((tw / float(th)) / ratio - 1) > PASS_TOL:
        raise SpecError("spec '%s': width x height and aspect disagree" % name)
    formats = None
    if row.get("formats"):
        formats = set()
        for token in re.split(r"[|;\s]+", row["formats"].lower()):
            if not token:
                continue
            if token not in FORMAT_ALIASES:
                raise SpecError("spec '%s': unknown format '%s' (use jpg, png, gif, webp, svg)" % (name, token))
            formats.add(FORMAT_ALIASES[token])
    if row.get("max_kb") and row.get("max_bytes"):
        raise SpecError("spec '%s': give max_kb or max_bytes, not both" % name)
    max_bytes = None
    if row.get("max_kb"):
        if not re.fullmatch(r"[0-9]*\.?[0-9]+", row["max_kb"]) or float(row["max_kb"]) <= 0:
            raise SpecError("spec '%s': max_kb must be a positive number" % name)
        max_bytes = int(round(float(row["max_kb"]) * KB))
    elif row.get("max_bytes"):
        if not re.fullmatch(r"[0-9]+", row["max_bytes"]) or int(row["max_bytes"]) <= 0:
            raise SpecError("spec '%s': max_bytes must be a positive whole number" % name)
        max_bytes = int(row["max_bytes"])
    min_dpi = None
    if row.get("min_dpi"):
        if not re.fullmatch(r"[0-9]*\.?[0-9]+", row["min_dpi"]) or float(row["min_dpi"]) <= 0:
            raise SpecError("spec '%s': min_dpi must be a positive number" % name)
        min_dpi = float(row["min_dpi"])
    return {"name": name, "width": tw, "height": th, "ratio": ratio, "rule": rule or None,
            "formats": formats, "max_bytes": max_bytes, "min_dpi": min_dpi}


# --------------------------------------------------------------------------
# Header readers
# --------------------------------------------------------------------------

def _fail(info, code, detail):
    info["error"] = code
    info["error_detail"] = detail
    return info


def _parse_png(f, size, info):
    info["format"] = "png"
    f.seek(8)
    first, complete = True, False
    try:
        for _ in range(200000):
            head = f.read(8)
            if len(head) < 8:
                break
            length, ctype = struct.unpack(">I4s", head)
            if first:
                if ctype != b"IHDR" or length != 13:
                    return _fail(info, "corrupt", "first chunk is not IHDR")
                data = f.read(13)
                info["w"], info["h"] = struct.unpack(">II", data[:8])
                f.seek(4, 1)
                first = False
                continue
            if ctype == b"pHYs" and length == 9:
                data = f.read(9)
                px, py, unit = struct.unpack(">IIB", data)
                if unit == 1 and px > 0 and py > 0:
                    info["dpi"] = (round(px * 0.0254, 1), round(py * 0.0254, 1))
                    info["dpi_source"] = "pHYs"
                f.seek(4, 1)
                continue
            if ctype == b"IEND":
                complete = True
                break
            nxt = f.tell() + length + 4
            if nxt > size:
                break
            f.seek(nxt)
    except struct.error:
        return _fail(info, "truncated", "header cut short")
    if info["w"] is None:
        return _fail(info, "truncated", "no IHDR chunk")
    if not complete:
        return _fail(info, "truncated", "no IEND chunk")
    return info


def _parse_exif_dpi(data):
    if len(data) < 8:
        return None
    order = {b"II": "<", b"MM": ">"}.get(data[:2])
    if order is None or struct.unpack(order + "H", data[2:4])[0] != 42:
        return None
    off = struct.unpack(order + "I", data[4:8])[0]
    if off + 2 > len(data):
        return None
    count = struct.unpack(order + "H", data[off:off + 2])[0]
    res = {}
    unit = 2
    for i in range(min(count, 200)):
        entry = data[off + 2 + 12 * i: off + 14 + 12 * i]
        if len(entry) < 12:
            break
        tag, typ, cnt = struct.unpack(order + "HHI", entry[:8])
        if tag in (0x011A, 0x011B) and typ == 5 and cnt == 1:
            voff = struct.unpack(order + "I", entry[8:12])[0]
            if voff + 8 <= len(data):
                num, den = struct.unpack(order + "II", data[voff:voff + 8])
                if den:
                    res[tag] = num / float(den)
        elif tag == 0x0128 and typ == 3:
            unit = struct.unpack(order + "H", entry[8:10])[0]
    if 0x011A not in res or unit not in (2, 3):
        return None
    x = res[0x011A]
    y = res.get(0x011B, x)
    scale = 1.0 if unit == 2 else 2.54
    return (round(x * scale, 1), round(y * scale, 1))


def _parse_jpeg(f, size, info):
    info["format"] = "jpeg"
    f.seek(2)
    jfif_dpi, exif_dpi = None, None
    for _ in range(4000):
        b = f.read(1)
        if not b:
            return _fail(info, "truncated", "ended before the frame header")
        if b != b"\xff":
            return _fail(info, "corrupt", "expected a marker byte")
        m = f.read(1)
        while m == b"\xff":
            m = f.read(1)
        if not m:
            return _fail(info, "truncated", "ended inside a marker")
        mv = m[0]
        if mv in (0x00, 0x01) or 0xD0 <= mv <= 0xD8:
            continue
        if mv in (0xD9, 0xDA):
            return _fail(info, "corrupt", "image data starts before any frame header")
        lb = f.read(2)
        if len(lb) < 2:
            return _fail(info, "truncated", "ended inside a segment length")
        seg = struct.unpack(">H", lb)[0]
        if seg < 2:
            return _fail(info, "corrupt", "segment length below 2")
        n = seg - 2
        if mv in SOF_MARKERS:
            d = f.read(5)
            if len(d) < 5:
                return _fail(info, "truncated", "frame header cut short")
            info["h"], info["w"] = struct.unpack(">HH", d[1:5])
            if not info["w"] or not info["h"]:
                return _fail(info, "corrupt", "zero width or height in the frame header")
            break
        if mv in (0xE0, 0xE1):
            d = f.read(n)
            if len(d) < n:
                return _fail(info, "truncated", "ended inside a segment")
            if mv == 0xE0 and d[:5] == b"JFIF\x00" and len(d) >= 12 and jfif_dpi is None:
                units, xd, yd = d[7], struct.unpack(">H", d[8:10])[0], struct.unpack(">H", d[10:12])[0]
                if units in (1, 2) and xd and yd:
                    k = 1.0 if units == 1 else 2.54
                    jfif_dpi = (round(xd * k, 1), round(yd * k, 1))
                elif units == 0:
                    info["notes"].append("JFIF density is an aspect ratio only (units 0), so it holds no DPI")
            elif mv == 0xE1 and d[:6] == b"Exif\x00\x00" and exif_dpi is None:
                exif_dpi = _parse_exif_dpi(d[6:])
        else:
            f.seek(n, 1)
    else:
        return _fail(info, "corrupt", "no frame header found")
    if jfif_dpi:
        info["dpi"], info["dpi_source"] = jfif_dpi, "JFIF"
    elif exif_dpi:
        info["dpi"], info["dpi_source"] = exif_dpi, "EXIF"
    f.seek(max(0, size - 2048))
    if b"\xff\xd9" not in f.read():
        return _fail(info, "truncated", "no end-of-image marker near the end of the file")
    return info


def _parse_gif(f, size, info):
    info["format"] = "gif"
    f.seek(6)
    d = f.read(4)
    if len(d) < 4:
        return _fail(info, "truncated", "header cut short")
    info["w"], info["h"] = struct.unpack("<HH", d)
    if not info["w"] or not info["h"]:
        return _fail(info, "corrupt", "zero width or height")
    f.seek(size - 1)
    if f.read(1) != b"\x3b":
        return _fail(info, "truncated", "no GIF trailer byte at the end")
    return info


def _parse_webp(f, size, info):
    info["format"] = "webp"
    f.seek(0)
    head = f.read(30)
    if len(head) < 21:
        return _fail(info, "truncated", "header cut short")
    head = head.ljust(30, b"\x00")  # tiny lossless files can end before byte 30; the RIFF length check below catches real truncation
    riff = struct.unpack("<I", head[4:8])[0]
    fourcc = head[12:16]
    data = head[20:30]
    if fourcc == b"VP8 ":
        if data[3:6] != b"\x9d\x01\x2a":
            return _fail(info, "corrupt", "missing VP8 start code")
        info["w"] = struct.unpack("<H", data[6:8])[0] & 0x3FFF
        info["h"] = struct.unpack("<H", data[8:10])[0] & 0x3FFF
    elif fourcc == b"VP8L":
        if data[0] != 0x2F:
            return _fail(info, "corrupt", "missing VP8L signature")
        bits = struct.unpack("<I", data[1:5])[0]
        info["w"], info["h"] = (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    elif fourcc == b"VP8X":
        info["w"] = int.from_bytes(data[4:7], "little") + 1
        info["h"] = int.from_bytes(data[7:10], "little") + 1
        info["animated"] = bool(data[0] & 0x02)
    else:
        return _fail(info, "corrupt", "unknown first WebP chunk")
    if not info["w"] or not info["h"]:
        return _fail(info, "corrupt", "zero width or height")
    if riff + 8 > size:
        return _fail(info, "truncated", "RIFF length says %d bytes but the file has %d" % (riff + 8, size))
    return info


def _svg_length(text):
    m = re.fullmatch(r"\s*([0-9]*\.?[0-9]+)\s*(px|pt|pc|in|cm|mm|em|ex|%)?\s*", text or "")
    if not m or m.group(2) in ("em", "ex", "%"):
        return None
    return float(m.group(1)) * SVG_UNITS[m.group(2) or ""]


def _parse_svg(f, size, info, text):
    info["format"] = "svg"
    info["vector"] = True
    tag = re.search(r"<svg\b[^>]*>", text, re.S)
    attrs = {}
    for m in re.finditer(r"([A-Za-z_:][\w:.-]*)\s*=\s*(\"([^\"]*)\"|'([^']*)')", tag.group(0)):
        attrs[m.group(1)] = m.group(3) if m.group(3) is not None else m.group(4)
    w, h = _svg_length(attrs.get("width")), _svg_length(attrs.get("height"))
    box = re.split(r"[\s,]+", attrs.get("viewBox", "").strip())
    vb = None
    if len(box) == 4:
        try:
            vb = (float(box[2]), float(box[3]))
        except ValueError:
            vb = None
    if w and h:
        info["w"], info["h"] = w, h
    elif vb and vb[0] > 0 and vb[1] > 0:
        info["w"], info["h"] = vb
        info["notes"].append("size taken from the viewBox because width and height are missing or relative")
    else:
        return _fail(info, "svg_no_dimensions", "no usable width and height or viewBox")
    f.seek(max(0, size - 1024))
    if b"</svg" not in f.read() and not tag.group(0).rstrip().endswith("/>"):
        return _fail(info, "truncated", "no closing svg tag near the end")
    return info


def read_info(path):
    info = {"format": None, "w": None, "h": None, "bytes": None, "dpi": None, "dpi_source": None,
            "vector": False, "animated": False, "error": None, "error_detail": None, "notes": []}
    try:
        size = os.path.getsize(path)
        info["bytes"] = size
        if size == 0:
            return _fail(info, "empty_file", "0 bytes")
        with open(path, "rb") as f:
            head = f.read(16)
            if head.startswith(b"\x89PNG\r\n\x1a\n"):
                return _parse_png(f, size, info)
            if head[:3] == b"\xff\xd8\xff":
                return _parse_jpeg(f, size, info)
            if head[:6] in (b"GIF87a", b"GIF89a"):
                return _parse_gif(f, size, info)
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                return _parse_webp(f, size, info)
            f.seek(0)
            text = f.read(8192).decode("utf-8", "ignore").lstrip(chr(0xFEFF))
            if re.search(r"<svg[\s>]", text) and text.lstrip().startswith("<"):
                return _parse_svg(f, size, info, text)
            return _fail(info, "unreadable_header", "no known signature")
    except OSError as exc:
        return _fail(info, "unreadable_file", exc.strerror or str(exc))


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def num(x):
    x = float(x)
    return int(x) if x.is_integer() else round(x, 2)


def looks_photographic(fmt, bpp):
    if fmt == "jpeg":
        return True
    if fmt in ("png", "gif"):
        return bpp is not None and bpp >= PHOTO_BPP_PNG_GIF
    if fmt == "webp":
        return bpp is not None and bpp >= PHOTO_BPP_WEBP
    return False


def format_advice(fmt, allowed, bpp):
    photo = looks_photographic(fmt, bpp)
    prefs = ("jpeg", "webp") if photo else ("png", "webp", "gif")
    pick = next((p for p in prefs if allowed is None or p in allowed), None)
    if pick is None:
        pick = sorted(allowed)[0] if allowed else fmt
    kind = "photo" if photo else "flat"
    if pick == fmt:
        return "keep_format_tune", pick, kind
    return "%s_use_%s" % (kind, pick), pick, kind


def crop_box(w, h, ratio):
    W, H = int(round(w)), int(round(h))
    if W / float(H) > ratio:
        cw, ch = max(1, int(round(H * ratio))), H
        box = {"x": (W - cw) // 2, "y": 0, "w": cw, "h": ch}
        pad = {"w": W, "h": max(1, int(round(W / ratio)))}
    else:
        cw, ch = W, max(1, int(round(W / ratio)))
        box = {"x": 0, "y": (H - ch) // 2, "w": cw, "h": ch}
        pad = {"w": max(1, int(round(H * ratio))), "h": H}
    return box, round(100.0 * cw * ch / (W * H), 1), pad


def check_geometry(spec, w, h, vector, issues, fix, sug):
    tw, th, ratio, rule = spec["width"], spec["height"], spec["ratio"], spec["rule"]
    if ratio is None and tw is None and th is None:
        return
    gap = abs((w / float(h)) / ratio - 1) if ratio else None
    if vector:
        if tw or th:
            sug["note"] = "vector file: exact pixel size is not applicable, aspect ratio only"
        if gap is not None and gap > PASS_TOL:
            issues.append("aspect_mismatch" if gap > CROP_GAP else "aspect_drift")
            fix.append("viewBox ratio is %.4f, spec wants %.4f; change the artboard" % (w / float(h), ratio))
        return
    if ratio is not None and gap > CROP_GAP:
        box, kept, pad = crop_box(w, h, ratio)
        issues.append("aspect_mismatch")
        sug["crop_box"], sug["kept_percent"], sug["pad_canvas"] = box, kept, pad
        text = ("aspect gap %.1f%% (over 3%%): crop to the %dx%d box at x=%d,y=%d (keeps %.1f%% of the image; "
                "the kept box is the safe area, so check nothing important sits outside it) "
                "or pad the canvas to %dx%d" % (gap * 100, box["w"], box["h"], box["x"], box["y"], kept, pad["w"], pad["h"]))
        if rule in ("exact", "min") and (tw or th):
            s = max(tw / float(box["w"]) if tw else 0, th / float(box["h"]) if th else 0)
            if tw and th and rule == "exact":
                sug["then_scale"] = {"w": tw, "h": th}
                text += "; then scale to %dx%d" % (tw, th)
            if s > UPSCALE_OK:
                issues.append("too_small")
                text += "; the crop is %.2fx too small, so re-export from a larger source" % s
        fix.append(text)
        return
    if rule == "exact":
        bad = (tw is not None and w != tw) or (th is not None and h != th)
        if bad:
            issues.append("size_mismatch")
            if tw and th:
                target = (tw, th)
            elif tw:
                target = (tw, int(round(h * tw / float(w))))
            else:
                target = (int(round(w * th / float(h))), th)
            s = max(target[0] / float(w), target[1] / float(h))
            sug["target"] = {"w": target[0], "h": target[1]}
            if s > UPSCALE_OK:
                issues.append("too_small")
                fix.append("is %dx%d, spec wants %dx%d: a %.2fx upscale blurs, so re-export from a larger source"
                           % (w, h, target[0], target[1], s))
            elif gap is not None and gap > PASS_TOL:
                sug["op"] = "scale_cover_then_trim"
                fix.append("is %dx%d, spec wants %dx%d: scale to cover, then trim the overflow (under 3%% of one side)"
                           % (w, h, target[0], target[1]))
            else:
                sug["op"] = "scale"
                fix.append("is %dx%d, spec wants %dx%d: scale to %dx%d" % (w, h, target[0], target[1], target[0], target[1]))
            return
    elif rule == "min":
        if (tw and w < tw) or (th and h < th):
            s = max(tw / float(w) if tw else 0, th / float(h) if th else 0)
            if s > UPSCALE_OK:
                issues.append("too_small")
                fix.append("is %dx%d, spec wants at least %sx%s: re-export from a larger source" % (w, h, tw or "-", th or "-"))
            else:
                issues.append("below_minimum")
                fix.append("is %.1f%% under the minimum: scale up by %.3fx" % ((s - 1) * 100, s))
            return
    elif rule == "max":
        if (tw and w > tw) or (th and h > th):
            scale = min(tw / float(w) if tw else 9e9, th / float(h) if th else 9e9)
            nw, nh = max(1, int(w * scale + 1e-9)), max(1, int(h * scale + 1e-9))
            issues.append("too_large")
            sug["target"] = {"w": nw, "h": nh}
            sug["op"] = "scale_to_fit"
            fix.append("is %dx%d, over the %sx%s maximum: scale to %dx%d" % (w, h, tw or "-", th or "-", nw, nh))
            return
    if gap is not None and gap > PASS_TOL:
        issues.append("aspect_drift")
        fix.append("aspect gap %.2f%%: keep the width and set the height to %d (or keep the height and set the width to %d)"
                   % (gap * 100, int(round(w / ratio)), int(round(h * ratio))))
        sug["target"] = {"w": int(round(w)), "h": int(round(w / ratio))}


def evaluate(spec, info, ext_fmt):
    issues, fix, sug = [], [], {}
    fmt = info["format"]
    w, h = info["w"], info["h"]
    size = info["bytes"]
    bpp = None if info["vector"] else size / float(w * h)
    if ext_fmt != fmt:
        issues.append("extension_mismatch")
        fix.append("the extension says %s but the header is %s; export with the right extension"
                   % (ext_fmt or "unknown", fmt))
    advice = None
    if spec["formats"] is not None and fmt not in spec["formats"]:
        issues.append("format_not_allowed")
        advice, pick, kind = format_advice(fmt, spec["formats"], bpp)
        fix.append("%s is not allowed (allowed: %s); %s content, export as %s"
                   % (fmt, ", ".join(sorted(spec["formats"])), "photographic" if kind == "photo" else "flat-graphic", pick))
    if spec["max_bytes"] is not None and size > spec["max_bytes"]:
        issues.append("over_size")
        advice, pick, kind = format_advice(fmt, spec["formats"], bpp)
        extra = size - spec["max_bytes"]
        tip = {"keep_format_tune": "keep %s and lower quality or colours in small steps, then reduce pixel size only if needed" % fmt}.get(
            advice, "%s content in %s: export as %s" % ("photographic" if kind == "photo" else "flat-graphic", fmt, pick))
        fix.append("%d bytes, limit %d (%d over, %.1f%%): %s" % (size, spec["max_bytes"], extra, 100.0 * extra / spec["max_bytes"], tip))
    if spec["min_dpi"] is not None:
        if info["dpi"] is None:
            issues.append("dpi_missing")
            fix.append("no DPI in PNG pHYs, JFIF or EXIF; set the density at export (pixels do not change)")
        elif min(info["dpi"]) < spec["min_dpi"] - DPI_SLACK:
            issues.append("dpi_low")
            fix.append("density is %s dpi, spec wants %s; re-export at that density and check the pixel size is enough"
                       % (num(min(info["dpi"])), num(spec["min_dpi"])))
        if not info["vector"]:
            sug["max_print_size_in"] = [round(w / spec["min_dpi"], 2), round(h / spec["min_dpi"], 2)]
    check_geometry(spec, w, h, info["vector"], issues, fix, sug)
    status = "pass"
    for cand in STATUS_ORDER[1:]:
        if any(ISSUE_STATUS[i] == cand for i in issues):
            status = cand
            break
    out = {"status": status, "issues": issues, "fix": fix}
    if advice:
        out["advice"] = advice
    if sug:
        out["suggest"] = sug
    return out


def check_file(path, specs):
    info = read_info(path)
    ext = os.path.splitext(path)[1].lower()
    ext_fmt = EXT_FORMAT.get(ext)
    entry = {"path": path.replace("\\", "/"), "name": os.path.basename(path), "format": info["format"],
             "w": num(info["w"]) if info["w"] is not None else None,
             "h": num(info["h"]) if info["h"] is not None else None,
             "bytes": info["bytes"], "aspect": None, "dpi": None, "vector": info["vector"],
             "animated": info["animated"], "warnings": list(info["notes"]), "results": {}}
    if info["w"] and info["h"]:
        entry["aspect"] = round(info["w"] / float(info["h"]), 4)
    if info["dpi"]:
        entry["dpi"] = {"x": info["dpi"][0], "y": info["dpi"][1], "source": info["dpi_source"]}
    if info["animated"]:
        entry["warnings"].append("animated: canvas size read, frame sizes not checked")
    if info["error"]:
        entry["read_error"] = {"code": info["error"], "detail": info["error_detail"]}
        for spec in specs:
            entry["results"][spec["name"]] = {"status": "unreadable", "issues": [info["error"]],
                                              "fix": [READ_FIX[info["error"]]]}
        return entry
    for spec in specs:
        entry["results"][spec["name"]] = evaluate(spec, info, ext_fmt)
    return entry


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------

def collect(paths, recursive):
    found, seen = [], set()

    def add(p):
        key = os.path.normcase(os.path.realpath(p))
        if key not in seen:
            seen.add(key)
            found.append(p)

    for p in paths:
        if os.path.isdir(p):
            if recursive:
                for root, dirs, files in os.walk(p):
                    dirs.sort()
                    for name in sorted(files):
                        if name.lower().endswith(IMAGE_EXTS):
                            add(os.path.join(root, name))
            else:
                for name in sorted(os.listdir(p)):
                    full = os.path.join(p, name)
                    if os.path.isfile(full) and name.lower().endswith(IMAGE_EXTS):
                        add(full)
        elif os.path.isfile(p):
            add(p)
        else:
            raise SpecError("path not found: %s" % p)
    if not found:
        raise SpecError("no image files found (looked for %s)" % ", ".join(IMAGE_EXTS))
    return sorted(found)


def same_file(a, b):
    try:
        if os.path.exists(a) and os.path.exists(b):
            return os.path.samefile(a, b)
    except OSError:
        pass
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def build_report(files, specs):
    by_status = {s: 0 for s in STATUS_ORDER}
    by_spec = {s["name"]: {k: 0 for k in STATUS_ORDER} for s in specs}
    all_pass = 0
    for entry in files:
        clean = True
        for name, res in entry["results"].items():
            by_status[res["status"]] += 1
            by_spec[name][res["status"]] += 1
            clean = clean and res["status"] == "pass"
        all_pass += clean
    ok = by_status["pass"] == len(files) * len(specs)
    return {"tool": "image_spec_check", "version": TOOL_VERSION, "ok": ok,
            "specs": [s["name"] for s in specs], "files": files,
            "summary": {"files": len(files), "specs": len(specs), "checks": len(files) * len(specs),
                        "files_passing_all_specs": all_pass, "by_status": by_status, "by_spec": by_spec}}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check image files against a spec table (headers only).")
    parser.add_argument("paths", nargs="+", help="image files or folders")
    parser.add_argument("--specs", required=True, help="CSV spec table")
    parser.add_argument("--spec", action="append", default=[], help="only this spec name (repeatable)")
    parser.add_argument("--recursive", action="store_true", help="search folders recursively")
    parser.add_argument("--out", help="also write the JSON report here (never over an input)")
    parser.add_argument("--force", action="store_true", help="allow --out to replace an existing report file")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            print(json.dumps({"ok": False, "error": "usage error: see --help"}))
            return 2
        raise
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        specs = load_specs(args.specs)
        if args.spec:
            names = {s["name"] for s in specs}
            missing = [n for n in args.spec if n not in names]
            if missing:
                raise SpecError("unknown spec name(s): %s; the table has: %s" % (", ".join(missing), ", ".join(sorted(names))))
            specs = [s for s in specs if s["name"] in args.spec]
        paths = collect(args.paths, args.recursive)
        if args.out:
            if os.path.isdir(args.out):
                raise SpecError("--out is a folder; give a file path")
            for guard in paths + [args.specs] + [p for p in args.paths if os.path.isfile(p)]:
                if same_file(args.out, guard):
                    raise SpecError("--out resolves to an input file (%s); refusing, even with --force" % guard)
            if os.path.exists(args.out) and not args.force:
                raise SpecError("--out exists; pass --force to replace an earlier report")
        report = build_report([check_file(p, specs) for p in paths], specs)
        text = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text + "\n")
    except SpecError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.stderr.write("error: %s\n" % exc)
        return 2
    except OSError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.stderr.write("error: %s\n" % exc)
        return 2
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
