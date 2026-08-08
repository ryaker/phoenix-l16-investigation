# MonoFusion Mode-0 Flow-Field Formula: Installed Static + Two-Body Runtime Proof

**Claim:** `CLM-PREFUSION-002` corrective addendum  
**Result:** `PROVEN` for canonical profile-3 MonoFusion mode `0`, with the scope below  

> **Later corrective closure:** this bundle replays from captured operand
> pyramids. The public-input level-0 joins and exact inter-level FastCollapse
> producer are closed separately by
> `bundle_static_runtime_prefusion_monofusion_operand_pyramid_two_body.md`.
> Read both bundles for a clean-room flow implementation.
>
> **Packed-consumer correction:**
> `bundle_static_runtime_prefusion_monofusion_mode0_patch_terminal_exact_replay.md`
> closes the subsequent float-flow to mode-0 descriptor conversion. Each
> component is truncated toward zero and its signed 16-bit low word is stored;
> rejected sentinel-derived values wrap rather than saturate. The earlier
> float-vector replay alone did not state this consumer-visible consequence.
**Installed binary:** `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`  
**SHA-256:** `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

## Question

The prior mode-0 admission decoded the wavelet/Wiener worker but did not state
how its per-8-pixel signed flow was constructed. This matters: replacing the
flow with zero displacement changes which A2 pixels enter every aligned
`16x16` MonoFusion patch.

This bundle closes that omitted numerical path from the two input `uint16`
pyramids through the final `519x389` float32 flow field and its public
vignetting/gain-derived rejection rule.

## Evidence Inputs

Two same-name, exact-28mm photographs from different physical calibration
signatures were captured independently with `.lris` auto-loading disabled:

| Scope | LRI | LRI SHA-256 |
|---|---|---|
| Unit-1 exact 28mm | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` | `2ac51af5c219639638ba34bb98975b62ee922331214043a938a7c37052700ff5` |
| Unit-2 exact 28mm | `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` | `faba5ceee50a6b4b3d3f58b7d725a320158270b26475a591b1f6853698a321ad` |

The reusable harness is under
`tools/lldb_probes/prefusion_monofusion_flow_origin/`. Runtime captures are
written beneath ignored `runs/prefusion_monofusion_flow_origin/`; they are
rerunnable artifacts, not the sole authority for this document.

Static inspection is against the SHA-pinned installed image. The principal
installed surfaces are:

- producer `0x1991e0`, reached from the mode-0 `0x1b17c0` family;
- stage boundaries `0x19955e`, `0x199840`, `0x1998e9`, `0x199995`, and
  `0x199af0`;
- quadratic subpixel helper `0x190da0`;
- final overlap worker family `0x197ba0`, including callback dispatch at
  `0x19802a`;
- rejection callback `0x1b3490`; and
- threshold-map construction at `0x1b1c1a`, which calls the already classified
  `0xfc2f0` `RemoveVignettingGeneric` path.

## Exact Pyramid and Stage Topology

Both bodies expose the same live five-level `uint16` operand dimensions:

```text
level 0: 4160 x 3120
level 1: 2080 x 1560
level 2:  520 x 390
level 3:  130 x 97
level 4:   32 x 24
```

The mode-0 flow builder executes these stages in order:

| Stage | Input level | Patch / spacing | Local radius | Output |
|---|---:|---:|---:|---:|
| initial | 4 | `8x8 / 8` | 8 | `4x3` |
| refine 1 | 3 | `8x8 / 8` | 4 | `16x12` |
| refine 2 | 2 | `16x16 / 16` | 8 | `32x24` |
| refine 3 | 1 | `16x16 / 16` | 4 | `130x97` |
| overlap final | 0 | `16x16 / 8` | 2 | `519x389` |

Every candidate cost is unsigned-`uint16` patch SAD accumulated into an
integer:

```text
SAD(bx,by,sx,sy,P) =
    sum(y=0..P-1, x=0..P-1,
        abs(int32(reference[by+y,bx+x]) - int32(source[sy+y,sx+x])))
```

Candidate traversal is `dy` outer, `dx` inner, with strict `<` replacement.
This tie policy is observable and is required for exact replay.

For each non-initial coarse stage at output grid coordinate `(gx,gy)`:

