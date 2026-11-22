#!/usr/bin/env python3
"""Check the form of a subagent definition file (Markdown with YAML frontmatter).

    python agent_def_lint.py <agent.md> [more.md ...] [--json]

Reads the given files and prints findings. Writes nothing.
Exit codes: 0 = no ERROR, 1 = at least one ERROR, 2 = usage error or unreadable file.

It checks form only: fields present, description wording, tool list against the
stated role, wording that assumes context the agent will not have, and whether
a bounded report format is defined. It cannot tell whether the agent does good work.
"""
import json
import re
import sys

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
# Below this length a description cannot hold both what the agent does and when to use it.
MIN_DESCRIPTION_CHARS = 80
# All agent descriptions are loaded into every session; long ones crowd the others out.
MAX_DESCRIPTION_CHARS = 600
# A body shorter than this has no room for input, rules and a report format.
MIN_BODY_WORDS = 40
READ_ONLY_ROLE = re.compile(r"\b(review(er|s|ing)?|audit(or|s|ing)?|research(er|ing)?|locat(e|or|ing)|find(er|s|ing)?|search(es|ing)?|explor(e|er|ing)|analy[sz](e|er|ing)|read-only|inspect(s|ing)?)\b", re.I)
TRIGGER = re.compile(r"\buse (this agent |it )?(when|whenever|for|before|after|proactively)\b|\bwhen (the|a|an|any|someone|asked)\b", re.I)
VAGUE_DESCRIPTION = re.compile(r"^(helps?|assists?|a helpful|general|useful)\b.{0,40}$", re.I)
ASSUMES_CONTEXT = re.compile(r"\b(as (we )?discussed|discussed (above|earlier)|from (above|earlier)|the (above|previous) (conversation|discussion|message)|continue (from )?where|what we talked about|earlier in (this|the) conversation)\b", re.I)
ASKS_USER = re.compile(r"\bask (the user|me|them)\b|\bcheck with the user\b|\bwait for (the user|confirmation)\b", re.I)
INVITES_EDITS = re.compile(r"\b(feel free to|go ahead and) (fix|change|edit|modify|update|refactor)\b|\bfix (any|small|minor) (issues|problems)\b", re.I)
REPORT_SECTION = re.compile(r"(?im)^#+ .*(report|output|response|return|format|deliver)|\b(report|respond|return|reply|output)\b[^\n]{0,60}\b(format|exactly|structure|sections|following)\b")
LENGTH_BOUND = re.compile(r"(?i)\b(at most|no more than|under|maximum|max|limit(ed)? to|up to|fewer than|within)\s+\**\d+\**\s+(lines|words|bullets|items|results|sentences|entries|locations|findings)")
INPUT_LOCATION = re.compile(r"(?i)\b(git (diff|status|log|show)|the caller('s)? (message|prompt|brief)|you (do|will|can)(n't| not) see the conversation|the (brief|prompt|message) (you receive|names|gives)|changed files|your input)\b")


