import { useEffect, useMemo, useState } from "react";

type Item = { id: string; name: string; price: number };

function useItems(query: string) {
  const [items, setItems] = useState<Item[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    fetch(`/api/items?q=${encodeURIComponent(query)}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.json();
      })
      .then((data: Item[]) => {
        setItems(data);
        setStatus("ready");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setStatus("error");
      });
    return () => controller.abort();
  }, [query]);

  return { items, status };
}

function Row({ item, onRemove }: { item: Item; onRemove: (id: string) => void }) {
  return (
    <li>
      {item.name} <button type="button" onClick={() => onRemove(item.id)}>Remove {item.name}</button>
    </li>
  );
}

export function Board({ query }: { query: string }) {
  const { items, status } = useItems(query);
  const [removed, setRemoved] = useState<string[]>([]);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const visible = useMemo(
    () => items.filter((i) => !removed.includes(i.id)).toSorted((a, b) => a.price - b.price),
    [items, removed],
  );

  if (status === "loading") return <p>Loading items</p>;
  if (status === "error") return <p role="alert">Could not load items. Try again.</p>;

  return (
    <section>
      {visible.length > 0 ? (
        <ul>
          {visible.map((item) => (
            <Row key={item.id} item={item} onRemove={(id) => setRemoved((prev) => [...prev, id])} />
          ))}
        </ul>
      ) : (
        <p>No items match. It's quiet here.</p>
      )}
      <p>Window width {width}px</p>
    </section>
  );
}
