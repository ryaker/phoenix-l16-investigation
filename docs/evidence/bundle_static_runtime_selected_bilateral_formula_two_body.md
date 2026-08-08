# Static and Runtime Proof: Selected Bilateral Formula and Callback Roles

## Scope

This bundle formula-closes the two `r9b == 0` bilateral workers selected by
the admitted profile-3 route evidence:

- `0x2fb320`, kernel size `5`, radius `2`, selected by the canonical Unit-1
  `28/35/70/150mm` quartet; and
- `0x2fd070`, kernel size `9`, radius `4`, observed on exact-35mm Unit-2.

It joins SHA-pinned installed bodies to fresh post-store runtime captures and
machine-replays every captured neighborhood. It also assigns operational
roles to callback fields `+0x08`, `+0x10`, `+0x18`, and `+0x20`. These are
clean-room roles, not asserted public protobuf field names.

## Artifacts

- Probe:
  [selected_bilateral_formula_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/selected_bilateral_formula_probe.py)
- LLDB scripts:
  [unit1_35mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/unit1_35mm.lldb),
  [unit2_35mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/unit2_35mm.lldb)
- Verifier:
  [verify_selected_bilateral_formula.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/verify_selected_bilateral_formula.py)
- Raw runtime reports:
  `runs/selected_bilateral_formula/unit1_35mm.json` and
  `runs/selected_bilateral_formula/unit2_35mm.json`
- Completed render outputs:
  `runs/selected_bilateral_formula/unit1_35mm.hdr` and
  `runs/selected_bilateral_formula/unit2_35mm.hdr`

Rerun directly with:

```bash
arch -x86_64 lldb -s /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/unit1_35mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
arch -x86_64 lldb -s /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/unit2_35mm.lldb /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process
python3 /Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/selected_bilateral_formula/verify_selected_bilateral_formula.py
```

## Installed Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier pins these complete ranges:

| Range | SHA-256 |
|---|---|
| `0x2fb320..0x2fc11f` | `c6a6926cffdfa8f79b8f6c0caa4a65066ab0b7f42f7ce4e15dc95a1ed65b7861` |
| `0x2fd070..0x2fdce0` | `c4660f0f361c2a4e9886d125197181dab9f50b7757c5ce3032197c65f547860a` |
| `0x2f6420..0x2f68a0` | `5f28dc1fdbd035a13e71867718f6865cc1b3c43ebfa70869526f090ae2b7cbb0` |

It also checks the exact 16-byte constants used by the workers:

| VA | Meaning | Exact lanes |
|---:|---|---|
| `0x5a81f0` | absolute-value mask | `0x7fffffff` x 4 |
| `0x5a88d0` | alpha-lane blend | `(0,0,0,1)` |
| `0x5a8920` | one | `(1,1,1,1)` |
| `0x5e7380` | weight floor | float32 `(1e-6,1e-6,1e-6,1e-6)` |

The selected bodies have uniform square support. No offset-indexed spatial
coefficient is read. Out-of-bounds source samples in the expanded local
descriptor are zero-filled; the verifier checks those padded cells in every
captured boundary neighborhood.

## Callback Custody

For every runtime sample, the verifier proves:

| Callback field | Operational role |
|---:|---|
| `+0x08` | per-pixel range-scale `vec4` image descriptor |
| `+0x10` | source `vec4` image descriptor |
| `+0x18` | destination `vec4` image descriptor |
| `+0x20` | coefficient `vec4` pointer |

The three callback descriptors have identical rectangles, dimensions, and
strides. The worker expands source and range-scale rectangles by radius `R`,
preserves logical width/height, and increases local stride by `2R`. Captured
local source/range-scale center values equal the callback `+0x10/+0x08`
values at the same coordinate. The final store address and value equal the
callback `+0x18` destination pixel. The callback vtable slot `+0x30` equals
the expected worker in every sample.

## Exact Formula

For output coordinate `p=(x,y)`, let:

- `R=2` for `0x2fb320`, or `R=4` for `0x2fd070`;
- `c = source[p]`;
- `s = coefficient * range_scale[p]`, componentwise;
- `D = (s.r, s.g, s.b, 1)`; and
- `epsilon = float32(1e-6)`.

