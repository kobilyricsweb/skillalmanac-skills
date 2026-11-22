I have a MacBook with 64 GB of unified memory (about 400 GB/s). I want a 30B mixture-of-experts model with 3B active parameters (48 layers, 4 KV heads, head dim 128, trained for 131072 tokens) to summarise long documents at 32768 context, f16 KV cache.

Does it fit? Which quant? I read that 30B models are slow, is that true here?
