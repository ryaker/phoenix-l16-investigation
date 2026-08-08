# Static/Runtime Evidence: Index-5 SGM Cost-Input Normalization

**Date:** 2026-07-17  
**Status:** VERIFIED; admitted `CLM-STEREO-001` addendum  
**Bearing:** selected profile-3 mode-8 G-42 to G-43 boundary

## Question

An implementation could reproduce the raw G-42 local-cost curve but needed an
invented per-pixel band-min subtraction to prevent the eight-path `uint16` SGM
sum from saturating. This proof asks what representation Lumen actually passes
from G-42 into the first G-43 recurrence.

## Artifacts

- live custody probe:
  `tools/lldb_probes/index5_sgm_cost_input/sgm_cost_input_probe.py`
- reusable runner:
  `tools/lldb_probes/index5_sgm_cost_input/run_lri.sh`
- installed/runtime verifier:
  `tools/lldb_probes/index5_sgm_cost_input/verify_sgm_cost_input.py`
- retained reports:
  `runs/index5_sgm_cost_input/{unit1_28,unit2_28}/report.json`

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Exact Formula

The selected projection vector contains four `0x50`-byte records, one for each
non-reference source. Installed `0x276bd9..0x276caa` derives that count and
constructs a binary32 scale from installed bytes `26 b4 17 3d`:

```text
installed_base = float32(0.037037037312984467)  # float32(1/27)
source_count   = (projection_end - projection_begin) / 0x50
factor         = float32(installed_base / float32(source_count))
```

For the selected five-image / four-projection path:

```text
source_count = 4
factor = 0.0092592593282461166f
```

G-42 first writes its summed raw matching costs to the aligned `uint16`
temporary. The direct loop at `0x277450..0x277467` then updates every active
hypothesis in place:

```text
local_cost[d] = uint16(trunc_toward_zero(
    float32(float32(raw_g42_sum[d]) * factor)
))
```

The same loop mirrors the low byte to the variable Cost-volume record. G-43
does not consume that byte mirror: `0x2779ee` loads eight `uint16` lanes
directly from the normalized temporary.

There is no per-pixel minimum subtraction or other pedestal operation between
G-42 and this recurrence load. The later `psubusw` at `0x2779f8` subtracts the
prior directional minimum after local-cost plus selected-path addition; it is
the admitted SGM recurrence normalization, not G-42 band normalization.

## Runtime Custody

Focused captures stop after G-42, after the in-place scale loop, and at the
first recurrence load on exact-focal Unit-1 and Unit-2 `28mm` LRIs. Both
captures prove projection count `4`, exact factor bits, instruction-equivalent
float32 replay of the entire captured vector, allocation identity, and exact
equality of the first eight recurrence lanes to the corresponding normalized
lanes.

```text
Unit-1: raw[0]=27521 -> normalized[0]=254 -> SGM lane[0]=254
Unit-2: raw[0]=24799 -> normalized[0]=229 -> SGM lane[0]=229
```

The two packets contain different image-dependent raw vectors while preserving
the same installed formula.

## Scope and Admission

Admitted for selected profile-3 mode-8 index-5 stereo:

- the exact raw-G-42-sum to local-SGM-cost normalization;
- direct same-allocation `uint16` custody into G-43;
- absence of a per-pixel band-min pedestal on this bounded path; and
- classification of `1/27` and the source-count division as installed
  algorithm constants, not LRI/calibration fields.

Installed formula scope is body/focal independent for the pinned bundle.
Direct runtime replay covers exact-focal Unit-1 and Unit-2 `28mm`; existing
admitted G-42/G-43 route and worker receipts provide Unit-1
`28/35/70/150mm` liveness. Body/firmware equality, other profiles or stereo
modes, and malformed/unsupported inputs are not claimed.

## Verification

```text
$ python3 tools/lldb_probes/index5_sgm_cost_input/verify_sgm_cost_input.py
index5_sgm_cost_input_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
installed_constant=0.037037037312984467 bytes=26b4173d
unit1_28mm=OK sources=4 factor=0.0092592593282461166 raw0=27521 normalized0=254 sgm_lane0=254
unit2_28mm=OK sources=4 factor=0.0092592593282461166 raw0=24799 normalized0=229 sgm_lane0=229
pedestal=ABSENT local_cost=trunc_f32(G42_sum*((1/27)/source_count))
```
