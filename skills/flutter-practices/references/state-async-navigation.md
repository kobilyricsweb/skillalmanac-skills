# State, async and navigation

Read for: choosing or reviewing state management, Future and Stream bugs, error handling, routing. Claims tagged "verify (unconfirmed)" are from memory; see sources.md.

## Choosing state management: scoring questions

Ask these in order and stop at the first row that fits.

| Question | Yes means |
|---|---|
| Does only one widget (and its children) read it, and does it die with that widget? | `setState` or `ValueNotifier` |
| Do two or three widgets in one subtree read it, with simple synchronous updates? | `ChangeNotifier` exposed through an inherited provider |
| Does it come from a server or disk, with loading, error, refresh, cache or dependent queries? | A reactive provider or query layer that owns loading, error and cache states |
| Do you need an explicit event log, replay, or strict separation between UI events and business transitions, with several people on the code? | Event-to-state machine (Bloc style) |
| Is it needed app-wide (auth, locale, theme)? | A single root-level notifier, created once, overridable in tests |

Decision costs to state in a recommendation: boilerplate per feature, ability to test without a widget tree, how disposal works, how rebuilds are scoped, and how much the team already knows. "Popular" is not a criterion. Do not migrate an app that works; propose a migration only for a named pain (untestable logic, rebuild storms, duplicated server data).

## State class rules

- Immutable. Change by creating a new value; `copyWith` or a sealed hierarchy (Dart 3) with `loading`, `data`, `error` cases.
- One owner per fact. If two stores hold the same server entity, delete one.
- UI reads state, sends events. Business logic never imports `package:flutter/material.dart` or holds a `BuildContext`.
- Navigation and snackbars triggered by state are one-shot effects: model them as events consumed once, not as a boolean that stays true after rotation.

## Futures and Streams: defects to look for

| Defect | Symptom | Fix |
|---|---|---|
| Future dropped | Unhandled exception, code after it runs too early | `await`, return it, or `unawaited(...)` plus internal try/catch |
| `FutureBuilder(future: fetch())` in build | Request repeats on every rebuild | Create the future once in `initState` or a provider |
| `setState` after dispose | "setState called after dispose" error | `if (!mounted) return;` after each await, and cancel timers and subscriptions in `dispose` |
| `BuildContext` used after `await` | Wrong or deactivated element | `if (!context.mounted) return;` (verify (unconfirmed) minimum version), or read navigator and messenger before the await |
| Stream listened to twice | "Stream has already been listened to" | Use a broadcast stream deliberately, or one subscription owner |
| Subscription never cancelled | Memory growth, callbacks after the screen closed | Store it; cancel in `dispose` |
| Parallel awaits written in sequence | Slow screens | `Future.wait([...])` when calls are independent |
| Catch-all `catch (e) {}` | Failures vanish | Catch a specific type, log, rethrow or convert to a state |

## Error handling layers

1. Repository: converts transport and parsing exceptions into a small set of domain failures (network, unauthorised, not found, unexpected). Expected failures become values; do not use exceptions for control flow.
2. State layer: maps a failure to an error state with a user-facing message key and a retry event.
3. UI: shows the state; never shows a raw exception string.
4. Global: in `main`, set `FlutterError.onError` (framework errors) and `PlatformDispatcher.instance.onError` (uncaught async errors) to your crash reporter and return true from the latter. Older projects use `runZonedGuarded`; do not mix both without checking for double reports (verify (unconfirmed) for the current recommendation).

## Navigation

| Need | Choice |
|---|---|
| Two to five screens, no deep links, no web | Imperative `Navigator.push` / `pop`, named routes optional |
| Deep links, web URLs, auth redirects, nested tabs | A declarative router package (path parameters, redirect callback, shell routes for tabs) |
| Return a result from a screen | `await Navigator.push<T>` and `pop(result)`, with a mounted check after |

Rules: route parameters are ids and small primitives; fetch the model on the destination screen. One redirect function decides auth state. Back-button handling goes through the router, not a raw `WillPopScope` (replaced by `PopScope` in newer releases; verify (unconfirmed)). Test deep links on a cold start and on a running app; they take different paths on each platform.

## Null safety habits

Prefer in this order: make the value non-nullable; early return after a null check; `??` with a meaningful default; pattern match (`if (x case final v?)`); local `final` copy then check. A `!` needs a nearby comment or an assertion that proves the value is set, otherwise treat it as a defect. `late` fields that are read before assignment throw at runtime; prefer a constructor parameter.
