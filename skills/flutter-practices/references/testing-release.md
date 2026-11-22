# Testing and release

Read for: writing or reviewing tests, CI, preparing a release. Claims tagged "verify (unconfirmed)" are from memory; see sources.md.

## Contents

- Test pyramid
- Widget test rules
- Integration and golden tests
- Release checklist

## Test pyramid

Working guidance, not a measured optimum:

| Layer | Tool | Share of effort | Tests |
|---|---|---|---|
| Unit | `package:test` or `flutter_test`, plain Dart | about 60 to 70 percent | Parsers, repositories with a fake client, notifiers and blocs, validators, formatters |
| Widget | `testWidgets`, `WidgetTester` | about 20 to 30 percent | One screen with fake dependencies: renders states (loading, data, error), taps, form validation, navigation calls |
| Integration | `integration_test` package on a device or emulator | about 5 to 10 percent | Two or three money paths end to end: sign in, core action, purchase or save |

Rules: a bug fix starts with a test that fails; fakes beat mocks for repositories (fewer brittle call expectations); no real network or real clock in unit and widget tests; inject a clock and a client.

## Widget test rules

1. Wrap the widget under test with the same app shell it needs (theme, localisation, router or provider scope); a missing ancestor is the most common failure.
2. Find by `Key`, type or semantics label. Avoid finding by index or by exact pixel position.
3. `pump()` advances one frame; `pump(duration)` advances time; `pumpAndSettle()` waits until no frames are scheduled and times out forever on an endless animation or a repeating timer: replace with `pump(Duration)`.
4. Set a fixed surface size and text scale in tests that check layout; also run one pass at a large text scale.
5. Assert on visible outcomes (text on screen, a callback fired once), not on internal state fields.
6. Test the empty, loading and error states, not only the happy path.
7. Dispose is exercised by pumping a different widget at the end when you own controllers or subscriptions.
8. Do not call real platform channels; set a mock handler for the channel name or use a fake wrapper.

## Integration and golden tests

- Integration tests run with `flutter test integration_test` on a device (command shape: verify (unconfirmed) for the current release). Keep them few and stable: seed data through a test backend or a fake repository, avoid sleeps, wait on finders.
- Golden tests compare rendered pixels with a stored image. Fonts and rendering differ by operating system, so generate and compare on one CI platform only, keep goldens small, and review image diffs in the pull request. Update goldens only with an explicit command and a human look.
- Run `flutter analyze` and `dart format --set-exit-if-changed .` in CI before tests. Fail the build on analyzer warnings you decided to keep as errors.
- Measure coverage on unit and widget layers for trend, not as a target; a number alone does not show behaviour is covered.

## Release checklist

Walk it top to bottom and write down each answer. Items marked U are version or store dependent: confirm on the day (verify (unconfirmed)).

```
Code
- [ ] flutter analyze clean; dart format clean; flutter test green
- [ ] No print or debug flags in lib (run the scanner); no TODO that blocks release
- [ ] Dependencies reviewed: flutter pub outdated; no dependency on a git branch or an abandoned package
Config
- [ ] Version and build number bumped (pubspec "version: x.y.z+build"; the build number must increase for each store upload)
- [ ] Release signing set up for Android (keystore kept out of the repo) and iOS (certificates and profiles)
- [ ] Flavors or environment defines point at production endpoints; no staging keys in the build
- [ ] App name, icon and splash correct per platform; permissions in manifest and plist match what the app really uses
Build
- [ ] Android: flutter build appbundle --release (U: required target API level, 64-bit and bundle rules)
- [ ] iOS: flutter build ipa --release (U: minimum Xcode and SDK version, privacy manifest and required-reason API declarations)
- [ ] Obfuscation, if used: --obfuscate with --split-debug-info=<dir>; archive the symbols directory with the build, otherwise crash traces cannot be read
- [ ] Installed the release build (not debug, not profile) on at least one low-end Android device and one iPhone; cold start, sign-in, the core path, rotate, background and resume, offline
Quality
- [ ] Performance checked in profile mode on a real device; no frame over budget on the core screens
- [ ] Accessibility pass with TalkBack and VoiceOver; text scale 1.5 and 2.0
- [ ] Crash reporting initialised in release and tested with a deliberate test crash
- [ ] Analytics and data-collection declarations match the store forms (U)
Rollout
- [ ] Staged rollout percentage chosen; rollback plan named (previous build kept; server feature flags)
- [ ] Release notes written; store listing screenshots current
- [ ] Monitor crash-free sessions and key funnel for the first 24 hours
```

Store requirements change on a yearly cycle. Do not state exact API levels or Xcode versions from memory: tag them "verify (unconfirmed)" and send the user to the store's current requirements page.
