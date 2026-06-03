# Lane B2 — RUNTIME: Block-8 AWB gains ARE consumed by the pixel path (as reciprocals, coupled into a color matrix)

**Status:** `NEEDS_CODEX_VALIDATION`. Method: **runtime differential rendering** (`lri_process` render of
28mm Unit-1 seed under LLDB; overwrite candidate heap values, re-render, compare DECODED-PIXEL SHA-256).
Promotes Block-8 `B8.19.15` from "looks like WB gains" (LEAD) → **OBSERVED: consumed by the renderer**.

## Prediction tested
Predicted libcp reads the 4 forward gains and multiplies the Bayer channels. **Directionally right
(consumed in the pixel path), mechanically wrong**: it consumes the **reciprocal** form, not the forward
gains, and applies them coupled into a color matrix (not independent per-channel).

## OBSERVED (every claim has a runtime value)
- **File bytes** @ abs offset `0x9b17535`: `0d 26e2db3f | 15 0000803f | 1d 0000803f | 25 105fcb3f` =
  R=1.717839, G1=1.0, G2=1.0, B=1.588839.
- **Heap copies at `CIAPI::Renderer::render` entry** (libcp `0x390180`): forward R-gain `0x3fdbe226` = 3
  copies (2 raw-TLV + 1 `Vec3<f>`); **reciprocal R 1/R=0.5821 (`0x3f150642`) = 9 copies** in distinct
  heap regions (per-tile/per-camera look).
- **Perturbation #1 (forward only):** overwrote all 3 forward R copies 1.7178→8.0. **Decoded-pixel SHA
  IDENTICAL to baseline** (0% pixels changed) ⇒ forward/TLV copies are NOT the pixel-path source.
- **Perturbation #2 (reciprocal):** overwrote all 9 reciprocal-R copies 0.5821→0.125. **Massive
  channel-specific change**: R mean 150.9→249.7 (saturating), G 154.8→0.065, B 147.9→0.075; pixel SHA
  changed ⇒ the reciprocal copies ARE consumed by the demosaic/color stage, and changing only R-reciprocal
  collapsed G/B ⇒ **WB applied INTO a color matrix** (coupled), not independent per-channel multiply.
- **Static signatures (LEAD):** `lt::Internal::DemosaickLightV1<i,j>(Image<vec4x32f>&, const Image<f>&,
  const Vec3<f>&)` (takes a Vec3 gain); `lt::Internal::Pipeline::setWhiteBalance(PipelineBase::AWB)(...)`;
  string `"awb_gains"` @ libcp file-offset `0x5cacaa`.

## Methodological note (important for ALL future runtime probes)
**Read watchpoints are NON-FUNCTIONAL in this Rosetta x86_64 LLDB environment** — proven by positive
control (a forced inferior read of a read-watched address did not trip; `watchpoint resources:` empty).
**Write watchpoints DO work** (control caught the write). ⇒ use **differential rendering / perturbation**
(as here) or single-step tracing to prove consumption; do NOT rely on read watchpoints. Also: hash
**decoded pixels**, not the output file (the file's MD5 changes from an embedded render timestamp +
non-deterministic JPEG entropy-offset — a methodology trap that masquerades as a real change).

## Clean-room relevance
Phoenix parses Block-8 `B8.19.15` per capture and applies WB as **1/gain folded into the demosaic color
matrix** (R,B>1 ⇒ reciprocals<1). LRI-resident input (Rule #0 OK).

## Open / scope
- Exact consuming-instruction VA + the 1/gain producer VA: NOT pinned (read-watchpoint limitation; needs
  single-step or native-arm64 tooling). The DemosaickLightV1/setWhiteBalance signatures are the LEAD site.
- ONE seed (28mm Unit-1), profile 3, `--export-fmt 4` (JPEG-as-.dng). Not retested on other zooms/units or
  the true `Renderer::writeImage` DNG path. The exact color-matrix coupling math not reversed.
