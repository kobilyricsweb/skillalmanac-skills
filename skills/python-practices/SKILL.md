---
name: python-practices
description: Holds Python 3.11+ code to a senior reviewer's standard and audits it with an ast script. Use when the user asks to write, refactor, review or modernise Python, says pythonic, best practices, add type hints, dataclass or pydantic, replace os.path or print, pyproject.toml, pytest setup, or threads vs asyncio vs processes. Covers typing, pathlib, logging, exceptions, packaging, tests and concurrency choice; the script lists anti-patterns by line. Do not use for non-Python languages, notebooks, framework internals (Django, FastAPI) or picking a library.
license: Apache-2.0
compatibility: The audit script needs Python 3.9 or newer to run, standard library only, no network. The rules target code written for Python 3.11 and newer. Without Python, apply the manual check in step 4.
metadata:
  author: Skill Almanac Editorial
  author_model: claude-sonnet-5-5
  license: Apache-2.0
  version: "0.1.0"
  network: none
---

# Python practices

Write Python the way a senior reviewer would approve it on the first pass. Each rule below has a trigger (when it applies) and a fix. If the project already has a different convention (a ruff or mypy config, an older `requires-python`), the project wins; say so in the report.

## Workflow

```
- [ ] 1 Read the target version and tooling
- [ ] 2 Write or edit with the policies below
- [ ] 3 Run the audit script on every touched file
- [ ] 4 Run the project's own checks
- [ ] 5 Report
```

1. **Read the target.** Open `pyproject.toml` (`requires-python`, `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`). No project files: assume 3.11. Below 3.11, skip the 3.11-only features marked (3.11) and say so.
2. **Write** with the policies in this file. For the dataclass versus pydantic choice, the concurrency choice, packaging or pytest layout, read [references/decision-tables.md](references/decision-tables.md), only the section you need.
3. **Audit.** Run `python scripts/py_audit.py <file-or-folder> ...`. It prints strict JSON. Fix every finding, or suppress one with `# audit: ignore <rule-id>` and a reason in the same comment when the rule does not fit (see the rule table). Re-run until `"verdict": "clean"`. Do not edit the script to make a check pass.
4. **Project checks.** Run whatever the repo defines: `pytest`, `ruff check`, `mypy` or `pyright`. Equivalent ruff codes for the script's rules: E722, B006, T201, PTH, F401. If none exist and Python is unavailable, grep the changed files for `except:`, `=[]`, `=\{\}`, `print(`, `os.path`, and read the imports by eye.
5. **Report** in this shape:

```
Target: <python version, source of that decision>
Changed: <files and the kind of change>
Audit: <verdict, counts per rule, suppressions with reasons>
Project checks: <commands run and result, or "none defined">
Decisions: <dataclass/pydantic, sync/async, any rule bent and why>
Not checked: <e.g. runtime behaviour, mypy strictness, tests not run>
```

## Typing policy

| Trigger | Do |
|---|---|
| Any public function, method or module constant | Annotate every parameter and the return type. Private helpers under 5 lines may skip return types. |
| Value can be absent | `str \| None`, not `Optional[str]`; give it no default unless `None` is meaningful. |
| Generic containers | `list[int]`, `dict[str, float]`, `collections.abc.Sequence` for read-only parameters. Never `typing.List`/`Dict`. |
| Method returns its own instance | `-> Self` (`typing.Self`, 3.11). |
| Fixed set of strings | `Literal["a", "b"]` for two to four values that are never iterated; `enum.StrEnum` (3.11) when you need to iterate, validate or attach behaviour. |
| Dict with known keys coming from JSON | `TypedDict`; if you create it and pass it around, a dataclass instead. |
| `Any` | Only at a boundary that returns untyped data (`json.loads`); narrow it on the next line. Each `Any` or `# type: ignore` needs a comment saying why. |
| Callable parameters | `Callable[[int], str]`; use a `Protocol` when it has keyword arguments or more than one method. |

Trap: `def f(items: list = [])` fails two rules at once (untyped generic, shared default). Write `def f(items: Sequence[int] | None = None)` and `items = [] if items is None else list(items)`.

## Data models

Default to `@dataclass(slots=True, kw_only=True)` for records you create, and `frozen=True` when instances are used as dict keys or shared across threads. Use pydantic only where untrusted input must be validated or coerced (HTTP bodies, config files, env vars). Full table, with the cases for `NamedTuple`, `TypedDict` and `attrs`, in [references/decision-tables.md](references/decision-tables.md) section 1.

## Paths: pathlib

Trigger: any `os.path.*`, `os.listdir`, `os.makedirs`, `os.remove`, `glob.glob`, or string concatenation with `"/"` or `"\\"`. The script flags only the `os.path` import and calls (rule `os-path`); the others are for your own review.

| Old | New |
|---|---|
| `os.path.join(a, "b")` | `Path(a) / "b"` |
| `os.path.exists(p)` / `isfile` / `isdir` | `p.exists()` / `p.is_file()` / `p.is_dir()` |
| `os.listdir(d)` | `sorted(d.iterdir())` (order is not guaranteed otherwise) |
| `os.makedirs(d, exist_ok=True)` | `d.mkdir(parents=True, exist_ok=True)` |
| `os.path.splitext(f)` | `p.suffix`, `p.stem`, `p.with_suffix(".x")` |
| `glob.glob("d/**/*.py", recursive=True)` | `d.rglob("*.py")` |
| `open(p).read()` | `p.read_text(encoding="utf-8")` |

