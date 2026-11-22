#!/usr/bin/env python3
"""vault_scan.py - read-only audit of a Markdown notes vault (Obsidian-style).

Usage:
    python vault_scan.py scan <vault_dir> [--exclude GLOB ...] [--max-items N]
    python vault_scan.py validate-plan <vault_dir> <plan.json>

scan
    Walks <vault_dir>, reads every .md file and prints ONE strict JSON document
    (schema_version "1") on stdout: broken and ambiguous links, orphan notes,
    duplicate titles, duplicate content, tag spelling variants, notes without
    frontmatter, and a proposed move plan. Nothing is written, renamed, moved or
    deleted: files are only opened for reading, and the move plan is a proposal.
    "tree_sha256" fingerprints the vault (note content plus attachment names and
    sizes), so a second scan proves that nothing changed.

validate-plan
    Checks a move plan (the scan output, or any JSON with a "moves" list of
    {"from": ..., "to": ...}) against the vault before a human applies it:
    sources exist, destinations are free, paths stay inside the vault, no
    duplicates, no action other than a move.

Skipped by default: folders whose name starts with "." (such as .obsidian, .git,
.trash), node_modules, and files whose name starts with ".". --exclude takes
glob patterns matched against the vault-relative path, case-insensitively.

Exit codes: 0 done (scan) or plan valid; 1 plan has problems; 2 usage or input
error (message on stderr). Python 3.9+, standard library only, no network.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import posixpath
import re
import sys
from difflib import get_close_matches

SCHEMA_VERSION = "1"
NOTE_EXT = ".md"
SKIP_DIRS = {"node_modules"}
MAX_BYTES = 2000000       # a note larger than this is listed as unreadable, not parsed
MAX_NOTES = 50000         # guard against pointing the scan at a whole disk
DEFAULT_MAX_ITEMS = 200   # per-list cap so the JSON stays readable in a chat
STUB_WORDS = 15           # an orphan this short with no tags and no links is a stub
SUGGEST_CUTOFF = 0.8      # difflib ratio for "did you mean" on a broken link
REVIEW_DIR = "_review"    # holding area for proposed moves; never a deletion

WIKI = re.compile(r"(!?)\[\[([^\[\]\n]+?)\]\]")
MDLINK = re.compile(r"(!?)\[[^\]\n]*\]\(([^)\n]+)\)")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_TAG = re.compile(r"(?<!\S)#([\w\-/]+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
DRIVE = re.compile(r"^[A-Za-z]:")
FM_KEY = re.compile(r"^([A-Za-z0-9_\- ]+):\s*(.*)$")


# ---------------------------------------------------------------- reading

def read_note(path):
    """Return (text, sha256_of_bytes) or raise OSError / ValueError."""
    with open(path, "rb") as fh:
        raw = fh.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("larger than %d bytes" % MAX_BYTES)
    text = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    return text, hashlib.sha256(raw).hexdigest()


def excluded(rel, patterns):
    low = rel.casefold()
    return any(fnmatch.fnmatchcase(low, p.casefold()) for p in patterns)


def walk_vault(vault, patterns):
    notes, attachments = [], []
    for root, dirs, files in os.walk(vault, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
        for name in sorted(files):
            if name.startswith("."):
                continue
            rel = os.path.relpath(os.path.join(root, name), vault).replace(os.sep, "/")
            if excluded(rel, patterns):
                continue
            (notes if name.casefold().endswith(NOTE_EXT) else attachments).append(rel)
            if len(notes) > MAX_NOTES:
                raise ValueError("more than %d notes; point the scan at a smaller folder" % MAX_NOTES)
    return notes, attachments


# ---------------------------------------------------------------- parsing

def split_frontmatter(text):
    """Return (lines_or_None, body_start_line_index, reason). reason: ok|none|unclosed."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 0, "none"
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return lines[1:i], i + 1, "ok"
    return None, 0, "unclosed"


