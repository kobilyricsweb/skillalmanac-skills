## Contents

- Test pyramid and what goes where
- Unit test recipes
- Compose UI test recipes
- Flaky test causes
- Release checklist

## Test pyramid and what goes where

Official guidance (working rule of thumb, not an optimum): about 70% small tests, 20% medium, 10% large.

| Size | Runs on | Covers | Do not |
|---|---|---|---|
| Small | local JVM (`src/test`) | ViewModels, use cases, repositories with fakes, mappers, reducers | start Android framework classes; use Robolectric only when a framework class is unavoidable |
| Medium | JVM with Robolectric, or device | Compose screens with a fake state, Room DAO against an in-memory database, navigation graphs | hit the real network |
| Large | device or emulator (`src/androidTest`) | two or three money paths end to end, permission flows, upgrade from the previous version | cover every screen; they are slow and flaky |

Prefer hand-written fakes (`FakeRepository` with a `MutableStateFlow`) to mocking frameworks for repositories: fakes keep behaviour and are reusable by UI tests. Mock only what you cannot fake (system services).

## Unit test recipes

- Coroutine tests: `runTest { }`; pass `StandardTestDispatcher(testScheduler)` into the class through its constructor. Replace `Dispatchers.Main` with a test rule that calls `Dispatchers.setMain(dispatcher)` before and `resetMain()` after.
- `StandardTestDispatcher` queues work until you call `advanceUntilIdle()` or `runCurrent()`; `UnconfinedTestDispatcher` runs eagerly (good for `stateIn` with `WhileSubscribed` only when a collector is launched with `backgroundScope`).
- StateFlow test: start a collector in `backgroundScope` (`backgroundScope.launch { vm.state.collect() }`) so `WhileSubscribed` has a subscriber, then assert `vm.state.value`.
- Flow with many emissions: a third-party Flow test library is common; otherwise collect to a list in `backgroundScope` and compare. Do not `delay` real time.
- Assert on state objects (`assertEquals(Content(name = "A"), vm.state.value)`), not on internal calls.
- One behaviour per test, named for the behaviour (`saveFails_showsErrorAndKeepsDraft`).

## Compose UI test recipes

- `createComposeRule()` for a composable alone; `createAndroidComposeRule<MainActivity>()` only when you need an Activity.
- Test the stateless `Screen` composable with a hand-built `UiState`; no ViewModel, no network.
- Find nodes by text or content description first, by `Modifier.testTag("x")` only when no user-visible semantics exist. Never by index or position.
- `composeTestRule.onNodeWithText("Save").performClick()` then assert the callback recorded by a lambda in the test.
- Wait for async UI with `waitUntil { ... }` (timeout in milliseconds) or by `waitForIdle()`; never `Thread.sleep`. Infinite animations stop idle sync: turn off auto-advance (`mainClock.autoAdvance = false`) and step the clock.
- Accessibility assertions in tests: `onNodeWithContentDescription("Close").assertHasClickAction()`; check a touch target with `assertWidthIsAtLeast(48.dp)`.
- Screenshot tests need a pinned environment (OS, fonts, density); keep them on one CI image.

## Flaky test causes

1. Real dispatchers (`Dispatchers.IO` hard-coded) racing the test thread.
2. A shared singleton or database across tests; reset or create per test.
3. Animations on the device; disable system animations on CI emulators.
4. Order dependence through static state (`object` caches).
5. Time and locale: inject a `Clock`; pin locale and time zone in the test.
6. Permission and notification dialogs on emulators; grant through test rules or `adb shell pm grant` in setup.

## Release checklist

Copy and tick. Items marked (unconfirmed) have values that change yearly: confirm on the console on release day.

```
Build
- [ ] release build type: minifyEnabled/isMinifyEnabled true, shrinkResources true, debuggable false
- [ ] R8 keep rules cover reflection, serialization and JNI entry points; the release build was launched and the main flows walked (R8 problems appear only in release)
- [ ] mapping file (and native symbols) uploaded to the crash reporter for this versionCode
- [ ] versionCode strictly increases; versionName matches the release notes
- [ ] app bundle (AAB) built; signing through the store's app-signing service; upload key stored outside the repository
- [ ] targetSdk meets the store's current deadline (unconfirmed); compileSdk is not older than targetSdk
- [ ] native libraries: 64-bit present; page-size requirement for recent targets (unconfirmed)
Quality
- [ ] ./gradlew lint with warnings reviewed; scanner: zero warn
- [ ] unit and Compose tests green on CI; at least one run on a physical device for the main path
- [ ] upgrade test from the previous release (database migration, saved preferences)
- [ ] strict mode and leak detector were debug-only and are absent from release
- [ ] no Log.d or println of user data in release (scanner rule log-in-release)
Privacy and policy
- [ ] manifest permissions equal what the app uses; exported flags explicit
- [ ] data-safety form matches the SDKs and permissions (unconfirmed policy)
- [ ] privacy policy URL live; account deletion path present if accounts exist (unconfirmed)
- [ ] no test endpoints, test keys or debug menus reachable
Performance and stability
- [ ] baseline profile generated and included, or the decision not to is recorded
- [ ] cold start and one scroll benchmark measured on a mid-range device in a release-like build
- [ ] crash-free and ANR rates of the previous release read from the vitals dashboard; stop-ship thresholds agreed (the store's bad-behavior thresholds are unconfirmed)
Rollout
- [ ] staged rollout starting small (working values 1%, 5%, 20%, 50%, 100%) with a named person watching crashes between steps
- [ ] rollback plan: halt the rollout; the fix ships as a higher versionCode (a published build cannot be unpublished from devices)
```

When a checklist item cannot be verified from the repository (store console values, signing setup), write it in the report under "Not checked"; do not tick it.
