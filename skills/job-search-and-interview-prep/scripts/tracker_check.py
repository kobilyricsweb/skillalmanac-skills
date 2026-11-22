#!/usr/bin/env python3
"""Validate a job-search tracker and print a weekly plan as strict JSON.

Usage:
    python tracker_check.py <tracker.csv|tracker.json> [--stories <stories.csv|stories.json>]
                            [--today YYYY-MM-DD] [--stale-days N] [--new-apps N]

Reads: the tracker file (and the optional stories file). Writes: nothing but
stdout. No network. Python 3.9+ standard library only.

Tracker formats
  CSV   one row per application. Header row required, case-insensitive.
        Required columns: company, role, status.
        Optional: applied_date, last_contact_date, next_action, next_action_date,
        interview_date, source, contact, notes. Extra columns are ignored.
  JSON  either a list of application objects, or an object with the key
        "applications" (list) and optionally "stories" (list).
Stories (inside the JSON tracker, or via --stories as CSV or JSON list)
  Fields: id, title, situation, task, action, result, source.

Dates are ISO YYYY-MM-DD. Exit codes: 0 no warn/error issue, 1 at least one
warn or error issue (the JSON is still printed), 2 unusable input or arguments
(a JSON error object is printed on stdout and a message on stderr).
"""
import argparse
import csv
import datetime
import io
import json
import re
import sys
import unicodedata

SCHEMA_VERSION = 1

# Days without contact before an active application counts as stale. 10 days is
# about two working weeks, long enough not to nag a recruiter, short enough that
# a silent application is still recoverable. A working value, not a measured one.
DEFAULT_STALE_DAYS = 10
# Applications per week the plan asks the user to submit. 5 keeps each one
# tailored; the user overrides it with --new-apps.
DEFAULT_NEW_APPS = 5
# A story bank needs breadth: about six stories cover the usual behavioural
# themes (conflict, failure, leadership, deadline, ambiguity, influence).
MIN_COMPLETE_STORIES = 6
# A component with fewer words than this cannot hold a usable situation/result.
MIN_COMPONENT_WORDS = 3
# Window for "due this week" and interview preparation.
WEEK_DAYS = 7

# Statuses. Active ones are checked for staleness; terminal ones are exempt from
# next-action checks.
ACTIVE = ("applied", "screening", "interviewing", "offer")
PRE_APPLY = ("wishlist", "preparing")
TERMINAL = ("accepted", "rejected", "withdrawn", "closed")
STATUSES = PRE_APPLY + ACTIVE + TERMINAL

COMPONENTS = ("situation", "task", "action", "result")
PLACEHOLDERS = {"", "tbd", "todo", "to do", "n/a", "na", "none", "?", "??", "...", "-", "xxx", "fill in", "later"}
COMPANY_SUFFIXES = {"inc", "llc", "ltd", "corp", "corporation", "co", "company", "gmbh", "plc", "sa", "ag", "limited", "lp"}
DATE_FIELDS = ("applied_date", "last_contact_date", "next_action_date", "interview_date")
REQUIRED_COLUMNS = ("company", "role", "status")


class InputError(Exception):
    """Raised for unusable input; main() turns it into exit code 2."""


def parse_date(text):
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()):
        return None
    try:
        return datetime.date.fromisoformat(text.strip())
    except ValueError:
        return None


def norm_company(name):
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode("ascii").lower()
    text = text.replace("&", " and ")
    tokens = re.sub(r"[^a-z0-9]+", " ", text).split()
    while tokens and tokens[-1] in COMPANY_SUFFIXES and len(tokens) > 1:
        tokens.pop()
    return " ".join(tokens)


def norm_text(value):
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def clean(value):
    return "" if value is None else str(value).strip()


