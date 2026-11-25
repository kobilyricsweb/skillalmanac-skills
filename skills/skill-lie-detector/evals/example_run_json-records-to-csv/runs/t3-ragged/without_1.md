```csv
name,price,stock,tags,discontinued
Widget,9.5,,red;small,
Gadget,,12,blue,
Doohickey,3,0,,true
```

- Columns are the union of all keys, in first-seen order. Missing values are left empty.
- The `tags` arrays are joined with `;` so each row stays on one line.
- Source: `t3.json` in the sandbox folder. I did not write a file.
