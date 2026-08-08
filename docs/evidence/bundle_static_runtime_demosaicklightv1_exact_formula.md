# DemosaickLightV1 Exact Formula

**Claim target:** `CLM-DEMOSAIC-002`  
**Installed binary:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Method:** SHA-pinned installed-bundle extraction, Capstone assertions, two
same-thread stopped-frame runtime replays, and the corrective full-frame
two-body replay linked below  
**Scope:** renderer-side formula is static and zoom-independent; Bayer phase is
selected per input camera. The public phase values were independently checked
across two physical units and four exact focal tiers in
`bundle_static_runtime_raw_sensor_layout_two_body_four_zoom.md`.

## Result

`DemosaickLightV1` is formula-closed. The original local replay in this bundle
misassigned the second directional stage and overgeneralized source borders.
The corrected interpretation below is proved full-frame in
`bundle_corrective_static_runtime_demosaicklightv1_fullframe_two_body.md`.
It is a residual-interpolation demosaic:

1. multiply the incoming scalar Bayer plane by the gain for the color at each
   CFA site;
2. construct a scalar edge-aware guide `A`;
3. form the measured residual `B = S - A`;
4. interpolate the residual belonging to each RGB channel and add it to `A`;
5. write RGBA float32 with alpha `1.0`.

The implementation uses SSE `rcpss` / `rcpps` reciprocal approximations without
a Newton refinement. An implementation seeking instruction-level agreement must
preserve float32 operation order and reciprocal semantics. A normal floating
division implementation expresses the same formula but is not promised to be
bit-identical.

## Phase And Gain Dispatch

The driver at `libcp+0x2eb560` accepts the red-site phase `(red_x, red_y)` and
dispatches:

| Red site | CFA quad | Body |
|---|---|---:|
| `(0,0)` | RGGB | `0x2ed580` |
| `(1,0)` | GRBG | `0x2eeb20` |
| `(0,1)` | GBRG | `0x2ef6a0` |
| `(1,1)` | BGGR | `0x2f0240` |

The verifier independently checks each vtable target and each body's raster gain
permutation:

```text
RGGB = [R,G,G,B]    GRBG = [G,R,B,G]
GBRG = [G,B,R,G]    BGGR = [B,G,G,R]
```

Let `I(x,y)` be the incoming float32 Bayer sample and `cfa(x,y)` its color.
The gain-scaled plane is:

```text
S(x,y) = I(x,y) * gain[cfa(x,y)]
```

This evidence closes the use of the three supplied gains, not their public LRI
origin; that remains `CLM-AWB-001`.

## Border Extension

The source row accessor at `0x2ece10` clamps outside the declared image bounds
while preserving Bayer parity. Equivalently, extend each of the four CFA
sub-lattices independently by endpoint replication. This applies only to
underlying `S` reads. The lazy graph evaluates derived `P`, `H`, and `A` rows at
virtual coordinates through halos of four, three, and one pixels respectively.
The residual producer computes virtual vertical rows and uses asymmetric
horizontal guards `B(-1,y)=B(0,y)` and `B(width,y)=B(width-2,y)` on the installed
even-width surface.

## Guide Construction

Use the four axial directions
`D = {(-1,0),(1,0),(0,-1),(0,1)}`. For direction `d`, `2d` is the
same-color site two pixels away. Let `axis(d)` pair left/right directions
together and up/down directions together.

### Green-site stencil

At every green CFA site, construct `P` with this exact 21-tap stencil:

```text
P(x,y) = (
    56*S(x,y)
  +  6*sum S(x+dx,y+dy) over (dx,dy) = (+/-1,0),(0,+/-1)
  -  4*sum S(x+dx,y+dy) over (dx,dy) = (+/-1,+/-1)
  -  2*sum S(x+dx,y+dy) over (dx,dy) = (+/-2,0),(0,+/-2)
  +     sum S(x+dx,y+dy) over (dx,dy) =
          (+/-1,+/-2),(+/-2,+/-1)
) / 64
```

The coefficients sum to `64`; DC gain is exactly one. The constants are float32
`56`, `6`, `-4`, `-2`, and `1/64`. Instruction-level agreement also requires
the tap-addition order recorded in the corrective full-frame bundle; reducing
the taps by coefficient group is not bit-equivalent.

### First chroma-site guide

Set `H(p)=P(p)` at green sites. At a red or blue site `p`, let:

```text
C       = S(p)
far_d   = S(p + 2d)
mid_d   = P(p + d)
grad_d  = abs(P(p-left) - P(p+right))   for horizontal d
          abs(P(p-up)   - P(p+down))    for vertical d
eps1    = max(gain_R, gain_G, gain_B) / 1024
w_d     = rcp(abs(far_d - C) + grad_d + eps1)
delta_d = mid_d - 0.5*(C + far_d)

H(p) = C + sum_d(w_d*delta_d) / sum_d(w_d)
```

