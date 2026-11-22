#!/usr/bin/env python3
"""Find the installed version of a package and the local files where its docs live.

Usage:
    python find_local_docs.py <project_dir> <package> [--ecosystem all|npm|python|go]

Reads (never writes, no network, no subprocess):
    npm:    package.json, package-lock.json, pnpm-lock.yaml, yarn.lock,
            node_modules/<pkg>/ (also pnpm's node_modules/.pnpm/), node_modules/@types/
    python: requirements*.txt, poetry.lock, uv.lock, virtualenv site-packages
            (.venv, venv, env, .env, __pypackages__), <pkg>.dist-info/METADATA
    go:     go.mod, go.sum, vendor/modules.txt, vendor/<module>/
    node_modules and the npm/poetry/uv lockfiles are also looked up in up to 3 parent
    directories of the project (workspace roots). Nothing else outside it is opened.

Prints ONE JSON object to stdout (schema in SKILL.md). Every version entry carries
the file and 1-based line where the version was read, so it can be cited.

Exit codes: 0 a version or an installed copy was found; 1 nothing found for the
package; 2 usage error (message is also a JSON object with an "error" key).
"""
import argparse
import glob
import json
import os
import re
import sys

SCHEMA_VERSION = 1
# A lockfile bigger than this is skipped with a warning; real lockfiles are well below it.
MAX_READ_BYTES = 50 * 1024 * 1024
# Counting lines of a larger file would be slow and useless for deciding what to read first.
MAX_COUNT_BYTES = 5 * 1024 * 1024
# Cap on listed files per category so a huge types tree cannot flood the agent's context.
MAX_LIST = 20
# How many parent directories may hold a hoisted node_modules (monorepo root).
PARENT_LEVELS = 3
# Virtualenv folder names by convention.
VENV_NAMES = (".venv", "venv", "env", ".env", "virtualenv")
CHANGELOG_PREFIXES = ("changelog", "changes", "history", "releases", "news")
ECOSYSTEMS = ("npm", "python", "go")

# Order in which kinds decide the resolved version: what runs, then what is locked,
# then what is pinned or merely declared.
KIND_PRIORITY = ("installed", "locked", "pinned", "declared", "checksum_listed")


def out_json(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=True, allow_nan=False, indent=2) + "\n")


