---
name: curl-to-python-requests
description: Converts a copied `curl` command into an equivalent Python requests snippet by splitting it with shlex, without running it or sending any request. Use when a user pastes a `curl` command from API docs or browser devtools and asks for the Python requests equivalent, or asks what a `curl` call does in Python. Do not use for executing the `curl` command, testing an endpoint, or translating code in other languages.
license: Apache-2.0
compatibility: Python 3.9+ stdlib only, no network (type A).
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-haiku-5-5
  version: "0.1.0"
  network: none
---

# `curl` to Python requests

Converts one `curl` command, saved in a text file, into a `requests` snippet. The script splits the command with shlex and never runs it. It sends no request. Credentials are printed as placeholders.

## Workflow

1. **Get the input.** Save the `curl` command in a UTF-8 text file under 2 MB, written in POSIX shell quoting (bash or zsh). Output: the file path, written as `<input-file>`. Stop if the command was copied in Windows cmd form (caret `^` line joins) or PowerShell form. See Refuse / stop when.
2. **Run the script.** Output: the exit code, and the snippet on stdout when the exit code is 0 or 1. On exit 2, go to the error contract.
3. **Read the findings.** Each `# FINDING` line in the snippet maps to one row of the findings table. Output: one row per finding, with its code and detail.
4. **Check the masking.** Read the `# Masked values:` line. Each name listed must appear in the snippet as `"<REDACTED>"`, `"<USER>"` or `"<PASSWORD>"`. Output: "masking confirmed", or the name that failed. If a name failed, do not deliver the snippet; stop and report the failure.
5. **Deliver.** Return the output contract below. Status is `complete` on exit 0 and `partial` on exit 1.

## Translation rules

| `curl` input | Snippet result | Rule |
|---|---|---|
| `-X METHOD` | `requests.<method>(`, lowercase | Explicit method wins. Unknown methods use `requests.request(` |
| `-I` or `--head` | `requests.head(` | Applies when no `-X` is given |
| body present, no `-X`, no `-I`, no `-G` | `requests.post(` | `curl`'s default when a body exists |
| `-G` with `-d` | GET; data pairs move to `params` | Body is dropped |
| `--json`, or `-d` with a Content-Type containing `json` | `json=json_body` | JSON is parsed; invalid JSON gives `data_body = "<REQUEST_BODY>"` |
| `-d`, `--data-raw`, `--data-binary` (other body) | `data=data_body` | Values joined with `&`; keys named in the sensitive list are masked |
| `-F name=value` | `files=[("name", (None, "value"))]` | Text fields only |
| `-L` present | `allow_redirects=True` | |
| `-L` absent | `allow_redirects=False` | `curl` does not follow redirects; requests follows them by default |
| `-k` or `--insecure` | `verify=False` | Otherwise the argument is omitted |
| `-u user:pass` | `auth=("<USER>", "<PASSWORD>")` | Username and password both masked |
| URL query string | `params` dict | Duplicate keys become a list of tuples |
| Sensitive key names | value becomes `"<REDACTED>"` | Keys: password, passwd, pwd, secret, token, api_key, apikey, access_token, client_secret (case-insensitive; hyphens count as underscores) |
| Sensitive header names | value becomes `"<REDACTED>"` | Authorization, Proxy-Authorization, Cookie, X-Api-Key, and any name containing token, secret, api-key or api_key |
| URL without a scheme | `http://` is added, finding `SCHEME_DEFAULTED` | Matches `curl`'s default |
| Input size | 2,097,152 bytes maximum | Working value, larger input is exit 2 |

## Findings (exit 1, snippet still printed)

