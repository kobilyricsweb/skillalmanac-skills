#!/usr/bin/env python3
"""Validate a design-token export (W3C design tokens format subset) and preview CSS.

Usage:
    python tokens_check.py check <tokens.json>   # strict JSON report on stdout
    python tokens_check.py css <tokens.json>     # flattened CSS custom properties only

Reads the one file given. Writes nothing. No network. Standard library only.

Exit codes: 0 no error findings (warnings allowed), 1 at least one error finding,
2 file missing, unreadable, not JSON or not a JSON object.

Format subset (see references/token-subset.md in the skill):
  - a token is an object with "$value"; every other object is a group
  - "$type" may sit on a token or on any parent group and is inherited
  - an alias is the string "{group.token}" naming another token by dotted path
  - root "$modes": ["light", "dark"] lists the modes; a token that varies by mode
    carries "$extensions": {"modes": {"light": ..., "dark": ...}} and "$value" is
    its mode-independent default
"""
import argparse
import json
import re
import sys

sys.setrecursionlimit(5000)

# A segment must be usable inside a CSS custom-property name.
SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]+$")
# House style: lower-case kebab segments, so exports from different files line up.
STYLE_SEGMENT = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Deeper paths make for names nobody types; 5 matches category/role/variant/state/scale.
MAX_DEPTH = 5

ALIAS_FULL = re.compile(r"^\{([^{}]+)\}$")
ALIAS_ANY = re.compile(r"\{([^{}]+)\}")
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
DIMENSION = re.compile(r"^-?\d+(?:\.\d+)?(?:px|rem)$")
DURATION = re.compile(r"^\d+(?:\.\d+)?(?:ms|s)$")
FONT_WEIGHT_WORDS = {
    "thin", "hairline", "extra-light", "ultra-light", "light", "normal", "regular",
    "book", "medium", "semi-bold", "demi-bold", "bold", "extra-bold", "ultra-bold",
    "black", "heavy", "extra-black", "ultra-black",
}
SIMPLE_TYPES = {"color", "dimension", "number", "fontFamily", "fontWeight", "duration",
                "cubicBezier", "string", "boolean"}
COMPOSITE_TYPES = {"shadow", "typography", "border", "gradient", "transition", "strokeStyle"}
SEVERITY_ORDER = {"error": 0, "warning": 1}


class DupDict(dict):
    """dict that remembers keys that appeared twice in the same JSON object."""


def _pairs_hook(pairs):
    out = DupDict()
    out.dups = []
    for key, value in pairs:
        if key in out:
            out.dups.append(key)
        out[key] = value
    return out


def _reject_constant(name):
    raise ValueError("non-standard JSON constant " + name)


class Token:
    def __init__(self, path, segments, type_, value, modes):
        self.path = path
        self.segments = segments
        self.type = type_
        self.value = value
        self.modes = modes  # dict or None


