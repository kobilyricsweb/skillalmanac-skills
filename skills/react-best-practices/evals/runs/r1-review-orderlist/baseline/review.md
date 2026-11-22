# Review: OrderList.jsx

File reviewed: `OrderList.jsx` in this work folder (not modified). Line numbers refer to that file.

## Critical

### 1. Hooks called after an early return (lines 13-15 before 17, 23, 27)
- **Where:** `if (!user) return <p>...</p>;` sits above three `useEffect` calls.
- **What the user sees:** Signed-out users see the message. When `user` goes from empty to set (sign-in without a page reload), React throws "Rendered more hooks than during the previous render" and the whole page goes blank. The reverse (sign-out) also throws.
- **Fix:** Move the `if (!user)` return below every hook. Guard inside the effects instead (`if (!user) return;`), and add `user` to the dependency arrays.

### 2. Removing a row deletes the wrong order and does not visibly remove it (lines 46, 54-57, 78-79)
- **Where:** The trash icon passes `index` from the rendered `sorted` list, but `removeOrder` splices `orders`, the unfiltered and unsorted source array.
- **What the user sees:** With a search term active, or after the list is sorted by total, clicking trash on one row removes a different order. Also, `splice` mutates the state array and `setOrders(orders)` passes the same reference, so React bails out and the row stays on screen until something else re-renders. The user thinks the delete failed.
- **Fix:** Remove by stable id, not index: `setOrders(prev => prev.filter(o => o.id !== order.id))`. Make the handler immutable and call it with `order.id`. Also call the server delete endpoint if one exists; right now the deletion is local only and is undone by the next poll (see #4).

### 3. Polling interval never cleared and uses stale `status` and `page` (lines 27-33)
- **Where:** `useEffect(() => { setInterval(...) }, [])` has no cleanup and an empty dependency list.
- **What the user sees:**
  - After clicking "Next page" (page 2), every 30 seconds the list jumps back to whatever `page` was at mount (page 1). The user never stays on page 2 for long.
  - After the status filter changes, the poll keeps fetching the original status, so the list flips back to the old status.
  - Every time the component unmounts and remounts (navigating away and back), another interval is added. The old ones keep calling `setOrders` on an unmounted component, which leaks memory and keeps network traffic going.
  - In React StrictMode (dev), the effect runs twice, so two intervals run.
- **Fix:** Merge polling into the main fetch effect, keyed on `[status, page]`, and clear it in the cleanup:
  ```js
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    const load = () => fetchOrders(status, page).then(items => { if (!cancelled) setOrders(items); });
    load();
    const id = setInterval(load, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, [user, status, page]);
  ```

### 4. Race between responses and no error handling on fetch (lines 17-21, 29-31)
- **Where:** Neither fetch checks `res.ok`, catches errors, or aborts. The response is written with `setOrders(data.items)` whenever it arrives.
- **What the user sees:**
  - Click Next quickly: a slow response for page 2 can arrive after page 3 and overwrite it, so the table shows the wrong page under the page-3 label.
  - If the server returns an error body or no `items` key, `data.items` is `undefined`, `orders.filter` throws in the effect at line 24, and the page crashes. A 500 response, a timeout or an offline state all produce this.
  - On network failure the promise rejects silently and the table stays empty with no message.
- **Fix:** Use `AbortController` (or the `cancelled` flag above). Check `res.ok`, default to `data.items ?? []`, and add `.catch` that sets an error state shown to the user.

### 5. Crash on malformed localStorage (line 11)
- **Where:** `JSON.parse(localStorage.getItem("order-columns") || ...)` runs on every render (the initializer is not lazy), and throws if the stored value is not valid JSON, or is valid JSON that is not an array.
- **What the user sees:** If the stored value is corrupted (manual edit, another tool writing it, a truncated write), the component throws during render and the whole page shows an error. It stays broken on every reload because the bad value is still in storage.
- **Fix:** Use a lazy initializer with a try/catch and an `Array.isArray` check:
  ```js
  const [columns] = useState(() => {
    try {
      const v = JSON.parse(localStorage.getItem("order-columns"));
      return Array.isArray(v) ? v : ["id", "customer", "total"];
    } catch { return ["id", "customer", "total"]; }
  });
  ```

### 6. Export button calls the handler during render (line 73)
- **Where:** `<button onClick={handleExport()}>` invokes `handleExport` immediately while rendering, instead of passing it as a callback.
- **What the user sees:** The browser navigates to `/api/orders/export?...` as soon as the component renders, so the page jumps to a CSV download (or the page reloads) without the user clicking. Clicking the button does nothing extra.
- **Fix:** `<button onClick={handleExport}>`. Also encode the parameter (see #12).

## High

### 7. `Row` is defined inside `OrderList` (lines 35-52, used at 79)
- **Where:** `function Row(...)` is declared inside the component body, so each render creates a new component type.
- **What the user sees:** On every render of `OrderList` (each keystroke in the search box, each poll, each page change), React unmounts and remounts every row. Any note the user is typing in a row's input is lost mid-edit, and focus leaves the input. Remounting all rows also makes typing and scrolling slower on long pages.
- **Fix:** Move `Row` to module scope and pass `columns`, `onRemove` and `order` as props. Keep the note state inside it, keyed by `order.id`.

### 8. Notes are never saved, and the note input never resyncs (lines 36, 43)
- **Where:** `useState(order.note || "")` copies the value once. Nothing calls a save API when the note changes.
- **What the user sees:** A note typed into the row disappears on refresh or page change, and the user gets no indication it was not saved. If the server later changes `order.note` (a poll), the input keeps showing the old text, because the initial value is not updated.
- **Fix:** Save on blur or on a debounced change with a PUT/PATCH call, show a saving/saved/failed state, and sync the local value when `order.note` changes (or use `key` with the saved value).

### 9. `sorted.length && (...)` renders "0" when the list is empty (line 75)
- **Where:** When `sorted.length` is `0`, React renders the number `0` as text.
- **What the user sees:** A stray "0" appears on the page when a search has no matches or a status has no orders.
- **Fix:** `{sorted.length > 0 && (...)}`. Also show an empty-state message such as "No orders found".

### 10. Sorting mutates state and runs on every render (line 68)
- **Where:** `filtered.sort(...)` sorts the state array in place. It runs on every render, not just when the data changes.
- **What the user sees:** The state array is reordered without `setFiltered` being called, which is a React rule break and can cause inconsistent output. Sorting runs on every keystroke and poll, which is wasteful on large pages. If `total` is a string in some responses, `b.total - a.total` gives `NaN` and the order becomes unstable.
- **Fix:** `const sorted = useMemo(() => [...filtered].sort((a, b) => Number(b.total) - Number(a.total)), [filtered]);`

### 11. `filtered` is duplicated state derived in an effect (lines 7, 23-25)
- **Where:** `filtered` is set from `orders` and `search` inside a `useEffect`.
- **What the user sees:** After each change to `orders` or `search` the table shows one frame of stale rows before the effect runs, which can make the removed row in #2 flicker or reappear. It also doubles the renders.
- **Fix:** Remove the state and effect. Compute `const filtered = useMemo(() => orders.filter(...), [orders, search]);` in the render.

### 12. Crash when a customer name is missing (line 24)
- **Where:** `o.customer.toLowerCase()` throws if `customer` is `null` or `undefined`.
- **What the user sees:** One order with no customer name stops the whole table from rendering, and the search box stops working.
- **Fix:** `(o.customer ?? "").toLowerCase().includes(search.toLowerCase())`.

### 13. Button "Select next two" does not select two (lines 59-62, 74)
- **Where:** `setSelected(selected + 1)` is called twice with the same stale value, so the state only goes up by one. Also there is no selection in the UI, so the number is shown but nothing is selected.
- **What the user sees:** Each click increases the counter by 1, not 2. The label implies rows get selected, but no row changes.
- **Fix:** Either remove the feature, or implement it properly: keep a `Set` of selected ids, use a checkbox per row, and select the next two unselected rows with `setSelected(prev => ...)` (functional update).

### 14. Export and filter values are not URL-encoded (lines 18, 29, 65)
- **Where:** `status` is put into the query string as-is.
- **What the user sees:** A status with `&`, `#`, spaces or non-ASCII characters is cut off or sent under the wrong parameter, so the wrong orders or an error are shown or exported.
- **Fix:** Use `URLSearchParams` or `encodeURIComponent(status)`.

## Medium

### 15. `Next page` has no upper bound and no Previous button (line 84)
- **Where:** `setPage(page + 1)` has no check for a last page.
- **What the user sees:** Clicking Next past the last page shows an empty table with no explanation. There is no way to go back, so the user must reload.
- **Fix:** Use the total count or `data.hasMore` from the response to disable Next, and add a Previous button with `setPage(p => Math.max(1, p - 1))`.

### 16. Page does not reset when the status changes (line 21, 84)
- **Where:** Changing `status` keeps the current `page`.
- **What the user sees:** Switching to a status with fewer pages can show an empty page 5, with no message.
- **Fix:** Reset `page` to 1 when `status` changes (for example in the handler that sets status, or with a `useEffect` on `status`).

### 17. Missing `key` on `<td>` in `columns.map` (lines 39-41)
- **Where:** The mapped `<td>` has no `key`.
- **What the user sees:** Nothing visible, but React logs a "Each child in a list should have a unique key" warning in the console, and column reordering can reuse DOM nodes incorrectly.
- **Fix:** `<td key={c}>{String(order[c] ?? "")}</td>`.

### 18. Rendering object values crashes the row (line 40)
- **Where:** `{order[c]}` renders whatever the value is. If a column value is an object or array (for example a nested `customer` object from the API), React throws "Objects are not valid as a React child".
- **What the user sees:** A blank page on the first affected order.
- **Fix:** Format values explicitly, e.g. `String(order[c] ?? "")` or a per-column formatter (currency for `total`).

### 19. Key by array index on the rows (line 79)
- **Where:** `key={index}`.
- **What the user sees:** When the list is sorted, filtered or a row is removed, React reuses row components for different orders, so row-local state (the note text from #8) attaches to the wrong order.
- **Fix:** `key={order.id}`.

### 20. Columns are read but there is no UI to change them, and `setColumns` is never used (lines 11, 39)
- **Where:** `columns` comes from localStorage, but nothing writes to it.
- **What the user sees:** Nothing changes. The stored preference can only be changed by hand in devtools, and an invalid value crashes the page (#5).
- **Fix:** Either remove the feature, or add a column picker that writes the value with `localStorage.setItem` and validates against the known column names.

### 21. Context value is recreated every render with no consumer (lines 71)
- **Where:** `OrdersContext.Provider value={{ orders, setOrders }}` builds a new object on every render. Nothing in this file or the provided code uses the context.
- **What the user sees:** Nothing directly. Any future consumer re-renders on every parent render.
- **Fix:** Remove the provider if unused, or memoize the value with `useMemo`.

### 22. Trash icon is not keyboard-accessible and has no alt text (lines 46-47)
- **Where:** A `<div onClick>` is used as the delete control, and `<img>` has no `alt`.
- **What the user sees:** Keyboard and screen-reader users cannot tell or operate the delete control. Sighted users get no hover or focus state.
- **Fix:** `<button type="button" aria-label="Delete order" onClick={...}><img src="/icons/trash.svg" alt="" /></button>`.

### 23. Inputs and buttons have no accessible names (lines 43, 72-74, 84)
- **Where:** The note input has no label. The search input has only a placeholder. Buttons without `type` default to `submit` if placed in a form later.
- **What the user sees:** Screen readers announce unnamed controls. Placeholder text disappears when typing.
- **Fix:** Add `aria-label` to each input and `type="button"` to each button.

## Low

### 24. Dead and unused state (lines 10, 11)
- `selected` only feeds the broken "Select next two" button (see #13).
- `setColumns` is unused (see #20).

### 25. Unhelpful naming and a file-level export mix (lines 3, 68)
- `OrdersContext` is exported from a component file. This makes React Fast Refresh reload the whole module on each edit instead of just the component. Consider moving it to its own file.
- `sorted` and `filtered` are named as if they were the only data; `orders` is the server page, which is easy to confuse with the visible rows.

### 26. Unused `React` import style note
- `import React` is not needed with the React 17+ JSX transform. Harmless.

## Summary of the most impactful fixes

1. Move the `if (!user)` return below all hooks (#1).
2. Delete rows by `order.id`, immutably, and call the server (#2).
3. Replace the interval with one effect keyed on `[user, status, page]` that cleans up and ignores stale responses (#3, #4).
4. Lift `Row` out of the component, and key rows by `order.id` (#7, #19).
5. Fix the export button to pass a function, not call it (#6).
6. Guard the empty-list `0` and the null `customer` (#9, #12).
