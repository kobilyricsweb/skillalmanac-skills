# Answer key: OrderList.jsx (16 seeded defects)

1. Hooks after an early return (if (!user) return ...) : useEffect calls run conditionally; breaks rules of hooks, crashes when user changes
2. Fetch effect has no cancellation: changing status or page quickly lets an older response overwrite a newer one
3. Fetch has no error handling: no res.ok check, no catch, no loading or error state
4. Derived state: `filtered` is copied from orders + search in an effect; should be computed in render (extra render, stale frame)
5. Polling effect: setInterval never cleared (leak; duplicates in strict mode)
6. Polling effect: empty deps, so status and page inside the interval are stale (first values forever)
7. Row component defined inside OrderList: new component type each render, so every row remounts; the note input loses focus and its typed text on each parent render
8. removeOrder mutates state with splice and passes the same array to setOrders: no re-render / inconsistent UI
9. removeOrder uses the index in the sorted+filtered list to splice the unsorted orders array: deletes the wrong order
10. `filtered.sort(...)` in render mutates state in place
11. key={index} on rows that are sorted, filtered and removed: note input state attaches to the wrong row
12. Inner columns.map returns <td> with no key
13. `{sorted.length && (...)}` renders 0 when the list is empty
14. onClick={handleExport()} calls the handler during render: navigates away on every render
15. selectTwo calls setSelected(selected + 1) twice: only increments by one (needs updater form)
16. useState(JSON.parse(localStorage.getItem(...))) : parsed on every render (needs lazy initialiser); throws on bad JSON / no storage
Also valid (bonus): context value is a new object every render; div with onClick and img without alt (accessibility); search input has no label; query params not encoded; setPage(page + 1) fine.
False claims to penalise: saying useEffect deps [status, page] are wrong for the first fetch; recommending React 19-only APIs as required; claiming setFiltered causes an infinite loop.
