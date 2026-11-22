#!/usr/bin/env python3
"""Validate a debugging ledger (Markdown or JSON) and print a strict JSON report.

    python ledger_check.py <ledger.md|ledger.json>

Reads the one file given; writes nothing; no network. Standard library only.
Output: one JSON object on stdout (no NaN, no trailing text).
Exit codes: 0 = no errors (warnings allowed), 1 = at least one error,
2 = usage problem (missing, empty or unparseable file; message in JSON "error").

Ledger format: see references/ledger-format.md. Short version:
  reproduction  : command, reproduced (yes/no), minimised (text), bisect (text)
  hypotheses[]  : id, statement, prediction, status
  experiments[] : id, hypothesis, variables_changed (list), result, outcome
  root_cause    : text (optional: hypothesis id)
  regression_test: id, path, failed_before_fix (yes/no), failure_output
  fix           : description, test (id)
Markdown uses "## Section" and "### H1" / "### E1" headings with "- key: value"
bullets; the order of the "## Regression test" and "## Fix" headings is the
order in which they were recorded.
"""
import json
import os
import re
import sys

DECISIVE = {"confirmed", "refuted"}  # outcomes that settle a hypothesis
YES = {"yes", "y", "true", "1", "fail", "failed", "failing"}
NO = {"no", "n", "false", "0", "pass", "passed", "passing"}
# Words that turn a root-cause statement back into a guess.
HEDGES = re.compile(r"\b(probably|maybe|perhaps|might|possibly|likely|seems? to|i think|i guess)\b", re.I)
MIN_ROOT_CAUSE_CHARS = 25  # shorter than this cannot name a mechanism and a location
MIN_FAILURE_OUTPUT_CHARS = 8  # "failed" alone is not evidence; an assertion line or message is

ALIASES = {
    "variables_changed": "variables_changed", "changed": "variables_changed", "variable": "variables_changed",
    "variables": "variables_changed", "changes": "variables_changed",
    "failed_before_fix": "failed_before_fix", "failed_before": "failed_before_fix", "fails_before_fix": "failed_before_fix",
    "failure_output": "failure_output", "output": "failure_output", "failing_output": "failure_output",
    "hypothesis": "hypothesis", "tests_hypothesis": "hypothesis",
}
SECTION_ALIASES = {
    "reproduction": "reproduction", "repro": "reproduction",
    "hypotheses": "hypotheses", "hypothesis ledger": "hypotheses", "hypothesis": "hypotheses",
    "experiments": "experiments", "experiment": "experiments",
    "root cause": "root_cause", "root cause statement": "root_cause",
    "regression test": "regression_test", "regression tests": "regression_test", "test": "regression_test", "tests": "regression_test",
    "fix": "fix",
}


class LedgerError(Exception):
    pass


def norm_key(raw):
    key = re.sub(r"[\s\-]+", "_", raw.strip().lower())
    return ALIASES.get(key, key)


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).split(";") if p.strip()]


def as_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower().rstrip(".")
    if text in YES:
        return True
    if text in NO:
        return False
    return None


# ---------------------------------------------------------------- parsing

