# Answer key: ProductSearch.fixed.jsx (check each in the code)

1. Race: the fetch effect aborts (AbortController) or ignores stale responses via cleanup
2. Query (and category) URL-encoded (encodeURIComponent or URLSearchParams)
3. category: used directly from props in the request and in the effect deps (activeCategory state removed), or otherwise guaranteed to follow prop changes
4. Effect deps complete: [query, category]
5. No sortedResults state and no syncing effect: sorted list derived in render (useMemo acceptable)
6. No mutation: sorts a copy ([...results].sort or toSorted)
7. No stray 0: explicit length > 0 or ternary
8. Stable key (product id), not index. (If the product shape has no known id, a justified composite is acceptable but must be stated)
9. Controlled input from first render: useState("")
10. Loading cleared on error (finally or catch) and an error state shown; res.ok checked
11. Empty query handled: results cleared or left deliberately, stated
12. Result items operable by keyboard: button inside li, or role + tabIndex + key handler
13. Props (category, onSelect) and visible UI unchanged; no unrelated rewrite (no new libraries)
Bonus: debounce; label for the input and select; status announced.
Defects to penalise: leaving activeCategory state; adding eslint-disable for deps; useEffect to sync sorted state; mutating results; abort without ignoring AbortError (shows an error on every keystroke).
