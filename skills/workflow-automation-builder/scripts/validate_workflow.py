#!/usr/bin/env python3
"""Validate a workflow design spec (JSON) for silent-failure risks.

Usage:
    python validate_workflow.py <spec.json>

Reads the one file given. Writes nothing. Prints ONE JSON object to stdout:
    {"tool": "validate_workflow", "spec": "<path>", "ok": bool,
     "summary": {"errors": n, "warnings": n, "steps": n},
     "findings": [{"rule", "severity", "step", "path", "message", "fix"}]}
Secret values found in the spec are never echoed; only a redacted prefix is shown.

Exit codes: 0 = no errors (warnings allowed), 1 = at least one error,
2 = the file is missing, empty, not UTF-8 or not valid JSON (the JSON then has
"ok": false and a "fatal" message).

The spec format is described in references/spec-format.md. Standard library only,
no network.
"""
import json
import os
import re
import sys

# Retrying more than this hides an outage behind a pile of duplicate calls (reason: 5 tries
# with doubling delay already span about a minute; 10 is a hard ceiling).
MAX_RETRY_ATTEMPTS = 10
# Loops past this size are almost always a missing filter, not intent.
MAX_LOOP_ITERATIONS_WARN = 1000
STEP_TYPES = {"filter", "action", "branch", "loop", "delay", "transform"}
TRIGGER_TYPES = {"webhook", "schedule", "poll", "event"}
EXHAUSTED_OK = {"dead_letter", "alert_stop", "fallback"}
EXHAUSTED_SILENT = {"skip", "ignore", "continue"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

SENSITIVE_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|apikey|authorization|private[_-]?key|credential|bearer)", re.I)
SAFE_KEY_SUFFIX = re.compile(r"(_ref|_name|_id|_header|_env)$", re.I)
TEMPLATE = re.compile(r"\{\{.*?\}\}|\$\{[^}]*\}")
SECRET_REF = re.compile(r"\{\{\s*secrets\.[A-Za-z0-9_.-]+\s*\}\}|\$\{(secret|vault):[A-Za-z0-9_./-]+\}")
CREDENTIAL_PATTERNS = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("sk_token", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"\bghp_[A-Za-z0-9]{30,}")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("slack_webhook_url", re.compile(r"hooks\.slack\.com/services/T[A-Za-z0-9]+/B[A-Za-z0-9]+/[A-Za-z0-9]{10,}")),
    ("url_with_credentials", re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@{]+:[^/\s@{]+@")),
    ("secret_in_query", re.compile(r"[?&](api[_-]?key|apikey|token|access_token|secret|sig|signature)=([^&\s{]+)", re.I)),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]


def redact(text):
    text = str(text)
    return text[:4] + "***" if len(text) > 4 else "***"


class Report:
    def __init__(self):
        self.findings = []

    def add(self, rule, severity, step, path, message, fix):
        self.findings.append({"rule": rule, "severity": severity, "step": step,
                              "path": path, "message": message, "fix": fix})


def as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def next_ids(step):
    """All step ids this step can flow to."""
    out = []
    for key in ("next", "else", "on_reject", "body"):
        for v in as_list(step.get(key)):
            if isinstance(v, str):
                out.append(v)
    for br in as_list(step.get("branches")):
        if isinstance(br, dict):
            for v in as_list(br.get("next")):
                if isinstance(v, str):
                    out.append(v)
    oe = step.get("on_error")
    if isinstance(oe, dict) and isinstance(oe.get("fallback_step"), str):
        out.append(oe["fallback_step"])
    return out


def is_write(step):
    cfg = step.get("config") if isinstance(step.get("config"), dict) else {}
    method = str(cfg.get("method", step.get("method", ""))).upper()
    kind = step.get("kind")
    if kind == "write" or step.get("writes") is True or method in WRITE_METHODS:
        return True
    return False


def write_unknown(step):
    cfg = step.get("config") if isinstance(step.get("config"), dict) else {}
    method = str(cfg.get("method", step.get("method", ""))).upper()
    return step.get("kind") not in ("read", "write") and step.get("writes") is None and not method


def scan_secrets(node, path, step_id, rep):
    if isinstance(node, dict):
        if "secret_ref" in node and len(node) == 1:
            return
        for k, v in node.items():
            child = f"{path}.{k}" if path else str(k)
            if isinstance(v, str) and SENSITIVE_KEY.search(k) and not SAFE_KEY_SUFFIX.search(k):
                rest = TEMPLATE.sub("", v).strip()
                rest = re.sub(r"^(Bearer|Basic|Token)\s*", "", rest, flags=re.I).strip()
                if rest:
                    rep.add("W003", "error", step_id, child,
                            f"field '{k}' holds a literal value ({redact(rest)}) instead of a secret reference",
                            "Store it in the platform's secret store and write {{secrets.NAME}} here.")
                    continue
            scan_secrets(v, child, step_id, rep)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            scan_secrets(v, f"{path}[{i}]", step_id, rep)
    elif isinstance(node, str):
        text = SECRET_REF.sub("", node)
        for name, pat in CREDENTIAL_PATTERNS:
            m = pat.search(text)
            if m:
                if name == "secret_in_query" and "{{" in m.group(2):
                    continue
                rep.add("W003", "error", step_id, path,
                        f"value looks like a credential ({name}: {redact(m.group(0))})",
                        "Remove it, rotate it (it is now in a file), and reference a secret store entry.")
                break


def find_cycles(graph):
    """Return list of cycles (each a list of ids). Simple DFS, enough for design-size graphs."""
    cycles, state, stack = [], {}, []

    def dfs(n):
        state[n] = 1
        stack.append(n)
        for m in graph.get(n, []):
            if m not in graph:
                continue
            if state.get(m) == 1:
                cycles.append(stack[stack.index(m):] + [m])
            elif state.get(m) is None:
                dfs(m)
        stack.pop()
        state[n] = 2

    for n in sorted(graph):
        if state.get(n) is None:
            dfs(n)
    return cycles


def loop_body_ids(steps_by_id, loop_id):
    body = steps_by_id[loop_id].get("body")
    seen, todo = set(), [b for b in as_list(body) if isinstance(b, str)]
    while todo:
        n = todo.pop()
        if n in seen or n == loop_id or n not in steps_by_id:
            continue
        seen.add(n)
        todo.extend(next_ids(steps_by_id[n]))
    return seen


def validate(spec):
    rep = Report()
    if not isinstance(spec, dict):
        rep.add("W000", "error", None, "$", "spec root must be a JSON object", "Wrap the spec in {...}.")
        return rep, 0
    steps = spec.get("steps")
    if not isinstance(steps, list) or not steps:
        rep.add("W000", "error", None, "steps", "spec has no steps list", "Add a non-empty 'steps' array.")
        return rep, 0
    trigger = spec.get("trigger")
    defaults = spec.get("defaults") if isinstance(spec.get("defaults"), dict) else {}
    default_on_error = defaults.get("on_error") if isinstance(defaults.get("on_error"), dict) else None

    if not spec.get("owner"):
        rep.add("W012", "warning", None, "owner", "no owner named; nobody is paged when it fails",
                "Add 'owner' (a person or on-call alias) and 'alert_channel'.")
    if not spec.get("alert_channel"):
        rep.add("W012", "warning", None, "alert_channel", "no alert channel; failures stay in a log nobody reads",
                "Add 'alert_channel'.")

    # trigger
    entry = []
    if not isinstance(trigger, dict):
        rep.add("W000", "error", None, "trigger", "spec has no trigger object", "Add a 'trigger' with a type and 'next'.")
    else:
        ttype = trigger.get("type")
        if ttype not in TRIGGER_TYPES:
            rep.add("W000", "error", None, "trigger.type",
                    f"trigger type must be one of {sorted(TRIGGER_TYPES)}", "Set trigger.type.")
        entry = [n for n in as_list(trigger.get("next")) if isinstance(n, str)]
        if not entry:
            rep.add("W000", "error", None, "trigger.next", "trigger does not point at a first step", "Set trigger.next.")
        if not trigger.get("dedupe_key"):
            rep.add("W009", "warning", None, "trigger.dedupe_key",
                    "no dedupe key: senders deliver at least once, so duplicates will run the workflow twice",
                    "Add trigger.dedupe_key built from the event id, e.g. {{trigger.body.event_id}}.")
        if ttype == "webhook" and not trigger.get("verify"):
            rep.add("W015", "warning", None, "trigger.verify",
                    "webhook trigger does not verify the sender; anyone who finds the URL can start it",
                    "Set trigger.verify to 'hmac_signature' or 'shared_secret_header' and keep the secret in the store.")
        if ttype in ("poll", "schedule") and not trigger.get("cursor") and ttype == "poll":
            rep.add("W017", "warning", None, "trigger.cursor",
                    "polling trigger has no cursor/overlap window; records can be missed or read twice",
                    "Add trigger.cursor (field) and an overlap window, then rely on dedupe_key.")
        scan_secrets(trigger, "trigger", "trigger", rep)

    steps_by_id, order = {}, []
    for i, s in enumerate(steps):
        if not isinstance(s, dict) or not isinstance(s.get("id"), str) or not s.get("id"):
            rep.add("W000", "error", None, f"steps[{i}]", "step must be an object with a string 'id'", "Give every step a unique id.")
            continue
        if s["id"] in steps_by_id:
            rep.add("W007", "error", s["id"], f"steps[{i}].id", "duplicate step id", "Make ids unique.")
            continue
        steps_by_id[s["id"]] = s
        order.append(s["id"])
        if s.get("type") not in STEP_TYPES:
            rep.add("W000", "error", s["id"], f"steps[{i}].type",
                    f"step type must be one of {sorted(STEP_TYPES)}", "Set step.type.")

    graph = {}
    for sid in order:
        graph[sid] = next_ids(steps_by_id[sid])
        for target in graph[sid]:
            if target not in steps_by_id:
                rep.add("W006", "error", sid, "next", f"points at unknown step '{target}'", "Fix the id or remove the reference.")

    # reachability
    seen, todo = set(), [e for e in entry if e in steps_by_id]
    while todo:
        n = todo.pop()
        if n in seen:
            continue
        seen.add(n)
        todo.extend(t for t in graph.get(n, []) if t in steps_by_id)
    for sid in order:
        if sid not in seen:
            rep.add("W005", "error", sid, "id", "step is unreachable from the trigger and will never run",
                    "Connect it from a reachable step or delete it.")

    # cycles and loops
    for cyc in find_cycles(graph):
        bounded = False
        for n in set(cyc):
            st = steps_by_id.get(n, {})
            lp = st.get("loop") if isinstance(st.get("loop"), dict) else {}
            if st.get("type") == "loop" and isinstance(lp.get("max_iterations"), int) and lp["max_iterations"] > 0:
                bounded = True
        if not bounded:
            rep.add("W002", "error", cyc[0], "next",
                    "cycle " + " -> ".join(cyc) + " has no loop step with max_iterations; it can run forever",
                    "Route the cycle through a loop step with loop.max_iterations and loop.exit_when.")

    loop_bodies = {}
    for sid in order:
        st = steps_by_id[sid]
        if st.get("type") != "loop":
            continue
        lp = st.get("loop") if isinstance(st.get("loop"), dict) else {}
        mi = lp.get("max_iterations")
        if not isinstance(mi, int) or isinstance(mi, bool) or mi <= 0:
            rep.add("W002", "error", sid, "loop.max_iterations", "loop has no positive integer max_iterations",
                    "Set loop.max_iterations to a hard cap above the largest legitimate batch.")
        elif mi > MAX_LOOP_ITERATIONS_WARN:
            rep.add("W002", "warning", sid, "loop.max_iterations",
                    f"max_iterations {mi} is above {MAX_LOOP_ITERATIONS_WARN}; check for a missing filter",
                    "Lower the cap or add a filter before the loop.")
        if not lp.get("exit_when") and not st.get("over"):
            rep.add("W002", "error", sid, "loop.exit_when",
                    "loop has neither a list to iterate ('over') nor an exit condition",
                    "Set 'over' (a bounded list) or loop.exit_when.")
        if not st.get("body"):
            rep.add("W002", "error", sid, "body", "loop has no body step", "Set 'body' to the first step of the loop.")
        elif all(b in steps_by_id for b in as_list(st.get("body")) if isinstance(b, str)):
            loop_bodies[sid] = loop_body_ids(steps_by_id, sid)

    in_loop = {}
    for lid, ids in loop_bodies.items():
        for n in ids:
            in_loop.setdefault(n, lid)

    # per-step checks
    workflow_has_dlq = bool(isinstance(spec.get("dead_letter"), dict) and spec["dead_letter"].get("destination"))
    for sid in order:
        st = steps_by_id[sid]
        scan_secrets({k: v for k, v in st.items() if k not in ("id",)}, f"steps.{sid}", sid, rep)
        stype = st.get("type")
        oe = st.get("on_error") if isinstance(st.get("on_error"), dict) else None
        effective = oe or default_on_error
        write = stype == "action" and is_write(st)

        if stype in ("action", "transform", "loop") and not effective:
            rep.add("W001", "error" if write or stype == "action" else "warning", sid, "on_error",
                    "step has no error handling; a failure here either stops silently or is ignored by the platform",
                    "Add on_error with retry (if the failure can be transient) and an 'then' of dead_letter, alert_stop or fallback.")
        if effective:
            retry = effective.get("retry") if isinstance(effective.get("retry"), dict) else None
            then = effective.get("then")
            if retry is not None:
                ma = retry.get("max_attempts")
                if not isinstance(ma, int) or isinstance(ma, bool) or ma < 1:
                    rep.add("W008", "error", sid, "on_error.retry.max_attempts",
                            "retry has no positive integer max_attempts (unbounded retry)", "Set max_attempts to 3-6.")
                elif ma > MAX_RETRY_ATTEMPTS:
                    rep.add("W008", "error", sid, "on_error.retry.max_attempts",
                            f"max_attempts {ma} is above {MAX_RETRY_ATTEMPTS}", "Lower it; use the dead letter store for the rest.")
                if retry.get("backoff") not in ("exponential", "fixed", "exponential_jitter"):
                    rep.add("W008", "warning", sid, "on_error.retry.backoff",
                            "retry backoff is missing or unknown; immediate retries hammer a failing service",
                            "Set backoff to exponential_jitter.")
                if write and ma and ma > 1 and not st.get("idempotency_key"):
                    rep.add("W004", "error", sid, "idempotency_key",
                            "write step retries but has no idempotency key, so a retry after a lost response writes twice",
                            "Add idempotency_key derived from the event.")
            if then in EXHAUSTED_SILENT:
                rep.add("W010", "error" if write else "warning", sid, "on_error.then",
                        f"'{then}' discards the failure with no trace", "Use dead_letter or alert_stop.")
            elif then not in EXHAUSTED_OK:
                rep.add("W010", "error", sid, "on_error.then",
                        "on_error has no valid 'then' (dead_letter, alert_stop or fallback); behaviour after the last retry is undefined",
                        "Set 'then'.")
            elif then == "dead_letter" and not workflow_has_dlq:
                rep.add("W010", "error", sid, "on_error.then",
                        "step dead-letters but the spec has no dead_letter.destination", "Add a top-level dead_letter object.")
            elif then == "fallback" and not isinstance(effective.get("fallback_step"), str):
                rep.add("W010", "error", sid, "on_error.fallback_step", "'then' is fallback but no fallback_step is named",
                        "Name a fallback_step.")

        if stype == "action":
            if write_unknown(st):
                rep.add("W013", "warning", sid, "kind", "cannot tell whether this action writes; the write checks are skipped",
                        "Set kind to 'read' or 'write'.")
            if write:
                key = st.get("idempotency_key")
                if not isinstance(key, str) or not key.strip():
                    if not st.get("naturally_idempotent"):
                        rep.add("W004", "error", sid, "idempotency_key",
                                "write action has no idempotency key; a duplicate event or retry will repeat the write",
                                "Add idempotency_key built from event data, or set naturally_idempotent with a note if the target upserts by key.")
                elif "{{" not in key:
                    rep.add("W004", "warning", sid, "idempotency_key",
                            "idempotency key is a constant, so every run after the first is treated as a duplicate",
                            "Build it from the event id, e.g. {{trigger.body.id}}-create-invoice.")
                elif sid in in_loop and not re.search(r"\{\{[^}]*(item|loop|index)[^}]*\}\}", key, re.I):
                    rep.add("W014", "warning", sid, "idempotency_key",
                            f"write runs inside loop '{in_loop[sid]}' but the key does not include the loop item; all iterations share one key",
                            "Add {{item.id}} or {{loop.index}} to the key.")
            if not st.get("timeout_seconds"):
                rep.add("W016", "warning", sid, "timeout_seconds", "no timeout; a hung call blocks the run without failing",
                        "Set timeout_seconds (10-30 for most APIs).")
            if not st.get("rate_limit") and not spec.get("concurrency"):
                rep.add("W011", "warning", sid, "rate_limit",
                        "no rate limit or workflow concurrency cap; a burst of events can exhaust the downstream quota",
                        "Add rate_limit {max_per_minute} on the step or concurrency at the top level.")
    return rep, len(order)


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"tool": "validate_workflow", "ok": False, "fatal": "usage: validate_workflow.py <spec.json>"}))
        return 2
    path = argv[1]
    result = {"tool": "validate_workflow", "spec": os.path.basename(path)}
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as exc:
        result.update(ok=False, fatal=f"cannot read file: {exc.strerror}")
        print(json.dumps(result))
        return 2
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        result.update(ok=False, fatal="file is not UTF-8")
        print(json.dumps(result))
        return 2
    if not text.strip():
        result.update(ok=False, fatal="file is empty")
        print(json.dumps(result))
        return 2
    try:
        spec = json.loads(text)
    except ValueError as exc:
        result.update(ok=False, fatal=f"not valid JSON: {exc}")
        print(json.dumps(result))
        return 2
    rep, n_steps = validate(spec)
    order = {"error": 0, "warning": 1}
    rep.findings.sort(key=lambda f: (order[f["severity"]], f["rule"], str(f["step"]), f["path"]))
    errors = sum(1 for f in rep.findings if f["severity"] == "error")
    warnings = len(rep.findings) - errors
    result.update(ok=errors == 0, summary={"errors": errors, "warnings": warnings, "steps": n_steps},
                  findings=rep.findings)
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    sys.exit(main(sys.argv))
