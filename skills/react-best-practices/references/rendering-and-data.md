# Rendering cost, keys, data and version notes

## Contents

- Keys
- When to memoise
- Rendering cost: causes worth fixing
- Data fetching
- Server and client components
- Accessibility in components
- Version notes
- Sources

## Keys

- A key identifies an item among its siblings across renders. Use an id that comes with the data. If the data has none, create ids when the items are created (on load or on add), not during render.
- Index keys are acceptable only when the list is static: never reordered, filtered, inserted into or deleted from. Otherwise component state and DOM state (input text, focus, scroll, animations) attach to the wrong item.
- A key generated in render (`Math.random()`, a new uuid) remounts every item on every render.
- The key goes on the outermost element returned by the map callback, including on a fragment (`Fragment` with `key`; the short syntax cannot take one).
- Changing a key on purpose is the supported way to reset a subtree's state.

## When to memoise

Check first whether the React Compiler is enabled in the build. With the compiler on, components and values are memoised automatically; do not add manual `memo`, `useMemo` or `useCallback`, and do not remove existing ones without testing.

Without the compiler, add memoisation only when all three hold: the render is measurably slow or the tree is large; the props really are stable between renders; and the cheaper structural fixes below do not apply.

Structural fixes that beat memoisation:

1. Move state down into the component that uses it, so siblings stop re-rendering.
2. Pass children as props (`children` or a slot): elements created by the parent do not re-render when the wrapper's state changes.
3. Split a context that mixes fast-changing and slow-changing values.
4. Hoist constants, static objects and pure helpers out of the component.

`useMemo` and `useCallback` without a dependency array do nothing. A memoised child receiving an inline object, array or arrow function still re-renders.

## Rendering cost: causes worth fixing

| Cause | Fix |
|---|---|
| Thousands of rows in the DOM | Virtualise the list, or paginate |
| Expensive computation in render (sort, filter, parse of large data) | `useMemo` with correct dependencies; or compute once when the data loads |
| A typing-driven state update re-renders a heavy tree | Keep the input state local; `useDeferredValue` or a transition for the heavy part; debounce requests |
| Context value recreated every render | `useMemo` the value, or split state and dispatch contexts |
| Whole-library imports | Import the specific module; lazy-load routes and heavy widgets with `lazy` declared at module scope plus `Suspense` |
| Layout thrash: reading layout then writing in a loop | Batch reads, then writes; `useLayoutEffect` only for measure-then-paint |
| Images without dimensions | Set width and height or aspect ratio to prevent layout shift |

## Data fetching

- Prefer, in order: the framework's server-side or loader data; a query or cache library already in the project; a hand-written effect with cancellation.
- Every data region has four states: loading, error (with a retry), empty, ready. Decide which of them keeps the previous data visible.
- Start independent requests together (`Promise.all`) instead of awaiting one after another. A child that fetches only after its parent finishes is a waterfall: hoist or preload.
- Mutations: disable or mark the control while pending, show the failure next to the action, and reconcile or refetch on success. Optimistic updates need a rollback path.
- Do not keep server data in two places (a query cache and component state). Derive from the cache.
- Encode user input put into URLs; never interpolate it into HTML.

## Server and client components

Applies only to frameworks that use React Server Components.

- Components are server components unless the file starts with the client directive. Hooks with state or effects, event handlers and browser APIs require a client component.
- Put the client boundary as low as possible: a small interactive leaf inside a server-rendered page, not the whole page.
- Props crossing from server to client must be serialisable: no functions (except server actions), no class instances.
- Client components cannot be `async`. Server components can, and can fetch directly.
- Do not read `window`, storage or the current time during render in a client component that is also pre-rendered on the server: the markup will not match on hydration. Read in an effect, or render a stable placeholder first.

## Accessibility in components

- Clickable things are `button type="button"` (actions) or `a href` (navigation). A `div` with `onClick` needs a role, `tabIndex`, key handling and focus styling to be equivalent; using the native element is shorter and safer.
- Every input has a `label` (`htmlFor` and `id`, or wrapping). Use `useId` for generated ids so server and client match.
- Icon-only buttons have an accessible name (`aria-label`); decorative icons are `aria-hidden`.
- Announce async results: `role="status"` for neutral updates, `role="alert"` for errors; the region exists before its text changes.
- When content is removed (row deleted, dialog closed), move focus to a sensible neighbour or back to the trigger.
- Toggle state is exposed (`aria-pressed`, `aria-expanded`, `aria-sort` on sortable column headers).

## Version notes

Check the installed major version before recommending or removing an API.

| Topic | React 18 and earlier | React 19 and later |
|---|---|---|
| Passing a ref to a function component | `forwardRef` required | `ref` is a regular prop; `forwardRef` still works but is no longer needed |
| `defaultProps` on function components | Works | Removed: use default parameter values |
| `propTypes` | Checked in development | Ignored: use TypeScript or validation at boundaries |
| Context provider | `Context.Provider` | The context itself can be rendered as the provider; `.Provider` still works |
| Form submission and pending state | Hand-written state | Actions with `useActionState`, `useFormStatus`, `useOptimistic` |
| Reading a promise or context conditionally | Not available | `use()` (may be called inside conditions and loops, unlike hooks) |
| Ref callbacks | Called with `null` on unmount | May return a cleanup function |
| Automatic memoisation | Not available | React Compiler, if enabled in the build |
| Non-reactive logic inside effects | Refs or dependency workarounds | Effect events (`useEffectEvent`) in versions that ship it as stable; check the installed minor version |

In any version: effects run twice on mount in development strict mode; state updates are batched, including inside promises and timers from React 18 on.

## Sources

- React documentation, Rendering Lists (keys): https://react.dev/learn/rendering-lists
- React documentation, Preserving and Resetting State: https://react.dev/learn/preserving-and-resetting-state
- React documentation, useMemo and memo reference: https://react.dev/reference/react/useMemo
- React documentation, React Compiler: https://react.dev/learn/react-compiler
- React 19 release notes and upgrade guide: https://react.dev/blog/2024/12/05/react-19 and https://react.dev/blog/2024/04/25/react-19-upgrade-guide
- React documentation, Server Components and directives: https://react.dev/reference/rsc/server-components
