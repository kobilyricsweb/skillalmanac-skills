#!/usr/bin/env python3
"""Turn a commit list or a CHANGELOG draft into a release-notes skeleton and a version bump.

Usage:
    python release_notes.py INPUT --current-version 1.4.2
        [--format auto|log|changelog] [--section NAME]
        [--audience users|developers]
        [--markdown-out PATH [--force]]

INPUT is a text file with one of:
  * `git log` output (full format with `commit <hash>` headers, or one commit per line,
    optionally with a leading hash and a leading "- " or "* ");
  * a Keep-a-Changelog style CHANGELOG.md (the Unreleased section, or the section named by
    --section, or the top section when neither exists).

Reads: INPUT only. Writes: nothing, unless --markdown-out is given; then only that one file
(the Markdown skeleton). The output path may never be the input path, even with --force.
--force only allows replacing an existing output file that is not the input.
Network: none. Nothing is pushed, tagged or committed.

Stdout: one strict JSON document (schema_version "1"): current_version, proposed_version,
bump, bump_standard, bump_reason, verdict, counts, sections{}, breaking[], unsorted[],
dropped[], warnings[], skeleton.
Exit codes: 0 verdict ok, 1 findings (verdict needs_review or ask_user), 2 bad input or usage.
A bad-input run still prints a JSON object with an "error" key.
"""
import argparse
import codecs
import json
import os
import re
import sys

SCHEMA_VERSION = "1"

# Share of entries without a recognised type above which the log is treated as not
# structured. Above this the type grouping would be mostly guesswork, so the verdict is
# "ask_user". 30 percent is the brief's working value, not a measured optimum.
UNTYPED_LIMIT = 0.30

# Subjects longer than this are cut off by most git UIs and mail tools (convention: 72).
SUBJECT_MAX = 72

# When at least this share of conventional entries carry a scope, an unscoped entry is
# reported as inconsistent. Below it, scopes are not this log's habit and nothing is flagged.
SCOPE_CONVENTION_SHARE = 0.5

KNOWN_TYPES = {"feat", "fix", "perf", "docs", "chore", "refactor", "test", "build", "ci", "style", "revert"}
INTERNAL_TYPES = {"chore", "refactor", "test", "build", "ci", "style"}

# type -> section name in the notes. "change", "deprecate", "remove" and "security" only
# come from CHANGELOG headings.
TYPE_SECTION = {
    "feat": "Added", "fix": "Fixed", "perf": "Performance", "docs": "Documentation",
    "chore": "Internal", "refactor": "Internal", "test": "Internal", "build": "Internal",
    "ci": "Internal", "style": "Internal", "change": "Changed", "deprecate": "Deprecated",
    "remove": "Removed", "security": "Security",
}
# type -> bump it causes. Internal types and docs cause none on their own.
TYPE_BUMP = {
    "feat": "minor", "change": "minor", "deprecate": "minor", "remove": "minor",
    "fix": "patch", "perf": "patch", "security": "patch",
}
BUMP_RANK = {"none": 0, "patch": 1, "minor": 2, "major": 3}

HEADING_TYPE = {
    "added": "feat", "new": "feat", "changed": "change", "deprecated": "deprecate",
    "removed": "remove", "fixed": "fix", "security": "security", "performance": "perf",
    "documentation": "docs", "internal": "chore",
}

USER_SECTION_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security",
                      "Performance", "Reverted"]
DEV_ONLY_SECTIONS = ["Documentation", "Internal"]

