"""header_review: checklist review of a pasted HTTP response header block.

Reads one UTF-8 text file holding raw response headers, one "Name: value"
per line. An HTTP status line is ignored. A line that starts with whitespace
continues the previous header. Cookie values are never printed, only names.

The script makes no network calls, starts no subprocesses, evaluates no code
and writes no files. It prints one JSON object to stdout. The findings are a
header checklist, not a penetration test.

Usage:
    python -I scripts/header_review.py <headers.txt>

Exit codes:
    0  no findings, or only info-level findings
    1  at least one high, medium or low finding
    2  usage or input error (one line of JSON with an "error" key on stdout)
"""
import json
import sys

MAX_BYTES = 2 * 1024 * 1024
MAX_LINES = 2000
HSTS_MIN_MAX_AGE = 15552000  # 180 days, working value, not a published spec
SEVERITY_ORDER = ("high", "medium", "low", "info")
REFERRER_KNOWN = {
    "no-referrer", "no-referrer-when-downgrade", "origin",
    "origin-when-cross-origin", "same-origin", "strict-origin",
    "strict-origin-when-cross-origin", "unsafe-url",
}
REFERRER_WEAK = {"unsafe-url", "no-referrer-when-downgrade"}


def fail(message):
    sys.stdout.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def read_input(path):
    try:
        with open(path, "rb") as fh:
            data = fh.read(MAX_BYTES + 1)
    except OSError:
        fail("cannot read input file")
    if len(data) > MAX_BYTES:
        fail("input exceeds 2 MB")
    if b"\x00" in data:
        fail("input contains NUL bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        fail("input exceeds 2000 lines")
    return lines


def parse_headers(lines):
    """Return (headers, skipped) where headers is a list of [lower, name, value]."""
    headers = []
    skipped = 0
    for raw in lines:
        if not raw.strip():
            continue
        if raw[0] in " \t":
            if headers:
                headers[-1][2] += " " + raw.strip()
            else:
                skipped += 1
            continue
        if raw.upper().startswith("HTTP/") or ":" not in raw:
            skipped += 1
            continue
        name, value = raw.split(":", 1)
        name = name.strip()
        headers.append([name.lower(), name, value.strip()])
    return headers, skipped


def values_for(headers, lower_name):
    return [h[2] for h in headers if h[0] == lower_name]


def add(findings, fid, severity, header, message):
    findings.append({"id": fid, "severity": severity, "header": header, "message": message})


def parse_csp(value):
    """First occurrence of each directive wins, as in the CSP specification."""
    result = {}
    for part in value.split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        name = tokens[0].lower()
        if name not in result:
            result[name] = [t.lower() for t in tokens[1:]]
    return result


def check_hsts(headers, findings):
    values = values_for(headers, "strict-transport-security")
    if not values:
        add(findings, "HSTS-001", "high", "Strict-Transport-Security",
            "header is missing; browsers will not pin the site to HTTPS")
        return
    if len(values) > 1:
        add(findings, "HSTS-004", "low", "Strict-Transport-Security",
            "more than one HSTS header is present")
    tokens = [t.strip().strip('"').lower() for t in values[0].split(";")]
    max_age = None
    for token in tokens:
        if token.startswith("max-age="):
            try:
                max_age = int(token.split("=", 1)[1])
            except ValueError:
                max_age = None
    if max_age is None or max_age < HSTS_MIN_MAX_AGE:
        add(findings, "HSTS-002", "medium", "Strict-Transport-Security",
            "max-age is missing or below %d seconds (working minimum)" % HSTS_MIN_MAX_AGE)
    if "includesubdomains" not in tokens:
        add(findings, "HSTS-003", "low", "Strict-Transport-Security",
            "includeSubDomains is not set")


def check_csp(headers, findings):
    """Return the parsed directives, or None when no enforced CSP exists."""
    values = values_for(headers, "content-security-policy")
    report_only = values_for(headers, "content-security-policy-report-only")
    if not values:
        if report_only:
            add(findings, "CSP-002", "high", "Content-Security-Policy",
                "only Content-Security-Policy-Report-Only is present; nothing is enforced")
        else:
            add(findings, "CSP-001", "high", "Content-Security-Policy",
                "header is missing")
        return None
    directives = parse_csp(values[0])
    script = directives.get("script-src", directives.get("default-src"))
    if script is None:
        add(findings, "CSP-003", "medium", "Content-Security-Policy",
            "neither script-src nor default-src is set; scripts are not restricted")
    else:
        has_nonce_or_hash = any(t.startswith(("'nonce-", "'sha256-", "'sha384-", "'sha512-"))
                                for t in script)
        if "'unsafe-inline'" in script:
            if has_nonce_or_hash:
                add(findings, "CSP-004", "info", "Content-Security-Policy",
                    "'unsafe-inline' is present next to a nonce or hash; modern browsers ignore it")
            else:
                add(findings, "CSP-004", "high", "Content-Security-Policy",
                    "script source allows 'unsafe-inline' with no nonce or hash")
        if "'unsafe-eval'" in script:
            add(findings, "CSP-005", "high", "Content-Security-Policy",
                "script source allows 'unsafe-eval'")
        if "*" in script:
            add(findings, "CSP-006", "high", "Content-Security-Policy",
                "script source contains a bare wildcard")
        for scheme in ("http:", "https:", "data:"):
            if scheme in script:
                add(findings, "CSP-012", "medium", "Content-Security-Policy",
                    "script source allows the whole scheme %s" % scheme)
    for name, sources in directives.items():
        if name == "script-src":
            continue
        if "*" in sources:
            add(findings, "CSP-007", "medium", "Content-Security-Policy",
                "%s contains a bare wildcard" % name)
        elif any(t.startswith("*.") for t in sources):
            add(findings, "CSP-011", "low", "Content-Security-Policy",
                "%s uses a host wildcard" % name)
    if "frame-ancestors" not in directives:
        add(findings, "CSP-008", "medium", "Content-Security-Policy",
            "frame-ancestors is missing")
    if "base-uri" not in directives:
        add(findings, "CSP-009", "low", "Content-Security-Policy",
            "base-uri is missing")
    return directives


def check_simple_headers(headers, findings, csp_directives):
    xcto = values_for(headers, "x-content-type-options")
    if not xcto:
        add(findings, "XCTO-001", "medium", "X-Content-Type-Options", "header is missing")
    elif xcto[0].lower() != "nosniff":
        add(findings, "XCTO-002", "medium", "X-Content-Type-Options",
            "value is not nosniff")

    referrer = values_for(headers, "referrer-policy")
    if not referrer:
        add(findings, "REF-001", "low", "Referrer-Policy", "header is missing")
    else:
        tokens = [t.strip().lower() for t in referrer[0].split(",")]
        recognized = [t for t in tokens if t in REFERRER_KNOWN]
        if not recognized:
            add(findings, "REF-003", "low", "Referrer-Policy", "no recognized policy value")
        elif recognized[-1] in REFERRER_WEAK:
            add(findings, "REF-002", "medium", "Referrer-Policy",
                "effective value %s leaks full URLs to other origins" % recognized[-1])

    if not values_for(headers, "permissions-policy"):
        add(findings, "PP-001", "low", "Permissions-Policy", "header is missing")

    xfo = values_for(headers, "x-frame-options")
    has_frame_ancestors = bool(csp_directives and "frame-ancestors" in csp_directives)
    if not xfo:
        if has_frame_ancestors:
            add(findings, "XFO-002", "info", "X-Frame-Options",
                "header is missing; CSP frame-ancestors covers framing")
        else:
            add(findings, "XFO-001", "medium", "X-Frame-Options",
                "neither X-Frame-Options nor CSP frame-ancestors limits framing")
    elif xfo[0].upper() not in ("DENY", "SAMEORIGIN"):
        add(findings, "XFO-003", "medium", "X-Frame-Options",
            "value %s is not DENY or SAMEORIGIN" % xfo[0])


def check_cookies(headers, findings):
    for value in values_for(headers, "set-cookie"):
        parts = [p.strip() for p in value.split(";")]
        name = parts[0].split("=", 1)[0].strip() or "(empty name)"
        attrs = [p.lower() for p in parts[1:]]
        samesite = None
        for attr in attrs:
            if attr.startswith("samesite="):
                samesite = attr.split("=", 1)[1].strip()
        secure = "secure" in attrs
        if not secure:
            add(findings, "COOKIE-001", "high", "Set-Cookie",
                "cookie %s lacks the Secure flag" % name)
        if "httponly" not in attrs:
            add(findings, "COOKIE-002", "medium", "Set-Cookie",
                "cookie %s lacks the HttpOnly flag" % name)
        if samesite is None:
            add(findings, "COOKIE-003", "medium", "Set-Cookie",
                "cookie %s has no SameSite attribute" % name)
        elif samesite not in ("strict", "lax", "none"):
            add(findings, "COOKIE-005", "low", "Set-Cookie",
                "cookie %s has an unknown SameSite value" % name)
        elif samesite == "none" and not secure:
            add(findings, "COOKIE-004", "high", "Set-Cookie",
                "cookie %s sets SameSite=None without Secure" % name)


def main(argv):
    if len(argv) != 2:
        fail("usage: header_review.py <headers.txt>")
    lines = read_input(argv[1])
    headers, skipped = parse_headers(lines)

    findings = []
    check_hsts(headers, findings)
    csp_directives = check_csp(headers, findings)
    check_simple_headers(headers, findings, csp_directives)
    check_cookies(headers, findings)

    findings.sort(key=lambda f: SEVERITY_ORDER.index(f["severity"]))
    counts = {level: 0 for level in SEVERITY_ORDER}
    for item in findings:
        counts[item["severity"]] += 1

    result = {
        "tool": "header_review",
        "version": "0.1.0",
        "input_lines": len(lines),
        "headers_parsed": len(headers),
        "lines_skipped": skipped,
        "counts": counts,
        "findings": findings,
        "scope": "header checklist, not a penetration test",
    }
    sys.stdout.write(json.dumps(result, indent=2) + "\n")
    actionable = counts["high"] + counts["medium"] + counts["low"]
    sys.exit(1 if actionable else 0)


if __name__ == "__main__":
    main(sys.argv)
