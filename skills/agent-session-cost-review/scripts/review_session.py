#!/usr/bin/env python3
"""Report where an agent session spent its tokens.

Usage:
    python review_session.py <file-or-dir> [<file-or-dir> ...] [threshold flags]

Reads: the paths given. A directory contributes its newest *.jsonl files
(at most 20). Writes: nothing but one JSON document on stdout. No network.
Message bodies are never printed beyond 80 characters, and anything that
looks like a key or token is replaced by [REDACTED] first.

Accepted inputs (each file is detected on its own):
  * JSONL, one record per line. Understood layouts: records with
    role/content (string or block list: text, thinking, tool_use,
    tool_result), the same wrapped in a "message" object, chat-style
    "tool_calls" with role "tool" replies, and function_call /
    function_call_output records.
  * One JSON document: a list of records, or {"messages": [...]}.
  * A plain log with marker lines starting "### ": user, assistant,
    system, "tool_call <Name>: <argument>", tool_result. Text up to the
    next marker belongs to the marker.

Token counts: if an assistant record carries usage.output_tokens the
record's events share that number by character weight; everything else is
estimated as ASCII chars / 4 plus other chars / 2 (rounded up). Totals say
which basis was used.

Exit codes: 0 report produced; 1 report produced but more than 20% of the
non-blank lines could not be parsed (treat the numbers as unreliable);
2 no usable input (missing file, nothing recognised).
"""
import argparse
import glob
import json
import math
import os
import re
import sys
from collections import defaultdict

VERSION = "0.1.0"

# Token heuristic: English prose and code average about four characters per
# token; non-ASCII text packs worse, so it is counted at two.
CHARS_PER_TOKEN_ASCII = 4
CHARS_PER_TOKEN_OTHER = 2
# A tool result over 20,000 characters (about 5,000 tokens) that later
# turns never cite is the clearest single waste.
OVERSIZED_CHARS = 20000
# Whole-file read without a range returning over 12,000 characters (about
# 3,000 tokens): a range read would usually do.
WHOLE_FILE_CHARS = 12000
# A result of 8,000+ characters in the first half of a session, with at
# least 20 events after it and no later citation, rides along unused.
UNUSED_CONTEXT_CHARS = 8000
UNUSED_CONTEXT_MIN_FOLLOWING = 20
# Same call three or more times is a loop candidate.
LOOP_MIN = 3
# Unjustified re-reads of an identical read call: 2 re-reads = 3 reads.
REPEAT_READ_MIN = 3
# An assistant text block over 1,000 tokens (about 4,000 characters).
VERBOSE_TOKENS = 1000
# A result counts as cited when 3 or more of its long identifiers show up
# in later assistant text or tool-call arguments.
REF_MIN_SHARED = 3
PREVIEW_CHARS = 80
TOP_TURNS = 10
MAX_FINDINGS = 50
MAX_DIR_FILES = 20
# Exit 1 when more than this share of non-blank lines was unparseable.
MAX_UNPARSEABLE_SHARE = 0.2
MAX_FILE_BYTES = 300 * 1024 * 1024

# Share of a finding's tokens that a fix can realistically remove: a
# narrowed read still returns something, a shortened reply still replies.
SAVE_FACTOR = {
    "failing_loop": 1.0,
    "repeated_command": 1.0,
    "repeated_read": 1.0,
    "oversized_output": 0.8,
    "unused_context": 0.9,
    "whole_file_read": 0.6,
    "verbose_reply": 0.5,
}

REMEDY = {
    "failing_loop": "Stop re-running it. Read the error once, write a one-line hypothesis, change something relevant, or ask the user; record the working command in the project notes.",
    "repeated_command": "Run it once and keep the answer in the plan or a notes file; re-run only after an edit that could change the result.",
    "repeated_read": "After the first read, restate the facts needed (names, signatures, line numbers) in the plan, or read only the narrow range; do not re-read an unchanged file.",
    "oversized_output": "Narrow the command (head, grep, a line range, a summary flag) or add an ignore rule for generated and vendor paths so the output never reaches the context.",
    "unused_context": "Avoid early broad listings; when a session has carried unused bulk for 20+ events, start a fresh session with a short handoff of what matters.",
    "whole_file_read": "Search for the symbol first, then read the range around it instead of the whole file.",
    "verbose_reply": "Lead with the change, drop recaps and restated plans, and ask for short or diff-only answers.",
}