Always pass `encoding=` when reading or writing text; the default is the platform locale (cp1252 on many Windows installs). Keep `os.path` only for `expandvars`, `expanduser` on a plain string, `relpath` where the result may need `..` (before 3.12), and `commonpath`; suppress the audit finding there with a reason. Accept `str | os.PathLike[str]` at public boundaries and convert once with `Path(x)`.

## Logging, not print

Trigger: `print(` in a module that is imported by anything else.

- Library and application modules: `log = logging.getLogger(__name__)` at module top, and `log.info("loaded %d rows from %s", n, path)`. Pass arguments, never an f-string (the message is built even when the level is off).
- Never call `logging.basicConfig()` or add handlers in a library. Configure logging once, in the entry point (`main()`).
- Inside `except`, use `log.exception("what failed")`; it records the traceback. `log.error(str(e))` loses it.
- `print` is correct in two places: a script or CLI whose output is its product (file has `if __name__ == "__main__"` or is `__main__.py`), and tests that use `capsys`. Diagnostics go to logging even in scripts; results go to stdout.
- Never log secrets, tokens, full request bodies or personal data; log ids.

## Exceptions policy

| Trigger | Do |
|---|---|
| `except:` | Never. Name the exception. |
| `except Exception:` | Only at a boundary: worker thread top, CLI `main`, request handler, plugin loader. There: `log.exception(...)` then re-raise or return a non-zero status. Never `pass`. |
| Ignoring one expected error | `with contextlib.suppress(FileNotFoundError):` on the single statement. |
| Raising from inside `except` | `raise NewError("context") from err` so the cause is kept; `from None` only to hide a noisy internal. |
| Own error types | One base per package (`class AppError(Exception)`), specific subclasses; no bare `Exception("...")` raises. |
| Input validation | `raise ValueError(...)`, never `assert` (removed under `python -O`). `assert` is for tests and impossible states. |
| File, network and database calls | Try the operation and catch the error (EAFP); checking `exists()` first races with other processes. |
| Several failures at once (3.11) | `ExceptionGroup` and `except*` only for `asyncio.TaskGroup` or batch jobs. |
| Failure value | Raise; do not return `None` or `-1` to mean failure while success can also be falsy. |
| Added context (3.11) | `err.add_note("while parsing line 12")` before re-raising. |

## Review traps (each is a one-line check)

| Trigger in code | Fix |
|---|---|
| `datetime.utcnow()` or `datetime.now()` stored or compared | `datetime.now(timezone.utc)` (`utcnow` is deprecated since 3.12) |
| `subprocess.run(cmd, shell=True)` with any variable in `cmd` | list of arguments, `check=True`, `timeout=` set |
| `zip(a, b)` where lengths must match | `zip(a, b, strict=True)` |
| `random` used for tokens, ids or passwords | `secrets.token_urlsafe(32)` |
| `open(p)` without `with` | `with p.open(encoding="utf-8") as fh:` |
| `if x == None`, `if len(xs) == 0` | `if x is None`, `if not xs` |
| Module-level code that runs on import (connect, parse args, call `main()`) | wrap in `if __name__ == "__main__":`; required on Windows and macOS for `multiprocessing` too |
| `import *` | explicit names |
| `requirements.txt` as the only dependency record of a package | `[project] dependencies` in `pyproject.toml` |

## Concurrency, packaging, tests

Pick by workload, not by habit: waiting on many network calls is `asyncio` or threads, heavy computation is processes. The thresholds and the async rules are in [references/decision-tables.md](references/decision-tables.md) section 2. Packaging (`pyproject.toml` skeleton, `src/` layout, version pins) is section 3, pytest conventions section 4. Read the section only when the task touches it. Sources for the version-specific facts are listed in [references/sources.md](references/sources.md); read it only to re-check a claim.

## Audit script

`scripts/py_audit.py`: run it. Standard library only; reads files, writes nothing, runs none of the audited code. Rules:

| Rule id | Flags |
|---|---|
| `bare-except` | `except:` with no type |
| `mutable-default` | list, dict or set literal or `list()`, `dict()`, `set()`, `defaultdict()`, `deque()` as a parameter default |
| `print-in-library` | `print()` in a file with no main guard that is not `__main__.py`, `test_*.py`, `*_test.py` or `conftest.py` |
| `os-path` | `os.path.<x>`, `import os.path`, `from os.path import ...` |
| `missing-main-guard` | a top-level call statement, or a `main` function nobody guards, in a file with no `if __name__ == "__main__"` |
| `unused-import` | imported name never used; skipped in `__init__.py`, `__future__` and names in `__all__` |

Output: `{"tool","version","files_scanned","findings":[{"file","line","col","rule","message"}],"counts","errors","verdict"}`; verdict is `clean`, `findings` or `incomplete` (a file could not be parsed). Exit 0 clean, 1 findings or errors, 2 bad usage or no Python files. `python scripts/py_audit.py --rules` prints the rule list. Suppress per line with `# noqa` or `# audit: ignore <rule-id>`.

## Limits

- The script is syntactic. It cannot see types, runtime behaviour, a `print` that is the real output of a library function, or an import used only in a doctest or a string the script does not parse.
- `unused-import` treats a name as used if it appears as a name or inside a string annotation; names used only through `globals()` or in `# type:` comments are reported.
- The numeric thresholds in the reference tables (concurrency counts, task sizes) are working values from common practice, not measured for your workload; measure before committing to a design.
- Rules target application and library code on 3.11 and newer. Notebooks, throwaway scripts and one-off migrations may break them on purpose.
- Style and formatting (line length, quotes, import order) are left to the project's formatter.
