# Lumen Parity Spec

This is the clean-room implementation spec for a modern Lumen replacement.

## Admission Rule

This spec may cite only:

- claim IDs from `docs/canonical/CLAIM_LEDGER.md`
- evidence files listed in those claim rows

It may not cite scratch docs directly unless the claim has already been admitted into the ledger.

## Status

This spec is a scaffold. It is not yet complete enough to implement end-to-end parity without reading the blocker list.

Before writing implementation text into any section below, confirm:

- the claim is `SPEC_READY`
- zoom scope is explicit
- any remaining open items are named

## Required Output Quality

The parity renderer must validate on:

- `28mm`
- `35mm`
- `70mm`
- `150mm`

The required visual quality bar is:

- no obvious ghosting
- no visible trailers
- no persistent edge doubling
- correct framing and crop behavior per zoom tier

## Spec Sections

### 1. Input Formats

- LRI parsing
- LRIS sidecar handling
- required metadata fields

### 2. Camera Participation

- fired-camera sets by zoom
- anchor vs contributor routing
- per-zoom exceptions

### 3. Calibration Inputs

- geometric calibration
- CCM / AWB inputs
- any merge-critical calibration terms

### 4. Per-Camera ISP

- unpack
- Bayer corrections
- demosaic
- white balance
- CCM
- any pre-merge transforms required for parity

### 5. Warp Coordinate Generation

- dst-coordinate grid generation
- coordinate basis
- warpfield application inputs

### 6. Merge / Accumulation

- IRAMP accumulator math
- contributor iteration
- any anchor pre-fusion interaction that is fully proven

### 7. Post-Merge Stages

- post-merge shaping
- framing / crop / output sizing
- output conversions

### 8. Validation

- canonical per-zoom LRI set
- output comparisons
- merge-quality checks

## Do Not Freeze Yet

The following areas are still blocked and must not be written as closed algorithm text yet:

- exact `src1` / `src2` pre-fusion reducer
- remaining producer-side row/map calibration semantics over the ROI-derived dst-coordinate lattice
- exact tele odd-camera routing
- any merge acceptance / rejection logic not yet proven
