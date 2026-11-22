#!/usr/bin/env python3
"""Validate a video timeline JSON before rendering (standard library only).

    python timeline_check.py <timeline.json> [--root DIR] [--strict]
                             [--max-line-chars N] [--max-lines N] [--max-cps N]

Reads: the timeline file, and checks that each declared asset path exists
(os.path.isfile only; asset contents are never opened). Writes: one JSON
object to stdout, nothing else. No network, no subprocess.

Exit codes: 0 no errors (and no warnings when --strict), 1 findings fail the
check, 2 the input cannot be used (missing or empty file, invalid JSON, NaN,
duplicate keys). In every case stdout is strict JSON.

The timeline format is described in SKILL.md of this skill. Times are seconds.
"""
import json
import math
import os
import re
import sys

# Half a frame of slack: two clips that touch at a frame boundary are not an overlap.
EPS_FRAMES = 0.5
# 23.976, 29.97 and 59.94 differ from 24, 30 and 60 by at most 0.06; treat as equal.
FPS_TOLERANCE = 0.1
# Caption defaults. 42 characters per line and 2 lines are common broadcast
# subtitle limits; 17 characters per second is a common reading-speed ceiling.
DEFAULT_MAX_LINE_CHARS = 42
DEFAULT_MAX_LINES = 2
DEFAULT_MAX_CPS = 17.0
# House defaults for on-screen time of a caption; not a standard.
MIN_CAPTION_SECONDS = 1.0
MAX_CAPTION_SECONDS = 7.0
# Percent of each edge kept free of text and logos; a house default.
DEFAULT_SAFE_MARGIN_PCT = 5.0
TRACK_KINDS = ("video", "audio", "caption", "overlay")
ASSET_TYPES = ("video", "audio", "image", "font")
# Asset types that must name a license (music and fonts are the usual claim sources).
LICENSE_REQUIRED = ("audio", "font")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class Fatal(Exception):
    pass


def _no_constant(name):
    raise Fatal("invalid JSON constant %s (NaN and Infinity are not allowed)" % name)


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Fatal("duplicate key %r in JSON object" % key)
        out[key] = value
    return out


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


class Report:
    def __init__(self):
        self.findings = []

    def add(self, level, code, where, message):
        self.findings.append({"level": level, "code": code, "where": where, "message": message})

    def err(self, code, where, message):
        self.add("error", code, where, message)

    def warn(self, code, where, message):
        self.add("warning", code, where, message)

    def count(self, level):
        return sum(1 for f in self.findings if f["level"] == level)


def load(path):
    if not os.path.isfile(path):
        raise Fatal("timeline file not found: %s" % path)
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except UnicodeDecodeError:
        raise Fatal("timeline file is not valid UTF-8 text: %s" % path)
    if not text.strip():
        raise Fatal("timeline file is empty: %s" % path)
    try:
        data = json.loads(text, parse_constant=_no_constant, object_pairs_hook=_pairs)
    except json.JSONDecodeError as exc:
        raise Fatal("invalid JSON at line %d column %d: %s" % (exc.lineno, exc.colno, exc.msg))
    except RecursionError:
        raise Fatal("nesting_too_deep: the JSON is nested too deeply to read")
    except ValueError as exc:
        raise Fatal("invalid_number: %s" % str(exc)[:120])
    if not isinstance(data, dict):
        raise Fatal("top level must be a JSON object with composition, assets and tracks")
    return data


def check_composition(comp, rep):
    ok = True
    if not isinstance(comp, dict):
        rep.err("E_SCHEMA", "composition", "composition must be an object")
        return False
    for key in ("fps", "duration"):
        if not is_num(comp.get(key)) or comp.get(key) <= 0:
            rep.err("E_SCHEMA", "composition." + key, "%s must be a number greater than 0" % key)
            ok = False
    for key in ("width", "height"):
        v = comp.get(key)
        if not (isinstance(v, int) and not isinstance(v, bool) and v > 0):
            rep.err("E_SCHEMA", "composition." + key, "%s must be a positive integer (pixels)" % key)
            ok = False
    return ok


def inside_root(root, full):
    try:
        return os.path.commonpath([os.path.abspath(root), os.path.abspath(full)]) == os.path.abspath(root)
    except ValueError:
        return False