def read_text(path, warnings=None):
    try:
        if os.path.getsize(path) > MAX_READ_BYTES:
            if warnings is not None:
                warnings.append("skipped %s: larger than %d MB" % (path, MAX_READ_BYTES // (1024 * 1024)))
            return None
        with open(path, "rb") as fh:
            return fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None


def count_lines(path):
    try:
        size = os.path.getsize(path)
        if size > MAX_COUNT_BYTES:
            return None
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def find_line(lines, needle):
    for i, line in enumerate(lines, 1):
        if needle in line:
            return i
    return None


def norm_py(name):
    return re.sub(r"[-_.]+", "-", name).lower()


class Report:
    def __init__(self, root, package):
        self.root = root
        self.package = package
        self.versions = []
        self.installed = []
        self.docs = []
        self.warnings = []
        self._seen = set()

    def rel(self, path):
        try:
            r = os.path.relpath(path, self.root)
        except ValueError:
            r = path
        return r.replace("\\", "/")

    def add_version(self, eco, file, kind, version, line=None, note=None):
        if not version:
            return
        key = (eco, self.rel(file), kind, version)
        if key in self._seen:
            return
        self._seen.add(key)
        entry = {"ecosystem": eco, "kind": kind, "version": version, "file": self.rel(file), "line": line}
        if note:
            entry["note"] = note
        self.versions.append(entry)

    def add_doc(self, eco, kind, path, note=None):
        if not os.path.isfile(path):
            return
        key = ("doc", self.rel(path))
        if key in self._seen:
            return
        self._seen.add(key)
        try:
            size = os.path.getsize(path)
        except OSError:
            size = None
        entry = {"ecosystem": eco, "kind": kind, "path": self.rel(path), "bytes": size, "lines": count_lines(path)}
        if note:
            entry["note"] = note
        self.docs.append(entry)

    def add_installed(self, eco, directory, version, line_file=None, line=None, extra=None, kind="installed"):
        entry = {"ecosystem": eco, "path": self.rel(directory), "version": version}
        if extra:
            entry.update(extra)
        self.installed.append(entry)
        if version:
            self.add_version(eco, line_file or directory, kind, version, line)


# ---------------------------------------------------------------- npm lockfiles

def scan_package_json(rep, root, pkg):
    path = os.path.join(root, "package.json")
    text = read_text(path, rep.warnings)
    if text is None:
        return
    try:
        data = json.loads(text)
    except ValueError:
        rep.warnings.append("package.json is not valid JSON")
        return
    lines = text.splitlines()
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(section) if isinstance(data, dict) else None
        if isinstance(deps, dict):
            for name, rng in deps.items():
                if name.lower() == pkg.lower() and isinstance(rng, str):
                    rep.add_version("npm", path, "declared", rng, find_line(lines, '"%s"' % name),
                                    "range declared in %s, not an installed version" % section)


def scan_package_lock(rep, root, pkg):
    path = os.path.join(root, "package-lock.json")
    text = read_text(path, rep.warnings)
    if text is None:
        return
    try:
        data = json.loads(text)
    except ValueError:
        rep.warnings.append("package-lock.json is not valid JSON")
        return
    lines = text.splitlines()
    want = pkg.lower()
    packages = data.get("packages") if isinstance(data, dict) else None
    if isinstance(packages, dict):
        for key, meta in packages.items():
            if not isinstance(meta, dict):
                continue
            k = key.lower()
            top = k == "node_modules/" + want
            if top or k.endswith("/node_modules/" + want):
                rep.add_version("npm", path, "locked" if top else "locked_nested", meta.get("version"),
                                find_line(lines, '"%s"' % key),
                                None if top else "nested copy at " + key)
    else:
        def walk(deps, top):
            for name, meta in deps.items():
                if not isinstance(meta, dict):
                    continue
                if name.lower() == want:
                    rep.add_version("npm", path, "locked" if top else "locked_nested", meta.get("version"),
                                    find_line(lines, '"%s"' % name), None if top else "nested copy")
                if isinstance(meta.get("dependencies"), dict):
                    walk(meta["dependencies"], False)
        if isinstance(data, dict) and isinstance(data.get("dependencies"), dict):
            walk(data["dependencies"], True)


PNPM_NEW = re.compile(r"""^ {2}['"]?/?(@[^/@'"\s]+/[^@'"\s:]+|[^@'"\s/:]+)@(\d[^'"\s:(]*)""")
PNPM_OLD = re.compile(r"""^ {2}['"]?/(@[^/'"\s]+/[^/'"\s]+|[^/'"\s]+)/(\d[^'"\s:_(]*)""")


def scan_pnpm_lock(rep, root, pkg):
    path = os.path.join(root, "pnpm-lock.yaml")
    text = read_text(path, rep.warnings)
    if text is None:
        return
    section = None
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^([A-Za-z]+):", line)
        if m:
            section = m.group(1)
            continue
        if section not in ("packages", "snapshots"):
            continue
        hit = PNPM_NEW.match(line) or PNPM_OLD.match(line)
        if hit and hit.group(1).lower() == pkg.lower():
            rep.add_version("npm", path, "locked", hit.group(2), i)


def scan_yarn_lock(rep, root, pkg):
    path = os.path.join(root, "yarn.lock")
    text = read_text(path, rep.warnings)
    if text is None:
        return
    matching = False
    for i, line in enumerate(text.splitlines(), 1):
        if line and not line[0].isspace() and not line.startswith("#") and line.rstrip().endswith(":"):
            matching = False
            for spec in line.rstrip()[:-1].split(","):
                spec = spec.strip().strip("\"'")
                at = spec.find("@", 1)
                if at > 0 and spec[:at].lower() == pkg.lower():
                    matching = True
            continue
        if matching:
            m = re.match(r"^\s+version:?\s+\"?([^\"\s]+)\"?\s*$", line)
            if m:
                rep.add_version("npm", path, "locked", m.group(1), i)
                matching = False


# ------------------------------------------------------------- python lockfiles

def scan_toml_lock(rep, path, pkg_norm):
    """poetry.lock and uv.lock share the [[package]] table layout with name and version keys."""
    text = read_text(path, rep.warnings)
    if text is None:
        return
    state = {"name": None, "version": None, "line": None}

    def flush():
        if state["name"] and state["version"] and norm_py(state["name"]) == pkg_norm:
            rep.add_version("python", path, "locked", state["version"], state["line"])
        state.update(name=None, version=None, line=None)

    in_pkg = False
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s == "[[package]]":
            flush()
            in_pkg = True
            continue
        if s.startswith("["):
            if in_pkg:
                flush()
            in_pkg = False
            continue
        if in_pkg:
            m = re.match(r'^name\s*=\s*"([^"]+)"', s)
            if m:
                state["name"] = m.group(1)
            m = re.match(r'^version\s*=\s*"([^"]+)"', s)
            if m and state["version"] is None:
                state["version"], state["line"] = m.group(1), i
    flush()


REQ_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*(.*)$")


def scan_requirements(rep, root, pkg_norm):
    files = set(glob.glob(os.path.join(root, "requirements*.txt")))
    files.update(glob.glob(os.path.join(root, "requirements", "*.txt")))
    for path in sorted(files):
        text = read_text(path, rep.warnings)
        if text is None:
            continue
        for i, raw in enumerate(text.splitlines(), 1):
            s = raw.split(" #")[0].strip()
            if not s or s.startswith(("#", "-")):
                continue
            m = REQ_LINE.match(s)
            if not m or norm_py(m.group(1)) != pkg_norm:
                continue
            spec = m.group(3).split(";")[0].split(" --")[0].strip()
            pin = re.match(r"^===?\s*([A-Za-z0-9._+!-]+)", spec)
            if pin:
                rep.add_version("python", path, "pinned", pin.group(1), i)
            elif spec:
                rep.add_version("python", path, "declared", spec, i, "specifier, not an installed version")
            else:
                rep.add_version("python", path, "declared", "(unconstrained)", i, "no version specifier")


# --------------------------------------------------------------------- go files

def scan_go(rep, root, pkg):
    sumf = os.path.join(root, "go.sum")
    text = read_text(sumf, rep.warnings)
    if text is not None:
        for i, line in enumerate(text.splitlines(), 1):
            parts = line.split()
            if len(parts) >= 2 and parts[0] == pkg and not parts[1].endswith("/go.mod"):
                rep.add_version("go", sumf, "checksum_listed", parts[1], i,
                                "go.sum may list several versions; go.mod decides which one is built")
    modf = os.path.join(root, "go.mod")
    text = read_text(modf, rep.warnings)
    if text is not None:
        in_block = False
        for i, line in enumerate(text.splitlines(), 1):
            s = line.split("//")[0].strip()
            if s.startswith("require ("):
                in_block = True
                continue
            if in_block and s == ")":
                in_block = False
                continue
            if s.startswith("replace") and pkg in s:
                rep.warnings.append("go.mod line %d replaces %s: the code used is not the published module" % (i, pkg))
            body = s[len("require"):].strip() if s.startswith("require ") else (s if in_block else "")
            parts = body.split()
            if len(parts) >= 2 and parts[0] == pkg:
                rep.add_version("go", modf, "declared", parts[1], i, "selected by go.mod require")
    vend = os.path.join(root, "vendor")
    mods = os.path.join(vend, "modules.txt")
    text = read_text(mods, rep.warnings)
    if text is not None:
        for i, line in enumerate(text.splitlines(), 1):
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "#" and parts[1] == pkg:
                rep.add_version("go", mods, "installed", parts[2], i, "vendored copy")
    vdir = os.path.join(vend, *pkg.split("/"))
    if os.path.isdir(vdir):
        rep.add_installed("go", vdir, None)
        for name in sorted(os.listdir(vdir)):
            low = name.lower()
            full = os.path.join(vdir, name)
            if low.startswith("readme"):
                rep.add_doc("go", "readme", full)
            elif low.startswith(CHANGELOG_PREFIXES):
                rep.add_doc("go", "changelog", full)
            elif low == "doc.go":
                rep.add_doc("go", "source_docs", full, "package doc comment")
        gofiles = [n for n in sorted(os.listdir(vdir)) if n.endswith(".go") and not n.endswith("_test.go") and n != "doc.go"]
        for name in gofiles[:MAX_LIST]:
            rep.add_doc("go", "source", os.path.join(vdir, name))
    else:
        if any(v["ecosystem"] == "go" for v in rep.versions):
            rep.warnings.append("no vendor/ copy of the Go module; read the module cache with `go list -m -f '{{.Dir}}' %s` (offline)" % pkg)


# ------------------------------------------------------------ installed: node

def collect_strings(node, found):
    if isinstance(node, str):
        found.append(node)
    elif isinstance(node, dict):
        for v in node.values():
            collect_strings(v, found)
    elif isinstance(node, list):
        for v in node:
            collect_strings(v, found)


def scan_npm_dir(rep, pkgdir, kind="installed"):
    pjson = os.path.join(pkgdir, "package.json")
    text = read_text(pjson, rep.warnings)
    data = {}
    if text is not None:
        try:
            data = json.loads(text)
        except ValueError:
            rep.warnings.append("%s/package.json is not valid JSON" % rep.rel(pkgdir))
    if not isinstance(data, dict):
        data = {}
    version = data.get("version") if isinstance(data.get("version"), str) else None
    extra = {}
    for key in ("homepage",):
        if isinstance(data.get(key), str):
            extra[key] = data[key]
    repo = data.get("repository")
    if isinstance(repo, dict) and isinstance(repo.get("url"), str):
        extra["repository"] = repo["url"]
    elif isinstance(repo, str):
        extra["repository"] = repo
    line = find_line(text.splitlines(), '"version"') if text else None
    rep.add_installed("npm", pkgdir, version, pjson, line, extra, kind)
    if data.get("deprecated"):
        rep.warnings.append("%s is marked deprecated by its own package.json: %s" % (rep.rel(pkgdir), str(data["deprecated"])[:200]))
    try:
        names = sorted(os.listdir(pkgdir))
    except OSError:
        return
    for name in names:
        low = name.lower()
        full = os.path.join(pkgdir, name)
        if low.startswith("readme") and os.path.isfile(full):
            rep.add_doc("npm", "readme", full)
        elif low.startswith(CHANGELOG_PREFIXES) and os.path.isfile(full):
            rep.add_doc("npm", "changelog", full)
    # Type declarations: the declared entries first, then the conventional fallback.
    declared = []
    for key in ("types", "typings"):
        if isinstance(data.get(key), str):
            declared.append(data[key])
    exp = []
    collect_strings(data.get("exports"), exp)
    declared.extend(s for s in exp if re.search(r"\.d\.[cm]?ts$", s))
    seen = False
    for rel_path in declared:
        full = os.path.normpath(os.path.join(pkgdir, rel_path))
        if os.path.isfile(full):
            rep.add_doc("npm", "types", full, "declared in package.json")
            seen = True
        else:
            rep.warnings.append("%s declares types file %s that is not on disk" % (rep.rel(pkgdir), rel_path))
    if not seen:
        fallback = os.path.join(pkgdir, "index.d.ts")
        if os.path.isfile(fallback):
            rep.add_doc("npm", "types", fallback, "conventional location, not declared")
            seen = True
    entries = []
    for key in ("main", "module"):
        if isinstance(data.get(key), str):
            entries.append(data[key])
    for rel_path in entries:
        full = os.path.normpath(os.path.join(pkgdir, rel_path))
        rep.add_doc("npm", "entry", full, "package.json main or module")
    # Local docs folders (markdown only, shallow).
    for dname in ("docs", "doc"):
        ddir = os.path.join(pkgdir, dname)
        if not os.path.isdir(ddir):
            continue
        count = 0
        for base, dirs, files in os.walk(ddir):
            dirs.sort()
            if base[len(ddir):].count(os.sep) >= 2:
                dirs[:] = []
            for f in sorted(files):
                if f.lower().endswith((".md", ".mdx")) and count < MAX_LIST:
                    rep.add_doc("npm", "docs_dir", os.path.join(base, f))
                    count += 1
    # Any other .d.ts in the package root or dist-like folders, capped.
    if not seen:
        count = 0
        for base, dirs, files in os.walk(pkgdir):
            dirs[:] = sorted(d for d in dirs if d != "node_modules")
            if base[len(pkgdir):].count(os.sep) >= 2:
                dirs[:] = []
            for f in sorted(files):
                if re.search(r"\.d\.[cm]?ts$", f) and count < MAX_LIST:
                    rep.add_doc("npm", "types", os.path.join(base, f), "found by search, no declared entry")
                    count += 1


def ancestor_dirs(root):
    """The project folder followed by up to PARENT_LEVELS parents."""
    bases = []
    cur = root
    for _ in range(PARENT_LEVELS + 1):
        bases.append(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return bases


def scan_node_modules(rep, root, pkg):
    bases = ancestor_dirs(root)
    seen_real = set()
    for base in bases:
        nm = os.path.join(base, "node_modules")
        if not os.path.isdir(nm):
            continue
        parts = pkg.split("/")
        cands = [os.path.join(nm, *parts)]
        pnpm = os.path.join(nm, ".pnpm")
        if os.path.isdir(pnpm):
            cands.extend(sorted(glob.glob(os.path.join(glob.escape(pnpm), glob.escape(pkg.replace("/", "+")) + "@*", "node_modules", *parts))))
        for cand in cands:
            real = os.path.realpath(cand)
            if os.path.isdir(cand) and real not in seen_real:
                seen_real.add(real)
                scan_npm_dir(rep, cand)
        types_name = ("@types/" + pkg[1:].replace("/", "__")) if pkg.startswith("@") else "@types/" + pkg
        tdir = os.path.join(nm, *types_name.split("/"))
        if os.path.isdir(tdir) and os.path.realpath(tdir) not in seen_real:
            seen_real.add(os.path.realpath(tdir))
            before = len(rep.installed)
            scan_npm_dir(rep, tdir, "installed_types")
            for entry in rep.installed[before:]:
                entry["role"] = "DefinitelyTyped stub; its version follows the library only by major.minor"


# --------------------------------------------------------- installed: python

def site_packages_dirs(root):
    found = []
    homes = [os.path.join(root, n) for n in VENV_NAMES] + [root]
    for home in homes:
        found.append(os.path.join(home, "Lib", "site-packages"))
        found.extend(glob.glob(os.path.join(glob.escape(home), "lib", "python*", "site-packages")))
        found.extend(glob.glob(os.path.join(glob.escape(home), "lib64", "python*", "site-packages")))
    found.extend(glob.glob(os.path.join(glob.escape(root), "__pypackages__", "*", "lib")))
    result = []
    for f in found:
        if os.path.isdir(f) and f not in result:
            result.append(f)
    return result


def top_level_names(distinfo):
    text = read_text(os.path.join(distinfo, "top_level.txt"))
    names = []
    if text:
        names = [t.strip() for t in text.splitlines() if t.strip()]
    else:
        rec = read_text(os.path.join(distinfo, "RECORD")) or ""
        for line in rec.splitlines():
            first = line.split(",")[0].replace("\\", "/")
            top = first.split("/")[0]
            if top and not top.startswith("..") and not top.endswith(".dist-info") and top not in ("__pycache__",):
                top = top[:-3] if top.endswith(".py") and "/" not in first else top
                if top not in names:
                    names.append(top)
    return names[:10]


def scan_site_packages(rep, root, pkg_norm):
    for sp in site_packages_dirs(root):
        try:
            entries = sorted(os.listdir(sp))
        except OSError:
            continue
        for d in entries:
            if not d.endswith(".dist-info"):
                continue
            name, _, ver = d[:-len(".dist-info")].rpartition("-")
            if not name or norm_py(name) != pkg_norm:
                continue
            distinfo = os.path.join(sp, d)
            meta = os.path.join(distinfo, "METADATA")
            text = read_text(meta, rep.warnings)
            version, vline, extra = ver, None, {}
            if text is not None:
                for i, line in enumerate(text.splitlines(), 1):
                    if not line.strip():
                        break  # header block ends at the first blank line
                    if line.startswith("Version:"):
                        version, vline = line.split(":", 1)[1].strip(), i
                    elif line.startswith("Requires-Python:"):
                        extra["requires_python"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Project-URL:"):
                        extra.setdefault("project_urls", []).append(line.split(":", 1)[1].strip()[:200])
                    elif line.startswith("Home-page:"):
                        extra["home_page"] = line.split(":", 1)[1].strip()
                extra["project_urls"] = extra.get("project_urls", [])[:8]
            rep.add_installed("python", distinfo, version, meta, vline, extra)
            rep.add_doc("python", "metadata", meta, "includes the long description if the author supplied one")
            for top in top_level_names(distinfo):
                pdir = os.path.join(sp, top)
                if os.path.isdir(pdir):
                    rep.add_doc("python", "entry", os.path.join(pdir, "__init__.py"), "package __init__: public names and docstring")
                    rep.add_doc("python", "types_marker", os.path.join(pdir, "py.typed"), "package ships inline type hints")
                    count = 0
                    for base, dirs, files in os.walk(pdir):
                        dirs[:] = sorted(x for x in dirs if x != "__pycache__")
                        if base[len(pdir):].count(os.sep) >= 2:
                            dirs[:] = []
                        for f in sorted(files):
                            if f.endswith(".pyi") and count < MAX_LIST:
                                rep.add_doc("python", "types", os.path.join(base, f), "stub file")
                                count += 1
                elif os.path.isfile(pdir + ".py"):
                    rep.add_doc("python", "entry", pdir + ".py", "single-module distribution")
                sdir = os.path.join(sp, top + "-stubs")
                if os.path.isdir(sdir):
                    init = os.path.join(sdir, "__init__.pyi")
                    rep.add_doc("python", "types", init, "separate stubs package")


# ----------------------------------------------------------------- orchestration

def resolve(rep):
    resolved, source, mismatch = None, None, False
    for kind in KIND_PRIORITY:
        vals = []
        for v in rep.versions:
            if v["kind"] == kind and v["version"] not in vals:
                vals.append(v["version"])
        if not vals:
            continue
        if kind == "installed" or len(vals) == 1:
            resolved, source = vals[0], kind
        else:
            rep.warnings.append("several different %s versions found (%s); no single version is resolved" % (kind, ", ".join(vals[:5])))
        if kind == "installed" and len(vals) > 1:
            rep.warnings.append("several installed copies with different versions; the first is the one nearest the project")
        break
    comparable = set()
    for v in rep.versions:
        if v["kind"] in ("installed", "locked", "pinned") and v["ecosystem"] != "go":
            comparable.add(v["version"])
    if len(comparable) > 1:
        mismatch = True
        rep.warnings.append("installed, locked or pinned versions disagree (%s): code runs against the installed copy; tell the user" % ", ".join(sorted(comparable)[:6]))
    return resolved, source, mismatch


def run(root, pkg, eco):
    rep = Report(root, pkg)
    pkg_norm = norm_py(pkg)
    bases = ancestor_dirs(root)  # workspaces keep their lockfile at the repository root
    if eco in ("all", "npm"):
        scan_package_json(rep, root, pkg)
        for base in bases:
            scan_package_lock(rep, base, pkg)
            scan_pnpm_lock(rep, base, pkg)
            scan_yarn_lock(rep, base, pkg)
        scan_node_modules(rep, root, pkg)
    if eco in ("all", "python"):
        scan_requirements(rep, root, pkg_norm)
        for base in bases:
            scan_toml_lock(rep, os.path.join(base, "poetry.lock"), pkg_norm)
            scan_toml_lock(rep, os.path.join(base, "uv.lock"), pkg_norm)
        scan_site_packages(rep, root, pkg_norm)
    if eco in ("all", "go"):
        scan_go(rep, root, pkg)
    if eco in ("all", "npm") and not any(i["ecosystem"] == "npm" for i in rep.installed):
        if os.path.exists(os.path.join(root, ".pnp.cjs")) or os.path.exists(os.path.join(root, ".pnp.js")):
            rep.warnings.append("Yarn Plug'n'Play project: packages are zip archives under .yarn/cache, not in node_modules; this script cannot read them")
    resolved, source, mismatch = resolve(rep)
    found = bool(rep.versions or rep.installed)
    if found and not rep.installed:
        rep.warnings.append("no installed copy found: do not answer API questions from memory; ask the user to install dependencies or read the changelog for the locked version")
    if not found:
        rep.warnings.append("package not found in any supported lockfile or installed location")
    ecos = sorted({v["ecosystem"] for v in rep.versions} | {i["ecosystem"] for i in rep.installed})
    report = {
        "tool": "find_local_docs",
        "schema_version": SCHEMA_VERSION,
        "project": root.replace("\\", "/"),
        "package": pkg,
        "ecosystems_with_hits": ecos,
        "found": found,
        "resolved_version": resolved,
        "resolved_from": source,
        "version_mismatch": mismatch,
        "versions": rep.versions,
        "installed": rep.installed,
        "docs": rep.docs,
        "warnings": rep.warnings,
    }
    return report, (0 if found else 1)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("usage error: %s\n" % message)
        out_json({"tool": "find_local_docs", "schema_version": SCHEMA_VERSION, "error": message})
        raise SystemExit(2)


def main(argv=None):
    parser = JsonArgumentParser(description="Find the installed version of a package and its local docs, types and source.")
    parser.add_argument("project_dir")
    parser.add_argument("package")
    parser.add_argument("--ecosystem", choices=("all",) + ECOSYSTEMS, default="all")
    args = parser.parse_args(argv)
    root = os.path.abspath(args.project_dir)
    if not os.path.isdir(root):
        msg = "project directory not found: %s" % args.project_dir
        sys.stderr.write(msg + "\n")
        out_json({"tool": "find_local_docs", "schema_version": SCHEMA_VERSION, "error": msg})
        return 2
    if not args.package.strip():
        sys.stderr.write("package name is empty\n")
        out_json({"tool": "find_local_docs", "schema_version": SCHEMA_VERSION, "error": "package name is empty"})
        return 2
    report, code = run(root, args.package.strip(), args.ecosystem)
    out_json(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
