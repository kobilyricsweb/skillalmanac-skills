# workspace-database-schema-planner

## One line

Plans a workspace as linked databases: entities, property types, relations and role-based views, delivered as tables plus a Mermaid diagram.

## What it does

The skill takes three inputs: the purpose of a workspace, the list of things it tracks, and the three questions the team must answer each week. It then works through a fixed seven-step procedure. It decides which things deserve their own database, which are only a property of another database, and which fields need a type. For each field it applies a threshold table: a select holds up to 12 options, a multi-select up to 20, and anything longer becomes a relation to its own database. It chooses the relation cardinality, gives every relation a reverse property, and removes any field that repeats a fact another field already holds. Each database then gets at most three views, and each view serves one named audience. The reply always uses the same seven headings, so a reviewer can compare two plans side by side.

## When to use

Use it when a workspace has grown into several tables that repeat the same names, when a content calendar, CRM, project tracker or inventory needs linked databases, or when you cannot decide between a select, a relation and a text field for one field.

## When not to use

Do not use it to write page text, copy or content templates, to build automations, or to change a workspace that already exists. It does not know which paid plan a team has, and it leaves plan-specific features out of the schema. It produces a plan only.

## Requirements

A text-capable agent. The package contains no scripts and needs no network access.

## Example

Excerpt from the smoke run (content calendar with posts, authors and campaigns), taken from the reply that followed SKILL.md:

```
### Relations
| From | Property | To | Cardinality | Reverse property |
|---|---|---|---|---|
| Posts | Author | Authors | one-to-many | Posts (on Authors) |
| Posts | Campaign | Campaigns | one-to-many | Posts (on Campaigns) |

### Diagram
erDiagram
  AUTHORS ||--o{ POSTS : "writes"
  CAMPAIGNS ||--o{ POSTS : "groups"
```

## Limits

The thresholds (8 databases, 12 select options, 20 multi-select options, 3 views per database, 3 levels of nesting) are working values chosen for this version, not published standards. The skill checks only the structure of its own output. It cannot confirm that a plan works in a real workspace, and it does not check whether a target tool supports a given rollup filter. A team still needs to build the schema and test it with real rows.

## Status

Provisional. Lint-clean, one smoke run. Not independently verified.
