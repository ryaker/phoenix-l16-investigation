# Static/Runtime Evidence: Index-5 Per-Level Projection Coordinates

**Date:** 2026-07-17  
**Status:** VERIFIED; admitted `CLM-STEREO-001` addendum  
**Bearing:** selected profile-3 mode-8 index-5 cost-volume construction

## Question

The full-resolution index-5 projection formula was already admitted, but the
coarse StereoLayer policy was not. An implementation had filled that gap with
a fitted level transform:

```text
H_level = diag(fx,fy,1) * H * diag(1/fx,1/fy,1,1)
```

That fit changed pixels and produced range extents that diverged beginning at
level 2. This bundle determines whether Lumen scales the projection record,
projects coarse coordinates directly, or first maps each coarse pixel into the
fixed source-image domain.

## Artifacts

- reusable LLDB capture:
  `tools/lldb_probes/index5_perlevel_projection_scale/perlevel_projection_probe.py`
- corpus runner:
  `tools/lldb_probes/index5_perlevel_projection_scale/run_lri.sh`
- installed/static plus eight-report verifier:
  `tools/lldb_probes/index5_perlevel_projection_scale/verify_perlevel_projection_scale.py`
- rerunnable raw reports:
  `runs/index5_perlevel_projection_scale/{unit1,unit2}_{28,35,70,150}mm/`
  (`unit2_150mm_retry` is the admitted successful tele capture)

The debugger used byte-identical temporary copies only to avoid macOS child
process access failures on the external volume. SHA-256 equality was checked
before capture. The durable proof does not depend on those temporary paths:
the repo-local harness can be rerun against any accessible LRI and the verifier
pins the installed binary plus retained report contents.

## Installed Formula

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

At `0x25e4e6..0x25e4f0`, the no-map projection-record constructor writes the
packed word `0x3f8000003f800000` to `record+0x48`, hence:

```text
record.scale_x = 1.0f
record.scale_y = 1.0f
```

The worker reads `step = StereoLayer+0x1c`. The y path at
`0x276e23..0x276e7c` and x path at `0x276f56..0x276fa8` independently compute:

```text
full_x = min(step * level_x + trunc(step / 2), Images.width  - 1)
full_y = min(step * level_y + trunc(step / 2), Images.height - 1)
```

The live level loops supply nonnegative coordinates and positive steps. The
resulting integer coordinates are converted to float32 and passed to the
already-admitted G-42 projection worker. No level-conjugated homography is
constructed or consumed on this path.

## Runtime Matrix

The post-`0x26a790` return probe captures each mode-8 layer only after all four
`0x50` projection records exist. Every one of the eight exact-focal body/focal
cells produced the same structural result:

| index | Guidance dimensions | `StereoLayer+0x1c` | each of 5 `Images` |
|---:|---:|---:|---:|
| 0 | `65x49` | 32 | `2080x1560` |
| 1 | `130x98` | 16 | `2080x1560` |
| 2 | `260x195` | 8 | `2080x1560` |
| 3 | `520x390` | 4 | `2080x1560` |
| 4 | `1040x780` | 2 | `2080x1560` |
| 5 | `2080x1560` | 1 | `2080x1560` |

Within every render:

- all four projection records have scale `(1.0f,1.0f)` at every level;
- each source's complete matrix/map/scale record is byte-identical across all
  six levels;
- all five sampled source descriptors stay at `2080x1560`; only Guidance and
  the reference iteration grid become coarse.

The runtime corpus is:

```text
Unit-1: 28mm, 35mm, 70mm, 150mm
Unit-2: 28mm, 35mm, 70mm, 150mm
```

The first Unit-2 150mm attempt stopped in the known debugger-induced tele
timing race at `libcp+0x2e8cc0` before any target packet. An unchanged retry
completed the six required captures and passed every invariant. The failed
attempt is not positive or negative data-path evidence.

## Clean-Room Rule

For each level pixel `(u_L,v_L)`, use the table's `step` to obtain the
full-source-domain reference coordinate:

```text
u = min(step*u_L + floor(step/2), 2079)
v = min(step*v_L + floor(step/2), 1559)
```

Then apply the unchanged full-domain projection record using the admitted
float32 correspondence:

```text
P = H * [u*d, v*d, d, 1]^T
```

Do **not** form `H_level = D*H*D^-1`, and do not sample coarse source-image
pyramids. This correction is load-bearing for coarse-level cost/range
construction.

## Scope and Admission

Admitted as a `CLM-STEREO-001` formula addendum for selected profile-3,
mode-8 levels 0 through 5:

- installed-static formula and constants are body/focal independent for the
  pinned bundle;
- runtime liveness and invariants are verified at all four exact focal tiers
  on both physical calibration bodies;
- body-specific projection coefficients are expected and are not claimed
  equal across bodies or captures;
- profiles 1/2, other stereo modes, different installed binaries, and
  structurally incomplete LRIs remain outside this admission.

## Verification

```text
$ python3 tools/lldb_probes/index5_perlevel_projection_scale/verify_perlevel_projection_scale.py
index5_perlevel_projection_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
levels=65x49,130x98,260x195,520x390,1040x780,2080x1560
image_coordinate_step=32,16,8,4,2,1
full=min(step*level_coord+trunc(step/2),image_extent-1)
Images=5x2080x1560 projection_scales=4x(1,1) records=invariant_across_levels
unit1_28mm=OK
unit1_35mm=OK
unit1_70mm=OK
unit1_150mm=OK
unit2_28mm=OK
unit2_35mm=OK
unit2_70mm=OK
unit2_150mm=OK
```