Initialize four-lane vectors `W=0` and `Q=0`. For every
`o=(dx,dy)` in the uniform square `[-R,R] x [-R,R]`, load
`q=source[p+o]` from the zero-padded local descriptor and compute:

```text
d = max(abs(q.r-c.r), abs(q.g-c.g), abs(q.b-c.b))
t = max(d - s, 0) * rcpps(D)
w = max(1 - t, epsilon)
W = W + w
Q = Q + q*w
```

All vector operations above are lane-wise except the scalar RGB maximum `d`,
which is broadcast. The alpha lane is excluded from `d`; its reciprocal
denominator is blended to `1` before `rcpps`. The worker then stores:

```text
destination[p] = rcpps(W) * Q
```

The installed body uses packed SSE `rcpps` without a refinement step for both
reciprocal operations. A portable implementation may either preserve that
instruction behavior for byte-oriented comparison or use ordinary division
when parity tolerances admit the small reciprocal approximation delta.

## Runtime Replay

Both fresh exact-35mm renders completed with process status `0`, empty probe
error arrays, and no drive step cap.

| Run | Selected store | Samples | Stack prefix |
|---|---:|---:|---|
| Unit-1 `L16_03041` | `0x2fbf05`, radius `2` | `16` | `0x2fbf05 -> 0x5509 -> 0x2f67e7 -> 0x2f59a6` |
| Unit-2 `L16_01956` | `0x2fdb5a`, radius `4` | `8` | `0x2fdb5a -> 0x5509 -> 0x2f6863 -> 0x2f59a6` |

The latest deterministic verifier result is:

```text
static_selected_bilateral=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 constants=abs_mask,alpha_lane,one,epsilon
unit1_35mm: OK samples={'after_store_0x2fb320_radius2': 16}
unit2_35mm: OK samples={'after_store_0x2fd070_radius4': 8}
selected_bilateral_formula=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 samples=24 max_sum_delta=0.00193786621 max_weighted_delta=0.00309753418 max_output_delta=0.000453352928 max_observed_divide_delta=0.000452637672
```

The replay uses float32 arithmetic and exact division as a deterministic
stand-in for `rcpps`. The measured residuals are bounded by the installed
approximate reciprocal behavior. Destination memory equals captured `xmm0`
within `1e-7` in every sample.

## Zoom and Body Scope

Prior admitted runtime route evidence proves `0x2fb320` liveness at Unit-1
`28mm`, `35mm`, `70mm`, and `150mm`; prior four-focal post-store evidence
also proves the same final normalization/store mechanics at all four tiers.
This bundle adds full neighborhood formula replay at Unit-1 `35mm` and the
live `0x2fd070` sibling at exact-35mm Unit-2. Because each complete worker
body is SHA-pinned and the formula is intrinsic to that body, the Unit-1
quartet is `VERIFIED_SAME_MECHANISM` for the selected `0x2fb320` formula,
with direct full replay at `35mm`.

## Admission

Admit for `CLM-DENOISE-002`:

- the exact selected `0x2fb320` radius-2 and `0x2fd070` radius-4 callback
  formulas above;
- callback field roles `+0x08=range scale`, `+0x10=source`,
  `+0x18=destination`, and `+0x20=coefficient`;
- uniform square support, zero-filled boundary expansion, the `1e-6` weight
  floor, and unrefined packed reciprocal normalization; and
- direct formula replay on two physical calibration bodies, joined to prior
  Unit-1 four-focal liveness/store proof.

Non-admissions:

- This does not claim the exact-35mm Unit-2 kernel-size incidence is universal
  across every Unit-2 capture.
- This does not assign public protobuf names to internal callback descriptors
  or coefficient vectors.
- This does not claim runtime liveness for the unselected kernel-size `3/7`
  siblings or the `r9b != 0` worker table.
- This does not turn an operational callback role into a direct LRI field;
  upstream construction remains a separate custody question wherever its
  value origin is implementation-relevant.
