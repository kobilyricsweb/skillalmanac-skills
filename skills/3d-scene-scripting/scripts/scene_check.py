#!/usr/bin/env python3
"""Validate a scene description JSON before any 3D script is written or rendered.

Usage:
    python scripts/scene_check.py <scene.json>

Reads the one file you name; writes nothing; no network. Prints one strict JSON
object (no NaN or Infinity) on stdout.

Exit codes: 0 no errors (warnings allowed), 1 at least one error finding,
2 the file is missing, empty, not valid JSON, or not a JSON object.

Scene description (all transforms are WORLD space; no parent hierarchy):
{
  "units": "meters", "up_axis": "Z" | "Y", "ground_level": 0.0,
  "objects":  [{"name", "type", "location":[x,y,z], "scale":[x,y,z],
                "dimensions":[x,y,z]   (world-axis size, scale included),
                "origin": "center" | "base", "role": "ground" (exempt from below-ground),
                "rigid_body": true | false, "material": "<name>"}],
  "materials": [{"name", "shader": "principled" | ...}],
  "lights":   [{"name", "type", "location":[x,y,z], "energy": number}],
  "camera":   {"name", "location":[x,y,z], "fov_deg": number,
               "target":[x,y,z]  OR  "rotation_euler_deg":[x,y,z] with
               "euler_order": "XYZ", "euler_convention": "blender" | "three"}
}
"""
import json
import math
import os
import sys

# Spare tolerance so float noise in exported values does not raise findings.
TOL = 1e-3
# Scale axes whose max/min ratio exceeds this count as non-uniform. 0.1 percent
# survives export rounding but catches real stretching (a 1:1.01 box already
# makes a physics collider disagree with its mesh).
UNIFORM_RATIO = 1.001
# A pinhole camera outside 1..170 degrees is almost always a unit mistake
# (radians typed as degrees, or a focal length typed as a field of view).
FOV_MIN, FOV_MAX = 1.0, 170.0
AXES = {"X": 0, "Y": 1, "Z": 2}
KNOWN_UP = ("Y", "Z")
UNIT_NAMES = ("meters", "centimeters", "millimeters", "inches", "feet", "unitless")


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, rule, subject, message):
        self.items.append({"severity": severity, "rule": rule, "subject": subject, "message": message})


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def vec3(v):
    if isinstance(v, list) and len(v) == 3 and all(is_num(x) for x in v):
        return [float(x) for x in v]
    return None