def parse_markdown(text):
    ledger = {"order": []}
    section = None
    item = None
    last_key = None
    target = None  # the dict currently receiving key/value bullets
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if level <= 2:
                canon = SECTION_ALIASES.get(re.sub(r"\s+", " ", title.lower()))
                section, item, last_key = canon, None, None
                if canon:
                    ledger["order"].append(canon)
                    if canon in ("reproduction", "root_cause", "regression_test", "fix"):
                        target = ledger.setdefault(canon, {})
                    else:
                        ledger.setdefault(canon, [])
                        target = None
                else:
                    target = None
                continue
            if section in ("hypotheses", "experiments", "regression_test"):
                ident = re.split(r"[\s:.\-]", title, maxsplit=1)[0]
                item = {"id": ident}
                rest = title[len(ident):].lstrip(" :.-")
                if rest:
                    item["title"] = rest
                if section == "regression_test":
                    ledger.setdefault("regression_tests", []).append(item)
                else:
                    ledger[section].append(item)
                target, last_key = item, None
            continue
        sub = re.match(r"^\s{2,}[-*]\s+(.*)$", line)
        if sub and target is not None and last_key:
            cur = target.get(last_key)
            if not isinstance(cur, list):
                cur = [cur] if cur else []
            cur.append(sub.group(1).strip())
            target[last_key] = cur
            continue
        kv = re.match(r"^\s*[-*]?\s*([A-Za-z][A-Za-z _\-]{0,40}?)\s*:\s*(.*)$", line)
        if kv and section != "root_cause":
            if target is None:
                continue
            last_key = norm_key(kv.group(1))
            target[last_key] = kv.group(2).strip()
            continue
        if section == "root_cause" and target is not None:
            body = re.sub(r"^\s*[-*]\s+", "", line).strip()
            kv2 = re.match(r"^(hypothesis)\s*:\s*(.*)$", body, re.I)
            if kv2:
                target["hypothesis"] = kv2.group(2).strip()
            else:
                target["text"] = (target.get("text", "") + " " + body).strip()
    return ledger


def load(path):
    if not os.path.isfile(path):
        raise LedgerError("file not found: " + path)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise LedgerError("cannot read as UTF-8 text: %s" % exc)
    if not text.strip():
        raise LedgerError("file is empty: " + path)
    if path.lower().endswith(".json") or text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise LedgerError("invalid JSON: %s" % exc)
        if not isinstance(data, dict):
            raise LedgerError("JSON ledger must be an object")
        data["order"] = [k for k in data.keys()]
        return data
    return parse_markdown(text)


# ---------------------------------------------------------------- checks

def add(findings, severity, code, where, message):
    findings.append({"severity": severity, "code": code, "where": where, "message": message})


