#!/usr/bin/env python3
"""Audit a folder (or one file) of Markdown docs. Read-only; prints one JSON object.

    python docs_audit.py <folder-or-file> [--max-age-days N] [--today YYYY-MM-DD]
                         [--require-version] [--strict]

Reads every .md, .mdx and .markdown file under the path (skipping .git, node_modules,
vendor, dist, build, site, venv, .venv). Writes nothing, runs nothing, uses no network.

What it checks, per file
    doc-type detection   explicit `doc_type:` or `type:` in a leading front-matter block,
                         else a path hint (README*, a folder named runbooks, how-to,
                         tutorials, reference, explanation), else heading scoring.
    missing-section      required sections for the detected type (see SECTIONS below).
    no-h1                no level-1 title.
    code-no-language     a fenced code block opened without a language tag.
    unclosed-fence       a fence that never closes (everything after it is code).
    broken-link          a relative link or image whose target file or folder is missing
                         or differs only in letter case (case-sensitive hosts break).
    broken-anchor        a link to a heading or id that does not exist in the target .md.
    no-last-verified     a how-to, tutorial, runbook or reference without a
                         "Last verified: YYYY-MM-DD" line.
    bad-verified-date    a "Last verified" line with no valid ISO date.
    future-verified-date a verified date later than today.
    stale-verified       a verified date older than --max-age-days.
    verified-no-version  only with --require-version: date without "against <version>".
    secret-in-doc        a key-shaped string (cloud key, private-key header, API token)
                         anywhere in the file, code blocks included. File CONTENTS are read.
    bad-encoding         the file is not valid UTF-8 (read with replacement characters).

Exit codes: 0 no error-severity findings (and no warnings when --strict is given);
1 findings at the failing severity; 2 usage error or unreadable path.

JSON contract (schema_version 1), always printed on exit 0 or 1:
    {"schema_version": 1, "command": "audit", "root": str, "today": "YYYY-MM-DD",
     "max_age_days": int, "files_scanned": int,
     "files": [{"path": str, "doc_type": str, "detected_by": str, "findings": [
         {"rule": str, "severity": "error"|"warning", "line": int, "message": str}]}],
     "summary": {"findings": int, "errors": int, "warnings": int,
                 "by_rule": {rule: int}, "by_type": {doc_type: int}},
     "ok": bool}
doc_type is one of readme, reference, how-to, tutorial, explanation, runbook, unknown.
detected_by is front-matter, path, headings or none. Paths use forward slashes and are
relative to the audited folder. Files and findings are sorted, so output is stable.
"""
import argparse
import datetime
import json
import os
import re
import sys

SCHEMA_VERSION = 1

# A review-and-test cycle for ops-facing docs is a quarter; longer than that and the
# commands, versions and screenshots in a how-to are more likely wrong than right.
DEFAULT_MAX_AGE_DAYS = 90

# Heading scoring needs a clear winner: at least two matching signals and strictly more
# than the runner-up. A wrong type produces false "missing section" errors, so unknown
# (no section check) is the safer outcome when evidence is thin.
MIN_SCORE = 2
TITLE_BONUS = 2

# A README intro (text between the title and the first sub-heading) of this many words
# counts as the "what it is" section even without its own heading.
INTRO_MIN_WORDS = 12

# Three or more ordered-list items count as a steps section when no heading names it.
MIN_STEP_ITEMS = 3

DOC_EXTS = (".md", ".mdx", ".markdown")
SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "site", "venv", ".venv", "__pycache__"}
TYPES = ("readme", "reference", "how-to", "tutorial", "explanation", "runbook")
NEEDS_VERIFIED = {"reference", "how-to", "tutorial", "runbook"}