def check_assets(assets, comp, root, rep):
    fps = comp["fps"]
    w, h = comp["width"], comp["height"]
    clean = {}
    if not isinstance(assets, dict):
        rep.err("E_SCHEMA", "assets", "assets must be an object keyed by asset id")
        return clean
    for aid, a in assets.items():
        where = "assets." + aid
        if not isinstance(a, dict):
            rep.err("E_SCHEMA", where, "asset must be an object")
            continue
        atype, path = a.get("type"), a.get("path")
        if atype not in ASSET_TYPES:
            rep.err("E_SCHEMA", where + ".type", "type must be one of %s" % ", ".join(ASSET_TYPES))
            continue
        if not isinstance(path, str) or not path.strip():
            rep.err("E_SCHEMA", where + ".path", "path must be a non-empty string")
            continue
        clean[aid] = a
        if "\\" in path:
            rep.warn("W_BACKSLASH_PATH", where + ".path", "use forward slashes so the timeline renders on every OS")
        full = os.path.normpath(os.path.join(root, path.replace("\\", "/")))
        if os.path.isabs(path) or not inside_root(root, full):
            rep.err("E_PATH_ESCAPE", where + ".path", "path must be relative and stay inside the project root")
        elif not os.path.isfile(full):
            rep.err("E_MISSING_ASSET", where + ".path", "file not found: %s" % path)
        if not NAME_RE.match(os.path.basename(path.replace("\\", "/"))):
            rep.warn("W_ASSET_NAME", where + ".path", "file name should be lowercase letters, digits, dot, dash, underscore, no spaces")
        lic = a.get("license")
        if not (isinstance(lic, str) and lic.strip()):
            if atype in LICENSE_REQUIRED:
                rep.err("E_NO_LICENSE", where + ".license", "%s assets must name their license or source" % atype)
            else:
                rep.warn("W_NO_LICENSE", where + ".license", "no license or source recorded")
        if atype in ("video", "image"):
            aw, ah = a.get("width"), a.get("height")
            if is_num(aw) and is_num(ah) and aw > 0 and ah > 0:
                if (aw, ah) != (w, h):
                    same_ratio = abs(aw * h - ah * w) <= 0.01 * aw * h
                    rep.warn("W_RESOLUTION_MISMATCH", where,
                             "asset is %sx%s, composition is %sx%s; %s" % (
                                 aw, ah, w, h, "scaling only" if same_ratio else "aspect ratio differs, expect crop or bars"))
            else:
                rep.warn("W_NO_DIMENSIONS", where, "width and height not recorded, resolution cannot be checked")
        if atype == "video":
            afps = a.get("fps")
            if is_num(afps) and afps > 0:
                if abs(afps - fps) > FPS_TOLERANCE:
                    rep.warn("W_FPS_MISMATCH", where, "asset is %s fps, composition is %s fps; frames will be dropped or repeated" % (afps, fps))
            else:
                rep.warn("W_NO_FPS", where, "fps not recorded, frame rate cannot be checked")
        if atype in ("video", "audio") and not (is_num(a.get("duration")) and a["duration"] > 0):
            rep.warn("W_NO_DURATION", where, "duration not recorded, trim cannot be checked")
    return clean


def check_caption(clip, where, dur, comp, limits, rep):
    text = clip.get("text")
    if not isinstance(text, str) or not text.strip():
        rep.err("E_SCHEMA", where + ".text", "caption clip needs non-empty text")
        return
    lines = text.split("\n")
    if len(lines) > limits["max_lines"]:
        rep.err("E_CAPTION_TOO_MANY_LINES", where, "%d lines, limit is %d" % (len(lines), limits["max_lines"]))
    for i, line in enumerate(lines, 1):
        if len(line) > limits["max_line_chars"]:
            rep.err("E_CAPTION_LINE_LENGTH", where, "line %d has %d characters, limit is %d" % (i, len(line), limits["max_line_chars"]))
    if dur is not None and dur > 0:
        total = len(text.replace("\n", " ").strip())
        cps = total / dur
        if cps > limits["max_cps"]:
            rep.err("E_CAPTION_TOO_FAST", where, "%d characters in %.2f s is %.1f chars/s, limit is %s" % (total, dur, cps, limits["max_cps"]))
        if dur < MIN_CAPTION_SECONDS:
            rep.warn("W_CAPTION_SHORT", where, "on screen %.2f s, below %s s" % (dur, MIN_CAPTION_SECONDS))
        if dur > MAX_CAPTION_SECONDS:
            rep.warn("W_CAPTION_LONG", where, "on screen %.2f s, above %s s; split it" % (dur, MAX_CAPTION_SECONDS))


