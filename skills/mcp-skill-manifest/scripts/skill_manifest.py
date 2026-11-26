#!/usr/bin/env python3
"""Build and check the `skills/list` manifest of the MCP Skills extension (beta)
for a folder of Agent Skills.

    python skill_manifest.py build <skills_root> --authority=<name> [--out=FILE]
                             [--ttl-ms=N] [--cache-scope=public|private]
                             [--exclude=GLOB ...] [--nested]
    python skill_manifest.py check <manifest.json> [--root=<skills_root>]
                             [--authority=<name>] [--exclude=GLOB ...] [--nested]

build  takes <skills_root> itself if it holds a SKILL.md, else each direct child
       folder that does (every folder below it with --nested), and writes a
       ListSkillsResult: one entry per skill with `uri`, `frontmatter` and a
       complete `resources` array (`uri`, `digest`, `size` for every file,
       SKILL.md included). Digests are sha256 over the raw bytes on disk.
       --out must point outside <skills_root>, or the manifest would become a
       file of the skill it describes.
check  validates a manifest against the rules in references/spec_rules.md. With
       --root it also re-reads the files and compares size, digest, the file
       set and the frontmatter, so a manifest that went stale is caught.

It does not run a server and makes no network calls. A digest match proves the
bytes are the ones the manifest lists. It does not prove the skill is safe.

Frontmatter is parsed with PyYAML when it is installed. Without it, only the
plainest frontmatter is read: `key: value` lines whose values are quoted
strings or plain words, and one level of such pairs under a key. Anything that
YAML could read differently (numbers, yes/no, lists, block text, comments)
stops the run with a request to install PyYAML.

Exit codes: 0 = no errors, 1 = errors found, 2 = usage error or unreadable input.
Python 3.9+, standard library only (PyYAML optional).
"""
import fnmatch
import hashlib
import json
import math
import os
import re
import stat
import sys
from urllib.parse import quote, unquote

MAX_RESOURCES = 512
MAX_BYTES = 16 * 1024 * 1024
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*://[^/?#]+/")
JUNK = (".DS_Store", "Thumbs.db", "__pycache__", ".git", ".pytest_cache")
NEED_YAML = "this frontmatter needs a full YAML parser; install PyYAML and run again"


class Problem(Exception):
    pass


def usage(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------- frontmatter ----------

def split_frontmatter(raw):
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Problem("SKILL.md is not UTF-8 text")
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        raise Problem("SKILL.md does not start with a --- frontmatter block")
    for i in range(1, len(lines)):
        if lines[i].rstrip() == "---":
            return "\n".join(lines[1:i])
    raise Problem("frontmatter block is not closed with ---")


PLAIN = re.compile(r"^[A-Za-z][A-Za-z0-9 _.,;()/+-]*$")
YAML_WORDS = {"true", "false", "yes", "no", "on", "off", "null", "y", "n", "nan", "inf"}


def strict_scalar(s):
    """A value that every YAML 1.1 parser reads as the same string, or a Problem."""
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] == '"' and "\\" not in s[1:-1] and '"' not in s[1:-1]:
        return s[1:-1]
    if len(s) >= 2 and s[0] == s[-1] == "'" and "'" not in s[1:-1]:
        return s[1:-1]
    if PLAIN.match(s) and s.lower() not in YAML_WORDS and ": " not in s and " #" not in s and not s.endswith(":"):
        return s
    raise Problem(NEED_YAML)


def mini_yaml(text):
    out, parent = {}, None
    for line in text.split("\n"):
        if not line.strip():
            continue
        if "\t" in line or line.lstrip().startswith(("#", "-")) or ":" not in line:
            raise Problem(NEED_YAML)
        pad = len(line) - len(line.lstrip(" "))
        key, _, rest = line.strip().partition(":")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key) or (rest and not rest.startswith(" ")):
            raise Problem(NEED_YAML)
        if pad == 0:
            if key in out:
                raise Problem(f"frontmatter key {key} appears twice")
            if rest.strip():
                out[key], parent = strict_scalar(rest), None
            else:
                out[key], parent = {}, key
        elif parent is not None and pad == 2 and rest.strip():
            if key in out[parent]:
                raise Problem(f"frontmatter key {parent}.{key} appears twice")
            out[parent][key] = strict_scalar(rest)
        else:
            raise Problem(NEED_YAML)
    if any(v == {} for v in out.values()):
        raise Problem(NEED_YAML)
    return out


