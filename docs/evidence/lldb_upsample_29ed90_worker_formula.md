# LLDB Evidence: `0x29ed90` Upsample Worker Formula

## Scope

This note follows the callback worker constructed by `0x29ed90`, the builder
already proven to produce the internally depth-labeled `UpsampleLayer+0x90`
descriptor.

It builds on:

- [lldb_upsample_layer_depth_path.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_layer_depth_path.md)
- [lldb_upsample_map_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_map_custody.md)

It proves:

- the callback object built by `0x29ed90` uses vtable address point `0x668288`
- vtable slot `+0x30` is `0x29f5c0`, and `0x29f5c0` tail-jumps to worker body
  `0x29f600` after adding `8` to the callback object pointer
- accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs all execute the
  `0x29f5c0 -> 0x29f600` worker path and reach output float store `0x29f9de`
- the callback payload layout, runtime descriptor shapes, coefficient table,
  scalar scale, and static worker arithmetic are now bounded

It does not assign public LRI field names or calibration schema names to the
worker inputs.

## Artifacts

- Static script:
  [static_worker_vtable.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/static_worker_vtable.lldb)
- Runtime probe:
  [upsample_29ed90_worker_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/upsample_29ed90_worker_probe.py)
- Runtime LLDB scripts:
  [worker_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/worker_28mm.lldb),
  [worker_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/worker_35mm.lldb),
  [worker_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/worker_70mm.lldb),
  [worker_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_29ed90_worker/worker_150mm.lldb)
- Raw static output:
  `runs/upsample_29ed90_worker/static_worker_vtable.log`
- Raw runtime outputs:
  `runs/upsample_29ed90_worker/worker_28mm.{log,json}`,
  `runs/upsample_29ed90_worker/worker_35mm.{log,json}`,
  `runs/upsample_29ed90_worker/worker_70mm.{log,json}`,
  `runs/upsample_29ed90_worker/worker_150mm.{log,json}`

Repo-local scan found no `Traceback`, `error:`, `warning:`,
`lost connection`, `EXC`, or `SIGABRT` entries in the accepted logs. All four
runtime JSON reports have empty `errors` arrays.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

- `0x29ed90` builds a callback object whose vtable address point is `0x668288`.
- Static vtable memory at `0x668288` begins:

```text
0x668288: 0x29f510 0x29f520 0x29f530 0x29f570
0x6682a8: 0x29f5a0 0x29f5b0 0x29f5c0 0x29f5d0
0x6682c8: 0x29f5f0 ...
```

- Slot `+0x30` is therefore `0x29f5c0`.
- `0x29f5c0` performs `rdi += 8` and tail-jumps to `0x29f600`.
- `0x29f600` iterates over the passed rectangle:
  `x = rect[0]..rect[2]-1`, `y = rect[1]..rect[3]-1`.
- `0x29f6f3` reads a 4-byte high-resolution pixel from payload field `+0x00`
  with `pmovzxbd`.
- `0x29f7d8` and `0x29f85b` read 4-byte low-resolution auxiliary pixels from
  payload field `+0x20` with `pmovzxbd`.
- `0x29f964` and `0x29f993` read low-resolution source floats from payload
  field `+0x08`.
- `0x29f701` reads one float scale from payload field `+0x18`.
- `0x29f740`, `0x29f772`, `0x29f7e5`, and surrounding instructions read
  spatial coefficients from payload field `+0x10`.
- `0x29f9de` stores one output float into payload field `+0x28`.

Static constants used by the body include:

| Address | Value(s) | Use proven by instruction context |
|---|---|---|
| `0x5a8120` | `-0.5`, `-1`, `1`, `0` nearby | coordinate centering and clamp constants |
| `0x5a8990` | `-126` repeated | lower clamp bound for the negative scaled color-distance term |
| `0x5a89a0` | `128` repeated | upper clamp bound for the negative scaled color-distance term |
| `0x5dae2c` | `0.0780245215`, `0.226067156`, `0.695833564`, `0.999925196` | cubic mantissa / bit-level exponential-approximation constants |
| `0x5dce90` | `9.99999993e-9` | epsilon added to each bilateral weight |

## Runtime Payload Layout

All accepted runs exited with process status `0` and did not hit the drive step
cap. Worker/vtable/store counts are capped sample counts, not full-render
totals.

| Zoom | Builder | Dispatch | Vtable slot cap | Worker cap | Store cap | JSON errors |
|---|---:|---:|---:|---:|---:|---|
| `28mm` | `1` | `1` | `8` | `8` | `16 pre / 16 post` | `0` |
| `35mm` | `1` | `1` | `8` | `8` | `16 pre / 16 post` | `0` |
| `70mm` | `1` | `1` | `8` | `8` | `16 pre / 16 post` | `0` |
| `150mm` | `1` | `1` | `8` | `8` | `16 pre / 16 post` | `0` |