def _clean(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def parse_frontmatter(fm_lines):
    """Tiny YAML subset: top-level 'key: value', 'key: [a, b]' and block lists."""
    data, key = {}, None
    for raw in fm_lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = FM_KEY.match(raw)
        if m and not raw[0].isspace():
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            if val == "":
                data[key] = []
            elif val.startswith("[") and val.endswith("]"):
                data[key] = [_clean(x) for x in val[1:-1].split(",") if _clean(x)]
            else:
                data[key] = _clean(val)
        else:
            s = raw.strip()
            if key is not None and (s.startswith("- ") or s == "-"):
                if not isinstance(data.get(key), list):
                    data[key] = []
                item = _clean(s[1:])
                if item:
                    data[key].append(item)
    return data


def fm_list(data, keys, split_on_space):
    out = []
    for k in keys:
        v = data.get(k)
        if isinstance(v, str):
            v = [v]
        for item in v or []:
            parts = re.split(r"[,\s]+" if split_on_space else r",", item)
            out.extend(p.strip().lstrip("#").strip() for p in parts if p.strip().lstrip("#").strip())
    return out


def _blank(m):
    return "".join(c if c == "\n" else " " for c in m.group(0))


def mask(text):
    """Blank out fenced code, inline code, %%comments%% and HTML comments, keeping line numbers."""
    out, fence = [], None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            out.append("")
        elif m:
            fence = m.group(1)
            out.append("")
        else:
            out.append(line)
    t = "\n".join(out)
    t = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), t)
    t = re.sub(r"%%.*?%%", _blank, t, flags=re.S)
    return re.sub(r"<!--.*?-->", _blank, t, flags=re.S)


def singular(word):
    """Crude English singular used only to group tag spellings."""
    if word in {"news", "series", "species", "status"} or len(word) <= 3:
        return word
    if word.endswith(("ss", "us", "is")):
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("sses", "shes", "ches", "xes", "zes")):
        return word[:-2]
    return word[:-1] if word.endswith("s") else word


def tag_key(tag):
    segs = tag.casefold().split("/")
    return "/".join(singular(re.sub(r"[-_ ]", "", s)) for s in segs)


