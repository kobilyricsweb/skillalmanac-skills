#!/usr/bin/env python3
"""Statically scan an agent-skill folder and print a risk table as strict JSON.

    python skill_audit.py scan <skill-folder>

Reads every file under the folder (it never executes, imports or modifies anything
there, and it follows no symbolic links). Writes nothing. Prints one JSON object on
stdout; problems go to stderr as one plain sentence.

Exit codes
    0  verdict low-risk    (no finding above "low")
    1  verdict needs-review (highest finding is "medium")
    3  verdict high-risk   (at least one "high" finding)
    2  usage error, folder missing, or no SKILL.md in the folder

JSON contract (schema_version 1)
    {"schema_version": 1, "command": "scan", "skill": str, "name": str|null,
     "summary": {"verdict": "low-risk"|"needs-review"|"high-risk",
                 "counts": {"high": int, "medium": int, "low": int, "info": int},
                 "files_scanned": int, "bytes_scanned": int,
                 "hosts": [str], "suppressed_findings": int},
     "frontmatter": {"present": bool, "bytes": int, "keys": [str],
                     "description_chars": int, "declared_network": str|null},
     "risk_table": [{"capability": str, "level": "none"|"info"|"low"|"medium"|"high",
                     "findings": int, "evidence": [str]}],
     "findings": [{"id": str, "file": str, "line": int, "capability": str,
                   "severity": "high"|"medium"|"low"|"info", "rule": str,
                   "context": "frontmatter"|"body"|"fenced-block"|"comment"|"code"|"file",
                   "evidence": str}],
     "limitations": [str]}
    risk_table always has the 12 capabilities in a fixed order. Findings are sorted by
    severity (high first), then file, then line, and numbered F001, F002, ... At most
    MAX_PER_RULE_PER_FILE findings per rule and file are listed; the rest are counted
    in summary.suppressed_findings (they still count towards the verdict).

What this is not: a sandbox, a malware engine or proof of safety. It matches text
patterns. A skill with no findings can still be harmful; a skill with findings is
often honest. A person (or the agent) triages every medium and high finding.
"""
import json
import os
import re
import sys

SCHEMA_VERSION = 1

# Thresholds. Each has a reason; change them only with a reason.
MAX_READ_BYTES = 2_000_000      # a text file bigger than this is itself suspicious; read only the first 2 MB
BIG_FILE_BYTES = 200_000        # house standard: no single file over 200 KB
BIG_PACKAGE_BYTES = 1_000_000   # house standard: package under 1 MB
MANY_FILES = 200                # a skill is a few files; hundreds hide things
BLOB_MEDIUM = 80                # base64-like run: shorter than 80 is usually a hash, path or identifier
BLOB_HIGH = 200                 # 200+ characters is a payload, not an identifier
HEX_ESCAPES_MIN = 8             # 8 consecutive \xNN escapes spell a short byte string
LONG_HEX_MIN = 128              # 128 hex digits is longer than any common hash (SHA-512 is 128, so >= means 'at least a hash')
MINIFIED_LINE = 1000            # a code line over 1000 characters is packed or generated
FM_BYTES_MEDIUM = 2048          # frontmatter is loaded for every installed skill; 2 KB is already large
FM_BYTES_HIGH = 8192            # 8 KB of frontmatter is context stuffing
DESC_MAX = 1024                 # open-spec limit for the description
EVIDENCE_CHARS = 160            # keeps the report readable
MAX_PER_RULE_PER_FILE = 5       # one noisy file must not bury the rest

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3}
LEVEL_NAMES = ["info", "low", "medium", "high"]

CAPABILITIES = [
    "network", "subprocess_shell", "dynamic_exec", "env_credentials", "file_writes",
    "persistence_config", "obfuscation", "prompt_injection", "installs_remote",
    "destructive_privileged", "package", "frontmatter",
]

SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

CODE_EXT = {
    ".py": "py", ".js": "js", ".mjs": "js", ".cjs": "js", ".ts": "js", ".jsx": "js", ".tsx": "js",
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".ps1": "shell", ".bat": "shell", ".cmd": "shell",
    ".rb": "other", ".pl": "other", ".php": "other", ".lua": "other", ".vbs": "other",
}
EXECUTABLE_EXT = {".exe", ".dll", ".so", ".dylib", ".bin", ".com", ".msi", ".jar", ".class", ".pyc",
                  ".pyd", ".whl", ".node", ".wasm", ".apk", ".scr", ".app"}
ARCHIVE_EXT = {".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".bz2", ".xz"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp"}
ALL_KINDS = {"py", "js", "shell", "other", "doc"}
CODE_KINDS = {"py", "js", "shell", "other"}


def _chars(*codes):
    return "".join(chr(c) for c in codes)


# Invisible characters, written as code points so this file stays plain ASCII.
TAG_CHARS = re.compile("[" + _chars(0xE0000) + "-" + _chars(0xE007F) + "]")
BIDI_CHARS = re.compile("[" + _chars(0x202A) + "-" + _chars(0x202E) + _chars(0x2066) + "-" + _chars(0x2069) + "]")
ZERO_WIDTH = re.compile("[" + _chars(0x200B) + "-" + _chars(0x200F) + _chars(0x2060) + "-" + _chars(0x2064)
                        + _chars(0x180E) + _chars(0xFEFF) + _chars(0xE0100) + "-" + _chars(0xE01EF) + "]")
ANY_INVISIBLE = re.compile("[" + _chars(0x200B) + "-" + _chars(0x200F) + _chars(0x202A) + "-" + _chars(0x202E)
                           + _chars(0x2060) + "-" + _chars(0x2069) + _chars(0x180E) + _chars(0xFEFF)
                           + _chars(0xE0000) + "-" + _chars(0xE01EF) + "]")

I = re.I

