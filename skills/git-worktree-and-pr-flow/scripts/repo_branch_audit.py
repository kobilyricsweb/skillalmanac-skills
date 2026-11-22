#!/usr/bin/env python3
"""Audit a repository's branches and linked worktrees by reading .git files only.

    python scripts/repo_branch_audit.py <repo-or-git-dir> [--stale-worktree-days N]
        [--stale-branch-days N] [--types a,b,c] [--trunk a,b,c] [--now EPOCH]

Reads (never writes, never runs git): HEAD, config, packed-refs, refs/heads/**,
refs/remotes/**, logs/HEAD and logs/refs/heads/** (reflog timestamps),
worktrees/<id>/{gitdir,HEAD,locked,logs/HEAD}, and the marker files of an
operation in progress (rebase-merge, MERGE_HEAD, index.lock and similar).
It cannot know whether a branch is merged: that needs the object database.

<repo-or-git-dir> is a working tree root (its .git directory or .git pointer file
is followed) or a git directory itself (a folder holding HEAD and refs/).

Output: one JSON object on stdout (schema in SKILL.md). UTF-8 on every platform.
Exit codes: 0 no error or warn findings, 1 at least one error or warn finding,
2 usage error or not a repository.
"""
import argparse
import json
import os
import re
import sys
import time

DAY = 86400
# A worktree whose HEAD reflog has not moved for 14 days is usually a finished or
# abandoned agent task: long enough to skip a weekend plus a sick day.
STALE_WORKTREE_DAYS = 14
# Branches live longer than worktrees (review waits); 30 days is where a rebase
# onto the trunk usually stops being trivial.
STALE_BRANCH_DAYS = 30
# A local branch never pushed is normal for the first days of a task; after 3 days
# it is a single disk failure away from being lost work.
UNPUSHED_GRACE_DAYS = 3
# Git removes its own lock files in milliseconds; one older than 10 minutes belongs
# to a crashed process.
STALE_LOCK_SECONDS = 600
# Total branch name length cap: keeps names readable in `git branch` and PR lists.
MAX_NAME_LENGTH = 50
# Slug (the part after type/) cap.
MAX_SLUG_LENGTH = 40
# Safety cap on refs read from one repository.
MAX_REFS = 50000

DEFAULT_TYPES = ["feat", "fix", "chore", "docs", "refactor", "test", "perf", "ci", "build", "hotfix", "release"]
DEFAULT_TRUNK = ["main", "master", "develop", "development", "trunk", "prod", "production", "staging"]
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}([0-9a-f]{24})?$")
REFLOG_TS_RE = re.compile(r"\s(\d{9,11}) [+-]\d{4}\t")
OPERATION_MARKERS = ["rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "BISECT_LOG"]
LOCK_FILES = ["index.lock", "HEAD.lock", "packed-refs.lock", "config.lock", "shallow.lock"]


def read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def mtime(path):
    try:
        return os.stat(path).st_mtime
    except OSError:
        return None


def resolve_git_dirs(target):
    """Return (git_dir, common_dir) for a work tree root or a git directory."""
    target = os.path.abspath(target)
    candidate = os.path.join(target, ".git")
    if os.path.isfile(candidate):
        text = read_text(candidate) or ""
        match = re.match(r"gitdir:\s*(.+)", text.strip())
        if not match:
            return None, None
        git_dir = match.group(1).strip()
        if not os.path.isabs(git_dir):
            git_dir = os.path.normpath(os.path.join(target, git_dir))
    elif os.path.isdir(candidate):
        git_dir = candidate
    elif os.path.isfile(os.path.join(target, "HEAD")) and os.path.isdir(os.path.join(target, "refs")):
        git_dir = target
    else:
        return None, None
    common = git_dir
    common_text = read_text(os.path.join(git_dir, "commondir"))
    if common_text:
        common = common_text.strip()
        if not os.path.isabs(common):
            common = os.path.normpath(os.path.join(git_dir, common))
    return git_dir, common


def parse_head(text):
    """Return ('branch', name) or ('detached', sha) or ('unknown', '')."""
    if text is None:
        return "unknown", ""
    text = text.strip()
    if text.startswith("ref:"):
        ref = text[4:].strip()
        if ref.startswith("refs/heads/"):
            return "branch", ref[len("refs/heads/"):]
        return "other-ref", ref
    if SHA_RE.match(text):
        return "detached", text
    return "unknown", ""


def read_refs(common, findings, now):
    """Return (heads, remotes): dicts name -> {sha, source, ref_path}."""
    heads, remotes = {}, {}
    packed = read_text(os.path.join(common, "packed-refs")) or ""
    for line in packed.splitlines():
        line = line.strip()
        if not line or line[0] in "#^":
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2 or not SHA_RE.match(parts[0]):
            continue
        sha, ref = parts
        if ref.startswith("refs/heads/"):
            heads[ref[len("refs/heads/"):]] = {"sha": sha, "source": "packed", "ref_path": None}
        elif ref.startswith("refs/remotes/"):
            remotes[ref[len("refs/remotes/"):]] = {"sha": sha, "source": "packed", "ref_path": None}
    seen = 0
    for kind, bucket in (("heads", heads), ("remotes", remotes)):
        base = os.path.join(common, "refs", kind)
        for dirpath, _dirs, files in os.walk(base):
            for name in files:
                seen += 1
                if seen > MAX_REFS:
                    findings.append(finding("warn", "ref_limit", "refs", f"stopped reading after {MAX_REFS} loose refs"))
                    return heads, remotes
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, base).replace(os.sep, "/")
                if rel.endswith(".lock"):
                    age = now - (mtime(full) or now)
                    if age > STALE_LOCK_SECONDS:
                        findings.append(finding("warn", "stale_lock", f"refs/{kind}/{rel}", "lock file older than 10 minutes; remove it only after confirming no git process runs"))
                    continue
                text = (read_text(full) or "").strip()
                if text.startswith("ref:"):
                    continue  # symbolic ref such as origin/HEAD
                if not SHA_RE.match(text):
                    findings.append(finding("error", "invalid_ref_file", f"refs/{kind}/{rel}", "ref file does not hold a 40 or 64 digit hex id"))
                    continue
                bucket[rel] = {"sha": text, "source": "loose", "ref_path": full}
    return heads, remotes


