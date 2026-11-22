# ProductSearch fixes

File: `ProductSearch.fixed.jsx` (same props `{ category, onSelect }`, same markup and class names).

## Bugs and changes

1. **Old results flashing over new ones (race condition).**
   The fetch effect had no cancellation, so a slow response for an older query could
   land after a newer one and overwrite it. Each request now has an `AbortController`,
   and the effect cleanup aborts the previous request when the inputs change or the
   component unmounts. `AbortError` is ignored in the catch.

2. **Stray `0` on the page.**
   `{sortedResults.length && (...)}` renders `0` when the array is empty, because `0`
   is a React-renderable value. Changed to `sortedResults.length > 0 && (...)`.

3. **Results not updating when the category changes.**
   The effect depended only on `[query]`, and `activeCategory` was copied from the prop
   once with `useState(category)` and never synced, so it went stale. Removed
   `activeCategory`; the effect now reads `category` directly and depends on
   `[query, category]`.

4. **Uncontrolled input warning.**
   `useState()` made `query` `undefined`, so the input started uncontrolled and then
   became controlled. Initial state is now `""`.

Additional fixes found while in the code:

- **Sorting mutated state and lagged one render.** The old second effect sorted
  `results` in place (`const copy = results` is the same array) and then stored the
  result in another state variable, so one render showed unsorted rows. Sorting is now
  a `useMemo` over `[...results]`, which is pure and runs in the same render.
- **Query and category were not URL-encoded.** A query such as `a&b` or `rock #1`
  broke the request. Both values now go through `encodeURIComponent`. `category` falls
  back to `""` when it is undefined, instead of sending the literal `undefined`.
- **Empty query kept stale results and could leave `loading` stuck.** An empty
  (or whitespace-only) query now clears results and loading. A non-OK HTTP status or
  network error also clears results and stops loading, instead of leaving the spinner
  on forever (the old code had no `.catch`).
- **Non-array response.** Non-array JSON is treated as no results so `.map` can't throw.
- **List key.** Uses `p.id` when present and falls back to the index.
- **`name` null safety.** The name comparison coerces missing names to `""`.

## Not verified

No test run was done. The file is a drop-in replacement for the original. Two
assumptions to confirm against the real API: the `/api/products` response is a JSON
array, and `category` may be an empty string when unset.
