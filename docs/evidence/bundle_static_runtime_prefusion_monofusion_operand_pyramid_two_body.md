# MonoFusion Mode-0 Operand Pyramid: Static + Two-Body Runtime Proof

**Claim:** `CLM-PREFUSION-002` corrective addendum  
**Result:** exact public-input-to-five-level operand-pyramid closure for
canonical profile-3 MonoFusion mode `0`, with the scope below

## Question

The admitted flow-field proof replayed the SAD/refinement stages from captured
five-level `uint16` operands. It did not state the reduction formula that
produces levels 1 through 4 from the public-input-derived level 0. Can a
clean-room implementation build those exact pyramids without Lumen code or
captured intermediates?

Yes. A previously unadmitted repo-local verifier contained the candidate
formula. This bundle independently re-runs it, strengthens its installed-code
and runtime-artifact custody checks, corrects the source level-0 public join to
include the admitted hot-pixel pre-stage, and admits the result.

## Artifacts

- [verify_operand_pyramid.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_flow_origin/verify_operand_pyramid.py)
- [verify_flow_reference_public_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_reference_public_origin.py)
- [verify_flow_source_public_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_source_public_origin.py)
- [verify_hot_pixel_fullframe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_flow_origin/verify_hot_pixel_fullframe.py)
- [monofusion_flow_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_flow_origin/monofusion_flow_origin_probe.py)
- `runs/prefusion_monofusion_flow_origin/unit{1,2}_28mm_stages/stages.json`
- `runs/prefusion_monofusion_flow_origin/unit{1,2}_28mm_hotpixel_preprocess/report.json`
- `runs/prefusion_monofusion_flow_origin/unit{1,2}_28mm_reference_operand/report.json`

Installed `libcp.dylib` SHA-256:
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

The strengthened verifier pins these installed bodies:

| Range | SHA-256 | Role |
|---|---|---|
| `0x1991d0..0x1991d9` | `c35aafed98719115154e3f41a6900882b6d87a41e240dfffd0622f89f89ad07b` | public producer thunk |
| `0x199140..0x199189` | `4ff81bdd98374842936f5b700a59524281446fcf37ef5ab8b0891837f1af4543` | descriptor wrapper into FastCollapse |
| `0x1895d0..0x189caf` | `7ed574bf612846de3b56681c9759ab6b3cb91ec4c40e98f1bf9dc756c6f26722` | depth/factor dispatch and pyramid construction |

Installed custody is:

```text
0x1b6340 reference/source wrapper
  -> 0x1b63a2 calls 0x1991d0
  -> 0x1991d0 jumps 0x199140
  -> 0x199173 calls 0x189cb0
  -> 0x189cb0 jumps 0x1895d0 FastCollapse builder
```

The complete `stages.json` reports authenticate every dumped level by
descriptor dimensions, byte count, path, and SHA-256 before numerical replay.

## Exact Schedule And Dimensions

The installed four-word reduction table is:

```text
factors = [2, 4, 4, 4]
```

Applied to both reference and source operands, this produces:

| Level | Factor from prior | Dimensions |
|---:|---:|---:|
| 0 | public-input construction | `4160 x 3120` |
| 1 | 2 | `2080 x 1560` |
| 2 | 4 | `520 x 390` |
| 3 | 4 | `130 x 97` |
| 4 | 4 | `32 x 24` |

Each output extent is integer floor division by the factor. Thus the odd
`390`-row input produces `97` rows and the `130 x 97` input produces
`32 x 24`; no ceil or padded output cell is added.

## Exact Kernels

The factor-2 table has seven stored float32 words; its final word is zero, so
the effective filter has six taps:

```text
bits: 3c8fb86f 3e04bdba 3eb46b27 3eb46b27 3e04bdba 3c8fb86f 00000000
float: 0.01754399947822094
       0.12962999939918518
       0.35238000750541687
       0.35238000750541687
       0.12962999939918518
       0.01754399947822094
       0.0
```

The factor-4 table has eleven stored words and ten effective taps:

```text
bits: 3c82eb6d 3d31f03d 3dbc58fc 3e1b4430 3e475dae 3e475dae
      3e1b4430 3dbc58fc 3d31f03d 3c82eb6d 00000000
float: 0.015981400385499
       0.043441999703645706
       0.09196659922599792
       0.1516273021697998
       0.19469329714775085
       0.19469329714775085
       0.1516273021697998
       0.09196659922599792
       0.043441999703645706
       0.015981400385499
       0.0
```

Both are symmetric even-length, half-sample-centered low-pass kernels.

## Exact Reduction Formula

For factor `F`, stored kernel `K`, radius `floor(len(K)/2)`, and phase
`P=1` for `F=2` or `P=2` for `F=4`, the installed operation is separable,
vertical first and horizontal second. Coordinates clamp independently to the
prior image edge.

```text
V[y,x] = f32_sum_in_tap_order(
    f32(K[t] * u16(input[clamp(F*y + P + t - radius), x])))

Q[y,x] = f32_sum_in_tap_order(
    f32(K[t] * V[y, clamp(F*x + P + t - radius)]))

output[y,x] = u16(trunc_toward_zero(Q[y,x]))
```

Every multiply and each left-to-right add rounds to binary32. The vertical
temporary remains binary32. There is no intermediate `uint16` quantization;
the only integer conversion is after the horizontal sum.

