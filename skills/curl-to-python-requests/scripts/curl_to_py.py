"""Translate a copied curl command into an equivalent Python requests snippet.

The curl command is read from a text file and split with shlex. It is never
executed, and no network request is made. Credentials (-u, Authorization,
Cookie, password-like names) are replaced by placeholders in the output.

Usage:
    python -I scripts/curl_to_py.py <input-file>

Exit codes:
    0  snippet printed, no findings
    1  snippet printed with one or more findings (unsupported or lossy parts)
    2  usage or input error; one-line JSON error on stderr, nothing on stdout
"""

import json
import os
import re
import shlex
import sys

MAX_BYTES = 2 * 1024 * 1024
REDACTED = "<REDACTED>"
SENSITIVE_KEYS = {
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "access_token", "client_secret",
}
SENSITIVE_HEADERS = {"authorization", "proxy-authorization", "cookie", "x-api-key"}
KNOWN_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
URL_RE = re.compile(r"([A-Za-z][A-Za-z0-9+.\-]*)://([^/?#]*)([^?#]*)(?:\?([^#]*))?(?:#.*)?", re.S)
PCT_RUN_RE = re.compile(r"(?:%[0-9A-Fa-f]{2})+")

# Options that take one value and are translated: option -> kind
VALUE_OPTS = {
    "-X": "request", "--request": "request",
    "-H": "header", "--header": "header",
    "-d": "data", "--data": "data", "--data-ascii": "data",
    "--data-binary": "data", "--data-raw": "data",
    "--json": "json",
    "-F": "form", "--form": "form",
    "-u": "user", "--user": "user",
    "-A": "agent", "--user-agent": "agent",
    "-e": "referer", "--referer": "referer",
    "-b": "cookie", "--cookie": "cookie",
    "--url": "url",
}
# Options that take one value and are not translated; the value is dropped
UNSUPPORTED_VALUE_OPTS = {
    "-o", "--output", "-x", "--proxy", "-m", "--max-time", "--connect-timeout",
    "--cacert", "-T", "--upload-file", "-c", "--cookie-jar", "-w", "--write-out",
    "-E", "--cert", "--resolve", "--retry", "--max-redirs", "--data-urlencode",
    "-K", "--config",
}
# Flags without a value: option -> flag name
FLAG_OPTS = {
    "-L": "location", "--location": "location",
    "-k": "insecure", "--insecure": "insecure",
    "-G": "get", "--get": "get",
    "-I": "head", "--head": "head",
    "--compressed": "compressed",
    "-s": "quiet", "--silent": "quiet", "-S": "quiet", "--show-error": "quiet",
    "-v": "quiet", "--verbose": "quiet", "-i": "quiet", "--include": "quiet",
}


