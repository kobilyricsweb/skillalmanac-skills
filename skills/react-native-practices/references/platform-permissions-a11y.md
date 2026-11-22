## Contents
- Platform boundary rules
- Permission handling procedure
- Permission strings and manifest entries
- Accessibility props

# Platform code, permissions and accessibility

## Platform boundary rules

Pick the lightest tool that fits the size of the difference.

| Difference | Tool | Example |
|---|---|---|
| One value (a size, a font, a colour) | `Platform.select({ ios: ..., android: ..., default: ... })` kept in one theme or constants module | shadow vs elevation |
| One small branch of behaviour | `Platform.OS === 'ios'` inside a single helper named for the purpose | `shouldShowBackLabel()` |
| Whole component differs | Platform file extensions: `Thing.ios.tsx`, `Thing.android.tsx`, `Thing.tsx` as the shared fallback; `.native.tsx` for both phones vs web | date picker |
| Native API missing on the web or on one phone OS | A thin wrapper module with the same exported signature per platform; callers never branch | `haptics.ts` / `haptics.web.ts` |
| Device model or OS version gating | Feature detection first; `Platform.Version` only when no detection exists (its type differs between iOS and Android) | |

Rules:
1. `Platform.OS` is lowercase: `ios`, `android`, `web` (and `windows`, `macos` on out-of-tree platforms). `'iOS'` or `'Android'` is always false and the scanner flags it as warn.
2. No bare per-platform numbers for status bar, notch or keyboard sizes; use safe-area insets.
3. More than 3 platform checks in one file is a sign the file should be split (the scanner reports this as info; 3 is a working value).
4. If the app targets web through Expo, every native-only import needs a `.web` counterpart or a guard; web builds fail or crash on native modules.
5. Shadows: iOS uses the shadow* props, Android uses `elevation`; a newer `boxShadow` style prop exists only on newer RN versions. verify (unconfirmed) the minimum RN version before using it.

## Permission handling procedure

Use this order for every permission (camera, photos, location, notifications, contacts, microphone):

1. Ask in context. Request at the moment the user taps the feature that needs it, never at launch.
2. Read the current status first (the module's get-permissions call). Do not request when already granted.
3. Branch on three outcomes, not two:
   - granted: continue.
   - denied and can ask again: show your own one-line reason, then request.
   - denied and cannot ask again (Expo permission modules return a `canAskAgain` flag; verify (unconfirmed) per module): the system will not show the prompt. Show an explanation and a button that calls `Linking.openSettings()`.
4. Handle partial grants: the iOS photo library can be "limited" and location can be approximate or while-in-use only. State what the feature does with less.
5. Re-check status when the app returns to the foreground (AppState `active`), because the user may have changed it in Settings.
6. Never block the whole app on one permission; give a degraded path (manual entry, pick from files).
7. Test the denied path and the cannot-ask-again path on a real device or simulator with a reset install; both are where bugs live.

Platform facts (verify (unconfirmed) for the target OS release):
- iOS shows the system prompt once; after a denial only the Settings screen can change it.
- Android 13 (API 33) and later require a runtime request for notifications.
- Android may stop showing the prompt after repeated denials.
- Background location needs a second, separate request and, on Android, a separate declaration in the store listing.

## Permission strings and manifest entries

- iOS refuses to show a prompt (and App Review rejects the build) without a usage description string for each sensitive API: camera, photo library, microphone, location when in use, and so on. In Expo set them through the module's config plugin in app config or through the `ios.infoPlist` block; in a bare project they live in Info.plist.
- Write each string as a purpose in plain words ("lets you attach a photo to your report"), not "needs camera".
- Android permissions go in the app config `android.permissions` or the module's plugin; request only what is used. Unused permissions trigger store questions.
- Any new native permission needs a new native build; an over-the-air update cannot add it.

## Accessibility props

Core props (RN 0.71 and later also accept web-style `aria-*` and `role` aliases; verify (unconfirmed) the exact set for your RN):

| Need | Prop | Notes |
|---|---|---|
| Make a custom touchable readable as one element | `accessible` (true on Pressable by default) | Text inside is read as the label when there is no explicit label |
| Name for an icon-only button | `accessibilityLabel` (`aria-label`) | Describe the action ("Delete message"), not the icon ("trash") |
| What kind of control | `accessibilityRole` (`role`): button, link, header, image, search, tab, switch, checkbox, ... | Screen readers announce it |
| Current state | `accessibilityState` ({ disabled, selected, checked, expanded, busy }) | Keep in step with the visual state |
| Extra instruction | `accessibilityHint` | Only when the result is not obvious; never repeat the label |
| Hide decoration | iOS `accessibilityElementsHidden`; Android `importantForAccessibility="no-hide-descendants"`; or `aria-hidden` | Hide purely visual repeats |
| Group related text | wrap in a View with `accessible` | One swipe stop instead of five |
| Announce a change | `AccessibilityInfo.announceForAccessibility` | Toasts and async results |
| Large text | Leave `allowFontScaling` on; test at the largest system font | Fixed-height rows clip text |

Numbers: touch targets at least 44 by 44 points on iOS and 48 by 48 dp on Android (platform guidance); when the visual is smaller use `hitSlop` rather than enlarging the art. Body text contrast at least 4.5:1 (WCAG 2.x AA).

Test with VoiceOver on iOS and TalkBack on Android, on a device, for each primary flow. Simulators do not replace this.