1. Set reference origin `(bx,by)=(gx*P,gy*P)`.
2. Set prior coordinate `(px,py)=(gx//4,gy//4)`.
3. Visit the clamped `3x3` prior neighborhood in `dy,dx` order.
4. For each prior vector `v`, form source origin
   `(bx+trunc(v.x*4), by+trunc(v.y*4))`, then clamp each axis to
   `[0, source_extent-P-1]`.
5. Select the strict minimum-SAD predictor.
6. Search the square local radius around that predictor. Local candidate
   origins are valid through `source_extent-P` inclusive.
7. If all nine costs around the winning local integer position exist, apply
   `0x190da0`; otherwise use subpixel `(0,0)`.
8. Store, in exact float32 nested-add order,
   `predictor_displacement + (local_displacement + subpixel)`.

The initial stage performs the same strict `dy,dx` radius-8 search around the
identity source origin and then applies the same optional quadratic fit.

## Exact Quadratic Fit

Let `a0..a8` be the ordinary row-major `3x3` SAD neighborhood, converted to
float32. Every operation below rounds to float32 in written order:

```text
hyy = max(0,
    4*a0 - 8*a1 + 4*a2 + 8*a3 - 16*a4 + 8*a5
    + 4*a6 - 8*a7 + 4*a8)

hxx = max(0,
    4*(a0+a2) - 8*a3 - 8*a5 + 4*a6 + 4*a8
    - 16*a4 + 8*(a1+a7))

hxy = 4*((a0-a2-a6)+a8)
det = hxx*hyy - hxy*hxy
if not (0 < det): hxy = 0
det = hxx*hyy - hxy*hxy
if det == 0: return (0,0)

gy = -2*a0 + 2*a2 - 4*a3 + 4*a5 - 2*a6 + 2*a8
gx = -2*a0 - 2*a2 + 2*a6 + 2*a8 - 4*a1 + 4*a7

dx = (hxy*gx - hxx*gy) / det
if abs(dx) >= 1: return (0,0)
dy = (hxy*gy - hyy*gx) / det
if abs(dy) >= 1: return (0,0)
return (dx,dy)
```

The verifier preserves the scalar SSE grouping rather than relying on the
algebraically flattened display above. All 64 captured fits, 32 per body,
match both float32 result words exactly. The following installed constants
are also byte-verified: `1` at `0x5a8128`, absolute-value mask `0x7fffffff`
at `0x5a81f0`, `4/-2/-4` at `0x5a8870/74/78`, `8` at `0x5a9b0c`, and `-16`
at `0x5aae78`.

## Exact Final Overlap Stage

At final grid `(gx,gy)`:

1. Set `(bx,by)=(8*gx,8*gy)` and prior coordinate
   `(px,py)=(gx//4,gy//4)` in the `130x97` stage.
2. Visit its clamped `3x3` neighborhood in `dy,dx` order.
3. Form each predictor source origin as
   `(bx+trunc(2*v.x), by+trunc(2*v.y))`, clamp to
   `[0,width-17] x [0,height-17]`, and select the strict minimum 16x16 SAD.
4. Search integer offsets `[-2,2]^2` around that predictor, with valid source
   origins through `(width-16,height-16)` inclusive, again using strict `<`.
5. There is no final quadratic fit. An accepted vector is the integer total
   displacement from `(bx,by)` to the winning source origin.

The rejection callback is evaluated on the **predictor source origin before
the local radius-2 refinement**, not on the reference origin or final source
origin. `0x197fbc..0x19802a` statically proves the minimum-SAD and normalized
predictor-coordinate argument construction.

## Public Rejection Origin and Formula

The mode-0 owner builds an in-place `4160x3120` scalar map by evaluating the
selected reference camera's public vignetting calibration through
`RemoveVignettingGeneric` with rectangle `[0,0,4160,3120]`, multiplier `1`,
and inverse flag `0`. At every checked pixel on both bodies, the runtime map
word equals clean-room interpolation of the selected public `17x13`
vignetting profile at exact 260-pixel node spacing.

For public `CameraModule.sensor_analog_gain = G`, the installed owner stores:

```text
c = clamp(f32((f32(G)-1) * f32(0.3333333432674408)), 0, 1)
T = f32(f32(30*c) + 30)
M = f32(T * 256)
```

