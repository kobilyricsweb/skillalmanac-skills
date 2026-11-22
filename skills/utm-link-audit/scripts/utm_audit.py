#!/usr/bin/env python3
"""Audit a file of campaign URLs for consistent UTM parameters.

Reads one URL per line and reports, with line numbers, these problem codes:
  BAD_URL           line has no scheme or host
  MISSING_PARAM     utm_source, utm_medium or utm_campaign is absent
  UPPERCASE         a utm_ key or value contains an uppercase letter
  SPACE             a utm value contains a space, %20 or an encoded plus
  BAD_MEDIUM        utm_medium is not in the allowed list
  MIXED_SEPARATOR   utm_campaign mixes "_" and "-", or differs from an
                    earlier campaign only by the separator character
  DUPLICATE         the URL matches an earlier line after normalization

Stdlib only. No network, no subprocess, no eval. The input file is read only.

Exit codes: 0 no findings, 1 findings reported, 2 usage or input error.
"""
import argparse
import json
import os
import re
import sys

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_LINE_CHARS = 4096
REQUIRED = ("utm_source", "utm_medium", "utm_campaign")
DEFAULT_MEDIUMS = "cpc,email,social,referral,display,affiliate,organic"
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
ESCAPE_RE = re.compile(r"%([0-9A-Fa-f]{2})")


class SplitUrl(object):
    """Plain holder for the parts of a URL. No network parsing is done."""

    def __init__(self, scheme, netloc, path, query):
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        self.query = query


def split_url(url):
    scheme, sep, rest = url.partition("://")
    if not sep or not SCHEME_RE.match(scheme):
        return SplitUrl("", "", "", "")
    rest = rest.split("#", 1)[0]
    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)
    netloc, slash, path = rest.partition("/")
    return SplitUrl(scheme, netloc, slash + path, query)


def unquote(text):
    """Decode %XX escapes. Non-ASCII bytes map to latin-1 characters."""
    return ESCAPE_RE.sub(lambda m: chr(int(m.group(1), 16)), text)


def fail(message):
    sys.stderr.write(json.dumps({"error": message}) + "\n")
    sys.exit(2)


def parse_mediums(text):
    items = [part.strip().lower() for part in text.split(",")]
    items = [item for item in items if item]
    if not items:
        fail("allowed-mediums must contain at least one value")
    return items


def raw_pairs(query):
    """Return (key, raw_value) pairs in order. Values stay undecoded."""
    pairs = []
    for part in query.split("&"):
        if not part:
            continue
        key, _, raw = part.partition("=")
        pairs.append((key, raw))
    return pairs


def has_space(raw):
    return " " in raw or "%20" in raw.upper() or "+" in raw


def check_line(number, url, allowed, state, findings):
    parts = split_url(url)
    if not parts.scheme or not parts.netloc:
        findings.append({"line": number, "code": "BAD_URL", "detail": "no scheme or host", "url": url})
        return
    pairs = raw_pairs(parts.query)

    # DUPLICATE: normalized form is scheme, host, path and the sorted,
    # lowercased, decoded query pairs.
    norm_pairs = tuple(sorted((unquote(k).lower(), unquote(v.replace("+", " ")).lower()) for k, v in pairs))
    norm_key = (parts.scheme.lower(), parts.netloc.lower(), parts.path, norm_pairs)
    if norm_key in state["seen_urls"]:
        first = state["seen_urls"][norm_key]
        findings.append({"line": number, "code": "DUPLICATE", "detail": "same as line %d" % first, "url": url})
    else:
        state["seen_urls"][norm_key] = number

    utm = {}
    for key, raw in pairs:
        if key.lower().startswith("utm_"):
            if key != key.lower():
                findings.append({"line": number, "code": "UPPERCASE", "detail": "key " + key, "url": url})
            if key.lower() not in utm:
                utm[key.lower()] = raw

    for name in REQUIRED:
        if name not in utm:
            findings.append({"line": number, "code": "MISSING_PARAM", "detail": name, "url": url})

    for name, raw in utm.items():
        value = unquote(raw.replace("+", " "))
        if has_space(raw):
            findings.append({"line": number, "code": "SPACE", "detail": "%s has a space" % name, "url": url})
        elif value != value.lower():
            findings.append({"line": number, "code": "UPPERCASE", "detail": "%s=%s" % (name, value), "url": url})

    medium_raw = utm.get("utm_medium")
    if medium_raw is not None and not has_space(medium_raw):
        medium = unquote(medium_raw).lower()
        if medium not in allowed:
            findings.append({"line": number, "code": "BAD_MEDIUM", "detail": "utm_medium=%s" % medium, "url": url})

    campaign_raw = utm.get("utm_campaign")
    if campaign_raw is not None and not has_space(campaign_raw):
        campaign = unquote(campaign_raw).lower()
        if "_" in campaign and "-" in campaign:
            findings.append({"line": number, "code": "MIXED_SEPARATOR", "detail": "campaign=" + campaign, "url": url})
        sep_key = campaign.replace("-", "_")
        if sep_key in state["campaigns"]:
            first_campaign, first_line = state["campaigns"][sep_key]
            if first_campaign != campaign:
                findings.append({
                    "line": number,
                    "code": "MIXED_SEPARATOR",
                    "detail": "campaign %s differs from %s on line %d by separator only" % (campaign, first_campaign, first_line),
                    "url": url,
                })
        else:
            state["campaigns"][sep_key] = (campaign, number)


def main(argv):
    parser = argparse.ArgumentParser(description="Audit campaign URLs for UTM consistency. Stdlib only, no network.")
    parser.add_argument("input", help="text file with one URL per line")
    parser.add_argument("--output", help="write the JSON report here instead of stdout")
    parser.add_argument("--allowed-mediums", default=DEFAULT_MEDIUMS,
                        help="comma-separated utm_medium values (default: %(default)s)")
    args = parser.parse_args(argv)

    allowed = parse_mediums(args.allowed_mediums)

    if not os.path.isfile(args.input):
        fail("input file not found")
    if os.path.getsize(args.input) > MAX_INPUT_BYTES:
        fail("input file exceeds 2 MB")
    with open(args.input, "rb") as handle:
        data = handle.read()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("input is not valid UTF-8")

    if args.output:
        out_norm = os.path.normcase(os.path.realpath(args.output))
        in_norm = os.path.normcase(os.path.realpath(args.input))
        if out_norm == in_norm:
            fail("output path must not be the input path")

    state = {"seen_urls": {}, "campaigns": {}}
    findings = []
    lines_read = 0
    urls_checked = 0
    for number, line in enumerate(text.splitlines(), start=1):
        lines_read += 1
        if len(line) > MAX_LINE_CHARS:
            fail("line %d exceeds %d characters" % (number, MAX_LINE_CHARS))
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        urls_checked += 1
        check_line(number, url, allowed, state, findings)

    summary = {}
    for item in findings:
        summary[item["code"]] = summary.get(item["code"], 0) + 1

    report = {
        "input": args.input,
        "lines_read": lines_read,
        "urls_checked": urls_checked,
        "allowed_mediums": allowed,
        "summary": summary,
        "findings": findings,
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    else:
        sys.stdout.write(rendered)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
