---
name: flutter-practices
description: Guides an agent writing or reviewing Flutter and Dart app code, with a scanner for missing const, print in lib, setState in build, oversized build methods, heavy null assertions and dropped Futures. Use when the user works on a Flutter app, asks about jank, needless rebuilds, setState vs Provider, Riverpod or Bloc, widget tests, Semantics, or a Flutter code review. Covers widget composition, state management choice, async errors, navigation, theming, platform channels, testing and release. Do not use for React Native, native Swift or Kotlin, server-side Dart without Flutter, or app store marketing.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, run the manual checks in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Flutter practices

Mobile Flutter and Dart rules for an agent that writes or reviews app code. Sibling skill for another stack: `react-native-practices`. Flutter web or desktop specifics are out of scope except where a rule is platform-neutral.

## Version rule

Before any API advice, read `pubspec.yaml` and note the `environment: sdk` range (Dart major matters: Dart 3 adds records, patterns and sealed classes), the `flutter` constraint, the state package and its major, the router package, and whether `uses-material-design` and Material 3 are on. State these in the answer. A claim tagged "verify (unconfirmed)" in the references is from memory: tell the user and point to [references/sources.md](references/sources.md) instead of presenting it as fact.

## Workflow

```
- [ ] 1 Read versions and project layout
- [ ] 2 Classify the task
- [ ] 3 Apply the matching rules
- [ ] 4 Run the scanner (or the manual checks)
- [ ] 5 Fix, re-run, report
```

1. **Read versions** as above. Find `lib/`, the entry point, the router and the state layer.
2. **Classify** and read only the matching reference.

| Task | Rules in | Read |
|---|---|---|
| Jank, needless rebuilds, long build method, slow list | Widgets below | [references/widgets-and-performance.md](references/widgets-and-performance.md) |
| Choosing or reviewing state management | State table below | [references/state-async-navigation.md](references/state-async-navigation.md) |
| Futures, streams, errors, context after await, routing | Async and navigation below | [references/state-async-navigation.md](references/state-async-navigation.md) |
| Theme, dark mode, Semantics, text scale, tap targets | Theming and accessibility below | [references/platform-a11y-theme.md](references/platform-a11y-theme.md) |
| Camera, sensors, native SDK, MethodChannel | Platform channels below | [references/platform-a11y-theme.md](references/platform-a11y-theme.md) |
| Writing tests, golden files, CI | Testing below | [references/testing-release.md](references/testing-release.md) |
| Store or internal release | Release below | [references/testing-release.md](references/testing-release.md) |

3. **Apply** the rules below. Smallest change that fixes the stated problem; do not swap the state package in a jank task.
4. **Scan.** Run `python scripts/flutter_scan.py <folder>` on the changed folders and read the JSON (contract below). Without Python, search the changed files for: `print(` outside `kDebugMode`, `setState(` as a direct statement of `build`, `build` methods over 80 lines, `!` after identifiers, calls to `Future`-returning functions with no `await` or `unawaited`, and widget calls with literal arguments lacking `const`. Never edit the script to make a finding go away.
5. **Fix and report.** Resolve every `warn`; for each `info` fix it or give a one-line reason. Re-run until warn is 0 or each remaining warn is explained. End with the report format at the bottom.

## Widgets

- `build` is pure and cheap: no network, no sorting or parsing of large data, no creating a controller, `Future`, `Stream` or `GlobalKey` inside it. Create those in `initState`, a provider, or a state object, and dispose them.
- Split by widget class, not by helper method `_buildHeader()`: a class can be `const`, gets its own element and can skip rebuilds; a method cannot.
- Working thresholds (not measured): build method over 80 lines is a prompt to extract, over 150 is a defect to fix. Scanner uses the same numbers.
- `const` every constructor call whose arguments are literals or other constants, and give your own widgets a `const` constructor. Rebuild cost of a const subtree is zero for that subtree.
- Keep `setState` low: call it in the smallest widget that owns the changed value, so the rebuilt subtree is small. Do not hoist a value into the page widget because two children need it; see the state table.
- Lists that can exceed about two screens use `ListView.builder` (or slivers), never `Column` inside `SingleChildScrollView` with a mapped list. Give list items a `ValueKey(id)` when rows can reorder or be removed.
- Heavy work (parsing JSON over about 1 MB, image processing) goes to `Isolate.run` or `compute`, not the UI isolate. Frame budget is about 16.7 ms at 60 Hz and 8.3 ms at 120 Hz.
- Measure jank in profile mode on a real mid-range device (`flutter run --profile`), never in debug mode or a simulator.

