Sample Extracts — REFERENCE ONLY

This folder contains example outputs of Phoenix's calibration parser for ONE specific LRI file (L16_02130.lri). It is NOT a runtime input to Phoenix.

Phoenix MUST parse calibration blocks (3/4/5/6) from each input LRI at render time. The .npz here exists so implementers can cross-check their parser output against known-good extracted values for one sample LRI.

Why NOT a runtime source:
1. Calibration is per-device — each L16 camera unit has its own factory calibration
2. Calibration travels inside every LRI file — it's self-contained
3. Phoenix must work on ANY LRI from ANY L16 unit without pre-extraction

What Phoenix's parser must produce for each LRI, matching the shapes in cal_color_l16_02130.npz:
- bayer_patterns: (16,) int — one per camera, value 3 = BGGR on L16
- black_levels: (16,) float — per-camera black level (e.g. 42.0)
- white_levels: (16,) float — per-camera white level (e.g. 1023.0)
- vignetting_grids: (16, 4, 17, 13) float32 — 16 cams × 4 channels × 17 rows × 13 cols
- ccm_matrices: (14, 3, 3, 3) float32 — 14 cams × 3 illuminants × 3x3 matrix
- cra_grids: (16, 13, 17, 4, 4) float32 — 16 cams × 13 rows × 17 cols × 4x4 mixing matrix

Protobuf paths partially documented in phoenix-pipeline-facts.md "Calibration Fields" section:
- Vignetting: rec.f4.f2[ch].f2.f3 (221 float32 → (17,13))
- CRA: rec.f4.f1.f4 (3,536 float32 → (13,17,4,4))
- CCM: factory block, 42 records per illuminant-camera pair, 3x3 float32 each
- Black/White levels: paths NOT explicitly documented — see open item #26 in phoenix-pipeline-facts.md

Usage:
  import numpy as np
  data = np.load('cal_color_l16_02130.npz')
  print(list(data.keys()))  # arrays listed above
  print(data['black_levels'])  # -> reference values for L16 serial 02130
