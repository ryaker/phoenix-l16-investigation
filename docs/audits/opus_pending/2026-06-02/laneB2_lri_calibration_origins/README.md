# Lane B2 — LRI per-camera calibration block (Blocker 2: calibration origins)

**Status:** `NEEDS_CODEX_VALIDATION`. LRI-file (input-side) investigation — deliberately stays on the LRI
bytes, NOT the libcp consumer (`0x23faf0` etc. = Codex's live thread), to avoid collision. WSJF #4.
Tool: `tools/lri_field_inspect.py`. Seed: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (28mm,
Unit-1). **Confidence split:** values I independently byte-reproduced = OBSERVED; sub-field→meaning
labels (from a subagent read, not all re-verified) = CANDIDATE.

## OBSERVED (independently byte-reproduced)

- **Intrinsics block = the smallest 16×field-13 LELR block = Block 3** (payload 32,832 B; sha256[:16]
  `722a6e72…` = Unit-1). 16 records = 16 cameras.
- **Camera-0 intrinsics values present as float32 in its record:** `fx = fy = 3375.884`,
  `cx = 2084.516` (≈ 4160/2 = 2080), `cy = 1541.342` (≈ 3120/2 = 1560), and `4160.0` (sensor width).
  Principal point ≈ image center. (Found by direct value search; the values are stored as **tagged
  protobuf fixed32 fields**, not a contiguous 9-float matrix.)
- **Focal-tier clustering across the 16 cameras (by dominant fx):**
  cams 0–4 fx ≈ 3369–3377; cams 5–9 fx ≈ 8284–8309; cams 10–15 fx ≈ 18638–18795. This is the canonical
  **L16 5 + 5 + 6 = 16** camera layout (5 wide / 5 mid / 6 tele), byte-confirmed per camera.
- **Two record-size classes** (8 records 1944 B, 8 records 2149 B) — the split does NOT align with the
  5/5/6 focal tiers, so record size encodes something orthogonal to focal length (unknown).

## CANDIDATE (subagent read; values plausible, NOT all re-verified here)

- `field-13[i].f7` = a Y/M/D/h/m/s tuple ⇒ **calibration date** (cam0: 2017-11-04 17:47:16).
- `f3.f2` entries hold a **3×3 pinhole intrinsics K** `[fx 0 cx; 0 fy cy; 0 0 1]` at per-scale entries
  (scale values 818.0, 1500.0 seen) — supported by the OBSERVED fx/cx/cy values above.
- `f3.f3` = **distortion / projection model**: header floats `(4160,4160)` + a 5-float vector
  `[0.0326, 0.1501, 0, 0, -0.5774]` (CANDIDATE radial distortion k1..k5) + a **101+30-entry (f32,f32)
  LUT** (CANDIDATE radius→correction curve, monotonic).
- Block 3 also carries ASCII `"L16"` (field 8) and `"Light Labs"` (field 18).
- **Other calibration-bearing blocks:** Block 4 (larger 16×field-13 = CANDIDATE distortion block),
  Block 6 (42×field-13 = unknown), Block 0/2 (LightHeader-class metadata). **No color-matrix / AWB / tone
  block positively identified** — consistent with the A5 post-merge 3×3 color matrix being runtime/per-LRI
  but sourced elsewhere or computed.

## Why it matters (Blocker 2)

Blocker 2's open item is "LRI calibration origins" for the warp/intrinsics fields. This locates the
per-camera intrinsics (K) + distortion in **Block 3** of the LRI and confirms the values are
LRI-resident (parse-at-render-time) — clean-room-friendly (Rule #0 source class 1). It does NOT prove how
libcp consumes them (that's the binary side / Codex's `0x23faf0` thread).

## Non-claims
- Single file (28mm Unit-1); not cross-checked vs 35/70/150mm or the Unit-2 twin.
- All `f3.*` sub-field meanings are CANDIDATE (value-plausibility only); the protobuf-field→public-name
  mapping needs the libcp accessor disasm to confirm — explicitly Codex's side, not done here.
- The distortion coeffs / LUT / date were read by a subagent and are NOT independently re-verified in this
  packet (only the fx/cx/cy values and the focal-tier clustering were). Treat accordingly.
- `commands.txt` reproduces the OBSERVED items.
