```csv
id,zip,phone,note
00731,02134,0501234567,=SUM(A1:A9)
00732,10001,0529876543,ok
00733,07030,0541112222,+1 call back
```

Notes:
1. **Leading zeros:** Excel strips them from `id`, `zip` and `phone` when the file is opened by double-clicking. To keep them, use Data > From Text/CSV and set those three columns to Text.
2. **Formula risk:** the `note` value `=SUM(A1:A9)` will be evaluated as a formula in Excel, not shown as text. `+1 call back` may also be read as a formula. Both should be entered as text.
3. **Conversion:** the script ran with no skipped records and no missing values. The file is saved at `<local path>`.