def parse(text):
    text = text.replace("\r\n", "\n").lstrip(chr(0xFEFF))
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    lines, body = text[4:end].split("\n"), text[end + 4:].lstrip("\n")
    data, i = {}, 0
    while i < len(lines):
        m = re.match(r"^([\w-]+):\s*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("", ">", "|", ">-", "|-"):
            block = []
            while i < len(lines) and (lines[i].startswith(" ") or not lines[i].strip()):
                if lines[i].strip():
                    block.append(lines[i].strip())
                i += 1
            if val == "" and block and all(b.startswith("- ") for b in block):
                data[key] = [b[2:].strip().strip("\"'") for b in block]
            else:
                data[key] = " ".join(block)
        else:
            data[key] = val.strip("\"'")
    return data, body


def as_set(value):
    if value is None:
        return None
    if isinstance(value, list):
        return {v.strip() for v in value if v.strip()}
    return {v.strip() for v in re.split(r"[,\s]+", value.strip("[]")) if v.strip()}


def lint_text(text):
    out = []

    def add(level, msg):
        out.append({"level": level, "message": msg})

    fm, body = parse(text)
    if fm is None:
        add("ERROR", "no YAML frontmatter; the file must start with '---', the fields, then '---'")
        return out
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not name:
        add("ERROR", "frontmatter has no 'name'")
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(name)):
        add("WARN", f"name '{name}' is not lowercase words joined by hyphens; callers have to type it")
    if not desc:
        add("ERROR", "frontmatter has no 'description'; the agent can never be chosen automatically")
    else:
        desc = str(desc)
        if len(desc) < MIN_DESCRIPTION_CHARS or VAGUE_DESCRIPTION.match(desc):
            add("ERROR", f"description is too thin to trigger delegation ({len(desc)} characters): say what it does, then 'Use when ...'")
        elif not TRIGGER.search(desc):
            add("WARN", "description does not say when to use the agent ('Use when ...')")
        if len(desc) > MAX_DESCRIPTION_CHARS:
            add("WARN", f"description is {len(desc)} characters; every session loads it, move detail into the body")
    tools, denied = as_set(fm.get("tools")), as_set(fm.get("disallowedTools")) or set()
    role_text = f"{name} {desc} {' '.join(body.split()[:60])}"
    read_only_role = READ_ONLY_ROLE.search(role_text) is not None
    if tools is None and not ({"Write", "Edit"} <= denied):
        add("WARN" if not read_only_role else "ERROR",
            "no 'tools' list: the agent inherits every tool of the caller, including file writes" +
            ("; this role reads and reports, so list read-only tools (Read, Grep, Glob)" if read_only_role else ""))
    elif tools is not None and read_only_role and (tools & WRITE_TOOLS) - denied:
        add("WARN", f"role reads and reports but tools include {sorted((tools & WRITE_TOOLS) - denied)}")
    words = len(body.split())
    if words < MIN_BODY_WORDS:
        add("ERROR", f"body is {words} words; it needs how to find the input, the rules to apply and the report format")
    m = ASSUMES_CONTEXT.search(body)
    if m:
        add("ERROR", f"body assumes the earlier conversation ('{m.group(0)}'); the agent starts without it")
    m = ASKS_USER.search(body)
    if m:
        add("ERROR", f"body tells the agent to consult the user ('{m.group(0)}'); it cannot, have it state assumptions and return open questions")
    m = INVITES_EDITS.search(body)
    if m and read_only_role:
        add("ERROR", f"body invites changes ('{m.group(0)}') although the role reads and reports")
    if not REPORT_SECTION.search(body):
        add("ERROR", "no report format; say exactly what the final message must contain")
    elif not LENGTH_BOUND.search(body):
        add("WARN", "report format has no numeric length bound (for example 'at most 30 lines')")
    if words >= MIN_BODY_WORDS and not INPUT_LOCATION.search(body):
        add("WARN", "body does not say how the agent finds its input (a command, a folder, or the caller's message)")
    if str(fm.get("permissionMode", "")).lower() in ("bypasspermissions", "dontask"):
        add("WARN", f"permissionMode '{fm.get('permissionMode')}' removes permission prompts; set it only at the user's explicit request")
    return out


def main(argv):
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    results, errors = {}, 0
    for p in paths:
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"cannot read {p}: {e}", file=sys.stderr)
            return 2
        if not text.strip():
            print(f"{p} is empty", file=sys.stderr)
            return 2
        results[p] = lint_text(text)
        errors += sum(1 for f in results[p] if f["level"] == "ERROR")
    if "--json" in argv:
        print(json.dumps(results, indent=2))
    else:
        for p, findings in results.items():
            print(p)
            for f in findings:
                print(f"  {f['level']:5} {f['message']}")
            if not findings:
                print("  OK    no findings")
        print(f"\n{errors} error(s). Form only: try the agent on two or three real requests.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