# Words are assembled from parts so this file does not itself read like an attack.
WRITE_CALL = (
    r"\bopen\s*\(.*?,\s*(?:mode\s*=\s*)?['\"][rwaxbt+]*[wax+][rwaxbt+]*['\"]|\.write_text\s*\(|\.write_bytes\s*\(|"
    r"\bshutil\.(?:copy\w*|move|rmtree|copytree)\s*\(|"
    r"\bos\.(?:remove|unlink|rmdir|removedirs|rename|replace|makedirs|mkdir|chmod|symlink)\s*\(|"
    r"\bfs\.(?:writeFile\w*|appendFile\w*|rm\w*|unlink\w*|rename\w*|mkdir\w*|copyFile\w*|createWriteStream)\b|"
    r"\.(?:unlink|rmdir|touch)\s*\(|"
    r"(?:^|[\s;|&])(?:rm|mv|cp|tee|chmod|chown|ln|truncate|shred)\s+|"
    r"\b(?:Remove-Item|Set-Content|Out-File|Add-Content|New-Item|Copy-Item|Move-Item)\b"
)
SHELL_REDIRECT = r"(?<![<>=\-0-9])>>?\s*[^\s&>=]"
OUTSIDE_PATH = (
    r"~[/\\]|\$HOME|%USERPROFILE%|%APPDATA%|%TEMP%|\bexpanduser\b|\bPath\.home\s*\(|\bhomedir\b|"
    r"\$env:(?:USERPROFILE|APPDATA|HOME)|/tmp/|\.\./|\.\.\\|['\"](?:/home/|/Users/|[A-Za-z]:\\)"
)
SYSTEM_PATH = (
    r"/etc/|/usr/|/bin/|/sbin/|/var/|/opt/|/Library/|C:\\Windows|C:\\Program Files|System32|\bHKLM\b|\bHKCU\b|/dev/"
)
WRITE_VERB = r"\b(?:add|append|write|edit|modify|overwrite|replace|insert|create|update|patch)\b"
AGENT_PATH = (r"(?:\.claude[/\\](?:settings|hooks|commands|agents)|\bsettings\.local\.json\b|\.mcp\.json\b|"
              r"\.cursor[/\\]rules|\.codex[/\\]|\.gemini[/\\]|copilot-instructions)")

