Sources for the facts used in this skill, restated in our own words. Check them again when a Python minor release ships.

- Python 3.11 release notes, https://docs.python.org/3/whatsnew/3.11.html : adds `tomllib`, `typing.Self`, `enum.StrEnum`, `asyncio.TaskGroup`, `asyncio.timeout`, `ExceptionGroup`, `except*` and `BaseException.add_note`.
- Python 3.12 release notes, https://docs.python.org/3/whatsnew/3.12.html : `datetime.utcnow()` and `utcfromtimestamp()` deprecated; `Path.relative_to(walk_up=True)` added.
- `dataclasses` module, https://docs.python.org/3/library/dataclasses.html : `slots`, `kw_only` and `frozen` parameters; mutable defaults for list, dict and set raise `ValueError`; `default_factory`.
- `pathlib` module, https://docs.python.org/3/library/pathlib.html : the table that maps `os` and `os.path` functions to `Path` methods; `encoding` is a parameter of `read_text`.
- `logging` how-to, https://docs.python.org/3/howto/logging.html : libraries use `getLogger(__name__)` and leave handler configuration to the application; lazy `%s` arguments.
- `concurrent.futures`, https://docs.python.org/3/library/concurrent.futures.html : default `ThreadPoolExecutor` worker count is `min(32, os.cpu_count() + 4)`; process pools pickle arguments.
- `multiprocessing` programming guidelines, https://docs.python.org/3/library/multiprocessing.html : spawn start method re-imports the main module, so the entry code needs a main guard.
- `asyncio` tasks, https://docs.python.org/3/library/asyncio-task.html : `create_task` references can be lost if not kept; `TaskGroup`; `to_thread`.
- Python Packaging User Guide, https://packaging.python.org/en/latest/guides/writing-pyproject-toml/ : `[project]`, `[project.scripts]`, `[project.optional-dependencies]`, `requires-python`.
- PEP 735 dependency groups, https://peps.python.org/pep-0735/ : `[dependency-groups]` table.
- pytest documentation, https://docs.pytest.org/en/stable/ : `tmp_path`, `monkeypatch`, `caplog`, `capsys`, `parametrize` with `ids`, `--strict-markers`, `pytest.approx`.
- Ruff rule index, https://docs.astral.sh/ruff/rules/ : E722 (bare except), B006 (mutable default), T201 (print), PTH (use pathlib), F401 (unused import).
