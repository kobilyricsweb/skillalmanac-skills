# Worked Example

Synthetic example; all names and values below are invented for this example only.

Input:

- Error `album_missing`: request `GET /albums/{id}` with documented field `id=42`; status `404`; body `{"code":"ALBUM_NOT_FOUND"}`; policy says show “Album unavailable” and use an empty state.
- Error `quota_hit`: request `POST /albums/search` with documented field `query=rain`; status `429`; body `{"code":"RATE_LIMITED"}`; no recovery policy supplied.
- Error `bad_query`: request `POST /albums/search` with documented field `query`; status `400`; body `{"code":"INVALID_QUERY"}`; policy says display the validation message; no fallback supplied.

Expected artifact:

The scope states that this is an offline illustration, and the assumptions state that no request was executed. The scenario matrix contains one row for each error, reproducing supplied requests, statuses, and bodies. `album_missing` has the supplied empty-state fallback; `quota_hit` and `bad_query` have unknown fallbacks. Missing-guidance findings identify that `quota_hit` lacks recovery guidance and that `bad_query` lacks a fallback. Conflicts are empty, and acceptance checks cover error coverage, documented fields, faithful reproduction, explicit unknowns, and non-execution.

Finding: `quota_hit` lacks recovery guidance. The artifact must not claim that waiting, retrying, or backoff is safe.