def read_text(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise InputError("cannot read %s: %s" % (path, exc.strerror or exc))
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("%s is not UTF-8 text; re-save it as UTF-8" % path)
    if not text.strip():
        raise InputError("%s is empty" % path)
    return text


def load_rows_csv(text, path, required):
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise InputError("%s has no header row" % path)
    names = [(h or "").strip().lower() for h in reader.fieldnames]
    missing = [c for c in required if c not in names]
    if missing:
        raise InputError("%s is missing required column(s): %s" % (path, ", ".join(missing)))
    rows = []
    for raw in reader:
        row = {}
        for key, value in raw.items():
            if key is None:
                continue
            row[key.strip().lower()] = clean(value)
        if any(row.values()):
            rows.append(row)
    return rows


def load_json(text, path):
    try:
        return json.loads(text)
    except ValueError as exc:
        raise InputError("%s is not valid JSON: %s" % (path, exc))


def as_rows(items, path, label):
    if not isinstance(items, list):
        raise InputError("%s: %s must be a list of objects" % (path, label))
    rows = []
    for item in items:
        if not isinstance(item, dict):
            raise InputError("%s: every entry in %s must be an object" % (path, label))
        rows.append({str(k).strip().lower(): clean(v) for k, v in item.items()})
    return rows


def load_tracker(path):
    text = read_text(path)
    stories = None
    if path.lower().endswith(".json") or text.lstrip().startswith(("{", "[")):
        data = load_json(text, path)
        if isinstance(data, dict):
            if "applications" not in data:
                raise InputError('%s: JSON object needs an "applications" list' % path)
            apps = as_rows(data["applications"], path, "applications")
            if "stories" in data:
                stories = as_rows(data["stories"], path, "stories")
        else:
            apps = as_rows(data, path, "the tracker")
    else:
        apps = load_rows_csv(text, path, REQUIRED_COLUMNS)
    if not apps:
        raise InputError("%s has no application rows" % path)
    return apps, stories


def load_stories(path):
    text = read_text(path)
    if path.lower().endswith(".json") or text.lstrip().startswith(("{", "[")):
        data = load_json(text, path)
        if isinstance(data, dict):
            data = data.get("stories")
        return as_rows(data, path, "stories")
    return load_rows_csv(text, path, ())


def issue(code, severity, subject, detail, fix):
    return {"code": code, "severity": severity, "subject": subject, "detail": detail, "fix": fix}


def label(app, index):
    company = app.get("company") or "(no company)"
    role = app.get("role") or "(no role)"
    return "row %d: %s, %s" % (index, company, role)


def check_applications(apps, today, stale_days):
    issues = []
    plan_facts = []  # per-app derived facts used by the plan
    for i, app in enumerate(apps, start=1):
        subject = label(app, i)
        for field in ("company", "role"):
            if not app.get(field):
                issues.append(issue("missing_field", "error", subject, "%s is empty" % field,
                                    "fill in %s" % field))
        status = app.get("status", "").lower().replace(" ", "-")
        if status not in STATUSES:
            issues.append(issue("bad_status", "error", subject,
                                "status %r is not one of: %s" % (app.get("status", ""), ", ".join(STATUSES)),
                                "use one of the allowed status words"))
            status = ""
        dates = {}
        for field in DATE_FIELDS:
            raw = app.get(field, "")
            if not raw:
                dates[field] = None
                continue
            parsed = parse_date(raw)
            if parsed is None:
                issues.append(issue("bad_date", "error", subject,
                                    "%s %r is not a valid YYYY-MM-DD date" % (field, raw),
                                    "write the date as YYYY-MM-DD"))
            elif field in ("applied_date", "last_contact_date") and parsed > today:
                issues.append(issue("future_date", "error", subject,
                                    "%s %s is after today (%s)" % (field, raw, today.isoformat()),
                                    "an application or contact cannot be dated in the future"))
                parsed = None
            dates[field] = parsed
        next_action = app.get("next_action", "")
        nad = dates.get("next_action_date")
        scheduled = bool(next_action) and nad is not None and nad >= today

        days_silent = None
        if status in ACTIVE:
            anchor = dates.get("last_contact_date") or dates.get("applied_date")
            if anchor is None:
                issues.append(issue("missing_date", "warn", subject,
                                    "active application has neither applied_date nor last_contact_date, so staleness cannot be measured",
                                    "add applied_date"))
            else:
                days_silent = (today - anchor).days
                if days_silent > stale_days and not scheduled:
                    issues.append(issue("stale_application", "warn", subject,
                                        "%d days since last contact or application, more than %d, and no follow-up is scheduled"
                                        % (days_silent, stale_days),
                                        "send a follow-up or set a dated next_action, or move the status to withdrawn or closed"))
        if status in PRE_APPLY + ACTIVE and not next_action:
            issues.append(issue("missing_next_action", "warn", subject,
                                "status %s but next_action is empty" % status,
                                "write one concrete next action with a date"))
        if next_action and nad is not None and nad < today and status in PRE_APPLY + ACTIVE:
            issues.append(issue("overdue_next_action", "warn", subject,
                                "next_action_date %s is %d days past" % (nad.isoformat(), (today - nad).days),
                                "do it, or move the date"))
        plan_facts.append({"app": app, "index": i, "status": status, "dates": dates,
                           "days_silent": days_silent, "scheduled": scheduled})
    return issues, plan_facts


def check_duplicates(apps):
    groups = {}
    for i, app in enumerate(apps, start=1):
        key = norm_company(app.get("company", ""))
        if key:
            groups.setdefault(key, []).append((i, app))
    issues = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) < 2:
            continue
        rows = ", ".join(str(i) for i, _ in members)
        roles = {}
        for i, app in members:
            roles.setdefault(norm_text(app.get("role", "")), []).append(i)
        same_role = [v for v in roles.values() if len(v) > 1]
        names = sorted({app.get("company", "") for _, app in members})
        if same_role:
            issues.append(issue("duplicate_application", "error", "company %s" % " / ".join(names),
                                "rows %s are the same company and the same role" % rows,
                                "merge the rows into one"))
        else:
            issues.append(issue("duplicate_company", "warn", "company %s" % " / ".join(names),
                                "rows %s are different roles at the same company" % rows,
                                "confirm each is a separate role and that recruiters know about your other applications"))
    return issues