# Required sections per type: (name, heading regex, alternative evidence).
# A section is present when any level 2-6 heading matches the regex, or the alternative holds.
SECTIONS = {
    "readme": [
        ("what-it-is", r"overview|about|what is|introduction|description|why", "intro"),
        ("install", r"install|getting started|setup|set up|requirements|prerequisites", None),
        ("usage", r"usage|quick ?start|example|how to use|getting started", None),
        ("license", r"licen[sc]e", None),
    ],
    "reference": [
        ("parameters-or-endpoints", r"parameters|arguments|options|endpoints?|methods|operations|routes|fields|schema|properties|commands|functions|classes|api", None),
        ("errors", r"errors?|error codes|status codes|exceptions|failure", None),
        ("examples", r"examples?|sample|request|usage", None),
    ],
    "how-to": [
        ("prerequisites", r"prerequisites?|before you (begin|start)|requirements|what you need", None),
        ("steps", r"^steps$|procedure|instructions|^how to", "steps"),
        ("verify", r"verify|verification|check that|confirm|expected (result|output)|test it", None),
    ],
    "tutorial": [
        ("goal", r"what you(.?ll| will) (build|learn|make)|what we.?ll|overview|goal|objectives?|introduction", None),
        ("prerequisites", r"prerequisites?|before you (begin|start)|requirements|what you need", None),
        ("steps", r"^steps$|step \d|part \d|^\d+[.)]? ", "steps"),
        ("result", r"result|what you (learned|built)|summary|recap|next steps|wrap.?up|conclusion", None),
    ],
    "explanation": [
        ("context", r"background|context|overview|introduction|why|problem|motivation", None),
        ("how-it-works", r"how it works|design|architecture|concepts?|model|mechanism|internals|approach", None),
        ("trade-offs", r"trade-?offs?|alternatives|limitations|drawbacks|when not|consequences|caveats", None),
    ],
    "runbook": [
        ("when-to-use", r"when to use|symptoms?|trigger|alert|purpose|scope|impact|overview", None),
        ("steps", r"^steps$|procedure|mitigation|diagnosis|resolution|remediation|response|instructions", "steps"),
        ("verify", r"verify|verification|recovery check|confirm|validate|success criteria", None),
        ("rollback", r"roll ?back|revert|undo|abort", None),
        ("escalation", r"escalat|contacts?|on-?call|owner|who to (call|ask)|support", None),
    ],
}

# Wording to suggest when a required section is missing.
SECTION_HINT = {
    "what-it-is": "'Overview' or an intro paragraph under the title",
    "install": "'Install' or 'Getting started'",
    "usage": "'Usage' or 'Quick start'",
    "license": "'License'",
    "parameters-or-endpoints": "'Endpoints', 'Parameters' or 'Methods'",
    "errors": "'Errors' or 'Status codes'",
    "examples": "'Examples'",
    "prerequisites": "'Prerequisites'",
    "steps": "'Steps' or an ordered list of 3 or more items",
    "verify": "'Verify' or 'Expected result'",
    "goal": "'What you will build' or 'Overview'",
    "result": "'Summary' or 'Next steps'",
    "context": "'Background' or 'Why'",
    "how-it-works": "'How it works' or 'Design'",
    "trade-offs": "'Trade-offs' or 'Alternatives'",
    "when-to-use": "'Symptoms' or 'When to use'",
    "rollback": "'Rollback'",
    "escalation": "'Escalation' or 'Contacts'",
}

# Heading signals used to score an unlabelled file. Several headings can match one
# regex; each heading counts once per type.
SIGNALS = {
    "readme": r"install|licen[sc]e|contributing|badges|features|getting started",
    "reference": r"endpoints?|parameters|returns|request|response|status codes|errors?|authentication|options|methods|schema|api",
    "how-to": r"prerequisites?|before you (begin|start)|verify|troubleshooting|^steps$|rollback",
    "tutorial": r"what you(.?ll| will) (build|learn)|what we.?ll|learning objectives|next steps|step \d|part \d",
    "explanation": r"background|concepts?|how it works|why |trade-?offs?|alternatives|architecture|rationale|design",
    "runbook": r"roll ?back|escalat|on-?call|symptoms?|mitigation|alert|incident|severity|when to use|recovery",
}
TITLE_SIGNALS = {
    "how-to": r"^how to |^(configure|set up|add|migrate|deploy|rotate|enable|create|upgrade|install|connect|restore) ",
    "tutorial": r"tutorial|getting started with|build (a|an|your) ",
    "reference": r"reference|\bapi\b|cli commands|configuration options",
    "runbook": r"runbook|playbook|incident|on-?call",
    "explanation": r"^(why|understanding|about|architecture|how .* works)",
    "readme": r"$^",
}
PATH_HINTS = [
    ("runbook", r"(^|/)(runbooks?|playbooks?)(/|$)|runbook"),
    ("tutorial", r"(^|/)tutorials?(/|$)|(^|/)tutorial[-_]"),
    ("how-to", r"(^|/)(how-?tos?|how_to)(/|$)|(^|/)how-?to[-_]"),
    ("reference", r"(^|/)references?(/|$)|api-reference|(^|/)reference[-_]"),
    ("explanation", r"(^|/)(explanations?|concepts?|architecture)(/|$)"),
]

