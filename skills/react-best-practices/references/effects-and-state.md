# Effects and state: decisions and replacements

## Contents

- Does this need an effect?
- Effect checklist
- Async effects and races
- Stale closures
- State structure
- Symptoms and their usual causes
- Sources

## Does this need an effect?

An effect synchronises a component with something outside React: the network, the DOM, a timer, a subscription, a browser API, a third-party widget. If nothing outside React is involved, there is a better tool.

| What the effect does | Replace it with |
|---|---|
| Sets state computed from props or other state | Compute it during render. `useMemo` only if measured slow |
| Resets all state when a prop (an id) changes | Give the component a `key` equal to that prop |
| Adjusts part of the state when a prop changes | Store the id or the raw input instead and derive the rest in render |
| Runs logic because the user did something (submit, click, select) | Put it in the event handler |
| Chains: effect A sets state that triggers effect B | Compute everything in one handler, or with a reducer |
| Tells the parent about a state change (`onChange` in an effect) | Call the parent's callback in the same handler that sets the state, or lift the state up |
| Passes data up from a child after fetching | Fetch in the parent and pass data down |
| Subscribes to an external store or browser value (online status, media query, storage) | `useSyncExternalStore` |
| Initialises something once per app load | Module scope, or a guard variable outside the component |
| Fetches data | The framework's data loading or a query library if the project has one; otherwise an effect with cancellation (below) |

Effects that remain are legitimate: subscriptions, timers, imperative DOM work (focus, scroll, measuring), wiring non-React widgets, analytics on view.

## Effect checklist

1. **Dependencies are complete.** Every reactive value read inside (props, state, anything derived from them, functions declared in the component) is in the array. Do not silence the lint rule; change the code so the dependency is unnecessary (move the function inside the effect, use an updater, move constants out of the component).
2. **Cleanup mirrors setup.** `addEventListener` and `removeEventListener` with the same function reference; `setInterval` and `clearInterval`; `subscribe` and `unsubscribe`; `observe` and `disconnect`; open and close.
3. **It survives running twice.** Development strict mode mounts, unmounts and mounts again. If the second run breaks something (duplicate request side effects, double subscription), the cleanup is incomplete.
4. **Object and function dependencies.** An object or function created during render is new every time and re-runs the effect on every render. Depend on primitives (`options.id`), or create the object inside the effect.
5. **No unconditional `setState` on a dependency it also sets.** That is an infinite loop.

## Async effects and races

The effect callback cannot be `async`: it must return a cleanup function or nothing. Pattern:

```jsx
useEffect(() => {
  const controller = new AbortController();
  async function load() {
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`, { signal: controller.signal });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResult({ status: "ready", data: await res.json() });
    } catch (err) {
      if (err.name !== "AbortError") setResult({ status: "error", error: err });
    }
  }
  setResult({ status: "loading" });
  load();
  return () => controller.abort();
}, [query]);
```

- Without the abort (or an `ignore` flag set in cleanup), typing "ab" then "abc" can show results for "ab" if that response arrives last.
- `fetch` does not reject on HTTP errors; check `res.ok`.
- Keep `status`, `data` and `error` in one state value so impossible combinations (loading and error together) cannot be represented.
- Debounce input-driven requests with a timer inside the effect, cleared in the cleanup.

## Stale closures

A function captures the props and state of the render that created it.

| Situation | Symptom | Fix |
|---|---|---|
| `setInterval(() => setCount(count + 1), 1000)` in an effect with `[]` | Counter stops at 1 | `setCount(c => c + 1)` |
| Two `setCount(count + 1)` calls in one handler | Only one increment | Updater form for each |
| Handler awaits, then reads state | Uses the value from before the await | Read from the updater, a ref, or re-derive from the response |
| Subscription callback reads props | Uses the first props forever | Add the prop to dependencies, or use an effect event where the React version has it |
| Memoised callback with missing dependencies | Acts on old data | Complete the dependencies |

A ref (`useRef`) holds a mutable value that does not trigger rendering. Read or write `ref.current` in handlers and effects, not during render.

## State structure

- **Minimal:** store the smallest set of facts; derive the rest. Selected item: store the id, not a copy of the object.
- **No contradictions:** replace `isLoading`, `isError`, `isSuccess` booleans with one `status`.
- **No duplication:** the same fact in two places will drift. A prop copied into state ignores later prop changes; name it `initialX` if that is intended.
- **Flat:** deeply nested state makes immutable updates error-prone; normalise by id.
- **Colocated:** state lives in the lowest component that needs it. Lift it only to the closest common parent of its readers. Context is for values many distant components read and that change rarely; split fast-changing values into their own context.
- **Controlled or uncontrolled, not both:** an input has `value` and `onChange`, or `defaultValue` and a ref. Switching from `undefined` to a string value mid-life triggers a warning and loses input.
- **Reducer** when the next state depends on the kind of event and several fields change together.
- **URL as state** for filters, sort order, page and selected tab, so the view can be shared and survives a reload.

## Symptoms and their usual causes

| Symptom | Look for |
|---|---|
| Input loses focus or its text on every keystroke | Component defined inside another component; unstable `key`; parent re-keying |
| "Too many re-renders" | `setState` during render; handler called instead of passed (`onClick={fn()}`) |
| Effect runs forever | Object or function dependency recreated each render; effect sets its own dependency |
| Request fires twice in development | Strict mode double mount: correct behaviour; make the effect cancellable rather than adding a guard |
| List items show the wrong state after reorder or delete | Index keys |
| Old search results flash over new ones | Fetch race, no cancellation |
| "0" appears in the page | `count && <X />` |
| Hydration mismatch warning | Render reads `window`, storage, time, random or locale-dependent formatting |
| Everything under a provider re-renders | Inline object as context value |
| State did not update right after `setX` | Reading state in the same handler: it is a snapshot; compute the next value in a variable and use it for both |
| "Rendered more hooks than during the previous render" | Hook after an early return, or inside a condition or loop |

## Sources

- React documentation, You Might Not Need an Effect: https://react.dev/learn/you-might-not-need-an-effect
- React documentation, Synchronizing with Effects and Lifecycle of Reactive Effects: https://react.dev/learn/synchronizing-with-effects
- React documentation, Choosing the State Structure: https://react.dev/learn/choosing-the-state-structure
- React documentation, Rules of Hooks: https://react.dev/reference/rules/rules-of-hooks
