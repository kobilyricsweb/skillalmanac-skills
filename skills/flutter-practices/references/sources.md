# Sources and unconfirmed claims

The URLs below were NOT fetched while writing this skill (no network was available). They are where to confirm each item. Everything in the references is written in the author's own words from memory.

## Where to confirm

| Topic | URL | What to confirm |
|---|---|---|
| Performance best practices | https://docs.flutter.dev/perf/best-practices | Build method guidance, avoiding saveLayer, list construction |
| Profiling and DevTools | https://docs.flutter.dev/perf/ui-performance | Profile mode, UI versus raster thread, frame budget |
| Renderer (Impeller) | https://docs.flutter.dev/perf/impeller | Which platforms default to it in your release |
| State management overview | https://docs.flutter.dev/data-and-backend/state-mgmt/options | Official list of approaches and their scope |
| Navigation and routing | https://docs.flutter.dev/ui/navigation | Navigator versus router, deep linking setup per platform |
| Accessibility | https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility | Semantics, minimum tap target, contrast, text scale |
| Theming | https://docs.flutter.dev/cookbook/design/themes | ThemeData, ColorScheme, Material 3 default |
| Platform channels | https://docs.flutter.dev/platform-integration/platform-channels | Codec types, threading, background isolates |
| Testing overview | https://docs.flutter.dev/testing/overview | Unit, widget, integration definitions and commands |
| Build and release, Android | https://docs.flutter.dev/deployment/android | Signing, appbundle, obfuscation |
| Build and release, iOS | https://docs.flutter.dev/deployment/ios | ipa build, signing, store upload |
| Lint set | https://dart.dev/tools/linter-rules | prefer_const_constructors, unawaited_futures, use_build_context_synchronously |
| Dart null safety and patterns | https://dart.dev/language/patterns | Pattern matching, promotion rules |
| Store requirements (Android) | https://developer.android.com/google/play/requirements/target-sdk | Target API level for new apps and updates |
| Store requirements (iOS) | https://developer.apple.com/documentation/bundleresources/privacy-manifest-files | Privacy manifest and required-reason APIs |

## Claims tagged "verify (unconfirmed)"

- Minimum Flutter version where `BuildContext.mounted` is available.
- Release in which Material 3 became the default (`useMaterial3`).
- `withOpacity` deprecation and its replacement; `MediaQuery.textScalerOf` and the `...Of` accessors.
- Impeller default per platform and shader-compilation jank behaviour.
- Recommended global error handling split (`FlutterError.onError`, `PlatformDispatcher.onError` versus `runZonedGuarded`).
- `PopScope` replacing `WillPopScope`.
- Null-check promotion of private final fields in recent Dart.
- Background isolate channel setup and its minimum version; FFI tooling.
- `debugPrint` behaviour in release builds.
- `integration_test` command shape.
- Every store requirement: target API level, Xcode and SDK minimums, privacy manifest details.
- Test-pyramid shares, build-length and null-assertion thresholds: working values by the author, not measured.
