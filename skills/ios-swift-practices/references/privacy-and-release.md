## Contents

1. Privacy manifest
2. Required-reason API categories
3. Permission purpose strings
4. Review-guideline items that cause rejections
5. Release checklist

Anything marked "verify (unconfirmed)" was written from memory of Apple's documentation and not re-read in this session.

## 1. Privacy manifest

A property-list file named `PrivacyInfo.xcprivacy`, added to the app target (and shipped inside each third-party SDK that is on Apple's list of commonly used SDKs; enforcement dates: verify (unconfirmed)). Top-level keys:

| Key | Type | Meaning |
|---|---|---|
| `NSPrivacyTracking` | Boolean | true only if the app or an SDK tracks users as Apple defines tracking |
| `NSPrivacyTrackingDomains` | Array of strings | domains used for tracking; blocked until the user allows tracking |
| `NSPrivacyCollectedDataTypes` | Array of dictionaries | each data type collected, whether linked to the user, whether used for tracking, and the purposes |
| `NSPrivacyAccessedAPITypes` | Array of dictionaries | each required-reason API category used plus the reason codes |

Rules of thumb:

- The manifest and the App Store Connect privacy answers must agree; a mismatch is a review risk.
- Each SDK keeps its own manifest; Xcode can merge them into one report (Product > Archive > Generate Privacy Report): verify (unconfirmed) menu path.
- Declaring a category without using it, or using one without declaring it, are both wrong. Search the whole app, including packages, for each API in section 2.

## 2. Required-reason API categories

Five categories exist at the time of writing; the reason codes below are examples to be checked against Apple's list before use (verify (unconfirmed)).

| Category key | Typical APIs that trigger it | Example reason code |
|---|---|---|
| `NSPrivacyAccessedAPICategoryUserDefaults` | `UserDefaults`, `@AppStorage` | `CA92.1` (read and write data only the app itself uses) |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | `creationDate`, `modificationDate`, `fileModificationDate`, `stat` | `C617.1` (files inside the app container) |
| `NSPrivacyAccessedAPICategorySystemBootTime` | `ProcessInfo.systemUptime`, `mach_absolute_time` | `35F9.1` (measure elapsed time between events in the app) |
| `NSPrivacyAccessedAPICategoryDiskSpace` | `volumeAvailableCapacityKey`, `systemFreeSize` | `E174.0` (check space before writing) |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | `UITextInputMode.activeInputModes` | `3EC4.1` (custom keyboard apps only) |

Pick the reason code that is true for your use; do not copy a code because it is accepted.

## 3. Permission purpose strings (Info.plist)

A missing key makes the system terminate the app when it first touches the protected resource, and fails review. The text must say why in plain words (not "needed for the app").

| Resource | Info.plist key |
|---|---|
| Camera | `NSCameraUsageDescription` |
| Microphone | `NSMicrophoneUsageDescription` |
| Photo library read/write | `NSPhotoLibraryUsageDescription` |
| Add-only to photos | `NSPhotoLibraryAddUsageDescription` |
| Location while in use | `NSLocationWhenInUseUsageDescription` |
| Location always | `NSLocationAlwaysAndWhenInUseUsageDescription` (plus the when-in-use key) |
| Contacts | `NSContactsUsageDescription` |
| Face ID | `NSFaceIDUsageDescription` |
| Bluetooth | `NSBluetoothAlwaysUsageDescription` |
| Calendar (iOS 17+ full or write-only) | `NSCalendarsFullAccessUsageDescription`, `NSCalendarsWriteOnlyAccessUsageDescription`: verify (unconfirmed) |
| Tracking (ATT) | `NSUserTrackingUsageDescription`, requested with `ATTrackingManager` |

Behaviour rules: ask at the moment the feature is used, after a screen that explains it; handle "denied" and "restricted" with a path to Settings; do not re-ask in a loop. `PhotosPicker` / `PHPickerViewController` need no photo-library permission because the user picks items out of process.

## 4. Review-guideline items that cause rejections

- Offering a third-party or social login requires also offering Sign in with Apple or another login service that meets Apple's privacy criteria (guideline 4.8): verify (unconfirmed) wording.
- An app that lets users create an account must let them delete it inside the app (guideline 5.1.1(v)).
- Digital goods are sold with In-App Purchase; include a visible Restore Purchases action.
- Placeholder content, broken links and a demo account that does not work are the common avoidable rejections; put working credentials in the review notes.
- Screens that mention other platforms, or incomplete features, are rejected under completeness rules.

## 5. Release checklist

Copy and tick:

```
- [ ] Marketing version bumped (CFBundleShortVersionString); build number (CFBundleVersion) higher than any build already uploaded for that version
- [ ] Release configuration builds; no `print` left outside #if DEBUG; no test endpoints or debug menus compiled in
- [ ] PrivacyInfo.xcprivacy present; every required-reason API used by the app and packages is declared; third-party SDK manifests present
- [ ] Every permission used has its Info.plist purpose string
- [ ] App Store Connect privacy answers match the manifest and the SDKs
- [ ] ITSAppUsesNonExemptEncryption set (or export compliance answered); standard HTTPS only normally means exempt: verify (unconfirmed)
- [ ] ATS exceptions removed or justified
- [ ] Entitlements and capabilities match what the code uses (push, sign-in with Apple, associated domains)
- [ ] Sign in with Apple offered if other social login is; in-app account deletion if accounts exist
- [ ] Restore Purchases present if IAP exists
- [ ] Accessibility pass done at the largest Dynamic Type size and with VoiceOver on the main flow
- [ ] Debug symbols (dSYM) uploaded to the crash-reporting tool
- [ ] Built with an Xcode version that App Store Connect currently accepts: verify (unconfirmed)
- [ ] Screenshots for the required device sizes: verify (unconfirmed)
- [ ] Review notes: demo account, how to reach hard-to-find features, any non-obvious permission
- [ ] TestFlight build run on a physical device at the minimum supported iOS version
- [ ] Age-rating questionnaire up to date
```
