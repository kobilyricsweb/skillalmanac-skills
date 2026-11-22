#!/usr/bin/env python3
"""Check a session handoff note for missing sections, vague items and unproven claims.

    python handoff_note_check.py <note.md> [--root <repo-root>]

Reads the note (and, with --root, looks up the file paths it names under that
folder). Writes nothing and prints one JSON object to stdout:

    {"schema_version": 1, "file": ..., "ok": true|false, "counts": {"PROBLEM": n, "NOTE": n},
     "findings": [{"level", "code", "line", "message"}, ...]}

Exit codes: 0 = no PROBLEM finding, 1 = at least one PROBLEM, 2 = usage error
or unreadable file (the JSON then has "error" and an empty findings list).

PROBLEM findings are facts a reader would trip over: a required section or
header line is missing or empty, a change names no file, a verification line has
no command or no result, a named path does not exist, a placeholder or a
credential-like string is left in. NOTE findings are leads to judge: vague
wording, undecided options without a default, a first step that is not concrete,
length. The script cannot tell whether a claim is true; it only checks that the
note shows its evidence.
"""
import json
import os
import re
import sys

# A handoff is read cold at the start of a session; past this the reader skims
# and misses the one line that matters.
MAX_LINES = 200
# Required "## " sections: key -> (label, accepted heading words).
SECTIONS = {
    "goal": ("Goal", ("goal",)),
    "state": ("Current state", ("current state", "state")),
    "changes": ("Changes made", ("changes made", "changes", "what changed")),
    "verification": ("Verification", ("verification", "verified")),
    "decisions": ("Open decisions", ("open decisions", "decisions")),
    "next": ("Next steps", ("next steps", "next")),
    "commands": ("Commands", ("commands",)),
    "unverified": ("Not verified", ("not verified", "unverified", "not done")),
}
DATE = re.compile(r"^\s*(?:[-*]\s*)?\**Written\**:\**\s*(\d{4}-\d{2}-\d{2})", re.M | re.I)
REPO_STATE = re.compile(r"^\s*(?:[-*]\s*)?\**Repo state\**:\**\s*(.+)$", re.M | re.I)
HASH = re.compile(r"\b[0-9a-f]{7,40}\b")
VAGUE = [
    r"\bfixed (some )?(stuff|things|issues|bugs)\b", r"\b(some|other|a few|various) (stuff|things)\b",
    r"\bvarious (fixes|changes|updates|tweaks|improvements)\b", r"\bmisc(ellaneous)?\b",
    r"\bminor (fixes|changes|tweaks|updates)\b", r"\bcleaned? up\b", r"\btweak(ed|s)?\b",
    r"\bmade it work\b", r"\bworks now\b", r"\bshould be (fine|ok|okay)\b", r"\blooks good\b",
    r"\bas discussed\b", r"\bas before\b", r"\bthe usual\b", r"\betc\b\.?", r"\band so on\b",
    r"\bwip\b", r"\bmostly (done|working)\b", r"\bupdated (the )?(code|files?)\b", r"\bimproved\b",
]
# A claim of success must come with a command and its result on the same line.
CLAIM = re.compile(
    r"\b(works|working|passes|passing|passed|all tests|verified|tested|no errors|is fixed|now works|builds? cleanly|green)\b", re.I)
RESULT = re.compile(
    r"(exit(?:ed)?(?: code)? \d+|\b\d+ (?:passed|failed|tests?|errors?|warnings?|ok|files?)\b|\b(?:returned|printed|showed|output|status|http) \S+|"
    r"\b(?:passed|failed|not run|did not run|could not run)\b|\b0 (?:errors|failures|warnings|fail)\b)", re.I)
NOT_RUN = re.compile(r"\b(not run|did not run|could not run|untested|not tested|not verified|unverified|never ran)\b", re.I)
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)")
# Assignment form in any letter case ("password = hunter2abc", "API_TOKEN: abc..."):
# a key-like name, = or :, and a value of 8+ characters that is not a reference.
SECRET_ASSIGN = re.compile(r"\b[\w.-]*(?:key|token|secret|password|passwd|pwd)[\"']?\s*[=:]\s*[\"']?([^\s\"'`,;]{8,})", re.I)
NOT_A_VALUE = re.compile(r"^(<|\$|\{|%|see[-_ ]|vault|env|redacted|example|changeme|placeholder|none|null|your[-_])", re.I)
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|<fill[^>]*>|\{\{[^}]*\}\}|\[\s*(?:describe|fill|path)[^\]]*\]", re.I)
BACKTICK = re.compile(r"`([^`\n]+)`")
PATHLIKE = re.compile(r"^(?:\./)?[\w.@-]+(?:/[\w.@*-]+)+/?$|^[\w@-]+\.[A-Za-z][\w]{0,5}$")
LINE_SUFFIX = re.compile(r"(?::\d+(?:-\d+)?|#L\d+(?:-L?\d+)?)$")
GONE = re.compile(r"\b(deleted|removed|renamed from|moved from)\b", re.I)
BULLET = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$")
NUMBERED = re.compile(r"^\s*\d+[.)]\s+")


