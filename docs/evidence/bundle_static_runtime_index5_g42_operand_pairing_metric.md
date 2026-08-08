# Installed/Runtime Evidence: Index-5 G-42 Operand Pairing and Byte Metric

**Date:** 2026-07-15  
**Status:** VERIFIED; proposed `CLM-STEREO-001` addendum  
**Bearing:** `StereoLayer<false>::runPass(int) -> 0x2732f0`, selected index `5`

## Question

G-42 left two implementation-critical facts open:

1. whether each plane-sweep hypothesis compares source `k` with the tier
   anchor / `Images[0]`, with another source, or with a running aggregate; and
2. whether the byte cost is plain SAD or a clamped/weighted/saturated variant.

This proof closes both for the selected profile-3 index-5 route.

## Artifacts

- `tools/lldb_probes/g42_cost_operand_pairing/g42_cost_probe_v2.py`
- `tools/lldb_probes/g42_cost_operand_pairing/g42_cost_probe_v3.py`
- `tools/lldb_probes/g42_cost_operand_pairing/verify_g42_metric.py`
- retained reports under `runs/g42_cost_operand_pairing/`
- prior four-focal route proof:
  `docs/evidence/bundle_proof_stereolayer_runpass_cost_path_four_zoom.md`
- prior four-focal `Images[0] -> Guidance` proof:
  `docs/evidence/bundle_static_runtime_index5_cost_operand_names_four_zoom.md`

The retained G-42 probes intentionally terminate after twelve complete
operand/cost packets, so process exit `-1` is expected. Complete-output
liveness at `28/35/70/150mm` comes from the prior route proof.

## Exact Operand Pairing

The SHA-pinned installed chain is deterministic:

```text
0x276b98  first item from StereoLayer+0x240 Images
0x276b9f  raw descriptor pointer
0x276bd4  call 0x275630

0x27564c  context+0x00 = first Images descriptor

0x276f56..0x2770e0
            clamp a 3x3 neighborhood in that first image
            and place its three rows at stack rbp-0x80/-0x70/-0x60

0x2773bd  rdi = rbp-0xd0
0x2773dc  call 0x2732f0
```

Because `rbp-0xd0` is the cost context, the three anchor rows are exactly:

```text
rbp-0x80 = context+0x50
rbp-0x70 = context+0x60
rbp-0x60 = context+0x70
```

Prior installed/runtime proof names the first Images item and its reused
descriptor as Guidance: A1 at `28/35mm`, B4 at `70/150mm`.

Inside `0x2732f0`, each source index `k` selects one descriptor from the Images
vector, projects the current reciprocal-depth hypothesis through that
source's composed record, bilinear-samples a source 3x3 byte patch, and
compares the three source rows against fixed context rows `+0x50/+0x60/+0x70`.
The context rows do not change while `k` advances. Therefore the selected
cost is:

```text
projected source-k patch versus unprojected Images[0] / Guidance anchor patch
```

It is not all-pairs matching and not comparison against a running mean.

## Exact Per-Source Metric

For source `k`, component `c`, and each of the nine 3x3 samples `p`:

```text
cap = (2, 6, 6, 0)
d[p,c] = min(abs(source_k[p,c] - anchor[p,c]), cap[c])
S[c] = saturating_u16_sum_over_3x3(d[p,c])

q[c] = ((uint32(weight[k,c]) * uint32(S[c])) + 16) >> 5
cost_k = trunc(min(float32(sum_c(q[c])), 65535.0f))
```

The SIMD loads are sixteen bytes wide, but the fold at
`0x27364b..0x273658` discards the fourth pixel dword from each row. The
metric is exactly 3x3, not 3x4.

Observed live cap bytes are `02 06 06 00` repeated across the SIMD vector.
Observed ordinary source weights are `(8160,680,680,0)`. The wide source
index `1` packets use `(12240,0,0,0)`; the weight is selected from
`context+0x80 + 8*k`, so the implementation must retain the per-source table
rather than universalize either captured vector.

`cost_k` is capped, but cross-source accumulation is not saturating:

```text
0x2736a9  addw %si,(%rcx)
cost_volume_u16 = (cost_volume_u16 + cost_k) mod 65536
```

The retained packets do not cross `65535`, so they independently verify the
running sum but do not exhibit wrap. The installed opcode closes the boundary
semantics. Any description of the cross-source store as saturating addition
is refuted.

## Runtime Replay

All three retained focal packets are the exact `2080x1560` index-5 layer and
use source indices `0,1,2,3`:

| Focal | Anchor family | Packets | Bit-exact per-source costs | Running accumulation |
|---|---|---:|---:|---|
| `28mm` | A1 / wide | 12 | `12/12` | exact |
| `35mm` | A1 / wide | 12 | `12/12` | exact |
| `70mm` | B4 / tele | 12 | `12/12` | exact |

The reports pin installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

Verifier output:

```text
g42_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 pairing=source_k_vs_Images0_Guidance metric=clamped_weighted_scaled_SAD
28mm: OK pairs=12 sources=0,1,2,3 bit_exact=12
35mm: OK pairs=12 sources=0,1,2,3 bit_exact=12
70mm: OK pairs=12 sources=0,1,2,3 bit_exact=12
g42_operand_pairing_metric=OK
```

## Scope and Admission Boundary

Admit for canonical profile-3 index-5 stereo:

- source-`k` versus first-Images / Guidance anchor pairing;
- fixed unprojected anchor 3x3 versus projected bilinear source 3x3;
- exact cap, weighted reduction, rounding, per-source clamp, and cross-source
  modulo-u16 accumulation semantics; and
- refutation of plain SAD, all-pairs/running-mean pairing, and saturating
  cross-source accumulation.

Runtime operand/bit replay covers Unit-1 `28mm`, `35mm`, and `70mm`.
Installed formula proof is focal/body independent, and prior complete
four-focal route proof supplies `150mm` liveness of the exact pinned
`0x2732f0` body. No Unit-2 G-42 packet is claimed. This does not close the
separate SGM pass-direction census, per-level hypothesis counts, level-0
range seed, or arbitrary supported-capture compatibility.

