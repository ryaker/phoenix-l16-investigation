# Opus quarantine backlog — WSJF-ordered (per Rich, 2026-06-03)

**Directive:** go slow / steady (Codex back 2026-06-07); docs state *what was found, not that it's
conclusive* (weak language, `NEEDS_CODEX_VALIDATION`); **no canonical/main doc touched**; order all work
(including pivots) by **WSJF = Cost-of-Delay / Job-Size**. One item per tick, top-down.

CoD and Size are 1–10 (Opus estimates, not truth). "Collision" flags overlap with Codex's live
`state_helper_23faf0` thread or its deep C6/iramp lanes — penalize those (re-do risk).

| # | Item | CoD | Size | Collision | WSJF | Notes |
|---|---|---:|---:|---|---:|---|
| 1 | **A7 `weight_vec4` lane semantics** — resolve the source vec4 layout (what `(%rcx,%rdi)`@`0x36a8c0` holds; which lane = color vs weight-accumulator) to finish the soft-blend picture (Blocker 5) | 5 | 3 | none (my A7) | **1.7** | bounded static trace of the `-0x1260` buffer origin; may need 1 runtime read |
| 2 | **Guided detail-transfer `0x36abf0` decode** — the `subps/mulps/maxps/minps` clamped stage after the blend (sharpen / detail-clamp?) | 3 | 2 | none (my A5 tail) | **1.5** | tiny; constants byte-readable; completes the finalization tail |
| 3 | **Runtime confirmation render** — capture non-zero-tile score / q1 / q2 / weight at a real multi-contributor tile; confirm chain continuity 6→7→8→9→10 | 9 | 7 | none (my lanes; renders OK while Codex offline) | **1.3** | biggest credibility lift (LEAD→OBSERVED) but the non-zero-tile probe is the known-hard gap; do carefully across ticks |
| 4 | **Blocker 2 — LRI calibration-origin side** — which LRI calibration-block bytes feed the warp/row/source-record fields, staying on LRI parsing (NOT the `0x23faf0` binary consumer = Codex's live thread) | 7 | 6 | partial (stay LRI-side) | **1.2** | the other major parity wall; the input side is independently parseable (like Lane P) |
| 5 | **A6 q2 wavelet-statistic full assembly** — assemble the 188-op `0x371730`/`0x371a90` CDF 9/7 reduction into q2's exact formula | 5 | 8 | none (my A6) | **0.6** | error-prone; metric already identified; low marginal value |
| 6 | **Post-merge 3×3 color-matrix runtime values** — read M from `__bss` at runtime (lldb) | 4 | 7 | none | **0.6** | needs a render/lldb; values are per-LRI; lower than #3 |
| 7 | **Blocker 4 — C6 remaining** (untested fields/aliases, `+0x60..+0x67` effect, alt route) | 6 | 9 | HIGH (Codex's deep C6 lane) | **0.4** | Codex owns this; high re-do risk; deprioritize |
| 8 | **182 alternate-container format RE** — recover unit assignment for the 182 | 2 | 8 | none | **0.25** | not blocking (integrity settled in Lane P); deep |

## Order of execution (top-down, one per tick, slow)

1 → 2 → 3 → 4 → (5/6 as fillers) → 7/8 only on direction.

## Progress (2026-06-03)

- **#1 DONE** — A7 `lane_semantics.md`: score-weighted mean (denom = Σ raw score); lane-0 identity open.
- **#2 DONE** — A5 `guided_detail_transfer.md`: `out=(B+C)+clamp((A−B)·2·C.lane3, ±0.1)` bounded residual.
- **#4 PARTIAL** — `laneB2_lri_calibration_origins/`: intrinsics in LRI Block 3; cam0 fx/cx/cy + 5+5+6
  focal tiers byte-verified (OBSERVED); distortion/LUT/date CANDIDATE; binary-consumer side left to Codex.
- **#4 extended** — `four_zoom_two_unit.md`: intrinsics block + 5+5+6 tiers confirmed across all 4 zooms
  AND both units (byte-verified); intrinsics are per-body constants; Unit-1≠Unit-2; block index varies.
- **WSJF re-score (2026-06-03):** #3 (runtime render) **downgraded** — Codex's `iramp_36cde0` doc already
  has non-zero score first-hit samples, and full chain-continuity is render-risky/large ⇒ low CoD/Size
  now. Deterministic, collision-free LRI/static items outrank it. Revised order: finish #4 sub-items
  (e.g. re-verify the 28mm K/distortion CANDIDATE labels deterministically; decode the f3.f3 distortion
  model) → #2-class small decodes → #3 only when a focused render window is warranted.
- **#4 sub-item DONE** — `verified_field_map.md`: independently reproduced cam0's nested calibration
  structure (K matrix `[fx 0 cx; 0 fy cy; 0 0 1]` per-scale, 5-coeff distortion, two (x,y) LUT curves,
  calib date) — all OBSERVED-structure; semantic names still CANDIDATE. B2 CANDIDATEs upgraded.
- Next (re-score live): cross-unit K/distortion VALUE diff (Unit-2 twin); unknown `f3.2.4/f3.2.6`
  scalars; Block-6 (42×field-13) identity.

## Notes
- This backlog is Opus planning, not a finding; it cites no claim as fact and touches no canonical doc.
- WSJF re-scored if a new finding changes CoD (e.g. if #1 reveals a hard gate, Blocker-5 CoD drops).
- Renders (#3, #6) only while Codex is confirmed offline, sequential, on the safe 28mm seed first.
