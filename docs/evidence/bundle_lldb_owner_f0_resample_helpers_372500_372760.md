# Bundle + LLDB Owner `+0xf0` Resample Helper Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document extends `bundle_lldb_owner_f0_resample_36f800.md`.

It proves, for the first gated owner `+0xf0` selected-cache route only:

- `0x372210` converts offset / scale double pairs into signed 16.16 fixed-point integers using the installed-bundle `65536.0` double constant.
- `0x372500` builds a row-plan/cache struct at worker stack `rbp-0xc0`.
- The row-plan struct stores source descriptor pointer, fixed x/y scale, fixed x start/end values, clamped fixed x bounds, and the 64-entry weight-table pointer.
- `0x3725f0` sizes/allocates the helper row-cache buffer used by the plan struct.
- The first captured `0x372760` row-cache store writes a horizontal 4-tap weighted `vec4`.
- Runtime packets across `28mm`, `35mm`, `70mm`, and `150mm` match the reconstructed 4-tap formula at the captured row-store site.
- Follow-up runtime packets across `28mm`, `35mm`, `70mm`, and `150mm` capture all four unique worker row-plans for the fresh first gated dispatch; every captured row-plan predicts only the middle `0x372760` store segment for that dispatch.

It does not prove:

- full-render leading/trailing row-cache reachability; follow-up
  `bundle_lldb_owner_f0_global_rowcache_segments.md` covers that boundary
- every possible `0x36f800` caller
- every possible owner `+0xf0` route
- alternate downstream routes after owner `+0xf0` expansion
- public names for offset / scale / pixel-format fields
- final output or display semantics
- final contributor acceptance / rejection or suppression policy

## Tooling Boundary

Reusable probe:

- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_36f800_probe.py`

Per-zoom scripts:

- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_28mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_35mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_70mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_150mm.lldb`

Rerunnable raw JSON packets and static disassembly captures live under ignored
`runs/owner_f0_resample_36f800/`.

## Static Proof

Inside `0x372210`, the installed bundle multiplies offset and scale doubles by
`65536.0` and truncates to signed int32:

```asm
0x37223f  movsd  0x239c91(%rip), %xmm0     ; 65536.0
0x372247  movsd  (%rax), %xmm1             ; offset x
0x37224b  mulsd  %xmm0, %xmm1
0x372258  cvttsd2si %xmm1, %eax
0x37225c  movl   %eax, -0x58(%rbp)
...
0x372270  movsd  (%rax), %xmm1             ; scale x
0x372274  mulsd  %xmm0, %xmm1
0x37227d  cvttsd2si %xmm1, %eax
0x372281  movl   %eax, -0x60(%rbp)
```

`0x372500` receives:

- `rdi = rbp-0xc0` row-plan struct
- `rsi = source descriptor`
- `rdx = executor region`
- `rcx = fixed offset pair`
- `r8 = fixed scale pair`
- `r9 = weight table`

Observed struct fields:

| Field | Static role |
|---|---|
| `+0x38` | source descriptor pointer |
| `+0x40` | fixed x scale |
| `+0x44` | fixed y scale |
| `+0x48` | fixed x start = `scale_x * region_x0 + offset_x` |
| `+0x4c` | fixed x end = `scale_x * region_x1 + offset_x` |
| `+0x50` | lower clamped fixed x bound |
| `+0x54` | upper clamped fixed x bound |
| `+0x58` | 64-entry weight table pointer |

`0x372760` fills row-cache `vec4`s. The first captured store can occur in one
of the visible loop segments:

| Store site | Segment |
|---|---|
| `0x372893` | leading clamped segment |
| `0x37290d` | middle segment |
| `0x3729dc` | trailing clamped segment |

For the captured store, the formula is:

