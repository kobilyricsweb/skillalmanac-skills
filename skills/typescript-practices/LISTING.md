# Listing page content: typescript-practices

**One line:** Helps an agent write and review strict TypeScript, with a scanner that lists unsafe patterns by line.

## What it does

The skill gives an agent a six-step procedure for strict TypeScript work: find the project's own type-check command and tsconfig, scan the files, fix each finding from a replacement table, write new code with fixed defaults, verify with the project's `tsc` and a re-scan, and report in a fixed shape. The table maps nine scanner rules to a replacement and to the only case where the escape hatch may stay. Two reference files carry the tsconfig flag table (what each flag rejects, an order of enabling, module settings by project kind) and the recipes (Result type, `assertNever`, narrowing, replacing `enum`, `satisfies`, boundary parsing, module boundaries). A decision table settles `type` against `interface`.

## Capabilities

- `scripts/ts_scan.py`: JSON report of nine anti-pattern rules with file, line, column, severity, message and the source line; counts per rule; suppressed findings; its own list of false-positive limits
- Tokenizer that ignores comments, strings, template literals and regex literals, so patterns inside text are not reported
- Inline `// ts-scan-ignore: <rule> -- <reason>` that keeps an accepted exception visible
- tsconfig baseline with a rollout order for an existing code base
- A fixed report: scanned, fixed, kept on purpose, type-check result, suggested next, not checked

## When to use

You ask for stricter TypeScript, removal of `any`, a review of `.ts` or `.tsx` files, a tsconfig strict setup, a `type` or `interface` decision, exhaustive switches, or Result-style error handling.

## When not to use

Plain JavaScript, framework design (React, Angular), build-tool configuration, comparing schema validation libraries. Difference from `python-practices`: different language and different checker; this skill has no Python content and no overlap in rules.

## Requirements

Python 3.9 or newer for the scanner (standard library only, no network). The project's own TypeScript install for the type check. Without Python the agent searches for the patterns by hand using the rule table.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Both outputs below come from `python evals/run_fixtures.py`-covered fixtures.

1. `python scripts/ts_scan.py evals/fixtures/bad.ts --min-severity high` returns exit code 1 and four findings: `double-assertion` at line 13 (`(raw as unknown as Config)`), `ts-suppression-no-reason` at lines 17 (`// @ts-ignore`) and 23 (`// @ts-expect-error`), and `ts-nocheck` at line 29. The same file without the severity filter has 18 findings across 9 rules.
2. `python scripts/ts_scan.py evals/fixtures/traps.ts` returns exit code 0 and `"total_findings": 0`, although the file mentions `any`, `enum`, `export default` and `as unknown as` inside comments, strings, template literals and regex literals.

No with-skill agent run exists yet, so no saved edit is shown.

## Limits

- Tokenizer plus regular expressions, no type information: finds the written word `any`, not values that are `any` by inference.
- Can flag an identifier named `any`, JSX text, or a default export a framework requires; can miss `!` at a line end in `.tsx`.
- A clean scan is not a type-safety proof; only the project's `tsc` is.
- Assumes TypeScript 5.x for the flag advice.

## Evidence

See `VERIFICATION.md`. In short: static lint with 0 FAIL and 0 WARN; 11 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, any cross-tool install, human review.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A service file with `any`, `!`, `as unknown as`, an enum and a bare `@ts-ignore`; run the scan: 7 findings (enum, default export, two any, double cast, bare ts-ignore, non-null), line numbers shown (the t1 task input).
2. The agent fixes by table: `unknown` plus a guard, an early return, a union instead of the enum, `@ts-expect-error` with a reason.
3. Run `tsc --noEmit` and the scan again: zero findings.
4. Show the report, including what was kept on purpose and what was not checked.

## FAQ seeds

- Does it need network? No.
- Does it run the TypeScript compiler? No. The scanner does not; the skill tells the agent to run the project's own `tsc`.
- Does it work with .tsx? Yes, with a stated weak spot for `!` in JSX text.
- Why does it flag my framework's default export? Use `--profile app` or `ts-scan-ignore`; page, route and config files are exempt already.
- Can it prove my code is type-safe? No; it lists patterns, the compiler checks types.
- Does it enable tsconfig flags for me? It proposes them and a rollout order; it edits the config only when you ask for strictness work.
- How do I uninstall? Delete the skill folder.

## Changelog

| Version | Date | Change | Re-verified |
|---|---|---|---|
| 0.1.0 | 2026-11-21 | First draft | Static and fixtures only |

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5); accountable publisher Global Media Holdings. No human review has taken place yet.
