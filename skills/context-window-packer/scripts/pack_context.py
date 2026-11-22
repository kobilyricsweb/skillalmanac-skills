#!/usr/bin/env python3
"""Pick which files fit into a fixed model context, and say why for each one.

Usage:
    python pack_context.py pack <manifest.json> [--root DIR] [--out PACKAGE] [--force]
                           [--chars-per-token N]
    python pack_context.py estimate <file> [<file> ...] [--chars-per-token N]

Reads: the manifest and every candidate file it names (read-only).
Writes: nothing, unless `pack --out PACKAGE` is given; then only that one file.
The output path is refused if it resolves to the manifest or to any candidate
path, even with --force. Without --force an existing output is not replaced.
Prints strict JSON (schema_version "1") on stdout. No network, no tokenizer
download, no model call: token counts are heuristic estimates with a stated
error range.

Manifest (JSON):
    {
      "budget": 32000,               total window in tokens (required)
      "reserve": 6000,               tokens kept free for reasoning and the answer
      "fixed_tokens": 900,           tokens already spent on instructions and the question
      "chars_per_token": 3.8,        optional ratio measured on your own sample
      "candidates": [
        {"id": "a", "path": "src/app.py", "priority": "must",
         "relevance": 9, "note": "entry point",
         "allow": ["signatures"], "summary": "optional hand-written stub"}
      ]
    }
Paths are relative to the manifest folder (or --root) and must stay inside it.

Exit codes: 0 no errors, 1 at least one error finding (a must item does not
fit, is missing, is unreadable, or matches a secret pattern), 2 bad input.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import re
import sys

SCHEMA_VERSION = "1"

# Characters per token for ASCII text, by file type. These are rule-of-thumb
# values for common BPE tokenizers (English prose runs near 4, code near 3 to
# 3.5, punctuation-heavy data near 3). They were not measured against a real
# tokenizer in this package; that is why every report carries an error range.
CHARS_PER_TOKEN = {"prose": 4.0, "code": 3.3, "struct": 3.0, "other": 3.5}
# Stated error of the estimate (percent, plus or minus) per file type.
ERROR_PCT = {"prose": 20, "code": 25, "struct": 30, "other": 30}
# Non-ASCII characters (accents, CJK, emoji) often cost one token or more each.
NONASCII_TOKENS_PER_CHAR = 1.0
# When more than this share of characters is non-ASCII the estimate is worse.
NONASCII_SHARE_WIDE_ERROR = 0.2
WIDE_ERROR_PCT = 40
# A ratio the user measured on their own sample of the same material.
USER_RATIO_ERROR_PCT = 10
# The answer needs room to think and write; never plan to fill the window.
MIN_RESERVE_PCT = 15
# Heuristic cost of the "=== id: path [level] ===" line above each item.
HEADER_CHARS_PER_TOKEN = 3.5
# Stubs and outlines are only worth offering when clearly smaller than the file.
LADDER_MAX_SHARE_OF_FULL = 0.7
# Minified or generated text: very long lines in a big file.
MINIFIED_MIN_BYTES = 5000
MINIFIED_MAX_LINE = 1500
# Files this large are refused rather than read.
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_SIGNATURE_LINES = 400
HEAD_LINES = 15
CSV_SAMPLE_ROWS = 3

PROSE_EXT = {".md", ".markdown", ".txt", ".rst", ".adoc"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".go", ".rs",
            ".c", ".h", ".cpp", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".sh",
            ".sql", ".lua", ".scala", ".css"}
STRUCT_EXT = {".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv", ".tsv", ".xml",
              ".html", ".htm", ".ini", ".cfg", ".svg"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
             "cargo.lock", "gemfile.lock", "composer.lock", "go.sum", "uv.lock",
             "pipfile.lock"}
PRIORITIES = ("must", "should", "nice")
LEVELS = ("full", "signatures", "summary")
DEFAULT_LADDER = {"must": ("full",), "should": ("full", "signatures", "summary"),
                  "nice": ("full", "signatures")}
DEFAULT_RELEVANCE = 5

SECRET_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("sk_token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("pgp_private_key_block", re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----")),
    # Three base64url segments, the first starting eyJ (base64 of '{"').
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}")),
    # KEY=value or KEY: value where the name holds a credential word. The value
    # must be 6+ characters and not a variable reference.
    ("env_credential", re.compile(
        r"^[ \t]*(?:export[ \t]+)?[\w.-]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API[_-]?KEY)[\w.-]*[ \t]*[=:][ \t]*"
        r"[\"']?(?![$<{%]|os\.|process\.env)[^\s\"']{6,}", re.I | re.M)),
]

JS_SIG = re.compile(
    r"^\s*(export\s+)?(default\s+)?(async\s+)?(function\*?|class|interface|type|enum)\b"
    r"|^\s*(export\s+)?(const|let|var)\s+\w+\s*(:[^=]+)?=\s*(async\s*)?(\(|function\b|\w+\s*=>)")
GENERIC_SIG = re.compile(
    r"^\s*(public|private|protected|internal|static|abstract|class|interface|struct|enum|"
    r"func|fn|def|function|impl|trait|type|pub|module|namespace|package)\b")
MD_HEADING = re.compile(r"^#{1,6}\s+\S")


class BadInput(Exception):
    """Raised for input the user must fix; becomes exit code 2."""


def file_kind(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in PROSE_EXT:
        return "prose"
    if ext in CODE_EXT:
        return "code"
    if ext in STRUCT_EXT:
        return "struct"
    return "other"


def estimate_tokens(text, kind, override=None):
    """Return (tokens, error_pct) for text of the given kind."""
    if not text:
        return 0, 0
    non_ascii = sum(1 for ch in text if ord(ch) > 127)
    ascii_chars = len(text) - non_ascii
    cpt = override if override else CHARS_PER_TOKEN[kind]
    tokens = math.ceil(ascii_chars / cpt + non_ascii * NONASCII_TOKENS_PER_CHAR)
    if override:
        err = USER_RATIO_ERROR_PCT
    else:
        err = ERROR_PCT[kind]
    if non_ascii / len(text) > NONASCII_SHARE_WIDE_ERROR:
        err = max(err, WIDE_ERROR_PCT)
    return tokens, err


def header_line(item_id, path, level):
    return f"=== {item_id}: {path} [{level}] ==="


def header_tokens(line):
    return math.ceil((len(line) + 1) / HEADER_CHARS_PER_TOKEN)


def normalise(text):
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")).strip()


def py_signatures(text):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return [ln.rstrip() for ln in text.split("\n") if re.match(r"^\s*(async\s+def|def|class)\s", ln)]
    lines = text.split("\n")
    out = []
    doc = ast.get_docstring(tree)
    if doc:
        out.append('"""' + doc.strip().split("\n")[0] + '"""')

    def visit(body, depth):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                for deco in getattr(node, "decorator_list", []):
                    out.append(lines[deco.lineno - 1].rstrip())
                sig = lines[start].rstrip()
                if not sig.rstrip().endswith(":"):
                    sig += " ..."
                out.append(sig)
                nd = ast.get_docstring(node)
                if nd:
                    out.append("    " * (depth + 1) + '"""' + nd.strip().split("\n")[0] + '"""')
                if isinstance(node, ast.ClassDef):
                    visit(node.body, depth + 1)
    visit(tree.body, 0)
    return out


def md_outline(text):
    out, fenced = [], False
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and MD_HEADING.match(ln):
            out.append(ln.rstrip())
    return out


def json_shape(text):
    try:
        data = json.loads(text)
    except ValueError:
        return []
    def kind(v):
        return type(v).__name__
    if isinstance(data, dict):
        return [f"{k}: {kind(v)}" for k, v in data.items()]
    if isinstance(data, list):
        out = [f"list of {len(data)} items"]
        if data and isinstance(data[0], dict):
            out += [f"  [0].{k}: {kind(v)}" for k, v in data[0].items()]
        return out
    return []


def make_signatures(text, path):
    """Return the 'signatures' form of a file (outline of its structure) or ''."""
    ext = os.path.splitext(path)[1].lower()
    lines = text.split("\n")
    if ext == ".py":
        sig = py_signatures(text)
    elif ext in JS_EXT:
        sig = [ln.rstrip().rstrip("{").rstrip() for ln in lines if JS_SIG.match(ln)]
    elif ext in (".md", ".markdown", ".rst", ".adoc"):
        sig = md_outline(text)
    elif ext == ".json":
        sig = json_shape(text)
    elif ext in (".csv", ".tsv"):
        sig = lines[:1 + CSV_SAMPLE_ROWS]
    elif ext in (".yaml", ".yml"):
        sig = [ln.rstrip() for ln in lines if re.match(r"^[A-Za-z_][\w-]*:", ln)]
    elif ext == ".toml":
        sig = [ln.rstrip() for ln in lines if re.match(r"^\[|^[A-Za-z_][\w-]*\s*=", ln)]
    elif ext in CODE_EXT:
        sig = [ln.rstrip().rstrip("{").rstrip() for ln in lines if GENERIC_SIG.match(ln)]
    else:
        sig = [ln.rstrip() for ln in lines if ln.strip()][:HEAD_LINES]
    sig = [s for s in sig if s.strip()][:MAX_SIGNATURE_LINES]
    return "\n".join(sig)


def make_stub(text, path, tokens_full):
    first = next((ln.strip() for ln in text.split("\n") if ln.strip()), "")
    if len(first) > 100:
        first = first[:97] + "..."
    n_lines = text.count("\n") + 1
    return f"[stub] {path}: {file_kind(path)} file, {n_lines} lines, about {tokens_full} tokens. First line: {first}"


def load_manifest(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        raise BadInput(f"cannot read manifest '{path}': {exc.strerror}")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise BadInput(f"manifest '{path}' is not valid UTF-8 JSON: {exc}")
    if not isinstance(data, dict):
        raise BadInput("manifest must be a JSON object")
    budget = data.get("budget")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
        raise BadInput("manifest.budget must be a positive integer (total window in tokens)")
    for key in ("reserve", "fixed_tokens"):
        val = data.get(key, 0)
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            raise BadInput(f"manifest.{key} must be a non-negative integer")
    cpt = data.get("chars_per_token")
    if cpt is not None and (not isinstance(cpt, (int, float)) or isinstance(cpt, bool) or cpt <= 0):
        raise BadInput("manifest.chars_per_token must be a positive number")
    cands = data.get("candidates")
    if not isinstance(cands, list) or not cands:
        raise BadInput("manifest.candidates must be a non-empty list")
    seen = set()
    for i, c in enumerate(cands):
        if not isinstance(c, dict):
            raise BadInput(f"candidates[{i}] must be an object")
        cid, cpath = c.get("id"), c.get("path")
        if not isinstance(cid, str) or not cid:
            raise BadInput(f"candidates[{i}].id must be a non-empty string")
        if cid in seen:
            raise BadInput(f"duplicate candidate id '{cid}'")
        seen.add(cid)
        if not isinstance(cpath, str) or not cpath:
            raise BadInput(f"candidate '{cid}': path must be a non-empty string")
        if c.get("priority") not in PRIORITIES:
            raise BadInput(f"candidate '{cid}': priority must be one of {', '.join(PRIORITIES)}")
        rel = c.get("relevance", DEFAULT_RELEVANCE)
        if not isinstance(rel, (int, float)) or isinstance(rel, bool) or not 0 <= rel <= 10:
            raise BadInput(f"candidate '{cid}': relevance must be a number from 0 to 10")
        allow = c.get("allow")
        if allow is not None:
            if not isinstance(allow, list) or any(a not in ("signatures", "summary") for a in allow):
                raise BadInput(f"candidate '{cid}': allow must be a list using only 'signatures' and 'summary'")
        if "summary" in c and not isinstance(c["summary"], str):
            raise BadInput(f"candidate '{cid}': summary must be a string")
    return data


def inside(root, target):
    root = os.path.normcase(os.path.realpath(root))
    target = os.path.normcase(os.path.realpath(target))
    try:
        return os.path.commonpath([root, target]) == root
    except ValueError:
        return False


def prepare(cand, order, root, override):
    """Read one candidate. Returns an item dict; item['skip'] = (code, detail) if unusable."""
    item = {"id": cand["id"], "path": cand["path"], "priority": cand["priority"],
            "relevance": cand.get("relevance", DEFAULT_RELEVANCE), "note": cand.get("note", ""),
            "order": order, "allow_secret": bool(cand.get("allow_secret_match")),
            "abs": os.path.normpath(os.path.join(root, cand["path"])), "skip": None,
            "levels": {}, "full_tokens": 0}
    ladder = list(DEFAULT_LADDER[item["priority"]])
    if "allow" in cand and cand["allow"] is not None:
        extra = [lvl for lvl in LEVELS[1:] if lvl in cand["allow"]]
        ladder = ["full"] + extra
    item["ladder"] = ladder
    if not inside(root, item["abs"]):
        item["skip"] = ("path_outside_root", "path leaves the manifest folder")
        return item
    if not os.path.isfile(item["abs"]):
        item["skip"] = ("missing_file", "file not found")
        return item
    size = os.path.getsize(item["abs"])
    if size > MAX_FILE_BYTES:
        item["skip"] = ("too_large", f"{size} bytes is over the {MAX_FILE_BYTES} byte read limit")
        return item
    try:
        with open(item["abs"], "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        item["skip"] = ("unreadable", exc.strerror or "read error")
        return item
    if b"\x00" in raw[:8192]:
        item["skip"] = ("binary", "contains NUL bytes")
        return item
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        item["skip"] = ("binary", "not valid UTF-8 text")
        return item
    text = text.replace("\r\n", "\n")  # same estimate on every operating system
    if not text.strip():
        item["skip"] = ("empty", "file has no content")
        return item
    longest = max(len(ln) for ln in text.split("\n"))
    if size >= MINIFIED_MIN_BYTES and longest > MINIFIED_MAX_LINE:
        item["skip"] = ("minified", f"longest line is {longest} characters")
        return item
    if not item["allow_secret"]:
        for name, pat in SECRET_PATTERNS:
            if pat.search(text):
                item["skip"] = ("possible_secret", f"matches {name} pattern (value not shown); remove it or set allow_secret_match")
                return item
    item["text"] = text
    item["kind"] = file_kind(item["path"])
    item["hash"] = hashlib.sha256(normalise(text).encode("utf-8")).hexdigest()
    item["lockfile"] = os.path.basename(item["path"]).lower() in LOCKFILES
    # Build the levels this item can be offered at.
    full_tok, err = estimate_tokens(text, item["kind"], override)
    item["error_pct"] = err
    item["full_tokens"] = full_tok

    def cost(level, body):
        tok, _ = estimate_tokens(body, item["kind"], override)
        return tok + header_tokens(header_line(item["id"], item["path"], level))

    item["levels"]["full"] = (text, cost("full", text))
    sig = make_signatures(text, item["path"])
    if sig and cost("signatures", sig) <= LADDER_MAX_SHARE_OF_FULL * item["levels"]["full"][1]:
        item["levels"]["signatures"] = (sig, cost("signatures", sig))
    stub = cand.get("summary") or make_stub(text, item["path"], full_tok)
    if cost("summary", stub) < item["levels"]["full"][1]:
        item["levels"]["summary"] = (stub, cost("summary", stub))
    return item


def refuse_output(out_path, manifest_path, items, force):
    out_real = os.path.normcase(os.path.realpath(out_path))
    inputs = {os.path.normcase(os.path.realpath(manifest_path))}
    inputs.update(os.path.normcase(os.path.realpath(i["abs"])) for i in items)
    if out_real in inputs:
        raise BadInput(f"refusing to write '{out_path}': it is the manifest or a candidate file (inputs are never overwritten)")
    if os.path.isdir(out_path):
        raise BadInput(f"output '{out_path}' is a directory")
    if os.path.exists(out_path) and not force:
        raise BadInput(f"output '{out_path}' exists; pass --force to replace it")


def pack(manifest_path, root, override_cli, out_path, force):
    data = load_manifest(manifest_path)
    root = root or os.path.dirname(os.path.abspath(manifest_path))
    override = override_cli or data.get("chars_per_token")
    budget = data["budget"]
    fixed = data.get("fixed_tokens", 0)
    requested = data.get("reserve", 0)
    min_reserve = math.ceil(budget * MIN_RESERVE_PCT / 100)
    reserve = max(requested, min_reserve)
    usable = budget - fixed - reserve
    if usable <= 0:
        raise BadInput(f"budget {budget} minus fixed_tokens {fixed} minus reserve {reserve} leaves nothing to pack")

    items = [prepare(c, n, root, override) for n, c in enumerate(data["candidates"])]
    if out_path:
        refuse_output(out_path, manifest_path, items, force)

    warnings, errors, dropped = [], [], []
    if requested < min_reserve:
        warnings.append({"code": "reserve_raised", "id": None,
                         "message": f"reserve {requested} is under {MIN_RESERVE_PCT}% of the window; raised to {reserve}"})
    if override:
        warnings.append({"code": "user_ratio_used", "id": None,
                         "message": f"chars_per_token {override} applied to every file; assumed error {USER_RATIO_ERROR_PCT}%"})

    def drop(item, code, detail):
        dropped.append({"id": item["id"], "path": item["path"], "priority": item["priority"],
                        "tokens_full": item.get("full_tokens", 0), "reason_code": code, "reason": detail})

    # Stage 1: unusable files.
    live = []
    for it in items:
        if it["skip"]:
            code, detail = it["skip"]
            drop(it, code, detail)
            if it["priority"] == "must":
                errors.append({"code": "must_unusable", "id": it["id"],
                               "message": f"must item '{it['id']}' cannot be included ({code}: {detail})"})
            continue
        if it["lockfile"]:
            if it["priority"] == "must":
                warnings.append({"code": "lockfile_flagged", "id": it["id"],
                                 "message": "generated lockfile kept only because it is marked must"})
            else:
                drop(it, "lockfile", "generated lockfile; lists versions, rarely what the question needs")
                continue
        live.append(it)

    # Stage 2: exact duplicates (after trimming trailing spaces and line endings).
    canon = {}
    unique = []
    for it in sorted(live, key=lambda x: (PRIORITIES.index(x["priority"]), x["order"])):
        first = canon.get(it["hash"])
        if first is None:
            canon[it["hash"]] = it
            unique.append(it)
        else:
            drop(it, "duplicate", f"same content as '{first['id']}'")
    unique.sort(key=lambda x: x["order"])

    # Stage 3: must items.
    chosen = {}  # id -> level
    must = [it for it in unique if it["priority"] == "must"]
    for it in must:
        chosen[it["id"]] = "full"

    def cost_of(it):
        return it["levels"][chosen[it["id"]]][1]

    used = sum(cost_of(it) for it in must)
    if used > usable:
        for it in sorted(must, key=lambda x: -x["levels"]["full"][1]):
            for lvl in it["ladder"][1:]:
                if used <= usable:
                    break
                if lvl in it["levels"] and it["levels"][lvl][1] < cost_of(it):
                    used -= cost_of(it)
                    chosen[it["id"]] = lvl
                    used += cost_of(it)
        if used > usable:
            errors.append({"code": "must_exceeds_budget", "id": None,
                           "message": f"must items need {used} tokens but only {usable} are usable "
                                      f"(budget {budget} - fixed {fixed} - reserve {reserve}); raise the budget, "
                                      f"mark some items 'should', or allow signatures/summary"})

    # Stage 4: greedy over should then nice, best relevance per token first.
    rest = [it for it in unique if it["priority"] != "must"]
    rest.sort(key=lambda x: (PRIORITIES.index(x["priority"]),
                             -(x["relevance"] / max(x["levels"]["full"][1], 1)), x["order"]))
    overspent = used > usable
    for it in rest:
        if overspent:
            drop(it, "no_room", "must items already fill the usable space")
            continue
        remaining = usable - used
        placed = None
        tried = []
        for lvl in it["ladder"]:
            if lvl not in it["levels"]:
                continue
            tok = it["levels"][lvl][1]
            if tok <= remaining:
                placed = lvl
                break
            tried.append(f"{lvl} needs {tok}")
        if placed:
            chosen[it["id"]] = placed
            used += it["levels"][placed][1]
            it["why"] = ("fits in full" if placed == "full" else
                         f"full did not fit ({it['levels']['full'][1]} > {remaining} left); {placed} fits")
        else:
            drop(it, "no_room", f"{'; '.join(tried) or 'no smaller form available'}; {remaining} tokens left")

    # Report.
    kept, compressed = [], []
    for it in unique:
        lvl = chosen.get(it["id"])
        if not lvl:
            continue
        row = {"id": it["id"], "path": it["path"], "priority": it["priority"], "level": lvl,
               "tokens": it["levels"][lvl][1], "relevance": it["relevance"]}
        if it["note"]:
            row["note"] = it["note"]
        if lvl == "full":
            row["reason"] = "must item" if it["priority"] == "must" else it.get("why", "fits in full")
            kept.append(row)
        else:
            row["tokens_full"] = it["levels"]["full"][1]
            row["reason"] = it.get("why") or "must item shrunk to fit the budget"
            compressed.append(row)
    kept_rows = kept + compressed
    total_tok = sum(r["tokens"] for r in kept_rows)
    weights = {r["id"]: next(i for i in unique if i["id"] == r["id"])["error_pct"] for r in kept_rows}
    err_pct = round(sum(r["tokens"] * weights[r["id"]] for r in kept_rows) / total_tok, 1) if total_tok else 0
    worst = math.ceil(total_tok * (1 + err_pct / 100))
    margin = usable - total_tok
    margin_worst = usable - worst
    if margin_worst < 0 <= margin:
        warnings.append({"code": "worst_case_overflow", "id": None,
                         "message": f"at the upper end of the estimate the package needs about {worst} tokens, "
                                    f"{-margin_worst} over the usable {usable}; drop one 'nice' item or supply a measured chars_per_token"})
    order_key = {p: i for i, p in enumerate(PRIORITIES)}
    kept.sort(key=lambda r: (order_key[r["priority"]], 0))
    report = {
        "schema_version": SCHEMA_VERSION, "command": "pack",
        "status": "error" if errors else "ok",
        "budget": budget, "fixed_tokens": fixed,
        "reserve": {"requested": requested, "effective": reserve, "min_pct": MIN_RESERVE_PCT},
        "usable": usable, "used": total_tok,
        "kept": kept, "compressed": compressed, "dropped": dropped,
        "margin": margin, "margin_worst_case": margin_worst,
        "estimate_error_pct": err_pct,
        "estimator": {"chars_per_token": dict(CHARS_PER_TOKEN) if not override else {"all": override},
                      "nonascii_tokens_per_char": NONASCII_TOKENS_PER_CHAR,
                      "label": "approximate; no tokenizer was run"},
        "warnings": warnings, "errors": errors,
    }
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            for it in sorted((i for i in unique if i["id"] in chosen),
                             key=lambda x: (PRIORITIES.index(x["priority"]), x["order"])):
                lvl = chosen[it["id"]]
                fh.write(header_line(it["id"], it["path"], lvl) + "\n")
                fh.write(it["levels"][lvl][0].rstrip("\n") + "\n\n")
        report["package"] = {"path": out_path, "items": len(chosen)}
    return report


def estimate_cmd(files, override):
    rows = []
    for path in files:
        try:
            with open(path, "rb") as fh:
                raw = fh.read(MAX_FILE_BYTES + 1)
        except OSError as exc:
            raise BadInput(f"cannot read '{path}': {exc.strerror}")
        if len(raw) > MAX_FILE_BYTES or b"\x00" in raw[:8192]:
            rows.append({"path": path, "tokens": None, "error_pct": None, "note": "binary or too large"})
            continue
        text = raw.decode("utf-8", errors="replace")
        kind = file_kind(path)
        tok, err = estimate_tokens(text, kind, override)
        rows.append({"path": path, "kind": kind, "chars": len(text), "tokens": tok, "error_pct": err,
                     "range": [math.floor(tok * (1 - err / 100)), math.ceil(tok * (1 + err / 100))]})
    return {"schema_version": SCHEMA_VERSION, "command": "estimate", "files": rows,
            "label": "approximate; no tokenizer was run"}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Pack candidate files into a fixed token budget.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pack", help="select, compress and drop candidates")
    p.add_argument("manifest")
    p.add_argument("--root", help="folder that candidate paths are relative to (default: manifest folder)")
    p.add_argument("--out", help="also write the packed context to this new file")
    p.add_argument("--force", action="store_true", help="replace an existing --out file (never an input)")
    p.add_argument("--chars-per-token", type=float, help="ratio measured on your own sample")
    e = sub.add_parser("estimate", help="estimate tokens for files")
    e.add_argument("files", nargs="+")
    e.add_argument("--chars-per-token", type=float)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if getattr(args, "chars_per_token", None) is not None and args.chars_per_token <= 0:
            raise BadInput("--chars-per-token must be positive")
        if args.command == "pack":
            report = pack(args.manifest, args.root, args.chars_per_token, args.out, args.force)
        else:
            report = estimate_cmd(args.files, args.chars_per_token)
    except BadInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report.get("errors") else 0


if __name__ == "__main__":
    sys.exit(main())
