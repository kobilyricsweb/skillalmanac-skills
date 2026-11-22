# Extract retry helper

Pure refactor: move the retry loop into `notifier/retry.py`, move the timeout into settings, rename variables for readability. No behaviour change. Also adds the index migration for the channel column.