def read_branch_config(common):
    """Return {branch: {'remote': str|None, 'merge': str|None}} from the config file."""
    config = {}
    text = read_text(os.path.join(common, "config")) or ""
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        header = re.match(r'^\[\s*branch\s+"(.*)"\s*\]$', line, re.I)
        if header:
            current = header.group(1).replace('\\"', '"').replace("\\\\", "\\")
            config.setdefault(current, {"remote": None, "merge": None})
            continue
        if line.startswith("["):
            current = None
            continue
        if current is None or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        key = key.lower()
        if key in ("remote", "merge"):
            config[current][key] = value
    return config


def last_reflog_epoch(path):
    text = read_text(path)
    if not text:
        return None
    for line in reversed(text.splitlines()):
        match = REFLOG_TS_RE.search(line + "\t") if "\t" not in line else REFLOG_TS_RE.search(line)
        if match:
            return int(match.group(1))
    return None


def finding(severity, code, subject, detail):
    return {"severity": severity, "code": code, "subject": subject, "detail": detail}


def naming_problems(name, types, trunk):
    """Return a list of reason codes; empty means the name follows the contract."""
    if name in trunk:
        return []
    problems = []
    if len(name) > MAX_NAME_LENGTH:
        problems.append(f"longer than {MAX_NAME_LENGTH} characters")
    if name != name.lower():
        problems.append("contains uppercase")
    if re.search(r"[^A-Za-z0-9._/-]", name):
        problems.append("contains characters outside a-z 0-9 . _ - /")
    if "/" not in name:
        problems.append("no type prefix (expected <type>/<slug>)")
        return problems
    head, _, slug = name.partition("/")
    if head.lower() not in types:
        problems.append(f"type '{head}' not in {','.join(types)}")
    if "/" in slug:
        problems.append("more than one slash")
    if slug and not SLUG_RE.match(slug.lower().replace("/", "-")):
        problems.append("slug must start with a letter or digit")
    if len(slug) > MAX_SLUG_LENGTH:
        problems.append(f"slug longer than {MAX_SLUG_LENGTH} characters")
    if not slug:
        problems.append("empty slug")
    if name.endswith((".", ".lock", "/")) or ".." in name or "//" in name:
        problems.append("ends with a dot, .lock or slash, or has .. or //")
    return problems


