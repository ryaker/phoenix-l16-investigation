# Static/Runtime Evidence: Guidance collapse2 Semantics and Hot-Pixel Narrowing

> **Corrective supersession (2026-07-16):** The collapse2 and hot-pixel
> formulas below remain valid for the pre-YUV intermediate. The old statement
> that this intermediate is directly packed as final Guidance is refuted.
> `CreateStereoImage` next applies its inlined `StereoISP::ConvertToYUV`
> matrix/power stage, so final key-0 Guidance is `[Y,U,V,1]`. See
> `bundle_static_runtime_index5_guidance_yuv_formula_two_body.md`.
>
> **Corrective supersession (2026-07-22):** Full-frame capture disproves the
> focused receipt's two-serial-residual interpretation and proves row-varying
> isolation selection. One residual plus the corrected selector is exact over
> the complete eight-pixel-inset interior; 118 outer-frame samples remain
> open. See
> `bundle_static_runtime_hot_pixel_fullframe_correction_unit1_28mm.md`.

## Scope

This evidence closes the public component-meaning and live-configuration part
of `CLM-STEREO-001` for index-5 Guidance. It also narrows, but does not close,
the remaining clean-room arithmetic for the live default hot-pixel stage.

Coverage is complete Unit-1 `28/35/70/150mm` SoftISP property capture, one
exact-focal Unit-2 `28mm` control, installed-bundle proof for all four Bayer
phases, gated worker receipts at Unit-1 `28mm` and `70mm`, and focused
Unit-1 `28mm` hot-pixel formula/decision receipts. The installed bundle is
SHA-256 `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## Artifacts

Reusable harnesses:

- `tools/lldb_probes/index5_guidance_channel_origin/softisp_property_probe.py`
- `tools/lldb_probes/index5_guidance_channel_origin/run_softisp_properties_matrix.sh`
- `tools/lldb_probes/index5_guidance_channel_origin/collapse2_worker_probe.py`
- `tools/lldb_probes/index5_guidance_channel_origin/verify_guidance_collapse2_semantics.py`
- `tools/lldb_probes/index5_guidance_channel_origin/hot_pixel_formula_probe.py`
- `tools/lldb_probes/index5_guidance_channel_origin/hot_pixel_decision_probe.py`
- `tools/lldb_probes/index5_guidance_channel_origin/verify_hot_pixel_formula.py`

Raw receipts are under `runs/index5_guidance_channel_origin/` with prefixes
`softisp_properties_`, `collapse2_worker_`, `hot_pixel_formula_`, and
`hot_pixel_decision_`.

Verifier results:

```text
guidance_collapse2_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 variants=4
live_softisp=Unit1(28,35,70,150)+Unit2(28) collapse2 none/native
gated_workers=28mm:E3/GRBG 70mm:E3/BGGR
guidance_components=C0:R C1:(G1+G2)/2 C2:B C3:1
guidance_collapse2_semantics=OK
guidance_hot_pixel_formula=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 rank6_trials=10000 decisions=96 accepted=93 rejected=3 accepted_residual=40 rank_residual=40 lut_gain_row=150 lut_lanes=green/blue/red/green lut_bits=4096/4096
```

## Live SoftISP Configuration

All five property captures agree. The natural query made by
`StereoISP::CreateStereoImage` is `demosaicking.type = collapse2`.

| Property | SoftISP input 1 | SoftISP input 2 |
|---|---|---|
| `demosaicking.type` | `none` | `collapse2` |
| `hot_pixel_removal.type` | `none` | `default` |
| `lens_shading.type` | `default` | `default` |
| `color_correction.type` | `none` | `none` |
| `bayer_phase_fix.type` | `none` | `none` |
| `highlight_restore.type` | `none` | `none` |
| `denoising.type` | `none` | `none` |
| `tone_adjust.type` | `none` | `none` |
| `contrast_adjust.type` | `none` | `none` |
| `tone_mapping.type` | `none` | `none` |
| `output.color_space` | `none` | `none` |
| `output.white_point` | `native` | `native` |

The first input is the already bounded direct source. The second input is the
generated Guidance path. Therefore no output color-space conversion, color
correction, denoise, tone, or contrast stage changes the component identity
after demosaicking. The live `default` hot-pixel stage changes selected scalar
Bayer samples before demosaicking and is not a pass-through.

## Exact collapse2 Components

RTTI and vtable proof identifies the four
`ImageDemosaickFilter<DemosaickFilterE3,float,phase>` specializations and
their workers at `0xa4ac0`, `0xa50d0`, `0xa56e0`, and `0xa5cf0`. Static
inspection of every specialization proves that each phase first normalizes
its 2x2 Bayer cell to `[R,G1,G2,B]`, then emits:

```text
C0 = R
C1 = float32(0.5 * G1 + 0.5 * G2)
C2 = B
C3 = 1.0
```

The direct pack path rounds and saturates those lanes to `vec4x8ui` without
permutation. Gated runtime independently reaches E3/GRBG at Unit-1 `28mm`
and E3/BGGR at Unit-1 `70mm`. The all-phase static proof plus the identical
four-focal live property selection makes the component formula applicable to
the admitted Unit-1 four-focal Guidance products; exact-focal Unit-2 `28mm`
independently selects the same live property configuration.

## Default Hot-Pixel Stage

The live stage chain is:

```text
setHotPixelRemoval::$_11 at 0x341770
  -> ImagePatchHotPixels helper 0x2e8680
  -> ImagePatchHotPixels worker 0x2e8cc0