# Key-shaped strings. Matched against file contents, never file names. Strings ending in
# EXAMPLE are the placeholders vendors publish for documentation and are allowed.
SECRET_PATTERNS = [
    ("cloud access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("API secret key (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{40,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
]

FENCE_RE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
ATX_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
OLIST_RE = re.compile(r"^\s*\d+[.)]\s+\S")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
LINK_RE = re.compile(r"\]\(\s*(<[^>\n]+>|[^\s)]+)")
REFDEF_RE = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(<[^>\n]+>|\S+)")
HTML_REF_RE = re.compile(r"""\b(?:href|src)=["']([^"']+)["']""", re.I)
ID_RE = re.compile(r"""\b(?:id|name)=["']([^"']+)["']""", re.I)
VERIFIED_RE = re.compile(r"last[ _-]?verified\W{0,8}(?P<rest>.*)$", re.I)
ISO_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
VERSION_RE = re.compile(r"against\s+\S+|\bv?\d+\.\d+(\.\d+)?\b", re.I)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def unquote(text):
    """Decode %XX escapes (UTF-8) without importing a URL library."""
    raw = re.sub(r"(?:%[0-9a-fA-F]{2})+", lambda m: bytes.fromhex(m.group(0).replace("%", "")).decode("utf-8", "replace"), text)
    return raw


def clean_heading(text):
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_]", "", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def slugify(text):
    """GitHub-style heading anchor, before duplicate suffixes."""
    text = clean_heading(text)
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def parse_doc(text):
    """Split text into structure. Lines inside front matter and fences are not prose."""
    lines = text.splitlines()
    front = {}
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 60)):
            if lines[i].strip() in ("---", "..."):
                for raw in lines[1:i]:
                    m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
                    if m:
                        front[m.group(1).lower()] = m.group(2).strip().strip("\"'")
                start = i + 1
                break
    prose = []          # (line number, text) outside code
    fences = []         # {"line", "lang"}
    fence = None        # (char, length, line, lang)
    unclosed = None
    for idx in range(start, len(lines)):
        line = lines[idx]
        no = idx + 1
        m = FENCE_RE.match(line)
        if fence is None:
            if m:
                info = m.group(3).strip()
                if m.group(2)[0] == "`" and "`" in info:
                    prose.append((no, line))
                    continue
                fence = (m.group(2)[0], len(m.group(2)), no, info)
                fences.append({"line": no, "lang": info.split()[0] if info else ""})
            else:
                prose.append((no, line))
        else:
            if m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and not m.group(3).strip():
                fence = None
    if fence is not None:
        unclosed = fence[2]
    return {"lines": lines, "front": front, "prose": prose, "fences": fences, "unclosed": unclosed}


def find_headings(prose):
    headings = []
    prev = None
    for no, line in prose:
        m = ATX_RE.match(line)
        if m:
            headings.append((len(m.group(1)), no, m.group(2)))
            prev = None
            continue
        s = SETEXT_RE.match(line)
        if s and prev is not None and prev[1].strip() and not OLIST_RE.match(prev[1]) \
                and not prev[1].lstrip().startswith(("-", "*", "+", ">", "|")):
            headings.append((1 if s.group(1)[0] == "=" else 2, prev[0], prev[1].strip()))
            prev = None
            continue
        prev = (no, line)
    return headings


def anchors_of(headings, prose):
    seen = {}
    out = set()
    for _level, _no, text in headings:
        slug = slugify(text)
        n = seen.get(slug, 0)
        out.add(slug if n == 0 else "%s-%d" % (slug, n))
        seen[slug] = n + 1
    for _no, line in prose:
        for m in ID_RE.finditer(line):
            out.add(m.group(1).lower())
    return out


def detect_type(rel_path, front, headings):
    declared = (front.get("doc_type") or front.get("type") or "").lower().replace("_", "-")
    declared = {"howto": "how-to", "api": "reference", "api-reference": "reference", "guide": "how-to"}.get(declared, declared)
    if declared in TYPES:
        return declared, "front-matter"
    low = rel_path.lower()
    stem = os.path.splitext(os.path.basename(low))[0]
    if stem == "readme":
        return "readme", "path"
    for typ, pat in PATH_HINTS:
        if re.search(pat, low):
            return typ, "path"
    h2 = [clean_heading(t) for lvl, _n, t in headings if lvl >= 2]
    title = next((clean_heading(t) for lvl, _n, t in headings if lvl == 1), "")
    scores = {}
    for typ in TYPES:
        score = sum(1 for h in h2 if re.search(SIGNALS[typ], h))
        if title and re.search(TITLE_SIGNALS[typ], title):
            score += TITLE_BONUS
        scores[typ] = score
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    best, second = ranked[0], ranked[1]
    if best[1] >= MIN_SCORE and best[1] > second[1]:
        return best[0], "headings"
    return "unknown", "none"