class Checker:
    def __init__(self, data):
        self.data = data
        self.findings = []
        self.tokens = []
        self.by_path = {}
        self.declared_modes = None

    def add(self, severity, code, path, message):
        self.findings.append({"severity": severity, "code": code, "path": path, "message": message})

    # ---- walking -------------------------------------------------------
    def run(self):
        root = self.data
        modes = root.get("$modes")
        if modes is not None:
            if isinstance(modes, list) and all(isinstance(m, str) and m for m in modes) and len(set(modes)) == len(modes):
                self.declared_modes = list(modes)
            else:
                self.add("error", "invalid_modes", "$modes", "$modes must be a list of unique non-empty strings")
        self._walk(root, [], None)
        seen = []
        for tok in self.tokens:
            for m in (tok.modes or {}):
                if m not in seen:
                    seen.append(m)
        self.modes_declared = self.declared_modes is not None
        self.modes = self.declared_modes if self.modes_declared else seen
        if self.modes_declared:
            for m in seen:
                if m not in self.modes:
                    self.add("warning", "undeclared_mode", "$modes", "mode '%s' is used by a token but not listed in $modes" % m)
        for m in self.modes:
            self._check_segment(m, "$modes", is_mode=True)
        self._check_names_and_collisions()
        for tok in self.tokens:
            self._check_token(tok)
        self._check_cycles()
        self._check_duplicates()

    def _walk(self, node, segs, inherited_type):
        gtype = node.get("$type", inherited_type) if isinstance(node.get("$type", inherited_type), str) else inherited_type
        for key in getattr(node, "dups", []):
            self.add("error", "duplicate_key", ".".join(segs) or "(root)", "key '%s' appears twice in this object; JSON parsers keep only the last one" % key)
        children = 0
        for key, val in node.items():
            if key.startswith("$"):
                continue
            children += 1
            child_segs = segs + [key]
            path = ".".join(child_segs)
            if not isinstance(val, dict):
                self.add("error", "not_a_token", path, "expected a token or a group (object), found %s" % type(val).__name__)
                continue
            if "$value" in val:
                self._add_token(child_segs, val, gtype)
            elif "value" in val and not isinstance(val["value"], dict) and not any(isinstance(v, dict) for k, v in val.items() if not k.startswith("$")):
                self.add("error", "legacy_value_key", path, "found 'value' without '$value'; this looks like the older Style Dictionary shape, rename the keys with a '$' prefix")
            else:
                self._walk(val, child_segs, gtype)
        if children == 0 and segs:
            self.add("warning", "empty_group", ".".join(segs), "group has no tokens")

    def _add_token(self, segs, node, gtype):
        path = ".".join(segs)
        for key in getattr(node, "dups", []):
            self.add("error", "duplicate_key", path, "key '%s' appears twice in this token" % key)
        ttype = node.get("$type", gtype)
        if not isinstance(ttype, str):
            ttype = None
        modes = None
        ext = node.get("$extensions")
        if isinstance(ext, dict) and "modes" in ext:
            if isinstance(ext["modes"], dict):
                modes = dict(ext["modes"])
                for key in getattr(ext["modes"], "dups", []):
                    self.add("error", "duplicate_key", path, "mode '%s' appears twice in this token" % key)
            else:
                self.add("error", "invalid_modes", path, "$extensions.modes must be an object of mode name to value")
        tok = Token(path, segs, ttype, node["$value"], modes)
        self.tokens.append(tok)
        self.by_path[path] = tok

    # ---- per-segment and per-token rules -------------------------------
    def _check_segment(self, seg, path, is_mode=False):
        what = "mode name" if is_mode else "name segment"
        if not seg or not SAFE_SEGMENT.match(seg):
            self.add("error", "naming_violation", path, "%s '%s' has characters that cannot form a CSS custom property name (allowed: letters, digits, hyphen, underscore); use hyphens instead of spaces, slashes and dots" % (what, seg))
        elif not STYLE_SEGMENT.match(seg):
            self.add("warning", "naming_violation", path, "%s '%s' is not lower-case kebab-case (e.g. 'brand-blue')" % (what, seg))

    def _check_names_and_collisions(self):
        css_names = {}
        for tok in self.tokens:
            for seg in tok.segments:
                self._check_segment(seg, tok.path)
            if len(tok.segments) > MAX_DEPTH:
                self.add("warning", "naming_violation", tok.path, "path is %d levels deep; more than %d makes names hard to use" % (len(tok.segments), MAX_DEPTH))
            css_names.setdefault(css_name(tok.path), []).append(tok.path)
        for name, paths in css_names.items():
            if len(paths) > 1:
                for p in paths:  # none of them can be emitted safely, so each is reported
                    self.add("error", "css_name_collision", p, "%s all flatten to the CSS name %s" % (", ".join(paths), name))

    def _check_token(self, tok):
        if tok.type is None:
            self.add("error", "missing_type", tok.path, "no $type on the token or any parent group")
        elif tok.type not in SIMPLE_TYPES and tok.type not in COMPOSITE_TYPES:
            self.add("warning", "unknown_type", tok.path, "type '%s' is not in the supported subset; value is not validated and is left out of the CSS preview" % tok.type)
        self._check_value(tok, tok.value, "$value")
        if tok.modes is not None:
            wanted = self.modes
            for m in wanted:
                v = tok.modes.get(m)
                if m not in tok.modes or v is None or (isinstance(v, str) and not v.strip()):
                    self.add("error", "missing_mode_value", tok.path, "no value for mode '%s'" % m)
            for m, v in tok.modes.items():
                if m in wanted and v is not None and not (isinstance(v, str) and not v.strip()):
                    self._check_value(tok, v, "mode " + m)

    def _check_value(self, tok, value, where):
        # aliases first: every reference must resolve to a token of a compatible type
        for ref in collect_aliases(value):
            target = self.by_path.get(ref)
            if target is None:
                reason = "names a group, not a token" if self._is_group(ref) else "does not exist"
                self.add("error", "unresolved_alias", tok.path, "%s: alias {%s} %s" % (where, ref, reason))
            elif tok.type and target.type and tok.type != target.type:
                self.add("error", "alias_type_mismatch", tok.path, "%s: alias {%s} is type %s but this token is %s" % (where, ref, target.type, tok.type))
        if tok.type in SIMPLE_TYPES:
            msg = literal_problem(tok.type, value)
            if msg:
                code, text = msg
                self.add("warning" if code == "unsupported_value" else "error", code, tok.path, "%s: %s" % (where, text))

    def _is_group(self, ref):
        prefix = ref + "."
        return any(p.startswith(prefix) for p in self.by_path)

    # ---- graph and duplicate rules -------------------------------------
    def _check_cycles(self):
        reported = set()
        for mode in [None] + list(self.modes):
            def refs(tok, mode=mode):
                val = tok.value
                if mode is not None and tok.modes and tok.modes.get(mode) is not None:
                    val = tok.modes[mode]
                return [r for r in collect_aliases(val) if r in self.by_path]
            state = {}
            stack = []

            def dfs(path):
                state[path] = 1
                stack.append(path)
                for r in refs(self.by_path[path]):
                    if state.get(r) == 1:
                        cyc = stack[stack.index(r):]
                        key = frozenset(cyc)
                        if key not in reported:
                            reported.add(key)
                            start = cyc.index(min(cyc))
                            ordered = cyc[start:] + cyc[:start]
                            for member in ordered:  # every member is unusable, so every member is reported
                                self.add("error", "circular_alias", member, "alias loop: " + " -> ".join(ordered + [ordered[0]]))
                    elif r not in state:
                        dfs(r)
                stack.pop()
                state[path] = 2
            for tok in self.tokens:
                if tok.path not in state:
                    dfs(tok.path)

    def _check_duplicates(self):
        bad = {f["path"] for f in self.findings if f["severity"] == "error"}
        groups = {}
        for tok in self.tokens:
            if tok.type not in SIMPLE_TYPES or tok.path in bad:
                continue
            if collect_aliases(tok.value):
                continue
            key = (tok.type, json.dumps(normalise(tok.type, tok.value), sort_keys=True))
            groups.setdefault(key, []).append(tok.path)
        for (ttype, _), paths in groups.items():
            if len(paths) > 1:
                self.add("warning", "duplicate_value", paths[0], "%d tokens of type %s share one literal value (%s); make one the source and alias the rest: %s" % (len(paths), ttype, preview_value(ttype, self.by_path[paths[0]].value), ", ".join(paths)))


