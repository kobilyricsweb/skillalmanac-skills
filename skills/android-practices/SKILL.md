---
name: android-practices
description: Guides an agent writing or reviewing native Android apps in Kotlin and Jetpack Compose, with a scanner for GlobalScope, runBlocking in UI code, !! density, Log.d left in release code, hard-coded strings in Composables and Context leaks in companion objects. Use when the user works on an Android app, asks about ViewModel, StateFlow, state hoisting, recomposition, lifecycle bugs, coroutines or Flow in Android, runtime permissions, TalkBack semantics, Compose tests or a Play release checklist. Do not use for Flutter, React Native, iOS, Kotlin Multiplatform shared-code design, backend Kotlin or store listing copy.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only. No network access is used. Without Python, run the manual checks in step 4.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# Android practices

Native Android rules (Kotlin, Jetpack Compose) for an agent that writes or reviews app code. Sibling skills for other stacks: `react-native-practices`, `flutter-practices`. Views/XML screens are covered only where a rule is the same (lifecycle, permissions, release).

## Version rule

Before any API advice, read `gradle/libs.versions.toml` or `build.gradle(.kts)`: `compileSdk`, `targetSdk`, `minSdk`, the Kotlin version, the Compose BOM or compiler version, the lifecycle, navigation and coroutines versions, and the DI library. State them in the answer. A claim tagged "verify (unconfirmed)" in this skill is from memory: tell the user and point to [references/sources.md](references/sources.md) instead of presenting it as fact.

## Workflow

```
- [ ] 1 Read versions and module layout
- [ ] 2 Classify the task
- [ ] 3 Apply the matching rules
- [ ] 4 Run the scanner (or the manual checks)
- [ ] 5 Fix, re-run, report
```

1. **Read versions** as above. Find the `app` module, the `ViewModel` classes, the repositories and the manifest.
2. **Classify** and read only the matching reference.

| Task | Rules in | Read |
|---|---|---|
| Layering, where state lives, hoisting, one-off events | Architecture and State below | [references/architecture-state.md](references/architecture-state.md) |
| Recomposition, jank, lazy lists, startup | Compose performance below | [references/architecture-state.md](references/architecture-state.md) |
| Coroutines, Flow, scopes, dispatchers, cancellation | Coroutines below | [references/coroutines-lifecycle.md](references/coroutines-lifecycle.md) |
| Rotation, process death, leaks, back handling | Lifecycle below | [references/coroutines-lifecycle.md](references/coroutines-lifecycle.md) |
| Permissions, storage, secrets, exported components | Permissions and privacy below | [references/permissions-a11y.md](references/permissions-a11y.md) |
| TalkBack, semantics, touch targets, font scale | Accessibility below | [references/permissions-a11y.md](references/permissions-a11y.md) |
| Writing tests, fakes, Compose tests, CI | Testing below | [references/testing-release.md](references/testing-release.md) |
| Store or internal release, R8, signing | Release below | [references/testing-release.md](references/testing-release.md) |

3. **Apply** the rules below. Smallest change that fixes the stated problem; do not introduce a DI framework or new architecture in a bug-fix task.
4. **Scan.** Run `python scripts/android_scan.py <folder>` on the changed folders and read the JSON (contract below). Without Python, search the changed `.kt` files for: `GlobalScope`, `runBlocking`, `!!`, `Log.d(` and `Log.v(` without a `BuildConfig.DEBUG` guard, string literals in `Text(`, `text =` or `contentDescription =` inside `@Composable` functions, and `Context`, `Activity`, `Fragment` or `View` typed properties inside `object` or `companion object`. Never edit the script to make a finding go away.
5. **Fix and report.** Resolve every `warn`; for each `info` fix it or give a one-line reason. Re-run until warn is 0 or each remaining warn is explained. End with the report format at the bottom.

## Architecture and state

Layers (official guidance): UI layer (composables plus a state holder, usually a `ViewModel`), data layer (repositories, data sources), and an optional domain layer of use cases. Add a use case only when logic is shared by two or more ViewModels or is too large for one; a use case that forwards one repository call is noise. Dependencies point inward: UI to data, never the reverse, and the data layer never imports `android.view` or Compose.

Where state lives:

| State | Home |
|---|---|
| Visual-only (scroll position, expanded flag, text being typed before submit) | `remember` or `rememberSaveable` in the composable that owns it |
| Read by two siblings | Hoist to their lowest common parent composable |
| Business rules, data from repositories, survives rotation | `ViewModel`, exposed as one immutable `StateFlow<UiState>` |
| Must survive process death (draft text, selected id) | `rememberSaveable` or `SavedStateHandle`; store ids, never lists or bitmaps |
| App-wide (session, settings) | Repository exposing a `Flow`, collected by ViewModels |

