## Contents

- Sources to confirm against
- Claims tagged verify (unconfirmed)

## Sources to confirm against

None of these pages was fetched when this skill was written; they are the places to confirm the tagged claims, with what each one settles.

| Topic | URL | Settles |
|---|---|---|
| App architecture guide | https://developer.android.com/topic/architecture | UI, domain and data layer roles; unidirectional data flow; one-off events guidance |
| Compose state and hoisting | https://developer.android.com/develop/ui/compose/state | state hoisting rule, `rememberSaveable`, state holders |
| Compose performance | https://developer.android.com/develop/ui/compose/performance | stability, strong skipping, lazy list keys, deferring reads, compiler reports |
| Coroutines best practices | https://developer.android.com/kotlin/coroutines/coroutines-best-practices | injected dispatchers, main-safe suspend functions, scopes that outlive the screen |
| Flow on Android and lifecycle collection | https://developer.android.com/kotlin/flow/stateflow-and-sharedflow | `StateFlow`, `SharedFlow`, `stateIn`, `WhileSubscribed` |
| Runtime permissions workflow | https://developer.android.com/training/permissions/requesting | request flow, rationale, denial behaviour, partial media access |
| Compose accessibility | https://developer.android.com/develop/ui/compose/accessibility | semantics, touch target, merging, headings, live regions |
| Testing fundamentals | https://developer.android.com/training/testing/fundamentals | small, medium, large sizes and the 70/20/10 guidance |
| Target API level requirements | https://developer.android.com/google/play/requirements/target-sdk | current deadline for targetSdk on new apps and updates |
| Android vitals | https://developer.android.com/topic/performance/vitals | bad-behavior thresholds for crashes and ANRs, startup |
| Shrink, obfuscate and optimize | https://developer.android.com/build/shrink-code | R8 settings, keep rules, mapping files |

## Claims tagged verify (unconfirmed)

Written from memory with no network. Confirm each before presenting it as fact.

1. `collectAsStateWithLifecycle` minimum lifecycle version (stated as 2.6).
2. Strong skipping mode default and the Kotlin version where it became the default (stated as Kotlin 2.0.20).
3. `launchWhenStarted` deprecation status in the project's lifecycle version.
4. Current official wording preferring state over `Channel` or `SharedFlow` for one-off events.
5. Exact option names for Compose compiler reports and metrics.
6. ANR limits (about 5 s for input dispatch) and Play vitals bad-behavior thresholds.
7. System behaviour after repeated permission denials; API levels for `POST_NOTIFICATIONS` (33), partial media access (34), nearby-devices permissions.
8. Predictive back opt-in flag and the target SDK where it became default.
9. Status of Jetpack security-crypto libraries; data extraction rule attribute names.
10. Current Play target-API deadline, 16 KB page-size requirement, data-safety and account-deletion policy.
11. Current text-field API behaviour (`TextFieldState` versus `String` value) and caret behaviour.
12. Foreground service type requirements.
13. Any quoted percentage for Baseline Profile gains.

Numbers in this skill that are working values, not documented limits: 30 rows before a scrolling Column is a smell; 50 KB saved-state target; 4 and 8 `!!` thresholds; 4-line `BuildConfig.DEBUG` guard window; the 1%, 5%, 20%, 50%, 100% rollout steps.