def exact_resolve(base_dir, rel):
    """Walk rel from base_dir with case-exact names. Returns (path, None) or (None, reason)."""
    cur = base_dir
    for part in rel.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            cur = os.path.dirname(cur)
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return None, "missing"
        if part in names:
            cur = os.path.join(cur, part)
            continue
        for n in names:
            if n.lower() == part.lower():
                return None, "case:" + n
        return None, "missing"
    return cur, None


def link_targets(prose):
    """Yield (line, raw target) for links, images, reference definitions, href and src."""
    for no, line in prose:
        stripped = INLINE_CODE_RE.sub(" ", line)
        found = []
        m = REFDEF_RE.match(stripped)
        if m:
            found.append(m.group(1))
        found += [m.group(1) for m in LINK_RE.finditer(stripped)]
        found += [m.group(1) for m in HTML_REF_RE.finditer(stripped)]
        for raw in found:
            yield no, raw.strip("<>")


def audit_file(abs_path, rel_path, root_dir, today, max_age, require_version, cache):
    with open(abs_path, "rb") as fh:
        data = fh.read()
    findings = []

    def add(rule, severity, line, message):
        findings.append({"rule": rule, "severity": severity, "line": line, "message": message})

    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("utf-8", errors="replace")
        add("bad-encoding", "warning", 1, "File is not valid UTF-8; re-save it as UTF-8 so links and headings read correctly.")
    doc = parse_doc(text)
    headings = find_headings(doc["prose"])
    doc_type, by = detect_type(rel_path, doc["front"], headings)
    cache[abs_path] = anchors_of(headings, doc["prose"])

    # Title
    if not any(lvl == 1 for lvl, _n, _t in headings):
        add("no-h1", "warning", 1, "No level-1 title. Start the file with one '# Title' that names the task or the thing.")

    # Required sections
    if doc_type in SECTIONS:
        h_text = [clean_heading(t) for lvl, _n, t in headings if lvl >= 2]
        h1_no = next((n for lvl, n, _t in headings if lvl == 1), 0)
        first_sub = next((n for lvl, n, _t in headings if lvl >= 2), 10 ** 9)
        ordered = sum(1 for _n, l in doc["prose"] if OLIST_RE.match(l))
        intro_words = 0
        if h1_no:
            for no, line in doc["prose"]:
                if h1_no < no < first_sub and not ATX_RE.match(line):
                    intro_words += len(line.split())
        for name, pat, alt in SECTIONS[doc_type]:
            ok = any(re.search(pat, h) for h in h_text)
            if not ok and alt == "steps" and ordered >= MIN_STEP_ITEMS:
                ok = True
            if not ok and alt == "intro" and intro_words >= INTRO_MIN_WORDS:
                ok = True
            if not ok:
                add("missing-section", "error", 1, "%s needs a '%s' section; add a heading worded like: %s." % (doc_type, name, SECTION_HINT[name]))

    # Code fences
    for f in doc["fences"]:
        if not f["lang"]:
            add("code-no-language", "warning", f["line"], "Code block has no language tag; open it with ```bash, ```json, ```text or similar.")
    if doc["unclosed"]:
        add("unclosed-fence", "error", doc["unclosed"], "Code fence opened here is never closed; everything after it renders as code.")

    # Links
    base_dir = os.path.dirname(abs_path)
    for no, raw in link_targets(doc["prose"]):
        if not raw or SCHEME_RE.match(raw) or raw.startswith("//") or "{{" in raw or "{%" in raw or "${" in raw:
            continue
        path_part, _, frag = raw.partition("#")
        path_part = unquote(path_part.split("?", 1)[0])
        frag = unquote(frag).lower()
        if path_part == "":
            if frag and frag not in cache[abs_path] and frag != "top":
                add("broken-anchor", "warning", no, "Anchor '#%s' matches no heading or id in this file." % frag)
            continue
        if path_part.startswith("/"):
            target, why = exact_resolve(root_dir, path_part.lstrip("/"))
        else:
            target, why = exact_resolve(base_dir, path_part)
        if target is None:
            if why and why.startswith("case:"):
                add("broken-link", "error", no, "Link '%s' differs only in letter case from '%s'; fix the case, hosts like GitHub and Linux are case-sensitive." % (raw, why[5:]))
            else:
                add("broken-link", "error", no, "Link target '%s' does not exist relative to this file; fix the path or remove the link." % path_part)
            continue
        if frag and os.path.isfile(target) and target.lower().endswith(DOC_EXTS):
            if target not in cache:
                try:
                    with open(target, "rb") as fh:
                        sub = parse_doc(fh.read().decode("utf-8", errors="replace"))
                    cache[target] = anchors_of(find_headings(sub["prose"]), sub["prose"])
                except OSError:
                    cache[target] = None
            if cache[target] is not None and frag not in cache[target]:
                add("broken-anchor", "warning", no, "Anchor '#%s' matches no heading or id in %s." % (frag, path_part))

    # Last verified
    verified = None
    for no, line in doc["prose"]:
        m = VERIFIED_RE.search(line)
        if m:
            verified = (no, m.group("rest"))
            break
    if verified is None:
        if doc_type in NEEDS_VERIFIED:
            add("no-last-verified", "warning", 1, "%s has no 'Last verified: YYYY-MM-DD against <version>' line; run its commands, then add one." % doc_type)
    else:
        no, rest = verified
        m = ISO_RE.search(rest)
        when = None
        if m:
            try:
                when = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                when = None
        if when is None:
            add("bad-verified-date", "error", no, "'Last verified' needs an ISO date such as 2026-11-21; found '%s'." % rest.strip()[:40])
        else:
            age = (today - when).days
            if age < 0:
                add("future-verified-date", "error", no, "Verified date %s is in the future; record the day the commands were actually run." % when.isoformat())
            elif age > max_age:
                add("stale-verified", "warning", no, "Last verified %d days ago (limit %d); re-run the commands and update the date." % (age, max_age))
            if require_version and not VERSION_RE.search(rest[m.end():] if m else rest):
                add("verified-no-version", "warning", no, "Add what it was verified against, e.g. 'against v2.3.1'.")

    # Secrets: all lines, fences included
    for idx, line in enumerate(doc["lines"]):
        for label, rx in SECRET_PATTERNS:
            for m in rx.finditer(line):
                value = m.group(0)
                if value.upper().endswith("EXAMPLE"):
                    continue
                add("secret-in-doc", "error", idx + 1, "Looks like a %s (%s***); revoke it if real and replace it with a placeholder such as <YOUR_TOKEN>." % (label, value[:4]))

    findings.sort(key=lambda f: (f["line"], f["rule"], f["message"]))
    return {"path": rel_path, "doc_type": doc_type, "detected_by": by, "findings": findings}


