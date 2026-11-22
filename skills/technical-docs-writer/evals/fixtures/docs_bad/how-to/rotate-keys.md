# Rotate the signing key

Last verified: 2026-05-01 against v2.3.1

## Prerequisites

- Shell access to the worker host
- The `ops` role

## Steps

1. Generate a new key: `quillpost keys new`.
2. Copy the key id printed by the command.
3. Set the key id in the config and restart the worker.

Old setup used this access key for the test bucket: AKIAQ7ZR2LMN5TPXW4DK

See the [API reference](../reference/Api.md) for the key endpoints.