## State management decision table

Choose by the state's scope and lifetime, not by popularity. One approach per feature; do not stack two global stores.

| Situation | Use | Why |
|---|---|---|
| Value used by one widget and its children, dies with the screen (toggle, form field, animation) | `setState` or `ValueNotifier` + `ValueListenableBuilder` | No dependency, no boilerplate |
| Shared by a subtree of one feature, few readers, simple updates | `InheritedWidget`-based provider (Provider-style) with `ChangeNotifier` | Small, readable, easy to test |
| Server data with caching, loading and error states, dependent queries, many consumers | Reactive provider container (Riverpod-style) or a repository plus a notifier per query | Declared dependencies, disposal, selective rebuilds, no `BuildContext` needed to read |
| Complex flows with explicit events, strict traceability, several engineers, undo or replay | Event-to-state machine (Bloc-style) | Every transition is an explicit, testable event |
| Cross-screen app state (auth, locale, theme) | One small global notifier or provider at the root | Created once, injected, replaceable in tests |

Rules: server data is never copied into a second store; state classes are immutable (sealed class or `freezed`-style variants for loading, data, error); widgets read the narrowest slice (`select`, `buildWhen`, `ValueListenableBuilder` on one value) so unrelated changes do not rebuild them. Package APIs change between majors: tag version details "verify (unconfirmed)".

## Async and errors

- Every `Future` is awaited, returned, or wrapped in `unawaited(...)` (from `dart:async`) with its own error handling. A dropped Future turns its failure into an unhandled exception.
- After any `await` in a `State` method, check `if (!mounted) return;` before `setState`, and `if (!context.mounted) return;` before using a `BuildContext` ("verify (unconfirmed)" for the minimum Flutter version of `context.mounted`). Never hold a `BuildContext` in a long-lived object.
- A `FutureBuilder` or `StreamBuilder` must receive a future or stream stored in state; creating it inside `build` restarts it on every rebuild.
- Catch specific exceptions where you can act on them; model expected failures as values (a sealed `Result`-style type) at repository boundaries, and let unexpected ones reach the global handlers: set `FlutterError.onError` and `PlatformDispatcher.instance.onError` once in `main` and send both to crash reporting (verify (unconfirmed) for older SDKs that used `runZonedGuarded`).
- Dispose what you create: `TextEditingController`, `FocusNode`, `ScrollController`, `AnimationController`, `StreamSubscription`, timers. Dispose in `dispose()`, before `super.dispose()`.
- `!` is a runtime crash waiting for null. Prefer an early `return` after a null check, `??` with a default, pattern matching (`if (x case final v?)`), or making the field non-nullable. Fields cannot be promoted by a null check (verify (unconfirmed) for private final fields in recent Dart), so copy to a local `final` first. Scanner thresholds: info from 4 per file, warn from 8 and at least 2 per 100 code lines.

## Navigation

One router for the app. Declarative routing (a router package with path parameters and redirects) when you need deep links, web URLs or auth guards; imperative `Navigator.push` is fine for a few screens with no deep links. Route arguments carry ids and small values, never a whole model or a callback. Redirects for auth are decided in one place, not inside each screen. Decide the router package from `pubspec.yaml`; do not add one in a bug-fix task.

## Theming and accessibility

Colors and text styles come from `Theme.of(context)` (`colorScheme`, `textTheme`), defined once in `ThemeData`; no hard-coded `Color(0x...)` or font sizes in screens. Provide light and dark themes. Every icon-only button has a `tooltip` or `Semantics(label: ...)` naming the action. Tap targets are at least 48 by 48 logical pixels (Material) and not below 44 (iOS guideline). Text contrast is at least 4.5:1 (3:1 for large text). Layouts must survive a larger text scale without overflow (test at 1.5 and 2.0). Details: [references/platform-a11y-theme.md](references/platform-a11y-theme.md).