# rule = (rule_id, capability, base_severity, kinds, pattern, flags, boosts, description)
# boosts: list of (regex, severity); the last boost that matches on the same line sets the severity.
RULES = [
    # ---- network
    ("net-import", "network", "medium", CODE_KINDS,
     r"^\s*(?:import|from)\s+(?:urllib3?(?!\.parse\b)|requests|http\.client|httpx|aiohttp|socket|ftplib|smtplib|"
     r"telnetlib|websockets?|paramiko|pycurl)\b", 0, [], "imports a network library"),
    ("net-call", "network", "medium", CODE_KINDS,
     r"\burlopen\s*\(|\bfetch\s*\(|XMLHttpRequest|\baxios\b|new\s+WebSocket|"
     r"require\(\s*['\"](?:node:)?(?:https?|net|dgram|tls|http2)['\"]\s*\)|from\s+['\"](?:node:)?(?:https?|net|tls)['\"]|"
     r"\b(?:Invoke-WebRequest|Invoke-RestMethod|iwr|irm|Net\.WebClient|DownloadString|DownloadFile)\b", 0, [],
     "makes a network call"),
    ("net-shell", "network", "medium", {"shell", "other"},
     r"(?:^|[\s;|&(])(?:curl|wget|nc|ncat|netcat|scp|sftp|ssh|telnet|ftp)\s", 0, [], "shell network command"),
    ("net-doc-command", "network", "medium", {"doc"},
     r"(?:^|[\s;|&(`$])(?:curl|wget|Invoke-WebRequest)\s+\S", 0, [], "documentation tells the agent to run a network command"),
    ("net-remote-image", "network", "medium", {"doc"},
     r"!\[[^\]]*\]\(\s*https?://[^)\s]*[?&][^)\s]+\)", 0, [], "remote image URL with a query string (can carry data out)"),
    ("net-remote-embed", "network", "high", {"doc"},
     r"<script\b[^>]*\bsrc\s*=", I, [], "remote or local script tag in a document"),
    ("net-embed-frame", "network", "medium", {"doc"},
     r"<(?:iframe|object|embed)\b|javascript:", I, [], "frame, object or javascript: URL in a document"),
    # ---- remote fetch-and-run
    ("fetch-exec", "installs_remote", "high", ALL_KINDS,
     r"(?:curl|wget)[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z|k|da)?sh\b|(?:curl|wget)[^\n|]*\|\s*(?:python[0-9.]*|node|perl|ruby)\b|"
     r"\biex\s*\(|\biex\s+\(|Invoke-" r"Expression|bash\s+<\(\s*(?:curl|wget)|\|\s*iex\b|certutil\s+-urlcache", I, [],
     "downloads remote content and runs it"),
    ("install-cmd", "installs_remote", "medium", ALL_KINDS,
     r"\b(?:pip3?|pipx|npm|npx|pnpm|yarn|bun|gem|cargo|brew|apt(?:-get)?|choco|winget|dnf|yum)\s+"
     r"(?:install|add|i|run|exec)\b|\bpython[0-9.]*\s+-m\s+pip\s+install\b|\bnpx\s+\S|\buvx\s+\S|\bgo\s+install\b|\bgit\s+clone\b",
     0, [(r"==\s*\d|@\d+\.\d+|--hash", "low")], "installs or fetches code (unpinned unless noted)"),
    # ---- subprocess and dynamic execution
    ("subprocess", "subprocess_shell", "medium", CODE_KINDS,
     r"\bsubprocess\b|\bos\.(?:system|popen|exec\w+|spawn\w+|startfile)\s*\(|\bchild_process\b|"
     r"\b(?:execSync|spawnSync|execFileSync)\b|\bStart-Process\b|\bRuntime\.getRuntime\b|\bpty\.spawn|\bcommands\.getoutput",
     0, [(r"shell\s*=\s*True|\bshell:\s*true|\bos\.system\s*\(", "high")], "starts another process"),
    ("shell-script", "subprocess_shell", "low", {"shell"},
     r"\A", 0, [], "shell or batch script (runs arbitrary commands by nature)"),
    ("dyn-exec", "dynamic_exec", "high", CODE_KINDS,
     r"(?<![\w.])(?:eval|exec)\s*\(|(?<![\w.])__import__\s*\(|\bimportlib\.import_module\s*\(|\bpickle\.loads?\s*\(|"
     r"\bmarshal\.loads?\s*\(|\bnew\s+Function\s*\(|\bvm\.runIn\w*\(|(?:^|[;&|]\s*)eval\s+\S|\bsource\s+<\(|"
     r"(?<![\w.])compile\s*\([^)]*['\"](?:exec|eval)['\"]", 0, [], "runs text as code"),
    # ---- environment and credentials
    ("literal-credential", "env_credentials", "high", ALL_KINDS,
     r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}\b|-----BEGIN (?:[A-Z]+ )*PRIVATE KEY(?: BLOCK)?-----|"
     r"(?<![\w-])sk-[A-Za-z0-9_-]{20,}|\bgh[pousr]_[A-Za-z0-9]{36,}|\bxox[abprs]-[A-Za-z0-9-]{10,}|"
     r"(?<![A-Za-z0-9])(?:password|passwd|pwd)\s*[=:]\s*['\"]?(?![<${\[(*'\"\s])[^\s'\"]{4,}",
     I, [], "a literal credential (cloud key id, private-key block, API token or password) is written into the file"),
    ("split-string-dispatch", "dynamic_exec", "medium", CODE_KINDS,
     r"__import__\s*\(\s*['\"][^'\"]*['\"]\s*\+|getattr\s*\([^)]*['\"][^'\"]*['\"]\s*\+\s*['\"]", 0, [],
     "builds a module or function name from joined strings, a way to hide a call from text matching"),
    ("env-read", "env_credentials", "medium", CODE_KINDS,
     r"\bos\.environ\b|\bos\.getenv\s*\(|\bgetenv\s*\(|\bprocess\.env\b|\$env:\w+|System\.getenv|\benviron\s*\[", 0,
     [], "reads environment variables"),
    ("env-secret-name", "env_credentials", "high", CODE_KINDS,
     r"[\"'$]\{?[A-Za-z_]*(?:API_?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AWS_|GITHUB_|OPENAI|ANTHROPIC)[A-Za-z_]*\}?",
     0, [], "reads or names a secret-looking variable"),
    ("env-dump", "env_credentials", "high", CODE_KINDS,
     r"dict\s*\(\s*os\.environ\s*\)|os\.environ\.(?:items|copy|keys|values)\s*\(|\bprintenv\b|^\s*env\s*(?:$|\|)|"
     r"Object\.(?:keys|entries|assign)\s*\([^)]*process\.env|\bGet-ChildItem\s+env:|\{\s*\.\.\.process\.env\s*\}|"
     r"json\.dumps\(\s*(?:dict\()?os\.environ", 0, [], "dumps the whole environment"),
    ("cred-path-code", "env_credentials", "high", CODE_KINDS,
     r"\.ssh[/\\]|\bid_(?:rsa|ed25519|ecdsa|dsa)\b|\.aws[/\\]|\.netrc\b|\.npmrc\b|\.pypirc\b|\.docker[/\\]config|"
     r"\.kube[/\\]config|\.gnupg\b|\.git-credentials\b|Login Data\b|\bcookies\.sqlite\b|Chrome[/\\]User Data|"
     r"\.config[/\\]gcloud|\.azure[/\\]|security\s+find-generic-password|\bcredentials\.json\b|\bwallet\.dat\b|"
     r"(?<!\w)\.env(?:\.local|\.production)?\b(?!\()", 0, [], "script touches a credential store or secret file"),
    ("cred-path-doc", "env_credentials", "medium", {"doc"},
     r"\.ssh[/\\]|\bid_(?:rsa|ed25519|ecdsa|dsa)\b|\.aws[/\\]|\.netrc\b|\.npmrc\b|\.pypirc\b|\.docker[/\\]config|"
     r"\.kube[/\\]config|\.gnupg\b|\.git-credentials\b|\bcredentials\.json\b|(?<!\w)\.env(?:\.local|\.production)?\b(?!\()",
     0, [], "documentation points the agent at a credential store or secret file"),
    # ---- writes
    ("file-write", "file_writes", "low", CODE_KINDS,
     WRITE_CALL, 0,
     [(OUTSIDE_PATH, "medium"), (SYSTEM_PATH, "high")], "writes, moves or deletes files"),
    ("shell-redirect", "file_writes", "low", {"shell"},
     SHELL_REDIRECT, 0, [(OUTSIDE_PATH, "medium"), (SYSTEM_PATH, "high")], "shell redirect writes a file"),
    # ---- persistence and agent configuration
    ("persistence", "persistence_config", "high", ALL_KINDS,
     r"(?<!\w)\.bashrc|\.bash_profile|\.zshrc|\.zprofile|(?<![\w])\.profile\b|\bcrontab\b|/etc/cron|/etc/profile|"
     r"LaunchAgents|LaunchDaemons|\bsystemctl\b|/etc/systemd|authorized_keys|\.git[/\\]hooks|\bschtasks\b|"
     r"\breg\s+add\b|CurrentVersion[/\\]Run|Start Menu[/\\]Programs[/\\]Startup|\blaunchctl\b|\bsitecustomize\b|\busercustomize\b",
     0, [], "sets something to run later or at login"),
    ("agent-config-code", "persistence_config", "medium", CODE_KINDS,
     r"\.claude[/\\](?:settings|hooks|commands|agents|skills)|\bsettings\.local\.json\b|\bCLAUDE\.md\b|\bAGENTS\.md\b|"
     r"\.mcp\.json\b|\bmcp\.json\b|\.cursor[/\\]rules|\.codex[/\\]|\.gemini[/\\]|\.agents[/\\]skills|copilot-instructions",
     0, [(WRITE_CALL + "|" + SHELL_REDIRECT, "high")], "script references agent configuration paths"),
    ("agent-config-doc", "persistence_config", "medium", {"doc"},
     WRITE_VERB + r"[^\n]{0,60}" + AGENT_PATH + "|" + AGENT_PATH + r"[^\n]{0,60}" + WRITE_VERB,
     I, [], "documentation tells the agent to change agent configuration"),
    ("standing-order", "persistence_config", "medium", {"doc"},
     r"\b(?:before|after)\s+(?:every|each|any)\s+(?:response|reply|message|turn|prompt|tool call)\b|"
     r"\bon every (?:message|turn|prompt)\b|\bat the start of every (?:session|conversation)\b|\bfor all future (?:sessions|conversations)\b",
     I, [], "instruction that applies to every turn, not to this skill's job"),
    # ---- destructive and privileged
    ("destructive", "destructive_privileged", "medium", ALL_KINDS,
     r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s|\bRemove-Item\b[^\n]*-Recurse|\bmkfs\b|\bdd\s+if=|\bgit\s+push\s+(?:-f|--force)|"
     r"\bgit\s+reset\s+--hard|\bDROP\s+(?:TABLE|DATABASE)\b|\bformat\s+[a-zA-Z]:|\bdel\s+/[sfq]", I,
     [(r"\brm\s+-[a-zA-Z]*\s+(?:/|~|\$HOME|\*)(?:\s|$)", "high")], "destructive command"),
    ("privileged", "destructive_privileged", "medium", ALL_KINDS,
     r"(?:^|[\s;&|`(])sudo\s|\bchmod\s+(?:-R\s+)?(?:7[0-7]{2}|[ugoa]*\+s)\b|\bsetuid\b|\bRunAs\b", 0, [],
     "asks for elevated privileges or loosens permissions"),
    # ---- obfuscation
    ("decode-call", "obfuscation", "medium", CODE_KINDS,
     r"\bb64decode\b|base64\.(?:b64|urlsafe_b64|b32|b16|a85|b85)decode|\batob\s*\(|Buffer\.from\([^)]*['\"]base64['\"]|"
     r"String\.fromCharCode|\bfromhex\s*\(|binascii\.(?:unhexlify|a2b_\w+)|\b(?:zlib|gzip|bz2|lzma)\.decompress|"
     r"codecs\.decode|\brot_?13\b|FromBase64String|certutil\s+-decode|base64\s+(?:-d|--decode)|\bunhexlify\b|"
     r"\bchr\s*\(\s*\d+\s*\)\s*\+\s*chr", 0, [], "decodes or decompresses a hidden string"),
    ("hex-escapes", "obfuscation", "medium", ALL_KINDS,
     r"(?:\\x[0-9a-fA-F]{2}){%d,}|(?:\\u[0-9a-fA-F]{4}){6,}|(?:\\[0-7]{3}){%d,}" % (HEX_ESCAPES_MIN, HEX_ESCAPES_MIN), 0, [],
     "long run of escaped bytes"),
    ("long-hex", "obfuscation", "medium", ALL_KINDS,
     r"\b[0-9a-fA-F]{%d,}\b" % LONG_HEX_MIN, 0, [], "very long hexadecimal string"),
    # ---- prompt injection (apply to every text file, code comments and strings included)
    ("inj-override", "prompt_injection", "high", ALL_KINDS,
     r"\b(?:ignore|disregard|forget|override|bypass|discard)\b[^.\n]{0,40}\b(?:previous|prior|above|earlier|preceding|system|safety|all)\b"
     r"[^.\n]{0,30}\b(?:instructions?|rules?|guidelines?|prompts?|safeguards?|restrictions?|constraints?|polic(?:y|ies))\b",
     I, [], "tells the model to drop its earlier instructions or safeguards"),
    ("inj-conceal", "prompt_injection", "high", ALL_KINDS,
     r"\b(?:do not|don'?t|never|without)\b[^.\n]{0,30}\b(?:tell|inform|mention|notify|alert|warn|disclose|reveal)\b[^.\n]{0,25}"
     r"\b(?:the |this )?(?:user|human|operator|person|owner)\b|"
     r"\b(?:hide|conceal|keep)\b[^.\n]{0,20}\b(?:this|these|it)\b[^.\n]{0,20}\b(?:from|secret|hidden)\b",
     I, [], "tells the model to hide something from the user"),
    ("inj-covert", "prompt_injection", "medium", ALL_KINDS,
     r"\bsilently\s+(?:run|execute|send|upload|install|download|post|copy|read|write|delete|disable)\b", I, [],
     "tells the model to act silently"),
    ("inj-exfil", "prompt_injection", "high", ALL_KINDS,
     r"\b(?:send|post|upload|forward|email|e-?mail|exfiltrate|transmit|leak|copy)\b[^.\n]{0,60}"
     r"\b(?:api[ _-]?keys?|tokens?|credentials?|passwords?|secrets?|ssh keys?|private keys?|\.env|environment variables|"
     r"chat history|conversation|source code|cookies)\b[^.\n]{0,80}\b(?:to|at|via)\b[^.\n]{0,40}"
     r"(?:https?://|[\w.-]+@[\w.-]+\.\w+|\bwebhook\b)", I, [], "tells the model to send secrets or private data somewhere"),
    ("inj-send-url", "prompt_injection", "medium", ALL_KINDS,
     r"\b(?:send|post|upload|forward|transmit)\b[^.\n]{0,50}\b(?:to|at)\b\s+https?://", I, [],
     "tells the model to send something to a URL"),
    ("inj-remote-follow", "prompt_injection", "high", ALL_KINDS,
     r"\b(?:fetch|download|load|read|open|retrieve|visit|pull)\b[^.\n]{0,60}https?://\S+[^\n]{0,80}\b(?:and|then)\b[^.\n]{0,25}"
     r"\b(?:follow|execute|run|obey|apply)\b|"
     r"\b(?:follow|obey|execute)\b[^.\n]{0,30}\b(?:instructions?|commands?)\b[^.\n]{0,30}\b(?:from|at|in)\b[^.\n]{0,20}"
     r"(?:https?://|that (?:page|url|site|file)|the (?:response|result))", I, [],
     "tells the model to fetch remote text and obey it"),
    ("inj-role", "prompt_injection", "medium", ALL_KINDS,
     r"\byou are now\b|\bnew (?:system )?instructions?\s*:|\bfrom now on,? (?:you|always|ignore)\b|"
     r"\b(?:developer|god|admin|root) mode\b|\bjailbreak\b|\bpretend (?:that )?(?:you|to be)\b|"
     r"\bact as (?:if )?(?:you (?:have|are) no|an? unrestricted)", I, [], "tries to reassign the model's role"),
    ("inj-approval", "prompt_injection", "medium", ALL_KINDS,
     r"\b(?:without|skip|bypass|never|don'?t)\b[^.\n]{0,25}\b(?:confirmation|approval|permission|review|asking|confirming)\b|"
     r"\bauto-?approv\w*\b|--dangerously-\w+|\bbypassPermissions\b|--yolo\b|--no-verify\b|"
     r"\bdisable\b[^.\n]{0,25}\b(?:safety|sandbox|guardrails?|permission checks?|prompts?)\b", I, [],
     "asks to skip a confirmation or turn off a safeguard"),
    ("inj-marker", "prompt_injection", "medium", ALL_KINDS,
     r"</?(?:system|assistant|instructions?|tool_call|tool_use|admin)>|\[/?INST\]|<\|(?:im_start|im_end|system)\|>", I, [],
     "fake chat-role or tool markup"),
    ("inj-priority", "prompt_injection", "medium", ALL_KINDS,
     r"\b(?:highest|top|overriding)\s+priority\b[^.\n]{0,40}\b(?:instruction|rule|directive)s?\b|"
     r"\bthese instructions? (?:take|have) (?:precedence|priority)\b", I, [],
     "claims to outrank the user's and the system's instructions"),
]

