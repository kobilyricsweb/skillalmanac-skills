```csv
order_id,customer_name,customer_email,items,total
A-001,Dana Levi,dana@example.com,"P1 x2; P7 x1",59.9
A-002,"Smith, John",john@example.com,P3 x5,120
A-003,"Ana ""Ani"" Ruiz",,,0
```

- `items` holds every line item in one cell as `SKU xQTY`, separated by semicolons, so each order stays on one row.
- A-003 has no email and no items in the source, so those cells are empty.
- Names with commas or quotes are wrapped in quotes so Excel keeps them in one column.