The SIMD body is `0x2ec9d0..0x2eca7a`.

### Refined Scalar Guide

Set `A(p)=H(p)` at red or blue sites. At green sites:

```text
C       = S(p)
farS_d  = S(p + 2d)
farH_d  = H(p + 2d)
adjH_d  = H(p + d)
eps1    = max(gain_R, gain_G, gain_B) / 1024
w_d     = rcp(abs(farS_d - C) + abs(adjH_d - H(p)) + eps1)
delta_d = 0.5*((H(p) - C) + (farH_d - farS_d))

A(p) = C + sum_d(w_d*delta_d) / sum_d(w_d)
```

The SIMD body is `0x2eccd0..0x2ecdbc`.

## Residual And RGB Reconstruction

The body at `0x2ee350` forms:

```text
B(x,y) = S(x,y) - A(x,y)
```

Its guard cells follow the derived-plane policy above, not the source
phase-preserving endpoint rule.
The final body gathers exactly four rows, not five:

```text
A(y-1), A(y), A(y+1), A(y+2)
B(y-1), B(y), B(y+1), B(y+2)
```

For pixel `p` and output channel `c`, define the contributor set:

```text
Q(p,c) = {p}                                   if cfa(p) = c
         two horizontal or vertical neighbors if p is green and c is R or B
         four axial neighbors                 if c = G and p is R or B
         four diagonal neighbors              for R-at-B or B-at-R
```

With:

```text
eps2     = max(gain_R, gain_G, gain_B) * 5/512
w(p,q)   = rcp(abs(A(p) - A(q)) + eps2)
RGB_c(p) = A(p) + sum(q in Q(p,c), w(p,q)*B(q))
                    / sum(q in Q(p,c), w(p,q))
alpha(p) = 1.0
```

For the direct measured channel, this reduces to `A(p)+B(p)=S(p)`.

## Runtime Replay

`runtime_unit1_28mm.json` captures one GRBG 2x2 output quad from the same thread
at `0x2eef80`, `0x2ef04d`, `0x2ef05e`, and `0x2ef480`. The verifier reconstructs
all twelve RGB values and four alpha values from the eight `A/B` row windows.
The render exits normally.

`guide_runtime_unit1_28mm.json` captures, on one thread:

- all 21 operands and output of the green-site stencil;
- the four `farS` / `midGuide` operands and output of the first chroma guide;
- the four `farS` / `farGuide` / `adjacentGuide` operands and output of the
  refined guide.

These local captures correctly recover the arithmetic operands, but the
original phase/site interpretation was superseded by the corrective bundle.
The captured
`eps1=0.0009765625` and `eps2=0.009765625` correspond to a sampled
`max_gain=1`.

The corrective replay compares complete installed and clean-room RGBA planes
on distinct-calibration Unit-1 and Unit-2 exact-`28mm` inputs: all
`51,916,800` float32 words match on each body. A tiled intermediate probe also
matches all `66,560` compared `A/B` words across top, interior, and bottom row
pairs. Those full-frame results, not the earlier local tolerance checks, are
the numerical closure authority.

## Reproduction

```bash
tools/lldb_probes/demosaic_light_v1/run_probe.sh
```

The durable harness is:

- `tools/lldb_probes/demosaic_light_v1/verify_demosaic_light_v1.py`
- `tools/lldb_probes/demosaic_light_v1/runtime_probe.py`
- `tools/lldb_probes/demosaic_light_v1/guide_runtime_probe.py`
- `tools/lldb_probes/demosaic_light_v1/unit1_28mm.lldb`
- `tools/lldb_probes/demosaic_light_v1/guide_unit1_28mm.lldb`

Current verifier result:

```text
PASS DemosaickLightV1 exact formula variants=4 runtime=1 guide_runtime=1
```

## Corrections To Quarantined Leads

Earlier scratch notes described five pyramid levels and treated the main-loop
pointers as per-level images. The installed body refutes that interpretation.
`r12` begins at `-0x20`, increments by eight, and exits when it reaches zero,
so `0x2eedd0..0x2eeeb2` executes exactly four times. The main-loop pointers are
four neighboring rows of `A` and four neighboring rows of `B`.

The scratch material was used only to identify candidate bodies. No claim here
depends on its conclusions.

## Scope And Exclusions

- **Formula scope:** all four Bayer phases in the installed renderer.
- **Zoom scope:** static renderer formula is zoom-independent; per-camera phase
  carriers were checked on exact-focal `28/35/70/150mm` LRIs from two physical
  units. Full-frame exact arithmetic replay is two-body exact-`28mm`.
- **Closed here:** taps, phase routing, supplied-gain application, both epsilon
  constants, guide equations, residual equation, borders, RGB reconstruction,
  alpha.
- **Not closed here:** public AWB origin/selection, upstream black-level and
  correction math, or downstream color conversion.