- State goes down, events go up (unidirectional data flow). A composable takes values and lambdas (`onSave: () -> Unit`), never a `ViewModel`. Only the screen-level composable obtains the ViewModel and calls `collectAsStateWithLifecycle()` (lifecycle-runtime-compose; verify (unconfirmed) minimum version 2.6). Plain `collectAsState()` keeps collecting while the app is in the background.
- `UiState` is one immutable class or sealed interface (`Loading`, `Content`, `Error`). Do not expose `MutableStateFlow` or several parallel flows that can disagree.
- One-off events (navigate, snackbar): put them in `UiState` as a nullable value the UI reports as consumed. A `Channel` or `SharedFlow` for events can drop or replay them across rotation (official guidance prefers state; verify (unconfirmed) for current wording).
- Convert a cold `Flow` to state with `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`. The 5 000 ms keeps the upstream alive across a rotation (about 5 s is the documented convention; a smaller value restarts work on every rotation).
- Side effects in composition: `LaunchedEffect(key)` for work tied to a key, `rememberCoroutineScope` for click handlers, `DisposableEffect` for register and unregister pairs, `rememberUpdatedState` for a lambda captured by a long-lived effect. Never launch a coroutine or write state directly in the composable body.

## Compose performance

- A composable is skipped when its inputs are equal and stable. Unstable inputs (`List`, classes from other modules without annotations, lambdas that capture unstable values) force recomposition. Strong skipping mode relaxes this and is on by default in recent Kotlin Compose plugins (verify (unconfirmed): Kotlin 2.0.20 or newer). Check the Compose compiler reports before adding `@Immutable` or `@Stable`.
- `LazyColumn` and `LazyRow`: always pass `key = { it.id }` (stable ids) and add `contentType` when row types differ. No nested vertically scrolling lazy lists; no `Column` in `verticalScroll` with a mapped list of more than about 30 rows (working value).
- `derivedStateOf` only when the input changes more often than the derived result (a scroll offset to a boolean). Do not wrap every computed value.
- Read fast-changing state as late as possible: `Modifier.offset { }` and `graphicsLayer { }` lambdas, or pass `() -> T` instead of `T`, so only the layout or draw phase reruns, not composition.
- Never allocate or sort inside composition without `remember(keys)`. Frame budget is 16.7 ms at 60 Hz and 8.3 ms at 120 Hz. Measure with a release-like build (minified, no debugger) on a mid-range device; debug builds recompose and run several times slower.
- Baseline Profiles and Macrobenchmark are the startup tools; the size of the gain is app-specific, so measure (verify (unconfirmed) any quoted percentage).

## Coroutines

- Scopes: `viewModelScope` in ViewModels, `lifecycleScope` plus `repeatOnLifecycle(STARTED)` in Activities and Fragments, `rememberCoroutineScope` in composables. Never `GlobalScope`. Work that must outlive the screen goes to an injected application scope with a `SupervisorJob`.
- Repository and data-source `suspend` functions are main-safe: they switch with `withContext(ioDispatcher)` themselves. Callers never pick `Dispatchers.IO`. Inject dispatchers (constructor parameter) so tests can replace them. Never hard-code `Dispatchers.Main` in a data layer.
- `runBlocking` is allowed in `main()` of a tool and in tests only. On the main thread it freezes input; the system raises an ANR after about 5 s without input handling (verify (unconfirmed) exact limits).
- Never swallow `CancellationException`. `runCatching { suspendCall() }` and `catch (e: Exception)` both catch it; rethrow it or catch specific types.
- `catch` in a Flow chain handles only upstream errors; put it before `stateIn`. `flowOn` changes only the upstream context. `callbackFlow` must end with `awaitClose { unregister() }`.
- Parallel work: `coroutineScope { async { } ; async { } }` and await both. A bare `launch` in a suspend function that returns early leaks work.

## Lifecycle

- Rotation recreates the Activity; the process can die in the background. State that matters after process death uses `rememberSaveable` or `SavedStateHandle`. The saved-instance Bundle shares a roughly 1 MB binder transaction limit; keep it under about 50 KB (working value) to avoid `TransactionTooLargeException`.
- A ViewModel never holds a `Context`, `Activity`, `View` or `Fragment` (use `AndroidViewModel` with the application context only if unavoidable). A static field of those types is a leak (scanner rule `context-leak-static`).
- Fragments: collect flows with `viewLifecycleOwner`, not `this`; null view bindings in `onDestroyView`.
- Every register has an unregister in the mirror callback (`onStart`/`onStop`, `onCreate`/`onDestroy`), or use a lifecycle-aware API. Compose equivalent: `DisposableEffect` with `onDispose`.
- Back handling: `BackHandler` in Compose; predictive back needs the opt-in manifest flag and an up-to-date target SDK (verify (unconfirmed) for the current default).

## Permissions and privacy

