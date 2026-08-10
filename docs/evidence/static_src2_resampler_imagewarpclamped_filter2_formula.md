# Static Evidence: src2 Resampler Formula (ImageWarpClamped<ResamplerFilter=2, vec4x32f>)

**Date:** 2026-08-10
**Installed libcp SHA-256:** `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
**Worker:** `0x3ed2e0` (the `PipelineCache::processLevel1` callback pinned in
`bundle_static_runtime_prefusion_src2_processlevel1_identity_four_zoom.md` as
`0x65f7e8/+0x30`; objdump mislabels it `CIAPI::PropertyAccessor::transform` from
symbol drift).
**Bearing:** CLM-PREFUSION-002 src2 stereo-plane resample -- the geometry gap that
`stage_a_boundary_closure_*` localized (Phoenix's envelope-fit approximation vs
this exact warp).

## What was OPEN and is now closed (static)

The ledger left "the exact upstream src1/src2 merge/reduction ... math open."
This bundle closes the src2 RESAMPLE math by disassembly of `0x3ed2e0`. The
per-output-pixel operation, over integer output (col,row) with a coordinate-
transform struct `T = *(src+0x1e0)`:

```text
# 1. projective transform (3x3 homography stored at T+0x28..0x48)
q1 = f32(col) + base_x
q2 = f32(row) + base_y
X  = T[0x28]*q1 + T[0x2c]*q2 + T[0x30]
Y  = T[0x34]*q1 + T[0x38]*q2 + T[0x3c]
W  = T[0x40]*q1 + T[0x44]*q2 + T[0x48]
iw = 1.0f / W                      # const 1.0f @ 0x5a8128
xu = X*iw - T[0x20]                # subtract center x  (T+0x20)
yu = Y*iw - T[0x24]                # subtract center y  (T+0x24)

# 2. radial distortion LUT (4096-entry), indexed by integer radius
r   = sqrt( (T[0x00]*xu)^2 + (T[0x04]*yu)^2 )   # T[0],T[4] = per-axis scale
idx = min( trunc_i32(r), 0xfff )                # clamp to 4095
f   = T[0x08][idx]                              # LUT base pointer = T+0x08
xd  = xu * f
yd  = yu * f

# 3. recombine to source sample coordinate (tile origin + bicubic support -1)
sx = (-1.0f) - src_base_x + <affine tap x> + xd     # const -1.0f @ 0x5a8124
sy = (-1.0f) - src_base_y + <affine tap y> + yd
sx *= 64.0f ; sy *= 64.0f          # const 64.0f @ 0x5d6368 (subpixel fixed-point)
ix = trunc(sx) >> 6 ; iy = trunc(sy) >> 6          # integer base cell
# low 6 bits of trunc(sx),trunc(sy) are the 1/64 subpixel fraction

