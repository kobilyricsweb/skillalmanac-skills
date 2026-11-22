# Rotate the signing key

Last verified: 2026-11-10 against v2.3.1

## Prerequisites

- Shell access to the worker host
- The `ops` role

## Steps

1. Generate a new key: `quillpost keys new`.
2. Copy the key id printed by the command.
3. Set the key id in the config and restart the worker.

## Verify

```text
$ quillpost keys list
key-2026-11   active
key-2026-05   retired
```

The old key must show `retired`. The AWS documentation key AKIAIOSFODNN7EXAMPLE is not a real credential.

See the [API reference](../reference/api.md#endpoints).
