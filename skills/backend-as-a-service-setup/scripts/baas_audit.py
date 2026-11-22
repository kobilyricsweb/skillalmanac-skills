#!/usr/bin/env python3
"""Read-only audit of a project folder that uses a hosted backend (BaaS).

    python scripts/baas_audit.py <project-folder> [--fail-on high|critical|medium|never]

What it reads: .env* files, .gitignore files, the git index file (read as bytes,
no git command), rules and policy files (*.rules, *.rules.json, *.sql,
firebase.json, appwrite.json, supabase/config.toml) and source/config text files
for secret-looking content. What it writes: nothing, except one JSON document on
stdout. It never prints a secret value, a prefix of one or its length; findings
carry the file, line, variable name and a category only.

Exit codes: 0 = no finding at or above --fail-on (default high);
1 = at least one such finding; 2 = bad usage (missing or non-directory path).

Standard library only. No network, no subprocess.
"""
import base64
import json
import os
import re
import sys

VERSION = "0.1.0"

# Directories that hold dependencies, build output or caches. Secrets found there
# are copies of something else, and walking them is slow.
SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", ".output", ".svelte-kit",
    ".venv", "venv", "__pycache__", ".dart_tool", "Pods", ".gradle", "coverage",
    ".turbo", ".firebase", "target", ".cache", ".parcel-cache",
}
MAX_FILE_BYTES = 1_000_000   # larger files are bundles or data dumps, not config
MAX_FILES = 20000            # hard stop so a huge monorepo cannot hang the audit

SEVERITIES = ["critical", "high", "medium", "low", "info"]
RANK = {s: i for i, s in enumerate(SEVERITIES)}

# Public-by-design prefixes: anything with one of these is compiled into the client
# bundle by the framework (verify the list for your framework against its docs).
PUBLIC_PREFIXES = (
    "NEXT_PUBLIC_", "VITE_", "REACT_APP_", "EXPO_PUBLIC_", "PUBLIC_", "NUXT_PUBLIC_",
    "GATSBY_", "VUE_APP_", "NG_APP_",
)
TEMPLATE_SUFFIXES = ("example", "sample", "template", "dist", "defaults")

# Names that mean "this holds a secret".
SECRET_NAME = re.compile(
    r"(SERVICE[_-]?ROLE|SECRET|PRIVATE[_-]?KEY|PASSWORD|PASSWD|ADMIN[_-]?(API[_-]?)?KEY|"
    r"SERVICE[_-]?ACCOUNT|ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|API[_-]?SECRET)", re.I)
PLACEHOLDER = re.compile(
    r"^(|<.*>|\[.*\]|\$\{.*\}|\$\(.*\)|%.*%|\{\{.*\}\}|x{3,}|\*{3,}|\.{3,}|0+|"
    r"(your|my|the)[-_ ].*|.*(changeme|change-me|replace[-_ ]?me|placeholder|example|dummy|todo|"
    r"redacted|insert[-_ ]|not[-_ ]set).*|true|false|null|none|undefined)$", re.I)