```

Gated `28mm` and `70mm` receipts observe nonzero patch counts, so this stage
is load-bearing. The worker applies the same unsigned eight-input rank network
while forming each source row of its rolling ring. A scalar transcription of
the installed compare network returns the sixth-smallest value for 10,000
deterministic random vectors. It forms one saturating positive residual
against that rank statistic. For pixel `(x,y)`, the neighborhood uses a fixed
distance-2 cross:

```text
(-2,0), (2,0), (0,-2), (0,2)
```

plus one of two diagonal sets. Let
`far = ((x&1) == ((y&1) XOR (phase_x XOR phase_y)))`:

```text
far:  (-2,-2), (-2,2), (2,-2), (2,2)
near: (-1,-1), (-1,1), (1,-1), (1,1)
```

Thus, for `rank6` equal to the sixth-smallest of the eight neighbors:

```text
r(x,y) = max(0, source(x,y) - rank6(source neighbors))
c(x,y) = source(x,y) - r(x,y)
```

The captured 13x13 source halo replays `r=40` and
`source-r = 398-40 = 358` exactly. That receipt also yielded `40` under a
hypothetical second pass and therefore did not prove such a pass. The worker
marks candidate `c` as `c|0x8000` only when:

```text
float32(r) > 4.0 * selected_bayer_noise_LUT[c]
```

The LUT lane follows the Bayer phase. `0xef120` selects the installed RGB
`SensorGainVars` row through `0xef050`, whose key is public
`int(float32(CameraModule.sensor_analog_gain * 100))`, and copies the selected
red/green/blue vectors. A live accepted receipt has source `398`, candidate
`358`, residual `40`, the candidate marker `0x8166`, and
`40 > 4*LUT_lane[358]`.

The `0xed830 -> 0xee510` LUT generator is exact. For selected channel
coefficients `(a,b)` and sensor configuration `(black,white,cliff_slope)`, let
`N = int(float32(white+1))` and, in double precision:

```text
x_i     = (i + 0.5) / N
sigma_i = sqrt(max(a*x_i + b, 1e-10))
u_i     = x_i / sigma_i
P(u)    = Horner(u, [
  1.430853e-06, 3.2172868e-07, -2.6295693e-05,
 -8.5123452e-05, -1.7851033e-05, 0.0020282884,
  0.024377832, 0.037234715, 0.70309281, 0.16923658])
base_i  = float32(sigma_i * 0.5 * (tanh(P(u_i)) + 1))
```

Then, with float32 rounding at every displayed operation:

```text
k     = int(float32(black * cliff_slope))
slope = float32(float32(base[k+2] - base[k-2]) * 0.25)
base[i<k] = float32(base[k] - float32(float32(k-i) * slope))
LUT[i] = float32(base[i] * white)
```

The installed gain-150 row and configuration `black=42`, `white=1023`,
`cliff_slope=2` generate the live lane order
`[green,blue,red,green]` bit-for-bit: `4096/4096` float32 words agree. The
verifier extracts the installed row independently and finds one unique
row/channel match for every captured vector.

The final marker-isolation predicate is transcribed in
`verify_hot_pixel_formula.py`. It has two Bayer-phase branches over the
`y-4..y+4`, `x-4..x+4` marker neighborhood. The verifier replays all 96 live
decisions exactly, including 93 accepts and 3 rejects, and verifies the final
`&0x7fff` marker removal before replacement. Full-frame proof adds the missing
row selector: branch selection uses
`((y&1) XOR (phase_x XOR phase_y))`, not a frame-constant phase XOR.

## Remaining Boundary

The outer eight-pixel frame remains open: 118 of 12,979,200 Unit-1 exact-28mm
samples differ after an otherwise exact public replay. Standard padding modes
are disproven. Cross-body/focal full-frame validation also remains open.

## Admission

Admitted to `CLM-STEREO-001`:

- exact Guidance components `R`, averaged Bayer green, `B`, and `1`;
- identical live `collapse2/default/native` SoftISP configuration at Unit-1
  `28/35/70/150mm` plus exact-focal Unit-2 `28mm`;
- load-bearing default hot-pixel stage identity, public analog-gain selector
  custody, one-residual rank-6 statistic, `4*LUT` candidate threshold, marker
  encoding, row-varying isolation selector, and exact inset-interior isolation
  predicate at focused Unit-1 `28mm` scope;
- nonzero stage liveness at Unit-1 wide and tele scope.

This evidence does not close the full hot-pixel stage. Collapse2 configuration
retains four-focal plus Unit-2 scope; the exact full-frame hot-pixel replay is
`PARTIAL` pending the global edge policy and cross-body/focal controls.
