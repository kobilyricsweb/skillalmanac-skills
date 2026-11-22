# Why Quillpost uses a queue

## Background

Direct sends made request latency depend on the mail provider.

## How it works

Services write a row; workers claim rows in batches and mark them sent.

## Trade-offs

Delivery is at least once, so receivers must tolerate duplicates.
