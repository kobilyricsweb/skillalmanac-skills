Synthetic input:
Roles: Editor, Guest.
Resource: article.
Operations: update, view.
Statements: Editors may update articles. Guests may view published articles.
Default rule: deny unmentioned operations.
No other exceptions or precedence clauses are supplied.

Actual artifact:

| Role | Resource | Operation | Status | Condition | Evidence |
|---|---|---|---|---|---|
| Editor | article | update | allow | none stated | Editor statement |
| Guest | article | view | conditional | article is published | Guest statement |
| Editor | article | view | deny | none | default deny |
| Guest | article | update | deny | none | default deny |

The Guest view permission does not establish access to unpublished articles. The default rule supplies the two denials shown; no other role, resource, or operation is covered by this input.