# Value patterns. Built from pieces where a literal would look like a real credential.
PRIVATE_KEY_RE = re.compile("-----BEGIN (?:[A-Z]+ )*PRIVATE KEY" + "-----")
VALUE_PATTERNS = [
    ("aws_access_key_id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_block", PRIVATE_KEY_RE),
    ("payment_live_secret", re.compile(r"sk_live_[0-9A-Za-z]{16,}")),
    ("llm_style_secret_token", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("baas_secret_key_format", re.compile(r"sb_secret_[A-Za-z0-9_-]{16,}")),
    ("service_account_json", re.compile(r'"type"\s*:\s*"service_account"')),
    ("database_url_with_password",
     re.compile(r"(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^/\s:@'\"]+:[^@\s'\"]{3,}@")),
]
JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.(eyJ[A-Za-z0-9_-]{8,})\.[A-Za-z0-9_-]{8,}")
SOURCE_ASSIGN = re.compile(
    r"""["']?([A-Za-z0-9_.-]*(?:service[_-]?role|secret|private[_-]?key|api[_-]?secret|admin[_-]?key)"""
    r"""[A-Za-z0-9_.-]*)["']?\s*[:=]\s*["']([^"'\s]{12,})["']""", re.I)

SOURCE_EXT = {
    ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".html", ".htm", ".json",
    ".yaml", ".yml", ".toml", ".dart", ".swift", ".kt", ".java", ".xml", ".plist", ".gradle",
    ".properties", ".py", ".go", ".rb", ".php", ".sql",
    ".pem", ".key", ".sh", ".txt", ".cfg", ".ini",
}
CLIENT_DIRS = {"public", "www", "static", "client", "frontend", "web", "pages", "components",
               "assets", "lib", "android", "ios", "mobile"}
CLIENT_EXT = {".html", ".htm", ".vue", ".svelte", ".jsx", ".tsx", ".dart", ".swift", ".kt"}
SERVER_DIRS = {"functions", "server", "api", "backend", "scripts", "workers"}

NOTES_NOT_CHECKED = [
    "Live backend settings (dashboard toggles, deployed rules, provider config) are not visible from files.",
    "Policy logic is matched by pattern; a policy that looks restrictive can still be wrong.",
    "Git history is not searched; a secret removed from the tree can remain in old commits.",
    "A global gitignore file and a .git file (worktree) are not read.",
]


# ---------------------------------------------------------------- helpers
def read_text(path):
    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_FILE_BYTES + 1)
    except OSError:
        return None
    if len(raw) > MAX_FILE_BYTES or b"\x00" in raw[:4096]:
        return None
    return raw.decode("utf-8", errors="replace")