def as_dict_list(value):
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def check(ledger):
    findings = []
    hyps = as_dict_list(ledger.get("hypotheses"))
    exps = as_dict_list(ledger.get("experiments"))
    repro = ledger.get("reproduction") if isinstance(ledger.get("reproduction"), dict) else {}
    root = ledger.get("root_cause")
    if isinstance(root, str):
        root = {"text": root}
    root = root if isinstance(root, dict) else {}
    tests = as_dict_list(ledger.get("regression_tests"))
    rt = ledger.get("regression_test")
    if isinstance(rt, dict) and rt:
        tests.append(rt)
    elif isinstance(rt, list):
        tests.extend(as_dict_list(rt))
    fix = ledger.get("fix") if isinstance(ledger.get("fix"), dict) else None
    order = ledger.get("order", [])

    # reproduction
    if not repro:
        add(findings, "error", "no_reproduction", "reproduction", "No reproduction recorded. A bug that cannot be triggered on demand cannot be tested.")
    else:
        if not str(repro.get("command", "")).strip():
            add(findings, "error", "no_reproduction", "reproduction", "Reproduction has no command or steps.")
        if as_bool(repro.get("reproduced")) is not True:
            add(findings, "error", "not_reproduced", "reproduction", "'reproduced' is not yes. Do not hypothesise on a bug you have not seen fail.")
        if not str(repro.get("minimised", "")).strip():
            add(findings, "warning", "no_minimisation", "reproduction", "No minimised case recorded.")
        if not str(repro.get("bisect", "")).strip():
            add(findings, "warning", "no_bisect", "reproduction", "No bisect (time, input or code) recorded.")

    # hypotheses
    seen, hyp_by_id = set(), {}
    for i, h in enumerate(hyps):
        hid = str(h.get("id") or "").strip() or "H?%d" % (i + 1)
        if hid in seen:
            add(findings, "error", "duplicate_id", hid, "Hypothesis id used twice.")
        seen.add(hid)
        hyp_by_id[hid] = h
        if not str(h.get("statement") or h.get("title") or "").strip():
            add(findings, "error", "no_statement", hid, "Hypothesis has no statement.")
        if not str(h.get("prediction", "")).strip():
            add(findings, "error", "no_prediction", hid, "No prediction. A hypothesis that forbids no outcome cannot be refuted.")
    if not hyps:
        add(findings, "error", "no_hypotheses", "hypotheses", "No hypotheses recorded.")

    # experiments
    by_hyp = {}
    multi, no_var = [], []
    for i, e in enumerate(exps):
        eid = str(e.get("id") or "").strip() or "E?%d" % (i + 1)
        ref = str(e.get("hypothesis", "")).strip()
        outcome = str(e.get("outcome", "")).strip().lower()
        if not ref or ref not in hyp_by_id:
            add(findings, "error", "experiment_unknown_hypothesis", eid, "Experiment names hypothesis %r, which is not in the ledger." % ref)
        variables = as_list(e.get("variables_changed"))
        if ref in hyp_by_id:
            # A run that changed zero or several variables cannot settle anything.
            by_hyp.setdefault(ref, []).append(outcome if len(variables) == 1 else "invalid")
        if not variables:
            no_var.append(eid)
            add(findings, "error", "experiment_no_variable", eid, "No variable recorded as changed. Name the one thing this run changed.")
        elif len(variables) > 1:
            multi.append(eid)
            add(findings, "error", "multi_variable_experiment", eid, "%d variables changed (%s). One experiment changes one variable." % (len(variables), "; ".join(variables)))
        else:
            if re.search(r"\band\b|,|&|\bplus\b", re.sub(r"\([^)]*\)", "", variables[0]), re.I):
                add(findings, "warning", "possible_multi_variable", eid, "The single variable %r reads like several. Split it or reword it." % variables[0])
        if not str(e.get("result", "")).strip():
            add(findings, "error", "experiment_no_result", eid, "No observed result recorded.")
        if outcome not in DECISIVE | {"inconclusive"}:
            add(findings, "error", "experiment_bad_outcome", eid, "outcome must be confirmed, refuted or inconclusive; got %r." % outcome)

    untested = []
    for hid, h in hyp_by_id.items():
        outcomes = by_hyp.get(hid, [])
        status = str(h.get("status", "open")).strip().lower() or "open"
        decisive = [o for o in outcomes if o in DECISIVE]
        if status == "abandoned":
            if not str(h.get("reason", "")).strip():
                add(findings, "warning", "abandoned_without_reason", hid, "Abandoned with no reason recorded.")
            continue
        if not decisive:
            untested.append(hid)
            why = "no experiment" if not outcomes else "only inconclusive or multi-variable experiments"
            add(findings, "error", "untested_hypothesis", hid, "Hypothesis is untested (%s)." % why)
        if status in DECISIVE and status not in decisive:
            add(findings, "error", "status_unsupported", hid, "Status is %s but no valid single-variable experiment has that outcome." % status)
        if status == "open" and decisive:
            add(findings, "warning", "status_stale", hid, "Status is open but an experiment already %s it." % decisive[-1])
    confirmed = [hid for hid, h in hyp_by_id.items() if "confirmed" in by_hyp.get(hid, [])]

    # root cause and fix
    root_text = str(root.get("text", "")).strip()
    if fix is not None and not root_text:
        add(findings, "error", "fix_without_root_cause", "root_cause", "A fix is recorded but there is no root cause statement.")
    if root_text:
        if len(root_text) < MIN_ROOT_CAUSE_CHARS:
            add(findings, "error", "root_cause_too_short", "root_cause", "Root cause is under %d characters; state the mechanism and where it happens." % MIN_ROOT_CAUSE_CHARS)
        if HEDGES.search(root_text):
            add(findings, "warning", "root_cause_hedged", "root_cause", "Root cause contains a hedge word; a root cause is something an experiment confirmed.")
        rh = str(root.get("hypothesis", "")).strip()
        if rh and rh not in confirmed:
            add(findings, "error", "root_cause_not_confirmed", "root_cause", "Root cause cites %s, which no experiment confirmed." % rh)
        elif not rh and not confirmed:
            add(findings, "error", "root_cause_not_confirmed", "root_cause", "No hypothesis has a confirming experiment, so the root cause is unsupported.")

    fix_checked = False
    if fix is not None:
        fix_checked = True
        refid = str(fix.get("test", "")).strip()
        chosen = None
        if refid:
            chosen = next((t for t in tests if str(t.get("id", "")).strip() == refid), None)
            if chosen is None:
                add(findings, "error", "fix_unknown_test", "fix", "Fix cites test %r, which is not in the ledger." % refid)
        elif len(tests) == 1:
            chosen = tests[0]
        elif len(tests) > 1:
            add(findings, "error", "fix_unknown_test", "fix", "Several tests recorded; the fix must name which one it makes pass.")
        if not tests:
            add(findings, "error", "fix_without_failing_test", "fix", "A fix is recorded but no regression test is.")
        elif chosen is not None:
            tid = str(chosen.get("id", "") or chosen.get("path", "") or "test")
            if as_bool(chosen.get("failed_before_fix")) is not True:
                add(findings, "error", "fix_without_failing_test", tid, "The test is not recorded as failing before the fix.")
            elif len(str(chosen.get("failure_output", "")).strip()) < MIN_FAILURE_OUTPUT_CHARS:
                add(findings, "error", "fix_without_failing_test", tid, "No failure output pasted from the pre-fix run; 'it failed' is not evidence.")
            seq_t, seq_f = chosen.get("seq"), fix.get("seq")
            if isinstance(seq_t, (int, float)) and isinstance(seq_f, (int, float)) and not isinstance(seq_t, bool) and seq_t >= seq_f:
                add(findings, "error", "fix_before_test", tid, "seq says the fix (%s) was recorded before the test (%s)." % (seq_f, seq_t))
            elif "fix" in order and "regression_test" in order and order.index("fix") < order.index("regression_test"):
                add(findings, "error", "fix_before_test", tid, "The Fix section comes before the Regression test section.")
            if as_bool(fix.get("test_passes_after")) is False:
                add(findings, "error", "fix_test_still_failing", tid, "Fix records the test as still failing.")
        if not str(fix.get("description", "")).strip():
            add(findings, "warning", "fix_no_description", "fix", "Fix has no description.")
    elif tests:
        add(findings, "warning", "test_without_fix", "fix", "A regression test exists but no fix is recorded yet.")

    errors = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    return {
        "ok": not errors,
        "counts": {"hypotheses": len(hyps), "experiments": len(exps), "tests": len(tests), "errors": len(errors), "warnings": len(warnings)},
        "untested_hypotheses": untested,
        "multi_variable_experiments": multi,
        "experiments_without_variable": no_var,
        "fix_recorded": fix_checked,
        "fix_without_failing_test": any(f["code"] in ("fix_without_failing_test", "fix_before_test", "fix_unknown_test") for f in errors),
        "findings": findings,
    }


def emit(obj):
    # ensure_ascii=True keeps the output pure ASCII, so no console code page can break it.
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=True, allow_nan=False) + "\n")


def main(argv):
    if len(argv) != 1 or argv[0] in ("-h", "--help"):
        sys.stderr.write("usage: ledger_check.py <ledger.md|ledger.json>\n")
        emit({"ok": False, "error": "usage: ledger_check.py <ledger.md|ledger.json>"})
        return 2
    try:
        ledger = load(argv[0])
    except LedgerError as exc:
        emit({"ok": False, "error": str(exc)})
        return 2
    report = check(ledger)
    report["file"] = os.path.basename(argv[0])
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