```text
fixed_x = signed 16.16 x coordinate
floor_x = fixed_x >> 16
frac_index = (fixed_x >> 10) & 0x3f
indices = clamp([floor_x - 1, floor_x, floor_x + 1, floor_x + 2], source_min_x, source_max_x)
weights = weight_table[frac_index][0..3]
dest_vec4 = sum(source_row[indices[i]] * weights[i] for i in 0..3)
```

The same static loop conditions also define the row-plan segment counts:

```text
current = start_x_fixed
leading_count  = ceil(max(0, lower_clamped_fixed - current) / scale_x_fixed)
current += leading_count * scale_x_fixed
middle_count   = ceil(max(0, upper_clamped_fixed - current) / scale_x_fixed)
current += middle_count * scale_x_fixed
trailing_count = ceil(max(0, end_x_fixed - current) / scale_x_fixed)
```

## Runtime Proof

The runtime proof stays gated to the same owner `+0xf0` selected-cache route as
`bundle_lldb_owner_f0_resample_36f800.md`.

`70mm` required `process handle SIGSEGV -p true -s false -n false` in the LLDB
script. A non-LLDB `70mm` render completed successfully, so the pre-route crash
is treated as debugger perturbation, not a render-path fact.

First-hit packets are not semantic constants. A later rerun accepted different
live source/destination descriptor shapes than the earlier helper checkpoint,
while preserving the same gated route and formula validation. The table below is
therefore the current durable snapshot from the fresh row-plan coverage run, not
a claim that these first-hit descriptor dimensions are stable API semantics.

| Zoom | Source descriptor | Destination descriptor | Fixed scale | Store segment | `fixed_x` | `frac_index` | Source indices | Row diff | First final-store diff |
|---|---:|---:|---:|---|---:|---:|---|---:|---:|
| `28mm` | `464x464` | `575x575` | `(52267,52267)` | middle | `184948` | `52` | `[1,2,3,4]` | `0.0` | `1.4901161193847656e-08` |
| `35mm` | `463x464` | `575x575` | `(52267,52267)` | middle | `135094` | `3` | `[1,2,3,4]` | `1.964508555829525e-10` | `1.8189894035458565e-10` |
| `70mm` | `542x543` | `575x575` | `(61292,61292)` | middle | `137672` | `6` | `[1,2,3,4]` | `3.725290298461914e-08` | `1.3271346688270569e-08` |
| `150mm` | `543x543` | `575x575` | `(61292,61292)` | middle | `148040` | `16` | `[1,2,3,4]` | `0.0` | `1.6298145055770874e-08` |

The `Row diff` column compares the destination `vec4` after the captured
`0x372760` store against the probe-computed 4-tap formula above.

## Worker Row-Plan Coverage

The follow-up probe records each unique worker executor region accepted inside
the same gated first `0x36f800` dispatch. All four zooms captured the same
region split:

```text
[0,0,256,256]
[256,0,575,256]
[0,256,256,575]
[256,256,575,575]
```

For each zoom, the live `0x372500` row-plan fields predict:

| Zoom | Unique worker row-plans | Predicted leading stores | Predicted middle stores | Predicted trailing stores | First row-fill observed stores |
|---|---:|---:|---:|---:|---|
| `28mm` | `4` | `0` | `1150` | `0` | `256` middle |
| `35mm` | `4` | `0` | `1150` | `0` | `256` middle |
| `70mm` | `4` | `0` | `1150` | `0` | `256` middle |
| `150mm` | `4` | `0` | `1150` | `0` | `256` middle |

This proves that the fresh four-zoom first gated dispatch row-plans cover only
the middle row-cache loop segment. Follow-up
`bundle_lldb_owner_f0_global_rowcache_segments.md` removes that first-dispatch
boundary and proves leading/trailing segment reachability under the canonical
full-render quartet.

## Limits

This checkpoint bounds row-plan/cache setup, the captured horizontal row-cache
formula, and the fresh first-dispatch worker row-plan segment coverage in the
already gated route. It does not prove every possible route into `0x36f800`, and
it does not close alternate routes or final acceptance / rejection logic.