ROLES = {"user", "assistant", "system", "developer", "tool", "function"}
SHELL_TOOLS = {"bash", "shell", "sh", "powershell", "terminal", "run_command", "run_terminal_cmd",
               "exec", "execute", "exec_command", "local_shell", "run_shell_command", "cmd"}
READ_TOOLS = {"read", "read_file", "readfile", "view", "view_file", "open_file", "fs_read"}
EDIT_TOOLS = {"edit", "write", "multiedit", "notebookedit", "str_replace", "apply_patch",
              "edit_file", "write_file", "create_file", "replace"}
SEARCH_TOOLS = {"grep", "glob", "search", "find", "ls", "list_dir", "list_files",
                "codebase_search", "grep_search", "file_search"}
TARGET_KEYS = ("file_path", "path", "filename", "file", "target_file", "notebook_path")
CMD_KEYS = ("command", "cmd", "script")
RANGE_KEYS = ("offset", "limit", "start_line", "end_line", "line_start", "line_end", "view_range", "lines", "range")
SEARCH_PROGS = {"grep", "rg", "find", "ls", "dir", "tree", "fd", "ag", "findstr", "select-string", "sls"}
READ_PROGS = {"cat", "type", "bat", "less", "more", "get-content", "gc", "head", "tail", "sed"}

FAIL_RE = re.compile(r"Traceback \(most recent|\bFAILED\b|\bERROR\b|Error:|exit code [1-9]|exited with [1-9]|"
                     r"command not found|No such file|npm ERR!|Permission denied", re.I)
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_./\\-]{9,}")
MARK_RE = re.compile(r"^###\s*(user|assistant|system|tool_call|tool_result)\b[ \t]*(.*)$", re.I)

REDACT = [re.compile(p) for p in (
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\bsk-[A-Za-z0-9_-]{20,}",
    r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    r"\bxox[abprs]-[A-Za-z0-9-]{10,}",
    r"\bAIza[0-9A-Za-z_-]{35}",
    r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}",
    r"(?i)\b(?:api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*\S+",
)]


def redact(text):
    for rx in REDACT:
        text = rx.sub("[REDACTED]", text)
    return text


def preview(text):
    text = redact(" ".join(str(text).split()))
    return text if len(text) <= PREVIEW_CHARS else text[:PREVIEW_CHARS - 3] + "..."


def est_tokens(text):
    ascii_chars = len(text.encode("ascii", "ignore"))
    other = len(text) - ascii_chars
    return math.ceil(ascii_chars / CHARS_PER_TOKEN_ASCII + other / CHARS_PER_TOKEN_OTHER)


def vocab_of(text):
    return set(m.lower().rstrip("./\\-") for m in TOKEN_RE.findall(text[:300000]))


def norm_path(p):
    return str(p).replace("\\", "/").strip().lower() if p else None


def first_of(d, keys):
    for k in keys:
        v = d.get(k)
        if v not in (None, "", [], {}):
            return v
    return None


# --------------------------------------------------------------- classification

