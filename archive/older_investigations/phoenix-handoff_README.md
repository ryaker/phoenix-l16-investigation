# Phoenix Handoff — Full Package
**Generated:** 2026-04-13 (Investigation Sessions 1-5 complete)

This folder contains everything needed to **implement** the Phoenix L16 bridge reimplementation. It is the full traceability-preserving set.

> For writing the **coding specification** only (not implementing), use the minimal sibling folder: `../phoenix-spec-writing/`. That folder has just `phoenix-pipeline-facts.md` + calibration schema + input-format decoder + tone curve metadata.

---

## Start here
**`phoenix-pipeline-facts.md`** — the canonical investigation document (rev 6). Every fact has a VA or file citation to real Lumen sources. Any earlier revision is superseded and should not be consulted.

**Read the `⚠ Rev 5 — Verified pipeline model` box at the top first.** It describes the per-tile execution model on production L16 renders. Several earlier claims have been empirically overturned and are flagged as SUPERSEDED with the reason and the correcting source.

---

## Folder layout

```
phoenix-handoff/
├── README.md                          # this file
├── phoenix-pipeline-facts.md          # Tier 1 — canonical, start here
│
├── calibration/
│   └── cal_color_l16_02130.npz        # Per-camera calibration arrays
│                                      #   bayer_patterns (16,), dtype int
│                                      #   black_levels (16,), dtype float
│                                      #   white_levels (16,), dtype float
│                                      #   vignetting_grids (16, 4, 17, 13) float32
│                                      #   ccm_matrices (14, 3, 3, 3) float32
│                                      #     — 14 cams × 3 illuminants × 3x3
│                                      #   cra_grids (16, 13, 17, 4, 4) float32
│
├── tone_curves/
│   ├── tmo_acr.npy                    # 1024 float32
│   ├── tmo_light_v1.npy               # 1024 float32  ← Phoenix default
│   ├── tmo_light_v1_lowlight.npy      # 1024 float32
│   ├── tmo_light_v2.npy               # 1024 float32
│   ├── lut_acr_raw.bin                # raw 4096 bytes (1024 × float32)
│   ├── lut_light_v1_lut_raw.bin       # raw bytes
│   ├── lut_light_v1_lowlight_lut_raw.bin
│   ├── lut_light_v2_lut_raw.bin
│   └── tmo_characterization.json      # curve metadata (midgray responses, pre-shaper formula)
│
├── reference/
│   ├── ground_truth.tiff              # ⚠ Actually a Linear Raw DNG 1.3.0.0 with
│   │                                  #   ProfileToneCurve metadata (1025 x/y pairs).
│   │                                  #   Used to validate Phoenix output.
│   └── depth_map.npy                  # Reference depth map for validation
│
├── decoders/
│   ├── lri_header_camera_config.md    # Per-capture camera firing + encoder + zoom parser
│   │                                  #   Verified on 162 LRIs. Contains standalone Python decoder.
│   ├── block8_awb_parse.py            # Block 8 f19.f15 AWB gain vector decoder
│   ├── lri_protobuf_walker.py         # Generic LRI protobuf field scanner
│   └── lris_depth_decode_notes.txt    # .lris Section 3 depth map decoding
│                                      #   Magic 0x51E8E000; depth_mm = 3460 + (116930-3460)*arr/16383
│
└── investigation_traceability/         # Tier 3 — raw evidence for specific claims
    ├── session2_*.md                  # Session 2: first LLDB runtime probe + corpus scans
    ├── session3_*.md                  # Session 3: upstream warp, V1 demosaic, merge chain
    ├── session4_*.md                  # Session 4: V1 body, V1/V2 selector, AWB slot 4, Phase B
    ├── session5_*.md                  # Session 5: lambda_0 Halide JIT limit, CCT derivation
    ├── cct_and_awb_auto.md            # Robertson CCT + no-AUTO-estimator finding
    ├── demosaic_v2_and_fusion_weights.md
    ├── q456_tone_ev_v2param.md        # Tone curve default = light_v1 resolution
    ├── wdr_format.md                  # WDR is not a real format
    ├── lens_shading_activation.md     # setLensShading is gated on LRIS VignettingCharacterization
    ├── zoom_config_table.txt          # Movable camera set {B1,B2,B3,B5,C1,C2,C3,C4}
    ├── fusion_blend_analysis.txt      # Proof that FusionCacheBayer is NOT cross-camera merge
    └── lri_header_camera_config.md    # (duplicate in decoders/)
```

---

## Critical caveats for the implementer

1. **`ground_truth.tiff` is a Linear Raw DNG**, not a rendered TIFF. It carries the target tone curve in `ProfileToneCurve` metadata. Extract with ExifTool or `PIL.Image.tag_v2`. To validate Phoenix output, apply the `light_v1` LUT to Phoenix's linear output and compare against `ground_truth.tiff`'s linear raw values (with ProfileToneCurve pre-applied).

2. **"WDR" is not a capture format.** It is a catalog misnomer; the files are 70mm/150mm 11-camera full-sensor captures. Classify LRIs by `(chunk_count, cam_split, per_cam_stride)` from LightHeader, not by `chunk0_len`.

3. **FusionCacheBayer is not cross-camera fusion.** It is an HDR bracket merger running inside the `tone_adjust.*` subsystem. The actual 10-camera merge is a side effect of `DemosaickLightV1::operator()` writing into a shared canvas (one invocation per camera per tile).

4. **lambda_0 `LinearizeAndColorScale` is Halide-JIT compiled.** The per-pixel `(raw - black) * scale` math cannot be statically extracted from the AOT binary — it's generated at runtime. Phoenix implements the semantic equivalent using `black_levels` and `white_levels` arrays from `calibration/cal_color_l16_02130.npz`.

5. **AWB application is `output = input × (1/stored_gain)`** where `1/stored_gain` is pre-computed at pipeline setup from Block 8 f19.f15. Verified to 5 decimal places against runtime context dumps.

6. **Tone curve default is `light_v1`**, not `light_v2` (the "v2" name collision with DemosaickLightV2 is coincidental). Verified via ground_truth.tiff `ProfileToneCurve` LUT match.

7. **DemosaickLightV1 fires on production L16 LRIs**, not V2. V2 is dormant in the libcp 0.26.3 build. Phoenix should implement V1's algorithm (Hamilton-Adams family green interpolation with Vec3 gain-derived adaptive noise floor).

8. **CCM uses two factory illuminants (A + D65)** with CCT-driven blending via Robertson forward lookup at VA 0x66d420. Default CCT is ~4300 K when the LRI doesn't carry an explicit `neutral_temp` field. Phoenix MVP can hardcode scene chromaticity `(0.36895, 0.21384)` for <1 ΔE error on neutral scenes.

9. **Phase B is the L16 grayscale output pipeline** and is architecturally separate from the color path. Phoenix skips it.

10. **Movable camera set is `{B1, B2, B3, B5, C1, C2, C3, C4}`.** Fixed: `{A1, A2, A3, A4, A5, B4, C5, C6}`. Verified on two independent data sources (78-float mirror_raw leaf + warp block encoder tables).

---

## Investigation discipline (Rich's rule)

> "Nothing from your spike should be in any of the documentation. The investigation should have all been just about Lumen and the LRI files and the actual camera stuff."

This package contains **zero spike outputs, zero MAD values, zero coverage percentages**. Every claim is derived from real Lumen sources (libcp.dylib RTTI/disassembly/LLDB, real LRI file parsing, calibration extraction). If Phoenix's output ever contradicts `ground_truth.tiff`, the conclusion is "the Phoenix implementation is wrong," NOT "the investigation was wrong."