class InputError(Exception):
    """Fatal problem with the input; exit 2."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


class CurlArgs:
    """Options collected from the curl command line."""

    def __init__(self):
        self.method = None
        self.headers = []        # raw -H values, in order
        self.extra_headers = []  # (name, value) from -A, -e, -b
        self.data = []           # -d parts
        self.json_raw = None     # --json text (last one wins)
        self.form = []           # (field, content) for -F text fields
        self.user = None
        self.urls = []
        self.flags = set()
        self.findings = []       # (code, detail) tuples


def read_input(path):
    try:
        if not os.path.isfile(path):
            raise InputError("FILE_NOT_FOUND", "input file is missing or not a regular file")
        if os.path.getsize(path) > MAX_BYTES:
            raise InputError("FILE_TOO_LARGE", "input is larger than 2 MB")
        with open(path, "rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        raise InputError("READ_ERROR", "input file could not be read")
    if len(raw) > MAX_BYTES:
        raise InputError("FILE_TOO_LARGE", "input is larger than 2 MB")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InputError("INVALID_UTF8", "input is not valid UTF-8")


def tokenize(text):
    text = text.replace("\r\n", "\n")
    text = re.sub(r"\\\n", " ", text)  # join POSIX line continuations
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        raise InputError("SHELL_PARSE_ERROR", "unbalanced quote or trailing backslash")
    if not tokens or tokens[0] not in ("curl", "curl.exe"):
        raise InputError("NOT_A_CURL_COMMAND", "the first word must be curl")
    return tokens[1:]


def apply_value(args, name, value):
    if name in UNSUPPORTED_VALUE_OPTS:
        args.findings.append(("UNSUPPORTED_OPTION", name))
        return
    kind = VALUE_OPTS[name]
    if kind == "request":
        args.method = value
    elif kind == "header":
        args.headers.append(value)
    elif kind == "data":
        if value.startswith("@") and name != "--data-raw":
            args.findings.append(("FILE_REFERENCE_NOT_READ", name))
        else:
            args.data.append(value)
    elif kind == "json":
        if value.startswith("@"):
            args.findings.append(("FILE_REFERENCE_NOT_READ", name))
        else:
            args.json_raw = value
    elif kind == "form":
        field, has_eq, content = value.partition("=")
        if not has_eq or not field:
            args.findings.append(("FORM_FIELD_MALFORMED", name))
        elif content.startswith("@") or content.startswith("<"):
            args.findings.append(("FILE_REFERENCE_NOT_READ", name))
        else:
            args.form.append((field, content.partition(";type=")[0]))
    elif kind == "user":
        args.user = value
    elif kind == "agent":
        args.extra_headers.append(("User-Agent", value))
    elif kind == "referer":
        args.extra_headers.append(("Referer", value))
    elif kind == "cookie":
        if "=" in value:
            args.extra_headers.append(("Cookie", value))
        else:
            args.findings.append(("FILE_REFERENCE_NOT_READ", name))
    elif kind == "url":
        args.urls.append(value)


def parse_args(tokens, args):
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        i += 1
        if tok == "--":
            args.urls.extend(tokens[i:])
            break
        if tok.startswith("--"):
            name, has_eq, value = tok.partition("=")
            if name in FLAG_OPTS:
                args.flags.add(FLAG_OPTS[name])
            elif name in VALUE_OPTS or name in UNSUPPORTED_VALUE_OPTS:
                if not has_eq:
                    if i >= len(tokens):
                        raise InputError("OPTION_MISSING_VALUE", "an option is missing its value")
                    value = tokens[i]
                    i += 1
                apply_value(args, name, value)
            else:
                args.findings.append(("UNSUPPORTED_OPTION", name))
        elif tok.startswith("-") and len(tok) > 1:
            j = 1
            while j < len(tok):
                short = "-" + tok[j]
                rest = tok[j + 1:]
                if short in FLAG_OPTS:
                    args.flags.add(FLAG_OPTS[short])
                    j += 1
                elif short in VALUE_OPTS or short in UNSUPPORTED_VALUE_OPTS:
                    if rest:
                        value = rest
                    else:
                        if i >= len(tokens):
                            raise InputError("OPTION_MISSING_VALUE", "an option is missing its value")
                        value = tokens[i]
                        i += 1
                    apply_value(args, short, value)
                    break
                else:
                    args.findings.append(("UNSUPPORTED_OPTION", short))
                    j += 1
        else:
            args.urls.append(tok)


def _unquote(text):
    """Form-style percent decoding: plus becomes space, UTF-8 escape runs are decoded."""
    text = text.replace("+", " ")
    return PCT_RUN_RE.sub(
        lambda m: bytes.fromhex(m.group(0).replace("%", "")).decode("utf-8", "replace"), text)


def _parse_pairs(raw):
    pairs = []
    for part in raw.split("&"):
        if part:
            key, _, value = part.partition("=")
            pairs.append((_unquote(key), _unquote(value)))
    return pairs


def is_sensitive_key(name):
    return name.strip().lower().replace("-", "_") in SENSITIVE_KEYS


def is_sensitive_header(name):
    low = name.strip().lower()
    return (low in SENSITIVE_HEADERS or "token" in low or "secret" in low
            or "api-key" in low or "api_key" in low)


def mask_obj(obj, masked):
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if is_sensitive_key(key) and not isinstance(value, (dict, list)):
                masked.add(key)
                out[key] = REDACTED
            else:
                out[key] = mask_obj(value, masked)
        return out
    if isinstance(obj, list):
        return [mask_obj(value, masked) for value in obj]
    return obj


def mask_pairs(pairs, masked):
    out = []
    for key, value in pairs:
        if is_sensitive_key(key):
            masked.add(key)
            out.append((key, REDACTED))
        else:
            out.append((key, value))
    return out


def pairs_to_literal(pairs):
    keys = [key for key, _ in pairs]
    if len(set(keys)) == len(keys):
        return dict(pairs)
    return [tuple(pair) for pair in pairs]


def json_body(text, findings, masked):
    try:
        parsed = json.loads(text)
    except (ValueError, RecursionError):
        findings.append(("JSON_BODY_INVALID", "body is not valid JSON; placeholder used"))
        return "data", "<REQUEST_BODY>"
    return "json", mask_obj(parsed, masked)


def build_body(args, headers, findings, masked):
    """Return (kind, value, extra_params). kind is json, data, files or None."""
    raw = "&".join(args.data) if args.data else None
    if "get" in args.flags:
        extra = _parse_pairs(raw) if raw is not None else []
        if args.json_raw is not None or args.form:
            findings.append(("UNSUPPORTED_OPTION", "-G with --json or -F: body dropped"))
        return None, None, extra
    if args.json_raw is not None:
        headers.setdefault("content-type", ("Content-Type", "application/json"))
        headers.setdefault("accept", ("Accept", "application/json"))
        kind, value = json_body(args.json_raw, findings, masked)
        return kind, value, []
    if args.form:
        files = []
        for field, content in args.form:
            if is_sensitive_key(field):
                masked.add(field)
                content = REDACTED
            files.append((field, (None, content)))
        return "files", files, []
    if raw is None:
        return None, None, []
    if "json" in headers.get("content-type", ("", ""))[1].lower():
        kind, value = json_body(raw, findings, masked)
        return kind, value, []
    parts = []
    for part in raw.split("&"):
        key, has_eq, _ = part.partition("=")
        name = _unquote(key)
        if has_eq and is_sensitive_key(name):
            masked.add(name)
            parts.append(key + "=" + REDACTED)
        else:
            parts.append(part)
    return "data", "&".join(parts), []


def render(obj, depth=0):
    pad = "    " * depth
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = "".join("%s    %s: %s,\n" % (pad, render(k), render(v, depth + 1))
                        for k, v in obj.items())
        return "{\n" + items + pad + "}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        items = "".join("%s    %s,\n" % (pad, render(v, depth + 1)) for v in obj)
        return "[\n" + items + pad + "]"
    if isinstance(obj, tuple):
        return "(" + ", ".join(render(v, depth) for v in obj) + ")"
    if obj is None:
        return "None"
    if isinstance(obj, bool):
        return "True" if obj else "False"
    if isinstance(obj, (int, float)):
        return repr(obj)
    return json.dumps(str(obj), ensure_ascii=False)


def translate(tokens):
    args = CurlArgs()
    parse_args(tokens, args)
    if not args.urls:
        raise InputError("NO_URL", "no URL found in the curl command")
    findings = args.findings
    masked = set()
    if len(args.urls) > 1:
        findings.append(("EXTRA_URL", "%d URLs given; only the first is translated" % len(args.urls)))

    headers = {}  # lower-case name -> (display name, value)
    for raw in args.headers:
        name, has_colon, value = raw.partition(":")
        if not has_colon or not name.strip():
            findings.append(("HEADER_MALFORMED", "a -H value has no name: value form; skipped"))
            continue
        headers[name.strip().lower()] = (name.strip(), value.strip())
    for name, value in args.extra_headers:
        headers[name.lower()] = (name, value)
    for key in list(headers):
        name, value = headers[key]
        if is_sensitive_header(name):
            masked.add(name)
            headers[key] = (name, REDACTED)

    kind, body, extra_params = build_body(args, headers, findings, masked)

    if args.method is not None:
        method = args.method
    elif "head" in args.flags:
        method = "HEAD"
    elif "get" in args.flags:
        method = "GET"
    elif kind is not None:
        method = "POST"
    else:
        method = "GET"
    method = method.upper()
    if not re.fullmatch(r"[A-Z]+", method):
        raise InputError("METHOD_INVALID", "the HTTP method must be letters only")

    url = args.urls[0]
    if not re.match(r"[A-Za-z][A-Za-z0-9+.\-]*://", url):
        url = "http://" + url
        findings.append(("SCHEME_DEFAULTED", "URL had no scheme; http is used, as curl does"))
    match = URL_RE.fullmatch(url)
    if not match or not match.group(2):
        raise InputError("URL_INVALID", "the URL could not be parsed or has no host")
    base = "%s://%s%s" % (match.group(1), match.group(2), match.group(3))
    pairs = _parse_pairs(match.group(4) or "") + extra_params
    pairs = mask_pairs(pairs, masked)

    auth = args.user is not None
    if auth:
        masked.add("basic auth")
        if ":" not in args.user:
            findings.append(("AUTH_NO_PASSWORD", "-u has no password; curl would prompt; placeholder used"))

    location = "location" in args.flags
    insecure = "insecure" in args.flags

    out = ["# Generated by curl_to_py.py from a curl command. Nothing was sent."]
    if masked:
        out.append("# Masked values: " + ", ".join(sorted(masked)))
    for code, detail in findings:
        out.append("# FINDING %s: %s" % (code, detail))
    out.append("import requests")
    out.append("")
    out.append("url = " + render(base))
    if pairs:
        out.append("params = " + render(pairs_to_literal(pairs)))
    if headers:
        out.append("headers = " + render({name: value for name, value in headers.values()}))
    if kind == "json":
        out.append("json_body = " + render(body))
    elif kind == "data":
        out.append("data_body = " + render(body))
    elif kind == "files":
        out.append("files = " + render(body))

    call_args = []
    if method not in KNOWN_METHODS:
        call_args.append(render(method))
    call_args.append("url")
    if pairs:
        call_args.append("params=params")
    if headers:
        call_args.append("headers=headers")
    if auth:
        call_args.append('auth=("<USER>", "<PASSWORD>")')
    if kind == "json":
        call_args.append("json=json_body")
    elif kind == "data":
        call_args.append("data=data_body")
    elif kind == "files":
        call_args.append("files=files")
    call_args.append("allow_redirects=" + ("True" if location else "False"))
    if insecure:
        call_args.append("verify=False")
    if method in KNOWN_METHODS:
        head = "response = requests.%s(" % method.lower()
    else:
        head = "response = requests.request("
    out.append(head)
    out.extend("    %s," % arg for arg in call_args)
    out.append(")")
    out.append("print(response.status_code)")
    return "\n".join(out) + "\n", findings


def main(argv):
    try:
        if len(argv) != 2:
            raise InputError("USAGE", "usage: curl_to_py.py <input-file>")
        text = read_input(argv[1])
        tokens = tokenize(text)
        snippet, findings = translate(tokens)
    except InputError as exc:
        sys.stderr.write(json.dumps({"error": exc.message, "code": exc.code}) + "\n")
        return 2
    sys.stdout.buffer.write(snippet.encode("utf-8"))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