def component_state(value):
    text = clean(value)
    if text.lower() in PLACEHOLDERS:
        return "missing"
    if len(text.split()) < MIN_COMPONENT_WORDS:
        return "thin"
    return "ok"


def check_stories(stories):
    issues = []
    complete = 0
    seen_ids = {}
    for i, story in enumerate(stories, start=1):
        sid = story.get("id") or "story-%d" % i
        subject = "story %s%s" % (sid, (" (%s)" % story["title"]) if story.get("title") else "")
        if sid in seen_ids:
            issues.append(issue("duplicate_story_id", "error", subject,
                                "id %s is also used by story %d" % (sid, seen_ids[sid]), "give each story a unique id"))
        seen_ids.setdefault(sid, i)
        missing, thin = [], []
        for comp in COMPONENTS:
            state = component_state(story.get(comp, ""))
            if state == "missing":
                missing.append(comp)
            elif state == "thin":
                thin.append(comp)
        if missing:
            issues.append(issue("story_missing_component", "error", subject,
                                "missing: %s" % ", ".join(missing),
                                "ask the user for the real detail; never invent it"))
        if thin:
            issues.append(issue("story_thin_component", "warn", subject,
                                "under %d words: %s" % (MIN_COMPONENT_WORDS, ", ".join(thin)),
                                "ask the user for one more concrete sentence"))
        if not clean(story.get("source", "")):
            issues.append(issue("story_missing_source", "warn", subject,
                                "no source: which job, project or period this really happened in",
                                "record where and when it happened"))
        if "result" not in missing and not re.search(r"\d", clean(story.get("result", ""))):
            issues.append(issue("story_result_not_quantified", "info", subject,
                                "result has no number", "ask whether any real figure exists; if not, keep it qualitative"))
        if not missing and not thin:
            complete += 1
    return issues, complete


def build_plan(facts, stories_info, today, new_apps, stale_days):
    items = []

    def add(kind, f, action, reason):
        app = f["app"]
        items.append({"kind": kind, "company": app.get("company", ""), "role": app.get("role", ""),
                      "action": action, "reason": reason})

    horizon = today + datetime.timedelta(days=WEEK_DAYS)
    # 1. interview preparation
    prep = [f for f in facts if f["dates"].get("interview_date") and today <= f["dates"]["interview_date"] <= horizon
            and f["status"] in ACTIVE]
    for f in sorted(prep, key=lambda f: (f["dates"]["interview_date"], f["app"].get("company", ""))):
        d = f["dates"]["interview_date"]
        add("interview_prep", f, "prepare for the interview on %s: map 3 to 4 stories to the role, research the company, write questions to ask" % d.isoformat(),
            "interview in %d days" % (d - today).days)
    # 2. stale follow-ups, oldest first
    stale = [f for f in facts if f["days_silent"] is not None and f["status"] in ACTIVE and not f["scheduled"]
             and f["days_silent"] > stale_days]
    for f in sorted(stale, key=lambda f: (-f["days_silent"], f["app"].get("company", ""))):
        add("follow_up", f, "send a short follow-up (see references/outreach-rules.md)", "%d days without contact" % f["days_silent"])
    # 3. overdue actions
    over = [f for f in facts if f["status"] in PRE_APPLY + ACTIVE and f["app"].get("next_action")
            and f["dates"].get("next_action_date") and f["dates"]["next_action_date"] < today]
    for f in sorted(over, key=lambda f: (f["dates"]["next_action_date"], f["app"].get("company", ""))):
        add("overdue_action", f, f["app"]["next_action"], "due %s" % f["dates"]["next_action_date"].isoformat())
    # 4. actions due this week
    due = [f for f in facts if f["status"] in PRE_APPLY + ACTIVE and f["app"].get("next_action")
           and f["dates"].get("next_action_date") and today <= f["dates"]["next_action_date"] <= horizon]
    for f in sorted(due, key=lambda f: (f["dates"]["next_action_date"], f["app"].get("company", ""))):
        add("due_this_week", f, f["app"]["next_action"], "due %s" % f["dates"]["next_action_date"].isoformat())
    # 5. rows that need a next action
    for f in facts:
        if f["status"] in PRE_APPLY + ACTIVE and not f["app"].get("next_action"):
            add("set_next_action", f, "decide and write one dated next action", "no next action recorded")
    # 6. new applications from the pre-apply pile
    pile = [f for f in facts if f["status"] in PRE_APPLY]
    pile.sort(key=lambda f: (0 if f["status"] == "preparing" else 1, f["app"].get("company", "")))
    for f in pile[:max(new_apps, 0)]:
        add("submit_application", f, "finish and submit the application", "status %s, weekly target %d" % (f["status"], new_apps))
    # 7. story bank
    interviewing = any(f["status"] in ("screening", "interviewing") for f in facts)
    if stories_info is not None:
        complete, flagged = stories_info
        if flagged:
            items.append({"kind": "fix_stories", "company": "", "role": "",
                          "action": "complete the %d flagged STAR stor%s with the user's real details" % (flagged, "y" if flagged == 1 else "ies"),
                          "reason": "stories with missing or thin components"})
        if interviewing and complete < MIN_COMPLETE_STORIES:
            items.append({"kind": "build_story_bank", "company": "", "role": "",
                          "action": "add %d more complete STAR stories from real experience" % (MIN_COMPLETE_STORIES - complete),
                          "reason": "interviews in progress and only %d complete stories (target %d)" % (complete, MIN_COMPLETE_STORIES)})
    elif interviewing:
        items.append({"kind": "build_story_bank", "company": "", "role": "",
                      "action": "start a STAR story bank of at least %d stories from real experience" % MIN_COMPLETE_STORIES,
                      "reason": "interviews in progress and no stories file was supplied"})
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank
    return items


