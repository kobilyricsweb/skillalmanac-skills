---
name: ios-swift-practices
description: Guides an agent writing or reviewing native iOS code in Swift and SwiftUI. Use when the user asks to build, fix, refactor or review an iOS app, a SwiftUI view or a view model, asks why a view does not update, or asks what App Store review needs. Gives decision tables for state (@State, @Binding, @Observable, environment), Swift concurrency and MainActor rules, optionals, networking, persistence, privacy manifests, accessibility, tests and a release checklist, plus a script that scans .swift files for six anti-patterns and prints JSON. Do not use for Android, Flutter, React Native, macOS-only AppKit, server-side Swift or UIKit-only legacy work.
license: Apache-2.0
compatibility: The optional script needs Python 3.9 or newer, standard library only, no network. Building and testing iOS code needs Xcode on macOS; without it, state in the report that nothing was compiled.
metadata:
  author: Skill Almanac Editorial
  license: Apache-2.0
  author_model: claude-sonnet-5-5
  version: "0.1.0"
  network: none
---

# iOS Swift practices

Write SwiftUI code that matches the project's real deployment target, keep UI state, concurrency and I/O in their own layers, and check the result with the scanner. Most wrong output comes from using an API the target does not have, so step 1 is not optional.

## Workflow

```
- [ ] 1 Find deployment target and Swift mode
- [ ] 2 Pick the row in each table below that matches
- [ ] 3 Write or change the code
- [ ] 4 Run the scanner, fix, re-run
- [ ] 5 Report
```

1. **Target.** Read `IPHONEOS_DEPLOYMENT_TARGET` and `SWIFT_VERSION` in `*.xcodeproj/project.pbxproj` (or `platforms:` and `swift-tools-version` in `Package.swift`; or the `.xcconfig`). Record them. Also record whether strict concurrency is `complete` or the target uses Swift 6 language mode. If you cannot read them, say so and write to the lowest row of each table.
2. **Tables.** Rows marked "iOS 17+" apply only when the target is 17 or higher. Items marked "verify (unconfirmed)" were not checked against current Apple documentation in this session: check them in the Xcode version in use before relying on them.
3. **Write.** Follow the tables and the layering rule below.
4. **Scan.** `python scripts/swift_scan.py <dir-or-files>`; see Scanner.
5. **Report** in the fixed shape at the end.

## Layering rule

`View` -> `@MainActor` model (`@Observable`, or `ObservableObject` below iOS 17) -> service protocol with `async throws` methods -> `URLSession` / store. A view never calls `URLSession`, never decodes JSON and never touches the database. Wire types (Codable DTOs) are mapped to domain structs at the service boundary so a server rename does not reach the views.

## State decision table

| Situation | Use | Notes |
|---|---|---|
| Value type, private to one view (toggle, text field, sheet flag) | `@State private var` | Always `private`; owned by the view |
| Child must read and write the parent's value | `@Binding` | Pass `$value`; do not copy into a child `@State` |
| Child only reads | plain `let` | No wrapper |
| View owns a model class, iOS 17+ | `@State private var model = Model()` with `@Observable class Model` | `@State` is correct here and only here |
| View owns a model class, below iOS 17 | `@StateObject` with `ObservableObject` + `@Published` | `@State` on such a class is a bug |
| Model passed in, `@Observable` | plain `let model: Model`; `@Bindable var model` if you need `$model.field` | iOS 17+ |
| Model passed in, `ObservableObject` | `@ObservedObject` | Never create it inside the child |
| Shared app-wide model | `.environment(model)` + `@Environment(Model.self)` (iOS 17+); `@EnvironmentObject` below | Inject in the `App`/root, not deep in the tree |
| One small preference | `@AppStorage` | Not for secrets or large data |
| Per-scene UI restore (selected tab) | `@SceneStorage` | |
| Persistent store query, iOS 17+ | SwiftData `@Query` | verify (unconfirmed): threading rules in the persistence section |

