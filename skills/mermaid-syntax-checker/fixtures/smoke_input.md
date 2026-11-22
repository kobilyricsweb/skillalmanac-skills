# Release notes draft

The first diagram shows the review flow. Its subgraph is never closed.

```mermaid
flowchart TD
    A[Start] --> B{Check}
    subgraph Group
        C[Step one] --> D[Step two]
    B -->|yes| C
```

The second diagram shows data intake. Its square bracket is never closed.

```mermaid
flowchart LR
    X[Input --> Y[Output]
```
