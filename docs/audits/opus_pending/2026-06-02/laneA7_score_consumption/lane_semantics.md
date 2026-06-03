# Lane A7 addendum — weight_vec4 lane semantics (WSJF #1, partial)

**Status:** `NEEDS_CODEX_VALIDATION`. Resolves the normalization/lane structure of the first weighted-add;
the physical channel identity of lane 0 remains open. Instructions OBSERVED (deterministic). VA == file
offset, `libcp.dylib` sha256 `b38dc4b3…`.

## Buffers (OBSERVED)

First weighted-add loop (`0x36a8b0..0x36a8ec`): source = `-0x1260` (descriptor; base ptr loaded
`0x36a87b movq -0x1260,%rcx`), dest accumulator = `-0x1230` (`0x36a882 movq -0x1230,%rdx`). Both
descriptors are set earlier (`0x36a547 movaps ...,-0x1260`; `0x36a505 ...,-0x1230`). Per pixel:
`xmm1 = src(%rcx,%rdi); mulps weight_vec4; addps dest(%rdx,%rdi); store` (`0x36a8c0..0x36a8cb`).

## Numerator vs denominator (OBSERVED — the key resolution)

- **Numerator** (per contributor, into `-0x1230`): `dest += weight_vec4 · src`, where (from A7)
  `weight_vec4 = (score + 2·max(score−0.5,0), score, score, score)`.
- **Denominator** (running weight sum, `xmm2 = -0x42f0`): accumulated at `0x36a8f0/0x36a8f7/0x36a8fe`
  as `xmm2 += xmm3` with `xmm3 = -0x4300 = score` (the **raw** score, NOT the boosted lane-0 weight).
- **Normalization:** `0x36a934 shufps + 0x36a938 rcpss` → `1/Σ score`, stored `-0x42f0`.

## Resulting per-lane semantics (OBSERVED structure)

- **Lanes 1–3:** `Σ(score · src_lane) / Σ score` — a clean **structural-similarity-weighted mean** of the
  source's channels 1–3.
- **Lane 0:** `Σ((score + 2·max(score−0.5,0)) · src_lane0) / Σ score` — same denominator (Σ raw score)
  but a **super-linearly boosted numerator** for contributors above the 0.5 score (high SSIM-cs);
  i.e. lane 0 over-weights well-matched contributors relative to a plain weighted mean.

This tightens the Blocker-5 picture: the merge is a **score-weighted average** (Σw·src/Σw with w=score),
with lane 0 carrying an extra high-similarity emphasis. Combined with A6 (score zeros below SSIM-cs≈0.8)
the effective behavior is: poorly-matched contributors contribute ~nothing; well-matched ones average,
with lane 0 favoring the best matches.

## Open
- **Physical identity of lane 0** (is it a color channel, luma, or a weight/confidence channel?) is NOT
  resolved — needs the `-0x1260`/`-0x1230` descriptor channel layout (vec4 = RGBA? or RGB+weight?).
  The asymmetric lane-0 boost suggests lane 0 may be special (e.g. a luma or weight channel), but this
  is a LEAD, not proven.
- There are **further accumulation passes** after this one (`0x36aa30` separable-weight pass into
  `-0x1200` with `reciprocal*0.2` in lane 3; `0x36abf0` guided clamp; `0x36acf0` 3×3 matrix). This
  addendum covers only the first weighted-add's lane semantics.
- LLM-read disasm. `NEEDS_CODEX_VALIDATION`.
