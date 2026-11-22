# Listing page content: flutter-practices

**One line:** Flutter and Dart rules plus a scanner that help an agent write idiomatic, performant app code.

## What it does

The skill makes the agent read `pubspec.yaml` first (Dart and Flutter constraints, state package, router), then pick the rule set for the task (widgets and performance, state management, async and errors, navigation, theming and accessibility, platform channels, testing, release) and read only the matching reference. A regex scanner, `scripts/flutter_scan.py`, walks `.dart` files and reports six documented anti-patterns with line numbers, severity and confidence as strict JSON. The agent fixes, re-runs, and closes with a fixed report that lists unconfirmed claims and what was not checked.

## Capabilities

- `scripts/flutter_scan.py`: flags widget calls with literal arguments but no `const`, `print` / `debugPrint` in lib code, `setState` called directly in `build`, build methods over 80 and 150 lines, many postfix `!` null assertions, and dropped Futures
- State management decision table with vendor-neutral criteria (setState, notifier provider, reactive provider container, event-to-state machine)
- Async and error rules: mounted checks, builders, disposal, layered error handling with global handlers
- Accessibility checklist (48 and 44 pixel tap targets, 4.5:1 contrast, text scale) and platform-channel contract
- Testing pyramid and a release checklist with store requirements marked unconfirmed

## When to use

You work on a Flutter app and ask about jank, needless rebuilds, choosing between `setState`, Provider, Riverpod or Bloc, async bugs, widget tests, accessibility or a pre-release review.

## When not to use

React Native (see `react-native-practices`), native Swift or Kotlin, Dart servers without Flutter, store marketing copy. It does not measure runtime performance and does not replace `flutter analyze`.

## How it differs from react-native-practices

Same structure, different stack. This skill covers Dart and the widget tree: const and widget-class composition, `BuildContext` and `mounted` rules, Dart null safety, Flutter testing tools and the Flutter release path. Its scanner reads `.dart` files; the React Native scanner reads `.tsx` and `.jsx`. No other skill in the registry covers Flutter.

## Requirements

Python 3.9 or newer for the scanner (standard library only). No network. Without Python the agent follows the manual checks in SKILL.md step 4.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

Real scanner runs on saved fixtures (no with-skill agent run exists yet), from the skill folder:

1. `python scripts/flutter_scan.py evals/files/t1-settings-screen`: exit 1; `setstate-in-build` (warn, line 19), `print-in-lib` (warn, line 23), six `missing-const` info findings (lines 25, 28, 33, 42, 44, 45).
2. `python scripts/flutter_scan.py evals/files/t2-checkout-flow`: exit 1; `unawaited-future` warn for `loadCart()` (line 23) and `trackEvent('submit')` (line 24), both medium confidence.
3. `python scripts/flutter_scan.py evals/fixtures/good`: exit 0, no findings; a generated `model.g.dart` is listed under `skipped`, and `test/` and `bin/` files are exempt from the print rule.

## Limits

- Regex scan, not the Dart analyzer; run `flutter analyze` as well.
- `missing-const` is a heuristic on argument text; non-SDK names lower confidence.
- `unawaited-future` sees only same-file Future declarations plus a short built-in list.
- Thresholds (80 and 150 lines, 4 and 8 null assertions) are working values, not measured.
- Package and store details change; unconfirmed items are tagged.
- Nothing measures runtime performance.

## Evidence

See `VERIFICATION.md`. Passed: static lint, 10 script fixture cases. Not tested: efficacy against a baseline, trigger behaviour, native discovery, cross-tool use, human review, and all version-dependent facts.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. Show a settings screen that rebuilds too much; the agent reads `pubspec.yaml` and states the versions.
2. Run the scanner: warn for `setState` in build and `print`, info for six missing `const`.
3. The agent moves the initial state to `initState`, adds `const`, removes the print; re-run shows zero warn.
4. The agent reports what was not measured in profile mode on a device.

## FAQ seeds

- Does it need network? No.
- Does it replace `flutter analyze`? No; it adds a few judgement checks and the rules around them.
- Will it tell me the exact current store rules? No; it marks them unconfirmed and points to the sources list.
- Does it pick a state management package for me? It gives a decision table by scope and cost; the choice stays with the team.
- Does it work for Flutter web or desktop? Only for platform-neutral rules.
- Why is a missing `const` only info? The scanner cannot confirm a custom constructor is const.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

- 0.1.0 (2026-11-21): first version; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by an AI model (claude-sonnet-5-5). No human editor has reviewed it yet; accountable editor: Global Media Holdings.