# ---- helpers ------------------------------------------------------------
def css_name(path):
    return "--" + path.replace(".", "-")


def collect_aliases(value):
    if isinstance(value, str):
        return ALIAS_ANY.findall(value)
    if isinstance(value, dict):
        out = []
        for v in value.values():
            out.extend(collect_aliases(v))
        return out
    if isinstance(value, list):
        out = []
        for v in value:
            out.extend(collect_aliases(v))
        return out
    return []


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def literal_problem(ttype, v):
    """Return (code, message) when a literal value does not fit its type, else None."""
    if isinstance(v, str) and ALIAS_FULL.match(v):
        return None
    if isinstance(v, str) and ALIAS_ANY.search(v) and ttype != "string":
        return ("invalid_value", "an alias must be the whole value for type %s, found %r" % (ttype, v))
    if ttype == "color":
        if isinstance(v, str):
            return None if HEX.match(v) else ("invalid_value", "color %r is not a hex value (#rgb, #rgba, #rrggbb or #rrggbbaa)" % v)
        if isinstance(v, dict):
            if v.get("colorSpace") != "srgb":
                return ("unsupported_value", "color space %r is not converted to CSS by this check" % v.get("colorSpace"))
            comps = v.get("components")
            if not (isinstance(comps, list) and len(comps) == 3 and all(is_number(c) and 0 <= c <= 1 for c in comps)):
                return ("invalid_value", "srgb color needs components: three numbers between 0 and 1")
            alpha = v.get("alpha", 1)
            if not (is_number(alpha) and 0 <= alpha <= 1):
                return ("invalid_value", "color alpha must be a number between 0 and 1")
            return None
        return ("invalid_value", "color must be a hex string or an srgb object")
    if ttype == "dimension":
        if isinstance(v, str):
            return None if DIMENSION.match(v) else ("invalid_value", "dimension %r needs a number and a unit px or rem (for example '16px')" % v)
        if isinstance(v, dict) and is_number(v.get("value")) and v.get("unit") in ("px", "rem"):
            return None
        return ("invalid_value", "dimension must be a string like '16px' or {value, unit} with unit px or rem")
    if ttype == "duration":
        if isinstance(v, str) and DURATION.match(v):
            return None
        if isinstance(v, dict) and is_number(v.get("value")) and v.get("unit") in ("ms", "s"):
            return None
        return ("invalid_value", "duration must look like '200ms' or '0.2s'")
    if ttype == "number":
        return None if is_number(v) else ("invalid_value", "number must be a JSON number, found %r" % (v,))
    if ttype == "fontWeight":
        if is_number(v) and 1 <= v <= 1000:
            return None
        if isinstance(v, str) and v in FONT_WEIGHT_WORDS:
            return None
        return ("invalid_value", "fontWeight must be 1-1000 or a weight keyword, found %r" % (v,))
    if ttype == "fontFamily":
        if isinstance(v, str) and v.strip():
            return None
        if isinstance(v, list) and v and all(isinstance(x, str) and x.strip() for x in v):
            return None
        return ("invalid_value", "fontFamily must be a non-empty string or list of strings")
    if ttype == "cubicBezier":
        if isinstance(v, list) and len(v) == 4 and all(is_number(x) for x in v) and 0 <= v[0] <= 1 and 0 <= v[2] <= 1:
            return None
        return ("invalid_value", "cubicBezier must be four numbers with x values between 0 and 1")
    if ttype == "string":
        return None if isinstance(v, str) else ("invalid_value", "string token must hold a string")
    if ttype == "boolean":
        return None if isinstance(v, bool) else ("invalid_value", "boolean token must hold true or false")
    return None


