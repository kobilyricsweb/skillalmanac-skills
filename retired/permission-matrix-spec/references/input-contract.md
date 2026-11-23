Required input fields:
- roles;
- resources;
- operations;
- permission statements;
- conditions and exceptions;
- source labels;
- any explicit default rule, such as default deny.

If a dimension is missing, report it and limit the matrix to supported combinations. If statements conflict, preserve each source and mark the cell conflict unless supplied precedence resolves it. An absent allow statement is unspecified by default; it becomes deny only when an explicit default-deny rule applies. Conditions must remain attached to the exact scope documented.

The output must contain a role-resource-operation matrix with status, condition, and evidence, plus unresolved conflicts and assumptions. The result specifies a documentary model only. It does not alter access controls, test runtime authorization, or infer permissions from titles or organizational position.
