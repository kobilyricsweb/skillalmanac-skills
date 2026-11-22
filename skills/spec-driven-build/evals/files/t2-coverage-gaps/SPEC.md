# Spec: CSV import for contacts

### REQ-001 Header required
The importer shall reject a file whose first row lacks an `email` column and import nothing.

Acceptance:
- Given a CSV with columns name,phone, when imported, then the result is error "missing email column" and 0 contacts are created.

### REQ-002 Skip invalid rows
The importer shall skip rows whose email fails basic format validation and report each skipped row number.

Acceptance:
- Given 5 rows of which rows 2 and 4 have invalid emails, when imported, then 3 contacts are created and the report lists rows 2 and 4.

### REQ-003 Duplicate emails
The importer shall update the existing contact when an email already exists, ignoring case.

Acceptance:
- Given an existing contact Ann@x.com, when a row with ann@x.com and a new name is imported, then the contact count is unchanged and the name is updated.

### REQ-004 Row limit
The importer shall reject files with more than 5,000 data rows.

Acceptance: a file with 5,001 data rows returns error "too many rows" and imports nothing.
