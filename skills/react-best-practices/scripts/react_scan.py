#!/usr/bin/env python3
"""Heuristic scanner for common React defects in .jsx/.tsx/.js/.ts files (standard library only).

Usage:
    python react_scan.py src/ [more paths ...] [--json]

Reads the files or folders named (skips node_modules, build output and tests'
snapshots). Writes nothing. No network. It is a pattern scanner, not a parser:
every finding is a lead to confirm by reading the code, and a clean run does not
prove the code is correct.

    FAIL  a pattern that is a bug in nearly every case
    WARN  a pattern that is often a bug or a cost; judge it in context

Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage or read error.
"""
import bisect
import json
import os
import re
import sys

EXTS = (".jsx", ".tsx", ".js", ".ts", ".mjs")
SKIP_DIRS = {"node_modules", "dist", "build", ".next", "out", "coverage", ".git", "__snapshots__"}
MAX_FILE_BYTES = 400_000    # larger files are generated bundles, not source
MUTATORS = "push|pop|shift|unshift|splice|sort|reverse|fill|copyWithin"
SUBSCRIPTIONS = r"addEventListener\(|setInterval\(|\.subscribe\(|new WebSocket\(|new EventSource\(|new (Intersection|Resize|Mutation)Observer\(|\.on\(\s*['\"]"
CANCEL_HINTS = r"AbortController|signal\b|\bignore\b|cancell?ed|\bactive\b|\bstale\b|didCancel|isMounted|isCurrent|\bcurrent\s*=\s*false"
CONTROL = re.compile(r"^(if|else|for|while|switch|do|try|catch|finally)\b")


def blank(src):
    """Return src with comments and string contents replaced by spaces (same length, same lines)."""
    out, i, n = list(src), 0, len(src)
    while i < n:
        c = src[i]
        two = src[i:i + 2]
        if two == "//":
            j = src.find("\n", i)
            j = n if j == -1 else j
            out[i:j] = " " * (j - i)
            i = j
        elif two == "/*":
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out[i:j] = [ch if ch == "\n" else " " for ch in src[i:j]]
            i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            if j < n and src[j] == c:
                out[i + 1:j] = " " * (j - i - 1)
                i = j + 1
            else:
                i += 1  # an apostrophe in JSX text, not a string
        elif c == "`":
            j = i + 1
            while j < n and src[j] != "`":
                j += 2 if src[j] == "\\" else 1
            out[i + 1:j] = [ch if ch == "\n" else " " for ch in src[i + 1:j]]
            i = j + 1
        else:
            i += 1
    return "".join(out)


def match_close(code, i, open_ch, close_ch):
    """Index of the bracket that closes code[i]; -1 if unbalanced."""
    depth = 0
    for j in range(i, len(code)):
        if code[j] == open_ch:
            depth += 1
        elif code[j] == close_ch:
            depth -= 1
            if depth == 0:
                return j
    return -1


def split_args(text):
    """Split a call's argument text on top-level commas."""
    args, depth, cur = [], 0, []
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            args.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        args.append("".join(cur))
    return args


DECL = re.compile(r"(?:^|\n)[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\s+([A-Za-z_$][\w$]*)\s*(?:<[^>(]*>)?\s*\(|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*(?:React\.)?(?:memo\(|forwardRef(?:<[^>]*>)?\()?\s*(?:async\s+)?(?:function\s*\w*\s*)?(?:<[^>(]*>\s*)?\()")


def find_units(code):
    """Components (Capitalised) and custom hooks (useX) with the span of their body."""
    units = []
    for m in DECL.finditer(code):
        name = m.group(1) or m.group(2)
        if not (name[0].isupper() or re.match(r"use[A-Z]", name)):
            continue
        close = match_close(code, m.end() - 1, "(", ")")
        if close == -1:
            continue
        k = close + 1
        tail = re.match(r"\s*(?::\s*[^={]+?)?\s*(=>)?\s*", code[k:k + 200])
        k += tail.end() if tail else 0
        if k < len(code) and code[k] == "{":
            end = match_close(code, k, "{", "}")
        elif k < len(code) and code[k] == "(":
            end = match_close(code, k, "(", ")")
        else:
            end = code.find("\n", k)
        if end == -1:
            continue
        units.append({"name": name, "start": m.start(1 if m.group(1) else 2), "body": k, "end": end, "hook": not name[0].isupper()})
    return units


