import { useEffect, useState } from "react";

// Props: category (string, changes when the user picks a category in the sidebar),
//        onSelect(product) is called when a result is clicked.
export default function ProductSearch({ category, onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [sortBy, setSortBy] = useState("name");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      setResults([]);
      setLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const url =
      `/api/products?q=${encodeURIComponent(term)}` +
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
        // An aborted request was superseded by a newer query or category; its result is discarded.
        if (err.name === "AbortError") return;
        setResults([]);
        setError("Could not load products.");
        setLoading(false);
      });

    return () => controller.abort();
  }, [query, category]);

  // Derived during render: no mirrored state and no mutation of the fetched array.
  const sortedResults = [...results].sort((a, b) =>
    sortBy === "price" ? a.price - b.price : a.name.localeCompare(b.name)
  );

  return (
    <div className="product-search">
      <input
        aria-label="Search products"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search products"
      />
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        <option value="name">Name</option>
        <option value="price">Price</option>
      </select>
      {loading && <p role="status">Loading</p>}
      {error && <p role="alert">{error}</p>}
      {sortedResults.length > 0 && (
        <ul>
          {sortedResults.map((p, i) => (
            <li key={p.id ?? i}>
              <button type="button" onClick={() => onSelect(p)}>
                {p.name} ${p.price}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
