# Listing page content: android-practices

**One line:** Native Android (Kotlin, Compose) rules plus a scanner that help an agent write idiomatic, leak-free app code.

## What it does

The skill makes the agent read the Gradle version files first (SDK levels, Kotlin, Compose, lifecycle, coroutines), then pick the rule set for the task (architecture and state, Compose performance, coroutines and Flow, lifecycle, permissions and privacy, accessibility, testing, release) and read only the matching reference. A regex scanner, `scripts/android_scan.py`, walks `.kt` files and reports six documented anti-patterns with line numbers, severity and confidence as strict JSON. The agent fixes, re-runs, and closes with a fixed report that lists unconfirmed claims and what was not checked.

## Capabilities

- `scripts/android_scan.py` flags `GlobalScope`, `runBlocking` (warn in UI-like files, info elsewhere), `!!` density, unguarded `Log.d` and `Log.v`, literal strings in `@Composable` bodies, and Context, Activity, Fragment or View held in `object` or `companion object`
- State placement table (remember, hoisted, ViewModel, saved state), one-off event pattern, Route/Screen split
- Scope, dispatcher and Flow-collection decision tables; cancellation traps
- Permission decision table (picker before permission), request flow, manifest hygiene
- Accessibility numbers (48 dp, 4.5:1, 200% font scale) and semantics recipes
- Testing pyramid, coroutine and Compose test recipes, and a copyable release checklist with store values marked unconfirmed

## When to use

You work on a native Android app and ask about ViewModel and state, recomposition and jank, lifecycle or leak bugs, coroutines and Flow, runtime permissions, TalkBack, Compose tests, or a pre-release review.

## When not to use

Flutter (see `flutter-practices`), React Native (see `react-native-practices`), iOS, Kotlin Multiplatform shared-module design, backend Kotlin, store listing copy. It does not measure runtime performance and does not replace Android lint or the unit tests.

## How it differs from react-native-practices and flutter-practices

Same structure, different stack. This skill covers Kotlin and Jetpack Compose: ViewModel and `StateFlow`, lifecycle-aware collection, structured concurrency, Android permissions and manifest hygiene, Compose semantics, and the Play release path. Its scanner reads `.kt` files. Overlap was checked by folder name only: no other Android skill exists in the registry.

## Requirements

Python 3.9 or newer for the scanner (standard library only). No network. Without Python the agent follows the manual checks in SKILL.md step 4.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real scanner runs on saved fixtures (no with-skill agent run exists yet), from the skill folder:

1. `python scripts/android_scan.py evals/files/t1-sync-viewmodel`: exit 1; `log-in-release` warn (lines 19 and 30), `runblocking-in-ui` warn at line 20, `global-scope` warn at line 27.
2. `python scripts/android_scan.py evals/files/t3-prerelease-review`: exit 1; `log-in-release` warn at line 9 and three `hardcoded-string-in-composable` info findings (lines 11, 12, 15). The icon with `contentDescription = null` and the three `!!` (below the threshold of 4) are silent.
3. `python scripts/android_scan.py evals/fixtures/good`: exit 0, 3 files scanned, no findings; a generated file and a test file are listed under `skipped`, and `src/debug` is exempt from the log rule.

## Limits

- Regex scan, not the Kotlin compiler or Android lint; run `./gradlew lint` as well.
- Only `.kt` files; block-bodied `@Composable` functions only for the string rule.
- `log-in-release` cannot see R8 log-stripping rules or logging trees.
- `context-leak-static` reads direct-typed properties only; plain `Context` is medium confidence.
- Thresholds (4 and 8 `!!`, 4-line guard window, 5 000 ms, 50 KB) are working values, not measured.
- Library and store details change; unconfirmed items are tagged.
- Nothing measures runtime performance.

## Evidence

See `VERIFICATION.md`. Passed: static lint, 13 script fixture cases. Not tested: efficacy against a baseline, trigger behaviour, native discovery, cross-tool use, human review, and all version-dependent facts.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a ViewModel that freezes on refresh; the agent reads the Gradle version files and states them.
2. Run the scanner: warn for `runBlocking`, `GlobalScope` and two `Log.d` calls.
3. The agent switches to `viewModelScope` and a suspend repository call, guards the logs; re-run shows zero warn.
4. The agent reports that nothing was run on a device and that lint and tests were not run.

## FAQ seeds

- Does it need network? No.
- Does it replace Android lint? No; it adds a few judgement checks and the rules around them.
- Will it tell me the current Play target-API deadline? No; it marks it unconfirmed and points to the source list.
- Does it pick a DI or navigation library for me? No; it keeps what the project uses.
- Does it work for XML Views apps? The lifecycle, permissions, testing and release rules do; the Compose rules do not.
- Why is a hard-coded string only info? The app may not need localisation, and the scanner cannot see the project policy.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
