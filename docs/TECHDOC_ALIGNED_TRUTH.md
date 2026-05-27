# L16 Phoenix — Tech-Doc-Aligned Truth

**Date:** 2026-04-22
**Purpose:** narrow adjudication layer over repo + scratch findings. This file is not a replacement for `docs/TRUTH.md`; it is a stricter subset meant to preserve only the claims that survive Light's own public technology article plus later LLDB/disassembly/archive evidence.

## Rule Set Used For This Audit

For **this document**, `/Users/ryaker/Documents/Light_Work/l16-tech-part-1-3.md` is treated as the **architectural guardrail**.

That means:

1. **Any repo or scratch claim that contradicts the Light tech article is rejected here.**
2. **Any additional implementation detail is included only if it is backed by later LLDB/disasm/archive evidence and does not contradict the article.**
3. **Any "0 hits", "GUI-only", or "never fires" claim is excluded unless it is either**
   - proven by static binary content, or
   - explicitly kept scope-bound to the tested LRI/focal/profile.
4. **Deprecated/archive docs are not authoritative.** They remain useful only as negative evidence, contradiction tracking, or history.

## Audited Inputs

Primary guardrail:

- `/Users/ryaker/Documents/Light_Work/l16-tech-part-1-3.md`

Canonical truth and historical audit inputs:

- `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/TRUTH.md`
- `/Users/ryaker/.claude/projects/-Users-ryaker-Dev-L16-Lumen-ReverseEngineering/memory/open_items_plan.md`

The original 2026-04-22 pass reviewed the then-current `docs/TRUTH.md`
v2.1.6 and listed `/tmp/l16_open_audit/_FINDINGS.md` as an audit input. That
path is transient and was not present under `/tmp` or `/private/tmp` when
checked on 2026-05-13. Future use of this document must therefore treat that
path as an unavailable historical reference and defer to the current
`docs/canonical/CLAIM_LEDGER.md` plus repo-local evidence docs.

Key repo/scratch evidence used to arbitrate contradictions:

- `/Volumes/Dev/lumen-phoenix-scratch/lightheader_camera_scan.md`
- `/Volumes/Dev/lumen-phoenix-scratch/35mm_crop_math.md`
- `/Volumes/Dev/lumen-phoenix-scratch/image_resolution_amp_verification.md`
- `/Volumes/Dev/lumen-phoenix-scratch/iramp_camera_identity.md`
- `/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md`
- `/Volumes/Dev/lumen-phoenix-scratch/depth_unlock_verification.md`
- `/Volumes/Dev/lumen-phoenix-scratch/depth_pipeline_chars_70mm.md`
- `/Volumes/Dev/lumen-phoenix-scratch/lumen_app_vs_bridge_delta.md`
- `/Volumes/Dev/lumen-phoenix-scratch/cleanup_actions_log_round4_precision.md`
- `/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md`
- `/Volumes/Dev/lumen-phoenix-scratch/critique_audit.md`

## Consolidated Truth

### 1. Public Architecture Truths That Must Be Preserved

- The L16 is a **16-module** camera built around **28mm, 70mm, and 150mm** equivalent focal classes. The public article explicitly says the 70mm and 150mm modules use mirrors, and that only those three focal classes exist as hardware classes.
- Live preview is generated from **one reference module**, not from the full fused stack.
- A capture uses **at least 10 simultaneously captured images**, and the set of modules used depends on zoom.
- At **28mm**, the public Light description is explicit: the camera uses **all five 28mm modules and all five 70mm modules**; the software computes a **depth map from the five 28mm views** and uses that depth to position and fuse the 70mm views.
- Light's public framing is therefore: **multi-camera capture, depth-guided fusion, single reference module for preview, and zoom-dependent module selection**. Any internal story that says the bridge path is "single-camera only", "no depth", or "not really multi-camera fusion" is wrong.

### 2. Zoom/Firing Truths Consistent With The Public Article

- The archive-wide firing scan is stable enough to treat as real architecture:
  - **28mm** dominant fired set: `5A + 5B`
  - **35mm** dominant fired set: `5A + 5B`
  - **70mm** dominant fired set: `5B + 6C`
  - **150mm** dominant fired set: `5B + 6C`
- This means the user-facing zoom behavior is best understood as **two internal tiers**, not four independent hardware tiers:
  - **Wide tier**: 28mm + 35mm
  - **Tele tier**: 70mm + 150mm
- **35mm is a centered crop of the wide tier**, not a separate hardware capture mode. This is consistent with the public article, which names only 28/70/150 as hardware focal classes.
- **150mm is a crop of the tele tier**. It still belongs to the B+C tele capture family.
- **C6 is physically active on tele captures** and appears in the file/capture layer; its later exclusion from some calibrated paths is an implementation filter, not proof that it is absent from capture hardware.

### 3. Fusion Truths

- The bridge-path cross-camera merge is **not** `FusionCacheBayer`, and it is **not** the `0x36fd30` kernel.
- The verified bridge-path cross-camera reducer is **`lt::ImageResolutionAmp` (IRAMP)** at `libcp+0x365960` with its Halide body at `0x3661b0..0x36ae41`.
- The strongest verified merge signature is the **N→1 accumulator** inside IRAMP's body. That is the right family of operation for the Light public story of depth-guided multi-image fusion.
- `0x36fd30` is an **alignment/luma-grid helper** that writes **uint8** output using **Rec.601 luma weights**. It is not the 10-camera fusion kernel.
- `FusionCacheBayer` may still be a real operator on some paths, but on the tested bridge HDR path it is **N=1**, so it cannot be the cross-camera merge described by Light.
- The internal role split is consistent across tiers:
  - **Wide tier**: A-group plays the reference/anchor role; B-group plays the contributor role
  - **Tele tier**: B-group plays the reference/anchor role; C-group plays the contributor role