Reference types in `@State` without `@Observable` do not refresh the view when they change. `@Observable` classes that drive UI should be `@MainActor`. In `@Observable` models mark non-UI cached values `@ObservationIgnored`.

## Concurrency rules

1. Annotate UI-facing types and functions `@MainActor`; do not hop with `DispatchQueue.main.async` inside async code. If you must update from a non-isolated context, `await` a `@MainActor` function.
2. `.task { }` and `.task(id:)` are cancelled when the view goes away; use them rather than `onAppear { Task { } }`.
3. `Task { }` inherits the actor and priority of the caller; `Task.detached` does not. Use detached only for work that must not run on the caller's actor.
4. Cancellation is cooperative: loops over `await` calls need `try Task.checkCancellation()`, and `CancellationError` or `URLError.cancelled` must not show an error alert.
5. An actor method can be interleaved at every `await`: re-read actor state after each `await` instead of assuming it is unchanged. This is the most common actor bug.
6. Shared mutable state goes in an `actor` or a `@MainActor` type. A class crossing isolation must be `Sendable` (final, immutable stored properties) or isolated. Do not silence diagnostics with `@unchecked Sendable` without a comment saying what lock protects it.
7. `withCheckedThrowingContinuation` must resume exactly once on every path.
8. Never block with `DispatchSemaphore.wait()` or `Thread.sleep` on an async path; use `try await Task.sleep(for:)`.
9. Migration path to Swift 6 mode: turn strict concurrency to `complete` in Swift 5 mode first and fix warnings; then switch the language mode. Xcode's newer "default MainActor isolation" setting: verify (unconfirmed).

## Optionals and errors

- Prefer `guard let` early exit; `if let x` shorthand needs Swift 5.7.
- `!` and `as!` only for a literal that cannot fail (`URL(string: "https://example.com")!` with a comment) or a programmer-error invariant; prefer `preconditionFailure("reason")`. `try!` is not acceptable in app code.
- `try?` only when the reason for failure does not matter and nothing is lost by failing; never on a save, a write or a purchase.
- One `enum AppError: LocalizedError` per layer, mapped at the boundary. Show user-readable text, never `error.localizedDescription` of a raw decoding error.
- Typed throws (`throws(MyError)`): verify (unconfirmed) for the Swift version in use.

## Networking and persistence

- `URLSession.data(for:)` does not throw for HTTP 4xx or 5xx. Cast to `HTTPURLResponse` and require `200..<300` yourself.
- `JSONDecoder.DateDecodingStrategy.iso8601` rejects fractional seconds; use a custom strategy with a formatter that allows them when the server sends `.123Z`.
- Default request timeout is 60 s; set an explicit shorter `timeoutInterval` for user-initiated requests. Retry only idempotent requests, with backoff.
- App Transport Security requires HTTPS; an exception in `Info.plist` needs a written reason for review.
- Store tokens and secrets in the Keychain, never in `UserDefaults`, `@AppStorage` or files. Money is `Decimal`, never `Double`.
- Files: Application Support for data to keep (backed up), Caches for rebuildable data (the system may delete it), tmp for scratch. Mark re-downloadable files `isExcludedFromBackup`.
- SwiftData and Core Data contexts are not safe to share across threads; model objects are not `Sendable`. Pass identifiers (`PersistentIdentifier`, `NSManagedObjectID`) across isolation boundaries and reload. Background writes via `@ModelActor`: verify (unconfirmed).

## Navigation and view structure

- `NavigationStack` with a typed path and `.navigationDestination(for:)`; `NavigationView` is deprecated. Put one stack at the root, not inside each pushed view.
- `.sheet(item:)` when the content depends on a value; `.sheet(isPresented:)` for fixed content.
- `ForEach` needs a stable `Identifiable` id; `id: \.self` on non-unique values corrupts updates.
- Keep `body` cheap: no formatter creation, sorting or filtering inside it. Split large bodies into separate `struct` views (own inputs, own invalidation); computed `var` fragments do not give that boundary. The scanner warns above 60 non-blank body lines.
- Use `#Preview` with injected fake services so previews never hit the network.

