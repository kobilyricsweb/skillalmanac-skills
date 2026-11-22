#!/usr/bin/env python3
"""Audit an agent instruction file (AGENTS.md, CLAUDE.md or similar) against its repo.

    python instruction_file_audit.py <instruction-file> [--root <repo-root>] [--json]

Reads the instruction file and looks up paths, manifests and lockfiles under the
repo root (default: the folder containing the instruction file). Writes nothing.

Exit codes: 0 = no finding of level PROBLEM, 1 = at least one PROBLEM,
2 = usage error or unreadable file.

PROBLEM findings are checkable facts (a path or command that does not exist, a
credential-like string). NOTE findings are leads for a human or agent to judge
(vague lines, duplicates, size). The script cannot see contradictions between
two rules or rules that are true but useless; read the file for those.
"""
import json
import os
import re
import sys

# Sizes from tool documentation: about 200 lines is the stated target for an
# always-loaded file; 32 KiB is the default cap one tool applies to the combined
# project instructions, after which text is silently dropped.
TARGET_LINES = 200
HARD_BYTES = 32 * 1024
# More than this many shouted words and the emphasis stops meaning anything.
MAX_EMPHASIS = 5
PATH_EXT = r"(?:md|mdc|txt|json|ya?ml|toml|ini|cfg|lock|js|jsx|mjs|cjs|ts|tsx|py|go|rs|rb|java|kt|swift|php|cs|c|h|cpp|sh|sql|html|css|scss|proto|graphql|tf|prisma)"
INLINE_CODE = re.compile(r"`([^`\n]+)`")
PATHLIKE = re.compile(r"^(?:\./)?[\w.@-]+(?:/[\w.@*-]+)*(?:/|\.%s)$|^(?:\./)?[\w.@-]+(?:/[\w.@-]+)+$" % PATH_EXT)
IMPORT = re.compile(r"(?m)(?:^|\s)@([\w./~-]+\.(?:md|mdc|txt))\b")
NPM_RUN = re.compile(r"\b(npm|pnpm|yarn|bun)\s+(?:run\s+)?([a-z][\w:.-]*)")
MAKE = re.compile(r"\bmake\s+([a-z][\w.-]*)")
PM_BUILTINS = {"install", "i", "ci", "add", "remove", "rm", "update", "up", "run", "exec", "dlx", "x", "init", "publish",
               "link", "why", "outdated", "audit", "create", "store", "config", "login", "version", "pack", "rebuild",
               "prune", "dedupe", "list", "ls", "start", "test", "t", "workspace", "workspaces", "import", "upgrade", "global", "cache"}
LOCKFILES = {"pnpm-lock.yaml": "pnpm", "yarn.lock": "yarn", "package-lock.json": "npm", "bun.lockb": "bun", "bun.lock": "bun"}
SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\b[A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD)\s*[=:]\s*['\"]?[A-Za-z0-9_\-/+]{12,})")
VAGUE = [
    r"\bclean,? (and )?maintainable\b", r"\bhigh[- ]quality\b", r"\bbest practices\b", r"\bbe careful\b", r"\bbe thorough\b",
    r"\bthink step by step\b", r"\bdo not make mistakes\b", r"\bdon't make mistakes\b", r"\bdouble-check your work\b",
    r"\bmeaningful (variable )?names\b", r"\bwrite good\b", r"\byou are an? (expert|senior|world-class)\b", r"\bquality matters\b",
    r"\bkeep (it|functions|things) (small|simple)\b", r"\bfollow (the )?(dry|solid)\b", r"\bis counting on you\b",
    r"\bthink about (edge cases|performance|security|accessibility)\b", r"\bwhen in doubt\b", r"\bwhere appropriate\b",
    r"\b(tests|quality|security) (are|is) important\b", r"\bnever break existing\b",
]
EMPHASIS = re.compile(r"\b(IMPORTANT|ALWAYS|NEVER|MUST|CRITICAL|WARNING)\b|!!+")


def load_scripts(root):
    """Map of directory (relative, '' for root) -> set of package.json script names."""
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "dist", "build", "vendor", ".venv", "__pycache__")]
        if "package.json" in files:
            try:
                data = json.load(open(os.path.join(base, "package.json"), encoding="utf-8"))
                out[os.path.relpath(base, root).replace(os.sep, "/")] = set((data.get("scripts") or {}).keys())
            except (OSError, ValueError):
                pass
        if base.count(os.sep) - root.count(os.sep) >= 4:
            dirs[:] = []
    return out


def make_targets(root):
    path = os.path.join(root, "Makefile")
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8", errors="replace").read()
    return set(re.findall(r"(?m)^([A-Za-z0-9_.-]+)\s*:(?!=)", text)) - {".PHONY"}


def strip_fences(text):
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)


