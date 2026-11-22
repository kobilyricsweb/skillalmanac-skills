import { useEffect, useState } from "react";

// Props: category (string, changes when the user picks a category in the sidebar),
//        onSelect(product) is called when a result is clicked.
export default function ProductSearch({ category, onSelect }) {
  const [query, setQuery] = useState();
  const [activeCategory, setActiveCategory] = useState(category);
  const [results, setResults] = useState([]);
  const [sortedResults, setSortedResults] = useState([]);
  const [sortBy, setSortBy] = useState("name");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    fetch(`/api/products?q=${query}&category=${activeCategory}`)
      .then((res) => res.json())
      .then((data) => {
        setResults(data);
        setLoading(false);
      });
  }, [query]);

  useEffect(() => {
    const copy = results;
    copy.sort((a, b) => (sortBy === "price" ? a.price - b.price : a.name.localeCompare(b.name)));
    setSortedResults(copy);
  }, [results, sortBy]);

  return (
    <div className="product-search">
      <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search products" />
      <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
        <option value="name">Name</option>
        <option value="price">Price</option>
      </select>
      {loading && <p>Loading</p>}
      {sortedResults.length && (
        <ul>
          {sortedResults.map((p, i) => (
            <li key={i} onClick={() => onSelect(p)}>
              {p.name} ${p.price}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
