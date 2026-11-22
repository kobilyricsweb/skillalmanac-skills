#!/usr/bin/env python3
"""Show what a robots.txt file lets each AI crawler do, and lint an llms.txt file (offline).

Usage:
    python ai_access_check.py robots.txt [--paths ROOT,docs/,blog/post-1] [--private admin/,cart/]
                              [--expect "OAI-SearchBot=allow,GPTBot=block"]
                              [--llms llms.txt] [--tokens ExtraBot,OtherBot] [--json]
    python ai_access_check.py --llms llms.txt

Reads:  a saved robots.txt and/or llms.txt file. Writes: nothing. Network: none.
        --paths   public content paths to test (default: the root). Use real paths from the site.
                  Write ROOT for "/" and leave the leading slash off the others (blog/post-1):
                  some shells on Windows rewrite an argument that starts with a slash.
        --private paths that must stay closed to every crawler; any crawler allowed there is a FAIL.
        --expect  the access policy the owner decided for the public paths; a mismatch is a FAIL.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = input problem.

Matching follows RFC 9309: a crawler obeys the most specific user-agent group that names it and
ignores the `*` group when it has its own; within a group the longest matching rule wins and
Allow wins a tie. The crawler table mirrors references/crawler-facts.md; update both together.
"""
import json
import os
import re
import sys

# token -> (operator, role, note). Roles: training, search, user (fetch on a person's request), control, ads.
CRAWLERS = {
    "GPTBot": ("OpenAI", "training", "content may be used to train models"),
    "OAI-SearchBot": ("OpenAI", "search", "blocked sites are not shown in search answers (may still appear as a plain link)"),
    "ChatGPT-User": ("OpenAI", "user", "fetch on a person's request; the operator says robots.txt rules may not apply"),
    "OAI-AdsBot": ("OpenAI", "ads", "checks landing pages submitted as ads"),
    "ClaudeBot": ("Anthropic", "training", "content may contribute to model training"),
    "Claude-SearchBot": ("Anthropic", "search", "blocking may reduce visibility and accuracy in search answers"),
    "Claude-User": ("Anthropic", "user", "fetch on a person's request; blocking prevents retrieval for that person"),
    "PerplexityBot": ("Perplexity", "search", "surfaces and links sites in answers; not used for model training"),
    "Perplexity-User": ("Perplexity", "user", "fetch on a person's request; the operator says it generally ignores robots.txt"),
    "Google-Extended": ("Google", "control", "controls Gemini training and grounding; no effect on Google Search; has no user-agent string of its own"),
    "Googlebot": ("Google", "search-engine", "web search; AI answers in search draw on pages that are indexed and snippet-eligible"),
    "Bingbot": ("Microsoft", "search-engine", "web search index"),
}
# Spellings seen in the wild that are not the documented robots.txt tokens.
LOOKALIKES = {"gpt-bot": "GPTBot", "gptbot/1.0": "GPTBot", "chatgpt": "ChatGPT-User", "chatgpt-bot": "GPTBot or OAI-SearchBot",
              "openai": "GPTBot, OAI-SearchBot, ChatGPT-User", "claude-bot": "ClaudeBot", "claude": "ClaudeBot, Claude-SearchBot, Claude-User",
              "anthropic": "ClaudeBot", "perplexity": "PerplexityBot", "perplexity-bot": "PerplexityBot",
              "google-extended-bot": "Google-Extended", "googleextended": "Google-Extended", "oai-searchbot/1.0": "OAI-SearchBot"}
KNOWN_FIELDS = {"user-agent", "allow", "disallow", "sitemap", "crawl-delay", "content-signal", "host", "clean-param"}
# An llms.txt is an index of entry points; beyond this many links it is a dump that no reader loads whole.
LLMS_MAX_LINKS = 100
LINK_ITEM = re.compile(r"^[-*]\s+\[([^\]]+)\]\(([^)\s]+)\)(\s*:\s*.+)?\s*$")


