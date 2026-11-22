## Contents

- Permission decision table
- Request flow
- Privacy and data rules
- Manifest and component hygiene
- Accessibility checklist with numbers
- Semantics recipes

## Permission decision table

Version notes below are from memory; every API-level number is "verify (unconfirmed)" until checked against the current docs.

| Need | Prefer | Permission only if the preferred way cannot do it |
|---|---|---|
| Pick a photo or video | system photo picker (no permission) | media read permissions; from API 34 the user may grant partial access, so the app must work with a subset |
| Pick or save a document | document picker / `ACTION_CREATE_DOCUMENT` (no permission) | broad storage access: almost never; Play restricts it |
| Take a photo | `ActivityResultContracts.TakePicture` into a `FileProvider` Uri (no permission) | `CAMERA` only for an in-app camera preview |
| Share content | share sheet / `ACTION_SEND` | none |
| Location | approximate first; ask precise only when the feature needs street-level accuracy | background location is a separate, later request on recent versions and needs a store justification |
| Notifications | explain value, then request `POST_NOTIFICATIONS` (runtime permission from API 33) | none; create the channel before posting |
| Contacts, calendar, microphone | request at the tap that needs it | none |
| Bluetooth scan or connect | the nearby-devices permissions on recent versions, with `neverForLocation` when scanning does not derive location | location permission on older versions |

## Request flow

1. Check `ContextCompat.checkSelfPermission` or the launcher result; never assume the last answer still holds (the user can revoke in settings at any time, and the app process may be killed).
2. If not granted and `shouldShowRequestPermissionRationale` is true, show a short in-app reason, then launch the request.
3. Launch with `rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission())` (or `registerForActivityResult` in Views). Register the launcher unconditionally during composition or `onCreate`, not inside a click handler.
4. On denial: keep every other feature working; disable only the dependent control and say why.
5. On permanent denial (the request returns immediately without a dialog and the rationale flag is false after a denial): link to app settings with `ACTION_APPLICATION_DETAILS_SETTINGS`. Do not loop the request.
6. Request the smallest set together; never request all permissions at first launch.

## Privacy and data rules

- Collect only what the feature uses. Every dangerous permission and every third-party SDK that collects data must appear consistently in the store's data-safety declaration; a mismatch is a review rejection risk (verify (unconfirmed) current policy).
- Secrets and tokens: Android Keystore keys, with data encrypted by them. Not `SharedPreferences` in plain text, not `BuildConfig` fields in a public repository, not logs. Do not assume a particular Jetpack security library is current: its status changes (verify (unconfirmed)).
- API keys shipped in the APK are extractable. Treat them as public; restrict by package name and signature on the provider side, or proxy through a backend.
- Logging: no tokens, emails, locations or full URLs with query parameters in `Log` calls of release builds (scanner rule `log-in-release`).
- `allowBackup`: decide it explicitly; with `true`, app data can be copied by device backup. Exclude token files with data extraction rules (verify (unconfirmed) attribute names by target SDK).
- Network: HTTPS only; cleartext is blocked by default for recent target SDKs; do not add a debug "trust all certificates" `TrustManager` that can reach release.
- Screens with sensitive data (payments, health) consider `FLAG_SECURE` to block screenshots and recents thumbnails.
- Clipboard: do not put secrets on it; on recent versions the system shows a toast when an app reads it.

## Manifest and component hygiene

- Every `activity`, `service`, `receiver` with an `intent-filter` declares `android:exported` explicitly (required when targeting recent SDKs). Default to `false`; export only deliberate entry points and validate their intent extras as untrusted input.
- `PendingIntent` gets `FLAG_IMMUTABLE` unless the receiver must modify it.
- `WebView`: no `setJavaScriptEnabled(true)` for untrusted content; no `addJavascriptInterface` with untrusted pages; restrict loaded URLs to an allow-list.
- Deep links: verify the host with Digital Asset Links for app links; treat the path and query as untrusted.
- Foreground services need a declared type and matching permission on recent versions (verify (unconfirmed)); prefer WorkManager for deferrable work.
- `FileProvider` paths: share the narrowest directory, never `root-path`.

## Accessibility checklist with numbers

| Check | Threshold |
|---|---|
| Touch target | at least 48 x 48 dp (visual size may be smaller; padding counts) |
| Text contrast | at least 4.5:1 normal text; 3:1 large text (18 sp regular or 14 sp bold and up) and non-text UI such as icons and borders |
| Font scale | no clipped or overlapping text at 200%; use `sp`, wrap rather than fixed heights |
| Spacing between targets | at least 8 dp |
| Time limits and motion | allow users to extend or disable; respect the system "remove animations" setting |
| Color | never the only carrier of meaning (error = red only fails) |
| Focus order | matches reading order; check with TalkBack swipe navigation |

## Semantics recipes

- Informative image: `Image(painter, contentDescription = stringResource(...))`. Decorative: `contentDescription = null`. Do not write "image of" or "button" in the label; the role is announced.
- Icon-only button: `IconButton(onClick) { Icon(imageVector, contentDescription = stringResource(R.string.close)) }`.
- Clickable row with several children: `Modifier.clickable(onClickLabel = ...)` merges descendants for the screen reader; for a non-clickable group use `Modifier.semantics(mergeDescendants = true) { }`.
- Toggle or radio rows: `Modifier.toggleable(value, role = Role.Switch, onValueChange)` or `selectable(selected, role = Role.RadioButton)`, so state is announced.
- Section titles: `Modifier.semantics { heading() }`.
- Dynamic status text (errors, loading done): `Modifier.semantics { liveRegion = LiveRegionMode.Polite }`.
- Swipe-only gesture: add `customActions` or a visible button; gestures alone are not reachable.
- Custom component size: `Modifier.minimumInteractiveComponentSize()` where the component is smaller than 48 dp.
- Verify with TalkBack on a device, plus the Accessibility Scanner app, plus a Compose UI test that finds the node with `onNodeWithContentDescription`. A scanner pass does not replace TalkBack.
