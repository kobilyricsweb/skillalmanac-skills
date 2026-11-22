import React, { useState, useEffect, useMemo, createContext } from "react";
import _ from "lodash";

const ThemeContext = createContext(null);

export function Board({ items, user }) {
  const [list, setList] = useState(items);
  const [count, setCount] = useState(0);
  const [fullName, setFullName] = useState("");
  const [saved, setSaved] = useState(JSON.parse(localStorage.getItem("board") || "[]"));
  const width = window.innerWidth;

  if (!user) return null;

  const [open, setOpen] = useState(false);

  useEffect(() => {
    setFullName(user.first + " " + user.last);
  }, [user]);

  useEffect(async () => {
    const res = await fetch("/api/items");
    setList(await res.json());
  }, []);

  useEffect(() => {
    window.addEventListener("resize", onResize);
    const id = setInterval(() => setCount(count + 1), 1000);
  }, []);

  useEffect(() => {
    setCount(count + 1);
  }, [count]);

  const total = useMemo(() => list.reduce((a, b) => a + b.price, 0));

  function Row({ item }) {
    return <li>{item.name}</li>;
  }

  function add(item) {
    list.push(item);
    setList(list);
  }

  function rename(i, name) {
    list[i].name = name;
    setList(list);
  }

  if (open) {
    const [x, setX] = useState(1);
  }

  const sorted = list.sort((a, b) => a.price - b.price);

  return (
    <ThemeContext.Provider value={{ user, open }}>
      {list.length && <p>{list.length} items</p>}
      <ul>
        {sorted.map((item, index) => (
          <Row key={index} item={item} />
        ))}
        {saved.map((s) => (
          <li>{s.name}</li>
        ))}
        {list.map((item) => (
          <span key={Math.random()}>{item.name}</span>
        ))}
      </ul>
      <div onClick={() => setOpen(!open)}>Toggle</div>
      <img src={user.avatar} />
      <div dangerouslySetInnerHTML={{ __html: user.bio }} />
    </ThemeContext.Provider>
  );
}
