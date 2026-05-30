# HYP-UNIT-CAFL — Which physical unit is California (Rich) vs Florida (father)

**Status:** `HYPOTHESIS` (unproven; uncitable as fact per `docs/hypotheses/README.md`)
**Relates to:** `docs/evidence/bundle_proof_two_unit_corpus_static.md` (the two units are PROVEN; only the
owner labeling is unproven).
**Created:** 2026-05-30

## Statement (unproven)

The two PROVEN physical units map to owners as one of:
- Unit-1 `722a6e721636c9c4` ↔ ? (CA / Rich, or FL / father)
- Unit-2 `223961c6bce6153e` ↔ ? (the other)

Per Rich: one camera was his (California, mostly static); one was his father's (Florida, heavy RV travel
with Rich's mother). Which signature is which is not yet established from bytes.

## Why not yet fact

- No lat/lon pairs were decodable in sampled files (GPS off, zeroed, or in an encoding the heuristic
  missed — e.g. int32 micro-degrees or a GPSMetadata sub-layout not reached).
- `body_serial` / `module_serial` are zeroed/redacted (Lane B finding).

## Proof plan

1. Decode the GPSMetadata block (field 19) sub-fields correctly across many files per unit.
2. **Travel-spread discriminator (Rich's human key):** the father's unit (FL, RV) should show a much wider
   geographic spread / more distinct capture locations than Rich's CA-clustered unit. Compute per-unit
   bounding-box / distinct-location count; the higher-spread unit is the father's.
3. Corroborate with capture-date cadence if useful.

## Resolution criteria

- RESOLVED when GPS decodes and one unit shows a wide multi-state spread (→ FL/father) while the other
  clusters in California (→ Rich); PROMOTE to the evidence doc with decoded coordinates.
- If GPS is genuinely absent corpus-wide, owner labels must come from Rich directly; this stays a
  hypothesis (the two-unit fact itself is independent and already proven).
