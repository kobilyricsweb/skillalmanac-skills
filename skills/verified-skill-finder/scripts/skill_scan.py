#!/usr/bin/env python3
"""Inventory and rank agent skills found in local folders. Read-only.

Usage:
    python skill_scan.py [--query "text"] [--top N] [--all] [PATH ...]

Each PATH is either one skill folder (it contains SKILL.md) or a folder that
holds skills, for example .claude/skills, .agents/skills or any path the user
names. Folders are searched up to 3 levels deep; a folder that holds SKILL.md
is not searched further. With no PATH, the existing ones among ./.claude/skills,
./.agents/skills, ~/.claude/skills and ~/.agents/skills are used.

What is read: SKILL.md (first 200 KB) and the names, sizes and modification
times of the other files in each skill folder. Nothing is written, executed,
imported or sent anywhere; symbolic links are not followed.

Output: one strict-JSON object on stdout (no NaN, no comments). Schema version 1:
  query, query_terms, roots, scanned (skill count), shown, skills[], duplicates[],
  warnings[]. See SKILL.md for the field list.

Exit codes: 0 done (even when nothing matched), 2 usage error or no readable path.
"""
import argparse
import json
import os
import re
import sys
import time

SCHEMA_VERSION = 1
MAX_SKILL_MD = 200 * 1024        # bytes read from SKILL.md; larger files are cut and flagged
MAX_DEPTH = 3                    # folder levels below a root; covers root/<group>/<skill>
MAX_SKILLS = 500                 # stop collecting beyond this and warn
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
ALLOWED_TOP_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Weights: a term in the name is the strongest sign of fit, in the description a
# strong one, in the body a weak one (bodies are long and mention many words).
W_NAME, W_DESC, W_BODY = 3.0, 2.0, 0.5
BODY_CHARS = 20000               # how much of the body is searched for query terms
STOPWORDS = set(
    "a an and are as at be by can do does for from get how i in is it me my of on or "
    "our skill skills that the there this to use want with you your any need needs "
    "which what whats should would could please find finding choose".split()
)
PERMISSIVE = {"mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause", "isc", "cc0-1.0",
              "unlicense", "0bsd", "zlib", "cc-by-4.0", "python-2.0"}
RESTRICTIVE_HINTS = ("gpl", "agpl", "lgpl", "-nc", "proprietary", "commercial",
                     "all rights reserved", "sspl", "busl", "elastic")
LICENSE_FILES = ("license", "license.txt", "license.md", "licence", "licence.txt",
                 "licence.md", "copying", "copying.txt")


def stem(word):
    """Crude English stemmer, applied to both query and text so they match."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 5 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def terms_of(text):
    """Lower-case word stems of text, stop words removed, order kept, no repeats."""
    seen, out = set(), []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) < 2 or w in STOPWORDS:
            continue
        s = stem(w)
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Return (fields, metadata, body, problems). Handles the YAML subset skills use:
    plain or quoted scalars, folded or literal block scalars, one nested string map."""
    problems = []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    bom = chr(0xFEFF)  # a byte-order mark before the first --- is common in files saved on Windows
    if lines and lines[0].startswith(bom):
        lines[0] = lines[0].lstrip(bom)
    if not lines or lines[0].strip() != "---":
        return {}, {}, text, ["no frontmatter block at the top of SKILL.md"]
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, {}, text, ["frontmatter block is not closed with ---"]
    fields, meta = {}, {}
    key, mode = None, None  # mode: scalar, block, map
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t":
            if key is None:
                continue
            if mode == "map":
                m = re.match(r"\s+([A-Za-z0-9_.-]+)\s*:\s*(.*)$", raw)
                if m:
                    meta[m.group(1)] = unquote(m.group(2))
            else:
                fields[key] = (fields.get(key, "") + " " + raw.strip()).strip()
            continue
        m = re.match(r"([A-Za-z0-9_.-]+)\s*:\s*(.*)$", raw)
        if not m:
            problems.append("unparseable frontmatter line: " + raw[:60])
            key, mode = None, None
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            fields[key], mode = "", "block"
        elif val == "":
            fields[key], mode = "", "map"
        else:
            fields[key], mode = unquote(val), "scalar"
    body = "\n".join(lines[end + 1:])
    return fields, meta, body, problems


