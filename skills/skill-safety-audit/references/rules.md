## Contents

- Rule list by capability
- Files and frontmatter checks
- Combined rules
- Typical false positives
- Sources

# Rule reference for skill_audit.py

Severity in the table is the base severity; some rules rise on the same line (noted). A finding inside the frontmatter of SKILL.md that belongs to prompt_injection is always high, because frontmatter is loaded into every session.

## Rule list by capability

| Rule id | Base | Matches (plain words) |
|---|---|---|
| net-import | medium | import of a network library (sockets, HTTP clients, mail, FTP, SSH) in code; the URL-parsing helper alone does not count |
| net-call | medium | a request call such as urlopen, fetch, XMLHttpRequest, axios, a WebSocket, a Node http module, or a PowerShell web cmdlet |
| net-shell | medium | a shell script line starting a network tool (curl, wget, nc, scp, ssh, ftp and similar) |
| net-doc-command | medium | Markdown or text tells the agent to run a download tool |
| net-remote-image | medium | Markdown image whose URL has a query string (query strings can carry data out) |
| net-remote-embed | high | a script tag in a document |
| net-embed-frame | medium | frame, object, embed or a javascript: URL in a document |
| fetch-exec | high | a download piped into a shell or interpreter, or a PowerShell expression evaluator fed from the web |
| install-cmd | medium | a package manager or git clone command; drops to low when the version is pinned |
| subprocess | medium | subprocess module, os.system and relatives, child_process, process spawners; high with shell=True or os.system |
| shell-script | low | any shell or batch file (one finding per file) |
| dyn-exec | high | eval, exec, dynamic import, pickle or marshal loading, new Function, shell eval or source from a process substitution |
| split-string-dispatch | medium | a module or attribute name is built by joining string pieces (`__import__("o" + "s")`, `getattr(m, "sys" + "tem")`), a way to hide a call from text matching. Only the common shapes are caught; other splitting can still pass |
| env-read | medium | os.environ, getenv, process.env, a PowerShell env drive |
| env-secret-name | high | a quoted or dollar-prefixed name containing KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL, AWS_, GITHUB_, OPENAI or ANTHROPIC |
| env-dump | high | the whole environment copied, listed or serialised |
| literal-credential | high | any file (code, docs, frontmatter) contains a real-looking secret value: an AWS key id (`AKIA` plus 16 characters), a private-key block header, an `sk-` token of 20+ characters, a `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` GitHub token of 36+ characters, an `xox` Slack token, or `password=`/`passwd=`/`pwd=` followed by a literal value (placeholders starting with `<`, `$`, `{` or a quote are skipped). File contents are matched, never file names. A pasted key is itself an incident: report it, never repeat the full value |
| cred-path-code | high | a script mentions ssh keys, cloud credential folders, token files such as .npmrc or .netrc, browser profile stores, wallet files, or a .env file |
| cred-path-doc | medium | the same paths in documentation (the skill tells the agent to go there) |
| file-write | low | write, delete, move or chmod calls; rises to medium when the same line names the home folder, a temp folder or a parent folder, and to high for system folders or the registry |
| shell-redirect | low | shell redirect to a file (same rise rules) |
| persistence | high | shell start-up files, cron, systemd, launchd, authorized_keys, git hooks, scheduled tasks, run keys, Python site customisation |
| agent-config-code | medium | a script names an agent's settings, hooks, commands, MCP or rules paths; high if the line also writes |
| agent-config-doc | medium | documentation tells the agent to add, edit or replace those files |
| standing-order | medium | an instruction that applies to every turn, response or session instead of to the skill's job |
| destructive | medium | recursive delete, disk format, force push, hard reset, table drop; high when the target is root, home or a wildcard |
| privileged | medium | sudo, setuid or setgid chmod, RunAs |
| decode-call | medium | base64, hex, rot13 or compression decoding, String.fromCharCode, atob |
| base64-blob | medium or high | a base64-like run of 80+ characters (high at 200+) that mixes upper case, lower case and digits or symbols |
| hex-escapes | medium | 8 or more consecutive hex, octal or 6 or more unicode escapes |
| long-hex | medium | a hexadecimal run of 128 or more digits |
| minified-line | medium | a code line over 1,000 characters |
| inj-override | high | an override verb (ignore, disregard, forget, bypass, discard) near a target word (previous, prior, above, system, safety, all) near an instruction noun (instructions, rules, guidelines, safeguards) |
| inj-conceal | high | a negation near a disclosure verb near the user, or hide/keep near "this" near "from/secret/hidden" |
| inj-covert | medium | "silently" followed by an action verb |
| inj-exfil | high | a send verb, a secret or private-data noun, and a destination (URL, address, webhook) in one sentence |
| inj-send-url | medium | a send verb followed by "to" and a URL |
| inj-remote-follow | high | fetch or read a URL and then follow or run what it says |
| inj-role | medium | role reassignment (a "you are" plus "now" statement, "from now on" rules, developer or admin mode, jailbreak) |
| inj-approval | medium | skip or bypass confirmation, auto-approve, flags that disable permission checks, no-verify |
| inj-marker | medium | fake system, assistant, tool or chat-template markup |
| inj-priority | medium | claims its instructions outrank others |
| html-comment | low, medium or high | every HTML comment in a text file: low if short and plain, medium if over 200 characters or worded like an instruction, high if it contains an override, concealment, exfiltration or remote-follow pattern |
| hidden-tag-chars | high | Unicode tag characters (invisible; the scan decodes and prints the hidden ASCII) |
| hidden-bidi | high | bidirectional control characters |
| hidden-zero-width | medium | zero-width and other invisible characters (a byte order mark at the very start of a file is ignored) |

