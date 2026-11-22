#!/usr/bin/env python3
"""Check the form of a skill folder that follows the open SKILL.md layout.

    python skill_check.py <skill-folder> [--json]

Reads SKILL.md and the files beside it; prints findings; writes nothing.
Exit codes: 0 = no ERROR, 1 = at least one ERROR, 2 = usage error.

It checks form only: frontmatter, name, description wording and length, body
size, links, orphan files, reference depth and a few wording habits that make
skills fail. It cannot tell whether the skill makes the agent do better work;
that needs the trigger and task evals described in SKILL.md.
Python 3.9+, standard library only, no network.
"""
import ast
import json
import os
import re
import sys

# Open-spec frontmatter keys. Other keys are rejected by some upload surfaces.
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# The spec caps the description at 1024 characters.
MAX_DESCRIPTION = 1024
# Below this there is no room for both the job and the trigger situations.
MIN_DESCRIPTION = 150
# Long descriptions crowd other skills out of the shared listing budget.
WARN_DESCRIPTION = 700
# Some tools shorten descriptions when many skills are installed, so trigger words go early.
FRONT_LOAD_LIMIT = 300
# Spec recommendation for the body.
MAX_BODY_LINES = 500
WARN_BODY_LINES = 200
# A reference longer than this needs a contents list so the agent can jump.
TOC_LINES = 100

USE_WHEN = re.compile(r"\buse (this skill )?(when|whenever|for|before|after)\b", re.I)
BOUNDARY = re.compile(r"\b(do not use|not for|does not|skip)\b", re.I)
FIRST_SECOND = re.compile(r"^(i |i'm |i can |you can |use this to |this skill helps you )", re.I)
VAGUE = re.compile(r"\b(helps? with|assists? with|handles? various|general purpose|and more|etc\.?)", re.I)
TAG = re.compile(r"<[a-zA-Z/][^>]*>")
TIME_SENSITIVE = re.compile(r"\b(as of 20\d\d|currently|at the moment|latest version|the new (api|feature)|recently|these days)\b", re.I)
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)]*)?\)")
BACKSLASH_PATH = re.compile(r"\b(?:scripts|references|assets)\\[\w.-]+")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def parse_frontmatter(text):
    """Return (data, body, errors) for the small YAML subset skills should use."""
    if not text.startswith("---\n"):
        return {}, text, ["SKILL.md must start with a line containing only '---'"]
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text, ["frontmatter is not closed with '---'"]
    raw, body = text[4:end], text[end + 4:].lstrip("\n")
    data, errors, current, block = {}, [], None, None
    for n, line in enumerate(raw.split("\n"), 2):
        if block is not None and (line.startswith(" ") or not line.strip()):
            # continuation of a block scalar: keep the text so the content
            # checks on the description still run (one pass shows every problem)
            data[block] = (data[block] + " " + line.strip()).strip()
            continue
        block = None
        if not line.strip():
            continue
        if line.startswith("  ") and current is not None:
            m = re.match(r"^\s+([\w.-]+):\s*(.*)$", line)
            if m:
                data[current][m.group(1)] = m.group(2).strip().strip("\"'")
            else:
                errors.append("line %d: cannot parse nested entry" % n)
            continue
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if not m:
            errors.append("line %d: cannot parse '%s'" % (n, line[:40]))
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", ">", "|-", ">-"):
            errors.append("line %d: block scalar for '%s'; many parsers fail on it, use one line" % (n, key))
            data[key], current, block = "", None, key
        elif val == "":
            data[key], current = {}, key
        else:
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key], current = val, None
    return data, body, errors