The callback object has seven qwords:

| Object field | Runtime role proven by static reads and runtime descriptor probes |
|---|---|
| `+0x00` | vtable address point `0x668288` |
| `+0x08` | high-resolution 4-byte-pixel descriptor, `4160 x 3120`, stride `4160` |
| `+0x10` | low-resolution float source descriptor, `2080 x 1560`, stride `2080` |
| `+0x18` | coefficient table pointer; first two floats are `1.0`, `0.3333333432674408` |
| `+0x20` | scale pointer; first float is `0.0034722222480922937` |
| `+0x28` | low-resolution 4-byte-pixel auxiliary descriptor, `2080 x 1560`, stride `2080` |
| `+0x30` | high-resolution float destination descriptor, `4160 x 3120`, stride `4160` |

At `0x29f5c0`, the object pointer is adjusted to `object+0x08`, so the worker
body treats the payload as six qwords at offsets `+0x00..+0x28`.

The `0x5440` dispatch sample passes full output rect `[0, 0, 4160, 3120]` and
tile pair `[128, 128]` in every accepted run. Captured worker-entry samples are
tile rectangles such as `[384, 0, 512, 128]` at `28mm`; these are runtime
samples, not algorithm constants.

## Worker Formula

The following pseudocode is a direct structural transcription of the static
worker body, with payload names chosen only from proven resolution and access
mode. Public semantic names remain unknown.

```text
for y in rect.y0 .. rect.y1 - 1:
  for x in rect.x0 .. rect.x1 - 1:
    hi = u8x4(hi_desc.data[y * hi_desc.stride + x])

    sx0 = clamp(signed_div_trunc_toward_zero(x - 1, 2), 0, src_w - 1)
    sx1 = clamp(sx0 + 1, 0, src_w - 1)
    sy0 = clamp(signed_div_trunc_toward_zero(y - 1, 2), 0, src_h - 1)
    sy1 = clamp(sy0 + 1, 0, src_h - 1)

    wx0 = coeff[min(int(abs((x - 0.5) - 2 * sx0)), 1)]
    wx1 = coeff[min(int(abs((x - 0.5) - 2 * sx1)), 1)]
    wy0 = coeff[min(int(abs((y - 0.5) - 2 * sy0)), 1)]
    wy1 = coeff[min(int(abs((y - 0.5) - 2 * sy1)), 1)]

    numerator = 0
    denominator = 0

    for (sx, wx) in [(sx0, wx0), (sx1, wx1)]:
      for (sy, wy) in [(sy0, wy0), (sy1, wy1)]:
        aux = u8x4(aux_desc.data[sy * aux_desc.stride + sx])
        d2 = (hi[0] - aux[0])^2 + (hi[1] - aux[1])^2 + (hi[2] - aux[2])^2
        q = clamp(-(d2 * scale), -126, 128)
        bilateral = bit_level_exp_approx(q) + 9.99999993e-9
        weight = wx * wy * bilateral
        numerator += src_desc.data[sy * src_desc.stride + sx] * weight
        denominator += weight

    dst_desc.data[y * dst_desc.stride + x] = numerator / denominator
```

The installed code implements the `bit_level_exp_approx(q)` term by splitting
`q` into an integer part and fractional part, left-shifting the integer part by
`23` to form float exponent bits, evaluating the cubic constants above over the
fractional part, and combining the two with integer `paddd`. This evidence
therefore proves the installed arithmetic sequence and constants, not that the
operation is a mathematically exact `exp(q)`.

## Proven Boundary

Across accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs:

```text
0x29ed90
  -> callback object vtable 0x668288
  -> 0x5440 dispatch
  -> vtable slot +0x30 = 0x29f5c0
  -> worker body 0x29f600
  -> output float store 0x29f9de
  -> 4160 x 3120 float destination descriptor
```

The worker is a guided 2x upsample over a low-resolution float source using a
high-resolution 4-byte-pixel guide, a low-resolution 4-byte-pixel auxiliary
guide, a two-entry spatial coefficient table `[1.0, 1/3]`, and a bilateral
color-distance weight built from the static approximation sequence above.

## Non-Claims

- This proof does not identify the public LRI/protobuf field that supplies the
  previous-layer `2080 x 1560` source descriptor.
- This proof does not assign public semantic names to the high-resolution guide,
  low-resolution source, low-resolution auxiliary, coefficient table, scale, or
  destination descriptor.
- This proof does not prove the final merge acceptance/rejection policy.
- This proof does not prove `src1` / `src2` semantic contents or C6 routing.
- Runtime worker/store counts in this note are capped probe samples, not
  full-render totals.