COMPILED = []
for _rid, _cap, _sev, _kinds, _pat, _flags, _boosts, _desc in RULES:
    COMPILED.append((_rid, _cap, _sev, _kinds, re.compile(_pat, _flags),
                     [(re.compile(b, re.I), s) for b, s in _boosts], _desc))

URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)(?::\d+)?", re.I)
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)
COMMENT_DIRECTIVE = re.compile(
    r"\b(?:ignore|you must|you should|always|never|do not|don'?t|run|execute|send|upload|assistant|agent|model|claude|"
    r"system|instruction|secret|password|token|api key)\b", re.I)
BASE64ISH = re.compile(r"[A-Za-z0-9+/]{%d,}={0,2}" % BLOB_MEDIUM)
INSTALL_HOOK = re.compile(r'"(?:preinstall|install|postinstall|prepare|prepublish)"\s*:')
FENCE = re.compile(r"^\s*(?:```|~~~)")


def printable(text):
    """Make hidden characters visible as <U+XXXX> so evidence never carries them."""
    return ANY_INVISIBLE.sub(lambda m: "<U+%04X>" % ord(m.group(0)), text)


def window(line, start):
    line = printable(line.strip("\r\n"))
    stripped = line.strip()
    if len(stripped) <= EVIDENCE_CHARS:
        return stripped
    begin = max(0, min(start, len(line)) - 40)
    return ("..." if begin else "") + line[begin:begin + EVIDENCE_CHARS].strip() + "..."