For predictor source origin `(sx,sy)`, the callback executes:

```text
nx = f32(f32(sx) / f32(width))
ny = f32(f32(sy) / f32(height))
mx = clamp(trunc_i32(f32(f32(width)  * nx)), 0, width-1)
my = clamp(trunc_i32(f32(f32(height) * ny)), 0, height-1)
limit = f32(sqrt_f32(vignetting_map[my,mx]) * M)
reject = (limit < f32(minimum_SAD))
```

The comparison is strictly below. On rejection, the local worker returns
float32 `-1000000` in both axes and the wrapper separately float32-adds the
predictor displacement. This explains the observed values around, but not
necessarily equal to, `-1000000`.

The public joins differ materially by body:

| Scope | Selected public calibration camera | Analog gain | `T` | `M` |
|---|---:|---:|---:|---:|
| Unit-1 exact 28mm | 12 | 1.0 | 30.0 | 7680.0 |
| Unit-2 exact 28mm | 4 | 3.875 | 58.75 | 15040.0 |

Selection uses the live calibration-vector position. Camera ID is the public
identity reached after that selection; it is not interchangeable with vector
position.

## Deterministic Replay Results

`verify_multistage_flow_replay.py` independently rebuilds all four coarse
stages from the captured input pyramids and matches each output float32 pair
bit-for-bit:

```text
initial:       12 / 12
refine 1:     192 / 192
refine 2:     768 / 768
refine 3:  12,610 / 12,610
total:     13,582 / 13,582 per body
```

`verify_final_overlap_replay.py` then independently rebuilds every final
candidate, public threshold/map decision, sentinel result, and wrapper add:

| Scope | Bit-exact vectors | Rejected | Minimum-SAD range |
|---|---:|---:|---:|
| Unit-1 exact 28mm | `201,891 / 201,891` | 73,073 | 37..226,578 |
| Unit-2 exact 28mm | `201,891 / 201,891` | 521 | 1,890..164,111 |

The complete result is `215,473 / 215,473` vectors per body and
`430,946 / 430,946` across the two bodies. The very different rejection
counts also refute a body-independent fixed mask, fixed confidence, or
zero-residual-flow substitute.

Captured final-oracle SHA-256 values are:

- Unit-1: `80838182f86d2ff939bd4c4049930edee1e3a4b9eb335d09fedb2201f5b850d3`
- Unit-2: `02f66a3ceff6679e67ea523f9548ba7082f30d7a055ef71b96fa98f384d08843`

## Reproduction

After producing the runtime captures with `run_stages.sh`,
`run_quadratic.sh`, and `run_threshold_map.sh`, the independent checks are:

```bash
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_multistage_flow_replay.py \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_stages

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_quadratic_formula.py \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_quadratic/quadratic.json \
  /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_threshold_map_public_origin.py \
  --lri "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  --report runs/prefusion_monofusion_flow_origin/unit1_28mm_threshold/threshold_map.json

python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_final_overlap_replay.py \
  --stage-dir runs/prefusion_monofusion_flow_origin/unit1_28mm_stages \
  --lri "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  --threshold-report runs/prefusion_monofusion_flow_origin/unit1_28mm_threshold/threshold_map.json
```

Use the Unit-2 paths listed above for the independent second-body replay.

## Admission Scope

- **Numerical runtime proof:** exact-focal `28mm` on both physical calibration
  bodies, two different scenes and different public gain/vignetting values.
- **Installed formula scope:** the SHA-pinned mode-0 bodies are not
  body-specific or focal-specific.
- **Canonical four-focal route scope:** prior admitted runtime proof shows
  profile-3 `28mm` and `35mm` select this same MonoFusion mode-0 path, while
  canonical `70mm` and `150mm` construct no MonoFusion and use direct B4.
- **Not claimed:** numeric equality between bodies, a separate full-vector
  replay at `35mm`, any cause attributed to capture date or firmware, or the
  formula of MonoFusion mode `1` used by compatibility profiles `1/2`.

## Canonical Consequence

`CLM-PREFUSION-002` can remain `PROVEN` / `SPEC_READY` for canonical profile
3, but only with this correction attached. A clean-room implementation must
construct and consume this live multistage flow and public rejection mask;
using zero residual gather is not equivalent to the admitted Lumen path.
