## Contents

1. Data models: dataclass, pydantic, TypedDict, NamedTuple
2. Concurrency: threads, asyncio, processes
3. Packaging with pyproject.toml
4. pytest conventions

## 1. Data models

| Situation | Use | Why / trigger |
|---|---|---|
| Record you create and pass between your own functions | `@dataclass(slots=True, kw_only=True)` | no validation cost, `slots` saves memory and blocks typo attributes, `kw_only` stops positional mix-ups past 3 fields |
| Same, and instances are dict keys, set members or shared across threads | add `frozen=True` | hashable and immutable; change with `dataclasses.replace` |
| Data arrives from outside the process: HTTP body, JSON file, env, user form | pydantic `BaseModel` (`model_validate`) | it checks and coerces types at the boundary; convert to a dataclass or plain objects after if the interior does not need validation |
| Settings read from environment | pydantic-settings or a frozen dataclass built by one `load_settings()` function | one place reads `os.environ`; nothing else does |
| Dict that stays a dict (parsed JSON you only read, kwargs) | `TypedDict` | typing only, no runtime check; do not build new ones across modules, use a dataclass |
| Small fixed tuple returned by one function (2 to 3 fields) | `NamedTuple` | unpacks like a tuple, named access |
| Mutable default for a field | `field(default_factory=list)` | a literal `[]` default raises `ValueError` in a dataclass for list, dict and set |
| Computed field | `@property` or `field(init=False)` set in `__post_init__` | keep invariants in `__post_init__` and raise `ValueError` |
| More than about 10 fields, or nested optional groups | split into two records | a long field list signals two concepts |
| Need validators, aliases and JSON schema but not at a boundary | still a dataclass plus one explicit `validate()` | pydantic everywhere couples the domain to a library |

Never use a plain `dict[str, Any]` as a record with more than 3 known keys that more than one function reads.

## 2. Concurrency

First decide what the program waits for.

| Workload | Tool | Working thresholds (measure to confirm) |
|---|---|---|
| Many network or disk waits, the libraries have async versions, hundreds or thousands in flight | `asyncio` | above about 100 concurrent connections the thread-per-task cost shows up |
| Waiting on I/O through blocking libraries (requests, a DB driver without async), fewer than about 50 in flight | `concurrent.futures.ThreadPoolExecutor(max_workers=N)` | set `N` yourself; the default is `min(32, cpu_count + 4)` |
| Pure Python computation that keeps a core busy | `ProcessPoolExecutor` | each task should run longer than about 10 ms, or batch items; arguments and results are pickled |
| Computation inside NumPy or another C library that releases the GIL | threads are enough | check the library docs |
| One slow blocking call inside async code | `await asyncio.to_thread(fn, ...)` | never call `time.sleep`, `requests.get` or sync file loops on the event loop |
| Mixed: async I/O plus CPU stage | `loop.run_in_executor(process_pool, ...)` | keep the pool object at module or app level, not per call |

Rules:
- Threads do not speed up CPU-bound pure Python on a standard (GIL) build.
- (3.11) Use `asyncio.TaskGroup` for related tasks (one failure cancels the rest, errors arrive as an `ExceptionGroup`); use `asyncio.timeout(seconds)` instead of `wait_for` for a block of work. `asyncio.gather` is for independent results where you will inspect failures yourself (`return_exceptions=True`).
- Call `asyncio.run(main())` once, at the entry point. Calling it inside a running loop raises `RuntimeError`.
- Keep a reference to every task you create with `create_task`; an unreferenced task can be garbage-collected mid-run. A `TaskGroup` holds them for you.
- Bound fan-out with `asyncio.Semaphore(n)` or a fixed worker count; do not spawn one task per item of a 100,000-item list.
- Processes: on Windows and macOS the default start method is spawn, so the entry module is re-imported; anything outside `if __name__ == "__main__":` runs again in every worker. This is why `missing-main-guard` exists.
- Shared mutable state between threads needs a `threading.Lock` or a `queue.Queue`; prefer passing messages over sharing.
- Always set timeouts on network calls; no timeout means a stuck worker forever.

## 3. Packaging with pyproject.toml

Skeleton for a library or app (standard names from the Python Packaging User Guide):

```toml
[build-system]
requires = ["hatchling>=1.24"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "One sentence."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27,<1",
]

[project.optional-dependencies]
yaml = ["pyyaml>=6"]

[dependency-groups]
dev = ["pytest>=8", "ruff", "mypy"]

[project.scripts]
my-tool = "my_package.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
```

| Trigger | Do |
|---|---|
| New project | `src/my_package/` layout; tests import the installed package, so a missing file in the build is caught |
| `setup.py` or `setup.cfg` only | move metadata to `[project]`; keep `setup.py` only for a compiled extension |
| Library dependencies | lower bound always, upper bound only on a known break; do not pin exact versions in a library |
| Application | commit a lock file (`uv.lock`, or pip-compile output with hashes); install from it in CI |
| Dev tools (pytest, ruff, mypy) | `[dependency-groups]` (PEP 735) or an optional-dependencies `dev` extra; never in runtime `dependencies` |
| Command line tool | `[project.scripts]` entry point pointing at a `main()` that returns an int; do not ship `python path/to/file.py` instructions |
| Version | one source: the `version` field, or `dynamic = ["version"]` with the backend reading it |
| Config for tools | in `[tool.*]` tables of the same file, one file to review |
| Reading TOML in code | `tomllib` (3.11), opened in binary mode: `tomllib.load(fh)` with `open("f.toml", "rb")` |

Build backend choice: hatchling, setuptools (61 or newer reads `[project]`), flit-core or uv_build are all valid; keep the repo's existing one.

## 4. pytest conventions

| Trigger | Convention |
|---|---|
| Test location | `tests/` beside `src/`; files `test_<module>.py`; one `conftest.py` per directory that needs shared fixtures |
| Test name | `test_<unit>_<condition>_<expected>`, for example `test_parse_empty_string_raises_value_error` |
| One test, one behaviour | one logical assert group; if the name needs "and", split it |
| Same logic, many inputs | `@pytest.mark.parametrize("raw, expected", [...], ids=[...])`; write ids so a failure reads clearly |
| Expected exception | `with pytest.raises(ValueError, match="empty"):` always with `match` |
| Temp files | `tmp_path` fixture (a `pathlib.Path`), never `tmpdir`, never a fixed path in the repo |
| Environment, attributes, time | `monkeypatch.setenv`, `monkeypatch.setattr`; restored automatically |
| Floats | `pytest.approx(0.3)`, never `==` |
| Log output | `caplog` fixture; check `caplog.records`, not printed text |
| Printed output of a script | `capsys.readouterr()` |
| Slow or external | custom marker (`@pytest.mark.slow`) registered in `[tool.pytest.ini_options] markers`; `--strict-markers` turns a typo into an error |
| Fixtures | smallest scope that works (`function` default); `yield` fixtures for cleanup; no logic hidden in autouse fixtures unless it is truly global |
| Mocking | mock at the edge you own (an HTTP client wrapper), not the standard library; prefer a small fake class over `Mock` for anything with more than 2 methods |
| Sleeping in tests | never `time.sleep`; inject a clock or poll with a deadline |
| Async tests | `pytest-asyncio` with `asyncio_mode = "auto"`, or `anyio`; a plain `async def test` without a plugin is skipped with a warning |
| Bug report | write the failing test first, see it fail for the right reason, then fix |
