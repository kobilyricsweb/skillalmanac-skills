```csv
order_id,customer_name,customer_email,items,total
A-001,Dana Levi,dana@example.com,P1 x2; P7 x1,59.9
A-002,"Smith, John",john@example.com,P3 x5,120
A-003,"Ana ""Ani"" Ruiz",,,0
```

- Each order's items are combined into one cell as `SKU x qty`, separated by semicolons, so each order stays on one row.
- A-003 has no email (blank cell) and no items (blank cell).
- The total has no currency column because the JSON doesn't include one.