def kind_of(path, text_head):
    ext = os.path.splitext(path)[1].lower()
    if ext in CODE_EXT:
        return CODE_EXT[ext]
    if not ext and text_head.startswith("#!"):
        first = text_head.split("\n", 1)[0].lower()
        if "python" in first:
            return "py"
        if "node" in first:
            return "js"
        return "shell"
    return "doc"


def real_blob(token):
    """A base64-like run counts only if it mixes cases and digits or symbols (not a path or word run)."""
    return bool(re.search(r"[A-Z]", token) and re.search(r"[a-z]", token) and re.search(r"[0-9+/]", token))


class Audit:
    def __init__(self, root):
        self.root = root
        self.raw = []                # findings before capping
        self.hosts = set()
        self.files_scanned = 0
        self.bytes_scanned = 0
        self.name = None
        self.fm = {"present": False, "bytes": 0, "keys": [], "description_chars": 0, "declared_network": None}
        self.per_file_rules = {}     # file -> rule_id -> (line, evidence)
        self.md_text = ""

    def add(self, rel, line, capability, severity, rule, context, evidence):
        self.raw.append({"file": rel, "line": line, "capability": capability, "severity": severity,
                         "rule": rule, "context": context, "evidence": evidence})
        self.per_file_rules.setdefault(rel, {}).setdefault(rule, (line, evidence))

    # ---------------------------------------------------------------- frontmatter
    def frontmatter(self, rel, lines, text):
        if not lines or lines[0].strip() != "---":
            self.add(rel, 1, "frontmatter", "medium", "fm-missing", "frontmatter", "SKILL.md does not start with a frontmatter block")
            return 0
        end = None
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end = i
                break
        if end is None:
            self.add(rel, 1, "frontmatter", "medium", "fm-unclosed", "frontmatter", "frontmatter block is never closed")
            return 0
        block = lines[1:end]
        fm_text = "\n".join(block)
        size = len(fm_text.encode("utf-8"))
        keys = []
        for ln in block:
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:", ln)
            if m:
                keys.append(m.group(1))
        desc = ""
        for idx, ln in enumerate(block):
            m = re.match(r"^description\s*:\s*(.*)$", ln)
            if m:
                value = m.group(1).strip()
                if value in (">", "|", ">-", "|-"):
                    extra = []
                    for nxt in block[idx + 1:]:
                        if nxt.startswith((" ", "\t")):
                            extra.append(nxt.strip())
                        else:
                            break
                    value = " ".join(extra)
                desc = value
                break
        declared = None
        for ln in block:
            m = re.match(r"^\s+network\s*:\s*(.+)$", ln)
            if m:
                declared = m.group(1).strip().strip("'\"")
        nm = re.search(r"^name\s*:\s*(\S.*)$", fm_text, re.M)
        if nm:
            self.name = nm.group(1).strip().strip("'\"")
        self.fm = {"present": True, "bytes": size, "keys": keys, "description_chars": len(desc), "declared_network": declared}
        if size > FM_BYTES_HIGH:
            self.add(rel, 1, "frontmatter", "high", "fm-oversized", "frontmatter", "frontmatter is %d bytes (limit for high: %d)" % (size, FM_BYTES_HIGH))
        elif size > FM_BYTES_MEDIUM:
            self.add(rel, 1, "frontmatter", "medium", "fm-oversized", "frontmatter", "frontmatter is %d bytes (limit for medium: %d)" % (size, FM_BYTES_MEDIUM))
        if len(desc) > DESC_MAX:
            self.add(rel, 1, "frontmatter", "medium", "fm-description-long", "frontmatter", "description is %d characters (open-spec limit %d)" % (len(desc), DESC_MAX))
        for ln_no, ln in enumerate(block, start=2):
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*)$", ln)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            if key == "hooks":
                self.add(rel, ln_no, "frontmatter", "high", "fm-hooks", "frontmatter", "frontmatter declares hooks (commands run automatically)")
            elif key not in SPEC_KEYS:
                self.add(rel, ln_no, "frontmatter", "low", "fm-extra-key", "frontmatter", "key '%s' is outside the open frontmatter spec" % key)
            if key == "allowed-tools":
                broad = re.search(r"(?:^|[\s,\[])\*(?:$|[\s,\]])|\bBash\b(?!\()|Bash\(\s*\*|\bBash\(.*:\*\)", val)
                self.add(rel, ln_no, "frontmatter", "medium" if broad else "low", "fm-allowed-tools", "frontmatter",
                         "allowed-tools pre-approves: %s" % printable(val.strip())[:100])
        return end + 1  # index of first body line (0-based)

    # ---------------------------------------------------------------- text scanning
    def scan_text(self, rel, text, kind, fm_end):
        lines = text.split("\n")
        # per-line rules
        in_fence = False
        for idx, raw in enumerate(lines):
            line = raw.rstrip("\r")
            line_no = idx + 1
            if kind == "doc" and FENCE.match(line):
                in_fence = not in_fence
            if kind == "doc":
                context = "frontmatter" if (rel == "SKILL.md" and idx < fm_end) else ("fenced-block" if in_fence else "body")
            else:
                context = "code"
            if len(line) > MINIFIED_LINE and kind in CODE_KINDS:
                self.add(rel, line_no, "obfuscation", "medium", "minified-line", context,
                         "line is %d characters long (limit %d)" % (len(line), MINIFIED_LINE))
            for rid, cap, sev, kinds, rx, boosts, _desc in COMPILED:
                if kind not in kinds:
                    continue
                if rid == "shell-script":
                    if idx == 0:
                        self.add(rel, 1, cap, sev, rid, "file", "%s is a shell or batch script" % rel)
                    continue
                m = rx.search(line)
                if not m:
                    continue
                severity = sev
                for brx, bsev in boosts:
                    if brx.search(line):
                        severity = bsev
                if rel == "SKILL.md" and context == "frontmatter" and cap == "prompt_injection":
                    severity = "high"   # frontmatter is loaded into every session, so injection there is never benign
                self.add(rel, line_no, cap, severity, rid, context, window(line, m.start()))
            for hm in URL_RE.finditer(line):
                self.hosts.add(hm.group(1).lower().rstrip("."))
            # base64-like blobs
            for bm in BASE64ISH.finditer(line):
                token = bm.group(0)
                if "://" in line[max(0, bm.start() - 3):bm.start()]:
                    continue
                if real_blob(token) and not re.fullmatch(r"[A-Za-z]+(?:/[A-Za-z]+)+", token):
                    severity = "high" if len(token) >= BLOB_HIGH else "medium"
                    self.add(rel, line_no, "obfuscation", severity, "base64-blob", context,
                             "%s... (%d base64-like characters)" % (token[:24], len(token)))
            # hidden characters
            self.hidden_chars(rel, line_no, line, idx == 0, context)
        # HTML comments (whole-text, can span lines)
        if kind == "doc":
            for cm in HTML_COMMENT.finditer(text):
                body = cm.group(1)
                line_no = text.count("\n", 0, cm.start()) + 1
                sev, why = "low", "HTML comment (invisible when rendered)"
                if len(body.strip()) > 200:
                    sev, why = "medium", "long HTML comment (%d characters, invisible when rendered)" % len(body.strip())
                if COMMENT_DIRECTIVE.search(body):
                    sev, why = "medium", "HTML comment that reads like an instruction (invisible when rendered)"
                for rid, cap, rsev, kinds, rx, _b, _d in COMPILED:
                    if cap == "prompt_injection" and rsev == "high" and rx.search(body):
                        sev, why = "high", "HTML comment containing %s wording (invisible when rendered)" % rid
                        break
                snippet = printable(" ".join(body.split()))[:EVIDENCE_CHARS]
                self.add(rel, line_no, "prompt_injection", sev, "html-comment", "comment", "%s: %s" % (why, snippet))

    def hidden_chars(self, rel, line_no, line, first_line, context):
        if not ANY_INVISIBLE.search(line):
            return
        scan = line[1:] if (first_line and line.startswith(chr(0xFEFF))) else line
        tags = TAG_CHARS.findall(scan)
        if tags:
            decoded = "".join(chr(ord(c) - 0xE0000) if 0x20 <= ord(c) - 0xE0000 < 0x7F else "?" for c in tags)
            self.add(rel, line_no, "prompt_injection", "high", "hidden-tag-chars", context,
                     "%d Unicode tag characters spelling: %s" % (len(tags), printable(decoded)[:100]))
        bidi = BIDI_CHARS.findall(scan)
        if bidi:
            self.add(rel, line_no, "prompt_injection", "high", "hidden-bidi", context,
                     "%d bidirectional control characters (can reorder visible text)" % len(bidi))
        zw = ZERO_WIDTH.findall(scan)
        if zw:
            codes = sorted({"U+%04X" % ord(c) for c in zw})
            self.add(rel, line_no, "prompt_injection", "medium", "hidden-zero-width", context,
                     "%d zero-width or invisible characters (%s)" % (len(zw), ", ".join(codes)))

    # ---------------------------------------------------------------- file level
    def combos(self):
        for rel, rules in self.per_file_rules.items():
            def first(*ids):
                for rid in ids:
                    if rid in rules:
                        return rules[rid]
                return None
            decode = first("decode-call", "base64-blob", "hex-escapes")
            run = first("dyn-exec", "subprocess")
            if decode and run:
                self.add(rel, run[0], "obfuscation", "high", "decode-then-run", "code",
                         "decodes a hidden string (line %d) and runs code (line %d): %s" % (decode[0], run[0], run[1]))
            secret = first("env-dump", "env-secret-name", "cred-path-code")
            net = first("net-import", "net-call", "net-shell")
            if secret and net:
                self.add(rel, net[0], "env_credentials", "high", "secret-plus-network", "code",
                         "reads secrets (line %d) and uses the network (line %d): %s" % (secret[0], net[0], net[1]))

    def package_checks(self, files_info, skill_text):
        total = sum(size for _r, size in files_info)
        if total > BIG_PACKAGE_BYTES:
            self.add("(package)", 0, "package", "medium", "package-size", "file", "package is %d bytes (house limit %d)" % (total, BIG_PACKAGE_BYTES))
        if len(files_info) > MANY_FILES:
            self.add("(package)", 0, "package", "low", "many-files", "file", "%d files (more than %d)" % (len(files_info), MANY_FILES))
        for rel, kind in self.code_files:
            base = os.path.basename(rel)
            if base not in self.md_text:
                self.add(rel, 0, "package", "medium", "unreferenced-script", "file",
                         "%s is code that no Markdown file in the package mentions" % rel)


