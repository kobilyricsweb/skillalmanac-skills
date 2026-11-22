## Contents

1. How to read this file
2. Sources by topic
3. Unconfirmed items

## 1. How to read this file

The URLs below were recorded from memory of Apple's and Swift.org's documentation structure; they were not fetched in the session that wrote this skill, so a page may have moved. Facts in the skill are restated in the author's own words. When a URL fails, search the same title on developer.apple.com.

## 2. Sources by topic

| Topic | Page to open |
|---|---|
| State and model data in SwiftUI, Observation | https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app |
| Moving from ObservableObject to the Observable macro | https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro |
| Swift concurrency, actors, Sendable | https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/ |
| Swift 6 language mode migration | https://www.swift.org/migration/documentation/migrationguide/ |
| URLSession | https://developer.apple.com/documentation/foundation/urlsession |
| App Transport Security | https://developer.apple.com/documentation/security/preventing-insecure-network-connections |
| Keychain | https://developer.apple.com/documentation/security/keychain-services |
| SwiftData | https://developer.apple.com/documentation/swiftdata |
| Privacy manifest files | https://developer.apple.com/documentation/bundleresources/privacy-manifest-files |
| Required-reason API declarations | https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api |
| Purpose strings | https://developer.apple.com/documentation/uikit/protecting-the-user-s-privacy |
| App Review Guidelines (4.8, 5.1.1) | https://developer.apple.com/app-store/review/guidelines/ |
| Accessibility in SwiftUI | https://developer.apple.com/documentation/swiftui/accessibility |
| Human Interface Guidelines, accessibility and layout (44 pt targets) | https://developer.apple.com/design/human-interface-guidelines/accessibility |
| WCAG contrast thresholds (4.5:1, 3:1) | https://www.w3.org/TR/WCAG22/#contrast-minimum |
| Swift Testing | https://developer.apple.com/documentation/testing |
| XCTest | https://developer.apple.com/documentation/xctest |

## 3. Unconfirmed items

These statements in the skill were not verified against a current source and are marked "verify (unconfirmed)" where they appear:

- Minimum OS for Observation, `@Bindable`, `@Environment(Model.self)`, SwiftData (stated as iOS 17).
- Typed throws availability; default MainActor isolation setting; `@ModelActor` behaviour.
- Enforcement dates and the SDK list for privacy manifests; the exact reason codes in the example column.
- Calendar permission key names introduced for iOS 17.
- Guideline 4.8 wording; export-compliance exemption for plain HTTPS; screenshot sizes; the Xcode version App Store Connect requires.
- Swift Testing minimum Xcode; the in-memory SwiftData configuration spelling.
- `DispatchQueue.main.async` equivalence advice (use `@MainActor`) is standard guidance, but whether a `View.body` is itself main-actor isolated depends on the SDK version.