def block_map(code, start, end):
    """For each brace inside [start, end): (position, stack of block kinds after it)."""
    marks, stack = [], []
    seg_start = start + 1
    for i in range(start + 1, end):
        ch = code[i]
        if ch == "{":
            seg = code[seg_start:i].strip()
            last = re.split(r"[;{}]", seg)[-1].strip() if seg else ""
            if CONTROL.match(last) or re.search(r"\)\s*$", last) and re.match(r"(if|for|while|switch|catch)\b", last):
                kind = "control"
            elif re.search(r"=>\s*$|\bfunction\b[^)]*\)\s*$|\)\s*$", last) and not last.endswith("=") and ("=>" in last or "function" in last):
                kind = "function"
            else:
                kind = "other"
            stack.append(kind)
            marks.append((i, tuple(stack)))
            seg_start = i + 1
        elif ch == "}":
            if stack:
                stack.pop()
            marks.append((i, tuple(stack)))
            seg_start = i + 1
        elif ch == ";":
            seg_start = i + 1
    return marks


def stack_at(marks, pos):
    idx = bisect.bisect_right([p for p, _ in marks], pos) - 1
    return marks[idx][1] if idx >= 0 else ()


def scan_file(path, add):
    with open(path, encoding="utf-8", errors="replace") as fh:
        src = fh.read()
    code = blank(src)
    line_of = lambda pos: code.count("\n", 0, pos) + 1
    lines = src.split("\n")

    def hit(level, code_, pos, msg, fix):
        ln = line_of(pos)
        add(level, code_, path, ln, msg, fix, lines[ln - 1].strip()[:110] if ln <= len(lines) else "")

    units = find_units(code)
    client = re.match(r"\s*['\"]use client['\"]", src) is not None

    # ---- file-level patterns ----
    for m in re.finditer(r"key=\{\s*(index|idx|i|ix|n)\s*\}", code):
        hit("WARN", "key-index", m.start(), "array index used as key", "Use a stable id from the data. Index keys keep the wrong state and DOM when the list is reordered, filtered or prepended.")
    for m in re.finditer(r"key=\{[^}\n]*(Math\.random|Date\.now|uuid|nanoid|randomUUID)\s*\(", code):
        hit("FAIL", "key-unstable", m.start(), "key is generated during render", "Generate the id once when the item is created and store it with the item; a new key every render remounts the item and drops its state.")
    for m in re.finditer(r"\.map\(\s*(?:\([^)]*\)|[\w$]+)\s*=>\s*\(?\s*<(>|[A-Za-z][\w.]*)([^>]*)", code):
        tag, attrs = m.group(1), m.group(2)
        if tag == ">":
            hit("FAIL", "key-missing", m.start(), "list renders a keyless fragment", "Use <Fragment key={id}> for a list of fragments.")
        elif "key=" not in attrs and "{..." not in attrs:
            hit("WARN", "key-missing", m.start(), f"<{tag}> returned from map has no key", "Add key with a stable id on the outermost element returned by the callback.")
    for m in re.finditer(r"\{\s*((?:[\w$.?]+\.)?length|[\w$.]*[cC]ount|[\w$.]*[tT]otal|[\w$.]*\.size)\s*&&\s*[<(]", code):
        hit("FAIL", "and-renders-zero", m.start(), f"`{m.group(1)} &&` renders the text 0 when the number is zero", "Compare explicitly: `x.length > 0 && ...`, or use a ternary.")
    for m in re.finditer(r"<[A-Za-z][\w.]*(?:\.Provider)?\s+value=\{\{", code):
        if "Provider" in m.group(0) or "Context" in m.group(0):
            hit("WARN", "context-inline-value", m.start(), "context value is a new object on every render", "Memoise the value (useMemo) or split state and dispatch into two contexts; otherwise every consumer re-renders each time.")
    for m in re.finditer(r"dangerouslySetInnerHTML", code):
        hit("WARN", "raw-html", m.start(), "raw HTML injection", "Render as text or sanitise with a vetted sanitiser first; state in the review where the HTML comes from.")
    for m in re.finditer(r"<img\b([^>]*)>", code):
        if "alt=" not in m.group(1) and "{..." not in m.group(1):
            hit("WARN", "img-alt", m.start(), "<img> without alt", 'Add alt text, or alt="" for decoration.')
    for m in re.finditer(r"<(div|span|li|td|p|section|article|img)\b([^>]*)\bonClick=", code):
        rest = code[m.start():code.find(">", m.end()) + 1 if code.find(">", m.end()) != -1 else m.end()]
        if "role=" not in rest or "tabIndex" not in rest:
            hit("WARN", "click-on-nonbutton", m.start(), f"<{m.group(1)}> with onClick is not keyboard accessible", "Use <button type=\"button\">, or add role, tabIndex and key handling.")
    for m in re.finditer(r"\b(componentWillMount|componentWillReceiveProps|componentWillUpdate|findDOMNode|UNSAFE_\w+)\b", code):
        hit("WARN", "legacy-api", m.start(), f"{m.group(1)} is a legacy API", "Replace it; these are removed or unsafe in current React.")
    for m in re.finditer(r"import\s+(?:\w+|\*\s+as\s+\w+)\s+from\s+['\"]", code):
        mod = re.match(r"['\"]([^'\"]+)", src[m.end() - 1:])
        if mod and mod.group(1) in ("lodash", "moment", "rxjs", "date-fns", "@mui/icons-material", "react-icons"):
            hit("WARN", "heavy-import", m.start(), f"whole-library import of {mod.group(1)}", "Import the specific function or path so the bundler can drop the rest.")
    if client:
        for m in re.finditer(r"(?:export\s+default\s+)?async\s+function\s+([A-Z]\w*)", code):
            hit("FAIL", "async-client-component", m.start(), f"{m.group(1)} is an async component in a client file", "Client components cannot be async; fetch in a server component or with a data hook.")

    # ---- per component / hook ----
    for u in units:
        body = code[u["body"]:u["end"] + 1]
        base = u["body"]
        marks = block_map(code, u["body"], u["end"]) if code[u["body"]] == "{" else []
        for other in units:
            if other is not u and u["body"] < other["start"] < u["end"] and not other["hook"] and not u["hook"]:
                hit("FAIL", "nested-component", other["start"], f"component {other['name']} is defined inside {u['name']}",
                    "Move it to module scope and pass what it needs as props; a nested definition is a new component type every render, so its subtree remounts and loses state.")
        states = {m.group(1): m.group(2) for m in re.finditer(r"\[\s*([\w$]+)\s*,\s*(set[A-Z][\w$]*)\s*\]\s*=\s*(?:React\.)?useState", body)}
        early_returns = [base + m.start() for m in re.finditer(r"\breturn\b", body) if "function" not in stack_at(marks, base + m.start())]
        last_return = max(early_returns) if early_returns else None

        after_return = []
        for m in re.finditer(r"(?<![\w$.])(use[A-Z][\w$]*)\s*(?:<[^>()]*>)?\(", body):
            pos = base + m.start()
            st = stack_at(marks, pos)
            if "control" in st:
                hit("FAIL", "hook-conditional", pos, f"{m.group(1)} is called inside a condition or loop", "Call hooks at the top level of the component, in the same order every render; move the condition inside the hook.")
            elif "function" in st:
                hit("FAIL", "hook-in-callback", pos, f"{m.group(1)} is called inside a nested function", "Call hooks only at the top level of a component or custom hook.")
            elif any(r < pos for r in early_returns if r != last_return) and not st:
                after_return.append((pos, m.group(1)))
            prefix = code[code.rfind("\n", 0, pos) + 1:pos]
            if re.search(r"(&&|\|\||\?)\s*$", prefix):
                hit("FAIL", "hook-conditional", pos, f"{m.group(1)} is called conditionally in an expression", "Call the hook unconditionally and use its result conditionally.")

        if after_return:
            more = f" (and {len(after_return) - 1} more hook call(s) below it)" if len(after_return) > 1 else ""
            hit("FAIL", "hook-after-return", after_return[0][0], f"{after_return[0][1]} is called after an early return{more}", "Move every hook above the first return.")
        for name, setter in states.items():
            for m in re.finditer(rf"(?<![\w$.]){re.escape(name)}\.({MUTATORS})\(", body):
                hit("FAIL", "state-mutation", base + m.start(), f"state `{name}` is mutated with .{m.group(1)}()",
                    f"Build a new value: {setter}(prev => [...prev, item]), prev.filter(...), prev.map(...), or copy first ([...{name}].sort(...), or toSorted()).")
            for m in re.finditer(rf"(?<![\w$.]){re.escape(name)}((?:\.[\w$]+|\[[^\]\n]+\])+)\s*(?:=(?!=)|\+=|-=|\+\+|--)", body):
                hit("FAIL", "state-mutation", base + m.start(), f"state `{name}` is assigned in place ({name}{m.group(1)})", f"Create a copy with the change and pass it to {setter}.")
            for m in re.finditer(rf"(?<![\w$.]){setter}\(", body):
                pos = base + m.start()
                prefix = code[code.rfind("\n", 0, pos) + 1:pos]
                if not stack_at(marks, pos) and not prefix.strip() and marks:
                    hit("FAIL", "set-state-in-render", pos, f"{setter} is called during render", "Set state in an event handler or effect, or derive the value during render instead of storing it.")

        for m in re.finditer(r"(?<![\w$.])useState\(\s*((?:JSON\.parse|localStorage\.getItem|sessionStorage\.getItem|[\w$.]*(?:compute|create|build|load|read|parse|generate|init)[\w$]*)\s*\()", body, re.I):
            hit("WARN", "state-eager-init", base + m.start(), "the initial state expression runs on every render", "Pass a function: useState(() => compute()).")

        for m in re.finditer(r"(?<![\w$.])(useEffect|useLayoutEffect|useMemo|useCallback)\s*\(", body):
            pos = base + m.end() - 1
            close = match_close(code, pos, "(", ")")
            if close == -1:
                continue
            args = split_args(code[pos + 1:close])
            if not args:
                continue
            hook, cb, deps = m.group(1), args[0], (args[1].strip() if len(args) > 1 else None)
            if hook in ("useMemo", "useCallback"):
                if deps is None:
                    hit("FAIL", "memo-no-deps", pos, f"{hook} has no dependency array, so it recomputes every render", "Add the dependency array, or remove the hook.")
                continue
            if re.match(r"\s*async\b", cb):
                hit("FAIL", "effect-async", pos, "the effect callback is async, so it returns a promise instead of a cleanup function", "Declare an async function inside the effect and call it; return a cleanup that cancels it.")
            if deps is None:
                hit("WARN", "effect-no-deps", pos, f"{hook} has no dependency array and runs after every render", "Add the dependency array that lists every reactive value the effect reads.")
            has_cleanup = re.search(r"\breturn\b", cb) is not None
            sub = re.search(SUBSCRIPTIONS, cb)
            if sub and not has_cleanup:
                hit("FAIL", "effect-no-cleanup", pos, f"the effect starts `{sub.group(0).strip('( ')}` and returns no cleanup", "Return a function that removes the listener, clears the timer or closes the connection.")
            elif re.search(r"setTimeout\(", cb) and not has_cleanup:
                hit("WARN", "effect-no-cleanup", pos, "the effect starts a timeout and returns no cleanup", "Return () => clearTimeout(id) so a stale timeout cannot fire after unmount or a dependency change.")
            if re.search(r"\bfetch\(|axios[.(]|\.get\(|\.post\(|await\s", cb) and not re.search(CANCEL_HINTS, cb):
                hit("WARN", "effect-fetch-race", pos, "the effect fetches with no cancellation, so a slow earlier response can overwrite a newer one",
                    "Abort with AbortController in the cleanup (or use an ignore flag), or move fetching to the framework's or a library's data layer.")
            inner = re.sub(r"^\s*\(?[^)]*\)?\s*=>\s*\{?|\}?\s*$", "", cb, count=0).strip()
            stmts = [s.strip() for s in re.split(r"[;\n]", inner) if s.strip() and s.strip() not in ("{", "}")]
            setters_called = re.findall(r"(?<![\w$.])(set[A-Z][\w$]*)\(", cb)
            if stmts and all(re.match(r"set[A-Z][\w$]*\(.*\)$", s) for s in stmts) and deps not in (None, "[]"):
                hit("WARN", "effect-derived-state", pos, "the effect only copies props or state into other state",
                    "Compute the value during render (const x = ...; useMemo if it is slow) and delete the state and the effect. To reset state on a prop change, use a key.")
            if deps and deps != "[]" and "if" not in cb:
                dep_names = set(re.findall(r"[\w$]+", deps))
                for name, setter in states.items():
                    if name in dep_names and setter in setters_called and not re.search(CANCEL_HINTS + r"|setTimeout|setInterval", cb):
                        hit("FAIL", "effect-loop", pos, f"the effect sets `{name}` and also depends on it, with no condition", "Remove the state from the effect or guard the update; this re-runs forever.")
            if deps == "[]":
                stale = [n for n in states if re.search(rf"(?<![\w$.]){re.escape(n)}\b(?!\s*=>)", cb)]
                if stale:
                    hit("WARN", "effect-stale-closure", pos, f"the effect reads state `{stale[0]}` but its dependency array is empty, so it keeps the first value",
                        f"Add it to the dependencies, or use the updater form ({states[stale[0]]}(prev => ...)) so the effect does not need to read it.")

        if marks:
            for m in re.finditer(r"(?<![\w$.])(localStorage|sessionStorage|window|document|navigator)\.", body):
                pos = base + m.start()
                prefix = code[code.rfind("\n", 0, pos) + 1:pos]
                if not stack_at(marks, pos) and "=>" not in prefix and "function" not in prefix and "typeof" not in prefix:
                    hit("WARN", "render-browser-global", pos, f"`{m.group(1)}` is read during render", "Read it in an effect or event handler; during server rendering it does not exist, and on the client it causes hydration mismatches.")
            for m in re.finditer(r"(?<![\w$.])(Math\.random\(|Date\.now\(|new Date\(\s*\))", body):
                pos = base + m.start()
                prefix = code[code.rfind("\n", 0, pos) + 1:pos]
                if not stack_at(marks, pos) and "=>" not in prefix and "function" not in prefix and "useState" not in prefix and "useRef" not in prefix and "useMemo" not in prefix:
                    hit("WARN", "render-impure", pos, f"`{m.group(1).rstrip('(')}` is called during render, so the output changes on every render", "Compute it in an event handler, an effect, or a lazy useState initializer.")
            for m in re.finditer(r"(?<![\w$.])(?:React\.)?lazy\(\s*\(\s*\)\s*=>", body):
                hit("FAIL", "lazy-in-render", base + m.start(), "lazy() is called inside a component", "Declare lazy components at module scope.")
    return len(units)


