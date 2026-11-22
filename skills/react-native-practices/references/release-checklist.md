## Contents
- Before the build
- Build and versioning
- Store submission
- After release
- Over-the-air updates

# Release checklist

Tag key: [Expo] applies to Expo managed or prebuild projects using EAS; [bare] to plain React Native. Anything marked verify (unconfirmed) must be checked against the store or tool page on the day of release because requirements change often.

## Before the build

- [ ] Run `python scripts/rn_scan.py src app` (adjust the folders) and resolve every warn: no console.log left, no invalid platform literals.
- [ ] TypeScript passes with no errors and the linter passes.
- [ ] Test a release-mode build (not a development build, not Expo Go) on one real iPhone and one mid-range Android device. Startup time, scrolling and permissions behave differently in release.
- [ ] Every permission used has a purpose string (iOS) and an entry in the Android manifest or config; remove permissions no longer used.
- [ ] Production API base URL and keys come from build-time config for the right profile; no staging URL in the production profile. Never ship server secrets in the bundle; anything in the bundle is readable.
- [ ] Crash reporting is configured for the production profile with source maps uploaded, otherwise stack traces are unreadable. verify (unconfirmed) the upload step for your crash tool.
- [ ] Deep links and push notification paths open the right screen from a cold start and from the background.
- [ ] App icon, splash and name are final; the adaptive icon on Android respects its safe zone.
- [ ] Accessibility pass: VoiceOver and TalkBack through the main flow.
- [ ] Offline and slow-network pass: airplane mode on every first-load screen.

## Build and versioning

- [Expo] Two numbers: the user-facing version (`version`) and a build counter (`ios.buildNumber`, `android.versionCode`). The store rejects a build number that is not higher than the last upload. EAS can manage the counter (`autoIncrement` in the build profile with a remote version source; verify (unconfirmed) field names in the eas.json docs).
- [Expo] Use separate build profiles at least for development, preview (internal testers) and production, with different bundle identifiers or suffixes if both must be installable side by side.
- [Expo] Changing native config, adding a native module or a config plugin requires a new binary; plan a store release, not an update.
- [bare] Bump versionCode / CFBundleVersion in the native projects; sign with the upload key you control and keep it backed up outside the repo.
- Hermes is the default engine on current RN; do not disable it unless a library demands it. verify (unconfirmed) for your RN version.
- Check the New Architecture state of the project: new projects on recent RN and Expo SDKs enable it by default (RN 0.76 and Expo SDK 52 to 53 were the transition; verify (unconfirmed)). A third-party native library that does not support it can crash at start. Test the exact build you ship.

## Store submission

- [ ] iOS: privacy manifest and required-reason API declarations are present for your app and for SDKs that need them; the App Store privacy label matches what the app and its SDKs collect. verify (unconfirmed) current Apple requirements.
- [ ] iOS: if accounts can be created in the app, in-app account deletion must be possible; third-party login may require an equivalent privacy-preserving option. verify (unconfirmed) current guidelines.
- [ ] Android: target API level meets the store's current minimum (it rises roughly yearly; verify (unconfirmed) the number on the Play Console help page on release day). Large-screen and 16 KB page size support are recent requirements for some targets; verify (unconfirmed).
- [ ] Android: the data safety form matches the app's real data use.
- [ ] Screenshots for each required device size; test-account credentials for reviewers in the review notes if login is required.
- [ ] Use a staged rollout (Android) or phased release (iOS) for production, starting small, and watch crash-free sessions before widening.

## After release

- [ ] Check the live version on a clean device installed from the store, not from the build artifact.
- [ ] Watch crash-free users and ANR (Android not-responding) rates for 24 hours; set a rollback or hotfix plan before release (an OTA fix if the bug is JS-only).
- [ ] Tag the commit that matches each store build.

## Over-the-air updates

- [Expo] EAS Update ships JS and asset changes only; it matches an update to binaries by runtimeVersion. Choose a runtimeVersion policy deliberately (a fixed string you bump when native code changes, or a policy derived from the app version or a fingerprint; verify (unconfirmed) policy names).
- An OTA update must never depend on a native change that is not in the installed binary.
- Test an update on a production-profile build pointing at a test channel before pointing production users at it.
- Store policies allow OTA updates of JS that stay within the app's reviewed purpose; do not use them to change what the app fundamentally does. verify (unconfirmed) current wording.