def _reject_constant(name):
    raise ValueError("non-finite number %s is not valid JSON" % name)


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def axis_rot(axis, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    if axis == "X":
        return [[1, 0, 0], [0, c, -s], [0, s, c]]
    if axis == "Y":
        return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    return [[c, -s, 0], [s, c, 0], [0, 0, 1]]


def euler_matrix(angles, order, convention):
    """Blender applies the letters in order as extrinsic rotations, so the last
    letter is the leftmost factor (XYZ gives Rz*Ry*Rx). three.js builds the
    matrix with the first letter leftmost (XYZ gives Rx*Ry*Rz). Same letters,
    different matrices; this is the portability trap the skill documents."""
    factors = [axis_rot(ch, angles[AXES[ch]]) for ch in order]
    if convention == "blender":
        factors.reverse()
    m = factors[0]
    for f in factors[1:]:
        m = mat_mul(m, f)
    return m


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def check_contract(scene, F):
    units = scene.get("units")
    if units not in UNIT_NAMES:
        F.add("error", "contract-units", "scene", "units must be one of %s; got %r" % (", ".join(UNIT_NAMES), units))
    up = scene.get("up_axis")
    if up not in KNOWN_UP:
        F.add("error", "contract-up-axis", "scene", "up_axis must be 'Y' or 'Z'; got %r" % (up,))
    gl = scene.get("ground_level", 0.0)
    if not is_num(gl):
        F.add("error", "contract-ground", "scene", "ground_level must be a finite number")
        gl = 0.0
    return up if up in KNOWN_UP else None, float(gl)


def check_names(scene, F):
    # Objects, lights and the camera share one namespace in Blender and in a
    # three.js scene graph lookup, so duplicates are checked across all three.
    seen = {}
    entries = []
    for coll in ("objects", "lights"):
        for o in scene.get(coll) or []:
            if isinstance(o, dict):
                entries.append((o.get("name"), coll))
    cam = scene.get("camera")
    if isinstance(cam, dict):
        entries.append((cam.get("name"), "camera"))
    lower = {}
    for name, coll in entries:
        if not isinstance(name, str) or not name.strip():
            F.add("error", "name-missing", coll, "an entry in %s has no usable name" % coll)
            continue
        seen.setdefault(name, []).append(coll)
        lower.setdefault(name.lower(), set()).add(name)
    for name, colls in sorted(seen.items()):
        if len(colls) > 1:
            F.add("error", "name-duplicate", name, "name used %d times (%s); the second one is renamed or overwritten by most tools" % (len(colls), ", ".join(colls)))
    for low, variants in sorted(lower.items()):
        if len(variants) > 1:
            F.add("warning", "name-case-collision", "/".join(sorted(variants)), "names differ only by case; they collide on case-insensitive file systems and exports")
    mats = {}
    for m in scene.get("materials") or []:
        if isinstance(m, dict) and isinstance(m.get("name"), str):
            mats[m["name"]] = mats.get(m["name"], 0) + 1
    for name, n in sorted(mats.items()):
        if n > 1:
            F.add("error", "name-duplicate", name, "material name defined %d times" % n)
    return set(mats)


def check_materials(scene, mat_names, F):
    used = set()
    for o in scene.get("objects") or []:
        if not isinstance(o, dict):
            continue
        ref = o.get("material")
        if ref is None:
            continue
        used.add(ref)
        if ref not in mat_names:
            F.add("error", "material-undefined", str(o.get("name")), "references material %r that is not in materials" % (ref,))
    for name in sorted(mat_names - used):
        F.add("warning", "material-unreferenced", name, "material is defined but no object uses it")


def check_objects(scene, up, ground, F):
    for o in scene.get("objects") or []:
        if not isinstance(o, dict):
            F.add("error", "object-shape", "objects", "an entry in objects is not an object")
            continue
        name = str(o.get("name"))
        loc = vec3(o.get("location"))
        if loc is None:
            F.add("error", "vector-shape", name, "location must be three finite numbers")
            continue
        scale = o.get("scale", [1, 1, 1])
        sc = vec3(scale)
        if sc is None:
            F.add("error", "vector-shape", name, "scale must be three finite numbers")
            sc = [1.0, 1.0, 1.0]
        if any(abs(s) < TOL for s in sc):
            F.add("error", "scale-zero", name, "a scale axis is zero; the object is flat or invisible")
        elif any(s < 0 for s in sc):
            F.add("warning", "scale-negative", name, "negative scale flips face winding; apply it or mirror with a modifier")
        mags = [abs(s) for s in sc if abs(s) >= TOL]
        if o.get("rigid_body") is True and mags and max(mags) / min(mags) > UNIFORM_RATIO:
            F.add("error", "nonuniform-scale-rigid", name, "rigid body has non-uniform scale %s; apply the scale to the mesh or set the collider size instead" % (sc,))
        if up is None or o.get("role") == "ground":
            continue
        idx = AXES[up]
        dims = vec3(o.get("dimensions"))
        base_origin = o.get("origin") == "base"
        if base_origin or dims is None:
            bottom = loc[idx]
        else:
            bottom = loc[idx] - 0.5 * abs(dims[idx])
        if bottom < ground - TOL:
            F.add("error", "below-ground", name, "lowest point %.4g is below ground level %.4g on the %s axis" % (bottom, ground, up))


def check_lights(scene, F):
    lights = scene.get("lights")
    if not isinstance(lights, list) or not lights:
        F.add("error", "light-missing", "scene", "no lights; the render is black or relies on an unstated world color")
        return
    for l in lights:
        if not isinstance(l, dict):
            continue
        if not is_num(l.get("energy")) or l["energy"] <= 0:
            F.add("warning", "light-energy", str(l.get("name")), "energy missing or not above zero; the light contributes nothing")
        if vec3(l.get("location")) is None and l.get("type") != "sun":
            F.add("error", "vector-shape", str(l.get("name")), "location must be three finite numbers")


def forward_vector(cam, F):
    loc = vec3(cam.get("location"))
    if loc is None:
        F.add("error", "vector-shape", str(cam.get("name")), "camera location must be three finite numbers")
        return None, None
    tgt = vec3(cam.get("target"))
    if tgt is not None:
        d = [tgt[i] - loc[i] for i in range(3)]
        n = norm(d)
        if n < TOL:
            F.add("error", "camera-degenerate", str(cam.get("name")), "camera location equals its target")
            return loc, None
        return loc, [x / n for x in d]
    rot = vec3(cam.get("rotation_euler_deg"))
    if rot is None:
        F.add("error", "camera-aim", str(cam.get("name")), "camera needs 'target' or 'rotation_euler_deg'")
        return loc, None
    order = cam.get("euler_order", "XYZ")
    conv = cam.get("euler_convention")
    if conv not in ("blender", "three") or not isinstance(order, str) or sorted(order) != ["X", "Y", "Z"]:
        F.add("error", "camera-aim", str(cam.get("name")), "rotation needs euler_convention 'blender' or 'three' and an euler_order that is a permutation of XYZ")
        return loc, None
    m = euler_matrix(rot, order, conv)
    # A camera looks down its local -Z axis in both Blender and three.js.
    return loc, [-m[0][2], -m[1][2], -m[2][2]]


def check_camera(scene, F):
    cam = scene.get("camera")
    if not isinstance(cam, dict):
        F.add("error", "camera-missing", "scene", "no camera defined")
        return
    fov = cam.get("fov_deg")
    if not is_num(fov) or not (FOV_MIN <= fov <= FOV_MAX):
        F.add("error", "camera-fov", str(cam.get("name")), "fov_deg must be a number from %g to %g" % (FOV_MIN, FOV_MAX))
        fov = None
    loc, fwd = forward_vector(cam, F)
    if fwd is None or fov is None:
        return
    half = math.radians(fov) / 2.0
    hit = 0
    behind = 0
    for o in scene.get("objects") or []:
        if not isinstance(o, dict) or o.get("role") == "ground":
            continue
        c = vec3(o.get("location"))
        if c is None:
            continue
        dims = vec3(o.get("dimensions"))
        radius = 0.5 * norm(dims) if dims else 0.0
        d = [c[i] - loc[i] for i in range(3)]
        dist = norm(d)
        if dist < TOL:
            continue
        dot = sum(d[i] * fwd[i] for i in range(3)) / dist
        if dot <= 0:
            behind += 1
            continue
        angle = math.acos(max(-1.0, min(1.0, dot)))
        ang_radius = math.asin(min(1.0, radius / dist)) if radius < dist else math.pi / 2
        if angle - ang_radius <= half:
            hit += 1
    if hit == 0:
        F.add("error", "camera-aim", str(cam.get("name")), "no object lies inside the camera cone (fov %g deg); %d object(s) are behind the camera" % (fov, behind))
    return hit


def validate(scene):
    F = Findings()
    up, ground = check_contract(scene, F)
    mat_names = check_names(scene, F)
    check_materials(scene, mat_names, F)
    check_objects(scene, up, ground, F)
    check_lights(scene, F)
    check_camera(scene, F)
    order = {"error": 0, "warning": 1}
    F.items.sort(key=lambda f: (order[f["severity"]], f["rule"], f["subject"]))
    errors = sum(1 for f in F.items if f["severity"] == "error")
    return {
        "command": "validate",
        "ok": errors == 0,
        "errors": errors,
        "warnings": len(F.items) - errors,
        "objects": len(scene.get("objects") or []),
        "findings": F.items,
    }


def main(argv):
    if len(argv) != 1:
        sys.stderr.write("usage: scene_check.py <scene.json>\n")
        return 2
    path = argv[0]
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        sys.stderr.write("cannot read %s: %s\n" % (path, exc))
        return 2
    if not raw.strip():
        sys.stderr.write("%s is empty; give a scene description JSON\n" % path)
        return 2
    try:
        scene = json.loads(raw.decode("utf-8-sig"), parse_constant=_reject_constant)
    except (ValueError, UnicodeDecodeError) as exc:
        sys.stderr.write("%s is not valid JSON: %s\n" % (path, exc))
        return 2
    if not isinstance(scene, dict):
        sys.stderr.write("%s must hold a JSON object at the top level\n" % path)
        return 2
    report = validate(scene)
    sys.stdout.write(json.dumps(report, indent=2, allow_nan=False, ensure_ascii=True) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
