# Listing page content: ios-swift-practices

**One line:** Makes an agent write current SwiftUI and check Swift files for six known anti-patterns.

## What it does

The skill tells the agent to read the project's deployment target and Swift mode first, then pick the matching row from a state decision table, a set of concurrency and MainActor rules, optional and error rules, and networking and persistence rules. Reference files cover the privacy manifest, permission purpose strings, accessibility thresholds, test-framework choice and a release checklist. A scanner script reads `.swift` files and prints one strict JSON object listing `try!`, `DispatchQueue.main.async` inside async code, `print(` outside tests, force-unwrap density, oversized `body` properties and `@State` holding classes that are not `@Observable`. Claims that depend on the Xcode or iOS version are marked "verify (unconfirmed)".

## Capabilities

- `scripts/swift_scan.py`: JSON findings with file, line, rule, severity and snippet; per-file force-unwrap density; exit code 1 when anything is found
- State, concurrency, optionals, networking, persistence and navigation rules in one page
- Privacy manifest keys, five required-reason categories, purpose-string keys, release checklist
- Accessibility rules with numeric thresholds and a hand-check procedure
- A fixed report that includes what was not compiled or tested

## When to use

You are building, refactoring or reviewing a native iOS app in Swift and SwiftUI; a view does not update; you ask what to put in a privacy manifest or what App Review will look at.

## When not to use

Android, Flutter, React Native, macOS-only AppKit, server-side Swift, UIKit-only legacy code, App Store marketing copy. It is not a compiler: it does not replace building in Xcode.

## Requirements

Python 3.9 or newer, standard library only, for the scanner. No network. Without Python the agent follows the manual search list in SKILL.md. Building and testing needs Xcode on macOS.

## Install

To be generated at publication: one pinned command per tool. The package installs to `.agents/skills/` and `.claude/skills/`.

## Examples

No with-skill agent run exists yet, so there is no saved model output. What exists is the scanner on the saved fixtures:

1. `python scripts/swift_scan.py evals/fixtures/Bad.swift`: 8 findings, exit code 1: `state-reference-type` at lines 18 and 19 (high) and 22 (warn), `force-unwrap-density` at line 29 (3 force operations in 41 code lines, 7.32 per 100), `try-bang` at 29, `print-in-app-code` at 31, `main-queue-in-async` at 32 and 36. The `print` inside `#if DEBUG`, the `DispatchQueue.main.async` in a non-async function, and the `!` and `try!` inside a string and a comment are not reported.
2. `python scripts/swift_scan.py evals/fixtures/Good.swift`: 0 findings, exit code 0 (`@Observable` model under `@State`, `Logger`, `.task`).

## Limits

- Lexical scan: no types or build graph; regex literals are not stripped; actor context outside the file is invisible.
- Classes from other packages are matched only by name suffix, at warn level.
- Thresholds (3 force unwraps, 1.0 per 100 lines, 60 body lines) are working values.
- Items marked "verify (unconfirmed)" were not checked against current Apple documentation.

## Evidence

See `VERIFICATION.md`. In short: static lint 0 FAIL / 0 WARN and 9 script fixture cases pass. Not tested: any with/without efficacy comparison, trigger behaviour in any tool, native discovery, cross-tool install, a real Xcode project, human review.

## Difference from neighbouring skills

`react-native-practices` and `flutter-practices` cover other stacks; `android-practices` (same wave) covers Kotlin. This skill is native iOS only and ships a Swift-specific scanner. `accessibility-audit` (batch_01) audits web pages; the accessibility reference here is limited to SwiftUI.

## Demo script (60 to 90 seconds)

To be recorded from a real run once one exists. Planned beats:

1. A project with deployment target 16: the agent reads the target and says `@Observable` is not available.
2. It writes the view, view model and service using `@StateObject` and a status-code check.
3. It runs `swift_scan.py`; findings appear as JSON; the agent fixes the `high` ones and re-runs to zero.
4. The report lists what was not compiled.

## FAQ seeds

- Does it need network? No.
- Does it build my app? No; it reads source text only.
- Does it work on UIKit code? The scanner reads any `.swift`; the tables are SwiftUI-oriented.
- How is it different from react-native-practices? It targets native Swift and checks Swift files.
- Why are some lines marked "verify (unconfirmed)"? They depend on the Xcode or iOS version and were not re-read against Apple's pages when written.
- How do I uninstall it? Delete the folder from `.agents/skills/` or `.claude/skills/`.

## Changelog

0.1.0, 2026-11-21: first draft; static lint and script fixtures only.

## License and authorship

Apache-2.0, copyright 2026 Global Media Holdings (skillalmanac.com). Drafted by claude-sonnet-5-5; accountable publisher Global Media Holdings. No human review has taken place yet.