def audit(root):
    a = Audit(root)
    a.code_files = []
    files_info = []
    skill_path = os.path.join(root, "SKILL.md")
    md_chunks = []
    entries = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        keep = []
        for d in sorted(dirnames):
            full = os.path.join(dirpath, d)
            rel = (d if rel_dir == "." else rel_dir + "/" + d)
            if os.path.islink(full):
                target = os.path.realpath(full)
                outside = not (target + os.sep).startswith(os.path.realpath(root) + os.sep)
                a.add(rel, 0, "package", "high" if outside else "low", "symlink", "file",
                      "directory symlink %s" % ("pointing outside the folder" if outside else "inside the folder"))
                continue
            if d == ".git":
                a.add(rel, 0, "package", "medium", "git-dir-unscanned", "file", ".git directory present and not scanned (hooks and history can hold code)")
                continue
            if d in ("__pycache__", "node_modules"):
                a.add(rel, 0, "package", "medium", "vendored-dir-unscanned", "file", "%s directory present and not scanned" % d)
                continue
            keep.append(d)
        dirnames[:] = keep
        for f in sorted(filenames):
            entries.append((os.path.join(dirpath, f), (f if rel_dir == "." else rel_dir + "/" + f)))
    for full, rel in entries:
        if os.path.islink(full):
            target = os.path.realpath(full)
            outside = not (target + os.sep).startswith(os.path.realpath(root) + os.sep)
            a.add(rel, 0, "package", "high" if outside else "low", "symlink", "file",
                  "symlink %s" % ("pointing outside the folder" if outside else "inside the folder"))
            continue
        try:
            size = os.path.getsize(full)
            with open(full, "rb") as fh:
                data = fh.read(MAX_READ_BYTES)
        except OSError as exc:
            a.add(rel, 0, "package", "medium", "unreadable", "file", "cannot read file: %s" % exc.__class__.__name__)
            continue
        files_info.append((rel, size))
        ext = os.path.splitext(rel)[1].lower()
        base = os.path.basename(rel)
        if base.startswith(".") and base not in (".gitignore", ".gitattributes", ".editorconfig"):
            a.add(rel, 0, "package", "low", "hidden-file", "file", "hidden file %s" % base)
        if size > BIG_FILE_BYTES:
            a.add(rel, 0, "package", "medium", "big-file", "file", "%d bytes (house limit per file %d)" % (size, BIG_FILE_BYTES))
        if size > MAX_READ_BYTES:
            a.add(rel, 0, "package", "medium", "truncated-read", "file", "only the first %d bytes were scanned" % MAX_READ_BYTES)
        if ext in EXECUTABLE_EXT:
            a.add(rel, 0, "package", "high", "executable-file", "file", "compiled or executable file type %s" % ext)
            continue
        if ext in ARCHIVE_EXT:
            a.add(rel, 0, "package", "medium", "archive-file", "file", "archive %s (contents not scanned)" % ext)
            continue
        if ext in IMAGE_EXT:
            a.add(rel, 0, "package", "info", "image-file", "file", "image %s (pixel data not scanned)" % ext)
            continue
        if b"\x00" in data[:8192]:
            a.add(rel, 0, "package", "medium", "binary-file", "file", "binary content, not scanned")
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            a.add(rel, 0, "package", "medium", "invalid-utf8", "file", "not valid UTF-8; scanned with replacement characters")
            text = data.decode("utf-8", errors="replace")
        a.files_scanned += 1
        a.bytes_scanned += len(data)
        kind = kind_of(rel, text[:200])
        if kind in CODE_KINDS:
            a.code_files.append((rel, kind))
        if kind == "doc" and ext in (".md", ".markdown", ".txt", ".rst"):
            md_chunks.append(text)
        if base == "package.json" and INSTALL_HOOK.search(text):
            a.add(rel, 0, "package", "high", "install-hook", "file", "package.json defines an install-time lifecycle script")
        if base in ("setup.py",):
            a.add(rel, 0, "package", "medium", "install-time-code", "file", "setup.py runs code when installed as a package")
        if ext == ".pth":
            a.add(rel, 0, "package", "high", "pth-file", "file", ".pth files can run code at every Python start")
        if base in ("Makefile", "Dockerfile") or rel.startswith(".github/"):
            a.add(rel, 0, "package", "low", "build-file", "file", "build or CI definition (runs commands when used)")
        fm_end = 0
        lines = text.split("\n")
        if rel == "SKILL.md":
            fm_end = a.frontmatter(rel, lines, text)
        a.scan_text(rel, text, kind, fm_end)
    a.md_text = "\n".join(md_chunks)
    a.combos()
    # declared network none, but code uses the network
    if a.fm["declared_network"] and a.fm["declared_network"].lower() in ("none", "no", "false", "0"):
        for rel, rules in a.per_file_rules.items():
            for rid in ("net-import", "net-call", "net-shell"):
                if rid in rules:
                    a.add(rel, rules[rid][0], "frontmatter", "high", "declared-network-mismatch", "code",
                          "frontmatter says network: none but code does: %s" % rules[rid][1])
                    break
    a.package_checks(files_info, a.md_text)
    return a