def classify_shell(cmd):
    """Return (op, target, ranged) for a shell command line."""
    seg = re.split(r"&&|;|\|\|", cmd)[0].strip()
    piped = "|" in seg
    toks = seg.split("|")[0].split()
    if not toks:
        return "run", None, False
    prog = os.path.basename(toks[0].strip("\"'")).lower()
    if prog.endswith(".exe"):
        prog = prog[:-4]
    rest = [t.strip("\"'") for t in toks[1:]]
    nonflag = [t for t in rest if not t.startswith("-")]
    target = next((t for t in reversed(nonflag)
                   if not t.isdigit() and not re.match(r"^\d+(,\d+)?[a-z]$", t)), None)
    if re.search(r"(^|\s)>>?\s*\S+", seg):
        return "edit", target, False
    if prog == "sed" and any(t == "-i" or t.startswith("-i") for t in rest):
        return "edit", target, False
    if prog == "tee":
        return "edit", target, False
    if prog in READ_PROGS:
        low = [t.lower() for t in rest]
        ranged = (prog in ("head", "tail") or piped or prog == "sed"
                  or any(t in ("-totalcount", "-tail", "-first") for t in low))
        return "read", target, ranged
    if prog in SEARCH_PROGS:
        return "search", target, False
    if prog == "git" and nonflag and nonflag[0] in ("log", "diff", "show", "status", "grep", "blame"):
        return "search", None, False
    return "run", None, False


PHASE_OF_OP = {"read": "explore", "search": "explore", "edit": "edit", "run": "run", "other": "other"}


def build_call(name, args):
    """Return dict of call attributes from a tool name and argument object."""
    lname = str(name or "unknown").lower()
    if not isinstance(args, dict):
        args = {"input": args} if args not in (None, "") else {}
    target = first_of(args, TARGET_KEYS)
    cmd = first_of(args, CMD_KEYS)
    if isinstance(cmd, list):
        cmd = " ".join(str(x) for x in cmd)
    ranged = any(k in args for k in RANGE_KEYS)
    if lname in SHELL_TOOLS or (cmd and lname not in READ_TOOLS | EDIT_TOOLS | SEARCH_TOOLS):
        op, t2, r2 = classify_shell(str(cmd or ""))
        target = target or t2
        ranged = ranged or r2
        key = " ".join(str(cmd or "").split())
    else:
        if lname in READ_TOOLS:
            op = "read"
        elif "str_replace" in lname:
            op = "read" if args.get("command") == "view" else "edit"
        elif lname in EDIT_TOOLS:
            op = "edit"
        elif lname in SEARCH_TOOLS:
            op = "search"
        else:
            op = "other"
        key = json.dumps(args, sort_keys=True, default=str)[:500]
    return {"tool": str(name or "unknown"), "target": norm_path(target), "key": key.lower(),
            "op": op, "ranged": bool(ranged), "phase": PHASE_OF_OP[op],
            "argtext": json.dumps(args, sort_keys=True, default=str)}


# --------------------------------------------------------------- event building

class Ctx:
    def __init__(self, label):
        self.label = label
        self.events = []
        self.pending = []          # unmatched call events, in order
        self.by_id = {}
        self.sessions = set()
        self.usage = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "messages": 0}
        self.seen_msg_ids = set()
        self.usage_events = 0
        self.unrecognized = []
        self.invalid = []

    def add(self, line, role, kind, text, ts, **kw):
        e = {"file": self.label, "line": line, "role": role, "kind": kind, "chars": len(text),
             "tokens": est_tokens(text), "ts": ts, "tool": None, "target": None, "key": None,
             "op": None, "ranged": False, "phase": kw.pop("phase", "reply"), "preview": preview(text),
             "vocab": None, "probe": None, "failing": False, "call": None, "result": None,
             "claimed": False, "idx": len(self.events), "id": kw.pop("id", None), "shared": 0}
        e.update(kw)
        if role == "assistant" or role == "tool_call":
            e["vocab"] = vocab_of(text)
        if role == "tool_result":
            e["probe"] = vocab_of(text)
        self.events.append(e)
        return e

    def add_call(self, line, name, args, ts, call_id):
        info = build_call(name, args)
        e = self.add(line, "tool_call", "call", info["argtext"], ts, phase=info["phase"], id=call_id,
                     tool=info["tool"], target=info["target"], key=info["key"], op=info["op"],
                     ranged=info["ranged"])
        e["preview"] = preview(info["key"] if info["op"] in ("run", "read", "search", "edit") and info["key"][:1] != "{" else info["argtext"])
        self.pending.append(e)
        if call_id:
            self.by_id[call_id] = e
        return e

    def add_result(self, line, text, ts, call_id, is_error=False):
        call = self.by_id.pop(call_id, None) if call_id else None
        if call is not None and call in self.pending:
            self.pending.remove(call)
        elif call is None and self.pending:
            call = self.pending.pop(0)
            if call["id"]:
                self.by_id.pop(call["id"], None)
        phase = call["phase"] if call else "other"
        e = self.add(line, "tool_result", "result", text, ts, phase=phase)
        if call:
            for k in ("tool", "target", "key", "op", "ranged"):
                e[k] = call[k]
            e["call"] = call
            call["result"] = e
        e["failing"] = bool(is_error or FAIL_RE.search(text[:20000]))
        return e