def add(findings, level, code, line, message):
    findings.append({"level": level, "code": code, "line": line, "message": message})


def split_sections(lines):
    """Return ({key: [(lineno, text), ...]}, {key: heading_lineno}, unknown headings).

    Fenced code blocks are kept inside their section but headings inside them are ignored.
    """
    by_key, where, unknown = {}, {}, []
    current, in_fence = None, False
    for no, raw in enumerate(lines, 1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else re.match(r"^##\s+(.+?)\s*#*\s*$", raw)
        if m:
            title = m.group(1).strip().lower()
            current = None
            for key, (_label, words) in SECTIONS.items():
                if title in words:
                    current = key
                    where.setdefault(key, no)
                    by_key.setdefault(key, [])
                    break
            if current is None:
                unknown.append((no, m.group(1).strip()))
            continue
        if current is not None:
            by_key[current].append((no, raw))
    return by_key, where, unknown


def content_lines(body):
    """Non-empty lines outside fences, as (lineno, text); fenced lines are returned separately."""
    prose, fenced, in_fence = [], [], False
    for no, raw in body:
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not raw.strip():
            continue
        (fenced if in_fence else prose).append((no, raw))
    return prose, fenced


def bullets(prose):
    out = []
    for no, raw in prose:
        m = BULLET.match(raw)
        if m:
            out.append((no, m.group(1)))
    return out


def check(path, root):
    findings = []
    with open(path, "rb") as fh:
        data = fh.read()
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if not text.strip():
        raise ValueError("the note is empty")

    if len(lines) > MAX_LINES:
        add(findings, "NOTE", "too_long", 1, "note has %d lines; over %d the next reader skims. Move detail to a linked file." % (len(lines), MAX_LINES))

    # Header lines
    if not DATE.search(text):
        add(findings, "PROBLEM", "missing_date", 1, "no 'Written: YYYY-MM-DD' line; a reader cannot tell how stale the note is.")
    rs = REPO_STATE.search(text)
    if not rs:
        add(findings, "PROBLEM", "missing_repo_state", 1, "no 'Repo state:' line with branch and commit (or 'no git').")
    elif not HASH.search(rs.group(1)) and "no git" not in rs.group(1).lower():
        add(findings, "PROBLEM", "repo_state_no_commit", text[:rs.start()].count("\n") + 1,
            "'Repo state' names no commit hash and does not say 'no git'.")

    # Whole-note scans
    in_fence = False
    for no, raw in enumerate(lines, 1):
        if raw.strip().startswith("```"):
            in_fence = not in_fence
        am = SECRET_ASSIGN.search(raw)
        if SECRET.search(raw) or (am and not NOT_A_VALUE.match(am.group(1))):
            add(findings, "PROBLEM", "credential_like", no, "credential-like string; remove it and say where the value comes from. Value not repeated here.")
        if not in_fence and PLACEHOLDER.search(raw):
            add(findings, "PROBLEM", "placeholder_left", no, "unfilled placeholder or TODO marker.")
        if not in_fence:
            for pat in VAGUE:
                m = re.search(pat, raw, re.I)
                if m:
                    add(findings, "NOTE", "vague_item", no, "vague wording '%s'; name the file, the behaviour or the number." % m.group(0))
                    break

    by_key, where, _unknown = split_sections(lines)
    for key, (label, _w) in SECTIONS.items():
        if key not in where:
            add(findings, "PROBLEM", "missing_section", 1, "required section '## %s' is missing." % label)
            continue
        prose, fenced = content_lines(by_key[key])
        if not prose and not fenced:
            add(findings, "PROBLEM", "empty_section", where[key], "section '## %s' is empty." % label)

    # Changes: every bullet names a file; named files exist
    if "changes" in by_key:
        prose, _f = content_lines(by_key["changes"])
        items = bullets(prose)
        for no, item in items:
            spans = BACKTICK.findall(item)
            paths = [s for s in spans if PATHLIKE.match(LINE_SUFFIX.sub("", s.strip()))]
            if not paths:
                add(findings, "PROBLEM", "change_without_path", no, "change names no file in backticks: '%s'" % item[:70])
                continue
            for p in paths:
                clean = LINE_SUFFIX.sub("", p.strip())
                if root and not GONE.search(item) and "*" not in clean:
                    if not os.path.exists(os.path.join(root, clean)):
                        add(findings, "PROBLEM", "path_missing", no, "path '%s' does not exist under the given root." % clean)

    # Verification: command in backticks plus a result, or an explicit 'not run'
    if "verification" in by_key:
        prose, _f = content_lines(by_key["verification"])
        for no, item in bullets(prose):
            if NOT_RUN.search(item):
                continue
            has_cmd = bool(BACKTICK.search(item))
            has_result = bool(RESULT.search(item))
            if not has_cmd:
                add(findings, "PROBLEM", "verification_no_command", no, "verification line shows no command in backticks: '%s'" % item[:70])
            elif not has_result:
                add(findings, "PROBLEM", "verification_no_result", no, "verification line shows a command but no result (exit code, counts or output): '%s'" % item[:70])

    # Claims outside Verification need evidence on the same line
    for key in ("state", "changes", "goal"):
        if key not in by_key:
            continue
        prose, _f = content_lines(by_key[key])
        for no, raw in prose:
            if CLAIM.search(raw) and not RESULT.search(raw) and not NOT_RUN.search(raw) and "verification" not in raw.lower():
                add(findings, "PROBLEM", "claim_without_evidence", no,
                    "success claim with no result on the line; move it to Verification with the command and output: '%s'" % raw.strip()[:70])

    # Open decisions
    if "decisions" in by_key:
        prose, _f = content_lines(by_key["decisions"])
        items = bullets(prose)
        flat = " ".join(t for _n, t in prose).strip().lower()
        if not (len(items) == 0 and re.match(r"^(none|no open decisions)\b", flat)):
            for no, item in items:
                if "?" not in item:
                    add(findings, "PROBLEM", "decision_not_a_question", no, "open decision is not phrased as a question: '%s'" % item[:70])
                if not re.search(r"\b(default|recommend\w*|leaning|proposed|option)\b", item, re.I):
                    add(findings, "NOTE", "decision_no_default", no, "open decision names no options or default; the next session cannot proceed without the owner.")

    # Next steps: numbered; first step concrete
    if "next" in by_key:
        prose, _f = content_lines(by_key["next"])
        steps = [(n, r) for n, r in prose if NUMBERED.match(r)]
        if not steps:
            add(findings, "PROBLEM", "next_not_numbered", where["next"], "next steps are not a numbered list in the order to do them.")
        elif not BACKTICK.search(steps[0][1]):
            add(findings, "NOTE", "first_step_not_concrete", steps[0][0], "the first step has no command or file in backticks.")

    # Commands: at least one fenced block or backticked command, no placeholders
    if "commands" in by_key:
        prose, fenced = content_lines(by_key["commands"])
        if not fenced and not any(BACKTICK.search(r) for _n, r in prose):
            add(findings, "PROBLEM", "commands_not_literal", where["commands"], "no literal command (fenced block or backticks); prose like 'run the tests' is not a command.")
        for no, raw in fenced:
            if re.search(r"<[A-Za-z][\w -]*>", raw) and "<<" not in raw:
                add(findings, "NOTE", "command_has_placeholder", no, "command contains a <placeholder>; give the real value or say where to find it.")

    return findings


def main(argv):
    args, root, note = list(argv), None, None
    while args:
        a = args.pop(0)
        if a == "--root":
            if not args:
                return emit({"file": note, "ok": False, "error": "--root needs a folder", "counts": {"PROBLEM": 0, "NOTE": 0}, "findings": []}, 2)
            root = args.pop(0)
        elif note is None:
            note = a
        else:
            return emit({"file": note, "ok": False, "error": "unexpected argument: %s" % a, "counts": {"PROBLEM": 0, "NOTE": 0}, "findings": []}, 2)
    if note is None:
        return emit({"file": None, "ok": False, "error": "usage: handoff_note_check.py <note.md> [--root <repo-root>]", "counts": {"PROBLEM": 0, "NOTE": 0}, "findings": []}, 2)
    if root is not None and not os.path.isdir(root):
        return emit({"file": note, "ok": False, "error": "root is not a folder: %s" % root, "counts": {"PROBLEM": 0, "NOTE": 0}, "findings": []}, 2)
    try:
        findings = check(note, root)
    except (OSError, ValueError) as exc:
        why = "file not found" if isinstance(exc, FileNotFoundError) else str(exc)
        return emit({"file": os.path.basename(note), "ok": False, "error": "cannot read note: %s" % why, "counts": {"PROBLEM": 0, "NOTE": 0}, "findings": []}, 2)
    findings.sort(key=lambda f: (f["line"], f["code"]))
    counts = {"PROBLEM": sum(f["level"] == "PROBLEM" for f in findings), "NOTE": sum(f["level"] == "NOTE" for f in findings)}
    ok = counts["PROBLEM"] == 0
    return emit({"file": os.path.basename(note), "ok": ok, "counts": counts, "findings": findings}, 0 if ok else 1)


def emit(obj, code):
    obj = dict([("schema_version", 1)] + list(obj.items()))
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True, sort_keys=False) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
