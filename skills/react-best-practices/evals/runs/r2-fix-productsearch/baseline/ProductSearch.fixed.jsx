import { useEffect, useMemo, useState } from "react";

// Props: category (string, changes when the user picks a category in the sidebar),
//        onSelect(product) is called when a result is clicked.
export default function ProductSearch({ category, onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [sortBy, setSortBy] = useState("name");
  const [loading, setLoading] = useState(false);

  // Fetch whenever the query OR the category changes. Each request gets its own
  // AbortController; when inputs change (or the component unmounts) the previous
  // request is aborted, so a slow old response can never overwrite newer results.
  useEffect(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    const url =
      `/api/products?q=${encodeURIComponent(trimmed)}` +
      `&category=${encodeURIComponent(category ?? "")}`;

    fetch(url, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setResults(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        if (err.name === "AbortError") return; // superseded by a newer request
        setResults([]);
        setLoading(false);
      });

    return () => controller.abort();
  }, [query, category]);

  // Derived, not stored in state: sorting happens in the same render as the
  // results (no one-render lag showing unsorted rows), and we sort a copy so
  // the results array held in state is never mutated.
  const sortedResults = useMemo(() => {
    const copy = [...results];
    copy.sort((a, b) =>
      sortBy === "price"
        ? a.price - b.price
        : String(a.name ?? "").localeCompare(String(b.name ?? ""))
    );
    return copy;
  }, [results, sortBy]);

  return (
    <div className="product-search">
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search products" />
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        <option value="name">Name</option>
        <option value="price">Price</option>
      </select>
      {loading && <p>Loading</p>}
      {/* Use an explicit boolean: `length && ...` renders a stray "0" when empty. */}
      {sortedResults.length > 0 && (
        <ul>
          {sortedResults.map((p, i) => (
            <li key={p.id ?? i} onClick={() => onSelect(p)}>
              {p.name} ${p.price}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
