## Contents

- Scope and dispatcher table
- Flow collection table
- Cancellation and error traps
- Lifecycle pitfalls and fixes
- Leak hunting procedure

## Scope and dispatcher table

| Situation | Scope | Dispatcher |
|---|---|---|
| Load data for a screen | `viewModelScope.launch` | default (Main.immediate); the repository switches itself |
| Work after the screen closes (upload, sync a draft) | injected `applicationScope` (`SupervisorJob() + Dispatchers.Default`), or WorkManager when it must survive process death | repository decides |
| Click handler in Compose | `rememberCoroutineScope()` | default |
| Work tied to a composable key | `LaunchedEffect(key)` | default |
| CPU-heavy parsing, sorting, diff | `withContext(Dispatchers.Default)` inside the data or domain class | Default |
| Blocking IO (file, database without Room suspend, socket) | `withContext(Dispatchers.IO)` inside the data class | IO |
| Test | `runTest` with a `StandardTestDispatcher` passed to the class under test | injected |

`Dispatchers.Main.immediate` runs inline when already on the main thread, so the first lines of a `viewModelScope.launch` execute before `launch` returns; do not rely on ordering with code after it.

Never create a `CoroutineScope(...)` in a class without a documented owner that cancels it. Never hold a scope in a `companion object`.

## Flow collection table

| Where | Use |
|---|---|
| Composable | `flow.collectAsStateWithLifecycle()` at the Route level |
| Activity or Fragment (views) | `viewLifecycleOwner.lifecycleScope.launch { repeatOnLifecycle(Lifecycle.State.STARTED) { flow.collect { } } }` |
| ViewModel exposing a cold upstream | `stateIn(viewModelScope, WhileSubscribed(5_000), initial)` |
| ViewModel combining sources | `combine(a, b) { ... }.stateIn(...)`; one state out |
| Callback API to Flow | `callbackFlow { ...; awaitClose { unregister() } }` |

A bare `lifecycleScope.launch { flow.collect { } }` keeps collecting in the background (battery, wasted work, updates to a stopped UI). `launchWhenStarted` only suspends the collector and keeps the upstream running; it is deprecated (verify (unconfirmed) status in your lifecycle version).

`SharedFlow` is hot with a buffer policy; `StateFlow` is hot with exactly one latest value and `distinctUntilChanged` built in (setting an equal value emits nothing, so mutate with `update { it.copy(...) }` and a new instance). `conflate()` drops intermediate values for a slow collector.

## Cancellation and error traps

1. `try { suspendCall() } catch (e: Exception) { log(e) }` swallows `CancellationException`; the coroutine keeps running after cancel. Fix: `catch (e: CancellationException) { throw e }` first, or catch a narrower type. Same for `runCatching`.
2. `launch` inside a `try` does not catch the child's exception; the exception goes to the parent. Wrap the body of the launch, or use `CoroutineExceptionHandler` only on a root `launch`.
3. `async` exceptions surface at `await()`; if the `async` is in a `coroutineScope` the sibling jobs are cancelled first.
4. A `SupervisorJob` isolates siblings only for its direct children; `launch(SupervisorJob())` in a child scope breaks the parent link and the job is no longer cancelled with the parent.
5. Blocking calls (`Thread.sleep`, a blocking JDBC or file read) in a coroutine ignore cancellation; use `delay`, `ensureActive()` in long loops, or `withContext(IO)`.
6. `withTimeout` throws `TimeoutCancellationException`, a `CancellationException` subtype; use `withTimeoutOrNull` when a timeout is an expected outcome.
7. Never expose `suspend` functions that internally `launch` and return; callers cannot await them or see their errors.

## Lifecycle pitfalls and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| State lost on rotation | state in a field of an Activity or in `remember` | ViewModel or `rememberSaveable` |
| State lost after the app was in the background a while | process death; only ViewModel memory was used | `SavedStateHandle` or `rememberSaveable` for ids and drafts |
| Crash `TransactionTooLargeException` | big objects in `onSaveInstanceState` or in navigation arguments | save ids only; reload from the repository |
| Dialog or snackbar shows twice | event in `SharedFlow` replay, or event re-read after rotation | consumed-state pattern (architecture-state.md) |
| Fragment crashes with `IllegalStateException` after `onDestroyView` | collecting with `this` instead of `viewLifecycleOwner`, or using a binding after destroy | `viewLifecycleOwner`; set binding to null in `onDestroyView` |
| Memory grows after leaving screens | static or singleton holding Activity, View or lambda that captures one | see procedure below |
| Work repeats on every rotation | `LaunchedEffect(Unit)` with a side effect, or `init {}` repeated in a recreated ViewModel factory | hoist to ViewModel `init` once; guard with state |
| Crash on `startActivityForResult` return | deprecated API plus process death | Activity Result API contracts |

## Leak hunting procedure

1. Run the scanner: `context-leak-static` and `global-scope` findings first.
2. Search for `Handler(`, `Timer`, `registerReceiver`, `addListener`, `setOnClickListener` captured by long-lived objects, and `Thread {` inside Activities; each needs a mirror cleanup.
3. Add a debug-only leak detector dependency (`debugImplementation`; never in release) and rotate the suspect screen five times, then trigger a dump. Record which reference chain it reports.
4. Fix the root holder, not the symptom: replace the static with a parameter or an injected application-scoped dependency, or hold a `WeakReference` when a back-reference is unavoidable.
5. Re-run step 3 and the scanner. Report the chain that was fixed, or "not reproduced".
