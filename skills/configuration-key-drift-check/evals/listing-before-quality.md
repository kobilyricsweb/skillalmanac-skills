# configuration-key-drift-check

Status: unpublished free candidate; no score or verification badge.

## One Line

Compare declared required and optional configuration key names with named configurations and expose drift.

## Audience

Maintainers, release engineers, and configuration reviewers.

## Benefit

Finds missing, unexpected, and duplicated key names before configuration changes are promoted.

## Limits

Key names only; no files, secret values, runtime checks, semantic validation, or compatibility guarantees.

## Synthetic Example

Required PORT, optional DEBUG, and prod keys PORT produce no findings.