def jsonable(value, where="frontmatter"):
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise Problem(f"{where} holds a number JSON cannot carry (NaN or infinity)")
        return
    if isinstance(value, list):
        for i, v in enumerate(value):
            jsonable(v, f"{where}[{i}]")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise Problem(f"{where} has a key that is not a string: {k!r}; quote it in SKILL.md")
            jsonable(v, f"{where}.{k}")
        return
    raise Problem(f"{where} holds a value JSON cannot carry ({type(value).__name__}); write it as a quoted string")


def parse_frontmatter(raw):
    text = split_frontmatter(raw)
    try:
        import yaml  # type: ignore
    except ImportError:
        data = mini_yaml(text)
    else:
        class Loader(yaml.SafeLoader):
            def construct_mapping(self, node, deep=False):
                self.flatten_mapping(node)
                seen = set()
                for key_node, _ in node.value:
                    key = self.construct_object(key_node, deep=deep)
                    if isinstance(key, str):
                        if key in seen:
                            raise yaml.constructor.ConstructorError(
                                "while reading frontmatter", node.start_mark,
                                f"frontmatter key {key!r} appears twice", key_node.start_mark)
                        seen.add(key)
                return super().construct_mapping(node, deep=deep)
        # Keep dates as the text the author wrote; JSON has no date type.
        Loader.yaml_implicit_resolvers = {
            k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
            for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
        try:
            data = yaml.load(text, Loader=Loader)
        except yaml.YAMLError as exc:
            raise Problem("frontmatter is not valid YAML: " + " ".join(str(exc).split())[:200])
    if not isinstance(data, dict):
        raise Problem("frontmatter is not a mapping")
    jsonable(data)
    return data


def same_json(a, b):
    """Equal as JSON, with types: 1, 1.0 and true are three different values."""
    try:
        return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError):
        return False


# ---------- walking and hashing ----------