Ask in context, at the moment the feature is used, with the Activity Result API (`rememberLauncherForActivityResult(RequestPermission())`). Handle three outcomes: granted, denied (explain once, keep the feature usable), permanently denied (point to settings; the system stops showing the dialog after repeated denials, verify (unconfirmed) the exact rule). Use a system picker instead of a broad permission whenever one exists (photo picker, document picker, share sheet). Full table in [references/permissions-a11y.md](references/permissions-a11y.md).

## Accessibility

Every image or icon that conveys meaning has `contentDescription`; decorative ones pass `null`. Touch targets are at least 48 by 48 dp. Text uses `sp` and survives 200% font scale. Contrast is at least 4.5:1 (3:1 for large text). Custom clickable rows use `Modifier.clickable(onClickLabel = ...)` or `toggleable(role = ...)`, and `semantics(mergeDescendants = true)` so TalkBack reads one item. Detail: [references/permissions-a11y.md](references/permissions-a11y.md).

## Testing

Pyramid (official rule of thumb, roughly 70% small, 20% medium, 10% large): many JVM unit tests (ViewModels, repositories, mappers) with fakes, some Compose UI tests against fake ViewModels or fake repositories, few device end-to-end tests on the money paths. Use `runTest` with an injected test dispatcher; replace `Dispatchers.Main` with a test rule. Find Compose nodes by semantics (text, content description, test tag), never by position. Details: [references/testing-release.md](references/testing-release.md).

## Release

Walk the "Release checklist" section of [references/testing-release.md](references/testing-release.md) item by item. Play target-API deadlines, the 64-bit and 16 KB page-size rules and vitals thresholds change yearly: mark them "verify (unconfirmed)" and tell the user to confirm on the console on release day.

## Script contract

`python scripts/android_scan.py <file-or-folder> [...]`: run it, do not edit it. Reads `.kt` only; writes nothing; no network. Prints one JSON object:

```
{"schema_version": 1, "tool": "android_scan", "files_scanned": int,
 "findings": [{"file", "line", "rule", "severity": "warn"|"info",
               "confidence": "high"|"medium"|"low", "match", "why", "fix"}],
 "counts_by_rule": {rule: int}, "summary": {"warn": int, "info": int},
 "skipped": [{"file", "reason"}], "limits": [str]}
```

Rules and severity: `global-scope` (warn); `runblocking-in-ui` (warn in a file that mentions @Composable, an Activity, Fragment, ViewModel, Service or receiver; info elsewhere; not checked in files with `fun main`); `null-assertion-density` (info from 4 `!!` per file, warn from 8 and at least 2 per 100 code lines); `log-in-release` (warn for `Log.d` and `Log.v` without a `BuildConfig.DEBUG` guard on the line or the 4 lines above; info for `println` and `printStackTrace`); `hardcoded-string-in-composable` (info); `context-leak-static` (warn, medium confidence for plain `Context`, high for Activity, Fragment or View types). Exit 0: no warn. Exit 1: at least one warn. Exit 2: no readable `.kt` file, with a plain message on stderr. Skipped and listed: test source sets (`test/`, `androidTest/`, `*Test.kt`), generated files (header says generated or do not edit), folders `build`, `.gradle`, `generated`. `src/debug/` is exempt from `log-in-release`. A finding is a place to look, not a proven defect.

## Report format

```
Versions: <compileSdk, targetSdk, minSdk, Kotlin, Compose BOM, lifecycle, coroutines, DI>
Changed: <files and the rule each change follows>
Scan: <warn and info counts before and after; remaining findings with reason>
Verified on device: <what ran on a device or emulator (release-like build for performance), or "nothing">
Unconfirmed claims: <the verify (unconfirmed) items you relied on>
Not checked: <e.g. lint not run, tests not run, performance not measured, Play rules not re-read>
```

## Limits

- Regex reading of Kotlin, not the compiler or Android lint. Run `./gradlew lint` and the unit tests for authoritative results; the scanner adds a few judgement checks and the rules around them.
- Only `.kt` files; Java, `.kts` and XML layouts are not read.
- `hardcoded-string-in-composable` sees block-bodied composables only, skips `@Preview` functions, and checks a fixed set of call sites; a string passed through a variable is invisible.
- `log-in-release` cannot see R8 rules that strip logs, a logging tree, or wrapper classes.
- `context-leak-static` reads property declarations with a direct type; generic holders and inferred types are missed, and an application Context in a static is usually acceptable (hence medium confidence).
- Thresholds (4 and 8 assertions, 2 per 100 lines, 4-line guard window, 5 000 ms, 50 KB) are working values, not measured.
- Library and store details (lifecycle, Compose compiler, target API, vitals) change; the references mark what was not confirmed.
- Nothing here measures runtime performance. Profile before claiming a speed-up.
- Not for Flutter, React Native, iOS or backend Kotlin.
