# Static/Runtime Evidence: Index-5 Cost Operand Names

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B operand-name refinement  
**Bearing:** sampled index-5 `0x276860` Cost-volume worker

## Question

Earlier four-focal packet proofs bound sampled `0x276860` operands to target
fields `+0x168`, `+0x198`, `+0x1e8`, `+0x200`, and `+0x288`, but left those
fields semantically anonymous.

This proof joins those runtime fields to installed `StereoLayer<false>` debug
labels and to the already proven producer paths.

## Artifacts

- Static/reused-runtime verifier:
  `tools/lldb_probes/index5_cost_operand_names/verify_cost_operand_names.py`
- Extended installed-label verifier:
  `tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py`
- Reused complete reports:
  `runs/codex_276860_payload_vector_formula/vector_formula_*.json`
- Reused accepted early-terminate packets:
  `runs/codex_276860_operand_source_context/operand_source_*.json`
- Reused camera-order reports:
  `runs/index5_composed_geometry_origin/composed_geometry_*.json`

No new LLDB render was needed.

## Installed Names

The pinned `0x26fe00` debug routine pairs exact strings with exact object
fields:

| Object field | Installed label |
|---|---|
| `+0x288` | `Guidance` |
| `+0x1e0` | `Pixel buf` |
| `+0x188` | `Min cost buf` |
| `+0x148` | `Line buf` |

The verifier pins complete installed windows for the debug routine, the
`0x26c480` setup path, the `0x26c8e0` scratch-buffer allocator, and the
`0x276a80..0x277a20` worker window.

## Field Layout and Runtime Join

`0x26c8e0` constructs the labeled scratch buffers. Combined with the admitted
runtime packets:

| Sampled field | Exact identity |
|---|---|
| target `+0x168` | `Line buf` data pointer |
| target `+0x198` | `Min cost buf` data pointer |
| target `+0x1e8` | `Pixel buf` data base |
| target `+0x200` | `Pixel buf` interior split/end pointer |
| target `+0x288` | `Guidance` descriptor/shared object |

All complete payload-vector reports require
`rbp-0x200 == target+0x168` and `rbp-0x210 == target+0x198` for every admitted
sample. All operand-source packets require `rbp-0x208 == target+0x1e8` and
`rbp-0x250 == target+0x200`.

For the sampled index-5 layout:

```text
Pixel buf split/end - Pixel buf data base = 33312 bytes
Min cost buf sampled capacity             = 16656 uint16 entries
```

These sizes are runtime layout observations, not universal constants.

## Guidance Origin

The pinned `0x26c480` setup path:

1. reads the first item from exact `StereoLayer+0x240` `Images`;
2. compares its dimensions with the current layer;
3. reuses that first image descriptor through `0x26c633` when dimensions
   match; and
4. stores it at exact `StereoLayer+0x288` `Guidance`.

Every admitted index-5 operand packet records one same-object
`guide_store_0x288_reuse_26c633` event and a `2080 x 1560` Guidance
descriptor.

The composed-geometry order proof independently establishes the first Images
camera:

| Focal family | First Images item / Guidance source |
|---|---|
| `28mm`, `35mm` | `A1` |
| `70mm`, `150mm` | `B4` |

Therefore the sampled index-5 Guidance is the tier-anchor image descriptor,
not an anonymous calibration table.

## Worker Meaning

The admitted operand and vector-formula reports now read as:

```text
Guidance bytes
  -> unsigned-byte-to-float conversion
  -> Pixel buf vectors

Pixel buf vector - Pixel buf comparison vector
  -> local scale/mask/polynomial shaping
  -> Min cost buf table term
  -> Line buf / temporary recurrence inputs
  -> saturating uint16 update of per-pixel Cost-volume payload
```

This names the sampled storage roles. It does not rename every arithmetic
term as a final cost or acceptance score.

## Verification

```text
static_index5_cost_operand_names=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
28mm: OK Guidance=first_Images_A1 Min_cost_buf=+0x198 Pixel_buf=+0x1e8/+0x200 Line_buf=+0x168
35mm: OK Guidance=first_Images_A1 Min_cost_buf=+0x198 Pixel_buf=+0x1e8/+0x200 Line_buf=+0x168
70mm: OK Guidance=first_Images_B4 Min_cost_buf=+0x198 Pixel_buf=+0x1e8/+0x200 Line_buf=+0x168
150mm: OK Guidance=first_Images_B4 Min_cost_buf=+0x198 Pixel_buf=+0x1e8/+0x200 Line_buf=+0x168
index5_cost_operand_names=OK
```

The adjacent operand-source and vector-formula verifiers also remain green.

## Admission and Remaining Boundary

Admitted:

- exact `Guidance`, `Pixel buf`, `Min cost buf`, and `Line buf` names for the
  sampled fields;
- Guidance origin as the first/tier-anchor Images descriptor; and
- the local generated-buffer classification above.

Still open:

- complete semantic names for every remaining recurrence source, temporary,
  cap, and baseline;
- stable full-map Cost-volume distributions;
- whole-State and selector-bank identities;
- public LRI/protobuf identity for the installed ray-depth bounds; and
- final source contribution and acceptance/rejection.

The named buffers are generated runtime scratch/products, not direct public
calibration protobuf fields.

The follow-up
`bundle_static_runtime_index5_sgm_parameter_origins_four_zoom.md` closes
target `+0x56/+0x58/+0x60` as installed, body-independent SGM `P1`,
guide-adaptive `P2/P1`, and guide-distance decay tuning.
