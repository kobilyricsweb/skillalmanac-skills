import React, { useState, useEffect, createContext } from "react";

export const OrdersContext = createContext(null);

export default function OrderList({ user, status }) {
  const [orders, setOrders] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState(0);
  const [columns, setColumns] = useState(JSON.parse(localStorage.getItem("order-columns") || '["id","customer","total"]'));

  if (!user) {
    return <p>Please sign in to see orders.</p>;
  }

  useEffect(() => {
    fetch(`/api/orders?status=${status}&page=${page}`)
      .then((res) => res.json())
      .then((data) => setOrders(data.items));
  }, [status, page]);

  useEffect(() => {
    setFiltered(orders.filter((o) => o.customer.toLowerCase().includes(search.toLowerCase())));
  }, [orders, search]);

  useEffect(() => {
    setInterval(() => {
      fetch(`/api/orders?status=${status}&page=${page}`)
        .then((res) => res.json())
        .then((data) => setOrders(data.items));
    }, 30000);
  }, []);

  function Row({ order, index }) {
    const [note, setNote] = useState(order.note || "");
    return (
      <tr>
        {columns.map((c) => (
          <td>{order[c]}</td>
        ))}
        <td>
          <input value={note} onChange={(e) => setNote(e.target.value)} />
        </td>
        <td>
          <div className="link" onClick={() => removeOrder(index)}>
            <img src="/icons/trash.svg" />
          </div>
        </td>
      </tr>
    );
  }

  function removeOrder(index) {
    orders.splice(index, 1);
    setOrders(orders);
  }

  function selectTwo() {
    setSelected(selected + 1);
    setSelected(selected + 1);
  }

  function handleExport() {
    window.location.href = `/api/orders/export?status=${status}`;
  }

  const sorted = filtered.sort((a, b) => b.total - a.total);

  return (
    <OrdersContext.Provider value={{ orders, setOrders }}>
      <input placeholder="Search customer" value={search} onChange={(e) => setSearch(e.target.value)} />
      <button onClick={handleExport()}>Export CSV</button>
      <button onClick={selectTwo}>Select next two ({selected})</button>
      {sorted.length && (
        <table>
          <tbody>
            {sorted.map((order, index) => (
              <Row key={index} order={order} index={index} />
            ))}
          </tbody>
        </table>
      )}
      <button onClick={() => setPage(page + 1)}>Next page</button>
    </OrdersContext.Provider>
  );
}