def classify_licence(spdx, has_file):
    """Return one of permissive, restrictive, unrecognised, file-only, missing."""
    low = (spdx or "").strip().lower()
    if low:
        if low in PERMISSIVE:
            return "permissive"
        if any(h in low for h in RESTRICTIVE_HINTS):
            return "restrictive"
        return "unrecognised"
    return "file-only" if has_file else "missing"


def newest_mtime(folder, warnings):
    """Count files, bytes and the newest modification time under folder; no symlinks."""
    n_files, total, newest, symlinks = 0, 0, 0.0, 0
    for dirpath, dirnames, filenames in os.walk(folder, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = os.path.join(dirpath, name)
            try:
                if os.path.islink(p):
                    symlinks += 1
                    continue
                st = os.stat(p)
            except OSError:
                continue
            n_files += 1
            total += st.st_size
            newest = max(newest, st.st_mtime)
    if symlinks:
        warnings.append("%s: %d symbolic link(s) skipped" % (folder, symlinks))
    return n_files, total, newest


def inspect_skill(folder, query_terms, warnings):
    skill_md = os.path.join(folder, "SKILL.md")
    try:
        with open(skill_md, "rb") as fh:
            raw = fh.read(MAX_SKILL_MD + 1)
    except OSError as exc:
        warnings.append("%s: cannot read SKILL.md (%s)" % (folder, exc.__class__.__name__))
        return None
    issues = []
    if len(raw) > MAX_SKILL_MD:
        raw = raw[:MAX_SKILL_MD]
        issues.append("SKILL.md is larger than 200 KB; only the start was read")
    text = raw.decode("utf-8", errors="replace")
    fields, meta, body, problems = parse_frontmatter(text)
    issues.extend(problems)
    folder_name = os.path.basename(os.path.normpath(folder))
    name = fields.get("name", "")
    desc = fields.get("description", "")
    if not name:
        issues.append("missing name")
    elif name != folder_name:
        issues.append("name '%s' differs from folder name '%s'" % (name, folder_name))
    if not desc:
        issues.append("missing description")
    extras = sorted(k for k in fields if k not in ALLOWED_TOP_KEYS)
    if extras:
        issues.append("top-level keys outside the open spec: " + ", ".join(extras))
    spdx = fields.get("license") or meta.get("license") or ""
    version = meta.get("version") or fields.get("version") or ""

    names = {e.lower(): e for e in os.listdir(folder)}
    has_license_file = any(n in names for n in LICENSE_FILES)
    evals_dir = os.path.join(folder, "evals")
    has_evals = os.path.isdir(evals_dir) and any(
        True for _r, _d, files in os.walk(evals_dir, followlinks=False) for _f in files)
    has_verification = "verification.md" in names
    has_changelog = any(n.startswith("changelog") for n in names)
    scripts_dir = os.path.join(folder, "scripts")
    script_count = 0
    if os.path.isdir(scripts_dir):
        script_count = sum(len(f) for _r, _d, f in os.walk(scripts_dir, followlinks=False))
    n_files, total, newest = newest_mtime(folder, warnings)
    modified = time.strftime("%Y-%m-%d", time.gmtime(newest)) if newest else None
    age = int((time.time() - newest) // 86400) if newest else None

    # Keyword match. Text after a "do not use" clause is the skill's own list of wrong jobs.
    m = re.search(r"\bdo not use\b|\bdon't use\b|\bdo not apply\b", desc, re.I)
    desc_pos, desc_neg = (desc[:m.start()], desc[m.start():]) if m else (desc, "")
    name_t = set(terms_of(name.replace("-", " ")))
    desc_t = set(terms_of(desc_pos))
    neg_t = set(terms_of(desc_neg))
    body_t = set(terms_of(body[:BODY_CHARS]))
    points, matched, excluded = 0.0, [], []
    for t in query_terms:
        pts = (W_NAME if t in name_t else 0) + (W_DESC if t in desc_t else 0) + (W_BODY if t in body_t else 0)
        if pts:
            matched.append(t)
            points += pts
        if t in neg_t and t not in name_t and t not in desc_t:
            excluded.append(t)
    top = W_NAME + W_DESC + W_BODY
    score = round(100.0 * points / (top * len(query_terms)), 1) if query_terms else 0.0
    return {
        "name": name or folder_name,
        "folder": folder_name,
        "path": os.path.abspath(folder).replace("\\", "/"),
        "description": desc,
        "license": spdx or None,
        "license_class": classify_licence(spdx, has_license_file),
        "license_file": has_license_file,
        "version": version or None,
        "has_evals": has_evals,
        "has_verification": has_verification,
        "has_changelog": has_changelog,
        "script_count": script_count,
        "file_count": n_files,
        "bytes": total,
        "last_modified": modified,
        "days_since_modified": age,
        "score": score,
        "matched_terms": matched,
        "excluded_by_description": excluded,
        "issues": issues,
    }


def find_skill_folders(root, warnings):
    """Yield folders at or below root that contain SKILL.md (depth-limited, no symlinks)."""
    root = os.path.abspath(root)
    if os.path.isfile(os.path.join(root, "SKILL.md")):
        yield root
        return
    stack = [(root, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth > MAX_DEPTH:
            continue
        try:
            entries = sorted(os.listdir(cur))
        except OSError as exc:
            warnings.append("%s: cannot list folder (%s)" % (cur, exc.__class__.__name__))
            continue
        for e in entries:
            p = os.path.join(cur, e)
            if e in SKIP_DIRS or os.path.islink(p) or not os.path.isdir(p):
                continue
            if os.path.isfile(os.path.join(p, "SKILL.md")):
                yield p
            else:
                stack.append((p, depth + 1))


def default_roots():
    home = os.path.expanduser("~")
    cands = [os.path.join(os.getcwd(), ".claude", "skills"), os.path.join(os.getcwd(), ".agents", "skills"),
             os.path.join(home, ".claude", "skills"), os.path.join(home, ".agents", "skills")]
    return [c for c in cands if os.path.isdir(c)]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Inventory and rank local agent skills (read-only).")
    ap.add_argument("paths", nargs="*", help="skill folder or folder of skills")
    ap.add_argument("--query", default="", help="what the skill should do, in plain words")
    ap.add_argument("--top", type=int, default=10, help="show at most N skills (default 10; 0 = all)")
    ap.add_argument("--all", action="store_true", help="also show skills with score 0 when a query is given")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if args.top < 0:
        print("--top must be 0 or more", file=sys.stderr)
        return 2
    warnings = []
    roots = args.paths or default_roots()
    good_roots = []
    for r in roots:
        if os.path.isdir(r):
            good_roots.append(r)
        else:
            warnings.append("%s: not a folder, skipped" % r)
    if not good_roots:
        print("No readable skill folder. Pass a path such as .claude/skills or a skill folder.", file=sys.stderr)
        return 2
    qterms = terms_of(args.query)
    if args.query and not qterms:
        warnings.append("query has no usable words after removing stop words; scores are 0")
    found, seen_dirs = [], set()
    for r in good_roots:
        for f in find_skill_folders(r, warnings):
            key = os.path.normcase(os.path.realpath(f))
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            if len(found) >= MAX_SKILLS:
                warnings.append("more than %d skills found; the rest were not read" % MAX_SKILLS)
                break
            info = inspect_skill(f, qterms, warnings)
            if info:
                found.append(info)
    by_name = {}
    for s in found:
        by_name.setdefault(s["name"], []).append(s["path"])
    duplicates = [{"name": n, "paths": sorted(p)} for n, p in sorted(by_name.items()) if len(p) > 1]
    shown = found
    if qterms and not args.all:
        shown = [s for s in found if s["score"] > 0]
    shown = sorted(shown, key=lambda s: (-s["score"], s["name"], s["path"]))
    if args.top:
        shown = shown[:args.top]
    for i, s in enumerate(shown, 1):
        s["rank"] = i
    report = {
        "schema_version": SCHEMA_VERSION,
        "query": args.query,
        "query_terms": qterms,
        "roots": [os.path.abspath(r).replace("\\", "/") for r in good_roots],
        "scanned": len(found),
        "shown": len(shown),
        "skills": shown,
        "duplicates": duplicates,
        "warnings": sorted(set(warnings)),
    }
    out = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False)
    sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
