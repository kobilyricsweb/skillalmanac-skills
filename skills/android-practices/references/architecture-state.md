## Contents

- Layer contract
- UiState and the screen split
- Hoisting decisions
- One-off events
- Recomposition diagnosis procedure
- Review smells

## Layer contract

| Layer | Contains | May import | Must not import |
|---|---|---|---|
| UI | composables, `ViewModel`, `UiState`, UI mappers | domain, data interfaces, Compose, lifecycle | Room entities, Retrofit DTOs, `SharedPreferences` |
| Domain (optional) | use cases (`operator fun invoke`), plain models | Kotlin, coroutines | `android.*`, Compose |
| Data | repository implementations, DAOs, API services, DTOs, mappers | Room, network library, `android.content` (application context only) | composables, `ViewModel`, `android.view` |

Rules that catch most real defects:

1. Repositories expose domain or UI-ready models, never DTOs or database entities. Map at the boundary, once.
2. The repository is the single source of truth. Reads come from the local store as a `Flow`; network results are written to it. The UI never merges a network result and a cached result itself.
3. A repository function that returns data is `suspend` or returns `Flow`; it never takes a callback and never returns a `LiveData` in new code.
4. Module or package by feature first (`feature/profile/{ui,domain,data}`), by layer second. A change to one feature touches one folder.
5. Dependency injection is constructor injection. A service-locator call inside a composable or a ViewModel body hides dependencies; tests then need the global container.

## UiState and the screen split

```kotlin
sealed interface ProfileUiState {
    data object Loading : ProfileUiState
    data class Content(val name: String, val saving: Boolean = false) : ProfileUiState
    data class Error(val messageRes: Int) : ProfileUiState
}

@Composable
fun ProfileRoute(viewModel: ProfileViewModel = hiltViewModel()) {   // only place that knows the ViewModel
    val state by viewModel.state.collectAsStateWithLifecycle()
    ProfileScreen(state = state, onSave = viewModel::save)
}

@Composable
fun ProfileScreen(state: ProfileUiState, onSave: () -> Unit) { /* stateless, previewable, testable */ }
```

The Route/Screen split gives previews, screenshot tests and UI tests a composable with no ViewModel. The DI call shown is one option (`hiltViewModel`, `koinViewModel`, `viewModel()` with a factory); keep whatever the project already uses. Use string resource ids or a small text wrapper in state for messages, never a hard-coded sentence built in the ViewModel (it would ignore locale changes).

## Hoisting decisions

Hoist state to the lowest composable that needs to read it, and at least to the highest composable that writes it. Practical test: if a parent needs the value to enable a button, or a sibling displays it, hoist; if only the widget itself cares (an expanded flag), keep it inside with `rememberSaveable` and do not expose it.

- A hoisted value pairs with its change callback: `value: T, onValueChange: (T) -> Unit`. The composable never mutates a passed-in `MutableState`.
- A text field with live validation: keep the raw text in the ViewModel only when other logic needs it each keystroke; otherwise keep the `TextFieldState` or `rememberSaveable` string in the screen and pass the final value on submit. Routing every keystroke through a ViewModel with `Dispatchers.IO` work in between is a known source of caret jumps (verify (unconfirmed) for the current text-field API).
- Do not pass `ViewModel` further than the Route composable; do not pass `NavController` below the navigation host (pass lambdas such as `onOpenDetail: (Long) -> Unit`).

## One-off events

Model "show snackbar" or "navigate" as data the screen has consumed:

```kotlin
data class Content(..., val pendingNav: Route? = null)
// ViewModel: _state.update { it.copy(pendingNav = Route.Done) }
// UI: LaunchedEffect(state.pendingNav) { state.pendingNav?.let { nav(it); viewModel.navConsumed() } }
```

Why not a `Channel` or `SharedFlow`: with no collector (rotation, app in background) a `SharedFlow` with no replay drops the event, and with replay it fires twice. State survives both. Official guidance has moved this way across releases (verify (unconfirmed) current wording). Navigation inside a ViewModel is acceptable only when it calls an injected navigator interface, not a `NavController` or Activity.

## Recomposition diagnosis procedure

1. Reproduce in a release-like build (R8 on, `debuggable` false, Baseline Profile if present) on a mid-range device; debug builds mislead.
2. Layout Inspector's recomposition counts: a composable that recomposes on every frame while nothing visible changes is the suspect.
3. Search for a state read in the wrong phase: a scroll offset or animated value read in the composable body instead of a `graphicsLayer {}` or `offset {}` lambda.
4. Check list parameters: a `List<T>` argument is treated as unstable unless strong skipping is on (verify (unconfirmed)); a `ImmutableList` or a wrapper class annotated `@Immutable` fixes it.
5. Check lambdas created in a loop: with strong skipping lambdas are remembered automatically; without it, hoist or `remember` them.
6. Generate Compose compiler reports (a compiler plugin option `reportsDestination` and `metricsDestination`, verify (unconfirmed) the exact option names) and read `*-composables.txt` for `restartable` without `skippable`.
7. Only then add `@Stable` or `@Immutable`. Annotating a class that actually mutates is a correctness bug: the UI stops updating.

## Review smells

- `viewModel.someFlow.collectAsState()` inside a deep child.
- `LaunchedEffect(Unit)` that reads a changing parameter (captured stale value; add the key or use `rememberUpdatedState`).
- `mutableStateOf` created without `remember` (reset on every recomposition).
- A `ViewModel` constructor taking `Context` or `Activity`.
- A `UiState` field of type `MutableStateFlow`, `Bitmap`, `Drawable` or `Uri` object that is not parcelable when the state is saved.
- `Thread.sleep` or blocking IO in `init {}` of a ViewModel.