def collect(root):
    if os.path.isfile(root):
        return os.path.dirname(os.path.abspath(root)), [os.path.abspath(root)]
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.lower().endswith(DOC_EXTS):
                out.append(os.path.abspath(os.path.join(dirpath, name)))
    return os.path.abspath(root), out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit a folder of Markdown docs; prints JSON.")
    ap.add_argument("path")
    ap.add_argument("--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS)
    ap.add_argument("--today", help="YYYY-MM-DD; defaults to the local date")
    ap.add_argument("--require-version", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    args = ap.parse_args(argv)
    if args.max_age_days < 0:
        print("--max-age-days must be 0 or more.", file=sys.stderr)
        return 2
    try:
        today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    except ValueError:
        print("--today must look like 2026-11-21.", file=sys.stderr)
        return 2
    if not os.path.exists(args.path):
        print("Path not found: %s" % args.path, file=sys.stderr)
        return 2
    root_dir, files = collect(args.path)
    if not files:
        print("No .md, .mdx or .markdown files under %s." % args.path, file=sys.stderr)
        return 2
    cache = {}
    results = []
    for abs_path in files:
        rel = os.path.relpath(abs_path, root_dir).replace(os.sep, "/")
        try:
            results.append(audit_file(abs_path, rel, root_dir, today, args.max_age_days, args.require_version, cache))
        except OSError as exc:
            print("Cannot read %s: %s" % (abs_path, exc.strerror), file=sys.stderr)
            return 2
    results.sort(key=lambda r: r["path"])
    by_rule, by_type = {}, {}
    errors = warnings = 0
    for r in results:
        for f in r["findings"]:
            by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
            by_type[r["doc_type"]] = by_type.get(r["doc_type"], 0) + 1
            if f["severity"] == "error":
                errors += 1
            else:
                warnings += 1
    ok = errors == 0 and (warnings == 0 or not args.strict)
    report = {
        "schema_version": SCHEMA_VERSION, "command": "audit", "root": os.path.basename(root_dir) or root_dir,
        "today": today.isoformat(), "max_age_days": args.max_age_days, "files_scanned": len(results),
        "files": results,
        "summary": {"findings": errors + warnings, "errors": errors, "warnings": warnings,
                    "by_rule": dict(sorted(by_rule.items())), "by_type": dict(sorted(by_type.items()))},
        "ok": ok,
    }
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=False, allow_nan=False) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