# 4. ResamplerFilter=2 = 4x4 BICUBIC (cubic-Lagrange) gather
#    taps ix .. ix+3 and iy .. iy+3, each edge-CLAMPED to [0, extent-1],
#    each sample a vec4x32f (16-byte movaps), 16 taps total, out-of-bounds
#    reads clamped (ImageWarpCLAMPED).
```

Confirmed constants (read from the installed image): radial LUT is 4096
entries (`cmp 0x1000 -> cmov 0xfff`); perspective numerator `1.0f`; the
subpixel scale is `64.0f` (six fraction bits, `sar $0x6`); the coordinate
origin term is `-1.0f`. The 4x4 tap gather with per-axis `cmovg/cmovge` bound
clamps is the bicubic support with edge clamp.

## Port bearing (Phoenix already has every piece)

This is the exact operation Phoenix approximates with `undistortPlaneEnvelopeU8x4`
(a uniform scale+origin envelope fit). The proven form is projective-H +
4096-radial-LUT + 4x4 bicubic, and Phoenix already ships:
- `engine/premerge/undistort.cpp` -- Brown-Conrady + 4096-entry cubic-Lagrange
  radial table;
- `engine/premerge/catmull_rom.h` -- the bicubic (cubic-Lagrange) kernel;
- `engine/depth/projection_record.*` -- the 3x3 H.

The port is to wire this exact warp (H + per-camera radial LUT + bicubic,
1/64 subpixel, edge clamp) as the stereo-plane resample in place of the
envelope-fit approximation.

## Still to close before porting (one operand capture, NOT a guess)

The static FORM is closed; the OPERANDS in `T = src+0x1e0` are not yet
captured. Before porting, one runtime capture on the deterministic u2_70
render must pin, per source: the 3x3 H bytes (T+0x28..0x48), the center
(T+0x20/0x24), the per-axis scale (T+0x00/0x04), and the 4096-entry LUT
(T+0x08) -- to confirm H equals the composed stereo projection record and the
LUT equals the public per-camera radial table (vs a src2-specific composition).
Porting the form with unconfirmed operands would be a guess; capturing them
first is the closure.

## Scope

Static single-worker disassembly of `0x3ed2e0` on the pinned installed libcp;
joins the already-admitted `processLevel1` identity bundle. It does not yet
claim the runtime operand values, the distributed reduction that consumes the
resampled level-1 output, or final acceptance/rejection.

## Addendum (same date): OPERANDS captured (u2_70 B4 anchor)

`tools/lldb_probes/src2_resampler_operands/src2_warp_operand_probe.py` at worker
ENTRY `0x3ed2e0`, T = *( *( *(rdi+0x20) ) + 0x1e0 ), deterministic u2_70 render.
The render invoked this worker ONCE (exit 0), consistent with the admitted fact
that visible src2 is the tier-anchor camera only (B4 tele); the four non-anchor
sources use a different resample path.

Captured T operands (`runs/src2_resampler_operands/u2_70mm/report.json`):

```text
scale_xy  = (1.0, 1.0)                      # T+0x00, T+0x04
center_xy = (2020.0, 1505.0)                # T+0x20, T+0x24
H (T+0x28..0x48) = [ 0.991346  0.0       17.0 ]
                   [ 0.0       0.991346  13.0 ]
                   [ 0.0       0.0        1.0 ]   # pure AFFINE, no perspective
radial LUT (4096f @ T+0x08): LUT[0]=1.0, min 0.999908, max 1.008506
   (idx 1->1.000005, 256->1.000125, 1024->1.0024, 2048->1.008506, 4095->0.999908)
```

### Bearing (corrects the pre-capture port hypothesis)

The pre-capture guess was "projective H + strong radial LUT; port
undistort.cpp." The measurement REFUTES the strong-distortion part for the
anchor resample:

1. H is a UNIFORM-SCALE AFFINE, not a projective homography. The scale
   `0.991346` is EXACTLY `4124/4160` -- the value Phoenix already pins as its
   envelope-fit scale (`computeEnvelopeFit`, TRUTH.md matrix class). Phoenix's
   envelope fit is therefore the PROVEN anchor affine, not an approximation of
   a different transform. Translation (17,13) and center (2020,1505) are the
   box-origin operands the envelope already models.
2. The radial LUT is NEAR-IDENTITY (<=0.85% at its peak, sub-0.01% for the
   inner ~half-radius). Phoenix's envelope omits this sub-1% radial term; it is
   the only proven-but-unported component of the ANCHOR resample.

So the stage-A anchor-plane residual is dominated by (a) this <=0.85% radial
LUT, and (b) resampling-kernel differences (Lumen's 4x4 bicubic at 1/64
subpixel vs Phoenix's envelope resampler), NOT a missing projective/strong-
distortion warp. The port surface for the anchor shrinks to: apply the captured
near-identity radial LUT and match the 4x4 bicubic/subpixel kernel.

### Still open

The four NON-anchor source planes do not pass this worker; their resample
worker/operands are not yet captured. Whether their transforms are also affine
(with the inter-camera R/t baked into H) or projective is the next capture.
