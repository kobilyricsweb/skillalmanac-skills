"""Retry helper shared by the senders."""
import time

MAX_ATTEMPTS = 3


def with_retry(call):
    attempt = 0
    while True:
        attempt += 1
        try:
            return call()
        except Exception:
            if attempt >= MAX_ATTEMPTS:
                raise
            time.sleep(0.01 * attempt)
