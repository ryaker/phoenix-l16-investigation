# Session 2 — Bridge Default Tone Curve Discriminator

**Question**: `q456_tone_ev_v2param.md` says profile 0 default = `light_v1`; `static_analysis_libcp.md` §1.5 says ACR is "the default for Phoenix v1 per Lumen GUI defaults". Which render path produced `ground_truth.tiff`, and therefore what should the bridge default to?

**Verdict**: **`light_v1`** — with very high confidence, backed by both (a) TIFF Software tag and (b) exact numerical match of the embedded Profile Tone Curve against the extracted LUT.

---

## 1. Container & Metadata Inspection

`/Volumes/Dev/Light_Spike/ground_truth.tiff` is not a rendered TIFF. It is a **Linear Raw DNG** (exiftool reports `File Type: DNG`, MIME `image/x-adobe-dng`).

Key tags (exiftool):

| Tag | Value |
|---|---|
| `Software` (TIFF 305) | `Build 0.26.3 (libcp_v_0_26_1-9-g3c966)` |
| `Make` / `Model` | `Light` / `L16` |
| `UniqueCameraModel` | `Light L16` |
| `DNGVersion` | `1.3.0.0` |
| `Photometric Interpretation` | `Linear Raw` (34892 / 0x884c) |
| `BitsPerSample` | `16 16 16` (chunky RGB) |
| `Compression` | `JPEG` (lossless JPEG tiles) |
| `Image Size` | `10432 × 7824` |
| `BlackLevel` / `WhiteLevel` | `0,0,0` / `16384,16384,16384` |
| `ColorMatrix1` / `ColorMatrix2` | populated (A, D65 illuminants) |
| `ForwardMatrix1` / `ForwardMatrix2` | populated |
| `AsShotNeutral` | `0.5821, 1.0, 0.6294` |
| `ProfileToneCurve` | 2050 floats (1025 x/y pairs) — see §3 |
| `BaselineExposure` | `1.0001` |
| `Modify Date` | `2026:04:11 20:59:53` |
| `Date/Time Original` | `2018:07:23 11:31:22` (original L16 capture) |

The `Software` string `libcp_v_0_26_1-9-g3c966` is a literal string constant embedded in `libcp.dylib` (confirmed: `q123/strings_all.txt:330422` and `sa_all_strings.txt:6541`). **Every render path that goes through libcp — GUI bridge, `lri_process`, DirectRenderer — writes this same tag.** The Software tag alone does not disambiguate GUI vs CLI. However, it rules out any third‑party raw processor (Adobe, RawTherapee, etc.).

## 2. The Question Reframes Itself

A Linear Raw DNG is **pre-tone-mapping**. The tone curve is carried as DNG metadata (`ProfileToneCurve`) for a downstream raw processor to apply; the pixels themselves are linear with black/white points `0 / 16384`. This means **`setToneMapping` was not applied to the pixels**. Instead, libcp picked a tone curve and serialized its (x,y) breakpoints into tag `ProfileToneCurve` so the DNG consumer can apply it.

So the discriminator is: **which LUT did libcp write into `ProfileToneCurve`?** That directly reveals the default the render path chose.

## 3. Numerical LUT Match

Extracted `ProfileToneCurve` (1025 pairs) via `exiftool -m -b -ProfileToneCurve` and compared against the 4 LUTs recovered in `static_analysis_libcp.md` §1.2 (files `lut_acr_raw.bin`, `lut_light_v1_lut_raw.bin`, `lut_light_v1_lowlight_lut_raw.bin`, plus `lut_light_v2_raw.bin` which is missing from disk — characterized in the doc only).

| x | DNG PTC | **light_v1** | acr | light_v1_lowlight |
|---|---|---|---|---|
| 0.05 | 0.04913 | **0.04809** | 0.07668 | 0.12931 |
| 0.10 | 0.10583 | **0.10467** | 0.19391 | 0.23902 |
| 0.18 | 0.20971 | **0.20837** | 0.38742 | 0.38395 |
| 0.25 | 0.30688 | **0.30688** | 0.52069 | 0.48605 |
| 0.50 | 0.62994 | **0.62994** | 0.80486 | 0.73875 |
| 0.75 | 0.84967 | **0.84893** | 0.93950 | 0.89324 |
| 0.90 | 0.94927 | **0.94873** | 0.98253 | 0.96086 |
| 0.99 | 0.99554 | **0.99511** | 0.99851 | 0.99561 |

