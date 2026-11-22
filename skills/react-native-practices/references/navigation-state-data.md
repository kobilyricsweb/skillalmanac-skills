## Contents
- Navigation structure
- State placement
- Data fetching with a query library
- Storage choices
- Keyboard and safe area

# Navigation, state and data

## Navigation structure

Two stacks are common: Expo Router (file-based, built on React Navigation) and React Navigation used directly. The shapes below apply to both.

| Rule | Reason |
|---|---|
| One root navigator; tabs inside it; stacks inside tabs. Do not nest tabs inside a stack inside tabs inside a stack | Each nesting level adds back-button and header behaviour you must reason about; two levels of tabs is a smell |
| Auth gate at the root: choose the signed-in tree or the signed-out tree, do not push a login screen on top | A pushed login can be swiped or navigated back from. In Expo Router use route groups such as `(auth)` and `(app)` and a redirect in the group layout; in React Navigation render different screens by auth state |
| Screen params carry ids and small primitives, not whole objects, functions or class instances | Non-serialisable params warn, break deep links and state restore. Fetch the entity by id on the screen |
| Every screen reachable by deep link is defined once with a stable path | Universal links and push notifications reuse those paths |
| Header options are set in the screen or the layout, not by calling setOptions from a chain of effects | Avoids flicker and stale titles |
| Do not keep fetching on screens that are mounted but not focused | Stack screens stay mounted below the top one; tab screens stay mounted after the first visit |

Version-dependent:
- React Navigation 7 changed `navigate`: it no longer pops back to an existing screen of the same name in a stack by default; the documented replacement for "go back to that screen" is `popTo`. verify (unconfirmed) against the installed 6.x or 7.x docs before editing code that relied on the old behaviour.
- Expo Router versions differ between SDKs (typed routes, `Link` props, `router.dismiss` behaviour). verify (unconfirmed) the router version in package.json before using an API from memory.
- Refetching on focus uses a focus hook (`useFocusEffect` in React Navigation; Expo Router re-exports the same name). A plain `useEffect` runs on mount only.

## State placement

Place state at the lowest level that needs it, in this order:
1. Local component state (form field, open/closed).
2. URL / route params (selected id, filter, tab): survives deep link and restart.
3. Server state in a query cache (anything that came from an API).
4. Small client store (Zustand, Redux Toolkit, Jotai) only for state shared across screens that is not server data: session, theme, draft.
5. Context for stable, rarely changing values (theme, locale). A context whose value changes often re-renders every consumer; split it or use a store with selectors.

Never copy server data into a client store "to share it"; read it from the query cache with the same key.

## Data fetching with a query library

TanStack Query is common in RN. Facts specific to RN (verify (unconfirmed) for the installed major; v5 was current when this was written):
- Window-focus refetching does not exist on its own in RN; wire the library's focus manager to AppState and its online manager to a network-state package, or accept that refetch happens only on mount and reconnect rules you set.
- Set a sensible staleTime (for example 30 to 60 seconds for feeds); the default of 0 refetches on every mount and every focus signal.
- Cancel is automatic when the query key changes; do not also guard with manual flags.
- Mutations: invalidate the exact keys they change; avoid invalidating the whole cache.
- Lists: use the library's infinite-query API with `onEndReached` on the list, and guard `onEndReached` against firing while a page is already loading (it can fire more than once per scroll).
- Do not put the auth token in a query key.

## Storage choices

| Data | Store | Note |
|---|---|---|
| Tokens, secrets | Keychain / Keystore backed storage (expo-secure-store in Expo) | Not AsyncStorage: it is unencrypted. SecureStore has a small per-value size limit (about 2 KB on iOS was documented; verify (unconfirmed)); store the token, not a large object |
| Preferences, small caches | AsyncStorage or MMKV | Async vs sync API differs; MMKV needs a native build, not Expo Go (verify (unconfirmed) current support) |
| Large structured data | SQLite (expo-sqlite) | Query instead of loading and filtering in JS |
| Files and images | File system API; keep paths, not bytes, in state | |

## Keyboard and safe area

- Forms: KeyboardAvoidingView usually needs `behavior="padding"` on iOS; on Android the manifest's `windowSoftInputMode` often makes it unnecessary, and wrong use doubles the offset. Test both; do not assume one value for both platforms. Edge-to-edge behaviour on Android changed in recent SDKs; verify (unconfirmed) for your SDK.
- Use `react-native-safe-area-context` insets (`useSafeAreaInsets`) for notches and home indicators, not fixed numbers per platform.
