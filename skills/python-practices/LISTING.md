# Listing page content: python-practices

**One line:** Holds Python 3.11+ code to a senior reviewer's standard and audits it with a stdlib ast script.

## What it does

The skill gives an agent a five-step procedure for writing or reviewing Python: read the project's target version and tooling, write with fixed policies, run an ast audit, run the project's own checks, then report in a fixed shape. The policies are tables with triggers: typing, dataclass versus pydantic, `os.path` to pathlib, logging instead of print, exceptions, review traps, concurrency (threads, asyncio, processes), pyproject packaging and pytest conventions. The audit script lists six anti-patterns with line numbers as strict JSON.

## Capabilities

- `scripts/py_audit.py <file-or-folder>`: JSON findings (file, line, column, rule, message), counts per rule, verdict `clean`, `findings` or `incomplete`; rules `bare-except`, `mutable-default`, `print-in-library`, `os-path`, `missing-main-guard`, `unused-import`
- Per-line suppression with `# noqa` or `# audit: ignore <rule-id>`
- Decision tables for data models, concurrency, packaging and pytest in `references/`
- A fixed report: target, changes, audit result, project checks, decisions, what was not checked

## When to use

Writing, refactoring, reviewing or modernising Python; adding type hints; choosing dataclass or pydantic; moving from `os.path` or `print`; setting up `pyproject.toml` or pytest; choosing threads, asyncio or processes.

## When not to use

Other languages, notebooks, framework internals (Django, FastAPI), picking a library. Differs from `simplify-and-refactor` (language-agnostic cleanup of changed code): this skill carries Python-specific policy and an ast audit.

## Requirements

Python 3.9 or newer to run the script (standard library only); the rules target code for 3.11 and newer. No network. Without Python the agent greps for the patterns by hand (step 4 of the skill).

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real fixture runs (saved in `evals/fixtures/RESULTS.txt`); no with-skill agent run exists yet.

1. `python scripts/py_audit.py evals/fixtures/bad_library.py`: verdict `findings`, exit 1, 11 findings: unused imports on lines 3 and 5, `os.path` on lines 5 and 10, mutable defaults on lines 9 and 20 (two), `print` on lines 11 and 29, bare `except:` on line 16, missing main guard on line 28.
2. `python scripts/py_audit.py evals/fixtures/bad_script_no_guard.py`: exit 1, `missing-main-guard` and `print-in-library` both at line 4 (a top-level `print` and `sys.exit` that run on import).
3. `python scripts/py_audit.py evals/fixtures/good_library.py`: verdict `clean`, exit 0.

## Limits

- Syntactic only: no types, no runtime behaviour.
- `unused-import` can miss names used only in unparsed strings or comments.
- Numeric thresholds in the tables are working values, not measured for your workload.
- Rules target application and library code on 3.11+; notebooks and one-off scripts may break them on purpose.
- Formatting and import order are left to the project's formatter.

## Evidence

See `VERIFICATION.md`. Static lint passed with 0 FAIL and 0 WARN; 10 of 10 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour, native discovery, cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a legacy module with `os.listdir`, `print`, a bare `except:` and `seen=[]`; run the audit: 7 findings with line numbers.
2. The agent rewrites it: pathlib, logging, named exceptions, `None` default.
3. Re-run the audit: `clean`; run the project's pytest.
4. Show the fixed report, including what was not checked.

## FAQ seeds

1. Does it need network? No.
2. Does it run my code? No; it parses files with `ast` and never imports or executes them.
3. Does it replace ruff or mypy? No; it covers six rules and says which ruff codes match; run the project's own linters too.
4. Does it work below Python 3.11? The script runs on 3.9+; the 3.11-only advice is marked and skipped for older targets.
5. How do I silence a finding? `# audit: ignore <rule-id>` with a reason on that line.
6. Why does it flag `print` in some files only? Files with a main guard, `__main__.py` and tests count as scripts.
7. How is it different from simplify-and-refactor? That one is language-agnostic cleanup; this one is Python policy plus an audit script.
8. What does it add over ruff? ruff already catches the six script rules (E722, B006, T201, PTH, F401 and friends); use ruff when it is configured. This skill adds the decision tables (typing, exceptions, concurrency choice, review traps), the 'project convention wins' rule and a dependency-free audit with a fixed report for repositories without a linter.
9. How do I uninstall it? Delete the `python-practices` folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first draft; static and fixture checks only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
