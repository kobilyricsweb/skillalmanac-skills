```csv
name,price,tags,stock,discontinued
Widget,9.5,red; small,,
Gadget,,blue,12,
Doohickey,3,,0,true
```

- I wrote the file as `<local path>`. You didn't name an output file, so I chose `t3.csv`.
- 3 rows, 5 columns, all 3 items converted with none skipped. Tags are joined with `; ` (default join mode).
- 5 of 15 cells are blank (33%), above the 25% threshold. The most blank column is `discontinued` (2 blanks). `stock`, `price` and `tags` each have 1 blank.