def is_link(path):
    """Symlink, or on Windows any reparse point (junctions included)."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def excluded(rel, patterns):
    parts = rel.split("/")
    return any(fnmatch.fnmatchcase(rel, p) or any(fnmatch.fnmatchcase(part, p) for part in parts) for p in patterns)


def has_skill_md(folder):
    try:
        return "SKILL.md" in os.listdir(folder)
    except OSError:
        return False


def skill_files(skill_dir, patterns, errors, warnings, label):
    files = []

    def on_error(exc):
        errors.append(f"{label}: cannot read folder {getattr(exc, 'filename', '')}: {exc.strerror or exc}")

    for dirpath, dirnames, filenames in os.walk(skill_dir, followlinks=False, onerror=on_error):
        dirnames.sort()
        for d in list(dirnames):
            rel_d = os.path.relpath(os.path.join(dirpath, d), skill_dir).replace(os.sep, "/")
            if is_link(os.path.join(dirpath, d)):
                warnings.append(f"{label}: linked folder skipped: {rel_d}")
                dirnames.remove(d)
            elif excluded(rel_d, patterns):
                dirnames.remove(d)
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, skill_dir).replace(os.sep, "/")
            if is_link(full):
                warnings.append(f"{label}: link skipped: {rel}")
                continue
            if excluded(rel, patterns):
                continue
            if any(part in JUNK or part.endswith(".pyc") for part in rel.split("/")):
                warnings.append(f"{label}: {rel} looks like a build or system file; it is listed. Use --exclude to leave it out, and do not serve it")
            files.append((rel, full))
    return files


def uri_for(authority, name, rel):
    return f"skill://{authority}/{quote(name, safe='')}/" + "/".join(quote(seg, safe="") for seg in rel.split("/"))


def find_skills(root, nested, patterns):
    """The root itself if it holds a SKILL.md, else its direct child folders that do.
    With nested=True every folder below the root that holds a SKILL.md is a skill."""
    if nested:
        found = []
        for dirpath, dirnames, _ in os.walk(root, followlinks=False):
            keep = []
            for d in sorted(dirnames):
                rel = os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/")
                if d not in JUNK and not is_link(os.path.join(dirpath, d)) and not excluded(rel, patterns):
                    keep.append(d)
            dirnames[:] = keep
            if has_skill_md(dirpath):
                found.append(dirpath)
        return found
    if has_skill_md(root):
        return [root]
    return [os.path.join(root, d) for d in sorted(os.listdir(root))
            if os.path.isdir(os.path.join(root, d)) and not is_link(os.path.join(root, d)) and has_skill_md(os.path.join(root, d))]


def build_entry(skill_dir, authority, patterns, errors, warnings):
    label = os.path.basename(os.path.abspath(skill_dir))
    try:
        with open(os.path.join(skill_dir, "SKILL.md"), "rb") as fh:
            fm = parse_frontmatter(fh.read())
    except Problem as exc:
        errors.append(f"{label}: {exc}")
        return None
    except OSError as exc:
        errors.append(f"{label}: cannot read SKILL.md: {exc.strerror or exc}")
        return None
    name = fm.get("name")
    if not isinstance(name, str) or not isinstance(fm.get("description"), str):
        errors.append(f"{label}: frontmatter needs string fields name and description")
        return None
    if name != label:
        warnings.append(f"{label}: folder name differs from frontmatter name {name!r}; the URI uses the frontmatter name")
    resources = []
    for rel, full in skill_files(skill_dir, patterns, errors, warnings, label):
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError as exc:
            errors.append(f"{label}: cannot read {rel}: {exc.strerror or exc}")
            continue
        resources.append({"uri": uri_for(authority, name, rel),
                          "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "size": len(raw)})
    entry = {"uri": uri_for(authority, name, "SKILL.md"), "frontmatter": fm, "resources": resources}
    errors.extend(entry_problems(entry, label))
    return entry


# ---------- rules on a manifest entry ----------

def path_problem(uri, root):
    """None when uri is a plain file path strictly inside root, else the reason."""
    if not isinstance(uri, str):
        return "is not a string"
    if "?" in uri or "#" in uri:
        return "has a query or fragment"
    if not uri.startswith(root + "/"):
        return "is outside the skill's directory"
    for seg in uri[len(root) + 1:].split("/"):
        plain = unquote(seg)
        if seg == "" or plain in (".", ".."):
            return "has an empty, . or .. path segment"
        if "/" in plain or "\\" in plain:
            return "has an encoded slash in a path segment"
    return None


def entry_problems(entry, label=None):
    out = []
    if not isinstance(entry, dict):
        return ["a skills entry is not an object"]
    uri = entry.get("uri")
    label = label or str(uri)
    if not isinstance(uri, str) or not uri.endswith("/SKILL.md"):
        return [f"{label}: uri must be the URI of the skill's SKILL.md"]
    if not SCHEME.match(uri):
        return [f"{label}: uri must have a scheme and an authority, as in skill://<authority>/<name>/SKILL.md"]
    root = uri[: -len("/SKILL.md")]
    last = unquote(root.rsplit("/", 1)[-1])
    fm = entry.get("frontmatter")
    if not isinstance(fm, dict) or not isinstance(fm.get("name"), str) or not isinstance(fm.get("description"), str):
        out.append(f"{label}: frontmatter must be an object with string name and description")
    else:
        if not 1 <= len(fm["description"]) <= 1024 or not fm["description"].strip():
            out.append(f"{label}: description must be non-empty and at most 1024 characters")
        if last != fm["name"]:
            out.append(f"{label}: the last segment of the skill path must equal frontmatter.name ({fm['name']!r})")
        if not NAME.match(fm["name"]) or len(fm["name"]) > 64:
            out.append(f"{label}: name {fm['name']!r} breaks the Agent Skills naming rules (lowercase letters, digits and single hyphens, at most 64 characters)")
    res = entry.get("resources")
    if res == "dynamic":
        return out
    if not isinstance(res, list):
        out.append(f"{label}: resources must be an array or the string \"dynamic\"; an entry without it is invalid")
        return out
    seen, total = set(), 0
    for r in res:
        if not isinstance(r, dict) or not all(k in r for k in ("uri", "digest", "size")):
            out.append(f"{label}: every resource needs uri, digest and size")
            continue
        ru = r["uri"]
        why = path_problem(ru, root)
        if why:
            out.append(f"{label}: resource {ru!r} {why}")
            continue
        if ru in seen:
            out.append(f"{label}: {ru} is listed twice")
        seen.add(ru)
        if not isinstance(r["digest"], str) or not DIGEST.match(r["digest"]):
            out.append(f"{label}: digest of {ru} must be sha256: followed by 64 lowercase hex characters")
        if not isinstance(r["size"], int) or isinstance(r["size"], bool) or r["size"] < 0:
            out.append(f"{label}: size of {ru} must be a whole number of bytes")
        else:
            total += r["size"]
    if uri not in seen:
        out.append(f"{label}: resources must include an entry for the SKILL.md itself")
    if len(res) > MAX_RESOURCES:
        out.append(f"{label}: {len(res)} resources; the limit is {MAX_RESOURCES}")
    if total > MAX_BYTES:
        out.append(f"{label}: {total} bytes in total; the limit is {MAX_BYTES} (16 MiB)")
    return out


def result_problems(doc):
    out = []
    if not isinstance(doc, dict) or not isinstance(doc.get("skills"), list):
        return ["the manifest must be an object with a skills array"]
    if doc.get("resultType") != "complete":
        out.append("resultType must be \"complete\"")
    ttl = doc.get("ttlMs")
    if not isinstance(ttl, int) or isinstance(ttl, bool) or ttl < 0:
        out.append("ttlMs must be a whole number, 0 or more")
    if doc.get("cacheScope") not in ("private", "public"):
        out.append("cacheScope must be \"private\" or \"public\"")
    uris = [e.get("uri") for e in doc["skills"] if isinstance(e, dict) and isinstance(e.get("uri"), str)]
    for u in sorted({u for u in uris if uris.count(u) > 1}):
        out.append(f"{u} appears in two entries")
    return out


# ---------- commands ----------

FLAGS = {"nested"}


def parse_args(argv, allowed):
    opts, pos = {"exclude": []}, []
    for a in argv:
        if a.startswith("--"):
            k, eq, v = a[2:].partition("=")
            if k not in allowed:
                usage(f"unknown option --{k}")
            if k in FLAGS:
                if eq:
                    usage(f"--{k} takes no value")
                opts[k] = True
            elif not eq or not v:
                usage(f"--{k} needs a value, as in --{k}=VALUE")
            elif k == "exclude":
                opts["exclude"].append(v)
            else:
                opts[k] = v
        else:
            pos.append(a)
    return opts, pos


def build_doc(root, authority, patterns, ttl, scope, nested=False):
    errors, warnings, skills = [], [], []
    dirs = find_skills(root, nested, patterns)
    if not dirs:
        errors.append(f"no SKILL.md found under {root}")
    for d in dirs:
        entry = build_entry(d, authority, patterns, errors, warnings)
        if entry:
            skills.append(entry)
    names = [e["frontmatter"]["name"] for e in skills]
    for n in sorted({n for n in names if names.count(n) > 1}):
        errors.append(f"two skills are named {n!r}; their URIs would collide")
    doc = {"resultType": "complete", "skills": skills, "ttlMs": ttl, "cacheScope": scope}
    return doc, errors, warnings


def emit(report):
    print(json.dumps(report, indent=1, ensure_ascii=False, allow_nan=False))
    sys.exit(0 if report["ok"] else 1)


def check_authority(value):
    if not value or not re.fullmatch(r"[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?", value):
        usage("--authority must be a host-like name (letters, digits, dots, hyphens)")


def cmd_build(argv):
    opts, pos = parse_args(argv, {"authority", "out", "ttl-ms", "cache-scope", "exclude", "nested"})
    if len(pos) != 1:
        usage("usage: skill_manifest.py build <skills_root> --authority=<name> [--out=FILE]")
    root = pos[0]
    check_authority(opts.get("authority"))
    if not os.path.isdir(root):
        usage(f"not a folder: {root}")
    out_path = opts.get("out")
    if out_path:
        root_real = os.path.normcase(os.path.realpath(root))
        out_real = os.path.normcase(os.path.realpath(out_path))
        inside = os.path.commonpath([root_real, out_real]) == root_real \
            if os.path.splitdrive(root_real)[0] == os.path.splitdrive(out_real)[0] else False
        if inside:
            usage("--out is inside the skills root; write the manifest outside it, or it becomes a file of the skill")
    try:
        ttl = int(opts.get("ttl-ms", "300000"))
    except ValueError:
        usage("--ttl-ms needs a whole number")
    doc, errors, warnings = build_doc(root, opts["authority"], opts["exclude"], ttl,
                                      opts.get("cache-scope", "public"), opts.get("nested", False))
    errors += result_problems(doc)
    if out_path and not errors:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, ensure_ascii=False, allow_nan=False)
            fh.write("\n")
    report = {"skills": len(doc["skills"]),
              "resources": sum(len(e["resources"]) for e in doc["skills"]),
              "bytes": sum(r["size"] for e in doc["skills"] for r in e["resources"]),
              "written": out_path if not errors else None,
              "errors": errors, "warnings": warnings, "ok": not errors}
    if not out_path and not errors:
        report["manifest"] = doc
    emit(report)


def cmd_check(argv):
    opts, pos = parse_args(argv, {"root", "authority", "exclude", "nested"})
    if len(pos) != 1:
        usage("usage: skill_manifest.py check <manifest.json> [--root=<skills_root> --authority=<name>]")
    try:
        with open(pos[0], encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        usage(f"cannot read {pos[0]}: {exc}")
    errors = result_problems(doc)
    warnings = []
    raw_entries = doc.get("skills", []) if isinstance(doc, dict) and isinstance(doc.get("skills"), list) else []
    entries = []
    for e in raw_entries:
        probs = entry_problems(e)
        errors += probs
        if isinstance(e, dict) and isinstance(e.get("uri"), str):
            entries.append(e)
            if e.get("resources") == "dynamic":
                warnings.append(f"{e['uri']}: resources is \"dynamic\"; there is no content integrity and hosts may decline to load it")
    if opts.get("root"):
        check_authority(opts.get("authority"))
        if not os.path.isdir(opts["root"]):
            usage(f"not a folder: {opts['root']}")
        fresh, berr, bwarn = build_doc(opts["root"], opts["authority"], opts["exclude"], 0, "public", opts.get("nested", False))
        errors += [f"folder: {x}" for x in berr]
        warnings += [f"folder: {x}" for x in bwarn]
        want = {e["uri"]: e for e in fresh["skills"]}
        have = {e["uri"]: e for e in entries}
        for uri in sorted(set(want) - set(have)):
            errors.append(f"{uri}: skill is in the folder but not in the manifest")
        for uri in sorted(set(have) - set(want)):
            errors.append(f"{uri}: skill is in the manifest but not in the folder")
        for uri in sorted(set(want) & set(have)):
            a, b = want[uri], have[uri]
            fm_b = b.get("frontmatter") if isinstance(b.get("frontmatter"), dict) else {}
            if not same_json(a["frontmatter"], fm_b):
                diff = sorted(k for k in set(a["frontmatter"]) | set(fm_b)
                              if k not in a["frontmatter"] or k not in fm_b or not same_json(a["frontmatter"][k], fm_b[k]))
                errors.append(f"{uri}: frontmatter differs from SKILL.md in field(s): {', '.join(diff)}")
            if not isinstance(b.get("resources"), list):
                continue
            fa = {r["uri"]: r for r in a["resources"]}
            fb = {r["uri"]: r for r in b["resources"] if isinstance(r, dict) and isinstance(r.get("uri"), str)}
            for u in sorted(set(fa) - set(fb)):
                errors.append(f"{u}: file exists but is not listed; a host treats reading it as a verification failure")
            for u in sorted(set(fb) - set(fa)):
                errors.append(f"{u}: listed but the file does not exist")
            for u in sorted(set(fa) & set(fb)):
                if fa[u]["size"] != fb[u].get("size"):
                    errors.append(f"{u}: size is {fa[u]['size']} bytes on disk, manifest says {fb[u].get('size')}")
                elif fa[u]["digest"] != fb[u].get("digest"):
                    errors.append(f"{u}: digest does not match the bytes on disk")
    emit({"skills": len(raw_entries), "errors": errors, "warnings": warnings, "ok": not errors})


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if not argv or argv[0] not in ("build", "check"):
        usage("usage: skill_manifest.py build|check ... (see the top of this file)")
    (cmd_build if argv[0] == "build" else cmd_check)(argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
