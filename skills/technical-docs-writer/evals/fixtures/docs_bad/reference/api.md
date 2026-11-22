# Quillpost API reference

Last verified: sometime in spring

## Endpoints

### POST /v1/messages

Queues one message.

## Examples

```bash
curl -X POST https://mail.internal.example/v1/messages -d @msg.json
```

Key handling is described in [rotation](../how-to/rotate-keys.md#rollback-plan).