## Privacy, permissions, accessibility, tests, release

Read the section you need, not the whole file:

- Privacy manifest (`PrivacyInfo.xcprivacy`), required-reason API categories, usage-description keys, Sign in with Apple and account deletion rules, release checklist: [references/privacy-and-release.md](references/privacy-and-release.md).
- Accessibility rules and thresholds, XCTest and Swift Testing rules, test doubles: [references/accessibility-and-testing.md](references/accessibility-and-testing.md).
- URLs for every claim and what is unconfirmed: [references/sources.md](references/sources.md).

Minimum bar even if you read nothing else: every control has an accessibility label and a 44 x 44 pt tap target; fonts are semantic (`.body`) so Dynamic Type works; any API on the required-reason list has a reason in the privacy manifest; every permission has a purpose string in `Info.plist` and is requested at the moment of use, not at launch.

## Scanner

`python scripts/swift_scan.py PATH [PATH ...] [--max-body-lines N] [--force-density X] [--include-tests] [--max-per-rule N]` -- run it, do not edit it to make a check pass. Reads only; stdout is one strict JSON object.

| Rule id | Severity | Fires on |
|---|---|---|
| `force-unwrap-density` | warn | file with at least 3 `!` / `as!` and 1.0 or more per 100 code lines |
| `try-bang` | high | every `try!` |
| `main-queue-in-async` | warn | `DispatchQueue.main.async` inside an `async` func, `Task`, `.task` or `.refreshable` body |
| `print-in-app-code` | warn | `print(` / `debugPrint(` outside tests and outside `#if DEBUG` |
| `giant-view-body` | warn, high above 2x | `var body: some View` over 60 non-blank code lines |
| `state-reference-type` | high (class found in scan), warn (guessed from name) | `@State` holding an `ObservableObject` or plain class; `@Observable` is accepted |

Output keys: `tool`, `version`, `files_scanned`, `test_files_skipped_for_rules`, `thresholds`, `total_findings`, `counts_by_rule`, `omitted_by_rule`, `findings` (each: `file`, `line`, `rule`, `severity`, `message`, `snippet`, plus rule extras), `per_file` (`file`, `code_lines`, `is_test_file`, `force_unwraps`, `force_unwraps_per_100_lines`), `limits`. Exit 0 no findings, 1 findings, 2 usage error (JSON with an `error` key).

Fix every `high`. For each `warn`, fix or write one line in the report saying why it stays. Re-run until the findings are fixed or explained. If Python is missing, search by hand for `try!`, `DispatchQueue.main.async` in `async` bodies, `print(`, `@State` on classes, and bodies longer than 60 lines.

## Report format

```
Target: <iOS version, Swift version/mode, or "not found">
Changed: <files and what>
Scanner: <total findings before -> after; warns kept and why>
Version-dependent choices: <rows used that depend on the target; items marked verify (unconfirmed) that were used>
Not checked: <e.g. not compiled, tests not run, no device, privacy manifest not validated by Xcode>
```

## Limits

- The scanner is lexical: no types, no build graph. It strips comments and strings but not regex literals; it misses `!` through type aliases, and cannot see an actor context set outside the file or a closure that escapes an async function.
- `state-reference-type` only knows classes declared in the scanned files; classes from packages are matched by name suffix (ViewModel, Manager, Service, Store, Controller, Coordinator, Client, Repository) at warn level.
- Test files are detected by path name or `import XCTest`/`import Testing`; `#Preview` blocks are scanned like app code.
- Thresholds (3 force unwraps, 1.0 per 100 lines, 60 body lines) are working values, not measured optima.
- Command-line tools may legitimately `print`; scan them with the `print-in-app-code` finding in mind.
- Nothing here replaces compiling, running tests or Apple's own validation at upload.
- Items marked "verify (unconfirmed)" and all dates and OS numbers can change with new Xcode and SDK releases.