def unquote(text):
    """Decode %XX escapes (UTF-8) in a Markdown link target, e.g. %20 for a space."""
    if "%" not in text:
        return text
    raw = re.sub(rb"%([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), text.encode("utf-8"))
    return raw.decode("utf-8", errors="replace")


def stem_of(rel):
    name = rel.rsplit("/", 1)[-1]
    return name[:-len(NOTE_EXT)] if name.casefold().endswith(NOTE_EXT) else name


# ---------------------------------------------------------------- scan

def build_index(notes, attachments, info):
    idx = {"noext": {}, "stem": {}, "alias": {}, "att_path": {}, "att_name": {}}
    for rel in notes:
        idx["noext"][rel[:-len(NOTE_EXT)].casefold()] = rel
        idx["stem"].setdefault(stem_of(rel).casefold(), []).append(rel)
        for alias in info[rel]["aliases"]:
            idx["alias"].setdefault(alias.casefold(), []).append(rel)
    for rel in attachments:
        idx["att_path"][rel.casefold()] = rel
        idx["att_name"].setdefault(rel.rsplit("/", 1)[-1].casefold(), []).append(rel)
    return idx


def resolve_wiki(target, idx):
    t = target.replace("\\", "/").strip().strip("/").casefold()
    base = t[:-len(NOTE_EXT)] if t.endswith(NOTE_EXT) else t
    if "/" in base:
        cands = [rel for key, rel in idx["noext"].items() if key == base or key.endswith("/" + base)]
    else:
        cands = list(idx["stem"].get(base, [])) or list(idx["alias"].get(base, []))
    if cands:
        return "note", sorted(set(cands))
    if "/" in t:
        files = [rel for key, rel in idx["att_path"].items() if key == t or key.endswith("/" + t)]
    else:
        files = idx["att_name"].get(t, [])
    return ("file", sorted(files)) if files else ("none", [])


def resolve_md(target, source, idx):
    """Resolve a [text](path) link relative to the source note, then from the vault root."""
    folder = posixpath.dirname(source)
    rooted = target.startswith("/")
    tries = [target.lstrip("/")] if rooted else [posixpath.join(folder, target), target]
    for cand in tries:
        t = posixpath.normpath(cand)
        if t.startswith(".."):
            continue
        low = t.casefold()
        if low in idx["att_path"]:
            return "file", [idx["att_path"][low]]
        key = low[:-len(NOTE_EXT)] if low.endswith(NOTE_EXT) else low
        if key in idx["noext"]:
            return "note", [idx["noext"][key]]
    return "none", []


def scan(vault, patterns, max_items):
    notes, attachments = walk_vault(vault, patterns)
    if not notes:
        raise ValueError("no .md notes found under " + vault)
    info, unreadable, tree = {}, [], hashlib.sha256()
    for rel in notes:
        try:
            text, digest = read_note(os.path.join(vault, rel))
        except (OSError, ValueError) as exc:
            unreadable.append({"path": rel, "reason": str(exc)})
            tree.update(("N %s unreadable\n" % rel).encode("utf-8"))
            continue
        tree.update(("N %s %s\n" % (rel, digest)).encode("utf-8"))
        fm_lines, body_at, reason = split_frontmatter(text)
        data = parse_frontmatter(fm_lines) if fm_lines else {}
        masked = mask(text)
        body_lines = masked.split("\n")
        inline_tags = sorted({m.group(1).rstrip("/-") for m in INLINE_TAG.finditer("\n".join(body_lines[body_at:]))
                              if re.search(r"[^\W\d]", m.group(1))}, key=str.casefold)
        title = data.get("title") if isinstance(data.get("title"), str) else ""
        norm = "\n".join(l.rstrip() for l in text.split("\n")).strip()
        info[rel] = {
            "text": text, "masked": masked, "data": data, "fm_reason": reason,
            "fm_empty": reason == "ok" and not data,
            "tags": list(dict.fromkeys(fm_list(data, ("tags", "tag"), True) + inline_tags)),
            "aliases": fm_list(data, ("aliases", "alias"), False),
            "title": " ".join((title or stem_of(rel)).casefold().split()),
            "words": len(re.findall(r"\w+", "\n".join(text.split("\n")[body_at:]))),
            "content_hash": hashlib.sha256(norm.encode("utf-8")).hexdigest() if norm else "",
        }
    for rel in attachments:
        try:
            size = os.path.getsize(os.path.join(vault, rel))
        except OSError:
            size = -1
        tree.update(("A %s %d\n" % (rel, size)).encode("utf-8"))
    parsed = [r for r in notes if r in info]
    idx = build_index(parsed, attachments, info)
    stems = sorted(idx["stem"])

    broken, ambiguous = [], []
    inbound = {r: set() for r in parsed}
    path_inbound = {r: 0 for r in parsed}
    outbound = {r: 0 for r in parsed}
    for rel in parsed:
        text = info[rel]["masked"]
        found = []
        for m in WIKI.finditer(text):
            inner = m.group(2).replace("\\|", "|")
            target = inner.split("|", 1)[0].split("#", 1)[0].strip()
            if target:
                found.append((m.start(), "embed" if m.group(1) else "wikilink", target))
        for m in MDLINK.finditer(text):
            raw = m.group(2).strip()
            raw = raw[1:raw.find(">")] if raw.startswith("<") and ">" in raw else raw.split()[0] if raw else ""
            raw = unquote(re.split(r"[#?]", raw, 1)[0])
            if raw and not SCHEME.match(raw) and not DRIVE.match(raw) and not raw.startswith("//"):
                found.append((m.start(), "markdown", raw))
        for pos, kind, target in sorted(found):
            outbound[rel] += 1
            line = text.count("\n", 0, pos) + 1
            if kind == "markdown":
                status, cands = resolve_md(target, rel, idx)
            else:
                status, cands = resolve_wiki(target, idx)
            by_path = kind == "markdown" or "/" in target
            if status == "none":
                sugg = []
                if kind != "markdown" and "/" not in target:
                    sugg = [idx["stem"][s][0] for s in get_close_matches(target.casefold(), stems, n=3, cutoff=SUGGEST_CUTOFF)]
                broken.append({"source": rel, "line": line, "kind": kind, "target": target, "suggestions": sugg})
            elif status == "note":
                if len(cands) > 1:
                    ambiguous.append({"source": rel, "line": line, "target": target, "candidates": cands})
                for c in cands:
                    if c != rel:
                        inbound[c].add(rel)
                        path_inbound[c] += 1 if by_path else 0

    orphans = [{"path": r, "outbound_links": outbound[r], "tags": len(info[r]["tags"]), "words": info[r]["words"],
                "has_frontmatter": bool(info[r]["data"])} for r in parsed if not inbound[r]]

    groups = {}
    for r in parsed:
        groups.setdefault(info[r]["title"], []).append(r)
    dup_titles = []
    for title, paths in sorted(groups.items()):
        if len(paths) > 1:
            stem_counts = {}
            for p in paths:
                stem_counts[stem_of(p).casefold()] = stem_counts.get(stem_of(p).casefold(), 0) + 1
            dup_titles.append({"title": title, "paths": sorted(paths),
                               "same_filename": any(c > 1 for c in stem_counts.values())})

    by_hash = {}
    for r in parsed:
        if info[r]["content_hash"]:
            by_hash.setdefault(info[r]["content_hash"], []).append(r)
    dup_content = [{"sha256": h[:16], "paths": sorted(p)} for h, p in sorted(by_hash.items()) if len(p) > 1]

    usage = {}
    for r in parsed:
        for t in info[r]["tags"]:
            usage.setdefault(t, set()).add(r)
    by_key = {}
    for t, users in usage.items():
        by_key.setdefault(tag_key(t), []).append(t)
    tag_variants = []
    for key, variants in sorted(by_key.items()):
        if len(variants) < 2:
            continue
        best = sorted(variants, key=lambda t: (-len(usage[t]), t != t.casefold(), len(t), t))[0]
        rows = []
        for t in sorted(variants, key=lambda t: (-len(usage[t]), t)):
            kind = "case" if t.casefold() == best.casefold() else \
                "separator" if re.sub(r"[-_ ]", "", t.casefold()) == re.sub(r"[-_ ]", "", best.casefold()) else "plural"
            rows.append({"tag": t, "notes": len(usage[t]), "difference": "suggested" if t == best else kind})
        tag_variants.append({"key": key, "suggested": best, "variants": rows})

    missing = [{"path": r, "reason": "unclosed" if info[r]["fm_reason"] == "unclosed" else
                "empty" if info[r]["fm_empty"] else "none"}
               for r in parsed if not info[r]["data"]]

    plan = build_plan(parsed, info, inbound, path_inbound, orphans, outbound, notes, attachments, dup_content)

    def cap(name, rows, trunc):
        if len(rows) > max_items:
            trunc[name] = len(rows) - max_items
        return rows[:max_items]

    trunc = {}
    return {
        "schema_version": SCHEMA_VERSION, "command": "scan", "read_only": True,
        "vault": os.path.abspath(vault).replace(os.sep, "/"),
        "tree_sha256": tree.hexdigest(),
        "counts": {"notes": len(notes), "attachments": len(attachments), "broken_links": len(broken),
                   "ambiguous_links": len(ambiguous), "orphans": len(orphans),
                   "duplicate_title_groups": len(dup_titles), "duplicate_content_groups": len(dup_content),
                   "tag_variant_groups": len(tag_variants), "missing_frontmatter": len(missing),
                   "planned_moves": len(plan["moves"]), "skipped_moves": len(plan["skipped"]),
                   "unreadable": len(unreadable)},
        "broken_links": cap("broken_links", broken, trunc),
        "ambiguous_links": cap("ambiguous_links", ambiguous, trunc),
        "orphans": cap("orphans", orphans, trunc),
        "duplicate_titles": cap("duplicate_titles", dup_titles, trunc),
        "duplicate_content": cap("duplicate_content", dup_content, trunc),
        "tag_variants": cap("tag_variants", tag_variants, trunc),
        "missing_frontmatter": cap("missing_frontmatter", missing, trunc),
        "unreadable": cap("unreadable", unreadable, trunc),
        "move_plan": plan,
        "truncated": trunc,
    }


def build_plan(parsed, info, inbound, path_inbound, orphans, outbound, notes, attachments, dup_content):
    """Propose moves only. Order of rules decides which rule claims a note first."""
    taken = {p.casefold() for p in notes + attachments}
    planned, moves, skipped = set(), [], []

    def propose(rel, folder, rule, confidence, reason):
        if rel in planned:
            return
        dest = folder + "/" + rel.rsplit("/", 1)[-1]
        if dest.casefold() in taken:
            skipped.append({"from": rel, "rule": rule, "reason": "destination exists: " + dest})
            return
        taken.add(dest.casefold())
        planned.add(rel)
        moves.append({"id": "", "from": rel, "to": dest, "rule": rule, "confidence": confidence,
                      "reason": reason, "path_links_affected": path_inbound.get(rel, 0)})

    kept = set()
    for group in dup_content:
        paths = group["paths"]
        keep = sorted(paths, key=lambda r: (-len(inbound[r]), len(r), r.casefold()))[0]
        kept.add(keep)
        for rel in paths:
            if rel != keep:
                propose(rel, REVIEW_DIR + "/duplicates", "duplicate-content", "high",
                        "identical content to " + keep + " (kept: more inbound links, then shorter path)")
    for o in orphans:
        rel = o["path"]
        if (o["words"] < STUB_WORDS and o["tags"] == 0 and o["outbound_links"] == 0
                and not rel.startswith(REVIEW_DIR + "/") and rel not in kept):
            propose(rel, REVIEW_DIR + "/stubs", "stub-orphan", "medium",
                    "no inbound links, no outbound links, no tags, %d words" % o["words"])
    folders = {}
    for rel in parsed:
        if "/" in rel:
            top = rel.split("/", 1)[0]
            if not top.startswith("_"):
                folders.setdefault(tag_key(top), set()).add(top)
    for rel in parsed:
        if "/" in rel or rel in planned:
            continue
        cands = []
        typ = info[rel]["data"].get("type")
        for source, value in ([("type", typ)] if isinstance(typ, str) and typ else []) + \
                [("tag", t) for t in info[rel]["tags"]]:
            hit = folders.get(tag_key(value.split("/")[0]))
            if hit:
                cands.append((source, value, hit))
        names = {f for _, _, hit in cands for f in hit}
        if len(names) == 1:
            source, value, _ = cands[0]
            propose(rel, sorted(names)[0], "tag-folder", "medium",
                    "root note whose %s '%s' matches folder '%s'" % (source, value, sorted(names)[0]))
        elif len(names) > 1:
            skipped.append({"from": rel, "rule": "tag-folder", "reason": "tags point to several folders: " + ", ".join(sorted(names))})
    order = {"duplicate-content": 0, "stub-orphan": 1, "tag-folder": 2}
    moves.sort(key=lambda m: (order[m["rule"]], m["from"].casefold()))
    for i, m in enumerate(moves, 1):
        m["id"] = "m%d" % i
    return {"dry_run": True, "applied": False, "moves": moves, "skipped": skipped}


# ---------------------------------------------------------------- validate-plan

def validate_plan(vault, plan_path):
    try:
        with open(plan_path, "rb") as fh:
            plan = json.loads(fh.read().decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ValueError("cannot read plan %s: %s" % (plan_path, exc))
    moves = plan.get("move_plan", {}).get("moves") if isinstance(plan, dict) and "move_plan" in plan else \
        plan.get("moves") if isinstance(plan, dict) else None
    if not isinstance(moves, list):
        raise ValueError('plan needs a "moves" list (or a scan output with move_plan.moves)')
    notes, attachments = walk_vault(vault, [])
    exact = set(notes + attachments)
    lower = {p.casefold() for p in exact}
    problems, seen_from, seen_to = [], set(), set()

    def bad(code, i, detail):
        problems.append({"code": code, "index": i, "detail": detail})

    def unsafe(p):
        if not isinstance(p, str) or not p.strip():
            return "empty or not a string"
        if "\\" in p:
            return "use forward slashes"
        if p.startswith("/") or DRIVE.match(p):
            return "absolute path"
        parts = p.split("/")
        if ".." in parts or "." in parts or "" in parts:
            return "path escapes or is not normalised"
        if any(s.startswith(".") for s in parts):
            return "hidden folder or file"
        return ""

    for i, mv in enumerate(moves):
        if not isinstance(mv, dict):
            bad("not-an-object", i, "move must be an object with from and to")
            continue
        action = mv.get("action", "move")
        if action != "move":
            bad("forbidden-action", i, "only moves are allowed, got %r" % (action,))
        src, dst = mv.get("from"), mv.get("to")
        problem = unsafe(src) or None
        if problem:
            bad("unsafe-source", i, "%s: %r" % (problem, src))
            continue
        problem = unsafe(dst) or None
        if problem:
            bad("unsafe-destination", i, "%s: %r" % (problem, dst))
            continue
        if src not in exact:
            bad("source-missing", i, "no such file in the vault: " + src)
        if not src.casefold().endswith(NOTE_EXT) or not dst.casefold().endswith(NOTE_EXT):
            bad("not-a-note", i, "only %s files may be moved" % NOTE_EXT)
        if src.casefold() == dst.casefold():
            bad("noop", i, "source and destination are the same")
        elif dst.casefold() in lower:
            bad("destination-exists", i, "already in the vault: " + dst)
        if src in seen_from:
            bad("duplicate-source", i, "moved twice: " + src)
        if dst.casefold() in seen_to:
            bad("duplicate-destination", i, "two notes to one path: " + dst)
        seen_from.add(src)
        seen_to.add(dst.casefold())
    return {"schema_version": SCHEMA_VERSION, "command": "validate-plan", "ok": not problems,
            "moves_checked": len(moves), "problems": problems}


# ---------------------------------------------------------------- cli

def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(prog="vault_scan.py", description="Read-only audit of a Markdown notes vault.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("vault")
    s.add_argument("--exclude", action="append", default=[], metavar="GLOB")
    s.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS)
    v = sub.add_parser("validate-plan")
    v.add_argument("vault")
    v.add_argument("plan")
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    if not os.path.isdir(args.vault):
        print("vault_scan.py: not a folder: " + args.vault, file=sys.stderr)
        return 2
    try:
        if args.cmd == "scan":
            report = scan(args.vault, args.exclude, max(1, args.max_items))
            code = 0
        else:
            report = validate_plan(args.vault, args.plan)
            code = 0 if report["ok"] else 1
    except ValueError as exc:
        print("vault_scan.py: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