def fmt_num(x):
    return str(int(x)) if float(x) == int(x) else repr(float(x))


def color_to_hex(v):
    if isinstance(v, str):
        h = v.lower()
        if len(h) in (4, 5):
            h = "#" + "".join(c * 2 for c in h[1:])
        return h
    parts = [max(0, min(255, round(c * 255))) for c in v["components"]]
    alpha = v.get("alpha", 1)
    if alpha < 1:
        parts.append(max(0, min(255, round(alpha * 255))))
    return "#" + "".join("%02x" % p for p in parts)


def normalise(ttype, v):
    """Canonical form so '#FFF' and '#ffffff' count as the same value."""
    if ttype == "color":
        h = color_to_hex(v) if (isinstance(v, str) or (isinstance(v, dict) and v.get("colorSpace") == "srgb")) else v
        if isinstance(h, str) and len(h) == 9 and h.endswith("ff"):
            h = h[:7]
        return h
    if ttype == "dimension" or ttype == "duration":
        if isinstance(v, dict):
            return fmt_num(v["value"]) + v["unit"]
        m = re.match(r"^(-?\d+(?:\.\d+)?)(.*)$", v)
        return fmt_num(float(m.group(1))) + m.group(2)
    if ttype == "fontFamily":
        return [v] if isinstance(v, str) else list(v)
    return v


def preview_value(ttype, v):
    n = normalise(ttype, v)
    return n if isinstance(n, str) else json.dumps(n)