The effective factor-2 source positions are `2*n + {-2,-1,0,1,2,3}`.
The effective factor-4 positions are `4*n + {-3,-2,-1,0,1,2,3,4,5,6}`.
At either image edge, each out-of-range position repeats the nearest source
sample before multiplication.

## Corrected Public Source Level 0

The old source-origin helper omitted default hot-pixel correction and matched
only `12,959,614 / 12,979,200` Unit-1 pixels. That is not admitted as a public
source formula.

The corrected proof first authenticates public A2 RAW10 against the exact
hot-pixel worker input. The already-admitted complete-frame worker then
replays every output pixel before this flow-specific encoding:

| Scope | Hot-pixel output exact | Changed pixels | Wrong-phase mismatch |
|---|---:|---:|---:|
| Unit-1 exact `28mm` | `12,979,200 / 12,979,200` | 19,586 | 31,091 |
| Unit-2 exact `28mm` | `12,979,200 / 12,979,200` | 8,404 | 7,505 |

For corrected A2 sample `c`, public black level `B=42`, and the selected
public A2 vignetting factor `v(x,y)`, source level 0 is:

```text
p = f32(f32(c) - f32(B))
p = f32(p * v(x,y))
i = clamp(trunc_toward_zero(f32(p + 0.5f)), 1, 4095)
source_level0 = sqrt_lut[i]
sqrt_lut[i] = u16(trunc(sqrt(i * 1023.0)))
```

The installed 4096-word LUT SHA-256 is
`ae826dc2c547e017d9f029f39cdd27901c84a16f1dcfd2fbbdc4de34447e71c1`.
The corrected source replay matches all `12,979,200` level-0 pixels on each
body. Unit-1 output SHA-256 is
`53be73132a89d4e056f45334ea1185681530cd54fccd3d8d36926e0ed89bf14b`;
Unit-2 is
`aefbd17345346df189191450bb030fab112d15bd9c9274754d0b2971145c0d08`.

This flow operand is not the later A2 exposure-scaled MonoFusion coefficient
plane; no exposure-ratio term appears in this flow-specific source level 0.

## Public Reference Level 0

The separately admitted and rerun reference verifier constructs A1 level 0
from public RAW normalization, exact `DemosaickLightV1`, installed AR1335 luma,
public A1/A2 exposure affine, selected public A1 vignetting, and the same
round/clamp/sqrt-LUT encoding. It again matches all `12,979,200` pixels on
each body:

- Unit-1 SHA-256:
  `a7c5c4f063502a530aef916886c9100430bb853f1a9e17677b24c79e1f0fea2a`
- Unit-2 SHA-256:
  `2b19a9182ccae53faa1c8941156c77fe358c66696e803ededb579a3171b4f019`

Thus neither operand pyramid begins from an unexplained captured level-0
golden.

## Exhaustive Reduction Results

For each body and each role, the verifier regenerates every level only from
the preceding level:

| Role/body | Level 1 | Level 2 | Level 3 | Level 4 |
|---|---:|---:|---:|---:|
| Unit-1 reference | 3,244,800 | 202,800 | 12,610 | 768 |
| Unit-1 source | 3,244,800 | 202,800 | 12,610 | 768 |
| Unit-2 reference | 3,244,800 | 202,800 | 12,610 | 768 |
| Unit-2 source | 3,244,800 | 202,800 | 12,610 | 768 |

Every listed sample is bit exact: `13,843,912 / 13,843,912` generated
`uint16` values in total. The two bodies provide different public RAW,
hot-pixel corrections, exposure/calibration data, level-0 hashes, and all
subsequent pyramid hashes.

## Scope And Consequence

- Numerical runtime: exact-`28mm` on both physical calibration bodies, both
  reference and source operands, complete level-0 and complete reduced levels.
- Installed formula: SHA-pinned common builder, exact constants, and exact
  worker order.
- Canonical focal scope: prior complete route proof shows profile-3 `28mm`
  and `35mm` use this MonoFusion mode-0 path. Canonical `70mm` and `150mm`
  construct no MonoFusion and therefore do not require this pyramid.
- Not claimed: a separate full numerical pyramid replay at `35mm`, profiles
  `1/2` mode-1 operand construction, cross-body numerical invariance, or any
  body/firmware cause.

This closes the reduction gap in the prior flow-field admission. A clean-room
profile-3 implementation can build both five-level operands from public LRI
inputs before applying the already-admitted flow search. `CLM-PREFUSION-002`
remains `PROVEN` / `SPEC_READY` with this corrective addendum attached.

## Reproduction

```bash
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_hot_pixel_fullframe.py \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_hotpixel_preprocess/report.json

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_source_public_origin.py \
  --libcp /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib \
  --lri "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  --hotpixel-report runs/prefusion_monofusion_flow_origin/unit1_28mm_hotpixel_preprocess/report.json \
  --observed runs/prefusion_monofusion_flow_origin/unit1_28mm_stages/source_level0.u16le

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_reference_public_origin.py

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_operand_pyramid.py \
  /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_stages \
  runs/prefusion_monofusion_flow_origin/unit2_28mm_stages
```

Run the first three commands with the Unit-2 LRI/report/run-directory paths
for the independent second-body receipts.
