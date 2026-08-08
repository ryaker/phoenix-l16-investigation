# MonoFusion Mode-0 A1 Flow-Reference Public Origin: Installed Static + Two-Body Runtime Proof

**Claims:** `CLM-PREFUSION-001`, `CLM-PREFUSION-002` corrective addendum  
**Result:** `PROVEN` for the canonical profile-3 mode-0 route, with the scope below  
**Installed binary:** `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`  
**SHA-256:** `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

## Question

The admitted mode-0 flow formula identifies exact reference and source
pyramids, but the A1 reference pyramid still lacked a complete public-LRI
origin. This bundle closes that residual from public A1 RAW10 through the
level-0 `uint16` Image consumed by the flow builder.

It also distinguishes this route from the selected default hot-pixel stage:
the A1 float plane passed directly to `DemosaickLightV1` is exactly the public
RAW normalization at every pixel. The open global-edge behavior of the A2
hot-pixel worker is therefore not an input to this A1 reference reconstruction.

## Evidence Inputs

The reusable capture and verifier are under
`tools/lldb_probes/prefusion_monofusion_flow_origin/`:

- `monofusion_reference_operand_probe.py`
- `run_reference_operand_unit1_28mm.sh`
- `run_reference_operand_unit2_28mm.sh`
- `verify_flow_reference_public_origin.py`

Runtime captures are written below ignored
`runs/prefusion_monofusion_flow_origin/*_reference_operand/`. They are
rerunnable artifacts rather than the sole authority for this bundle.

| Scope | LRI | LRI SHA-256 |
|---|---|---|
| Unit-1 exact 28mm | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` | `2ac51af5c219639638ba34bb98975b62ee922331214043a938a7c37052700ff5` |
| Unit-2 exact 28mm | `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` | `faba5ceee50a6b4b3d3f58b7d725a320158270b26475a591b1f6853698a321ad` |

The verifier pins the installed bodies `0x1b17c0`, `0x1acbf0`, `0x1b5660`,
`0x1b5f60`, `0x18dd00`, `0x1b6340`, and `0xfc2f0`, all four installed
`DemosaickLightV1` phase bodies, and the `4096`-word LUT at `0x5cc080`.

## Public Inputs

The complete selected input set is:

- `CameraModule.sensor_data_surface`
- `CameraModule.sensor_bayer_red_override`
- `CameraModule.lens_position`
- `CameraModule.sensor_exposure`
- `CameraModule.sensor_analog_gain`
- `SensorCharacterization.black_level`
- `SensorCharacterization.white_level`
- `VignettingCharacterization.vignetting[]`

The installed constants are response scalar
`R=2.3183400630950928`, AR1335 luma weights
`[0.2155500054359436, 0.43230700492858887,
0.35214298963546753, 0]`, and the sqrt LUT described below. Public
`sensor_digital_gain` is not an operand of the exposure ratio.

## Exact Reconstruction

Let `raw` be unpacked public A1 RAW10, `B=42`, `W=1023`, and
`D=W-B=981`. The initializer first forms, with installed scalar-SSE rounding:

```text
normalized = float32((float32(raw) - 42) * rcpss(981))
rcpss(981) bits = 0x3a859800
```

The public A1 red-site override is `(1,0)`, so the selected worker is
`DemosaickLightV1` GRBG with unity gains `(1,1,1)`. Its output descriptor is
the descriptor read directly by the next luma helper. The already admitted
all-phase demosaic verifier independently pins that worker's exact formula.

For demosaicked channels `(r,g,b,a)`, the luma helper preserves this float32
grouping:

```text
rb = float32(r*0.2155500054359436 + b*0.35214298963546753)
ga = float32(g*0.43230700492858887 + a*0)
luma = float32(float32(rb + ga) * 981)
```

Let the public exposure energies be:

```text
E1 = float32(A1.sensor_exposure * A1.sensor_analog_gain)
E2 = float32(A2.sensor_exposure * A2.sensor_analog_gain)
Q  = float32(E1 / E2)
S  = float32(R / Q)
affine = min(float32(luma * S), 981)
```

`S=R/Q` is the reciprocal companion of the previously admitted A2 source
scale `Q/R`. The selected A1 public vignetting profile is interpolated using
the admitted exact `17x13` profile formula at the live public lens position.
Selection is by runtime calibration-vector position `0`; its public record
camera ID differs by body and is not the vector index.

For interpolated gain `V(x,y)`, the level-0 flow-reference sample is:

```text
z = float32(affine(x,y) * V(x,y))
i = clip(trunc_i32(float32(z + 0.5)), 1, 4095)
reference_u16(x,y) = LUT[i]
LUT[i] = trunc_u16(sqrt(i * 1023))
```

The installed little-endian `uint16` LUT has SHA-256
`ae826dc2c547e017d9f029f39cdd27901c84a16f1dcfd2fbbdc4de34447e71c1`
and matches all `4096` generated entries.

## Exact Results

Every stage below is checked over all `4,160 * 3,120 = 12,979,200` pixels.

| Scope | Public A1 RAW normalization | Luma | Affine | Final level 0 | `Q` | `S` | Vignetting public record ID |
|---|---:|---:|---:|---:|---:|---:|---:|
| Unit-1 exact 28mm | `12,979,200/12,979,200` | exact | exact | exact | `0.51181560754776` | `4.52963924407959` (`0x4090f2ce`) | `12` |
| Unit-2 exact 28mm | `12,979,200/12,979,200` | exact | exact | exact | `0.5000497102737427` | `4.636219024658203` (`0x40945be8`) | `4` |

The body discriminator materially changes public RAW bytes, exposure ratio,
vignetting grid, affine scale, demosaic output, and final image:

| Scope | Packed RAW10 SHA-256 | Demosaic output SHA-256 | Final level-0 SHA-256 |
|---|---|---|---|
| Unit-1 | `87b238e19d8fec8e2a5bb33faf6a4e145c088b8285cf0b0b18a62f3a984fbd27` | `70c14c383a89d2368bb6827a05a075ab457df85c8ca4b02842685733ae55b810` | `a7c5c4f063502a530aef916886c9100430bb853f1a9e17677b24c79e1f0fea2a` |
| Unit-2 | `fe750e70d2ef24dc72964fb4574bee96817fb6d42fefb4914c81356260513d62` | `de242b171af796aa17ee9c642a756a9fb9f74865c4ff2ea6945d85903cfbb9c6` | `2b19a9182ccae53faa1c8941156c77fe358c66696e803ededb579a3171b4f019` |

The different inputs and outputs refute a retained golden operand, one-body
calibration substitution, or fixed scale while preserving exact public
reconstruction on both physical calibration signatures.

## Installed Custody

The mode-0 initializer provides the direct sequence:

```text
public A1 normalized RAW
  -> 0x2eb560 DemosaickLightV1
  -> 0x1b5f60 luma helper
  -> 0x1b5660 reciprocal exposure affine
  -> 0xfc2f0 selected A1 vignetting
  -> 0x18dd00 round/clamp/sqrt-LUT conversion
  -> 0x1b6340 / 0x1991d0 reference pyramid
  -> 0x1991e0 flow producer
```

The captured demosaic output descriptor equals the luma source descriptor,
so there is no anonymous transform between those two surfaces.

## Scope and Admission

Runtime numerical proof is complete-frame, exact-focal `28mm` on both
physical calibration signatures. SHA-pinned installed formula proof is
same-mechanism. Prior admitted route evidence supplies the required canonical
four-focal statement: profile-3 `28mm` and `35mm` use this mode-0 A1/A2
MonoFusion path; `70mm` and `150mm` construct no MonoFusion and use direct B4.

No mode-1 formula, 35mm full-plane replay, cross-body numeric invariance,
body/firmware cause, or A2 global-edge hot-pixel policy is claimed. This
closes the A1 flow-reference public-origin residual while leaving the current
`CLM-STEREO-001` A2 outer-edge blocker unchanged.

## Reproduction

```bash
bash tools/lldb_probes/prefusion_monofusion_flow_origin/run_reference_operand_unit1_28mm.sh
bash tools/lldb_probes/prefusion_monofusion_flow_origin/run_reference_operand_unit2_28mm.sh
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_reference_public_origin.py
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_flow_reference_public_origin.py \
  --lri "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri" \
  --run-dir runs/prefusion_monofusion_flow_origin/unit2_28mm_reference_operand
```
