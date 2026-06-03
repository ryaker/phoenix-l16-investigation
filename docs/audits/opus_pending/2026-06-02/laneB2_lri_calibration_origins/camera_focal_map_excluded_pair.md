<!-- provenance: workflow wf_6de845a7-df9 (l16-b2-lri-w5), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, deterministic LRI byte-parse, single seed 28mm Unit-1 unless noted).
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## Block-6 excluded pair {1,15} + 16-camera focal map
Seed: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (28mm capture, image_focal_length=28). All values deterministically re-extractable via `tools/lri_field_inspect.py` (`scan_lri_blocks`, `list(parse_proto_fields(...))`).

### PREDICTION (stated first) — REFUTED
"1 and 15 are the two reference/anchor cameras, one per outer tier." The bytes refute the reference-camera and symmetric-anchor framing (see below). They ARE in the two outermost tiers, but not as references and not symmetrically (no middle-tier exclusion).

### (1) 16-camera focal-group map — OBSERVED
Block 3, 16x field-13 records. fx read from K-matrix at proto path `field3.field2.field2.field1` (fixed32): field 1=fx, 5=fy, 3=cx, 6=cy (classic K layout; fx==fy in every record).

| id | fx | group | id | fx | group |
|---|---|---|---|---|---|
| 0 | 3375.88 | 28mm | 8 | 8304.20 | 70mm |
| 1 | **3368.87** | **28mm** | 9 | 8297.86 | 70mm |
| 2 | 3371.07 | 28mm | 10 | 18794.65 | 150mm |
| 3 | 3372.44 | 28mm | 11 | 18658.58 | 150mm |
| 4 | 3377.38 | 28mm | 12 | 18730.58 | 150mm |
| 5 | 8283.43 | 70mm | 13 | 18637.72 | 150mm |
| 6 | 8309.02 | 70mm | 14 | 18677.76 | 150mm |
| 7 | 8307.70 | 70mm | 15 | **18655.07** | **150mm** |

Tiers: **28mm = {0,1,2,3,4}**, **70mm = {5,6,7,8,9}**, **150mm = {10,11,12,13,14,15}**. Split = 5+5+6.

### (2) lens_type-per-id HwInfo — NOT PRESENT as a clean 16-entry map (OBSERVED)
- Block 0 LightHeader.field18 `hw_info` holds only **5** `CameraModuleHwInfo` records, ids {0,4,6,8,9}, fields are small varints (field2=2, field3∈{3,4}), not a focal/lens-type-per-id table.
- Block 3.field18 = HwInfo.field5 `pcb_rev` = `"Light Labs"` (not per-camera).
- The only authoritative per-id focal discriminator in this seed is the **Block-3 fx magnitude** above.

### (3) What is special about ids 1 and 15 — OBSERVED
- **Focal group:** id 1 = 28mm (fx 3368.87); id 15 = 150mm (fx 18655.07). The excluded pair = one camera from each **outermost** tier; the middle 70mm tier loses none.
- **Not the reference camera:** Block0.field5 `image_reference_camera = 0` → id 0 is the array master/anchor.
- **Not a distinct sensor type:** Block-3 records for id 1 and id 15 are byte-structurally identical to their tier peers (same 13-byte field-7 trailer `08e10f100b18042011282f3010`; same K-matrix and field-2.6 secondary-focal layout).
- **Only observed distinction:** set-membership — {1,15} are precisely the two ids absent from Block 6's 14-camera (x3-record) list.

### Scope
Single seed (Unit-1, 28mm). Did NOT cross-parse the other three focal seeds or Unit-2 twins; did NOT inspect what Block 6's 3-records-per-camera payload encodes; did NOT trace runtime use of {1,15} in libcp. Reporting parsed LRI bytes only — no PROVEN/confirmed claims.