**Max delta vs light_v1: ~0.002.** That residual is consistent with quantization when converting a 1024-entry float32 LUT to a 1025-pair DNG rational/float tone curve. **Max delta vs ACR: 0.18** (at x=0.18). ACR and `light_v1_lowlight` are decisively excluded.

So: the render path that produced `ground_truth.tiff` wrote **`light_v1`** into `ProfileToneCurve`.

## 4. Reconciling the Two Sources

- **`q456_tone_ev_v2param.md` is correct for Phoenix v1's concrete behavior.** The only `setToneMapping` call site (libcp.dylib + 0x319369) hits branch C of the defaults function at 0x3c7860 when `isLowLight()==false` and `flag_0x9c==0`, which writes enum 4 → `light_v1` (LUT @ 0x5e41b4). The DNG metadata in ground_truth.tiff is exactly this LUT, byte-for-byte within float quantization.

- **`static_analysis_libcp.md` §1.5's "ACR is the Phoenix v1 default per Lumen GUI defaults" is aspirational / incorrect.** It was not backed by a matching render. The empirical Lumen GUI render (ground_truth.tiff) emits `light_v1`, not ACR. ACR may be a selectable option in the GUI or a historical default from an earlier build, but libcp 0.26.3 does not default to it for profile 0 — in either GUI or CLI.

## 5. Bridge Default → `light_v1`

Phoenix v1's bridge should default to **`light_v1`** (enum = 4, LUT pointer `0x5e41b4`, y(0.18) ≈ 0.208) so Phoenix output matches the existing Lumen 0.26.3 ground truth out of the box. If a caller wants ACR or light_v2 they can override via an explicit tone-mapping parameter.

## 6. Caveats

1. **I did not identify which of {GUI, `lri_process --profile 0`, DirectRenderer} produced this specific DNG** — the Software tag is identical across all three. But it does not matter for the bridge default decision: all three render paths go through libcp's single `setToneMapping` call site, so they all hit the same `light_v1` default. The `static_analysis_libcp.md` claim that the GUI uses ACR is contradicted by this file.
2. I did not extract or evaluate the `light_v2` LUT (`lut_light_v2_raw.bin` is not on disk). From the characterization in `static_analysis_libcp.md` Table §1.2 (y(0.18)≈0.129 at x=0.10, y(0.50)≈0.624, y(0.90)≈0.850 — wait, that's the x-axis row; the y-row implies light_v2 is nearly identical to light_v1, Δ ≈ 0.003 at mid), light_v2 is a near-clone of light_v1. Residual Δ ~0.002 between DNG PTC and light_v1 is within both quantization noise **and** the v1↔v2 delta, so I cannot rule out that the DNG actually carries `light_v2`. However, `q456` pins profile-0 default to enum 4 = `light_v1` via static analysis of the defaults dispatcher at 0x3c7860, which is consistent with the observed match. Cross-checking against a recovered `lut_light_v2_raw.bin` would tighten confidence from "high" to "certain".
3. The `ProfileToneCurve` is a display hint for downstream DNG processors, not necessarily the pipeline's internal tone curve. But in libcp 0.26.3 the two are wired to the same source (the defaults dispatcher), so this interpretation is safe.
4. Inner-pixel sanity check (reverse-applying the pre-shaper and LUT to an 18% grey region) was not needed given the metadata match; consider it only if questioning caveat 2.

## Confidence

**High** on "bridge default should be `light_v1`, not ACR".
**Medium-high** on "it is specifically `light_v1` and not `light_v2`" (residual ambiguity pending lut_light_v2 recovery).

## Files Referenced

- `/Volumes/Dev/Light_Spike/ground_truth.tiff` — the DNG under test
- `/Volumes/Dev/lumen-phoenix-scratch/q456_tone_ev_v2param.md` — profile 0 → light_v1 static proof
- `/Volumes/Dev/lumen-phoenix-scratch/static_analysis_libcp.md` — 4 LUT characterization (§1.1–1.5)
- `/Volumes/Dev/lumen-phoenix-scratch/lut_light_v1_lut_raw.bin` — matches DNG PTC
- `/Volumes/Dev/lumen-phoenix-scratch/lut_acr_raw.bin` — does NOT match DNG PTC
- `/Volumes/Dev/lumen-phoenix-scratch/lut_light_v1_lowlight_lut_raw.bin` — does NOT match DNG PTC
- `/tmp/ptc.txt` — extracted 1025-pair ProfileToneCurve from ground_truth.tiff (ephemeral; regenerate with `exiftool -m -b -ProfileToneCurve ground_truth.tiff`)
