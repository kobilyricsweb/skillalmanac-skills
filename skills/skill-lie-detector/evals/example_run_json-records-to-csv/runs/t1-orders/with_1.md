```csv
order_id,customer_name,customer_email,items,total
A-001,Dana Levi,dana@example.com,P1 x2; P7 x1,59.9
A-002,"Smith, John",john@example.com,P3 x5,120
A-003,"Ana ""Ani"" Ruiz",,,0
```

- **Items:** Each order has a variable number of line items, so they're packed into one `items` cell as `SKU xQty`, separated by semicolons, to keep one row per order.
- **Blanks:** A-003 has no email (`null` in the JSON) and no items, so those cells are empty.
- **Quoting:** Names with commas or quotes are quoted per CSV rules, so Excel keeps them in one cell.