| Code | Meaning | Action in the reply |
|---|---|---|
| `UNSUPPORTED_OPTION` | Flag not translated, such as `-o`, `-f`, `--cacert`, `--proxy` | Name the flag; the user writes that part by hand |
| `FILE_REFERENCE_NOT_READ` | `@file` body, `-F field=@file`, or a `-b` cookie file | The file contents are not read; the user supplies them |
| `FORM_FIELD_MALFORMED` | `-F` value without `name=value` | Ask the user to fix the field |
| `HEADER_MALFORMED` | `-H` value without a colon | The header is skipped; say so |
| `JSON_BODY_INVALID` | JSON body does not parse | Body is the placeholder `"<REQUEST_BODY>"`; the user supplies the body |
| `EXTRA_URL` | More than one URL in the command | Only the first is translated; say which one |
| `AUTH_NO_PASSWORD` | `-u` given without a password | `curl` would prompt; the user fills `<PASSWORD>` |
| `SCHEME_DEFAULTED` | URL had no scheme | Ask the user to confirm the scheme |

## Input errors (exit 2, no snippet)

| Code | Cause |
|---|---|
| `USAGE` | Argument count is not one |
| `FILE_NOT_FOUND` | Path missing or not a regular file |
| `FILE_TOO_LARGE` | Input over 2,097,152 bytes |
| `READ_ERROR` | File could not be opened or read |
| `INVALID_UTF8` | Input is not valid UTF-8 (a UTF-8 byte order mark is accepted) |
| `SHELL_PARSE_ERROR` | Unbalanced quote or trailing backslash |
| `NOT_A_CURL_COMMAND` | First word is not `curl` or `curl.exe` |
| `OPTION_MISSING_VALUE` | An option that takes a value is last on the line |
| `NO_URL` | No URL in the command |
| `URL_INVALID` | URL cannot be parsed or has no host |
| `METHOD_INVALID` | Method contains characters other than letters |

## Script contract

- Command: `python -I scripts/curl_to_py.py <input-file>`
- Argument: one positional path to the input file. The file is only read.
- stdout (exit 0 or 1): UTF-8 Python source. Order: comment lines (`# Generated by curl_to_py.py...`, `# Masked values: ...`, one `# FINDING CODE: detail` per finding), `import requests`, `url = ...`, optional `params`, `headers`, `json_body` or `data_body` or `files`, then `response = requests.<method>(...)`, then `print(response.status_code)`.
- stderr (exit 2): one JSON line, `{"error": "<message>", "code": "<CODE>"}`. Codes are listed in the input errors table.
- Exit codes: 0 no findings; 1 findings, snippet printed; 2 usage or input error.
- Shipped files: [scripts/curl_to_py.py](scripts/curl_to_py.py), [fixtures/post_json_basic_auth.txt](fixtures/post_json_basic_auth.txt), [fixtures/get_findings.txt](fixtures/get_findings.txt), [LICENSE.txt](LICENSE.txt).

## Output contract

Reply with these headings, in this order:

- `## Snippet`: the stdout of the script, in a Python code block, unchanged.
- `## Findings`: a table with columns Code | Detail | Action, one row per FINDING line. Write "None" when there are none.
- `## Masked`: the names from the `# Masked values:` line, comma separated.
- `## Status`: `complete` (exit 0) or `partial` (exit 1).
- `## Open questions`: a numbered list of values the user must supply (`<USER>`, `<PASSWORD>`, `<REQUEST_BODY>`, file contents) and of anything refused.

On exit 2, reply with `## Error` and the code and message from stderr, and nothing else.

## Refuse / stop when

- The text has no `curl` command, or the first word is not `curl`: stop, reply with `NOT_A_CURL_COMMAND`.
- Input is over 2,097,152 bytes or is not UTF-8: stop, reply with the exit 2 code.
- The command is in Windows cmd or PowerShell form (caret `^` joins, backtick continuations): stop and ask the user for the bash or zsh form. The script does not parse those forms.
- The user asks to run the command, call the URL, or check that the endpoint responds: refuse that clause only. Deliver the snippet, set status `partial`, and list the refused request under Open questions.
- The user asks to reveal masked credentials, or to read a file named by `@file`: refuse that clause only. The script never prints secret values and never reads referenced files. List the request under Open questions.
- The masking check in step 4 fails: stop and do not deliver the snippet.