def rel_posix(path, base):
    return os.path.relpath(path, base).replace(os.sep, "/")


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def blank_comments(text, line_style, block=True):
    """Replace comments by spaces, keeping newlines so line numbers stay right."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    if block:
        text = re.sub(r"/\*.*?\*/", blank, text, flags=re.S)
    return re.sub(line_style + r"[^\n]*", blank, text)


def is_placeholder(value):
    return bool(PLACEHOLDER.match(value.strip()))


def is_public_name(name):
    return name.upper().startswith(PUBLIC_PREFIXES)


def env_class(basename):
    """Return (kind, label): kind is 'template', 'env' or None."""
    low = basename.lower()
    if not (low == ".env" or low.startswith(".env.") or low.endswith(".env")):
        return None, None
    parts = [p for p in low.split(".") if p]
    if parts and parts[-1] in TEMPLATE_SUFFIXES:
        return "template", "template"
    rest = [p for p in parts if p != "env"]
    label = rest[0] if rest else "base"
    mapping = {"production": "prod", "prod": "prod", "staging": "staging", "stage": "staging",
               "preview": "staging", "qa": "staging", "development": "dev", "dev": "dev",
               "test": "test", "local": "local", "base": "base"}
    return "env", mapping.get(label, label)


def parse_env(text):
    entries = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        name, value = m.group(1), m.group(2)
        if value[:1] in ("'", '"'):
            end = value.find(value[0], 1)
            value = value[1:end] if end > 0 else value[1:]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        entries.append((name, value, number))
    return entries


def classify_value(value):
    """Return ('secret', kind), ('public', kind) or (None, None). Never returns the value."""
    m = JWT_RE.search(value)
    if m:
        try:
            payload = m.group(1)
            payload += "=" * (-len(payload) % 4)
            role = json.loads(base64.urlsafe_b64decode(payload.encode("ascii"))).get("role")
        except (ValueError, TypeError, AttributeError):
            role = None
        if role == "service_role":
            return "secret", "service_role_jwt"
        if role == "anon":
            return "public", "anon_jwt"
        return None, None
    if "sb_publishable_" in value:
        return "public", "publishable_key"
    for kind, rx in VALUE_PATTERNS:
        m = rx.search(value)
        if m:
            if kind == "database_url_with_password" and weak_password(m.group(0)):
                continue
            return "secret", kind
    return None, None


# Passwords that documentation and tests use; a URL carrying one is not a leaked credential.
WEAK_PASSWORDS = {"pass", "password", "passwd", "secret", "user", "admin", "root", "test", "changeme", "xxx", "xxxx"}


def weak_password(url_head):
    m = re.search(r"://[^:/]*:([^@]*)@", url_head)
    pw = m.group(1).lower() if m else ""
    return pw in WEAK_PASSWORDS or pw[:1] in ("$", "<", "{", "%") or is_placeholder(pw)


# ---------------------------------------------------------------- gitignore
def gitignore_regex(pattern):
    chars, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            chars.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            chars.append("/.*")
            i += 3
        elif pattern.startswith("**", i):
            chars.append(".*")
            i += 2
        elif c == "*":
            chars.append("[^/]*")
            i += 1
        elif c == "?":
            chars.append("[^/]")
            i += 1
        elif c == "[":
            end = pattern.find("]", i + 2)
            if end == -1:
                chars.append(re.escape(c))
                i += 1
            else:
                body = pattern[i + 1:end].replace("\\", "\\\\")
                if body.startswith("!"):
                    body = "^" + body[1:]
                chars.append("[" + body + "]")
                i = end + 1
        elif c == "\\" and i + 1 < len(pattern):
            chars.append(re.escape(pattern[i + 1]))
            i += 2
        else:
            chars.append(re.escape(c))
            i += 1
    return "".join(chars)


def load_ignore_rules(path):
    text = read_text(path)
    rules = []
    if text is None:
        return rules
    for raw in text.splitlines():
        line = raw.rstrip("\r\n")
        line = re.sub(r"(?<!\\)\s+$", "", line)
        if not line or line.startswith("#"):
            continue
        negate = line.startswith("!")
        if negate:
            line = line[1:]
        if line.startswith("\\#") or line.startswith("\\!"):
            line = line[1:]
        dir_only = line.endswith("/")
        line = line.rstrip("/")
        if not line:
            continue
        anchored = "/" in line
        line = line.lstrip("/")
        body = gitignore_regex(line)
        rx = re.compile("^" + ("" if anchored else "(?:.*/)?") + body + "$")
        rules.append((rx, negate, dir_only))
    return rules


class IgnoreMatcher:
    def __init__(self, base):
        self.base = base
        self.cache = {}

    def rules_for(self, directory):
        if directory not in self.cache:
            rules = load_ignore_rules(os.path.join(directory, ".gitignore"))
            if directory == self.base:
                rules = load_ignore_rules(os.path.join(directory, ".git", "info", "exclude")) + rules
            self.cache[directory] = rules
        return self.cache[directory]

    def _evaluate(self, parts, is_dir):
        result = None
        full = os.path.join(self.base, *parts)
        directory = self.base
        chain = [directory]
        for part in parts[:-1]:
            directory = os.path.join(directory, part)
            chain.append(directory)
        for d in chain:
            rel = os.path.relpath(full, d).replace(os.sep, "/")
            for rx, negate, dir_only in self.rules_for(d):
                if dir_only and not is_dir:
                    continue
                if rx.match(rel):
                    result = not negate
        return bool(result)

    def is_ignored(self, path):
        parts = os.path.relpath(path, self.base).split(os.sep)
        for i in range(1, len(parts) + 1):
            if self._evaluate(parts[:i], i < len(parts)):
                return True
        return False


def read_git_index(repo_root):
    """Return the set of tracked paths from .git/index (v2/v3), or None if unreadable."""
    index_path = os.path.join(repo_root, ".git", "index")
    try:
        with open(index_path, "rb") as fh:
            data = fh.read()
        return parse_index(data)
    except OSError:
        return None


def parse_index(data):
    try:
        if data[:4] != b"DIRC":
            return None
        version = int.from_bytes(data[4:8], "big")
        if version not in (2, 3):
            return None  # version 4 compresses path prefixes; not parsed
        count = int.from_bytes(data[8:12], "big")
        pos, paths = 12, set()
        for _ in range(count):
            flags = int.from_bytes(data[pos + 60:pos + 62], "big")
            name_at = pos + 62 + (2 if version == 3 and flags & 0x4000 else 0)
            end = data.index(b"\x00", name_at)
            paths.add(data[name_at:end].decode("utf-8", errors="replace"))
            size = (name_at - pos) + (end - name_at)
            pos += size + (8 - size % 8)
        return paths
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------- audit
class Audit:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.findings = []
        self.seen = set()
        self.files = []
        self.truncated = False
        self.repo_root = self.find_repo_root()
        self.base = self.repo_root or self.root
        self.ignore = IgnoreMatcher(self.base)
        self.tracked = read_git_index(self.repo_root) if self.repo_root else None

    def find_repo_root(self):
        cur = self.root
        for _ in range(12):
            if os.path.isdir(os.path.join(cur, ".git")):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        return None

    def add(self, severity, category, path, detail, fix, line=None, key=None):
        rel = rel_posix(path, self.root) if os.path.isabs(path) else path
        sig = (category, rel, line, key)
        if sig in self.seen:
            return
        self.seen.add(sig)
        item = {"severity": severity, "category": category, "file": rel, "line": line,
                "key": key, "detail": detail, "fix": fix}
        self.findings.append(item)

    def walk(self):
        count = 0
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                path = os.path.join(dirpath, name)
                if os.path.islink(path):
                    continue
                count += 1
                if count > MAX_FILES:
                    self.truncated = True
                    return
                self.files.append(path)

    # ---- env files
    def audit_env(self):
        by_dir = {}
        any_env = False
        for path in self.files:
            kind, label = env_class(os.path.basename(path))
            if not kind:
                continue
            text = read_text(path)
            if text is None:
                continue
            any_env = True
            entries = parse_env(text)
            by_dir.setdefault(os.path.dirname(path), []).append((path, kind, label, entries))
            ignored = self.ignore.is_ignored(path)
            tracked = None
            if self.tracked is not None:
                tracked = rel_posix(path, self.base) in self.tracked
            secret_seen = False
            for name, value, number in entries:
                verdict, vkind = classify_value(value)
                by_name = bool(SECRET_NAME.search(name)) and not is_placeholder(value) and len(value) >= 8
                secret = verdict == "secret" or (by_name and verdict != "public")
                if is_public_name(name) and (SECRET_NAME.search(name) or verdict == "secret"):
                    real = secret and not is_placeholder(value)
                    self.add("critical" if real else "high", "env_public_var_secret", path,
                             "A variable with a client-bundle prefix is named for or holds a secret; "
                             "it would be shipped to every browser or app user.",
                             "Remove the public prefix, move the value to server-only config, rotate the key "
                             "if it was ever deployed.", number, name)
                    continue
                if not secret:
                    continue
                secret_seen = True
                what = vkind or "secret_by_name"
                if kind == "template":
                    self.add("high", "env_example_real_value", path,
                             "A template env file holds a real-looking secret (%s); templates are committed." % what,
                             "Replace with a placeholder and rotate the key.", number, name)
                elif tracked is True:
                    self.add("critical", "env_secret_tracked", path,
                             "Secret (%s) sits in a file that git tracks." % what,
                             "Rotate the key, untrack the file (git rm --cached), add it to .gitignore.", number, name)
                elif not ignored:
                    extra = "" if tracked is False else " Git index not readable, so tracked state is unknown."
                    self.add("critical", "env_secret_not_ignored", path,
                             "Secret (%s) in an env file that no .gitignore rule covers.%s" % (what, extra),
                             "Add the file to .gitignore before the first commit; rotate if it was committed.",
                             number, name)
            if kind == "env" and not secret_seen:
                if tracked is True:
                    self.add("medium", "env_file_tracked", path, "Env file is tracked by git (no secret found in it).",
                             "Keep only a .env.example in git.")
                elif not ignored:
                    self.add("medium", "env_file_not_ignored", path,
                             "Env file is not covered by .gitignore (no secret found in it today).",
                             "Ignore .env* and allow only the example file.")
        if any_env and not self.ignore.rules_for(self.base):
            self.add("medium", "no_gitignore", self.base, "Env files exist but no .gitignore was found at the repo root.",
                     "Create a .gitignore that ignores .env* except the example file.")
        for directory, group in by_dir.items():
            self.audit_env_group(directory, group)

    def audit_env_group(self, directory, group):
        base_keys, example_keys = {}, set()
        classes = {}
        for path, kind, label, entries in group:
            keys = {n for n, _, _ in entries}
            if kind == "template":
                example_keys |= keys
            elif label == "base":
                base_keys[path] = keys
            elif label in ("dev", "staging", "prod", "test"):
                classes.setdefault(label, []).append((path, entries))
        shared_base = set().union(*base_keys.values()) if base_keys else set()
        eff = {}
        for label, items in classes.items():
            keys = set(shared_base)
            for _, entries in items:
                keys |= {n for n, _, _ in entries}
            eff[label] = keys
        if len(eff) >= 2:
            union = set().union(*eff.values()) | example_keys
            for key in sorted(union):
                missing = sorted(l for l in eff if key not in eff[l])
                if missing:
                    where = sorted(l for l in eff if key in eff[l])
                    note = " (documented in the example file)" if key in example_keys else ""
                    first = classes[missing[0]][0][0]
                    self.add("medium", "env_key_drift", first,
                             "Key is set for %s but missing for %s%s." % (
                                 ", ".join(where) or "no environment", ", ".join(missing), note),
                             "Add the key to every environment (with that environment's own value) or remove it everywhere.",
                             None, key)
        prod = classes.get("prod")
        if prod:
            prod_vals = {}
            for path, entries in prod:
                for name, value, number in entries:
                    prod_vals[name] = (value, path, number)
                    if re.search(r"(URL|HOST|ORIGIN|ENDPOINT|DOMAIN)", name, re.I) and re.search(
                            r"(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.0\.2\.2)", value):
                        self.add("high", "env_prod_points_to_local", path,
                                 "Production env value points at a local address.",
                                 "Set the production backend URL.", number, name)
            for label in ("dev", "staging", "test"):
                for path, entries in classes.get(label, []):
                    for name, value, number in entries:
                        if name in prod_vals and not is_placeholder(value) and value == prod_vals[name][0] and re.search(
                                r"(KEY|SECRET|TOKEN|PASSWORD|URL|PROJECT|BUCKET|DATABASE|HOST)", name, re.I):
                            self.add("high", "env_value_shared_with_prod", path,
                                     "%s uses the same value as production; the %s environment reaches production data or keys."
                                     % (label, label),
                                     "Create a separate backend project or database for %s and give it its own keys." % label,
                                     number, name)

    # ---- source files
    def audit_source(self):
        for path in self.files:
            name = os.path.basename(path)
            ext = os.path.splitext(name)[1].lower()
            if ext not in SOURCE_EXT or env_class(name)[0]:
                continue
            if name.endswith("lock.json") or name.endswith(".lock") or name == "package-lock.json":
                continue
            if self.ignore.is_ignored(path):
                continue
            text = read_text(path)
            if text is None:
                continue
            parts = set(os.path.relpath(path, self.root).replace("\\", "/").lower().split("/")[:-1])
            client = bool(parts & CLIENT_DIRS) or ext in CLIENT_EXT
            if parts & SERVER_DIRS:
                client = False
            severity = "critical" if client else "high"
            if re.search(r"(\.spec\.|\.test\.|__tests?__|(^|/)tests?/|fixtures?/)", rel_posix(path, self.root).lower()):
                severity = "medium"  # test code: still worth a look, rarely a live credential
            where = "client-side file" if client else "source file"
            seen_lines = set()
            for m in JWT_RE.finditer(text):
                verdict, kind = classify_value(m.group(0))
                if verdict == "secret":
                    ln = line_of(text, m.start())
                    seen_lines.add(ln)
                    self.add(severity, "source_secret", path, "Service-role style JWT inside a %s." % where,
                             "Remove it, rotate the key, read it from server-only environment config.", ln, kind)
            for kind, rx in VALUE_PATTERNS:
                if kind == "service_account_json" and ext != ".json":
                    continue
                for m in rx.finditer(text):
                    ln = line_of(text, m.start())
                    if ln in seen_lines:
                        continue
                    if kind == "database_url_with_password" and weak_password(m.group(0)):
                        continue
                    seen_lines.add(ln)
                    self.add(severity, "source_secret", path, "%s inside a %s." % (kind, where),
                             "Remove it, rotate the key, read it from server-only environment config.", ln, kind)
            for m in SOURCE_ASSIGN.finditer(text):
                value = m.group(2)
                if is_placeholder(value) or re.match(r"^(process\.env|import\.meta|os\.environ|\$)", value):
                    continue
                ln = line_of(text, m.start())
                if ln in seen_lines:
                    continue
                seen_lines.add(ln)
                self.add(severity, "source_secret", path,
                         "Secret-named assignment with a literal value inside a %s." % where,
                         "Move the value to server-only environment config and rotate it.", ln, m.group(1)[:60])

    # ---- rules and policies
    def audit_rules(self):
        for path in self.files:
            name = os.path.basename(path).lower()
            if name.endswith(".rules.json") or name == "database.rules.json":
                self.audit_rtdb(path)
            elif name.endswith(".rules"):
                self.audit_rules_file(path)
            elif name == "firebase.json":
                self.audit_firebase_json(path)
            elif name == "appwrite.json":
                self.audit_appwrite(path)
            elif name == "config.toml" and os.path.basename(os.path.dirname(path)).lower() == "supabase":
                self.audit_supabase_config(path)
        self.audit_sql()

    def audit_rules_file(self, path):
        text = read_text(path)
        if text is None:
            return
        clean = blank_comments(text, r"//")
        found = False
        for m in re.finditer(r"\ballow\s+([a-z ,]+?)\s*(?::\s*if\s+(.*?))?\s*;", clean, flags=re.S):
            found = True
            methods = {x.strip() for x in m.group(1).split(",") if x.strip()}
            cond = re.sub(r"\s+", "", m.group(2) or "")
            ln = line_of(clean, m.start())
            writes = bool(methods & {"write", "create", "update", "delete"})
            sev = "critical" if writes else "medium"
            label = ", ".join(sorted(methods))
            if m.group(2) is None or cond == "true":
                self.add(sev, "rules_open", path, "Rule allows %s for everyone (no condition)." % label,
                         "Require an owner or role check; for intended public reads, document it.", ln, label)
            elif re.match(r"request\.time<", cond) and "request.auth" not in cond:
                self.add("high", "rules_time_bounded_open", path,
                         "Rule allows %s until a date, with no auth check (test-mode rule). It is open "
                         "today and the app breaks on that date." % label,
                         "Replace with an auth and ownership rule now.", ln, label)
            elif cond == "request.auth!=null":
                self.add("medium", "rules_auth_only", path,
                         "Rule allows %s for any signed-in user, not just the owner." % label,
                         "Compare request.auth.uid with the owner field or a role claim.", ln, label)
        if not found:
            self.add("info", "rules_file_no_allow", path, "Rules file has no allow statement, so it denies everything.",
                     "Confirm this is intended.")

    def audit_rtdb(self, path):
        text = read_text(path)
        if text is None:
            return
        try:
            data = json.loads(text)
        except ValueError:
            self.add("low", "rules_unparsable", path, "Rules JSON could not be parsed.", "Fix the JSON.")
            return

        def walk(node, trail):
            if isinstance(node, dict):
                for key, val in node.items():
                    here = trail + [key]
                    if key in (".read", ".write"):
                        v = str(val).strip().lower()
                        spot = "/".join(here)
                        if v == "true":
                            self.add("critical" if key == ".write" else "medium", "rules_open", path,
                                     "%s is true: open to everyone." % key, "Require auth and ownership.", None, spot)
                        elif re.match(r"^now\s*<", v) and "auth" not in v:
                            self.add("high", "rules_time_bounded_open", path,
                                     "%s is open until a date (test-mode rule)." % key, "Replace with an auth rule.",
                                     None, spot)
                        elif v.replace(" ", "") == "auth!=null":
                            self.add("medium", "rules_auth_only", path,
                                     "%s allows any signed-in user." % key, "Compare auth.uid with the owner.", None, spot)
                    else:
                        walk(val, here)
        walk(data, [])

    def audit_firebase_json(self, path):
        text = read_text(path)
        try:
            data = json.loads(text or "")
        except ValueError:
            return
        entries = []
        for section in ("firestore", "storage", "database"):
            node = data.get(section) if isinstance(data, dict) else None
            nodes = node if isinstance(node, list) else [node] if isinstance(node, dict) else []
            for n in nodes:
                entries.append((section, n.get("rules") if isinstance(n, dict) else None))
        for section, rules in entries:
            if not rules:
                self.add("medium", "rules_not_configured", path,
                         "firebase.json has a %s section without a rules file; defaults may be open or closed "
                         "depending on how the project was created (verify against vendor docs, unconfirmed)." % section,
                         "Point it at a committed rules file.", None, section)
            elif not os.path.exists(os.path.join(os.path.dirname(path), rules)):
                self.add("high", "rules_file_missing", path, "Referenced %s rules file does not exist." % section,
                         "Create the file or fix the path before deploying.", None, section)

    def audit_appwrite(self, path):
        text = read_text(path)
        if text is None:
            return
        for m in re.finditer(r"(create|update|delete|write)\(\\*[\"']any\\*[\"']\)", text):
            self.add("high", "rules_open", path,
                     "Permission %s(any) lets anonymous callers change data (verify the permission syntax "
                     "against vendor docs, unconfirmed)." % m.group(1),
                     "Use a role such as users or a specific user or team.", line_of(text, m.start()), m.group(1) + "(any)")

    def audit_supabase_config(self, path):
        text = read_text(path)
        if text is None:
            return
        for m in re.finditer(r"\[storage\.buckets\.([\w-]+)\]([^\[]*)", text):
            if re.search(r"public\s*=\s*true", m.group(2)):
                self.add("low", "public_bucket", path,
                         "Bucket is public: files are readable by anyone with the URL (verify against vendor docs, "
                         "unconfirmed).", "Keep only intentionally public assets in it.", line_of(text, m.start()), m.group(1))

    def audit_sql(self):
        tables, rls, policy_count = {}, set(), {}
        saw_policy_file = False
        saw_supabase_dir = any(os.sep + "supabase" + os.sep in p or p.endswith(os.sep + "supabase") for p in self.files)

        def norm(name):
            name = name.replace('"', "").strip().lower()
            if name.startswith("public."):
                name = name[7:]
            return None if "." in name else name

        for path in self.files:
            if not path.lower().endswith(".sql"):
                continue
            text = read_text(path)
            if text is None:
                continue
            clean = blank_comments(text, r"--")
            for m in re.finditer(r"create\s+table\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)", clean, flags=re.I):
                n = norm(m.group(1))
                if n:
                    tables.setdefault(n, (path, line_of(clean, m.start())))
            for m in re.finditer(r"alter\s+table\s+(?:if\s+exists\s+)?(?:only\s+)?([\w.\"]+)\s+enable\s+row\s+level\s+security",
                                 clean, flags=re.I):
                n = norm(m.group(1))
                if n:
                    rls.add(n)
            for m in re.finditer(r"create\s+policy\s+(\"[^\"]+\"|\S+)\s+on\s+([\w.\"]+)([^;]*);", clean, flags=re.I | re.S):
                saw_policy_file = True
                n = norm(m.group(2))
                body = m.group(3)
                if n:
                    policy_count[n] = policy_count.get(n, 0) + 1
                cmd = re.search(r"\bfor\s+(all|select|insert|update|delete)\b", body, flags=re.I)
                cmd = cmd.group(1).lower() if cmd else "all"
                roles = re.search(r"\bto\s+([\w\s,\"]+?)(?:\busing\b|\bwith\b|$)", body, flags=re.I | re.S)
                roles = roles.group(1).lower() if roles else "public"
                if re.search(r"\busing\s*\(\s*true\s*\)", body, flags=re.I) or re.search(
                        r"\bwith\s+check\s*\(\s*true\s*\)", body, flags=re.I):
                    exposed = "anon" in roles or "public" in roles
                    sev = "high" if cmd != "select" else "medium"
                    self.add(sev, "policy_open", path,
                             "Policy on %s for %s is always true%s." % (n or "table", cmd.upper(),
                                                                       " and applies to anonymous callers" if exposed else ""),
                             "Compare the row owner with auth.uid() or a tenant claim.",
                             line_of(clean, m.start()), n)
            for m in re.finditer(r"grant\s+(?:all|insert|update|delete)[^;]*\bto\s+[^;]*\banon\b", clean, flags=re.I):
                self.add("high", "grant_to_anon", path, "Write-capable grant to the anonymous role.",
                         "Grant only select, and only where a policy limits rows.", line_of(clean, m.start()))
            for m in re.finditer(r"security\s+definer", clean, flags=re.I):
                window = clean[max(0, m.start() - 400):m.end() + 400]
                if not re.search(r"search_path", window, flags=re.I):
                    self.add("medium", "definer_no_search_path", path,
                             "SECURITY DEFINER function without a fixed search_path nearby (approximate check).",
                             "Add SET search_path = '' and schema-qualify names.", line_of(clean, m.start()))
        for table, (path, ln) in sorted(tables.items()):
            if table not in rls:
                self.add("high", "table_without_rls", path,
                         "Table %s is created in the public schema without enabling row level security in any SQL file." % table,
                         "Enable RLS and add policies in the same migration.", ln, table)
            elif not policy_count.get(table):
                self.add("low", "rls_without_policy", path,
                         "Table %s has RLS enabled and no policy: only the service key can read it." % table,
                         "Add policies, or confirm the table is server-only.", ln, table)
        if saw_supabase_dir and not saw_policy_file and not tables:
            self.add("info", "no_policy_files_found", self.root, "A supabase folder exists but no SQL file defines tables or policies; "
                     "policies may live only in the dashboard.", "Export them to migrations so review is possible.")

    def run(self):
        self.walk()
        self.audit_env()
        self.audit_source()
        self.audit_rules()
        self.findings.sort(key=lambda f: (RANK[f["severity"]], f["file"], f["line"] or 0, f["category"], f["key"] or ""))
        for i, f in enumerate(self.findings, 1):
            f["id"] = "F%03d" % i
        counts = {s: 0 for s in SEVERITIES}
        for f in self.findings:
            counts[f["severity"]] += 1
        return counts


def main(argv):
    args = list(argv)
    fail_on = "high"
    if "--fail-on" in args:
        i = args.index("--fail-on")
        try:
            fail_on = args[i + 1]
            del args[i:i + 2]
        except IndexError:
            fail_on = ""
    if fail_on not in ("critical", "high", "medium", "never") or len(args) != 1 or not os.path.isdir(args[0]):
        sys.stderr.write("usage: baas_audit.py <project-folder> [--fail-on critical|high|medium|never]\n"
                         "The folder must exist and be a directory.\n")
        return 2
    audit = Audit(args[0])
    counts = audit.run()
    if counts["critical"] or counts["high"]:
        verdict = "fail"
    elif counts["medium"]:
        verdict = "review"
    else:
        verdict = "pass"
    report = {
        "tool": "baas_audit", "version": VERSION, "root": args[0],
        "git": {"repo_found": audit.repo_root is not None, "index_readable": audit.tracked is not None},
        "files_scanned": len(audit.files), "truncated": audit.truncated,
        "summary": counts, "verdict": verdict, "findings": audit.findings,
        "not_checked": NOTES_NOT_CHECKED,
    }
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n")
    limit = {"critical": 0, "high": 1, "medium": 2}.get(fail_on)
    if limit is not None and any(RANK[f["severity"]] <= limit for f in audit.findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
