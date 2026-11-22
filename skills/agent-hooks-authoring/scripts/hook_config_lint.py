#!/usr/bin/env python3
"""Static check of a Claude Code hooks configuration.

    python hook_config_lint.py <settings.json | hooks.json> [--strict] [--json]

Reads the given settings file and, when a handler's script can be located on
disk relative to the project root, that script's text. Writes nothing and runs
nothing: hooks are never executed by this tool.

Exit codes: 0 = no ERROR (with --strict: no ERROR and no WARN), 1 = findings,
2 = usage error or unreadable file.
"""
import json
import os
import re
import sys

# Event names from the hooks reference this skill was written against.
EVENTS = [
    "SessionStart", "Setup", "UserPromptSubmit", "UserPromptExpansion", "PreToolUse",
    "PermissionRequest", "PermissionDenied", "PostToolUse", "PostToolUseFailure",
    "PostToolBatch", "MessageDisplay", "TaskCreated", "TaskCompleted", "Stop",
    "TeammateIdle", "CwdChanged", "WorktreeCreate", "WorktreeRemove", "Notification",
    "SubagentStart", "SubagentStop", "StopFailure", "InstructionsLoaded", "ConfigChange",
    "DirectoryAdded", "FileChanged", "PreCompact", "PostCompact", "PreModelSwitch",
    "PostModelSwitch", "Elicitation", "ElicitationResult", "SessionEnd",
]
# Events whose matcher is ignored by the harness.
NO_MATCHER = {"UserPromptSubmit", "PostToolBatch", "MessageDisplay", "TaskCreated", "TaskCompleted",
              "Stop", "TeammateIdle", "CwdChanged", "WorktreeCreate", "WorktreeRemove"}
