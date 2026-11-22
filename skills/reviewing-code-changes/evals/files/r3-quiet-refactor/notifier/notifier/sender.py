"""Send notifications to the provider."""
from notifier.retry import with_retry
from notifier.settings import DEFAULT_TIMEOUT_S
from notifier.transport import post


def send(message):
    return with_retry(lambda: post("/v1/send", message, timeout=DEFAULT_TIMEOUT_S))


def send_batch(messages):
    return [send(message) for message in messages]