def build_report(a, root):
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    raw = sorted(a.raw, key=lambda f: (order[f["severity"]], f["file"], f["line"], f["rule"]))
    counts_all = {"high": 0, "medium": 0, "low": 0, "info": 0}
    seen = {}
    listed = []
    suppressed = 0
    for f in raw:
        counts_all[f["severity"]] += 1
        key = (f["file"], f["rule"])
        seen[key] = seen.get(key, 0) + 1
        if seen[key] > MAX_PER_RULE_PER_FILE:
            suppressed += 1
            continue
        listed.append(f)
    for i, f in enumerate(listed, start=1):
        f["id"] = "F%03d" % i
    table = []
    for cap in CAPABILITIES:
        mine = [f for f in raw if f["capability"] == cap]
        level = "none"
        if mine:
            level = LEVEL_NAMES[max(SEVERITY_RANK[f["severity"]] for f in mine)]
        ev = ["%s:%d: %s" % (f["file"], f["line"], f["evidence"]) if f["line"] else "%s: %s" % (f["file"], f["evidence"])
              for f in mine[:3]]
        table.append({"capability": cap, "level": level, "findings": len(mine), "evidence": ev})
    if counts_all["high"]:
        verdict = "high-risk"
    elif counts_all["medium"]:
        verdict = "needs-review"
    else:
        verdict = "low-risk"
    findings = [{"id": f["id"], "file": f["file"], "line": f["line"], "capability": f["capability"],
                 "severity": f["severity"], "rule": f["rule"], "context": f["context"], "evidence": f["evidence"]}
                for f in listed]
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "scan",
        "skill": os.path.basename(os.path.abspath(root)),
        "name": a.name,
        "summary": {"verdict": verdict, "counts": counts_all, "files_scanned": a.files_scanned,
                    "bytes_scanned": a.bytes_scanned, "hosts": sorted(a.hosts), "suppressed_findings": suppressed},
        "frontmatter": a.fm,
        "risk_table": table,
        "findings": findings,
        "limitations": [
            "Text patterns only: nothing was executed, imported or resolved.",
            "Does not see code fetched at run time, prose that persuades without trigger words, or non-English injection.",
            "Binary files, archives, images and skipped directories are listed but their contents are not read.",
            "A clean result is not a safety guarantee; a finding is not proof of intent.",
        ],
    }


def main(argv):
    if len(argv) != 2 or argv[0] != "scan":
        sys.stderr.write("usage: skill_audit.py scan <skill-folder>\n")
        return 2
    root = argv[1]
    if not os.path.isdir(root):
        sys.stderr.write("not a folder: %s\n" % root)
        return 2
    if not os.path.isfile(os.path.join(root, "SKILL.md")):
        sys.stderr.write("no SKILL.md in %s; point the scan at the skill folder itself\n" % root)
        return 2
    report = build_report(audit(root), root)
    sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return {"low-risk": 0, "needs-review": 1, "high-risk": 3}[report["summary"]["verdict"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
