# HYP-LANEB — LRI Calibration Field Decode & Hardcode/Compute Map

**Status:** `HYPOTHESIS` (unproven; uncitable as fact per `docs/hypotheses/README.md`)
**Relates to:** Lane B / WSJF #2 (pair-grid producer calibration / LRI origins).
**Created:** 2026-05-30
**Proven companion facts:** `docs/evidence/bundle_proof_lri_calibration_origin_static.md`

## Statements (each unproven; do not cite as fact)

> NOTE: statement (1) below was PROMOTED to fact on 2026-05-30 — parent re-verified
> `1/3`→14, `1/288`→0 with a clean `1.0`→5627 sanity. It now lives in
> `docs/evidence/bundle_proof_lri_calibration_origin_static.md` FACT 4. Kept here struck-through for
> provenance. Remaining statements (2)–(4) are still hypotheses.

1. ~~**libcp `__const` hardcode/compute map.**~~ **PROMOTED — see evidence FACT 4.** coeff `1/3` is a
   universal `__const` (count 14, safe to hardcode); the `1/288` scale is absent (count 0, runtime-
   computed). The cubic exp-approx `0x5dae2c` / bilateral eps `0x5dce90` / 4096 radius-length sub-claims
   were not independently re-run and remain hypotheses until checked the same way.

2. **Per-camera K-matrix decode (cams 1..15).** Only cam0's K block decodes cleanly (principal point
   2048.0; focal-px header template `[818, 1500, 818]`). Cams 1..15 do not decode at the same fixed
   offset — the proto sub-layout shifts. The per-camera-distinct calibration payload lives in intrinsics
   `record.f3.f3` (1682B, proven distinct by 16 hashes), but the field-level K/distortion decode for
   cams 1..15 is unproven.
   - To verify: stricter proto path for `record.f3.f2`/`f3.f3` across all 16 cams.

3. **Row-composition matrix source (links to the 0x25e0c0 producer).** Hypothesis: the `0x25e0c0` row
   producer's 4×4 double matrix chain `source_b_product * inverse(source_a_product)` takes its source
   records from the LRI intrinsics K + distortion. Pure hypothesis — requires a peer runtime lane to
   capture the `state+0x448` node bytes, then a static byte-match against LRI intrinsics floats.

4. **CalibStage banks.** Hypothesis: CalibStage stage 0/1 ("factory"/"current") correspond to the two
   focal entries per camera, or to the wide(15061B)/tele(17762B) distortion record sizes. Unproven.

## Disproof Criteria

- (1) is REFUTED if a clean re-run shows the byte-search is broken (1.0 sanity = 0) or different counts.
- (2)/(3)/(4) are REFUTED if the decoded fields do not match the named producer offsets.

## Retracted (kept as do-not-repeat)

An intermediate Lane B pass mis-claimed per-camera focal "818 wide / 1635 tele" — a record-misindex bug,
retracted by the agent. The true focal-px header is the same template `[818, 1500, 818]` for all 16
cameras; genuine per-camera differences live in `record.f3.f3` (the 16-distinct-hash fact). Do not
revive the "818/1635" split.