CONV_RE = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()\r\n]*)\))?(?P<bang>!)?:\s*(?P<desc>\S.*)?$")
BREAKING_FOOTER_RE = re.compile(r"^BREAKING[ -]CHANGE:\s*(.*)$")
FOOTER_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z-]*(?::\s|\s#)")
BREAKING_BULLET_RE = re.compile(r"^(?:\*\*|\[)?BREAKING(?:[ -]CHANGES?)?(?:\*\*|\])?:?\s*(?:\*\*)?\s*")
ISSUE_RE = re.compile(r"(?<![\w&/])#(\d+)\b")
HASH_LINE_RE = re.compile(r"^(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.I)
REVERT_QUOTED_RE = re.compile(r'^Revert\s+"(.+)"\s*$', re.I)
REVERTS_COMMIT_RE = re.compile(r"This reverts commit ([0-9a-f]{7,40})", re.I)
MERGE_PR_RE = re.compile(r"^Merge pull request #\d+\b", re.I)
MERGE_ANY_RE = re.compile(r"^Merge (pull request|branch|remote-tracking branch|tag)\b", re.I)
FIXUP_RE = re.compile(r"^(fixup!|squash!|amend!|wip\b)", re.I)
VERSION_RE = re.compile(r"^(?P<v>v?)(?P<maj>\d+)\.(?P<min>\d+)\.(?P<pat>\d+)(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")

# Wording that often hides a breaking change in an entry nobody marked as breaking.
BREAKING_HINT_RE = re.compile(
    r"\b(remov(?:e|es|ed|ing)|drop(?:s|ped|ping)?|renam(?:e|es|ed|ing)|no longer|incompatible"
    r"|requires?\s+(?:node|python|java|version|v?\d)|minimum\s+version|defaults?\s+(?:to|is|now)"
    r"|changes?\s+(?:the\s+)?default)\b", re.I)
HINT_TYPES = {"feat", "fix", "perf", "refactor", "change"}

# Internal wording that should be rewritten as the visible effect for users.
INTERNAL_WORD_RE = re.compile(
    r"\b(refactor\w*|handler|helper|wrapper|plumbing|boilerplate|internal(?:ly)?|wip|misc|stuff"
    r"|clean ?up|tweak\w*|lint\w*|mock\w*|dto|middleware|impl|utils?|utility|dedupe)\b", re.I)
USER_FACING_TYPES = {"feat", "fix", "perf", "change", "security", "deprecate", "remove"}

# Common imperative verbs for the "subject has a verb" check. Inflections are tried too.
VERBS = set("""
add allow apply avoid block bump cache change check clarify clean clear close collapse combine compute
describe explain
configure connect convert copy correct create cut debug declare default define delay delete
deprecate detect disable display document download drop enable encode ensure expand expose
extend extract fall fetch filter fix flag force format generate handle hide highlight
ignore implement import improve include increase initialize inline insert install introduce
invalidate keep limit load lock log make mark match merge migrate move normalize note
omit open optimize order override pad parse pass patch pin prevent print process prompt
protect provide publish pull push put raise read rebuild reduce refactor refresh register
reject release reload remove rename render reorder repair replace report request require
reset resolve restore restrict retry return reuse revert review rewrite rotate round run
save scale scroll select send separate set show shorten simplify skip sort speed split
start stop store stream strip submit support surface swap switch sync tag take throw
tighten toggle track transform translate trigger trim truncate try tune turn unify update
upgrade use validate verify warn wrap write
""".split())


def emit(report):
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False, sort_keys=False) + "\n")


def fail_input(message):
    sys.stderr.write("error: " + message + "\n")
    emit({"schema_version": SCHEMA_VERSION, "error": message})
    return 2


def read_text(path):
    """Read a file as text. Windows shells often write UTF-16; handle that and cp1252."""
    with open(path, "rb") as handle:
        raw = handle.read()
    if not raw.strip():
        raise ValueError("input file is empty")
    note = None
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        text = raw.decode("utf-16")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1252", errors="replace")
            note = "input was not valid UTF-8; decoded as cp1252, check accented characters"
    return text.replace("\r\n", "\n").replace("\r", "\n"), note


