# Lane B2 addendum — cam0 calibration record field map (independently verified)

**Status:** `NEEDS_CODEX_VALIDATION`. Field structure + decoded values **independently reproduced**
(deterministic nested-protobuf walk, 28mm Unit-1 seed, camera-0) — upgrades the README's subagent
CANDIDATEs to OBSERVED-structure. Semantic *names* remain CANDIDATE (strongly value-supported).
`tools/lri_field_inspect.py`; field path = nested proto field numbers; f32 = wire-type-5 fixed32.

## Verified field map (LRI Block 3, field-13[0] = camera 0)

```
f1            = 0
f3.1          = 0                         (small/large record discriminator: 0 small, 2 large)
f3.2[scale]   per-scale intrinsics block, scales seen: f3.2.1 = 818.0 and 1500.0
  f3.2.2.1.1..9 = [3375.884, 0, 2084.516, 0, 3375.884, 1541.342, 0, 0, 1.0]
                 = 3x3 pinhole intrinsics K = [fx 0 cx; 0 fy cy; 0 0 1]   (CANDIDATE name; layout exact)
                   fx=fy=3375.884, cx=2084.516 (≈4160/2), cy=1541.342 (≈3120/2)
  f3.2.4        = 60 / 62   (unknown varint)
  f3.2.6        = 8707.0 / 9654.0  (unknown f32)
  (3rd f3.2 entry, scale 818: f3.2.3.1.1 = identity 3x3 + extra — the large-record size delta lives here)
f3.3          distortion / projection model
  f3.3.1.1    = (2063.0, 1534.0)          (CANDIDATE principal point at half-res)
  f3.3.1.2    = (4160.0, 4160.0)          (CANDIDATE sensor dims / normalizer)
  f3.3.1.3    = [0.0326, 0.1501, 0.0, 0.0, -0.5774]   (5 coeffs; CANDIDATE Brown-Conrady [k1,k2,p1,p2,k3])
  f3.3.1.5    = varints (18,14,4125,3093) (unknown)
  f3.3.2.5    = 101-entry (x,y) curve, x: 0→2.89 monotonic, y: 0→31.65→29.7  (CANDIDATE radius→correction LUT)
  f3.3.2.6    = 30-entry (x,y) curve, x: 0→2.9, y: 0→-0.024  (CANDIDATE second correction/vignette LUT)
  f3.3.2.{2,3,4,9,10} = 3.7003, 2.557, 0.0011, 8707.0, 0.0004  (unknown scalars)
f3.4          = (-1.0, -1.0)              (CANDIDATE sentinel)
f3.5          = (100.0, 54000.0)          (CANDIDATE exposure/range pair)
f7            = (2017, 11, 4, 17, 47, 16) (CANDIDATE calibration date 2017-11-04 17:47:16)
```

## Confidence

- **OBSERVED (byte-reproduced):** the field nesting, the 9-value 3×3 matrix in exact K layout
  (`[fx 0 cx; 0 fy cy; 0 0 1]`, per-scale), the 5-coeff distortion vector, the two (x,y) LUT curves, and
  the date tuple — all decoded deterministically from the bytes.
- **CANDIDATE (semantic names):** "intrinsics K", "principal point", "Brown-Conrady k1..k3", "radius→
  correction LUT", "calibration date" — inferred from value plausibility (cx≈w/2, cy≈h/2, monotonic
  radius axis, valid date). The proto-field→public-name mapping is confirmable only via the libcp
  accessor disasm (Codex's side); not done here.

## Clean-room relevance
All of this is **LRI-resident** per-camera calibration → clean-room Phoenix parses it at render time
(Rule #0 source class 1); standard pinhole+Brown-Conrady undistort is reimplementable from formula. No
libcp bytes needed for the intrinsics/distortion path.

## Non-claims
- Camera-0 only (other cams differ by tier fx, per `four_zoom_two_unit.md`); the field STRUCTURE is shared.
- Semantic names unproven; binary consumer untouched (Codex's `0x23faf0` thread).
