```csv
name,price,tags,stock,discontinued
Widget,9.5,red;small,,
Gadget,,blue,12,
Doohickey,3,,0,true
```

- `tags` is a list, so its values are joined with `;` inside the cell.
- Columns follow the order keys first appear in the file. Missing keys are left empty.
- The source file has no header row to take names from, so the columns come from the object keys.
