# HTTP security headers review

## One line

Turns a pasted HTTP response header block into a severity-ranked list of missing or weak security headers and cookie flags, using a stdlib-only Python checker.

## What it does

The skill has an agent collect a response header block as plain text, runs `scripts/header_review.py` on it, and writes a short report. The script reads the file, parses the header lines, and checks Strict-Transport-Security (presence, max-age against a working minimum, includeSubDomains), Content-Security-Policy (presence, unsafe-inline without a nonce or hash, unsafe-eval, bare and host wildcards, scheme-wide sources, frame-ancestors, base-uri), X-Content-Type-Options, Referrer-Policy (weak effective values), Permissions-Policy, X-Frame-Options (presence and accepted values), and each Set-Cookie for Secure, HttpOnly and SameSite. Each finding gets an ID, a severity of high, medium, low or info, the header name and a message. Cookie values are never printed. The script makes no network calls and writes no files.

## When to use

Use it when a developer or site owner has a response from their own application and wants to know which of the common browser-facing headers are absent, and which present ones are set in a way that weakens them. It fits a pre-release check on a single page, or a comparison before and after a configuration change, when the header block is already in hand.

## When not to use

Do not use it to scan a live site, to probe for exploitable behavior, or to judge application code. It cannot see server-side logic, authentication design, or headers it does not list. It is not a penetration test and its output should not be presented as one.

## Requirements

Python 3.9 or newer, standard library only. No network access, no installed packages, and no write access is needed. The input is a UTF-8 text file of at most 2 MB and 2000 lines.

## Example

Command: `python -I scripts/header_review.py fixtures/weak_headers.txt`, exit code 1. Output from the smoke run, verbatim:

```json
{
  "tool": "header_review",
  "version": "0.1.0",
  "input_lines": 11,
  "headers_parsed": 10,
  "lines_skipped": 1,
  "counts": {
    "high": 4,
    "medium": 6,
    "low": 4,
    "info": 0
  },
  "findings": [
    {
      "id": "CSP-004",
      "severity": "high",
      "header": "Content-Security-Policy",
      "message": "script source allows 'unsafe-inline' with no nonce or hash"
    },
    {
      "id": "CSP-005",
      "severity": "high",
      "header": "Content-Security-Policy",
      "message": "script source allows 'unsafe-eval'"
    },
    {
      "id": "COOKIE-001",
      "severity": "high",
      "header": "Set-Cookie",
      "message": "cookie prefs lacks the Secure flag"
    },
    {
      "id": "COOKIE-004",
      "severity": "high",
      "header": "Set-Cookie",
      "message": "cookie prefs sets SameSite=None without Secure"
    },
    {
      "id": "HSTS-002",
      "severity": "medium",
      "header": "Strict-Transport-Security",
      "message": "max-age is missing or below 15552000 seconds (working minimum)"
    },
    {
      "id": "CSP-008",
      "severity": "medium",
      "header": "Content-Security-Policy",
      "message": "frame-ancestors is missing"
    },
    {
      "id": "REF-002",
      "severity": "medium",
      "header": "Referrer-Policy",
      "message": "effective value unsafe-url leaks full URLs to other origins"
    },
    {
      "id": "XFO-003",
      "severity": "medium",
      "header": "X-Frame-Options",
      "message": "value ALLOW-FROM example-partner is not DENY or SAMEORIGIN"
    },
    {
      "id": "COOKIE-002",
      "severity": "medium",
      "header": "Set-Cookie",
      "message": "cookie session lacks the HttpOnly flag"
    },
    {
      "id": "COOKIE-002",
      "severity": "medium",
      "header": "Set-Cookie",
      "message": "cookie prefs lacks the HttpOnly flag"
    },
    {
      "id": "HSTS-003",
      "severity": "low",
      "header": "Strict-Transport-Security",
      "message": "includeSubDomains is not set"
    },
    {
      "id": "CSP-011",
      "severity": "low",
      "header": "Content-Security-Policy",
      "message": "default-src uses a host wildcard"
    },
    {
      "id": "CSP-009",
      "severity": "low",
      "header": "Content-Security-Policy",
      "message": "base-uri is missing"
    },
    {
      "id": "PP-001",
      "severity": "low",
      "header": "Permissions-Policy",
      "message": "header is missing"
    }
  ],
  "scope": "header checklist, not a penetration test"
}
```

## Limits

The checks cover only the listed headers. Thresholds such as the 180-day HSTS minimum are working values chosen for this checklist, not published standards. The script reads one header block and cannot tell whether a header is set by a CDN, a proxy or the application. A header missing from a pasted block may be present in another response, and a present header may be overridden elsewhere. Cookie checks look at attributes only, not at what the cookie stores. Duplicate headers are reported only for HSTS.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