def parse_robots(text):
    groups, order, problems, extras = {}, [], [], {"sitemap": [], "crawl-delay": {}, "content-signal": []}
    agents, in_rules = [], False
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            problems.append("line %d: not a 'field: value' line: %r" % (n, raw.strip()[:60]))
            continue
        field, value = [s.strip() for s in line.split(":", 1)]
        field = field.lower()
        if field not in KNOWN_FIELDS:
            problems.append("line %d: unknown field '%s' (crawlers ignore it)" % (n, field))
            continue
        if field == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(value)
            if value.lower() not in groups:
                groups[value.lower()] = []
                order.append(value)
        elif field in ("allow", "disallow"):
            if not agents:
                problems.append("line %d: rule before any User-agent line (ignored)" % n)
                continue
            in_rules = True
            for a in agents:
                groups[a.lower()].append((field == "allow", value, n))
        elif field == "crawl-delay":
            in_rules = True
            for a in agents:
                extras["crawl-delay"][a] = value
        elif field == "sitemap":
            extras["sitemap"].append(value)
        elif field == "content-signal":
            extras["content-signal"].append(value)
    return groups, order, problems, extras


def decide(rules, path):
    best = (-1, True, None)
    for allow, pattern, line in rules:
        if pattern == "":
            continue  # "Disallow:" with no value allows everything
        rx = "^" + re.escape(pattern).replace(r"\*", ".*")
        if rx.endswith(r"\$"):
            rx = rx[:-2] + "$"
        if re.match(rx, path):
            if len(pattern) > best[0] or (len(pattern) == best[0] and allow):
                best = (len(pattern), allow, line)
    return best[1], best[2]


def lint_llms(text):
    out = []
    lines = text.lstrip(chr(0xFEFF)).splitlines()
    body = [l for l in lines if l.strip()]
    if not body:
        return [("FAIL", "llms.txt is empty")]
    if not re.match(r"^# \S", body[0]):
        out.append(("FAIL", "the first line must be an H1 with the site or project name ('# Name'); found %r" % body[0][:50]))
    if sum(1 for l in lines if re.match(r"^# \S", l)) > 1:
        out.append(("FAIL", "more than one H1; the format has exactly one"))
    if not any(l.startswith(">") for l in body[1:4]):
        out.append(("WARN", "no blockquote summary after the H1 (optional, but it is what a reader sees first)"))
    section, links, sections = None, 0, []
    for n, l in enumerate(lines, 1):
        if re.match(r"^#{3,}\s", l):
            out.append(("WARN", "line %d: heading deeper than H2; file lists are delimited by H2 only" % n))
        elif l.startswith("## "):
            section = l[3:].strip()
            sections.append(section)
        elif section and l.strip().startswith(("-", "*")):
            m = LINK_ITEM.match(l.strip())
            if not m:
                out.append(("FAIL", "line %d: list item is not '- [name](url)' or '- [name](url): note'" % n))
                continue
            links += 1
            if not re.match(r"^https?://", m.group(2)):
                out.append(("WARN", "line %d: link is not an absolute URL: %s" % (n, m.group(2))))
    if not sections:
        out.append(("WARN", "no H2 sections with link lists; the file gives readers nowhere to go"))
    if links > LLMS_MAX_LINKS:
        out.append(("WARN", "%d links; keep the file an index of entry points (under about %d), not a copy of the sitemap" % (links, LLMS_MAX_LINKS)))
    out.append(("NOTE", "%d sections, %d links%s" % (len(sections), links, "; has an 'Optional' section" if "Optional" in sections else "")))
    return out


