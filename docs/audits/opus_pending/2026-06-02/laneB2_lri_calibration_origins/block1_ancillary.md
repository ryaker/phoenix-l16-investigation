<!-- provenance: workflow wf_4ebb1a19-717 (l16-lri-block4-w9), 2026-06-03; finder + (verifier where it ran); verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed).
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## Block 1 decode — L16_02130 (2018-07-23, 28mm canonical)

**LRI:** `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`
**Block:** idx=1, block_offset=81143279, total_size=2577, msg_offset=32, msg_len=25, msg_type=1
**Proto payload (25B) @ file offset 81143311:** `55e874c43f58cbf6fd068001009501e874c43f9801cbf6fd06`

### (1) Full field enumeration (OBSERVED values; CANDIDATE names)
| field | wire | raw | value | CANDIDATE name |
|---|---|---|---|---|
| f10 | fixed32 | 0x3fc474e8 / 1069839592 | float **1.5348176956** | `gain_or_iso_mult` (record A) |
| f11 | varint | — | **14646091** | `exposure_us` (record A) |
| f16 | varint | — | **0** | `status_flag` |
| f18 | fixed32 | 0x3fc474e8 / 1069839592 | float **1.5348176956** (== f10) | `gain_or_iso_mult` (record B) |
| f19 | varint | — | **14646091** (== f11) | `exposure_us` (record B) |

Consumes 25/25 bytes exactly. f10==f18 and f11==f19 are bit-identical → two identical paired sub-records (target-vs-actual or two-frame bracket — CANDIDATE).

### (2) What is 1.5348?
- **NOT a constant / NOT refractive:** cross-capture it varies — 70mm/35mm/150mm ≈ 1.0000, 28mm-day = 1.5348, 28mm-night(Unit-2) = **32.0**.
- **NOT focus/AF** (refutes the inventory "AF/lens ancillary" LEAD by value behavior): the paired varint f11 read as **microseconds** gives sane exposure times — night=42000us (long, low-light), day-wide=14646us, 70mm=1769us, 150mm=511us — and f10 spikes to 32.0 exactly on the low-light night capture, behaving like a **gain/ISO multiplier**.
- **CANDIDATE:** Block 1 = a per-capture **auto-exposure / gain+shutter pair** record (two identical entries), status flag f16.

### (3) Per-capture metadata the renderer needs?
Plausibly yes as exposure/gain state, but unconfirmed at the renderer. The "focus/AF" framing is NOT supported by the parsed values. Names remain CANDIDATE; libcp/RTTI confirmation of the proto class and field semantics was NOT done.

### Factorization / grid test
NOT a 2D grid. Payload is a 25-byte protobuf of 5 scalar fields — does not factor as W*H or N*k float array. Prediction "not a grid" CONFIRMED.

### Open
- High-entropy **2520-byte trailing region** (file 81143336..81145856) after the declared 25-byte proto — purpose unidentified (LEAD).
- Note: "exact" captures (L16_00010/00005) carry a *different richer* msg_type=1 schema at a different block idx (f10,f11,f14,f15,f16,f17 with f17≈374/220) — separate from this Block-1 schema; not the THREAD target.