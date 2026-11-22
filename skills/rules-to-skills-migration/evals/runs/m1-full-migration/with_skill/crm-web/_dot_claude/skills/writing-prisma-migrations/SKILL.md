---
name: writing-prisma-migrations
description: Creates a Prisma migration for the crm-web database safely, previewing the SQL and blocking destructive changes. Use when the user changes prisma/schema.prisma, asks for a migration, adds, renames or drops a column or table. Do not use for seed data or for running migrations in production.
metadata:
  source: .cursor/rules/db-migration.mdc
---

# Prisma migrations

A migration that drops data cannot be undone after release.

## Workflow

1. Edit `prisma/schema.prisma`.
2. Preview the SQL first: `pnpm prisma migrate diff --from-schema-datasource prisma/schema.prisma --to-schema-datamodel prisma/schema.prisma --script`.
3. Create the migration with `pnpm prisma migrate dev --name <change>`. This needs the shadow database; start it with `pnpm db:shadow`.
4. Open the generated SQL. If it drops a column or a table, stop and split the change: add first, backfill, drop in a later release.

## Rules that always hold

- Never edit a migration that has been merged.
