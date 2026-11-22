#!/usr/bin/env python3
"""Inventory the rule and instruction files in a repo and suggest where each should go.

    python rules_inventory.py <repo-root> [--json]

Reads rule files of the known formats under the repo root. Writes nothing.
Exit codes: 0 = inventory printed, 2 = usage error or the folder cannot be read.

The suggestion for each file comes from its activation (always, glob, model
decision, manual) and its shape (short conventions or a long step-by-step
procedure). It is a starting point for a decision, not the decision.
"""
import json
import os
import re
import sys

SKIP_DIRS = {"node_modules", ".git", "dist", "build", "vendor", ".venv", "venv", "__pycache__", ".next", "target"}
# An always-loaded rule longer than this costs every session real context;
# with numbered steps on top it is almost certainly a procedure.
LONG_ALWAYS_ON_LINES = 25
# A procedure has several ordered steps.
MIN_STEPS_FOR_PROCEDURE = 4
# On-demand rules this short that state plain conventions usually belong in the always-on file.
SHORT_RULE_LINES = 6
# Search depth below the repo root; rule folders are near the top.
MAX_DEPTH = 5


def read(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def frontmatter(text):
    text = text.replace("\r\n", "\n").lstrip(chr(0xFEFF))
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    data = {}
    for line in text[4:end].split("\n"):
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            data[m.group(1)] = m.group(2).strip().strip("\"'")
    return data, text[end + 4:].lstrip("\n")


def find_sources(root):
    found = []
    base_depth = root.rstrip(os.sep).count(os.sep)
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if base.count(os.sep) - base_depth >= MAX_DEPTH:
            dirs[:] = []
        rel = os.path.relpath(base, root).replace(os.sep, "/")
        rel = "" if rel == "." else rel + "/"
        for f in sorted(files):
            p, kind = rel + f, None
            if ".cursor/rules/" in "/" + rel and f.endswith(".mdc"):
                kind = "cursor-rule"
            elif ".cursor/rules/" in "/" + rel and f.endswith(".md"):
                kind = "cursor-rule-ignored"
            elif f == ".cursorrules":
                kind = "cursor-legacy"
            elif (".windsurf/rules/" in "/" + rel or ".devin/rules/" in "/" + rel) and f.endswith(".md"):
                kind = "windsurf-rule"
            elif f in (".windsurfrules", "global_rules.md") and (rel == "" or rel.endswith((".windsurf/", ".devin/"))):
                kind = "windsurf-legacy"
            elif p == ".github/copilot-instructions.md":
                kind = "copilot-instructions"
            elif rel.startswith(".github/instructions/") and f.endswith(".md"):
                kind = "copilot-scoped"
            elif ".claude/rules/" in "/" + rel and f.endswith(".md"):
                kind = "claude-rule"
            elif f in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
                kind = "instruction-file"
            if kind:
                found.append((p, kind, os.path.join(base, f)))
    return found


def activation(kind, fm):
    if kind == "cursor-rule":
        if fm.get("alwaysApply", "").lower() == "true":
            return "always"
        if fm.get("globs"):
            return "glob"
        return "model-decision" if fm.get("description") else "manual"
    if kind == "windsurf-rule":
        return {"always_on": "always", "glob": "glob", "model_decision": "model-decision", "manual": "manual"}.get(
            fm.get("trigger", ""), "always" if not fm else "manual")
    if kind in ("copilot-scoped", "claude-rule"):
        return "glob" if (fm.get("applyTo") or fm.get("paths")) else "always"
    if kind == "cursor-rule-ignored":
        return "not loaded"
    return "always"


def shape(body):
    lines = [l for l in body.split("\n") if l.strip()]
    steps = len(re.findall(r"(?m)^\s*\d+[.)]\s", body))
    checklist = len(re.findall(r"(?m)^\s*[-*]\s+\[[ x]\]", body))
    return len(lines), steps, checklist


def glob_directory(globs):
    """The deepest literal directory that covers a glob list, or '' for the repo root."""
    best = None
    for g in re.split(r"[,\s]+", globs.strip("[]")):
        g = g.strip("\"'")
        if not g:
            continue
        parts = []
        for seg in g.split("/"):
            if any(c in seg for c in "*?[{"):
                break
            parts.append(seg)
        literal = "/".join(parts[:-1] if parts and "." in parts[-1] else parts)
        best = literal if best is None else os.path.commonprefix([best, literal])
    return (best or "").strip("/")


def suggest(kind, act, body, fm):
    n, steps, checklist = shape(body)
    procedure = steps >= MIN_STEPS_FOR_PROCEDURE or checklist >= MIN_STEPS_FOR_PROCEDURE
    flags = []
    if kind == "cursor-rule-ignored":
        return "none until renamed", ["plain .md in .cursor/rules is ignored by the tool; decide whether it was meant to be a rule"]
    if kind == "instruction-file":
        if procedure and n > LONG_ALWAYS_ON_LINES:
            flags.append("contains step-by-step procedures; move those to skills and leave pointers")
        return "keep (shared always-on file)", flags
    if act == "always":
        if procedure and n > LONG_ALWAYS_ON_LINES // 2:
            flags.append(f"procedure filed as always-on ({n} lines, {steps} steps): loads in every session")
            return "skill, with a one-line pointer in AGENTS.md", flags
        if n > LONG_ALWAYS_ON_LINES * 2:
            flags.append(f"{n} lines always loaded; trim or split")
        return "root AGENTS.md", flags
    if act == "glob":
        d = glob_directory(fm.get("globs") or fm.get("paths") or fm.get("applyTo") or "")
        if procedure:
            flags.append("procedure scoped by file pattern; consider a skill")
        return (f"{d}/AGENTS.md (nested)" if d else "root AGENTS.md (pattern spans the repo; exact glob scope is lost)"), flags
    if act == "model-decision":
        if not procedure and n <= SHORT_RULE_LINES:
            flags.append("short convention filed as on-demand; if it should always hold, put it in AGENTS.md")
        return "skill", flags
    if not fm.get("description"):
        flags.append("no description: one must be written before it can trigger as a skill")
    return "skill", flags


def norm_line(line):
    return re.sub(r"[^a-z0-9 ]", "", line.lower()).strip()


def inventory(root):
    rows, line_index = [], {}
    for rel, kind, full in find_sources(root):
        text = read(full)
        fm, body = frontmatter(text)
        act = activation(kind, fm)
        dest, flags = suggest(kind, act, body, fm)
        n, steps, _ = shape(body)
        rows.append({"file": rel, "format": kind, "activation": act, "lines": n, "numbered_steps": steps,
                     "bytes": len(text.encode("utf-8")), "description": fm.get("description", ""),
                     "globs": fm.get("globs") or fm.get("paths") or fm.get("applyTo") or "",
                     "suggested_destination": dest, "flags": flags})
        for l in body.split("\n"):
            key = norm_line(re.sub(r"^\s*([-*]|\d+[.)])\s+", "", l))
            if len(key.split()) >= 4:
                line_index.setdefault(key, set()).add(rel)
    overlaps = [{"text": k, "files": sorted(v)} for k, v in sorted(line_index.items()) if len(v) > 1]
    return rows, overlaps


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    if not os.path.isdir(root):
        print(f"{root} is not a folder", file=sys.stderr)
        return 2
    rows, overlaps = inventory(root)
    if "--json" in argv:
        print(json.dumps({"sources": rows, "identical_lines_in_several_sources": overlaps}, indent=2))
        return 0
    if not rows:
        print("No rule or instruction files of a known format were found. User-level rules stored in an application's settings are not on disk; ask the user.")
        return 0
    always_bytes = sum(r["bytes"] for r in rows if r["activation"] == "always")
    print(f"{len(rows)} source file(s); {always_bytes} bytes are loaded in every session today.\n")
    print("| File | Format | Activation | Lines | Steps | Suggested destination |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['file']} | {r['format']} | {r['activation']} | {r['lines']} | {r['numbered_steps']} | {r['suggested_destination']} |")
    flagged = [(r["file"], f) for r in rows for f in r["flags"]]
    if flagged:
        print("\nFlags:")
        for file, f in flagged:
            print(f"- {file}: {f}")
    if overlaps:
        print("\nSame line in more than one source (merge once):")
        for o in overlaps[:40]:
            print(f"- \"{o['text'][:70]}\" in {', '.join(o['files'])}")
    print("\nNot detected: reworded duplicates, conflicting facts between sources, and rules kept in application settings. Read the sources for those.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
