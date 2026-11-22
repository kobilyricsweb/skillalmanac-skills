# Spec format for scripts/size_model.py

One JSON object. Numbers must be plain JSON numbers greater than zero unless noted.

```json
{
  "model": {
    "name": "my-model-8b",
    "params_b": 8,
    "moe": false,
    "active_params_b": null,
    "layers": 32,
    "kv_heads": 8,
    "head_dim": 128,
    "trained_context": 131072
  },
  "context": 8192,
  "kv_dtype": "f16",
  "use": "chat",
  "hardware": [
    {
      "name": "desktop",
      "os": "windows",
      "vram_gb": 24,
      "gpus": 1,
      "split_layers": false,
      "ram_gb": 32,
      "gpu_bandwidth_gbps": 900,
      "ram_bandwidth_gbps": 50,
      "unified": false,
      "os_reserve_gb": 4
    }
  ]
}
```

## model

| Field | Required | Meaning |
|---|---|---|
| name | no | Label for the report |
| params_b | yes | Total parameters in billions |
| moe | no | true for a mixture-of-experts model |
| active_params_b | MoE only | Parameters used per token, in billions; must be below params_b |
| layers, kv_heads, head_dim | no | Architecture facts from the model card. If any is missing the KV estimate is flagged approximate |
| trained_context | no | Longest context the model was trained for; a larger request triggers a warning and caps `max_context` |

## Top level

| Field | Default | Values |
|---|---|---|
| context | required | Tokens the user wants to hold |
| kv_dtype | f16 | f16, q8_0, q4_0 |
| use | chat | chat (working minimum 8192), coding (16384), long_documents (32768); a smaller context warns |
| kv_bytes_per_element | none | Optional cross-check; a value that disagrees with kv_dtype produces a warning and the dtype wins |

## hardware[] entries

| Field | Default | Meaning |
|---|---|---|
| name | machine N | Label |
| os | linux | windows, macos or linux; selects the OS reserve (4, 4, 2 GB) |
| vram_gb | 0 | Per-GPU memory; 0 or absent means no discrete GPU (negative is rejected) |
| gpus | 1 | Count; only counted past one when split_layers is true |
| split_layers | false | Set true only when the user confirms layers can be split across the GPUs |
| ram_gb | required | System RAM; for Apple silicon this is the unified pool |
| unified | false | true for Apple silicon and similar shared-memory machines |
| gpu_bandwidth_gbps | none | Memory bandwidth of the GPU (or of unified memory) in GB/s; without it no speed ceiling for GPU runs |
| ram_bandwidth_gbps | none | System RAM bandwidth in GB/s; needed for cpu_only and partial_offload speed |
| os_reserve_gb | by os | Override the OS reserve |

## Output keys

Top level: `inputs` (echo plus assumptions), `warnings[]`, `hardware[]`. Each hardware entry: `name`, `fast_pool_gb`, `slow_pool_gb`, `os_reserve_gb`, `warnings[]`, `per_quant[]`, `recommendation[]` (three lines). Each per_quant row: `quant`, `bits_per_weight`, `bits_per_weight_status`, `quality_note`, `weights_gb`, `kv_gb`, `activation_gb`, `total_gb`, `needed_with_headroom_gb`, `verdict`, `tokens_per_second_ceiling`, `speed_class`, `max_context`, `max_context_with_offload`, `warnings[]`; partial offload rows also carry `approx_gpu_share` and, with layers known, `approx_gpu_layers`.

`max_context` is the largest context that still passes the headroom rule in the memory the model runs from first (VRAM or unified pool, or RAM when there is no GPU), capped at trained_context. `max_context_with_offload` uses VRAM plus RAM.
