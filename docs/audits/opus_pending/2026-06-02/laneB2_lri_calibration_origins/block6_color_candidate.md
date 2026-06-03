# Lane B2 addendum — Block 6 (42×field-13): candidate color-calibration block

**Status:** `NEEDS_CODEX_VALIDATION`. Structure OBSERVED (byte-reproduced, 28mm Unit-1); the
color-calibration interpretation is **CANDIDATE** (row-sum signature). LRI-input side only.

## OBSERVED structure

LRI Block 6 (payload 35,266 B) = **42 field-13 records** in two size classes: **14 × 1472 B** + **28 ×
519 B**. Each record (`f13[i]`) has:
- `f2.1` = small int (varint),
- **`f2.2` = a 3×3 float matrix** (9 fixed32),
- **`f2.3` = a 3×3 float matrix** (9 fixed32),
- `f2.4`, `f2.5` = scalars,
- `f2.6` = a repeated list of 3-float vectors (many entries).

**Row-sum signature (the key observation):** across ALL records (big and small), the `f2.2`/`f2.3`
matrices share **fixed row-sums ≈ (0.964, 1.0, 0.825)** even though the individual entries vary per
record. Example `f2.2` rows: cam-rec [0.8996,0.1317,−0.0671]/[0.31,1.0739,−0.384]/[−0.0572,−0.4301,1.3125].

## CANDIDATE interpretation

Fixed per-row sums with varying entries is the signature of a **color transform / color-correction
matrix (CCM)** family (a white/channel-preserving 3×3 applied to RGB). So Block 6 is a **candidate
per-camera-group color-calibration block** — two 3×3 matrices per record (CANDIDATE: a forward + inverse,
or two color stages) plus a 3-vector list (CANDIDATE: color samples / patch references).

This matters because:
- B2's README noted "no color-matrix/AWB/tone block positively identified" — Block 6 is now the leading
  **candidate** for the LRI color-calibration origin.
- It is a plausible **LRI source for the A5 post-merge runtime `__bss` 3×3 color matrix** (which is
  computed per-render, not embedded) — i.e. that runtime matrix may be derived from these LRI matrices.

## Non-claims / open
- The (14, 28, 42) grouping does NOT map to the 16 cameras; the per-record grouping semantics are
  **unknown** (not per-camera). Do not assume per-camera.
- "Color-correction matrix" is CANDIDATE from the row-sum signature only; could be another linear color/
  space transform. Not confirmed vs the libcp consumer.
- The two matrices' roles (forward/inverse vs two stages) and `f2.6` vector meaning are unknown.
- Whether the A5 runtime color matrix is actually derived from Block 6 is a LEAD (needs runtime / the
  binary init path) — NOT established.
- 28mm Unit-1 only.