def check_box(clip, where, is_caption, comp, rep):
    box = clip.get("box")
    if box is None:
        return
    keys = ("x", "y", "w", "h")
    if not (isinstance(box, dict) and all(is_num(box.get(k)) for k in keys)):
        rep.err("E_SCHEMA", where + ".box", "box must be an object with numeric x, y, w, h in pixels")
        return
    margin = comp.get("safe_margin_pct", DEFAULT_SAFE_MARGIN_PCT)
    if not is_num(margin) or margin < 0 or margin >= 50:
        margin = DEFAULT_SAFE_MARGIN_PCT
    mx, my = comp["width"] * margin / 100.0, comp["height"] * margin / 100.0
    left, top = box["x"], box["y"]
    right, bottom = left + box["w"], top + box["h"]
    if left < mx or top < my or right > comp["width"] - mx or bottom > comp["height"] - my:
        msg = "box (%s,%s,%s,%s) leaves the %s%% safe area" % (box["x"], box["y"], box["w"], box["h"], margin)
        if is_caption:
            rep.err("E_CAPTION_OUTSIDE_SAFE_AREA", where, msg)
        else:
            rep.warn("W_OUTSIDE_SAFE_AREA", where, msg)


def check_tracks(tracks, assets, comp, limits, rep):
    fps, total = comp["fps"], comp["duration"]
    eps = EPS_FRAMES / fps
    n_clips = 0
    used = set()
    seen_ids = set()
    if not isinstance(tracks, list):
        rep.err("E_SCHEMA", "tracks", "tracks must be an array")
        return 0, used
    for ti, track in enumerate(tracks):
        tw = "tracks[%d]" % ti
        if not isinstance(track, dict):
            rep.err("E_SCHEMA", tw, "track must be an object")
            continue
        tid = track.get("id") if isinstance(track.get("id"), str) else str(ti)
        tw = "track %s" % tid
        kind = track.get("kind")
        if kind not in TRACK_KINDS:
            rep.err("E_SCHEMA", tw + ".kind", "kind must be one of %s" % ", ".join(TRACK_KINDS))
            continue
        clips = track.get("clips")
        if not isinstance(clips, list):
            rep.err("E_SCHEMA", tw + ".clips", "clips must be an array")
            continue
        spans = []
        for ci, clip in enumerate(clips):
            n_clips += 1
            cid = clip.get("id") if isinstance(clip, dict) and isinstance(clip.get("id"), str) else "#%d" % ci
            where = "%s clip %s" % (tid, cid)
            if not isinstance(clip, dict):
                rep.err("E_SCHEMA", where, "clip must be an object")
                continue
            if isinstance(clip.get("id"), str):
                if clip["id"] in seen_ids:
                    rep.err("E_SCHEMA", where, "duplicate clip id")
                seen_ids.add(clip["id"])
            start = clip.get("start")
            if not is_num(start) or start < 0:
                rep.err("E_SCHEMA", where + ".start", "start must be a number of seconds, 0 or more")
                continue
            if is_num(clip.get("duration")) and clip["duration"] > 0:
                dur = float(clip["duration"])
            elif is_num(clip.get("end")) and clip["end"] > start:
                dur = float(clip["end"]) - start
            else:
                rep.err("E_SCHEMA", where, "needs duration > 0 or end > start")
                continue
            end = start + dur
            spans.append((float(start), end, cid))
            if end > total + eps:
                rep.err("E_BEYOND_DURATION", where, "ends at %.3f s, composition is %.3f s" % (end, total))
            f_start = start * fps
            if abs(f_start - round(f_start)) > 0.001:
                rep.warn("W_OFF_FRAME_GRID", where, "start %.4f s is not on a frame boundary at %s fps" % (start, fps))
            for ref_key in ("asset", "font"):
                ref = clip.get(ref_key)
                if ref is None:
                    continue
                if ref not in assets:
                    rep.err("E_UNKNOWN_ASSET", where + "." + ref_key, "asset id %r is not declared in assets" % (ref,))
                    continue
                used.add(ref)
            ref = clip.get("asset")
            a = assets.get(ref) if isinstance(ref, str) else None
            if a is not None:
                at = a["type"]
                if (at == "audio") != (kind == "audio") and at != "font":
                    rep.warn("W_KIND_MISMATCH", where, "%s asset on a %s track" % (at, kind))
                src_in = clip.get("source_in", 0)
                speed = clip.get("speed", 1)
                if is_num(src_in) and is_num(speed) and speed > 0 and src_in >= 0 \
                        and is_num(a.get("duration")) and at in ("video", "audio"):
                    need = src_in + dur * speed
                    if need > a["duration"] + eps:
                        rep.err("E_TRIM_BEYOND_SOURCE", where,
                                "needs source up to %.3f s but asset %s is %.3f s long" % (need, ref, a["duration"]))
            elif kind in ("video", "audio") and "asset" not in clip:
                rep.err("E_SCHEMA", where + ".asset", "%s clip needs an asset id" % kind)
            if kind == "caption":
                check_caption(clip, where, dur, comp, limits, rep)
            check_box(clip, where, kind == "caption", comp, rep)
        if not track.get("allow_overlap", False):
            spans.sort()
            for prev, cur in zip(spans, spans[1:]):
                if cur[0] < prev[1] - eps:
                    rep.err("E_OVERLAP", tw, "clips %s and %s overlap by %.3f s" % (prev[2], cur[2], prev[1] - cur[0]))
    return n_clips, used