def run(args):
    today = parse_date(args.today) if args.today else datetime.date.today()
    if today is None:
        raise InputError("--today must be YYYY-MM-DD")
    if args.stale_days < 1:
        raise InputError("--stale-days must be at least 1")
    apps, embedded = load_tracker(args.tracker)
    stories = embedded
    if args.stories:
        stories = load_stories(args.stories)

    issues, facts = check_applications(apps, today, args.stale_days)
    issues.extend(check_duplicates(apps))
    stories_info = None
    complete = None
    if stories is not None:
        story_issues, complete = check_stories(stories)
        flagged = len({s["subject"] for s in story_issues if s["code"] in ("story_missing_component", "story_thin_component")})
        issues.extend(story_issues)
        stories_info = (complete, flagged)
    interviewing = any(f["status"] in ("screening", "interviewing") for f in facts)
    if stories is not None and interviewing and complete < MIN_COMPLETE_STORIES:
        issues.append(issue("story_bank_thin", "info", "story bank",
                            "%d complete stories, target %d, and interviews are in progress" % (complete, MIN_COMPLETE_STORIES),
                            "add stories from real experience"))

    order = {"error": 0, "warn": 1, "info": 2}
    issues.sort(key=lambda x: (order[x["severity"]], x["code"], x["subject"]))
    counts = {"error": 0, "warn": 0, "info": 0}
    for x in issues:
        counts[x["severity"]] += 1
    by_status = {}
    for f in facts:
        key = f["status"] or "invalid"
        by_status[key] = by_status.get(key, 0) + 1
    report = {
        "schema_version": SCHEMA_VERSION,
        "command": "check",
        "ok": counts["error"] == 0 and counts["warn"] == 0,
        "today": today.isoformat(),
        "params": {"stale_days": args.stale_days, "new_apps": args.new_apps},
        "summary": {
            "applications": len(apps),
            "by_status": {k: by_status[k] for k in sorted(by_status)},
            "stories": None if stories is None else len(stories),
            "complete_stories": complete,
            "issues": counts,
        },
        "issues": issues,
        "weekly_plan": build_plan(facts, stories_info, today, args.new_apps, args.stale_days),
    }
    return report


def emit(obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, sort_keys=False)
    sys.stdout.write(text + "\n")


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser(description="Validate a job-search tracker and print a weekly plan as JSON.")
    parser.add_argument("tracker")
    parser.add_argument("--stories")
    parser.add_argument("--today")
    parser.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    parser.add_argument("--new-apps", type=int, default=DEFAULT_NEW_APPS)
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        if exc.code not in (0, None):
            emit({"schema_version": SCHEMA_VERSION, "command": "check", "ok": False, "error": "bad arguments"})
            return 2
        raise
    try:
        report = run(args)
    except InputError as exc:
        sys.stderr.write("error: %s\n" % exc)
        emit({"schema_version": SCHEMA_VERSION, "command": "check", "ok": False, "error": str(exc)})
        return 2
    emit(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
