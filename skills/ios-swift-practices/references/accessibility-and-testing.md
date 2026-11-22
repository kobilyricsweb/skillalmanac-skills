## Contents

1. Accessibility rules
2. Accessibility checks by hand
3. Choosing XCTest or Swift Testing
4. Test rules and doubles

Items marked "verify (unconfirmed)" were not re-read against Apple documentation in this session.

## 1. Accessibility rules

| Rule | How |
|---|---|
| Tap targets at least 44 x 44 pt | `.frame(minWidth: 44, minHeight: 44)` and `.contentShape(Rectangle())` on small icons |
| Dynamic Type everywhere | semantic fonts (`.font(.body)`, `.headline`); `@ScaledMetric` for sizes that must grow with text; no fixed `.frame(height:)` on text containers |
| Layout survives the largest accessibility sizes | switch stacks with `ViewThatFits` or `@Environment(\.dynamicTypeSize)` and `dynamicTypeSize.isAccessibilitySize` |
| Every non-text control has a label | `.accessibilityLabel("Close")` on icon-only buttons; `Label("Add", systemImage: "plus")` is better than an `Image` alone |
| Decorative images are hidden | `Image(decorative: "x")` or `.accessibilityHidden(true)` |
| Group what reads as one thing | `.accessibilityElement(children: .combine)` on a row; `.ignore` plus an explicit label when the combined text is poor |
| State is not carried by colour alone | add a symbol or text; read `@Environment(\.accessibilityDifferentiateWithoutColor)` |
| Motion respects Reduce Motion | read `@Environment(\.accessibilityReduceMotion)` and swap springs and parallax for fades |
| Text contrast at least 4.5:1 (3:1 for large text) | WCAG thresholds; check custom colours in light and dark and with Increase Contrast |
| Use real controls | `Button`, `Toggle`, `NavigationLink`; `onTapGesture` on a `Text` or `Image` has no button trait, so add `.accessibilityAddTraits(.isButton)` if you must |
| Values, not duplicated labels | `.accessibilityValue("3 of 5")` for sliders and steppers; `.accessibilityHint` only for non-obvious results |
| Custom actions replace swipe-only gestures | `.accessibilityAction(named:)` |

## 2. Accessibility checks by hand

1. Run the main flow with VoiceOver on a device or simulator; every element is reachable and read in a sensible order.
2. Set Settings > Accessibility > Larger Text to the largest size; nothing is clipped or overlaps.
3. Turn on Bold Text, Increase Contrast, Reduce Motion; check each screen once.
4. Xcode's Accessibility Inspector audit gives a list; it cannot judge whether a label is meaningful, so read the labels.
5. Add `.accessibilityIdentifier("login.submit")` for UI tests; identifiers are not read aloud and must not replace labels.

## 3. Choosing XCTest or Swift Testing

| Need | Use |
|---|---|
| New unit tests, parameterised cases, async tests | Swift Testing (`import Testing`, `@Test`, `#expect`, `#require`, `@Suite`, `@Test(arguments:)`): verify (unconfirmed) minimum Xcode (the Swift 6 toolchain era) |
| UI tests (`XCUIApplication`) | XCTest only |
| Performance measurement (`measure { }`) | XCTest only |
| Existing XCTest suite | keep; both frameworks can live in one test target; do not rewrite a working suite for style |
| Objective-C callers | XCTest |

## 4. Test rules and doubles

- Test through the service protocol: a fake that returns canned values and records calls beats a mock library for most cases.
- Stub `URLSession` by registering a `URLProtocol` subclass on an ephemeral `URLSessionConfiguration`; this exercises the real request building and decoding.
- Never call the real network or the real Keychain from a unit test; use an in-memory store and a fake keychain wrapper.
- Time and randomness are injected (`Date` provider closure, or a `Clock`), never read inside the unit under test.
- `@MainActor` model tests are marked `@MainActor`. In async XCTest code use `await fulfillment(of: [expectation], timeout: 2)`; the older `wait(for:timeout:)` can deadlock the main actor.
- Async code is tested by awaiting it. A `Task.sleep` in a test is a flaky test; make the code under test return when finished, or inject a controllable clock.
- One behaviour per test; name tests as sentences (`loadFailureShowsRetry`).
- SwiftData tests use an in-memory configuration (`ModelConfiguration(isStoredInMemoryOnly: true)`): verify (unconfirmed) API spelling for the iOS version in use.
- Coverage is a diagnostic, not a target; do not add assertion-free tests to move a number.