def validate(data, root, strict, cli_limits):
    rep = Report()
    comp = data.get("composition")
    if not check_composition(comp, rep):
        return rep, 0, 0, 0
    caps = comp.get("captions") if isinstance(comp.get("captions"), dict) else {}
    limits = {
        "max_line_chars": DEFAULT_MAX_LINE_CHARS, "max_lines": DEFAULT_MAX_LINES, "max_cps": DEFAULT_MAX_CPS,
    }
    for key in limits:
        for src in (caps, cli_limits):
            if is_num(src.get(key)) and src[key] > 0:
                limits[key] = src[key]
    assets = check_assets(data.get("assets", {}), comp, root, rep)
    n_clips, used = check_tracks(data.get("tracks"), assets, comp, limits, rep)
    for aid, a in assets.items():
        if aid not in used and a["type"] != "font":
            rep.warn("W_UNUSED_ASSET", "assets." + aid, "declared but no clip uses it")
    return rep, len(assets), n_clips, len(data["tracks"]) if isinstance(data.get("tracks"), list) else 0


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=True, indent=2, allow_nan=False) + "\n")


def parse_args(argv):
    opts = {"strict": False, "root": None, "limits": {}, "path": None}
    i = 0
    flags = {"--max-line-chars": "max_line_chars", "--max-lines": "max_lines", "--max-cps": "max_cps"}
    while i < len(argv):
        a = argv[i]
        if a == "--strict":
            opts["strict"] = True
        elif a == "--root" or a in flags:
            if i + 1 >= len(argv):
                raise Fatal("%s needs a value" % a)
            i += 1
            if a == "--root":
                opts["root"] = argv[i]
            else:
                try:
                    opts["limits"][flags[a]] = float(argv[i])
                except ValueError:
                    raise Fatal("%s needs a number" % a)
        elif a.startswith("--"):
            raise Fatal("unknown option %s" % a)
        elif opts["path"] is None:
            opts["path"] = a
        else:
            raise Fatal("only one timeline file is accepted")
        i += 1
    if opts["path"] is None:
        raise Fatal("usage: timeline_check.py <timeline.json> [--root DIR] [--strict]")
    return opts


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        opts = parse_args(argv)
        data = load(opts["path"])
        root = opts["root"] or os.path.dirname(os.path.abspath(opts["path"]))
        rep, n_assets, n_clips, n_tracks = validate(data, root, opts["strict"], opts["limits"])
    except Fatal as exc:
        emit({"command": "timeline_check", "ok": False, "fatal": str(exc)})
        return 2
    errors, warnings = rep.count("error"), rep.count("warning")
    ok = errors == 0 and not (opts["strict"] and warnings)
    emit({
        "command": "timeline_check",
        "ok": ok,
        "strict": opts["strict"],
        "summary": {"errors": errors, "warnings": warnings, "tracks": n_tracks, "clips": n_clips, "assets": n_assets},
        "findings": rep.findings,
    })
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