## Platform channels

Use an existing maintained plugin first. Write a channel only for a gap, keep it thin (one method per native capability, serialisable arguments only, typed error codes), generate the interface with a code generator when there are more than three methods, and never call a channel from `build`. Native handlers run on the platform main thread by default, so long native work must hop to a background thread there. Procedure and error contract: [references/platform-a11y-theme.md](references/platform-a11y-theme.md).

## Testing

Pyramid (working guidance, not a measured optimum): many unit tests on pure Dart (repositories, notifiers, parsers), a moderate number of widget tests for screens with fake dependencies, few integration tests for the two or three money paths on a device. Widget tests find by `Key`, semantics label or type, not by position. `pumpAndSettle` never settles with an endless animation; pump an explicit duration instead. Golden files differ by OS and font; pin one CI platform. See [references/testing-release.md](references/testing-release.md).

## Release

Walk [references/testing-release.md](references/testing-release.md) section "Release checklist" item by item. Store requirements (Android target API level, iOS privacy manifest, SDK minimums) change every year: tag them "verify (unconfirmed)" and tell the user to confirm on the store page on release day.

## Script contract

`python scripts/flutter_scan.py <file-or-folder> [...]`: run it, do not edit it. Reads `.dart` only; writes nothing; no network. Prints one JSON object:

```
{"schema_version": 1, "tool": "flutter_scan", "files_scanned": int,
 "findings": [{"file", "line", "rule", "severity": "warn"|"info",
               "confidence": "high"|"medium"|"low", "match", "why", "fix"}],
 "counts_by_rule": {rule: int}, "summary": {"warn": int, "info": int},
 "skipped": [{"file", "reason"}], "limits": [str]}
```

Rules: `missing-const`, `print-in-lib`, `setstate-in-build`, `long-build-method`, `null-assertion-density`, `unawaited-future`. Exit 0: no warn. Exit 1: at least one warn. Exit 2: no readable `.dart` file, with a plain message on stderr. Generated files (`*.g.dart`, `*.freezed.dart`, a "GENERATED CODE" header) are skipped and listed. Tests (`test/`, `integration_test/`, `*_test.dart`) and `bin/`, `tool/` are exempt from `print-in-lib`; tests are also exempt from the null-assertion rule. Severity and confidence follow fixed rules; they are guesses, not measurements. A finding is a place to look, not a proven defect. `missing-const` is always `info`.

## Report format

```
Versions: <dart sdk range, flutter, state package, router, material 3 yes/no/unknown>
Changed: <files and the rule each change follows>
Scan: <warn and info counts before and after; remaining findings with reason>
Verified on device: <what ran on a device or emulator (profile mode for performance), or "nothing">
Unconfirmed claims: <the verify (unconfirmed) items you relied on>
Not checked: <e.g. flutter analyze not run, performance not measured, store rules not re-read>
```

## Limits

- Regex scan, not the Dart analyzer. Run `flutter analyze` and `dart format` for the authoritative lints; the scanner adds a few judgement checks the default lints omit.
- `missing-const` judges constness from argument text for a fixed widget list; a non-SDK name lowers confidence to low. It cannot see whether a custom constructor is const.
- `setstate-in-build` ignores setState inside nested callbacks and cannot follow a helper called from `build`.
- `unawaited-future` sees only Futures declared in the same file plus a short built-in list; a braceless `if (...)` body is not checked.
- A `!` inside `${...}` interpolation is not counted; strings and comments are masked.
- Build length covers methods named `build` only, and thresholds (80, 150 lines; 4 and 8 assertions) are working values.
- Package details (Provider, Riverpod, Bloc, router majors, Impeller defaults, store requirements) change; the references mark what was not confirmed.
- Nothing here measures runtime performance. Profile before claiming a speed-up.
- Not for React Native, native iOS or Android code, or Dart servers.