- Exact internal wrapper semantics for `src1`/`src2` remain narrower than the older scratch stories suggested. The safe truth is the **role split**, not the older "composite-anchor kernel" narrative.

### 4. Depth Truths

- The Light article says depth is part of the real L16 capture-and-fuse pipeline. Later LLDB work is consistent with that and overturns the older "bridge has no depth" story.
- On the tested bridge HDR path, **depth-related internal work does fire**:
  - `StereoAsyncAPI`
  - `DepthCache` construction path
  - `Triangulator::refine3dPoints`
- Therefore these older universal claims are wrong:
  - "Bridge HDR profile=3 does not produce depth"
  - "DepthCache is GUI-only"
  - "Depth pipeline is absent from bridge"
- The safe formulation is:
  - **Depth is real and active on the bridge profile-3 path**
  - **The bridge tool is still only a subset of Lumen.app's total invocation surface**
  - **GUI-only editing APIs are separate from the existence of depth computation**
- At **28mm**, the verified behavior is fully consistent with the public story: wide cameras support depth, and tele/wider-group fusion uses that geometry.
- At **70mm/150mm**, depth is also active, but the exact internal stereo pair-construction remains less fully decoded than the high-level fact that the tele depth path exists.

### 5. Per-Camera ISP Truths

- Fired cameras go through a real **per-camera ISP** before the cross-camera merge. This is fully consistent with the Light article's "take many images, then fuse them" model.
- On the tested bridge HDR path, the active demosaic is **`DemosaickLightV1`**, not V2.
- **AWB gains are stored in the LRI** and are applied as **reciprocals** during pipeline setup.
- **CCM data comes from calibration Block 6 `color_matrix`**, not from the previously misidentified field.
- CCM application is **chromaticity-space based**, and interpolation is **mired-space based**.
- **Per-camera Bayer phase is not uniform across all cameras.** Older "BGGR for all cameras" claims are wrong.
- The safest bridge-parity statement is:
  - **Per-camera ISP is real**
  - **Calibration is per-LRI and must be parsed from the file**
  - **You cannot collapse the system to one hardcoded Bayer layout, one hardcoded CCM, or a no-depth/no-calibration merge**

### 6. Bridge vs Lumen Truth

- `lri_process` is a **bridge/test harness**, not the whole Lumen.app.
- It is still a valid source for **bridge color-path truth**, but not every negative result on bridge can be promoted into a global statement about the app.
- The rule that survives the audit is:
  - **Use bridge LLDB results as scope-bound runtime evidence**
  - **Do not use bridge-only 0-hit claims as universal architecture claims**

## Claims Rejected As Wrong

| Rejected claim | Why it is wrong now |
|---|---|
| `FusionCacheBayer` is the 10-camera merge | Tested bridge HDR runs show `FusionCacheBayer` as `N=1`; later audits move the cross-camera reducer to IRAMP/ImageResolutionAmp. |
| `0x36fd30` is the cross-camera fusion kernel | The kernel writes uint8 luma-grid output with Rec.601 weights and alignment semantics; it is not a float multi-camera reducer. |
| Bridge HDR profile=3 does not produce depth | Contradicted by the Light article's architecture and by later LLDB verification of active depth-path internals on bridge. |
| `DepthCache` / depth pipeline is GUI-only | Same problem: earlier 0-hit interpretations were over-generalized and later corrected/scope-banded. |
| 35mm = `5B + computational synthesis` | Contradicted by the 9390-LRI firing scan and the 35mm crop analysis; 35mm belongs to the wide `5A + 5B` tier. |
| 150mm = `C-only` | Contradicted by the archive-wide firing scan; the dominant tele set is `5B + 6C`. |
| `DemosaickLightV2` is the bridge target | Contradicted by bridge LLDB evidence; V1 is the active tested bridge demosaic. |
| BGGR for all cameras | Contradicted by per-camera Bayer-phase decoding. |
| `libcp+0x2b3410` is the composite-anchor blender | Later runtime analysis reclassified it as a cubic B-spline resampler in `color_denoise_multiplier`, not the anchor combiner story earlier docs claimed. |

## Things Intentionally Excluded From Truth

These may still be real research topics, but they are **not** included here because they are unresolved, scope-bound, or too contradiction-prone:

- The exact internal composition semantics of `src1` and `src2`
- The exact point at which every "dropped" camera becomes visible downstream
- Exact tele stereo pair-construction inside `StereoAsyncAPI`
- Dark-current / non-HDR formulas outside the tested bridge HDR path
- GUI-only editing stages unless directly tied to a verified runtime path
- Any absolute "never fires", "always uses", or "GUI-only" statement derived only from one or two bridge runs

## Bottom Line

The safest consolidated picture is:

- **Light's public architecture is fundamentally right**: the L16 is a multi-camera, depth-guided fusion system using at least 10 simultaneous captures per shot.
- **The repo/scratch work that survives audit supports that picture**, especially after the later corrections that moved the real merge to IRAMP and restored depth to the bridge profile-3 story.
- The main dead ends were:
  - over-trusting zero-hit bridge probes,
  - misidentifying `FusionCacheBayer` and `0x36fd30`,
  - carrying stale 35mm/150mm zoom stories forward after better evidence existed.

If a future claim conflicts with this file, `l16-tech-part-1-3.md`, and the later IRAMP/depth/archive evidence at the same time, that future claim should be presumed wrong until re-proved.
