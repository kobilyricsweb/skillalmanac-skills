#!/usr/bin/env python3
"""Inventory the licences that installed dependencies DECLARE, from local files only.

Usage:
    python license_inventory.py scan PATH [PATH ...] [--policy policy.json]
    python license_inventory.py normalise "MIT License" "(MIT OR Apache-2.0)"

What it reads (never writes, never touches the network, never runs project code):
  * node_modules/**/package.json            -> "license" / "licenses" fields
  * *.dist-info/METADATA (site-packages)    -> License-Expression, License, Classifier
  * first 6000 characters of a LICENSE / LICENCE / COPYING / UNLICENSE file
    beside each package, matched against a few well-known text openings
  * package-lock.json (license field when present), poetry.lock, Cargo.lock,
    go.sum -> package names only, so absent metadata stays absent
  * package.json, requirements*.txt, go.mod outside installed trees -> which
    packages are direct dependencies

Output: strict JSON on stdout (see SKILL.md for the contract). It states what is
DECLARED. It makes no compliance or legal statement.

Exit codes: 0 nothing needs attention; 1 at least one unknown, conflict or
policy flag; 2 usage error, unreadable policy, or no package metadata found.
"""
import json
import os
import re
import sys

# Bucket order used when several licences apply together (AND): the highest
# rank wins so the most demanding declared term is never hidden.
BUCKET_RANK = {"permissive": 0, "unrecognised": 1, "weak-copyleft": 2, "strong-copyleft": 3, "custom": 4, "none": 5}
ACTION_RANK = {"accept": 0, "review": 1, "flag": 2}
# Reading caps: a licence header is within the first few KB; metadata files are small.
LICENSE_HEAD_CHARS = 6000
MAX_SMALL_FILE = 2 * 1024 * 1024
MAX_LOCK_FILE = 64 * 1024 * 1024
SKIP_DIRS = {".git", "__pycache__", ".hg", ".svn"}

NOT_CHECKED = [
    "Whether any licence is compatible with how the project is used or distributed.",
    "Licence texts beyond the first 6000 characters of one file per package.",
    "Packages with no local metadata (lock-file or go.sum names) have no declaration to read.",
    "Dependencies declared only in pyproject.toml, Cargo.toml or yarn/pnpm lock files.",
]

_PERMISSIVE = [
    "MIT", "MIT-0", "Apache-2.0", "Apache-1.1", "BSD-2-Clause", "BSD-3-Clause", "BSD-4-Clause",
    "0BSD", "ISC", "Unlicense", "CC0-1.0", "WTFPL", "Zlib", "BlueOak-1.0.0", "PSF-2.0",
    "Python-2.0", "BSL-1.0", "X11", "NCSA", "CC-BY-3.0", "CC-BY-4.0",
]
_WEAK = [
    "LGPL-2.0", "LGPL-2.0-only", "LGPL-2.0-or-later", "LGPL-2.0+", "LGPL-2.1", "LGPL-2.1-only",
    "LGPL-2.1-or-later", "LGPL-2.1+", "LGPL-3.0", "LGPL-3.0-only", "LGPL-3.0-or-later", "LGPL-3.0+",
    "MPL-1.1", "MPL-2.0", "EPL-1.0", "EPL-2.0", "CDDL-1.0", "CDDL-1.1", "CC-BY-SA-3.0", "CC-BY-SA-4.0",
]
_STRONG = [
    "GPL-2.0", "GPL-2.0-only", "GPL-2.0-or-later", "GPL-2.0+", "GPL-3.0", "GPL-3.0-only",
    "GPL-3.0-or-later", "GPL-3.0+", "AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later", "AGPL-3.0+",
    "SSPL-1.0", "EUPL-1.1", "EUPL-1.2",
]
SPDX_BUCKET = {}
for _ids, _bucket in ((_PERMISSIVE, "permissive"), (_WEAK, "weak-copyleft"), (_STRONG, "strong-copyleft")):
    for _i in _ids:
        SPDX_BUCKET[_i] = _bucket
SPDX_LOWER = {k.lower(): k for k in SPDX_BUCKET}
FAMILY_BUCKET = {"GPL": "strong-copyleft", "AGPL": "strong-copyleft", "SSPL": "strong-copyleft", "EUPL": "strong-copyleft",
                 "LGPL": "weak-copyleft", "MPL": "weak-copyleft", "EPL": "weak-copyleft", "CDDL": "weak-copyleft"}


