Synthetic input: The template has placeholders {{client_name}} and {{invoice_date}}. Candidate sources are customer.display_name=“Rina Cole” and invoice.created_at=“2026-11-20T14:00:00Z”. The only mapping policy explicitly supplied is “client_name maps to customer.display_name.” No policy maps invoice_date, and no date-format rule is supplied.

Artifact:
- client_name: candidate customer.display_name; selected source customer.display_name; status bound; transform none; value may be read as “Rina Cole.”
- invoice_date: candidate invoice.created_at; selected source unknown; status unresolved; transform none; missing behavior unknown because no policy was supplied.

Review note: The timestamp is retained as a candidate but is not used. The map does not use today’s date, infer equivalence from the names, fill the template, or send a document.
