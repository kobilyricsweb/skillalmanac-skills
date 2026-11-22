# Quillpost

Quillpost is a small queue worker that delivers outbound email for internal services and retries failures.

## Install

```bash
pip install quillpost==2.3.1
```

## Usage

```bash
quillpost run --config quillpost.toml
```

Rotate keys with the [how-to](how-to/rotate-keys.md#steps). Report text lives in [docs](explanation/why-queues.md).

## License

Apache-2.0.
