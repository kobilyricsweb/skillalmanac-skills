```csv
id,zip,phone,note
00731,02134,0501234567,=SUM(A1:A9)
00732,10001,0529876543,ok
00733,07030,0541112222,+1 call back
```

Notes:
- Excel strips leading zeros when it opens a CSV by default, so `00731` would show as `731`. Import with Data > From Text/CSV and set the `id`, `zip` and `phone` columns to Text.
- The `note` cell on row 1 (`=SUM(A1:A9)`) and row 3 (`+1 call back`) may be read by Excel as formulas. Set `note` to Text too, or prefix those values with an apostrophe.
- You didn't name an output file, so I saved it as `<local path>`. The script reported 3 rows, 4 columns, 0 missing values and 0 skipped records.