def simplify(text):
    """Lower-case, drop the words licence/license/the, keep digits, dots and plus signs."""
    t = text.lower()
    t = re.sub(r"\blicen[cs]es?\b", " ", t)
    t = re.sub(r"\bthe\b", " ", t)
    t = re.sub(r"[^a-z0-9.+]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _suffix(s):
    if "+" in s or "later" in s or "newer" in s:
        return "-or-later"
    if "only" in s:
        return "-only"
    return ""


def _version(s):
    m = re.search(r"(\d(?:\.\d)?)", s)
    if not m:
        return None
    v = m.group(1)
    return v if "." in v else v + ".0"


def _family_id(family, s):
    v = _version(s)
    if v is None:
        return family + " (version unstated)", FAMILY_BUCKET[family]
    ident = "%s-%s%s" % (family, v, _suffix(s))
    if ident in SPDX_BUCKET:
        return ident, SPDX_BUCKET[ident]
    return ident, FAMILY_BUCKET[family]


def alias_lookup(s):
    """Map a simplified licence name to (id, bucket), or None when not recognised."""
    if not s:
        return None
    if s.startswith("see ") and " in " in s or s in ("unlicensed", "proprietary", "commercial", "custom", "other", "other proprietary", "all rights reserved") or s.startswith("proprietary"):
        return None  # handled as custom by the caller
    if s in ("public domain", "public domain dedicated"):
        return "public-domain", "permissive"
    if s in ("unlicense",):
        return "Unlicense", "permissive"
    if s in ("mit", "expat", "mit x11"):
        return "MIT", "permissive"
    if s == "mit no attribution":
        return "MIT-0", "permissive"
    m = re.match(r"^(?:asl|apache)(?: software)?(?: v| version)? ?(\d(?:\.\d)?)?$", s)
    if m:
        v = m.group(1)
        if v is None:
            return "Apache (version unstated)", "permissive"
        if v in ("2", "2.0"):
            return "Apache-2.0", "permissive"
        if v == "1.1":
            return "Apache-1.1", "permissive"
        return None
    if re.search(r"\bbsd\b", s) and not re.search(r"gpl|mit|apache", s):
        if re.search(r"\b3 clause|\b3c\b|\bnew\b|modified|revised|bsd 3\b", s):
            return "BSD-3-Clause", "permissive"
        if re.search(r"\b2 clause|simplified|freebsd|bsd 2\b", s):
            return "BSD-2-Clause", "permissive"
        if re.search(r"\b4 clause|original bsd|bsd 4\b", s):
            return "BSD-4-Clause", "permissive"
        return "BSD (clause count unstated)", "permissive"
    if s == "isc":
        return "ISC", "permissive"
    if s in ("zlib", "0bsd", "wtfpl", "cc0", "cc0 1.0", "cc0 1.0 universal"):
        return {"zlib": "Zlib", "0bsd": "0BSD", "wtfpl": "WTFPL"}.get(s, "CC0-1.0"), "permissive"
    if s in ("python software foundation", "psf", "psf 2.0", "python software foundation 2.0"):
        return "PSF-2.0", "permissive"
    if re.search(r"\bagpl|affero", s):
        return _family_id("AGPL", s)
    if re.search(r"\blgpl|lesser general public|library general public", s):
        return _family_id("LGPL", s)
    if re.search(r"\bgpl|general public", s):
        return _family_id("GPL", s)
    if re.search(r"^mpl|mozilla public", s):
        return _family_id("MPL", s)
    if re.search(r"^epl|eclipse public", s):
        return _family_id("EPL", s)
    if re.search(r"^cddl|common development and distribution", s):
        return _family_id("CDDL", s)
    if re.search(r"^eupl|european union public", s):
        return _family_id("EUPL", s)
    if re.search(r"^sspl|server side public", s):
        return "SSPL-1.0", "strong-copyleft"
    return None


def normalise_one(token):
    """Return (id, bucket, note) for one licence name as stated."""
    tok = token.strip()
    note = None
    m = re.match(r"^(.*?)\s+WITH\s+(.+)$", tok)
    base = tok
    if m:
        base, note = m.group(1).strip(), "exception stated: " + m.group(2).strip()
    low = base.lower()
    if low in SPDX_LOWER:
        ident = SPDX_LOWER[low]
        bucket = SPDX_BUCKET[ident]
    else:
        s = simplify(base)
        hit = alias_lookup(s)
        if hit:
            ident, bucket = hit
        elif s.startswith("see ") and " in " in s or s in ("unlicensed", "proprietary", "commercial", "custom", "other", "other proprietary", "all rights reserved") or s.startswith("proprietary"):
            ident, bucket = tok, "custom"
        else:
            ident, bucket = tok, "unrecognised"
    if m:
        ident = ident + " WITH " + m.group(2).strip()
    return ident, bucket, note


def parse_expression(text):
    """Split a declared string into OR groups of AND members (SPDX precedence).

    Only upper-case OR / AND split; lower-case words stay inside a name.
    Returns (groups, notes) where groups is a list of lists of (id, bucket).
    """
    t = text.strip()
    while t.startswith("(") and t.endswith(")") and t.count("(") == 1:
        t = t[1:-1].strip()
    notes = []
    if ("(" in t or ")" in t) and re.search(r"\s(?:OR|AND)\s", t):
        # Nested groups would be flattened wrongly; keep the text and ask for a human read.
        return [[(t, "unrecognised")]], ["nested parentheses are not parsed; read the expression by hand"]
    groups = []
    for part in re.split(r"\s+OR\s+", t):
        members = []
        for piece in re.split(r"\s+AND\s+", part):
            ident, bucket, note = normalise_one(piece.strip())
            if note:
                notes.append(note)
            members.append((ident, bucket))
        groups.append(members)
    if len(groups) == 1 and len(groups[0]) == 1 and groups[0][0][1] == "unrecognised" and "/" in t:
        parts = [normalise_one(x.strip()) for x in t.split("/")]
        if len(parts) > 1 and all(b != "unrecognised" for _, b, _n in parts):
            groups = [[(i, b)] for i, b, _n in parts]
            notes.append("slash read as alternatives")
    return groups, notes


def group_bucket(members):
    return max((b for _, b in members), key=lambda b: BUCKET_RANK[b])


def package_bucket(groups):
    if len(groups) == 1:
        return group_bucket(groups[0])
    return "dual"


def family_key(ident):
    s = ident.split(" WITH ")[0].lower()
    s = re.sub(r"(-only|-or-later|\+)$", "", s)
    return s


def families_compatible(a, b):
    """True when two ids can describe the same licence (an unstated version matches any)."""
    a, b = family_key(a), family_key(b)
    if a == b:
        return True
    for x, y in ((a, b), (b, a)):
        for tag in (" (version unstated)", " (clause count unstated)"):
            if x.endswith(tag) and y.startswith(x[: -len(tag)]):
                return True
    return False


def title_of(text):
    """Lower-cased first three non-empty lines: where a licence text names itself."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return re.sub(r"\s+", " ", " ".join(lines[:3]).lower())


MENTION_NAMES = (("gnu affero general public license", "AGPL"), ("gnu lesser general public license", "LGPL"),
                 ("gnu library general public license", "LGPL"), ("gnu general public license", "GPL"),
                 ("mozilla public license", "MPL"), ("eclipse public license", "EPL"))


def mentions(text, guess):
    """Licence families named somewhere in the text other than the one it opens as. Info only, never a conflict."""
    t = re.sub(r"\s+", " ", text.lower())
    own = (guess or "").split("-")[0]
    found = []
    for key, fam in MENTION_NAMES:
        if key in t and fam != own and fam not in found:
            found.append(fam)
    return found


def fingerprint(text):
    """Guess the licence a text opens with, from its title (first lines) and a few permissive phrases. None when unsure."""
    t = re.sub(r"\s+", " ", text.lower())
    head = title_of(text)
    heads = []
    for key, fam in (("gnu affero general public license", "AGPL"), ("gnu lesser general public license", "LGPL"),
                     ("gnu library general public license", "LGPL"), ("gnu general public license", "GPL")):
        i = head.find(key)
        if i >= 0:
            heads.append((i, fam))
    if heads:
        fam = min(heads)[1]
        window = t[:1500]
        if fam == "LGPL":
            return "LGPL-3.0" if "version 3" in window else ("LGPL-2.1" if "version 2.1" in window else None)
        if fam == "AGPL":
            return "AGPL-3.0"
        return "GPL-3.0" if "version 3" in window else ("GPL-2.0" if "version 2" in window else None)
    if "mozilla public license" in head and "2.0" in head:
        return "MPL-2.0"
    if "eclipse public license" in head:
        return "EPL-2.0" if "2.0" in head else ("EPL-1.0" if "1.0" in head else None)
    if "apache license" in t and "version 2.0" in t[:600]:
        return "Apache-2.0"
    if "unencumbered software released into the public domain" in t:
        return "Unlicense"
    if "permission is hereby granted, free of charge" in t:
        return "MIT"
    if "redistribution and use in source and binary forms" in t:
        if "endorse or promote" in t or "neither the name" in t:
            return "BSD-3-Clause"
        return "BSD-2-Clause"
    if "permission to use, copy, modify, and/or distribute this software for any purpose with or without fee" in t:
        if "provided that the above copyright notice" in t:
            return "ISC"
        return "0BSD"
    return None


def read_text(path, cap):
    try:
        if os.path.getsize(path) > cap:
            return None, "file larger than %d bytes, skipped" % cap
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8-sig", errors="replace"), None
    except OSError as exc:
        return None, str(exc)


def license_file_in(directory):
    """Return (path, head_text) of the best licence-like file in a directory, or (None, None)."""
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return None, None
    pat = re.compile(r"^(licen[cs]e|copying|unlicense)(\.[a-z]+)?$|^licen[cs]e[-_.]", re.I)
    for n in names:
        p = os.path.join(directory, n)
        if os.path.isfile(p) and pat.match(n):
            text, _ = read_text(p, MAX_SMALL_FILE)
            if text is not None:
                return p, text[:LICENSE_HEAD_CHARS]
    sub = os.path.join(directory, "licenses")
    if os.path.isdir(sub):
        return license_file_in(sub)
    return None, None


def rel(path, roots):
    for r in roots:
        try:
            if os.path.commonpath([os.path.abspath(path), os.path.abspath(r)]) == os.path.abspath(r):
                return os.path.relpath(path, os.path.dirname(os.path.abspath(r)) or ".").replace(os.sep, "/")
        except ValueError:
            continue
    return path.replace(os.sep, "/")


def npm_declared(data):
    lic = data.get("license")
    if isinstance(lic, str) and lic.strip():
        return lic.strip(), None
    if isinstance(lic, dict) and isinstance(lic.get("type"), str):
        return lic["type"].strip(), "license field is an object (legacy form)"
    old = data.get("licenses")
    if isinstance(old, list):
        types = [x.get("type") if isinstance(x, dict) else x for x in old]
        types = [x.strip() for x in types if isinstance(x, str) and x.strip()]
        if types:
            return " OR ".join(types), "legacy licenses array read as alternatives"
    return None, None


def parse_metadata_headers(text):
    """Return a list of (key, value) from the header block of a METADATA file."""
    headers = []
    for line in text.splitlines():
        if not line.strip():
            break
        if line[0] in " \t" and headers:
            k, v = headers[-1]
            headers[-1] = (k, v + "\n" + line.strip())
        elif ":" in line:
            k, v = line.split(":", 1)
            headers.append((k.strip(), v.strip()))
    return headers


def canon_py(name):
    return re.sub(r"[-_.]+", "-", name).lower()


class Inventory:
    def __init__(self, roots):
        self.roots = roots
        self.recs = {}
        self.unreadable = []
        self.npm_direct = None
        self.py_direct = None
        self.go_direct = None
        self.skipped_symlinks = 0

    def add(self, rec):
        key = (rec["ecosystem"], rec["name"] if rec["ecosystem"] != "pypi" else canon_py(rec["name"]), rec["version"])
        old = self.recs.get(key)
        if old is None or (not old["installed"] and rec["installed"]):
            self.recs[key] = rec

    def bad(self, path, error):
        self.unreadable.append({"path": rel(path, self.roots), "error": error})

    def read_npm_dir(self, nm):
        try:
            entries = sorted(os.listdir(nm))
        except OSError as exc:
            self.bad(nm, str(exc))
            return
        pkgdirs = []
        for e in entries:
            if e.startswith("."):
                continue
            p = os.path.join(nm, e)
            if os.path.islink(p):
                self.skipped_symlinks += 1
                continue
            if e.startswith("@") and os.path.isdir(p):
                for s in sorted(os.listdir(p)):
                    sp = os.path.join(p, s)
                    if os.path.islink(sp):
                        self.skipped_symlinks += 1
                    elif os.path.isdir(sp):
                        pkgdirs.append(sp)
            elif os.path.isdir(p):
                pkgdirs.append(p)
        for d in pkgdirs:
            pj = os.path.join(d, "package.json")
            if not os.path.isfile(pj):
                continue
            text, err = read_text(pj, MAX_SMALL_FILE)
            if text is None:
                self.bad(pj, err)
                continue
            try:
                data = json.loads(text)
            except ValueError as exc:
                self.bad(pj, "invalid JSON: %s" % exc)
                continue
            if not isinstance(data, dict):
                self.bad(pj, "package.json is not an object")
                continue
            declared, note = npm_declared(data)
            lf, head = license_file_in(d)
            rec = {"ecosystem": "npm", "name": str(data.get("name") or os.path.basename(d)), "version": str(data.get("version") or ""),
                   "declared": declared, "source_file": rel(pj, self.roots), "installed": True, "notes": [note] if note else [],
                   "file": rel(lf, self.roots) if lf else None, "file_guess": fingerprint(head) if head else None,
                   "file_mentions": mentions(head, fingerprint(head)) if head else []}
            self.add(rec)

    def read_dist_info(self, di):
        meta = os.path.join(di, "METADATA")
        text, err = read_text(meta, MAX_SMALL_FILE)
        if text is None:
            self.bad(meta, err)
            return
        headers = parse_metadata_headers(text)
        name = next((v for k, v in headers if k.lower() == "name"), None)
        version = next((v for k, v in headers if k.lower() == "version"), "")
        if not name:
            self.bad(meta, "METADATA has no Name header")
            return
        expr = next((v for k, v in headers if k.lower() == "license-expression"), None)
        lic_field = next((v for k, v in headers if k.lower() == "license"), None)
        classes = []
        for k, v in headers:
            if k.lower() == "classifier" and v.startswith("License ::"):
                last = v.split("::")[-1].strip()
                if last and last.lower() not in ("osi approved", "license"):
                    classes.append(last)
        notes = []
        free_text = None
        if lic_field is not None and lic_field.strip().lower() in ("", "unknown", "none"):
            lic_field = None
        if lic_field is not None and ("\n" in lic_field or len(lic_field) > 120):
            free_text = lic_field
            lic_field = None
            notes.append("License field holds free text, not a name")
        declared = None
        extra_conflicts = []
        if expr and expr.strip():
            declared = expr.strip()
            notes.append("read from License-Expression")
        elif lic_field:
            declared = lic_field.strip()
            notes.append("read from License field")
        elif classes:
            declared = " OR ".join(classes)
            notes.append("read from Classifier lines; multiple classifiers read as alternatives" if len(classes) > 1 else "read from Classifier line")
        if declared and lic_field and classes and not (expr and expr.strip()):
            field_ids = [i for g in parse_expression(lic_field)[0] for i, _ in g]
            class_ids = [normalise_one(c)[0] for c in classes]
            if not any(families_compatible(a, b) for a in field_ids for b in class_ids):
                extra_conflicts.append({"kind": "metadata-fields-disagree", "declared": lic_field, "other": "; ".join(classes)})  # the Classifier lines
        lf, head = license_file_in(di)
        guess = fingerprint(head) if head else None
        if guess is None and free_text:
            guess = fingerprint(free_text)
        rec = {"ecosystem": "pypi", "name": name, "version": version, "declared": declared, "source_file": rel(meta, self.roots),
               "installed": True, "notes": notes, "file": rel(lf, self.roots) if lf else None, "file_guess": guess,
               "file_mentions": mentions(head or free_text or "", guess),
               "extra_conflicts": extra_conflicts}
        self.add(rec)

    def read_lock_names(self, path, name):
        text, err = read_text(path, MAX_LOCK_FILE)
        if text is None:
            self.bad(path, err)
            return
        src = rel(path, self.roots)
        if name == "package-lock.json":
            try:
                data = json.loads(text)
            except ValueError as exc:
                self.bad(path, "invalid JSON: %s" % exc)
                return
            pk = data.get("packages") if isinstance(data, dict) else None
            if isinstance(pk, dict):
                for key, val in pk.items():
                    if not key or not isinstance(val, dict) or val.get("link"):
                        continue
                    nm = key.split("node_modules/")[-1]
                    declared, note = npm_declared(val)
                    self.add({"ecosystem": "npm", "name": nm, "version": str(val.get("version") or ""), "declared": declared,
                              "source_file": src, "installed": False, "notes": ([note] if note else []) + ["from lock file, not installed locally"],
                              "file": None, "file_guess": None})
            elif isinstance(data, dict) and isinstance(data.get("dependencies"), dict):
                self._walk_v1(data["dependencies"], src)
        elif name in ("poetry.lock", "Cargo.lock"):
            eco = "pypi" if name == "poetry.lock" else "cargo"
            for m in re.finditer(r'\[\[package\]\]\s*\r?\nname = "([^"]+)"\s*\r?\nversion = "([^"]+)"', text):
                self.add({"ecosystem": eco, "name": m.group(1), "version": m.group(2), "declared": None, "source_file": src,
                          "installed": False, "notes": ["name from lock file; no licence metadata in it"], "file": None, "file_guess": None})
        elif name == "go.sum":
            seen = set()
            for line in text.splitlines():
                parts = line.split()
                if len(parts) < 3:
                    continue
                mod, ver = parts[0], re.sub(r"/go\.mod$", "", parts[1])
                if (mod, ver) in seen:
                    continue
                seen.add((mod, ver))
                self.add({"ecosystem": "go", "name": mod, "version": ver, "declared": None, "source_file": src, "installed": False,
                          "notes": ["go.sum lists module names and hashes only"], "file": None, "file_guess": None})

    def _walk_v1(self, deps, src):
        for nm, val in deps.items():
            if not isinstance(val, dict):
                continue
            self.add({"ecosystem": "npm", "name": nm, "version": str(val.get("version") or ""), "declared": None, "source_file": src,
                      "installed": False, "notes": ["name from lock file; no licence metadata in it"], "file": None, "file_guess": None})
            if isinstance(val.get("dependencies"), dict):
                self._walk_v1(val["dependencies"], src)

    def read_manifest(self, path, name):
        text, err = read_text(path, MAX_SMALL_FILE)
        if text is None:
            self.bad(path, err)
            return
        if name == "package.json":
            try:
                data = json.loads(text)
            except ValueError as exc:
                self.bad(path, "invalid JSON: %s" % exc)
                return
            if isinstance(data, dict):
                self.npm_direct = self.npm_direct or set()
                for sect in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
                    if isinstance(data.get(sect), dict):
                        self.npm_direct.update(data[sect].keys())
        elif name.startswith("requirements") and name.endswith(".txt"):
            self.py_direct = self.py_direct or set()
            for line in text.splitlines():
                line = line.split("#", 1)[0].strip()
                if not line or line.startswith("-") or "://" in line.split(";")[0].split("@")[0]:
                    continue
                m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
                if m:
                    self.py_direct.add(canon_py(m.group(1)))
        elif name == "go.mod":
            self.go_direct = self.go_direct or set()
            in_block = False
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("require ("):
                    in_block = True
                    continue
                if in_block and s == ")":
                    in_block = False
                    continue
                body = None
                if in_block:
                    body = s
                elif s.startswith("require "):
                    body = s[len("require "):].strip()
                if body and "// indirect" not in body:
                    parts = body.split()
                    if parts:
                        self.go_direct.add(parts[0])

    def walk(self):
        for root in self.roots:
            for base, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                # Judge "inside an installed tree" from the scanned root downward, so a
                # project that happens to live under such a folder name is not misread.
                parts = [p.lower() for p in os.path.relpath(base, root).split(os.sep)] + [os.path.basename(os.path.abspath(root)).lower()]
                in_installed = "node_modules" in parts or "site-packages" in parts or "dist-packages" in parts
                if os.path.basename(base) == "node_modules":
                    self.read_npm_dir(base)
                if base.endswith(".dist-info") and "METADATA" in files:
                    self.read_dist_info(base)
                for f in sorted(files):
                    p = os.path.join(base, f)
                    if f in ("package-lock.json", "poetry.lock", "Cargo.lock", "go.sum") and not in_installed:
                        self.read_lock_names(p, f)
                    elif not in_installed and (f in ("package.json", "go.mod") or (f.startswith("requirements") and f.endswith(".txt"))):
                        self.read_manifest(p, f)


def load_policy(path):
    text, err = read_text(path, MAX_SMALL_FILE)
    if text is None:
        raise ValueError("cannot read policy file %s: %s" % (path, err))
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise ValueError("policy file is not valid JSON: %s" % exc)
    if not isinstance(data, dict):
        raise ValueError("policy file must be a JSON object")
    extra = set(data) - {"buckets", "licenses", "packages", "note"}
    if extra:
        raise ValueError("policy has unknown keys %s; allowed: buckets, licenses, packages, note" % sorted(extra))
    pol = {"buckets": {}, "licenses": {}, "packages": {}}
    for k, v in (data.get("buckets") or {}).items():
        if k not in BUCKET_RANK or v not in ACTION_RANK:
            raise ValueError("buckets: '%s': '%s' is invalid; bucket must be one of %s and action one of %s" % (k, v, sorted(BUCKET_RANK), sorted(ACTION_RANK)))
        pol["buckets"][k] = v
    for k, v in (data.get("licenses") or {}).items():
        if v not in ACTION_RANK:
            raise ValueError("licenses: '%s': action '%s' must be one of %s" % (k, v, sorted(ACTION_RANK)))
        pol["licenses"][k.lower()] = v
    for k, v in (data.get("packages") or {}).items():
        if isinstance(v, str):
            v = {"action": v}
        if not isinstance(v, dict) or v.get("action") not in ACTION_RANK:
            raise ValueError("packages: '%s' needs an action of %s (optionally with a reason)" % (k, sorted(ACTION_RANK)))
        pol["packages"][k] = {"action": v["action"], "reason": str(v.get("reason", ""))}
    return pol


def member_action(ident, bucket, pol):
    return pol["licenses"].get(ident.lower(), pol["buckets"].get(bucket, "review"))


def evaluate(rec, groups, bucket, pol):
    """Return (policy_action or None, review_needed, note or None)."""
    if pol is None:
        needs = min(any(b != "permissive" for _, b in g) for g in groups)
        return None, bool(needs), None
    for key in (rec["ecosystem"] + ":" + rec["name"], rec["name"]):
        if key in pol["packages"]:
            act = pol["packages"][key]
            return act["action"], act["action"] != "accept", "package-level policy entry" + (": " + act["reason"] if act["reason"] else "")
    per_group = []
    for g in groups:
        per_group.append(max((member_action(i, b, pol) for i, b in g), key=lambda a: ACTION_RANK[a]))
    act = min(per_group, key=lambda a: ACTION_RANK[a])
    note = "choice of terms: least severe policy action among the alternatives; the project must record which is elected" if len(groups) > 1 else None
    return act, act != "accept", note


def build_report(inv, pol):
    packages, unknown, conflicts, mention_rows = [], [], [], []
    direct_sets = {"npm": inv.npm_direct, "pypi": inv.py_direct, "go": inv.go_direct, "cargo": None}
    for key in sorted(inv.recs, key=lambda k: (k[0], k[1], k[2])):
        rec = inv.recs[key]
        declared = rec["declared"]
        if declared:
            groups, enotes = parse_expression(declared)
        else:
            groups, enotes = [[("(none)", "none")]], []
        bucket = package_bucket(groups)
        notes = list(rec["notes"]) + enotes
        ds = direct_sets.get(rec["ecosystem"])
        if ds is None:
            direct = None
        elif rec["ecosystem"] == "pypi":
            direct = canon_py(rec["name"]) in ds
        else:
            direct = rec["name"] in ds
        action, needs, pnote = evaluate(rec, groups, bucket, pol)
        if pnote:
            notes.append(pnote)
        ident = {"ecosystem": rec["ecosystem"], "name": rec["name"], "version": rec["version"]}
        norm = " OR ".join(" AND ".join(i for i, _ in g) for g in groups) if declared else None
        packages.append(dict(ident, declared=declared, normalised=norm, bucket=bucket,
                             expression=[[{"id": i, "bucket": b} for i, b in g] for g in groups] if declared else [],
                             source_file=rec["source_file"], direct=direct, installed=rec["installed"],
                             policy_action=action, review_needed=needs, notes=notes))
        if not declared:
            reason = "no-declaration" if rec["installed"] else "not-installed-no-metadata"
            detail = "licence file text resembles " + rec["file_guess"] if rec.get("file_guess") else None
            unknown.append(dict(ident, reason=reason, detail=detail))
        elif bucket == "custom":
            unknown.append(dict(ident, reason="custom-or-unlicensed", detail=declared))
        elif any(b == "unrecognised" for g in groups for _, b in g):
            unknown.append(dict(ident, reason="unrecognised-name", detail=declared))
        guess = rec.get("file_guess")
        if declared and guess:
            ids = [i for g in groups for i, b in g if b not in ("custom", "unrecognised", "none")]
            if ids and not any(families_compatible(guess, i) for i in ids):
                conflicts.append(dict(ident, kind="licence-file-differs", declared=declared, other=guess, file=rec["file"]))
        if rec.get("file_mentions"):
            mention_rows.append(dict(ident, kind="mention", declared=declared, mentions=rec["file_mentions"], file=rec["file"]))
        for ec in rec.get("extra_conflicts", []):
            conflicts.append(dict(ident, kind=ec["kind"], declared=ec["declared"], other=ec["other"], file=None))
    by_bucket, by_eco = {}, {}
    for p in packages:
        by_bucket[p["bucket"]] = by_bucket.get(p["bucket"], 0) + 1
        by_eco[p["ecosystem"]] = by_eco.get(p["ecosystem"], 0) + 1
    summary = {
        "packages": len(packages),
        "direct": sum(1 for p in packages if p["direct"] is True),
        "transitive": sum(1 for p in packages if p["direct"] is False),
        "direct_unknown_for": sum(1 for p in packages if p["direct"] is None),
        "by_bucket": dict(sorted(by_bucket.items())),
        "by_ecosystem": dict(sorted(by_eco.items())),
        "unknown": len(unknown),
        "conflicts": len(conflicts),
        "flagged": sum(1 for p in packages if p["policy_action"] == "flag"),
        "review_needed": sum(1 for p in packages if p["review_needed"]),
    }
    return {
        "tool": "license_inventory", "command": "scan", "roots": [r.replace(os.sep, "/") for r in inv.roots],
        "policy_supplied": pol is not None, "packages": packages, "unknown": unknown, "conflicts": conflicts, "mentions": mention_rows,
        "unreadable": inv.unreadable, "skipped_symlinks": inv.skipped_symlinks, "summary": summary,
        "statement": "These are declared licences read from local files. This is not a compliance or legal conclusion.",
        "not_checked": NOT_CHECKED,
    }


def cmd_normalise(items):
    out = []
    for text in items:
        groups, notes = parse_expression(text)
        out.append({"input": text, "normalised": " OR ".join(" AND ".join(i for i, _ in g) for g in groups),
                    "bucket": package_bucket(groups), "expression": [[{"id": i, "bucket": b} for i, b in g] for g in groups], "notes": notes})
    print(json.dumps({"tool": "license_inventory", "command": "normalise", "results": out}, indent=2, ensure_ascii=False))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if not argv or argv[0] not in ("scan", "normalise"):
        print("usage: license_inventory.py scan PATH [PATH ...] [--policy policy.json] | normalise NAME [NAME ...]", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "normalise":
        if not rest:
            print("normalise needs at least one licence string", file=sys.stderr)
            return 2
        return cmd_normalise(rest)
    policy_path = None
    paths = []
    i = 0
    while i < len(rest):
        if rest[i] == "--policy":
            if i + 1 >= len(rest):
                print("--policy needs a file path", file=sys.stderr)
                return 2
            policy_path = rest[i + 1]
            i += 2
        else:
            paths.append(rest[i])
            i += 1
    if not paths:
        print("scan needs at least one PATH (a project folder, node_modules, or site-packages)", file=sys.stderr)
        return 2
    for p in paths:
        if not os.path.isdir(p):
            print("not a folder: %s" % p, file=sys.stderr)
            return 2
    pol = None
    if policy_path:
        try:
            pol = load_policy(policy_path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
    inv = Inventory(paths)
    inv.walk()
    if not inv.recs:
        print("no package metadata found under the given paths (looked for node_modules, *.dist-info, lock files, go.sum)", file=sys.stderr)
        return 2
    report = build_report(inv, pol)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    s = report["summary"]
    return 1 if (s["unknown"] or s["conflicts"] or s["flagged"]) else 0


if __name__ == "__main__":
    sys.exit(main())