def check(root):
    """Return a list of (level, code, message) for the skill folder."""
    out = []

    def add(level, code, msg):
        out.append((level, code, msg))

    root = os.path.abspath(root)
    path = os.path.join(root, "SKILL.md")
    if not os.path.isfile(path):
        return [("ERROR", "skill-md", "SKILL.md not found; the file name is exact and upper case")]
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read().replace("\r\n", "\n")
    except UnicodeDecodeError:
        return [("ERROR", "encoding", "SKILL.md is not valid UTF-8; re-save it as UTF-8")]
    fm, body, errors = parse_frontmatter(text)
    for e in errors:
        add("ERROR", "frontmatter", e)

    extra = sorted(set(fm) - SPEC_KEYS)
    if extra:
        add("WARN", "frontmatter-keys", "keys outside the open spec: %s; some surfaces reject unknown keys" % extra)

    name = fm.get("name", "")
    if not isinstance(name, str) or not name:
        add("ERROR", "name", "name is missing")
    else:
        if len(name) > 64 or not NAME_RE.match(name):
            add("ERROR", "name", "name '%s' must be 1-64 characters of a-z, 0-9 and single hyphens" % name)
        if name != os.path.basename(root):
            add("ERROR", "name-folder", "name '%s' must equal the folder name '%s'" % (name, os.path.basename(root)))
        if "anthropic" in name or "claude" in name:
            add("ERROR", "name-reserved", "name contains a word that upload surfaces reserve")

    desc = fm.get("description", "")
    if not isinstance(desc, str) or not desc.strip():
        add("ERROR", "description", "description is missing; it is the only text the agent sees before loading the skill")
    else:
        n = len(desc)
        if n > MAX_DESCRIPTION:
            add("ERROR", "description-length", "description is %d characters; the spec limit is %d" % (n, MAX_DESCRIPTION))
        elif n < MIN_DESCRIPTION:
            add("WARN", "description-length", "description is %d characters; under %d rarely holds both the job and its triggers" % (n, MIN_DESCRIPTION))
        elif n > WARN_DESCRIPTION:
            add("WARN", "description-length", "description is %d characters; over %d it crowds the shared listing" % (n, WARN_DESCRIPTION))
        m = USE_WHEN.search(desc)
        if not m:
            add("ERROR", "description-when", "description has no 'Use when ...' clause; the agent cannot tell when to load the skill")
        elif m.start() > FRONT_LOAD_LIMIT:
            add("WARN", "description-frontload", "'Use when' starts at character %d; put trigger words in the first %d" % (m.start(), FRONT_LOAD_LIMIT))
        if not BOUNDARY.search(desc):
            add("WARN", "description-boundary", "description names no near-miss it is not for ('Do not use for ...')")
        if FIRST_SECOND.search(desc.strip()):
            add("ERROR", "description-person", "description must be third person ('Writes ...', not 'I can ...' or 'You can ...')")
        if TAG.search(desc):
            add("ERROR", "description-tag", "description contains an XML or HTML tag")
        v = VAGUE.search(desc)
        if v:
            add("WARN", "description-vague", "vague wording '%s'; name the concrete verbs, objects and user phrases" % v.group(0))

    meta = fm.get("metadata")
    if not fm.get("license"):
        add("WARN", "license", "no license field")
    if meta is not None and not isinstance(meta, dict):
        add("ERROR", "metadata", "metadata must be a map of string values")

    lines = body.count("\n") + 1
    if lines > MAX_BODY_LINES:
        add("ERROR", "body-size", "body has %d lines; the limit is %d, move detail into references/" % (lines, MAX_BODY_LINES))
    elif lines > WARN_BODY_LINES:
        add("WARN", "body-size", "body has %d lines; aim under %d" % (lines, WARN_BODY_LINES))
    if len(body) // 4 > 5000:
        add("WARN", "body-tokens", "body is about %d tokens by chars/4; recommended under 5000" % (len(body) // 4))
    if not re.search(r"(?im)^#{1,3}\s+limits\b", body):
        add("WARN", "limits", "no 'Limits' section stating what the skill does not cover")
    if not re.search(r"(?m)^\s*1\.\s", body):
        add("WARN", "workflow", "no numbered workflow; multi-step jobs need an order the agent can follow")
    t = TIME_SENSITIVE.search(body)
    if t:
        add("WARN", "time-sensitive", "time-sensitive wording '%s' goes stale; state the fact with its date or drop it" % t.group(0))
    if HTML_COMMENT.search(text):
        add("ERROR", "hidden-comment", "HTML comment found; hidden text has no place in a skill")
    if BACKSLASH_PATH.search(text):
        add("ERROR", "paths", "backslash path found; use forward slashes")

    for target in MD_LINK.findall(body):
        if re.match(r"^[a-z]+:", target):
            continue
        if not os.path.isfile(os.path.join(root, target)):
            add("ERROR", "link-missing", "SKILL.md links to '%s' which does not exist" % target)

    for sub in ("references", "assets", "scripts"):
        folder = os.path.join(root, sub)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            full = os.path.join(folder, fname)
            if not os.path.isfile(full):
                continue
            rel = "%s/%s" % (sub, fname)
            if rel not in body and fname not in body:
                add("WARN", "orphan", "%s is never mentioned in SKILL.md; the agent will not know it exists" % rel)
            if sub == "references" and fname.endswith(".md"):
                with open(full, encoding="utf-8-sig", errors="replace") as fh:
                    content = fh.read()
                if content.count("\n") + 1 > TOC_LINES and not re.search(r"(?m)^##\s+Contents", content):
                    add("WARN", "reference-toc", "%s is over %d lines and has no '## Contents' list" % (rel, TOC_LINES))
                if any(x.endswith(".md") and not re.match(r"^[a-z]+:", x) for x in MD_LINK.findall(content)):
                    add("ERROR", "reference-chain", "%s links to another file; references must be one level deep" % rel)
            if sub == "scripts" and fname.endswith(".py"):
                try:
                    with open(full, encoding="utf-8-sig") as fh:
                        tree = ast.parse(fh.read(), filename=rel)
                    if not ast.get_docstring(tree):
                        add("WARN", "script-docstring", "%s has no module docstring with usage and exit codes" % rel)
                except (SyntaxError, UnicodeDecodeError) as e:
                    add("ERROR", "script-syntax", "%s does not parse: %s" % (rel, e))
    if not any(level == "ERROR" for level, _, _ in out):
        add("OK", "summary", "no ERROR findings")
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1 or not os.path.isdir(args[0]):
        print(__doc__)
        return 2
    findings = check(args[0])
    errors = sum(1 for level, _, _ in findings if level == "ERROR")
    warns = sum(1 for level, _, _ in findings if level == "WARN")
    if "--json" in argv:
        print(json.dumps({"errors": errors, "warns": warns,
                          "findings": [{"level": a, "code": b, "message": c} for a, b, c in findings]}, indent=2))
    else:
        for level, code, msg in findings:
            print("%-5s %-20s %s" % (level, code, msg))
        print("\nRESULT: %d error(s), %d warning(s). Form only: run the trigger and task evals before trusting the skill." % (errors, warns))
    return 1 if errors else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