## Files and frontmatter checks

| Rule id | Severity | Condition |
|---|---|---|
| fm-missing, fm-unclosed | medium | no frontmatter block, or one that never closes |
| fm-oversized | medium or high | frontmatter over 2,048 bytes (medium) or 8,192 bytes (high) |
| fm-description-long | medium | description over 1,024 characters |
| fm-hooks | high | frontmatter declares hooks (commands that run automatically) |
| fm-extra-key | low | a top-level key outside the open spec |
| fm-allowed-tools | low or medium | pre-approved tools; medium when a shell or a wildcard is pre-approved |
| declared-network-mismatch | high | metadata says network none but code uses the network |
| executable-file | high | compiled or packed file types (exe, dll, so, dylib, jar, class, pyc, whl, wasm and similar) |
| archive-file, binary-file | medium | archive or file with null bytes; contents are not read |
| image-file | info | image; pixel data is not read |
| invalid-utf8 | medium | text file that is not valid UTF-8 |
| install-hook | high | package.json with an install-time lifecycle script |
| install-time-code, pth-file | medium, high | setup.py; a .pth file |
| symlink | low or high | link inside the folder (low) or pointing outside it (high); never followed |
| git-dir-unscanned, vendored-dir-unscanned | medium | .git, node_modules or __pycache__ present and not read |
| unreferenced-script | medium | code file whose name no Markdown file in the package mentions |
| big-file, package-size, many-files, hidden-file, build-file, truncated-read, unreadable | low or medium | size over 200 KB per file or 1 MB per package, over 200 files, dot files, build or CI definitions, files over 2 MB (first 2 MB read), unreadable files |

## Combined rules

- `decode-then-run` (high): the same file decodes a hidden string and also runs code or starts a process.
- `secret-plus-network` (high): the same file reads a secret (env-dump, env-secret-name or cred-path-code) and uses the network. Typical honest case: an API client that reads one key for one host. Clear it only when the key and host belong together and SKILL.md tells the user to provide the key.

## Typical false positives

- Security, DevOps and instruction-file skills quote attack strings and mention credential paths on purpose. The finding's `context` shows `fenced-block`; read the sentence to confirm it is quoted.
- `install-cmd` on a pinned install is low; on an unpinned one it means the skill fetches whatever version is newest on the day it is used.
- `env-read` on a locale or home-folder variable is harmless alone; it matters with a network row.
- `file-write` inside the skill folder (a cache file) is normal; look at the evidence line for the target path.
- `subprocess` with a fixed argument list, calling a tool the skill documents, is a reviewed-and-explained case; with `shell=True` and any variable in the string it is not.
- A long base64-like string can be a fixture or a hash; open it and check what decodes (without running anything).

## Sources

Facts below are stated in the editor's own words and were not re-fetched for this version.

- Open skill format and frontmatter keys: https://agentskills.io/specification
- Prompt injection is the top-ranked risk for applications built on language models: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Bidirectional control characters can make source code display differently from how it is read by a compiler ("Trojan Source"): https://trojansource.codes/
- The Unicode tag block (U+E0000 to U+E007F) is invisible in most renderers and has been used to hide ASCII text from human readers while models still read it: https://www.unicode.org/charts/PDF/UE0000.pdf
- Loading pickled data can run arbitrary code, so it must never be used on untrusted files: https://docs.python.org/3/library/pickle.html