def main(argv):
    opts, args, i = {}, [], 0
    while i < len(argv):
        if argv[i] in ("--paths", "--private", "--expect", "--llms", "--tokens"):
            if i + 1 >= len(argv):
                sys.stderr.write("ERROR: %s needs a value\n" % argv[i])
                return 2
            opts[argv[i]] = argv[i + 1]
            i += 2
        elif argv[i].startswith("--"):
            opts[argv[i]] = True
            i += 1
        else:
            args.append(argv[i])
            i += 1
    if (not args and "--llms" not in opts) or len(args) > 1:
        print(__doc__)
        return 2
    for path in args + ([opts["--llms"]] if "--llms" in opts else []):
        if not os.path.isfile(path):
            sys.stderr.write("ERROR: file not found: %s. Save the live file first, then pass its path.\n" % path)
            return 2

    findings, matrix, report = [], [], {}

    def add(level, msg):
        findings.append({"level": level, "message": msg})

    if args:
        text = open(args[0], "rb").read().decode("utf-8-sig", "replace")
        if "<html" in text[:500].lower():
            add("FAIL", "the robots.txt file is an HTML page (an error page or a login wall was saved); crawlers treat it as no rules or as unreachable")
        groups, order, problems, extras = parse_robots(text)
        for p in problems:
            add("WARN", "robots.txt " + p)
        def path_list(value):
            out = []
            for item in [x.strip() for x in value.split(",") if x.strip()]:
                if re.match(r"^[A-Za-z]:[\\/]", item):
                    sys.stderr.write("ERROR: the shell rewrote a path argument into %r. Write ROOT for the home page and "
                                     "leave the leading slash off other paths, for example --paths ROOT,blog/post-1\n" % item)
                    sys.exit(2)
                out.append("/" if item in ("ROOT", "/") else "/" + item.lstrip("/"))
            return out

        public = path_list(str(opts.get("--paths", "ROOT")))
        private = [p for p in path_list(str(opts.get("--private", ""))) if p not in public]
        paths = public + private
        tokens = dict(CRAWLERS)
        for extra in [t.strip() for t in str(opts.get("--tokens", "")).split(",") if t.strip()]:
            tokens.setdefault(extra, ("?", "unknown", "not in the bundled table"))
        star = groups.get("*", [])
        for token, (operator, role, note) in tokens.items():
            own = token.lower() in groups
            rules = groups[token.lower()] if own else star
            row = {"token": token, "operator": operator, "role": role, "group": token if own else ("*" if "*" in groups else "none"),
                   "paths": {}, "note": note}
            for path in paths:
                allowed, line = decide(rules, path)
                row["paths"][path] = {"allowed": allowed, "line": line}
            matrix.append(row)
            if own and star:
                star_blocks = {pat for allow, pat, _ in star if not allow and pat}
                own_blocks = {pat for allow, pat, _ in rules if not allow and pat}
                lost = sorted(star_blocks - own_blocks)
                if lost and "/" not in own_blocks:
                    add("WARN", "%s has its own group, so it ignores the '*' group: these '*' disallows do not apply to it: %s. Repeat them in its group if they should." % (token, ", ".join(lost)))
        for name in order:
            low = name.lower()
            if low in LOOKALIKES and low not in {t.lower() for t in tokens}:
                add("WARN", "group 'User-agent: %s' is not a documented token; the documented token is %s. The group has no effect on that crawler." % (name, LOOKALIKES[low]))
        by_token = {r["token"]: r for r in matrix}
        for r in matrix:
            blocked = [p for p, v in r["paths"].items() if not v["allowed"] and p in public]
            open_private = [p for p in private if r["paths"][p]["allowed"]]
            if open_private:
                add("FAIL", "%s may fetch the private path(s) %s (its group is '%s'); a crawler with its own group does not inherit the '*' disallows" % (r["token"], ", ".join(open_private), r["group"]))
            if r["role"] == "search" and blocked:
                add("WARN", "%s (answer-search index) is blocked on %s: %s" % (r["token"], ", ".join(blocked), r["note"]))
            if r["role"] == "search-engine" and blocked:
                add("WARN", "%s is blocked on %s: pages leave that search engine and the AI answers built on it" % (r["token"], ", ".join(blocked)))
            if r["role"] == "user" and blocked:
                add("NOTE", "%s is blocked on %s: %s" % (r["token"], ", ".join(blocked), r["note"]))
        ge = by_token["Google-Extended"]
        if any(not ge["paths"][p]["allowed"] for p in public):
            add("NOTE", "Google-Extended is disallowed: this limits Gemini training and grounding only; it does not remove pages from Google Search or its AI answers")
        if extras["crawl-delay"]:
            add("NOTE", "Crawl-delay set for %s: honoured by some crawlers (Anthropic documents support), ignored by Googlebot" % ", ".join(sorted(extras["crawl-delay"])))
        if not extras["sitemap"]:
            add("NOTE", "no Sitemap line in robots.txt")
        if extras["content-signal"]:
            add("NOTE", "Content-Signal lines present: %s (a preference signal; support differs by crawler)" % "; ".join(extras["content-signal"]))
        for pair in [p.strip() for p in str(opts.get("--expect", "")).split(",") if p.strip()]:
            if "=" not in pair:
                sys.stderr.write("ERROR: --expect entries look like Token=allow or Token=block; got %r\n" % pair)
                return 2
            token, want = [s.strip() for s in pair.split("=", 1)]
            row = next((r for r in matrix if r["token"].lower() == token.lower()), None)
            if row is None or want.lower() not in ("allow", "block"):
                sys.stderr.write("ERROR: --expect: unknown token or value in %r (add the token with --tokens)\n" % pair)
                return 2
            for path, v in row["paths"].items():
                if path in public and v["allowed"] != (want.lower() == "allow"):
                    add("FAIL", "policy mismatch: %s should be %s on %s but robots.txt %s it (group '%s'%s)" % (
                        row["token"], want.lower() + "ed", path, "allows" if v["allowed"] else "blocks", row["group"],
                        ", line %d" % v["line"] if v["line"] else ", no matching rule"))
        report["robots"] = {"paths": paths, "private": private, "matrix": matrix, "sitemaps": extras["sitemap"]}

    if "--llms" in opts:
        llms_text = open(opts["--llms"], "rb").read().decode("utf-8-sig", "replace")
        for level, msg in lint_llms(llms_text):
            add(level, "llms.txt: " + msg)

    order_ = {"FAIL": 0, "WARN": 1, "NOTE": 2}
    findings.sort(key=lambda f: order_[f["level"]])
    counts = {k: sum(1 for f in findings if f["level"] == k) for k in order_}
    limits = ["robots.txt is a request, not an access control; user-initiated fetchers may not follow it",
              "a firewall, CDN bot rule or login wall can block a crawler that robots.txt allows; check server logs or the CDN settings",
              "no file here controls whether an assistant cites the site; that depends on being indexed and on the content"]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--json" in opts:
        print(json.dumps({"counts": counts, "findings": findings, "limits": limits, **report}, indent=2))
        return 1 if counts["FAIL"] else 0
    print("AI ACCESS CHECK: %d FAIL, %d WARN, %d NOTE" % (counts["FAIL"], counts["WARN"], counts["NOTE"]))
    if matrix:
        paths = report["robots"]["paths"]
        print("\n%-18s %-11s %-14s %-8s %s" % ("token", "operator", "role", "group", "  ".join(p + ("(private)" if p in report["robots"]["private"] else "") for p in paths)))
        for r in matrix:
            cells = "  ".join(("allow" if r["paths"][p]["allowed"] else "BLOCK").ljust(max(5, len(p) + (9 if p in report["robots"]["private"] else 0))) for p in paths)
            print("%-18s %-11s %-14s %-8s %s" % (r["token"], r["operator"], r["role"], r["group"][:8], cells))
    print()
    for f in findings:
        print("%-4s %s" % (f["level"], f["message"]))
    print("\nLimits:")
    for line in limits:
        print("  - " + line)
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
