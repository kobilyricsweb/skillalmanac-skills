I want to run an 8B dense model (32 layers, 8 KV heads, head dim 128, trained for 131072 tokens) for chat at 8192 context with the default f16 KV cache.

Machine A: Windows desktop, 24 GB VRAM (about 900 GB/s), 32 GB RAM (about 50 GB/s).
Machine B: Windows laptop, 8 GB VRAM (about 300 GB/s), 16 GB RAM (about 50 GB/s).

Which quant should I use on each, and will it be fast?
