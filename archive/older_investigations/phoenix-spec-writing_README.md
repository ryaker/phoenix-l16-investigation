# Phoenix — Spec Writing Package
**Generated:** 2026-04-13

This folder contains the **minimal set of files needed to write the Phoenix coding specification**. The full implementation package is in the sibling folder `../phoenix-handoff/`.

## What's here

| File | Purpose in the spec |
|---|---|
| `phoenix-pipeline-facts.md` | **THE canonical investigation document.** Start here. Every pipeline stage, every VA, every formula Phoenix needs — verified from real Lumen sources. |
| `lri_header_camera_config.md` | Per-capture camera firing + encoder + zoom parser. Verified on 162 LRIs. Contains a standalone Python decoder the spec can cite for input file parsing. |
| `cal_color_l16_02130.npz` | Per-camera calibration arrays. Use `numpy.load()` to cite exact array shapes and field names in the spec. Contains `bayer_patterns`, `black_levels`, `white_levels`, `vignetting_grids`, `ccm_matrices`, `cra_grids`. |
| `tmo_characterization.json` | Tone curve metadata: 4 curves (`acr`, `light_v1`, `light_v1_lowlight`, `light_v2`), midgray responses, pre-shaper formula. Phoenix default = `light_v1` (verified). |

## How to use this package

1. **Read `phoenix-pipeline-facts.md` top to bottom.** The `⚠ Rev 5 — Verified pipeline model` box at the top is the authoritative per-tile execution sequence Phoenix must implement.
2. **For any section the spec needs to describe empirically**, cite the corresponding file:
   - Input file parsing → `lri_header_camera_config.md`
   - Calibration data shape → `cal_color_l16_02130.npz` (inspect with numpy)
   - Tone curve selection → `tmo_characterization.json` + the LUT VA table in phoenix-pipeline-facts.md
3. **Do not cite session writeups** in the spec. They exist in the full handoff folder for the implementer's traceability; the spec should cite only the canonical doc.

## If you need more detail than phoenix-pipeline-facts.md provides

Go to `../phoenix-handoff/investigation_traceability/` for raw session reports, or `../phoenix-handoff/decoders/` for additional parser utilities. Those are reference-level documents — the spec should not depend on them, but they're available for disambiguation.

## Inspecting the calibration .npz

```python
import numpy as np
data = np.load('cal_color_l16_02130.npz')
print("Arrays:", list(data.keys()))
print("black_levels:", data['black_levels'].shape, data['black_levels'].dtype)
print("white_levels:", data['white_levels'].shape, data['white_levels'].dtype)
print("ccm_matrices:", data['ccm_matrices'].shape)  # (14, 3, 3, 3) = 14 cams × 3 illum × 3x3
print("vignetting_grids:", data['vignetting_grids'].shape)  # (16, 4, 17, 13)
print("cra_grids:", data['cra_grids'].shape)  # (16, 13, 17, 4, 4)
```

## Investigation discipline (carry forward into the spec)

Per Rich's rule: **the spec must describe what Lumen does, not what any Phoenix implementation attempt has done.** If the spec ever contains phrases like "we observed X in the spike" or "the spike produced Y," those are implementation test results, not investigation findings, and they do not belong in the spec.