TOOL_EVENTS = {"PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"}
BLOCKING_GUARDS = {"PreToolUse", "UserPromptSubmit", "Stop", "SubagentStop", "PreCompact"}
HANDLER_TYPES = {"command", "http", "mcp_tool", "prompt", "agent"}
KNOWN_TOOLS = ["Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "Read", "Glob", "Grep", "WebFetch", "WebSearch", "Agent", "Task"]
# Timeouts are seconds. One hour is already far beyond any sensible hook, so a
# larger number is almost always a millisecond value written by mistake.
MAX_SANE_TIMEOUT_S = 3600
INTERPRETERS = r"(?:node|python3?|bash|sh|ruby|deno|bun|pwsh|powershell)"
RELATIVE_SCRIPT = re.compile(r"(?:^|\s)(?:%s\s+)?(\.{0,2}/?[\w.-]+(?:/[\w.-]+)+\.(?:js|mjs|cjs|py|sh|rb|ts|ps1))" % INTERPRETERS)
SCRIPT_AFTER_ROOT = re.compile(r"\$\{?CLAUDE_PROJECT_DIR\}?\"?/([\w./ -]+?\.(?:js|mjs|cjs|py|sh|rb|ts|ps1))")


class Findings:
    def __init__(self):
        self.items = []

    def add(self, level, where, message):
        self.items.append({"level": level, "where": where, "message": message})


def nearest_event(name):
    for e in EVENTS:
        if e.lower() == name.lower():
            return e
    return None


def project_root(settings_path):
    """<root>/.claude/settings.json -> <root>; plugin hooks/hooks.json -> its parent folder."""
    d = os.path.dirname(os.path.abspath(settings_path))
    return os.path.dirname(d) if os.path.basename(d) in (".claude", "hooks") else d


def unquoted_root_var(command):
    """True when $CLAUDE_PROJECT_DIR appears outside double quotes."""
    in_quotes = False
    i = 0
    while i < len(command):
        ch = command[i]
        if ch == "\\":
            i += 2
            continue
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == "$" and re.match(r"\$\{?CLAUDE_PROJECT_DIR", command[i:]) and not in_quotes:
            return True
        i += 1
    return False


def check_matcher(f, where, event, matcher):
    if matcher in (None, "", "*"):
        return
    if not isinstance(matcher, str):
        f.add("ERROR", where, "matcher must be a string")
        return
    if event in NO_MATCHER:
        f.add("WARN", where, f"{event} takes no matcher; '{matcher}' is ignored and the hook fires every time")
        return
    literal = re.fullmatch(r"[A-Za-z0-9_\-, |]+", matcher) is not None
    if literal and event in TOOL_EVENTS:
        for part in [p.strip() for p in re.split(r"[|,]", matcher)]:
            for tool in KNOWN_TOOLS:
                if part != tool and part.lower() == tool.lower():
                    f.add("WARN", where, f"matcher '{part}' will not match the tool '{tool}': tool names are capitalised")
            if part.startswith("mcp__") and part.count("__") < 2:
                f.add("WARN", where, f"matcher '{part}' matches nothing; MCP tools are mcp__<server>__<tool>, use a regex such as '{part}__.*'")
    if not literal:
        try:
            re.compile(matcher)
        except re.error as e:
            f.add("ERROR", where, f"matcher is treated as a regular expression and does not compile: {e}")


def check_script_text(f, where, event, path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return
    if event in ("Stop", "SubagentStop") and "stop_hook_active" not in text:
        f.add("WARN", where, f"{os.path.basename(path)} never reads stop_hook_active; a check that keeps failing keeps the agent running")
    if event in BLOCKING_GUARDS:
        exits = set(re.findall(r"(?:process\.exit|sys\.exit|\bexit)\s*\(?\s*(\d+)", text))
        if "1" in exits and "2" not in exits:
            f.add("WARN", where, f"{os.path.basename(path)} exits with 1 and never with 2; exit 1 is a non-blocking error, only exit 2 blocks")
    if event == "PreToolUse" and re.search(r"tool_input\s*(?:\.|\[['\"])\s*(cmd|path|filename|file)\b", text):
        f.add("WARN", where, f"{os.path.basename(path)} reads a tool_input field that the built-in tools do not send; Bash sends 'command', the editing tools send 'file_path'")


def check_handler(f, where, event, h, root):
    if not isinstance(h, dict):
        f.add("ERROR", where, "handler must be an object")
        return
    t = h.get("type")
    if t not in HANDLER_TYPES:
        f.add("ERROR", where, f"handler type {t!r} is not one of {sorted(HANDLER_TYPES)}")
        return
    timeout = h.get("timeout")
    if timeout is not None:
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            f.add("ERROR", where, f"timeout must be a positive number of seconds, got {timeout!r}")
        elif timeout > MAX_SANE_TIMEOUT_S:
            f.add("WARN", where, f"timeout {timeout} is in seconds ({timeout / 60:.0f} minutes); it looks like a millisecond value")
    if t != "command":
        return
    command = h.get("command")
    if not isinstance(command, str) or not command.strip():
        f.add("ERROR", where, "command handler needs a non-empty 'command' string")
        return
    if "CLAUDE_PROJECT_DIR" not in command and h.get("args") is None:
        m = RELATIVE_SCRIPT.search(command)
        if m and not os.path.isabs(m.group(1)):
            f.add("WARN", where, f"script path '{m.group(1)}' is relative to the current directory, which changes during a session; use \"$CLAUDE_PROJECT_DIR\"/{m.group(1).lstrip('./')}")
            check_script_text(f, where, event, os.path.join(root, m.group(1)))
    if unquoted_root_var(command) and h.get("shell") != "powershell":
        f.add("WARN", where, "$CLAUDE_PROJECT_DIR is used outside double quotes; a project path with a space will break the command")
    if re.search(r"(^|[\s|;&(])jq(\s|$)", command):
        f.add("INFO", where, "command needs jq, which is not installed by default on macOS or Windows")
    if re.search(r"(^|[\s|;&(])python3(\s|$)", command):
        f.add("INFO", where, "command needs python3; on Windows that name is often a store stub rather than an interpreter")
    for m in SCRIPT_AFTER_ROOT.finditer(command):
        script = os.path.join(root, *m.group(1).strip().split("/"))
        if os.path.isfile(script):
            check_script_text(f, where, event, script)
        else:
            f.add("WARN", where, f"script '{m.group(1).strip()}' was not found under the project root {root}")


def lint(settings_path):
    f = Findings()
    try:
        raw = open(settings_path, encoding="utf-8-sig").read()
    except OSError as e:
        print(f"cannot read {settings_path}: {e}", file=sys.stderr)
        return None
    if not raw.strip():
        print(f"{settings_path} is empty; nothing to check", file=sys.stderr)
        return None
    try:
        data = json.loads(raw)
    except ValueError as e:
        f.add("ERROR", "file", f"not valid JSON: {e}. The harness ignores a settings file it cannot parse")
        return f
    hooks = data.get("hooks") if isinstance(data, dict) else None
    if hooks is None:
        for wrong in ("hook", "Hooks"):
            if isinstance(data, dict) and wrong in data:
                f.add("ERROR", "file", f"top-level key '{wrong}' should be 'hooks'")
        if not f.items:
            f.add("INFO", "file", "no 'hooks' key; nothing configured")
        return f
    if not isinstance(hooks, dict):
        f.add("ERROR", "hooks", "'hooks' must be an object keyed by event name")
        return f
    root = project_root(settings_path)
    for event, groups in hooks.items():
        if event not in EVENTS:
            near = nearest_event(event)
            f.add("ERROR", event, f"unknown event name; event names are case-sensitive" + (f", did you mean '{near}'?" if near else ""))
            continue
        if not isinstance(groups, list):
            f.add("ERROR", event, "value must be a list of matcher groups")
            continue
        for gi, group in enumerate(groups):
            where = f"{event}[{gi}]"
            if not isinstance(group, dict):
                f.add("ERROR", where, "matcher group must be an object")
                continue
            if "hooks" not in group:
                if "type" in group or "command" in group:
                    f.add("ERROR", where, "handler is one level too high; wrap it as {\"hooks\": [ {\"type\": ..., \"command\": ...} ]}")
                else:
                    f.add("ERROR", where, "matcher group has no 'hooks' list")
                continue
            check_matcher(f, where, event, group.get("matcher"))
            if not isinstance(group["hooks"], list) or not group["hooks"]:
                f.add("ERROR", where, "'hooks' must be a non-empty list of handlers")
                continue
            for hi, h in enumerate(group["hooks"]):
                check_handler(f, f"{where}.hooks[{hi}]", event, h, root)
    return f


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    f = lint(args[0])
    if f is None:
        return 2
    out = sys.stdout
    try:
        out.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    errors = [i for i in f.items if i["level"] == "ERROR"]
    warns = [i for i in f.items if i["level"] == "WARN"]
    if "--json" in argv:
        print(json.dumps({"errors": len(errors), "warnings": len(warns), "findings": f.items}, indent=2))
    else:
        for i in f.items:
            print(f"{i['level']:5} {i['where']}: {i['message']}")
        print(f"\n{len(errors)} error(s), {len(warns)} warning(s). This check does not run the hooks: fire each one with a sample payload.")
    if errors or ("--strict" in argv and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