def block_text(content):
    """Flatten a content value (string or block list) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, str):
                parts.append(b)
            elif isinstance(b, dict):
                t = b.get("text")
                if t is None and isinstance(b.get("content"), (str, list)):
                    t = block_text(b.get("content"))
                parts.append(t if isinstance(t, str) else "")
        return "\n".join(parts)
    return "" if content is None else str(content)


def load_args(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {"input": raw}
        except ValueError:
            return {"command": raw}
    return {}


def ingest_record(ctx, rec, line):
    """Add events for one JSON record. Return False if it was not recognised."""
    if not isinstance(rec, dict):
        return False
    msg = rec["message"] if isinstance(rec.get("message"), dict) else rec
    ts = rec.get("timestamp") or rec.get("ts") or rec.get("time") or rec.get("created_at") or msg.get("timestamp")
    sid = rec.get("sessionId") or rec.get("session_id") or msg.get("session_id")
    if sid:
        ctx.sessions.add(str(sid))
    rtype = rec.get("type")
    if rtype == "function_call":
        ctx.add_call(line, rec.get("name"), load_args(rec.get("arguments")), ts, rec.get("call_id") or rec.get("id"))
        return True
    if rtype == "function_call_output":
        ctx.add_result(line, block_text(rec.get("output")), ts, rec.get("call_id"))
        return True
    role = msg.get("role") or (rtype if rtype in ROLES else None)
    if role not in ROLES:
        return False
    start = len(ctx.events)
    content = msg.get("content")
    if role in ("tool", "function"):
        ctx.add_result(line, block_text(content), ts, msg.get("tool_call_id") or msg.get("call_id"),
                       bool(msg.get("is_error")))
    elif isinstance(content, str):
        if content:
            ctx.add(line, "system" if role == "developer" else role, "text", content, ts,
                    phase="prompt" if role in ("user", "system", "developer") else "reply")
    elif isinstance(content, list):
        for b in content:
            if isinstance(b, str):
                ctx.add(line, role, "text", b, ts, phase="prompt" if role != "assistant" else "reply")
                continue
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "tool_use":
                ctx.add_call(line, b.get("name"), b.get("input"), ts, b.get("id"))
            elif bt == "tool_result":
                ctx.add_result(line, block_text(b.get("content")), ts, b.get("tool_use_id"),
                               bool(b.get("is_error")))
            elif bt == "thinking":
                ctx.add(line, "assistant", "thinking", str(b.get("thinking") or ""), ts, phase="reply")
            elif bt in ("text", "input_text", "output_text"):
                t = str(b.get("text") or "")
                if t:
                    ctx.add(line, "system" if role == "developer" else role, "text", t, ts,
                            phase="prompt" if role != "assistant" else "reply")
    for tc in msg.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") or {}
        ctx.add_call(line, fn.get("name"), load_args(fn.get("arguments")), ts, tc.get("id"))
    if isinstance(msg.get("function_call"), dict):
        fc = msg["function_call"]
        ctx.add_call(line, fc.get("name"), load_args(fc.get("arguments")), ts, None)
    # usage: split output tokens over this record's assistant events by characters
    usage = msg.get("usage") or rec.get("usage")
    if role == "assistant" and isinstance(usage, dict):
        mid = msg.get("id") or rec.get("id")
        if mid and mid in ctx.seen_msg_ids:
            return True
        if mid:
            ctx.seen_msg_ids.add(mid)
        out = usage.get("output_tokens", usage.get("completion_tokens"))
        inp = usage.get("input_tokens", usage.get("prompt_tokens"))
        if isinstance(out, int) or isinstance(inp, int):
            ctx.usage["messages"] += 1
            ctx.usage["input"] += inp if isinstance(inp, int) else 0
            ctx.usage["output"] += out if isinstance(out, int) else 0
            for src, dst in (("cache_read_input_tokens", "cache_read"), ("cache_creation_input_tokens", "cache_creation")):
                v = usage.get(src)
                ctx.usage[dst] += v if isinstance(v, int) else 0
        mine = [e for e in ctx.events[start:] if e["role"] in ("assistant", "tool_call")]
        total_chars = sum(e["chars"] for e in mine)
        if isinstance(out, int) and mine:
            for e in mine:
                e["tokens"] = max(1, round(out * e["chars"] / total_chars)) if total_chars else out
            ctx.usage_events += len(mine)
    return True


def parse_marker_log(ctx, lines):
    blocks, cur = [], None
    unparsed = []
    for n, raw in enumerate(lines, 1):
        m = MARK_RE.match(raw)
        if m:
            cur = {"line": n, "role": m.group(1).lower(), "rest": m.group(2).strip(), "body": []}
            blocks.append(cur)
        elif cur is not None:
            cur["body"].append(raw)
        elif raw.strip():
            unparsed.append(n)
    for b in blocks:
        body = "\n".join(b["body"]).strip("\n")
        role = b["role"]
        if role == "tool_call":
            name, sep, arg = b["rest"].partition(":")
            if not sep:
                parts = b["rest"].split(None, 1)
                name, arg = (parts[0] if parts else "unknown"), (parts[1] if len(parts) > 1 else "")
            argtext = (arg.strip() + ("\n" + body if body else "")).strip()
            lname = name.strip().lower()
            if lname in SHELL_TOOLS:
                args = {"command": argtext}
            elif lname in READ_TOOLS | EDIT_TOOLS | SEARCH_TOOLS:
                args = {"file_path": argtext.split()[0] if argtext.split() else ""}
                if re.search(r"\b(lines?|offset|limit)\b", argtext, re.I):
                    args["offset"] = 1
            else:
                args = {"input": argtext}
            ctx.add_call(b["line"], name.strip(), args, None, None)
        elif role == "tool_result":
            ctx.add_result(b["line"], (b["rest"] + ("\n" if b["rest"] and body else "") + body), None, None)
        else:
            text = (b["rest"] + ("\n" if b["rest"] and body else "") + body)
            ctx.add(b["line"], role, "text", text, None, phase="prompt" if role != "assistant" else "reply")
    return unparsed


def parse_file(path, label):
    ctx = Ctx(label)
    with open(path, "rb") as fh:
        data = fh.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("file is over 300 MB; split it first")
    text = data.decode("utf-8-sig", errors="replace")
    lines = [ln.rstrip("\r") for ln in text.split("\n")]
    nonblank = sum(1 for ln in lines if ln.strip())
    first = next((ln.strip() for ln in lines if ln.strip()), "")
    fmt = "jsonl"
    if MARK_RE.match(first):
        fmt = "marker_log"
        for n in parse_marker_log(ctx, lines):
            ctx.invalid.append((n, "text before the first marker"))
    else:
        doc = None
        if first.startswith("[") or first == "{":
            try:
                doc = json.loads(text)
            except ValueError:
                doc = None
        if isinstance(doc, dict) and isinstance(doc.get("messages"), list):
            doc = doc["messages"]
        if isinstance(doc, list):
            fmt = "json_document"
            nonblank = len(doc)
            for i, rec in enumerate(doc, 1):
                if not ingest_record(ctx, rec, i):
                    ctx.unrecognized.append((i, "entry has no recognised role"))
        else:
            for n, ln in enumerate(lines, 1):
                if not ln.strip():
                    continue
                try:
                    rec = json.loads(ln)
                except ValueError:
                    ctx.invalid.append((n, "not valid JSON"))
                    continue
                if not ingest_record(ctx, rec, n):
                    ctx.unrecognized.append((n, "JSON record has no recognised role"))
    return ctx, fmt, nonblank, len(lines)


# --------------------------------------------------------------- analysis

def mark_references(events):
    vocab = set()
    for e in reversed(events):
        if e["role"] == "tool_result":
            e["shared"] = len(e["probe"] & vocab) if e["probe"] else 0
        elif e["vocab"]:
            vocab |= e["vocab"]


def make_finding(kind, evs, basis, detail, cfg_note=None):
    tokens = sum(e["tokens"] for e in basis)
    for e in basis:
        e["claimed"] = True
    lines = sorted({e["line"] for e in evs})
    return {"kind": kind, "file": evs[0]["file"], "evidence_line": lines[0], "evidence_lines": lines[:10],
            "tool": evs[0]["tool"], "estimated_tokens": tokens,
            "estimated_saving_tokens": int(tokens * SAVE_FACTOR[kind]),
            "detail": detail, "evidence": evs[0]["preview"], "remedy": REMEDY[kind]}


def detect(events, cfg):
    findings = []
    n = len(events)
    calls = [e for e in events if e["role"] == "tool_call"]
    # 1. identical repeated calls (non-read): loops
    groups = defaultdict(list)
    for c in calls:
        if c["op"] != "read":
            groups[(c["tool"], c["key"])].append(c)
    for g in groups.values():
        if len(g) < cfg.loop_min:
            continue
        failing = sum(1 for c in g if c["result"] and c["result"]["failing"])
        kind = "failing_loop" if failing >= 2 else "repeated_command"
        basis = []
        for c in g[1:]:
            basis.append(c)
            if c["result"]:
                basis.append(c["result"])
        findings.append(make_finding(kind, g, basis, "%d identical calls, %d with failing results" % (len(g), failing)))
    # 2. identical read calls repeated with no edit to that file in between
    edits = defaultdict(list)
    for c in calls:
        if c["op"] == "edit" and c["target"]:
            edits[c["target"]].append(c["idx"])
    rgroups = defaultdict(list)
    for c in calls:
        if c["op"] == "read" and c["target"]:
            rgroups[(c["target"], c["key"])].append(c)
    for (target, _), g in rgroups.items():
        unj = []
        for prev, cur in zip(g, g[1:]):
            if not any(prev["idx"] < i < cur["idx"] for i in edits.get(target, [])):
                unj.append(cur)
        if len(unj) + 1 >= REPEAT_READ_MIN:
            basis = []
            for c in unj:
                basis.append(c)
                if c["result"]:
                    basis.append(c["result"])
            findings.append(make_finding("repeated_read", g, basis,
                                         "%d identical reads of %s, %d with no edit in between" % (len(g), target, len(unj))))
    # 3. single-result findings
    for i, e in enumerate(events):
        if e["role"] != "tool_result" or e["claimed"]:
            continue
        cited = e["shared"] >= REF_MIN_SHARED
        if e["chars"] > cfg.oversized_chars and not cited:
            findings.append(make_finding("oversized_output", [e], [e],
                                         "%d characters returned, %d shared identifiers with later turns" % (e["chars"], e["shared"])))
        elif (e["op"] == "read" and not e["ranged"] and e["chars"] > cfg.whole_file_chars):
            findings.append(make_finding("whole_file_read", [e], [e],
                                         "%d characters from a read with no range" % e["chars"]))
        elif (e["chars"] >= cfg.unused_context_chars and not cited and i < n / 2
              and n - i - 1 >= cfg.unused_context_min_following):
            findings.append(make_finding("unused_context", [e], [e],
                                         "%d characters, %d events after it, nothing later cites it" % (e["chars"], n - i - 1)))
    # 4. verbose assistant text
    for e in events:
        if e["role"] == "assistant" and e["kind"] == "text" and not e["claimed"] and e["tokens"] >= cfg.verbose_tokens:
            findings.append(make_finding("verbose_reply", [e], [e], "%d tokens in one assistant text block" % e["tokens"]))
    return findings


def pct(part, whole):
    return round(100.0 * part / whole, 1) if whole else 0.0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Report where an agent session spent its tokens (JSON on stdout).")
    ap.add_argument("paths", nargs="+", help="transcript files or directories")
    ap.add_argument("--oversized-chars", type=int, default=OVERSIZED_CHARS)
    ap.add_argument("--whole-file-chars", type=int, default=WHOLE_FILE_CHARS)
    ap.add_argument("--unused-context-chars", type=int, default=UNUSED_CONTEXT_CHARS)
    ap.add_argument("--unused-context-min-following", type=int, default=UNUSED_CONTEXT_MIN_FOLLOWING)
    ap.add_argument("--loop-min", type=int, default=LOOP_MIN)
    ap.add_argument("--verbose-tokens", type=int, default=VERBOSE_TOKENS)
    cfg = ap.parse_args(argv)
    notes = []
    files = []
    for p in cfg.paths:
        if os.path.isdir(p):
            found = sorted(glob.glob(os.path.join(p, "**", "*.jsonl"), recursive=True),
                           key=os.path.getmtime, reverse=True)
            if len(found) > MAX_DIR_FILES:
                notes.append("directory %s holds %d .jsonl files; only the newest %d were read" % (p, len(found), MAX_DIR_FILES))
            if not found:
                sys.stderr.write("error: no .jsonl files under %s\n" % p)
                return 2
            files.extend(found[:MAX_DIR_FILES])
        elif os.path.isfile(p):
            files.append(p)
        else:
            sys.stderr.write("error: %s does not exist; pass a transcript file or a directory of .jsonl files\n" % p)
            return 2
    all_events, file_info, findings = [], [], []
    usage = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "messages": 0}
    usage_events = 0
    unparse_samples, nonblank_total, unparse_total = [], 0, 0
    sessions = set()
    unmatched = 0
    for path in files:
        label = os.path.basename(path)
        try:
            ctx, fmt, nonblank, nlines = parse_file(path, label)
        except (OSError, ValueError) as exc:
            sys.stderr.write("error: cannot read %s: %s\n" % (path, exc))
            return 2
        mark_references(ctx.events)
        findings.extend(detect(ctx.events, cfg))
        bad = ctx.invalid + ctx.unrecognized
        unparse_total += len(bad)
        nonblank_total += nonblank
        for n, why in sorted(bad)[:10]:
            if len(unparse_samples) < 10:
                unparse_samples.append({"file": label, "line": n, "reason": why})
        file_info.append({"file": label, "format": fmt, "lines": nlines, "events": len(ctx.events),
                          "invalid_json_lines": len(ctx.invalid), "unrecognized_records": len(ctx.unrecognized)})
        for k in usage:
            usage[k] += ctx.usage[k]
        usage_events += ctx.usage_events
        sessions |= ctx.sessions
        unmatched += sum(1 for e in ctx.events if e["role"] == "tool_result" and e["call"] is None)
        all_events.extend(ctx.events)
    if not all_events:
        sys.stderr.write("error: no events recognised; see the accepted layouts in the script docstring\n")
        return 2
    total = sum(e["tokens"] for e in all_events)
    by_role = defaultdict(lambda: [0, 0])
    by_phase = defaultdict(lambda: [0, 0])
    by_tool = {}
    for e in all_events:
        by_role[e["role"]][0] += 1
        by_role[e["role"]][1] += e["tokens"]
        by_phase[e["phase"]][0] += 1
        by_phase[e["phase"]][1] += e["tokens"]
        if e["tool"] and e["role"] in ("tool_call", "tool_result"):
            t = by_tool.setdefault(e["tool"], {"tool": e["tool"], "calls": 0, "call_tokens": 0,
                                               "result_tokens": 0, "largest_result_chars": 0})
            if e["role"] == "tool_call":
                t["calls"] += 1
                t["call_tokens"] += e["tokens"]
            else:
                t["result_tokens"] += e["tokens"]
                t["largest_result_chars"] = max(t["largest_result_chars"], e["chars"])
    for t in by_tool.values():
        t["total_tokens"] = t["call_tokens"] + t["result_tokens"]
        t["share_pct"] = pct(t["total_tokens"], total)
    findings.sort(key=lambda f: (-f["estimated_tokens"], f["file"], f["evidence_line"]))
    truncated = len(findings) > MAX_FINDINGS
    findings = findings[:MAX_FINDINGS]
    for i, f in enumerate(findings, 1):
        f["rank"] = i
    savings = []
    for kind in SAVE_FACTOR:
        fs = [f for f in findings if f["kind"] == kind]
        if fs:
            tok = sum(f["estimated_tokens"] for f in fs)
            sv = sum(f["estimated_saving_tokens"] for f in fs)
            savings.append({"kind": kind, "findings": len(fs), "estimated_tokens": tok,
                            "estimated_saving_tokens": sv, "share_of_total_pct": pct(sv, total),
                            "remedy": REMEDY[kind]})
    savings.sort(key=lambda s: -s["estimated_saving_tokens"])
    top = sorted(all_events, key=lambda e: -e["tokens"])[:TOP_TURNS]
    ts_events = sum(1 for e in all_events if e["ts"])
    share = unparse_total / nonblank_total if nonblank_total else 0.0
    if usage_events:
        basis = "usage counts for %d assistant events, character estimate for the rest" % usage_events
    else:
        basis = "character estimate only (%d ASCII chars or %d other chars per token)" % (CHARS_PER_TOKEN_ASCII, CHARS_PER_TOKEN_OTHER)
    report = {
        "tool": "review_session.py", "version": VERSION,
        "files": file_info,
        "totals": {
            "files": len(files), "events": len(all_events), "estimated_tokens": total, "token_basis": basis,
            "reported_usage": None if not usage["messages"] else {
                "input_tokens": usage["input"], "output_tokens": usage["output"],
                "cache_read_tokens": usage["cache_read"], "cache_creation_tokens": usage["cache_creation"],
                "messages_with_usage": usage["messages"]},
            "by_role": sorted(({"role": r, "events": v[0], "estimated_tokens": v[1], "share_pct": pct(v[1], total)}
                               for r, v in by_role.items()), key=lambda x: -x["estimated_tokens"]),
            "estimated_saving_tokens": sum(s["estimated_saving_tokens"] for s in savings),
        },
        "by_phase": sorted(({"phase": p, "events": v[0], "estimated_tokens": v[1], "share_pct": pct(v[1], total)}
                            for p, v in by_phase.items()), key=lambda x: -x["estimated_tokens"]),
        "by_tool": sorted(by_tool.values(), key=lambda t: -t["total_tokens"]),
        "top_turns": [{"file": e["file"], "line": e["line"], "role": e["role"], "tool": e["tool"],
                       "estimated_tokens": e["tokens"], "preview": e["preview"]} for e in top],
        "findings": findings,
        "findings_truncated": truncated,
        "savings": savings,
        "checks": {
            "non_blank_lines": nonblank_total, "unparseable_total": unparse_total,
            "unparseable_share": round(share, 3), "unparseable_samples": unparse_samples,
            "missing_timestamps": len(all_events) - ts_events, "events_with_timestamps": ts_events,
            "session_ids": sorted(sessions), "mixed_sessions": len(sessions) > 1,
            "multiple_files": len(files) > 1, "unmatched_tool_results": unmatched,
        },
        "notes": notes,
    }
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    return 1 if share > MAX_UNPARSEABLE_SHARE else 0


if __name__ == "__main__":
    sys.exit(main())
