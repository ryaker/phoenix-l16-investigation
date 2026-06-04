<!-- provenance: orchestrator binary symbol/string sweep of libcp.dylib, 2026-06-03; prompted by Rich's "what is TOTALLY unknown / no candidate" question -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine). These are **newly-surfaced pipeline stages that the entire
investigation has NEVER covered** — not "located but undecoded," but "present in the binary and never looked
at." Found by symbol/string sweep; NOT yet decoded or runtime-confirmed. Binary `libcp.dylib`.

> **FOLLOW-UP 2026-06-03 (same day): these blind spots are now PARTIALLY MAPPED.** See
> `denoise_sharpen_tone_stages_mapped.md` — ColorNoiseReduction fully mapped (covariance multi-scale chroma-NR,
> body `0x34b3f0`, registers before CCM), bilateral mapped (`0x2f6420`, W∈{3,5,7,9}), sharpen structural
> (SharpenLineFactory + Laplacian-pyramid clarity). KEY: all config/tuning-profile driven, NOT LRI (item-#27
> class). And `depth_stereo_no_lri_origin.md` — the depth/stereo subsystem is runtime-stereo-matched (no LRI
> origin); its cost math remains undecoded.

# BLIND SPOTS — whole pipeline stages missing from the current map

Context: asked "what is TRULY unknown (no candidate to evaluate)?", a sweep for denoise/sharpen/tone stages
returned rich symbol evidence for stages that appear in **zero canonical ledger claims**. The synthesized
pipeline (undistort → calib → merge → resample → color → assembly) is therefore INCOMPLETE — it omits at
least denoise, sharpen, and a real tone-adjust stage.

## 1. DENOISE — present, zero ledger coverage (OBSERVED via symbols/strings)
- `lt::Internal::ImageDenoiseNLM(Image<vec4x32f>&, ...)` — non-local-means denoiser.
- `lt::Internal::ImageDenoisePatchNLM<4>(...)` — patch-based NLM (templated patch size 4).
- `lt::Internal::(anon)::ImageDenoiseBilateralGeneric<W, B>` — bilateral denoiser, **window sizes W ∈ {3,5,7,9}**,
  two boolean variants each (8 instantiations).
- `lt::(anon)::ImageDenoise` ($_0, $_1) — planar `Image<f>` denoise overloads.
- `lt::Internal::ColorNoiseReduction(Image<vec4x32f>&, ..., Vec3<f>&, **SensorGainVars**, i,i,f,f)` — chroma
  noise reduction with a **signal/ISO-dependent noise model** (`SensorGainVars`).
- Pipeline integration: **`lt::Internal::Pipeline::setColorNoiseReduction(PipelineBase::ColorNoiseReduction)`**
  `$_77` — Bayer + Color payload variants (mirrors the `setColorCorrection $_58` path we mapped).
- Config keys (string table): `bilateral_denoiser`, `bilateral_denoiser.chroma_boost`,
  `bilateral_denoiser.window_size`, `bilateral_420`, `color_noise_reduction`, `color_noise_reduction.type`,
  `color_noise_reduction.color_denoise_multiplier`, `nlm_denoiser`, `nlm_denoiser.chroma_boost`.
- Also: string `"Median filter of the requested win_size is not implemented"` ⇒ a median-filter path exists.

## 2. SHARPEN + TONE-ADJUST — present, zero ledger coverage (OBSERVED via symbols/strings)
- `lt::Internal::SharpenLineFactory<f>` (+ shared_ptr/default_delete management) — a sharpening stage.
- Config keys under **`tone_mapping.*` / `tone_adjust.*`**: `sharpening`, `sharpening_scale`,
  `tone_mapping.sharpening`, `tone_mapping.sharpening_scale`, `tone_adjust.fusion_sharpening`,
  `tone_adjust.lpyr_clarity`, `fusion_sharpening`, `lpyr_clarity`, `clarity`. ⇒ a real **tone-adjust /
  tone-mapping** stage with sharpening + local-contrast (clarity) sub-parameters — also thin/absent in the
  current canonical map.

## 3. BILATERAL UPSAMPLE — likely the depth guided-upsampler (LEAD)
- `lt::BilateralUpsample<f,h>` and `lt::BilateralUpsampleFromCollapse<2,f,vec4x8ui>` — joint/guided bilateral
  upsampling. Strong LEAD that this is the `0x29ed90` "guided 2× upsample" behind the `depth_*.dp` map
  (ties to the depth/stereo subsystem).

## Why this matters (clean-room parity)
A clean-room renderer that omits denoise + sharpen + tone-adjust will NOT match libcp output regardless of how
perfect the merge/color stages are. These are first-class pipeline stages with their own LRI/config-driven
parameters. They were never in the investigation scope.

## What is now needed (all OPEN — no decode yet)
- Which denoise path(s) fire in bridge HDR (NLM vs bilateral vs color-noise-reduction), in what order, and
  where in the pipeline (pre- vs post-merge / per-camera vs on the merged image).
- The `setColorNoiseReduction` apply chain + the `ColorNoiseReduction`/`SensorGainVars` parameter source
  (LRI? sensor metadata? config default?) — mirror the CCM `setColorCorrection → 0xa9f20 → 0xbfa20` method.
- The sharpen/tone-adjust apply site + ordering + parameter source.
- Whether `BilateralUpsample` is the depth upsampler.
- Decode of the actual denoise/sharpen math (NLM weights, bilateral sigmas, sharpen kernel).

## Honest framing correction (Rich, 2026-06-03)
"Located but can't yet fully decode" was conflating three states: (a) full mechanism decoded awaiting
validation = a real upgrade candidate; (b) a VA + role label, no math; (c) a bare VA. Only (a) is a candidate.
(b)/(c) are still UNKNOWN. These denoise/sharpen/tone stages are worse than (c): they were **not even
located** before this sweep — genuine blind spots, now promoted to known-but-uninvestigated.
