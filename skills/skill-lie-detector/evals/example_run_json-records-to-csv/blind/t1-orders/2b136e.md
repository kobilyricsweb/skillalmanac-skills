I converted `t1.json` using the default join mode, so each order is one row. The file is at `orders.csv` in the working folder.

```csv
order_id,customer.name,customer.email,items,total
A-001,Dana Levi,dana@example.com,"{""sku"":""P1"",""qty"":2}; {""sku"":""P7"",""qty"":1}",59.9
A-002,"Smith, John",john@example.com,"{""sku"":""P3"",""qty"":5}",120
A-003,"Ana ""Ani"" Ruiz",,,0
```

- The `items` column holds each line item as JSON text, separated by `; `. Excel will show the raw JSON, so use Text to Columns or Power Query if you need separate sku and qty columns. The alternative, one row per item, would give more than one row per order.
- For A-003, the email is blank because it was `null`, and items is blank because the list was empty.
- I named the output `orders.csv` because you didn't give a name.
