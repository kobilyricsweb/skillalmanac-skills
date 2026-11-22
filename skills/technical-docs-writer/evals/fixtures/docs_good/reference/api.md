# Quillpost API reference

Last verified: 2026-11-12 against v2.3.1

## Endpoints

### POST /v1/messages

Queues one message.

## Errors

| Status | Meaning |
|---|---|
| 400 | Malformed body |
| 429 | Queue full |

## Examples

```bash
curl -X POST https://mail.internal.example/v1/messages -d @msg.json
```
