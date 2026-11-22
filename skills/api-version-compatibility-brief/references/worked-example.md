Synthetic input:
Version 1: POST /profiles requires name:string; documented success response is 200.
Version 2: POST /profiles requires display_name:string; documented success response is 201. No rename note is supplied. No other behavior notes are supplied.

Actual artifact:

| Contract element | v1 | v2 | Classification |
|---|---|---|---|
| Request field name | required string | absent | removed from supplied v2 contract |
| Request field display_name | absent | required string | added to supplied v2 contract |
| Success status | 200 | 201 | changed |
| Rename intent | not stated | not stated | behaviorally uncertain |

Conclusion: the field contracts are not documented as unchanged because the required field name differs. The two fields may represent a rename, but the supplied specifications do not establish that intent. No claim is made about runtime compatibility, other status codes, or migration behavior.
