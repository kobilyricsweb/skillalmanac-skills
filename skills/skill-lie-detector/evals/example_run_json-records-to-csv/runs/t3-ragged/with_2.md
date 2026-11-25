```csv
name,price,tags,stock,discontinued
Widget,9.5,red; small,,
Gadget,,blue,12,
Doohickey,3,,0,true
```

Notes:
- Saved as `<local path>`. You didn't name an output file, so I used `t3.csv` next to the input. Tags are joined with `; ` (default mode).
- All 3 records converted, none skipped. 5 of 15 cells are blank (33%), above the 25% threshold. The most blank column is `discontinued` (2 blanks). `price`, `stock`, and `tags` each have 1.
- The CSV has 5 columns; `discontinued` appears only on the third record, and `tags` is missing on that record.
