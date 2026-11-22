# ProductSearch.jsx: fix notes

Fixed file: `ProductSearch.fixed.jsx` in this folder. Props (`category`, `onSelect`) and the visible layout (input, sort select, Loading text, result list) are unchanged.

## Reported symptoms and causes

| Symptom | Cause in the original | Fix |
|---|---|---|
| Old results flash over new ones | The fetch effect had no cancellation. A slow response for an earlier query could arrive after a newer one and overwrite `results`. | One `AbortController` per run, aborted in the effect cleanup. Superseded responses are dropped. |
| Stray `0` on the page | `{sortedResults.length && (...)}` renders `0` when the list is empty. | `sortedResults.length > 0 && (...)`. |
| Results do not update when the category changes | The effect depended only on `[query]`. `activeCategory` was copied from the prop once in `useState(category)` and never updated, so the request always used the first category. | The category is read straight from props and listed in the dependencies: `[query, category]`. The `activeCategory` state is deleted. |
| Uncontrolled input warning | `useState()` made `query` `undefined` at first, so `value` went from `undefined` to a string. | `useState("")`. |

## Other changes

- **Sorting no longer mutates state.** The original sorted `results` in place (`copy = results; copy.sort(...)`) and then copied it into a second state (`sortedResults`) through an effect. Now `sortedResults` is derived during render from a copy (`[...results].sort`). This removes a state variable and an effect, and the one-render lag where the list showed unsorted data.
- **Clearing the query clears the results.** The original returned early on an empty query, so the previous results stayed on screen. Now an empty (or whitespace-only) query empties the list and cancels any request in flight. Whitespace-only input no longer triggers a request. This is a behaviour change.
- **Query and category are URL-encoded** with `encodeURIComponent`. Before, a query containing `&` or `#` broke the URL.
- **HTTP errors and network failures are handled.** Before, a non-OK response or a rejected fetch left `loading` stuck on `true` with no message. Now a non-OK response or failure clears the results, sets `loading` to false and shows `Could not load products.` (`role="alert"`). This is a new visible message, shown only on failure.
- **Accessibility, with no visual change intended:**
  - Each result is a `<button type="button">` inside the `<li>`, replacing the `onClick` on `<li>`, so it is keyboard-operable. Check that existing CSS does not target `li` click styling; the button inherits the text and is otherwise unstyled.
  - The search input has `aria-label="Search products"`.
  - The Loading text has `role="status"`.
- **Keys:** `key={p.id ?? i}`. The list is re-sorted, so an index key alone can match rows to the wrong items. This assumes the API returns a product `id` when available. If it never does, the index fallback still works, because the rows hold no state.

## Behaviour that did not change

- The request fires only when there is a non-empty query. Changing the category with an empty query still does nothing.
- The request URL keeps the same path and parameter names (`q`, `category`).
- The sort options and default (`name`), and the price formatting `name $price`, are unchanged.

## Checks run

- `react_scan.py` on the original: 1 FAIL (`sortedResults.length &&` renders 0), 3 WARN (fetch race, index key, `li` onClick).
- `react_scan.py` on the fixed file: 0 FAIL, 0 WARN.

## Not verified

- Runtime behaviour was not executed. The race fix, category refetch and no-`0` render are reasoned from the source, not observed in a browser or test.
- No project type-check, lint (`react-hooks/exhaustive-deps`) or tests were run. The repo was not provided; only the single file was given.
- Whether `/api/products` returns an `id` field, and what the real error and response shapes are, is assumed.
- Any CSS that targets `li` clicks or the list layout was not checked.
