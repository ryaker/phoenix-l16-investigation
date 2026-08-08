# Corrective DemosaickLightV1 Full-Frame Two-Body Replay

**Claim target:** `CLM-DEMOSAIC-002` corrective addendum  
**Installed binary:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Method:** SHA-pinned installed-body reinspection, tiled stopped-frame
intermediate capture, independent clean-room implementation, full-frame
bit comparison, and native SSE reciprocal cross-check  
**Scope:** exact numerical replay on distinct-calibration Unit-1 and Unit-2
exact-`28mm` A1 operands; installed formula is phase/body/focal independent;
public CFA phase carriers retain the prior two-body four-focal scope

## Why This Corrective Bundle Exists

The original admission correctly identified residual interpolation, the
21-tap coefficients, both directional equations, epsilon constants, and final
channel reconstruction. It interpreted two important implementation details
incorrectly:

1. it assigned the second directional correction to red/blue sites, but the
   installed worker applies it at green sites and retains the first correction
   at red/blue sites; and
2. it generalized the source row accessor's phase-preserving endpoint clamp to
   the derived guide/residual planes, but the lazy row graph evaluates those
   planes at virtual coordinates with finite halos.

The earlier stopped-frame checks were local and tolerant enough to admit that
wrong interpretation. The clean-room implementation that followed the prose
mismatched `8,534,575/12,979,200` level-0 scalar pixels. This bundle replaces
that interpretation with full-frame, two-body, bit-exact proof.

## Corrected Construction

Let `S(x,y)` be the gain-scaled scalar CFA source. Only accesses to `S` use
phase-preserving endpoint replication. Let `P`, `H`, and `A` be derived planes.

1. Evaluate the 21-tap green guide `P` at green sites. To satisfy later lazy
   requests, evaluate it through a four-pixel virtual halo. Each `P` sample
   still reads its underlying `S` taps through the source clamp.
2. At green sites set `H=P`. At red/blue sites apply the first four-direction
   correction and evaluate `H` through a three-pixel virtual halo.
3. At red/blue sites set `A=H`. At green sites apply the second/refined
   four-direction correction and evaluate `A` through a one-pixel virtual halo.
4. Form `B=S-A` for core and virtual vertical rows. The residual producer's
   horizontal guards are asymmetric: `B(-1,y)=B(0,y)` and
   `B(width,y)=B(width-2,y)` for the even `4160`-pixel surface.
5. Perform the admitted inverse-gradient residual reconstruction from `A/B`.

The directional equations remain those in the base bundle, with corrected
site ownership. At a red/blue site `p`, the first correction is:

```text
C       = S(p)
far_d   = S(p + 2d)
mid_d   = P(p + d)
grad_d  = abs(P(p-left)-P(p+right))  for horizontal d
          abs(P(p-up)-P(p+down))     for vertical d
w_d     = rcpss((grad_d + eps1) + abs(far_d-C))
delta_d = mid_d - 0.5*(C + far_d)
H(p)    = C + rcp(sum_d w_d) * sum_d(w_d*delta_d)
```

At a green site `p`, the refinement is:

```text
C       = S(p)
farS_d  = S(p + 2d)
farH_d  = H(p + 2d)
adjH_d  = H(p + d)
w_d     = rcpss((abs(farS_d-C) + eps1) + abs(adjH_d-H(p)))
delta_d = 0.5*((H(p)-C) + (farH_d-farS_d))
A(p)    = C + rcp(sum_d w_d) * sum_d(w_d*delta_d)
```

All sums preserve installed float32 pairings. In particular, the 21-tap
worker does not reduce taps by coefficient group. With `axial1`, `diagonal1`,
and `axial2` each paired in installed order, it evaluates:

```text
v  = 6*axial1
v += 56*S(x,y)
v += -4*diagonal1
v += S(x-1,y-2)
v += -2*axial2
v += S(x+1,y-2)
v += S(x-2,y-1); v += S(x+2,y-1)
v += S(x-2,y+1); v += S(x+2,y+1)
v += S(x-1,y+2); v += S(x+1,y+2)
P  = v * (1/64)
```

Changing that ordering alone leaves `5,056` one-ULP output differences on the
Unit-1 full-frame operand, so it is implementation-relevant.

## Runtime And Clean-Room Results

The installed A1 demosaic output and the independent Phoenix replay are equal
word for word on both physical calibration signatures:

| Input | RGBA float32 words | Mismatches | SHA-256 |
|---|---:|---:|---|
| Unit-1 exact-`28mm` `2018-07-23/L16_02130` | `51,916,800` | `0` | `70c14c383a89d2368bb6827a05a075ab457df85c8ca4b02842685733ae55b810` |
| Unit-2 exact-`28mm` `2018-07-04/L16_02130` | `51,916,800` | `0` | `de242b171af796aa17ee9c642a756a9fb9f74865c4ff2ea6945d85903cfbb9c6` |

Each replay also matches the installed downstream level-0 scalar operand at
all `12,979,200` pixels. The bodies have distinct public RAW payloads,
calibration signatures, vignetting grids, exposure ratios, and output hashes.

A separate tiled stopped-frame capture stitches eight worker tiles at each of
four output row pairs (`y=0/1`, `100/101`, `1560/1561`, and `3118/3119`). The
clean-room `A` guide and `B` residual planes match all `66,560` compared core
float32 words bit for bit, including `1,792` words adjacent to internal tile
edges. The capture retains `137,216` halo words for boundary auditing; this
count is custody, not a claim that every retained halo word was compared.

Finally, the x86_64 test invokes hardware `_mm_rcp_ss` under the same Rosetta
environment as the installed renderer and matches the portable reciprocal for
`98,304/98,304` representative normal values. This independently rules out an
ARM/x86 reciprocal difference as the source of the prior mismatch.

## Reproduction

Capture and verify installed guide/residual rows:

```bash
tools/lldb_probes/prefusion_monofusion_flow_origin/run_reference_guide_rows_unit1_28mm.sh
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_reference_guide_rows.py \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_guide_rows/report.json \
  /path/to/cleanroom_guide.f32le /path/to/cleanroom_residual.f32le
```

Compare each full-frame installed capture with a clean-room RGBA dump:

```bash
python3 tools/lldb_probes/prefusion_monofusion_flow_origin/verify_demosaic_fullframe.py \
  runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_operand/a1_reference_source.f32x4le \
  /path/to/cleanroom_rgba.f32x4le
```

The clean-room replay executable is built from the Phoenix source tool
`tools/validate_a1_reference_level0.cpp`; it decodes each LRI from public wire
fields and accepts the installed level-0 capture only as its final oracle.

## Admission Scope

- **Exact runtime arithmetic:** Unit-1 and Unit-2 exact-`28mm`, complete
  `4160x3120` A1 frames.
- **Intermediate runtime arithmetic:** Unit-1 exact-`28mm`, four complete row
  pairs spanning top, interior, and bottom worker boundaries.
- **Installed-static scope:** all four CFA phases; formula has no body/focal
  selector.
- **Public carrier scope:** exact-focal two-body `28/35/70/150mm` from the
  existing raw-layout bundle.
- **Not claimed:** other libcp builds or firmware invariance, profiles that
  select a different demosaic, or upstream correction/public-AWB semantics.
