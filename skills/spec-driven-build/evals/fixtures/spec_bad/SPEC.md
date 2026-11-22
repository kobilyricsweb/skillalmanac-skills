# Spec: invoice export

### REQ-001 Export as CSV
The system shall export invoices as CSV.

Acceptance:
- Given 3 invoices, when the user clicks Export, then a CSV with 3 data rows downloads.

### REQ-002 Fast export
Exports should be fast and easy to use. Maximum size TBD.

### REQ-003 Date filter
The user can filter invoices by date range before export.

Acceptance:
- Given invoices in March and April, when the filter is March, then only March rows are exported.

### REQ-004 Currency column
The export shall include a currency column.

Acceptance: every row has a three letter ISO currency code.

### REQ-003 Duplicate id
Accidentally reused id.
Acceptance: not applicable here at all.

### REQ-006 Email the export [deferred]
Out of this release.
