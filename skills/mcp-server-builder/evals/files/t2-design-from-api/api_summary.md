# Internal "Shelf" inventory API (summary)

Base: https://shelf.internal.example/api/v2. Auth: bearer token, one per service account.

- GET /items?q=&category=&page=&per_page= returns items (id, sku, name, qty, location). per_page max 500.
- GET /items/{id} returns one item with history (up to 10,000 events).
- POST /items creates an item (sku, name, qty, location). Not idempotent: posting the same sku twice creates two rows.
- PATCH /items/{id}/qty adjusts quantity by a signed delta.
- DELETE /items/{id} deletes an item and its history. No undo.
- POST /reports/stocktake starts a stocktake job and returns a job id; jobs take 2 to 20 minutes. GET /reports/stocktake/{job} returns status and, when done, a CSV link.

The server will run on a developer laptop for one warehouse manager who uses a desktop assistant.
