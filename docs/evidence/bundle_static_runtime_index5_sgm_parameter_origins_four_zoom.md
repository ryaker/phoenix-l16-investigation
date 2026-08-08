# Static/Runtime Evidence: Index-5 SGM Parameter Origins

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B operational-name/origin refinement  
**Bearing:** target `StereoLayer<false>` fields `+0x56`, `+0x58`, and `+0x60`

## Question

The admitted index-5 Cost-volume worker proof left three local controls
anonymous:

- `u16[target+0x56]`;
- `f32[target+0x58]`; and
- `f32x4[target+0x60]`.

This proof asks whether they come from public per-camera calibration/LRI data
or from installed algorithm configuration, and what the live recurrence
permits them to be called.

## Artifacts

- New reusable verifier:
  `tools/lldb_probes/index5_sgm_parameter_origin/verify_sgm_parameter_origin.py`
- Reused constructor reports:
  `runs/stereolayer_constructor_provenance/ctor_28mm_narrow.json`
  and `ctor_28mm_no_lris_narrow.json`
- Reused accepted four-focal packets:
  `runs/codex_276860_xmm3_term_step/xmm3_term_step_*.json`
  and `runs/codex_276860_xmm4_origin/xmm4_origin_*.json`
- Adjacent recurrence verifier:
  `tools/lldb_probes/codex_276860_payload_vector_formula/validate_vector_formula.py`

No new LLDB render was needed.

## Static Origin

The pinned pipeline-constructor tail creates all six `StereoParams` packets
through `0x27abb0`. For index `5`, the call at `0x3f40d7` supplies:

| `StereoParams` field | Installed producer |
|---|---|
| `+0x46` | literal unsigned `1` |
| `+0x48` | binary float at `0x5da924`, exactly `500.0f` |
| `+0x50..+0x5c` | `0x27abb0` divides one binary numerator by literal `(6,16,16)` and writes a zero fourth lane |

The numerator at `0x5db370` is exactly the float32 encoding of
`log2(e) / 3`. Therefore the generated vector is exactly:

```text
[
  log2(e) / 18,
  log2(e) / 48,
  log2(e) / 48,
  0
]
=
[
  0.080149725,
  0.030056147,
  0.030056147,
  0
]
```

`0x26b750` then copies those packet bytes to object `+0x56`, `+0x58`, and
`+0x60`. This chain has no LRI, module, camera, calibration, or protobuf
input.

## Operational Names

The installed typeinfo names the object `lt::StereoLayer<false>`, while the
same construction path carries the installed error text `SGM after upsampled
depth is not allowed.`

The pinned `0x2779b0..0x277a10` recurrence has the SGM form:

1. add `object+0x56` to each of the two adjacent-hypothesis candidates;
2. take their unsigned minimum with the same-hypothesis candidate;
3. take the minimum with `Min cost buf + adaptive penalty`;
4. subtract the `Min cost buf` baseline; and
5. accumulate the result into the per-pixel Cost-volume record.

The adaptive term is:

```text
guide_weight ~= exp2(
  -sum(abs(guide_delta[0:3]) * object+0x60[0:3])
)

adaptive_penalty =
  trunc(P1 * object+0x58 * guide_weight)
```

Consequently the operational names are:

| Object field | Operational identity |
|---|---|
| `+0x56 = 1` | adjacent-hypothesis SGM penalty `P1` |
| `+0x58 = 500.0` | nominal guide-adaptive `P2/P1` ceiling scale |
| `+0x60` | three-channel exponential guide-distance decay coefficients, with effective denominators `(18,48,48)` |

The polynomial/exponent-bit sequence is an approximation, so a zero guide
difference produces a sampled value near, rather than mathematically equal
to, the nominal `P2/P1` ceiling.

## Runtime Join

The auto-sidecar and `--no-auto-lris` constructor reports both capture the
same index-5 packet values. Every accepted `28mm`, `35mm`, `70mm`, and
`150mm` worker packet then reads:

```text
P1            = 1
P2/P1 scale   = 500.0
guide decay   = 8a25a43d 4f38f63c 4f38f63c 00000000
```

The four-focal runtime scope establishes live use. Body variation cannot
enter this origin chain: the pinned producer uses only installed literals and
binary constants. A second-body render would repeat the same unconditional
construction and is not a useful discriminator for these three fields.

## Verification

```text
static_index5_sgm_parameter_origin=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 guide_decay=0.080149725,0.030056147,0.030056147
28mm: OK P1=1 P2_over_P1=500 guide_decay=8a25a43d4f38f63c4f38f63c00000000
35mm: OK P1=1 P2_over_P1=500 guide_decay=8a25a43d4f38f63c4f38f63c00000000
70mm: OK P1=1 P2_over_P1=500 guide_decay=8a25a43d4f38f63c4f38f63c00000000
150mm: OK P1=1 P2_over_P1=500 guide_decay=8a25a43d4f38f63c4f38f63c00000000
index5_sgm_parameter_origin=OK
```

The existing `xmm3` term, `xmm4` origin, and payload-vector recurrence
validators also remain green.

## Admission and Remaining Boundary

Admitted:

- installed, body-independent origin for target `+0x56/+0x58/+0x60`;
- operational `P1`, guide-adaptive `P2/P1` scale, and guide-distance decay
  coefficient names; and
- exact values and live four-focal use above.

Still open:

- public channel names for the three Guidance components; installed
  `StereoISP::ConvertToYUV` typeinfo alone is not custody proof that these
  exact components are Y/U/V;
- complete names/custody for every remaining recurrence source, temporary,
  cap, and baseline;
- stable full-map Cost-volume distributions;
- final source contribution and acceptance/rejection; and
- whole-State and selector-bank identities.

These fields are installed SGM tuning, not direct public calibration or LRI
protobuf fields.