def worktree_path_from_gitdir_file(wt_dir):
    text = read_text(os.path.join(wt_dir, "gitdir"))
    if text is None:
        return None
    pointer = text.strip().splitlines()[0] if text.strip() else ""
    if not pointer:
        return None
    if not os.path.isabs(pointer):
        pointer = os.path.normpath(os.path.join(wt_dir, pointer))
    return pointer  # path of <worktree>/.git


def operation_findings(git_dir, label, findings, now):
    for marker in OPERATION_MARKERS:
        if os.path.exists(os.path.join(git_dir, marker)):
            findings.append(finding("warn", "operation_in_progress", label, f"{marker} present: finish or abort that operation before anything else"))
    for lock in LOCK_FILES:
        path = os.path.join(git_dir, lock)
        stamp = mtime(path)
        if stamp is not None and now - stamp > STALE_LOCK_SECONDS:
            findings.append(finding("warn", "stale_lock", label, f"{lock} is {int((now - stamp) // 60)} minutes old"))


def audit(target, args):
    git_dir, common = resolve_git_dirs(target)
    if not git_dir or not os.path.isdir(common):
        return None
    now = args.now if args.now is not None else time.time()
    types = [t.strip().lower() for t in args.types.split(",") if t.strip()]
    trunk = [t.strip() for t in args.trunk.split(",") if t.strip()]
    findings = []
    heads, remotes = read_refs(common, findings, now)
    config = read_branch_config(common)
    if re.search(r"refstorage\s*=\s*reftable", read_text(os.path.join(common, "config")) or "", re.I):
        findings.append(finding("warn", "reftable_unsupported", "refs", "repository uses reftable ref storage; branches and worktree refs cannot be read from files, use git commands"))

    # worktrees: the primary one plus every entry under worktrees/
    worktrees = []
    primary_path = os.path.dirname(common) if os.path.basename(common) == ".git" else None
    head_kind, head_value = parse_head(read_text(os.path.join(common, "HEAD")))
    worktrees.append({"id": "(primary)", "path": primary_path.replace(os.sep, "/") if primary_path else None, "exists": primary_path is not None and os.path.isdir(primary_path),
                      "head_kind": head_kind, "head": head_value, "locked": False, "lock_reason": None, "age_days": None})
    operation_findings(common, "(primary)", findings, now)
    wt_root = os.path.join(common, "worktrees")
    if os.path.isdir(wt_root):
        for wt_id in sorted(os.listdir(wt_root)):
            wt_dir = os.path.join(wt_root, wt_id)
            if not os.path.isdir(wt_dir):
                continue
            git_file = worktree_path_from_gitdir_file(wt_dir)
            wt_path = os.path.dirname(git_file).replace(os.sep, "/") if git_file else None
            exists = git_file is not None and os.path.exists(git_file)
            kind, value = parse_head(read_text(os.path.join(wt_dir, "HEAD")))
            lock_text = read_text(os.path.join(wt_dir, "locked"))
            locked = lock_text is not None
            stamp = last_reflog_epoch(os.path.join(wt_dir, "logs", "HEAD"))
            if stamp is None:
                stamp = mtime(os.path.join(wt_dir, "HEAD"))
            age = round((now - stamp) / DAY, 1) if stamp else None
            worktrees.append({"id": wt_id, "path": wt_path, "exists": exists, "head_kind": kind, "head": value,
                              "locked": locked, "lock_reason": (lock_text or "").strip() or None, "age_days": age})
            if git_file is None:
                findings.append(finding("error", "worktree_metadata_broken", wt_id, "worktrees/%s/gitdir is missing or empty" % wt_id))
            elif not exists and not locked:
                findings.append(finding("error", "stale_worktree", wt_id, f"checkout directory {wt_path} is gone; `git worktree prune` removes the record"))
            elif not exists and locked:
                findings.append(finding("warn", "locked_worktree_missing", wt_id, f"locked ({(lock_text or '').strip() or 'no reason'}) and its directory {wt_path} is gone; unlock before pruning"))
            elif age is not None and age > args.stale_worktree_days:
                findings.append(finding("warn", "idle_worktree", wt_id, f"HEAD has not moved for {age} days (limit {args.stale_worktree_days})"))
            if kind == "detached":
                findings.append(finding("warn", "detached_worktree", wt_id, "HEAD is detached: commits made here belong to no branch"))
            if kind == "branch" and value not in heads:
                findings.append(finding("warn", "worktree_branch_missing", wt_id, f"HEAD points to refs/heads/{value}, which does not exist (deleted or unborn)"))
            operation_findings(wt_dir, wt_id, findings, now)

    checked_out = {}
    for wt in worktrees:
        if wt["head_kind"] == "branch":
            checked_out.setdefault(wt["head"], []).append(wt["id"])

    branches = []
    for name in sorted(heads):
        info = heads[name]
        stamp = last_reflog_epoch(os.path.join(common, "logs", "refs", "heads", *name.split("/")))
        if stamp is None and info["ref_path"]:
            stamp = mtime(info["ref_path"])
        age = round((now - stamp) / DAY, 1) if stamp else None
        conf = config.get(name, {"remote": None, "merge": None})
        has_upstream = bool(conf["remote"] and conf["merge"])
        upstream_exists = None
        upstream = None
        if has_upstream:
            merge = conf["merge"]
            short = merge[len("refs/heads/"):] if merge.startswith("refs/heads/") else merge
            upstream = f"{conf['remote']}/{short}"
            upstream_exists = upstream in remotes if conf["remote"] != "." else short in heads
        branches.append({"name": name, "source": info["source"], "sha": info["sha"], "upstream": upstream,
                         "upstream_ref_exists": upstream_exists, "age_days": age, "checked_out_in": checked_out.get(name, [])})
        is_trunk = name in trunk
        problems = naming_problems(name, types, trunk)
        if problems:
            findings.append(finding("warn", "naming_violation", name, "; ".join(problems)))
        if not is_trunk and not has_upstream:
            old = age is not None and age > UNPUSHED_GRACE_DAYS
            findings.append(finding("warn" if old else "info", "no_upstream", name,
                                    "no tracking branch configured" + (f"; local-only for {age} days" if old else "")))
        if has_upstream and upstream_exists is False:
            findings.append(finding("warn", "upstream_gone", name, f"tracks {upstream}, which no longer exists (merged and deleted, or never fetched)"))
        if not is_trunk and age is not None and age > args.stale_branch_days:
            findings.append(finding("warn", "stale_branch", name, f"last update {age} days ago (limit {args.stale_branch_days})"))

    counts = {"error": 0, "warn": 0, "info": 0}
    for item in findings:
        counts[item["severity"]] += 1
    order = {"error": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: (order[f["severity"]], f["code"], f["subject"]))
    return {
        "tool": "repo_branch_audit", "schema_version": 1,
        "git_dir": git_dir.replace(os.sep, "/"), "common_dir": common.replace(os.sep, "/"),
        "policy": {"types": types, "trunk": trunk, "max_name_length": MAX_NAME_LENGTH, "max_slug_length": MAX_SLUG_LENGTH,
                   "stale_worktree_days": args.stale_worktree_days, "stale_branch_days": args.stale_branch_days,
                   "unpushed_grace_days": UNPUSHED_GRACE_DAYS},
        "now": int(now),
        "worktrees": worktrees, "branches": branches,
        "remote_branch_count": len(remotes),
        "findings": findings, "counts": counts,
        "ok": counts["error"] == 0 and counts["warn"] == 0,
        "not_checked": ["whether any branch is merged", "uncommitted changes in worktrees", "commit contents and message format"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Read-only audit of branches and worktrees from .git files.")
    parser.add_argument("repo", help="work tree root or git directory")
    parser.add_argument("--stale-worktree-days", type=float, default=STALE_WORKTREE_DAYS)
    parser.add_argument("--stale-branch-days", type=float, default=STALE_BRANCH_DAYS)
    parser.add_argument("--types", default=",".join(DEFAULT_TYPES), help="allowed branch types, comma separated")
    parser.add_argument("--trunk", default=",".join(DEFAULT_TRUNK), help="long-lived branch names exempt from naming")
    parser.add_argument("--now", type=float, default=None, help="epoch seconds to use as the current time (tests)")
    return parser


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    report = audit(args.repo, args)
    if report is None:
        print(f"error: {args.repo} is not a git work tree or git directory (no .git, or HEAD and refs/ missing)", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