def to_css(ttype, v):
    """Convert one value to CSS text, or None when the type is not converted."""
    if isinstance(v, str) and ALIAS_ANY.search(v):
        return ALIAS_ANY.sub(lambda m: "var(%s)" % css_name(m.group(1)), v)
    if ttype == "color":
        return v if isinstance(v, str) else (color_to_hex(v) if v.get("colorSpace") == "srgb" else None)
    if ttype in ("dimension", "duration"):
        return v if isinstance(v, str) else fmt_num(v["value"]) + v["unit"]
    if ttype in ("number", "fontWeight"):
        return fmt_num(v) if is_number(v) else str(v)
    if ttype == "fontFamily":
        names = [v] if isinstance(v, str) else v
        return ", ".join(n if re.match(r"^[A-Za-z0-9_-]+$", n) or n.startswith('"') else '"%s"' % n for n in names)
    if ttype == "cubicBezier":
        return "cubic-bezier(%s)" % ", ".join(fmt_num(x) for x in v)
    if ttype == "string":
        return v
    return None  # boolean, composites and unknown types have no single CSS value


def build_css(checker):
    bad = {f["path"] for f in checker.findings if f["severity"] == "error"}
    skipped = []
    root_lines = []
    mode_lines = {m: [] for m in checker.modes}
    for tok in checker.tokens:
        if tok.path in bad:
            skipped.append({"path": tok.path, "reason": "token has an error finding"})
            continue
        base = to_css(tok.type, tok.value)
        if base is None:
            skipped.append({"path": tok.path, "reason": "type %s has no single CSS value" % tok.type})
            continue
        root_lines.append("  %s: %s;" % (css_name(tok.path), base))
        for m, v in (tok.modes or {}).items():
            if m in mode_lines:
                text = to_css(tok.type, v)
                if text is not None:
                    mode_lines[m].append("  %s: %s;" % (css_name(tok.path), text))
    blocks = [":root {\n" + "\n".join(root_lines) + "\n}"] if root_lines else []
    for m in checker.modes:
        if mode_lines[m]:
            blocks.append('[data-theme="%s"] {\n' % m + "\n".join(mode_lines[m]) + "\n}")
    return "\n".join(blocks) + ("\n" if blocks else ""), skipped


def load(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            text = fh.read()
    except OSError as exc:
        return None, "cannot read %s: %s" % (path, exc.strerror or exc)
    except UnicodeDecodeError:
        return None, "%s is not valid UTF-8 text" % path
    if not text.strip():
        return None, "%s is empty" % path
    try:
        data = json.loads(text, object_pairs_hook=_pairs_hook, parse_constant=_reject_constant)
    except ValueError as exc:
        return None, "%s is not valid JSON: %s" % (path, exc)
    if not isinstance(data, dict):
        return None, "%s must contain a JSON object at the top level" % path
    return data, None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a design-token export and preview CSS variables.")
    parser.add_argument("command", choices=["check", "css"])
    parser.add_argument("file")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # same bytes on Windows, macOS and Linux
    data, err = load(args.file)
    if err:
        sys.stderr.write("error: " + err + "\n")
        return 2
    checker = Checker(data)
    checker.run()
    css, skipped = build_css(checker)
    if args.command == "css":
        sys.stdout.write(css)
        return 1 if any(f["severity"] == "error" for f in checker.findings) else 0
    findings = sorted(checker.findings, key=lambda f: (SEVERITY_ORDER[f["severity"]], f["path"], f["code"], f["message"]))
    by_code = {}
    for f in findings:
        by_code[f["code"]] = by_code.get(f["code"], 0) + 1
    errors = sum(1 for f in findings if f["severity"] == "error")
    report = {
        "command": "check",
        "file": args.file,
        "ok": errors == 0,
        "tokens": len(checker.tokens),
        "modes": checker.modes,
        "modes_declared": checker.modes_declared,
        "counts": {"error": errors, "warning": len(findings) - errors},
        "counts_by_code": dict(sorted(by_code.items())),
        "findings": findings,
        "css_skipped": skipped,
        "css_preview": css,
    }
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