def audit(path, root):
    findings = []

    def add(level, kind, line, msg):
        findings.append({"level": level, "kind": kind, "line": line, "message": msg})

    raw = open(path, encoding="utf-8", errors="replace").read()
    lines = raw.split("\n")
    here = os.path.dirname(os.path.abspath(path))
    scripts = load_scripts(root)
    all_scripts = set().union(*scripts.values()) if scripts else set()
    targets = make_targets(root)
    locks = {pm for lf, pm in LOCKFILES.items() if os.path.isfile(os.path.join(root, lf))}

    seen_paths, seen_cmds = set(), set()
    in_fence = False
    for n, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
        code_spans = INLINE_CODE.findall(line) if not in_fence else [line.strip()]
        for span in code_spans:
            span = span.strip()
            if not in_fence and PATHLIKE.match(span) and "*" not in span and not span.startswith(("http", "@")):
                key = span.rstrip("/")
                if key not in seen_paths:
                    seen_paths.add(key)
                    candidates = [os.path.join(root, key), os.path.join(here, key)]
                    if not any(os.path.exists(c) for c in candidates):
                        add("PROBLEM", "missing-path", n, f"`{span}` does not exist under {os.path.basename(root) or root}")
            for pm, script in NPM_RUN.findall(span):
                explicit_run = re.search(r"\b%s\s+run\s+%s\b" % (pm, re.escape(script)), span) is not None
                if scripts and (explicit_run or script not in PM_BUILTINS) and script not in all_scripts and (pm, script) not in seen_cmds:
                    seen_cmds.add((pm, script))
                    add("PROBLEM", "missing-script", n, f"`{pm} {'run ' if explicit_run else ''}{script}`: no package.json in the repo defines a script named '{script}'")
                if locks and pm not in locks and ("pm", pm) not in seen_cmds:
                    seen_cmds.add(("pm", pm))
                    add("PROBLEM", "wrong-package-manager", n, f"file uses `{pm}` but the lockfile says {', '.join(sorted(locks))}")
            for target in MAKE.findall(span):
                if targets is not None and target not in targets and ("make", target) not in seen_cmds:
                    seen_cmds.add(("make", target))
                    add("PROBLEM", "missing-make-target", n, f"`make {target}`: the Makefile has no such target")
                elif targets is None and ("make", "") not in seen_cmds:
                    seen_cmds.add(("make", ""))
                    add("PROBLEM", "missing-make-target", n, "file uses `make` but there is no Makefile at the repo root")
        if SECRET.search(line):
            add("PROBLEM", "possible-credential", n, "looks like a credential; remove it, rotate it, and do not quote it in replies")

    prose = strip_fences(raw)
    for m in IMPORT.finditer(re.sub(r"`[^`\n]*`", "", prose)):
        target = m.group(1)
        n = prose[:m.start()].count("\n") + 1
        full = os.path.expanduser(target) if target.startswith("~") else os.path.join(here, target)
        if not os.path.isfile(full):
            add("PROBLEM", "missing-import", n, f"import `@{target}` points to a file that does not exist")

    low = [l.lower() for l in lines]
    for n, l in enumerate(low, 1):
        for rx in VAGUE:
            if re.search(rx, l):
                add("NOTE", "vague", n, f"generic line an agent already follows or cannot act on: {lines[n - 1].strip()[:80]}")
                break
    norm = {}
    for n, l in enumerate(low, 1):
        key = re.sub(r"[^a-z0-9 ]", "", l).strip()
        if len(key.split()) >= 4:
            if key in norm:
                add("NOTE", "duplicate", n, f"repeats line {norm[key]}")
            else:
                norm[key] = n
    emph = len(EMPHASIS.findall(prose))
    if emph > MAX_EMPHASIS:
        add("NOTE", "emphasis", 0, f"{emph} emphasis markers (IMPORTANT, ALWAYS, NEVER, !!); keep them for the two or three rules that matter most")
    n_lines, n_bytes = len([l for l in lines if l.strip()]), len(raw.encode("utf-8"))
    if n_bytes > HARD_BYTES:
        add("PROBLEM", "size", 0, f"{n_bytes} bytes: over the 32 KiB default cap of one tool, which drops the rest silently; split into nested files")
    elif n_lines > TARGET_LINES:
        add("NOTE", "size", 0, f"{n_lines} non-blank lines; the documented target for an always-loaded file is under {TARGET_LINES}")
    stats = {"non_blank_lines": n_lines, "bytes": n_bytes, "approx_tokens": n_bytes // 4,
             "paths_checked": len(seen_paths), "package_scripts_known": len(all_scripts),
             "make_targets_known": len(targets) if targets is not None else 0}
    return findings, stats


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args, root, i = [], None, 0
    while i < len(argv):
        if argv[i] == "--root" and i + 1 < len(argv):
            root, i = argv[i + 1], i + 2
        elif argv[i] == "--json":
            i += 1
        elif argv[i].startswith("--"):
            print(__doc__)
            return 2
        else:
            args.append(argv[i])
            i += 1
    if len(args) != 1:
        print(__doc__)
        return 2
    path = args[0]
    if not os.path.isfile(path):
        print(f"cannot read {path}: not a file", file=sys.stderr)
        return 2
    if os.path.getsize(path) == 0:
        print(f"{path} is empty; nothing to audit", file=sys.stderr)
        return 2
    root = os.path.abspath(root or os.path.dirname(os.path.abspath(path)))
    if not os.path.isdir(root):
        print(f"--root {root} is not a folder", file=sys.stderr)
        return 2
    findings, stats = audit(path, root)
    problems = [f for f in findings if f["level"] == "PROBLEM"]
    if "--json" in argv:
        print(json.dumps({"stats": stats, "findings": findings}, indent=2))
    else:
        print(f"{path}: {stats['non_blank_lines']} non-blank lines, {stats['bytes']} bytes, about {stats['approx_tokens']} tokens loaded every session")
        print(f"checked {stats['paths_checked']} paths; knows {stats['package_scripts_known']} package scripts, {stats['make_targets_known']} make targets")
        for f in findings:
            where = f"line {f['line']}" if f["line"] else "file"
            print(f"  {f['level']:7} {f['kind']:22} {where}: {f['message']}")
        notes = len(findings) - len(problems)
        print(f"\n{len(problems)} problem(s), {notes} note(s). Not checked: contradictions between rules, and whether a true rule is worth its line.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