def norm_key(text):
    """Normalise a subject for duplicate and revert matching."""
    text = text.lower()
    text = re.sub(r"^\w+(\([^)]*\))?!?:\s*", "", text)
    text = re.sub(r"\(?#\d+\)?", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def starts_with_verb(desc):
    match = re.match(r"[A-Za-z]+", desc.strip())
    if not match:
        return False
    word = match.group(0).lower()
    candidates = {word}
    for suffix in ("ing", "ed", "es", "s", "d"):
        if word.endswith(suffix) and len(word) > len(suffix) + 1:
            base = word[: -len(suffix)]
            candidates.update({base, base + "e"})
            if len(base) > 2 and base[-1] == base[-2]:
                candidates.add(base[:-1])
    return bool(candidates & VERBS)


def new_entry(ref, subject, body, commit_hash=None, line=0):
    return {
        "ref": ref, "hash": commit_hash, "subject": subject.strip(), "body": list(body), "line": line,
        "type": None, "scope": None, "desc": subject.strip(), "breaking": False, "note": "",
        "conventional": False, "is_revert": False, "revert_hash": None, "revert_subject": None,
        "from_merge": False, "heading_type": None, "issues": [],
    }


def parse_log(text):
    """Return (entries, merges_skipped)."""
    lines = text.split("\n")
    entries, merges_skipped = [], 0
    if re.search(r"(?m)^commit [0-9a-f]{7,40}\b", text):
        blocks, current = [], None
        for number, line in enumerate(lines, 1):
            match = re.match(r"^commit ([0-9a-f]{7,40})\b", line)
            if match:
                current = {"hash": match.group(1), "line": number, "header": [], "msg": [], "in_msg": False}
                blocks.append(current)
            elif current is not None:
                if line.startswith("    ") or (current["in_msg"] and not line.strip()):
                    current["in_msg"] = True
                    current["msg"].append(line[4:] if line.startswith("    ") else "")
                elif not current["in_msg"]:
                    current["header"].append(line)
        for block in blocks:
            msg = list(block["msg"])
            while msg and not msg[0].strip():
                msg.pop(0)
            if not msg:
                continue
            is_merge = any(h.startswith("Merge:") for h in block["header"])
            subject, body = msg[0], msg[1:]
            if is_merge or MERGE_ANY_RE.match(subject):
                title = next((b.strip() for b in body if b.strip()), "")
                if MERGE_PR_RE.match(subject) and title:
                    entry = new_entry(block["hash"][:7], title, [], block["hash"], block["line"])
                    entry["from_merge"] = True
                    entries.append(entry)
                else:
                    merges_skipped += 1
                continue
            entries.append(new_entry(block["hash"][:7], subject, body, block["hash"], block["line"]))
        return entries, merges_skipped
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        is_continuation = line[0] in " \t" or BREAKING_FOOTER_RE.match(line.strip())
        if is_continuation and entries:
            entries[-1]["body"].append(line.strip())
            continue
        text_line = re.sub(r"^[-*+]\s+", "", line.strip())
        commit_hash = None
        match = HASH_LINE_RE.match(text_line)
        if match and len(text_line) > match.end():
            commit_hash = match.group(0)
            text_line = text_line[match.end():].strip()
        text_line = re.sub(r"^\([^)]*\)\s+", "", text_line) if commit_hash else text_line
        if MERGE_ANY_RE.match(text_line):
            merges_skipped += 1
            continue
        entries.append(new_entry(commit_hash[:7] if commit_hash else "L%d" % number, text_line, [], commit_hash, number))
    return entries, merges_skipped


def parse_changelog(text, section_name):
    """Return (entries, section_title). Entries come from bullets under ### headings."""
    lines = text.split("\n")
    h2 = [(i, re.sub(r"[\[\]]", "", m.group(1)).strip()) for i, l in enumerate(lines)
          for m in [re.match(r"^##\s+(?!#)(.+?)\s*$", l)] if m]
    start, end, title = 0, len(lines), "(whole file)"
    if h2:
        pick = None
        wanted = (section_name or "").strip().lower().lstrip("v")
        for index, (_, name) in enumerate(h2):
            token = re.split(r"\s+[-–—]\s+", name)[0].strip().lower().lstrip("v")
            if wanted and token == wanted:
                pick = index
                break
            if not wanted and token == "unreleased":
                pick = index
                break
        if pick is None:
            if wanted:
                raise ValueError("section '%s' not found; sections: %s" % (section_name, ", ".join(n for _, n in h2)))
            pick = 0
        start = h2[pick][0] + 1
        end = h2[pick + 1][0] if pick + 1 < len(h2) else len(lines)
        title = h2[pick][1]
    entries, heading, top_indent = [], None, None
    for number in range(start, end):
        line = lines[number]
        heading_match = re.match(r"^###\s+(.+?)\s*$", line)
        if heading_match:
            heading = heading_match.group(1).strip()
            top_indent = None
            continue
        bullet = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if bullet:
            indent = len(bullet.group(1).replace("\t", "    "))
            if entries and top_indent is not None and indent > top_indent:
                entries[-1]["body"].append(bullet.group(2).strip())
                continue
            top_indent = indent
            entry = new_entry("L%d" % (number + 1), bullet.group(2), [], None, number + 1)
            entry["heading_type"] = HEADING_TYPE.get((heading or "").lower())
            entry["heading"] = heading
            entries.append(entry)
        elif line.strip() and line[0] in " \t" and entries:
            entries[-1]["body"].append(line.strip())
    return entries, title


def classify(entry):
    """Fill type, scope, desc, breaking, note, issues, revert data from the subject and body."""
    subject = entry["subject"]
    if "heading" in entry:
        marker = BREAKING_BULLET_RE.match(subject)
        if marker:
            entry["breaking"] = True
            subject = subject[marker.end():].strip() or subject
    quoted = REVERT_QUOTED_RE.match(subject)
    if quoted:
        entry["is_revert"] = True
        entry["type"] = "revert"
        entry["revert_subject"] = quoted.group(1)
        entry["desc"] = subject
    else:
        match = CONV_RE.match(subject)
        if match and match.group("type").lower() in KNOWN_TYPES:
            entry["type"] = match.group("type").lower()
            entry["scope"] = (match.group("scope") or "").strip() or None
            entry["desc"] = (match.group("desc") or "").strip()
            entry["conventional"] = True
            if match.group("bang"):
                entry["breaking"] = True
            if entry["type"] == "revert":
                entry["is_revert"] = True
                entry["revert_subject"] = entry["desc"].strip('"')
        else:
            entry["type"] = entry["heading_type"]
            entry["desc"] = subject
    footer_note = None
    body = entry["body"]
    for index, line in enumerate(body):
        hit = BREAKING_FOOTER_RE.match(line.strip())
        if hit:
            entry["breaking"] = True
            parts = [hit.group(1).strip()]
            for follow in body[index + 1:]:
                if not follow.strip() or FOOTER_TOKEN_RE.match(follow.strip()):
                    break
                parts.append(follow.strip())
            footer_note = " ".join(p for p in parts if p)
            break
    if footer_note:
        entry["note"] = footer_note
    elif entry["breaking"] and entry["body"] and "heading" in entry:
        entry["note"] = " ".join(b.strip() for b in entry["body"])
    for line in body:
        found = REVERTS_COMMIT_RE.search(line)
        if found:
            entry["revert_hash"] = found.group(1).lower()
    issues = set(int(n) for n in ISSUE_RE.findall(entry["subject"] + " " + " ".join(body)))
    entry["issues"] = sorted(issues)


def clean_text(entry):
    text = entry["desc"].strip()
    text = re.sub(r"\s*\(#\d+\)\s*$", "", text).rstrip(".").strip()
    return text[:1].upper() + text[1:] if text else text


def warn(warnings, code, severity, message, refs=None):
    warnings.append({"code": code, "severity": severity, "message": message, "refs": refs or []})


def pair_reverts(entries, dropped, warnings):
    """Drop a revert and its target when both are in this release."""
    removed = set()
    for rev in entries:
        if not rev["is_revert"] or id(rev) in removed:
            continue
        target = None
        if rev["revert_hash"]:
            for other in entries:
                if other is rev or id(other) in removed or not other["hash"]:
                    continue
                if other["hash"].startswith(rev["revert_hash"]) or rev["revert_hash"].startswith(other["hash"]):
                    target = other
                    break
        if target is None and rev["revert_subject"]:
            key = norm_key(rev["revert_subject"])
            for other in entries:
                if other is rev or id(other) in removed:
                    continue
                if key and norm_key(other["subject"]) == key:
                    target = other
                    break
        if target is None:
            warn(warnings, "revert_target_outside", "warn",
                 "revert '%s' targets a change that is not in this release; write it as what users see again, and check whether it removes a released feature (that would be breaking)" % rev["subject"],
                 [rev["ref"]])
        elif target["is_revert"]:
            warn(warnings, "revert_chain", "warn",
                 "revert '%s' reverts another revert; resolve by hand which behaviour users end up with" % rev["subject"],
                 [rev["ref"], target["ref"]])
        else:
            removed.add(id(rev))
            removed.add(id(target))
            dropped.append({"reason": "reverted_in_release", "ref": rev["ref"], "subject": rev["subject"]})
            dropped.append({"reason": "reverted_in_release", "ref": target["ref"], "subject": target["subject"]})
            warn(warnings, "revert_pair_dropped", "info",
                 "'%s' and its revert are both in this release; both left out of the notes" % target["subject"],
                 [target["ref"], rev["ref"]])
    return [e for e in entries if id(e) not in removed]


def dedupe(entries, dropped, warnings):
    seen, kept = {}, []
    for entry in entries:
        key = (entry["scope"] or "", norm_key(entry["desc"]))
        if key[1] and key in seen:
            first = seen[key]
            first["issues"] = sorted(set(first["issues"]) | set(entry["issues"]))
            dropped.append({"reason": "duplicate_subject", "ref": entry["ref"], "subject": entry["subject"]})
            warn(warnings, "duplicate_subject", "warn",
                 "same subject appears more than once (cherry-pick or repeated commit); kept the first, dropped the copy",
                 [first["ref"], entry["ref"]])
            continue
        seen[key] = entry
        kept.append(entry)
    return kept


def bump_for(entries):
    best, reason = "none", "no entry that users would notice"
    for entry in entries:
        if entry["breaking"]:
            return "major", "breaking change marked in %s: %s" % (entry["ref"], clean_text(entry)[:60])
        bump = "patch" if entry["is_revert"] else TYPE_BUMP.get(entry["type"], "none")
        if BUMP_RANK[bump] > BUMP_RANK[best]:
            best = bump
            label = "revert" if entry["is_revert"] else entry["type"]
            reason = "highest-impact entry is %s (%s)" % (label, entry["ref"])
    return best, reason


def build_report(entries, merges_skipped, args, version, input_format, notes):
    warnings, dropped = [], []
    for note in notes:
        warn(warnings, "input_note", "warn", note)
    if merges_skipped:
        warn(warnings, "merge_skipped", "info",
             "%d merge commit(s) skipped; use git log --no-merges or --first-parent to avoid noise" % merges_skipped)
    live = []
    for entry in entries:
        if FIXUP_RE.match(entry["subject"]):
            dropped.append({"reason": "fixup_or_wip", "ref": entry["ref"], "subject": entry["subject"]})
            continue
        classify(entry)
        live.append(entry)
    if not live:
        raise ValueError("no commits or entries found in the input")
    considered = len(live)
    untyped = [e for e in live if e["type"] is None and not e["is_revert"]]
    ratio = len(untyped) / considered
    live = pair_reverts(live, dropped, warnings)
    live = dedupe(live, dropped, warnings)

    conventional = [e for e in live if e["conventional"]]
    scoped_share = (sum(1 for e in conventional if e["scope"]) / len(conventional)) if conventional else 0.0
    for entry in live:
        ref = [entry["ref"]]
        if input_format == "log" and len(entry["subject"]) > SUBJECT_MAX and not entry["from_merge"]:
            warn(warnings, "subject_too_long", "warn", "subject is %d characters (limit %d): %s" % (len(entry["subject"]), SUBJECT_MAX, entry["subject"][:50]), ref)
        if not entry["desc"].strip():
            warn(warnings, "empty_description", "warn", "entry has a type but no description", ref)
        elif not entry["is_revert"] and not starts_with_verb(entry["desc"]):
            warn(warnings, "no_leading_verb", "warn", "description does not start with a verb: '%s'" % entry["desc"][:50], ref)
        if entry["conventional"] and not entry["scope"] and conventional and scoped_share >= SCOPE_CONVENTION_SHARE and entry["type"] in USER_FACING_TYPES:
            warn(warnings, "missing_scope", "warn", "no scope although %d%% of typed entries have one: '%s'" % (round(scoped_share * 100), entry["subject"][:50]), ref)
        if entry["breaking"] and not entry["note"]:
            warn(warnings, "breaking_without_migration_text", "warn", "breaking entry has no BREAKING CHANGE text saying who is affected and what to do: '%s'" % entry["subject"][:50], ref)
        if not entry["breaking"] and entry["type"] in HINT_TYPES and BREAKING_HINT_RE.search(entry["desc"]):
            warn(warnings, "possible_unmarked_breaking", "warn", "wording suggests a breaking change but no marker: '%s'" % entry["subject"][:50], ref)
        if entry["type"] == "remove" and not entry["breaking"]:
            warn(warnings, "removed_not_marked_breaking", "warn", "listed under Removed but not marked BREAKING: confirm whether users lose something they use", ref)
        if entry["type"] == "change" and entry.get("heading") is not None:
            warn(warnings, "changed_is_ambiguous", "info", "'Changed' heading hides whether behaviour breaks; confirm and mark BREAKING if so: '%s'" % entry["subject"][:50], ref)
        if entry["type"] in USER_FACING_TYPES or entry["is_revert"]:
            hit = INTERNAL_WORD_RE.search(entry["desc"])
            if hit:
                entry["rewrite"] = hit.group(0)
                warn(warnings, "internal_wording", "warn", "internal wording '%s' in a user-facing entry; say what users see" % hit.group(0), ref)
        if CVE_RE.search(entry["subject"] + " " + " ".join(entry["body"])):
            warn(warnings, "security_disclosure", "warn", "mentions a CVE: confirm the fix is available and disclosure timing before publishing", ref)
    if ratio > UNTYPED_LIMIT:
        warn(warnings, "log_not_structured", "warn", "%d of %d entries (%d%%) have no recognised type, above the %d%% limit; ask the user how to sort them instead of guessing" % (len(untyped), considered, round(ratio * 100), round(UNTYPED_LIMIT * 100)))

    match = VERSION_RE.match(version)
    if match.group("pre"):
        warn(warnings, "prerelease_current", "warn", "current version is a pre-release; the bump is computed on its numbers, decide whether to cut the final version first")
    bump, reason = bump_for(live)
    standard = bump
    if int(match.group("maj")) == 0:
        if bump == "major":
            bump = "minor"
            reason += "; 0.x convention applied (breaking changes bump the minor number, 1.0.0 is a deliberate decision)"
            warn(warnings, "zero_major", "warn", "version is 0.x: semver allows any change at any time; breaking change proposed as a minor bump, standard rule would give major")
        else:
            warn(warnings, "zero_major", "info", "version is 0.x: breaking changes are not guaranteed to be major bumps in this project")
    maj, minor, pat = int(match.group("maj")), int(match.group("min")), int(match.group("pat"))
    proposed = None
    if bump == "major":
        proposed = "%d.0.0" % (maj + 1)
    elif bump == "minor":
        proposed = "%d.%d.0" % (maj, minor + 1)
    elif bump == "patch":
        proposed = "%d.%d.%d" % (maj, minor, pat + 1)
    if proposed:
        proposed = match.group("v") + proposed

    sections, breaking, unsorted = {}, [], []
    for entry in live:
        if entry["breaking"]:
            breaking.append({"ref": entry["ref"], "type": entry["type"], "scope": entry["scope"], "text": clean_text(entry), "note": entry["note"], "issues": entry["issues"]})
        elif entry["is_revert"]:
            item = {"ref": entry["ref"], "scope": entry["scope"], "text": clean_text(entry), "issues": entry["issues"]}
            sections.setdefault("Reverted", []).append(item)
        elif entry["type"] is None:
            unsorted.append({"ref": entry["ref"], "subject": entry["subject"], "issues": entry["issues"]})
        else:
            item = {"ref": entry["ref"], "scope": entry["scope"], "text": clean_text(entry), "issues": entry["issues"]}
            if entry.get("rewrite"):
                item["rewrite_flag"] = entry["rewrite"]
            sections.setdefault(TYPE_SECTION[entry["type"]], []).append(item)

    developers = args.audience == "developers"
    omitted = {}
    order = USER_SECTION_ORDER + (DEV_ONLY_SECTIONS if developers else [])
    for name in DEV_ONLY_SECTIONS:
        if not developers and sections.get(name):
            omitted[name] = len(sections[name])
    placeholders = 0

    def line_for(item):
        text = item["text"]
        if item["scope"]:
            text = "**%s:** %s" % (item["scope"], text)
        if item["issues"]:
            text += " (" + ", ".join("#%d" % n for n in item["issues"]) + ")"
        return "- " + text

    out = ["## %s - <release date>" % (proposed or "<version>"), ""]
    if breaking:
        out += ["### Breaking changes", ""]
        for item in breaking:
            out.append(line_for(item))
            if item["note"]:
                out.append("  - Details: " + item["note"])
            out.append("  - Who is affected: [FILL]")
            out.append("  - What to do: [FILL]")
            placeholders += 2
        out.append("")
    for name in order:
        items = sections.get(name)
        if not items:
            continue
        out += ["### " + name, ""]
        for item in items:
            row = line_for(item)
            if item.get("rewrite_flag"):
                row += ' [REWRITE: internal wording "%s"]' % item["rewrite_flag"]
                placeholders += 1
            if name == "Reverted":
                row += " [REWRITE: say what users see again]"
                placeholders += 1
            out.append(row)
        out.append("")
    if unsorted:
        out += ["### Needs a decision", ""]
        for item in unsorted:
            extra = " (" + ", ".join("#%d" % n for n in item["issues"]) + ")" if item["issues"] else ""
            out.append("- [SORT] %s%s" % (item["subject"], extra))
            placeholders += 1
        out.append("")
    skeleton = "\n".join(out).rstrip() + "\n"

    verdict = "ask_user" if ratio > UNTYPED_LIMIT else ("needs_review" if any(w["severity"] == "warn" for w in warnings) else "ok")
    counts = {
        "entries_parsed": len(entries), "entries_kept": len(live), "merges_skipped": merges_skipped,
        "dropped": len(dropped), "breaking": len(breaking), "unsorted": len(unsorted),
        "untyped_share": round(ratio, 4), "placeholders_in_skeleton": placeholders,
        "omitted_from_notes": omitted,
        "by_section": {name: len(items) for name, items in sorted(sections.items())},
    }
    report = {
        "schema_version": SCHEMA_VERSION, "input_format": input_format, "audience": args.audience,
        "current_version": version, "proposed_version": proposed, "bump": bump, "bump_standard": standard,
        "bump_reason": reason, "verdict": verdict, "counts": counts, "sections": sections,
        "breaking": breaking, "unsorted": unsorted, "dropped": dropped, "warnings": warnings,
        "skeleton": skeleton,
    }
    return report


def paths_collide(a, b):
    if os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b)):
        return True
    try:
        return os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b)
    except OSError:
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Commit list or CHANGELOG draft to release-notes skeleton and version bump.")
    parser.add_argument("input")
    parser.add_argument("--current-version", required=True)
    parser.add_argument("--format", choices=["auto", "log", "changelog"], default="auto")
    parser.add_argument("--section", default=None)
    parser.add_argument("--audience", choices=["users", "developers"], default="users")
    parser.add_argument("--markdown-out", default=None)
    parser.add_argument("--force", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    if not VERSION_RE.match(args.current_version):
        return fail_input("--current-version must look like 1.4.2 or v1.4.2 (optionally with -rc.1), got '%s'" % args.current_version)
    if not os.path.isfile(args.input):
        return fail_input("input file not found: %s" % args.input)
    if args.markdown_out:
        if paths_collide(args.markdown_out, args.input):
            return fail_input("--markdown-out resolves to the input file; refusing to overwrite an input")
        if os.path.exists(args.markdown_out) and not args.force:
            return fail_input("--markdown-out exists; pass --force to replace it")
        parent = os.path.dirname(os.path.abspath(args.markdown_out))
        if not os.path.isdir(parent):
            return fail_input("directory for --markdown-out does not exist: %s" % parent)
    try:
        text, note = read_text(args.input)
        fmt = args.format
        if fmt == "auto":
            if re.search(r"(?m)^commit [0-9a-f]{7,40}\b", text):
                fmt = "log"
            elif re.search(r"(?m)^##+\s", text):
                fmt = "changelog"
            else:
                fmt = "log"
        notes = [note] if note else []
        source_section = None
        if fmt == "changelog":
            entries, source_section = parse_changelog(text, args.section)
            merges = 0
        else:
            entries, merges = parse_log(text)
        report = build_report(entries, merges, args, args.current_version, fmt, notes)
        report["source_section"] = source_section
    except (ValueError, OSError) as exc:
        return fail_input(str(exc))
    if args.markdown_out:
        if paths_collide(args.markdown_out, args.input):
            return fail_input("--markdown-out resolves to the input file; refusing to overwrite an input")
        with open(args.markdown_out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(report["skeleton"])
        report["markdown_written"] = args.markdown_out
    emit(report)
    return 0 if report["verdict"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