def collect(paths):
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                files += [os.path.join(root, n) for n in names if n.endswith(EXTS) and not n.endswith(".d.ts")]
        else:
            raise FileNotFoundError(p)
    return sorted(set(files))


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    paths = [a for a in argv if not a.startswith("--")]
    if not paths:
        print(__doc__)
        return 2
    try:
        files = collect(paths)
    except FileNotFoundError as e:
        print(f"error: {e} does not exist. Pass source files or folders.", file=sys.stderr)
        return 2
    if not files:
        print("error: no .jsx, .tsx, .js or .ts files found under the given paths.", file=sys.stderr)
        return 2
    findings, units, skipped = [], 0, []

    def add(level, code, path, line, msg, fix, snippet):
        item = {"level": level, "code": code, "file": path.replace(os.sep, "/"), "line": line, "message": msg, "fix": fix, "source": snippet}
        if not any(f["code"] == code and f["file"] == item["file"] and f["line"] == line for f in findings):
            findings.append(item)

    for f in files:
        if os.path.getsize(f) > MAX_FILE_BYTES:
            skipped.append(f)
            continue
        units += scan_file(f, add)
    findings.sort(key=lambda f: (f["level"] != "FAIL", f["file"], f["line"]))
    fails = sum(f["level"] == "FAIL" for f in findings)
    if "--json" in argv:
        print(json.dumps({"files": len(files), "components_and_hooks": units, "fail": fails, "warn": len(findings) - fails, "findings": findings, "skipped": skipped}, indent=2))
        return 1 if fails else 0
    for f in findings:
        print(f"{f['level']} {f['code']} {f['file']}:{f['line']}: {f['message']}\n     > {f['source']}\n     fix: {f['fix']}")
    print(f"\nSUMMARY: {fails} FAIL, {len(findings) - fails} WARN in {len(files)} file(s), {units} component(s)/hook(s) recognised" + (f", {len(skipped)} large file(s) skipped" if skipped else ""))
    print("Pattern scan only: confirm each finding in the code. NOT CHECKED: missing effect dependencies in general, types, data flow across files, runtime behaviour, performance.")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
