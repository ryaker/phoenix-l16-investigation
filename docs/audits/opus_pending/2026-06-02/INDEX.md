# Opus Quarantine Campaign — 2026-06-02 — Codex Validation Index

**Branch:** `research/opus-quarantine-2026-06-02` (isolated worktree, cut from committed `dbf9a04`).
**Status of EVERYTHING here:** `NEEDS_CODEX_VALIDATION`. Nothing is truth. Opus has no ledger authority.
**Binary:** `libcp.dylib` sha256 `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
**Not pushed to main. No canonical doc touched. Codex's in-progress main-worktree edits were never touched.**

## Terminology convention (contamination-audit note, 2026-06-02)

In these packets, **"machine-verified" / "byte-verified" / "machine-anchored"** denote charter status
**`OBSERVED`** — a deterministic, reproducible check (byte-read of rodata, `strings` match, branch-target
grep, exact canonical-form match). They are **stronger than `LEAD`/`CANDIDATE`** (which mark LLM-read
interpretation) but they are **NOT** the ledger-grade `VERIFIED`/`PROVEN`/`SPEC_READY` status — only the
ledger confers that, and only after Codex independently re-extracts. So: re-run the `commands.txt` checks;
an `OBSERVED` item should reproduce exactly, but it is not ledger fact until you admit it.
Where a packet says **"PROVEN `CLM-MERGE-002`"** it is *citing the ledger's* status of an existing claim,
not asserting Opus authority. A contamination audit (2026-06-02) found no cross-citation of one Opus
packet as fact, and `NEEDS_CODEX_VALIDATION` on every packet.

## Backlog (WSJF-ordered)

`BACKLOG_WSJF.md` — remaining quarantine investigation items ranked by WSJF (Cost-of-Delay / Job-Size),
per Rich's 2026-06-03 directive. Worked top-down, one per tick, slow. Planning only (no claims).

## Start here for the merge story

`MERGE_PIPELINE.md` — end-to-end IRAMP merge→output dataflow synthesis (entry → coverage gate →
block-match align → SSIM-class score → soft similarity-weighted blend → Hann accumulator → edge-pad →
cubic resample → runtime color matrix), one table with per-stage VAs, confidence, and packet refs.
Navigational only; no new claims. Read it before the per-lane packets below.

## How Codex should consume this

1. Re-run each packet's `commands.txt` / probe from scratch against the real binary+LRIs.
2. Re-extract the disasm/registers independently — do NOT trust Opus's quoted bytes.
3. Only then promote/reject into the ledger. Treat every label below as a lead, not a finding.

## Packets (all `NEEDS_CODEX_VALIDATION`)

| Lane | Topic | Strongest lead (UNVALIDATED) | Commit |
|---|---|---|---|
| A1 | post-node consumers of the `0x23faf0` tree node | node field map `+0x00..+0xa0`; producer sites `0x23c6da`/`0x23cbbc`; CANDIDATE consumer `0x23c917` (cvtps2pd widening of `+0x20..+0x50` into a new `0xa8` record); `+0x54..+0xa0` written but not re-read in `0x23c5f0` | `ddd494c` |
| A2 | reducer/body search | RTTI: `0x2f78e0` normalizer = `ImageDenoiseBilateralGeneric<5,true>` (LEAD: bilateral denoise, not the merge); `0x3ec960` = per-camera `SourceImageCache` lambda (`LensUndistortCRA`, ONE camera+ONE tile); `0x369f80` IMAGE-EFFECTING accumulator. AGAINST a single tidy N→1 reducer on the **direct-call surface** (vtable/std::function indirection uncrossable statically — needs Codex runtime backtrace) | `7eb2a77` |
| C | C6 tele alias/terminal-route | clear `0x3c90a5 = movb $0x0,0x30(%rax)` zeros ONLY `item+0x30`; key at `+0x60` stays `15`, so `+0x30`-blind classifier `0xf6c60` (mask `0xfc00`) still maps key15 → camera-group-type 2, surviving the clear (CANDIDATE survival angle). No `call 0xf2720`-independent pointer-into-image-kernel path found statically | `c93988e` |
| B | Unit-2 four-zoom accumulator coeff tile | OBSERVED: all four Unit-2 twin seeds (28/35/70/150mm) capture a `0x369fa4` coeff tile float32-identical to the Unit-1 Hann-16 reference (maxdiff 0.0). Cross-unit runtime re-capture; sequential renders. NOT a universality claim | `8441753` |
| A3 | src1/src2 per-tile merge nest + inner body (static) | **READ `CORRECTION.md` then `step0_inner_body.md`.** Machine-verified nest in `0x3661b0`: tile-X `0x369140` → tile-Y `0x369160` → contributor loop `0x3692f0..0x369f24` (per-tile **coverage sentinel** `0x36930f cmpl $0x80000000`) → single Hann **overlap-add** `0x369f80` into shared base `-0x1710`. **NEW (deterministic):** inner body `0x369320..0x369ec4` does **per-contributor SAD block-match motion search** (`mpsadbw`×16 + `phminposuw` argmin `0x3694b1..0x369643`) — motion-compensated merge. Accumulate runs once/tile reading scratch `-0x4240` via `0x36e530`. **RESOLVED by reconciliation** (`step0_reconciliation.md`): `0x36cde0(-0x4240,-0x11a0)` returns a per-contributor match SCORE (Codex `bundle_lldb_iramp_36cde0_scalar.md`), so `-0x4240` is a compared patch, not an accumulator. Inner body emits `(flow_x,flow_y,score)` tuple; real pixel reduction is downstream — Codex's committed **reciprocal-weighted add** (`bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`). **Converged:** merge = score-weighted N→1 reduction (motion-aligned + quality-weighted), not naive sum, not hard select. `-0x4240` watchpoint task retracted. | `ecfc8ab`→…→`966ef2d`→(+reconcile) |

| A5 | IRAMP post-merge output finalization | **Deterministic anchors:** edge-extend helper `0x3750a0` identified by embedded asserts `"Amount to extend must be positive"` / `"ROI must be within image!"` / `"ROI start must be non-negative!"`; resample helpers `0x2b2be0`+sibling `0x36f800` = 64-entry cubic-kernel LUT + recursive subdivision driver `0x5440`. Finalization tail `0x369ff2..0x36ae41` = **bounds-clamp → edge-pad → cubic resample to output**, NOT a quality gate. Only rejection = degenerate-rect skip `0x36a0eb/0x36a0ef jle 0x36a15b`. **Negative-shaped result for the acceptance/rejection blocker at THIS site** (no score gate in the finalization). Consistent with PROVEN `CLM-MERGE-002` (resample stage after the accumulator). **BYTE-VERIFIED kernel identity** (`kernel_identity.md`): `0x2b2be0` = cubic B-spline (B=1,C=0), `0x36f800` = Catmull-Rom (B=0,C=0.5), both 4-tap×64-phase, exact canonical match ≤3e-8 — parity-grade (reimplementable from formula). **APPLY (`apply_structure.md`, machine-anchored):** Q16.16 coords (scale `0x5abed8=65536.0`), `phase=(coord_q>>10)&0x3f` (64 phases), `srcIdx=coord_q>>16`, separable 4-tap `mulps`/`addps` (`0x2b3410..0x2b3435`) into dst view; leaf `0x6685b8+0x30=0x2b3180→0x2b31c0`. Complete clean-room resampler spec. | `31ef04e`→(+kernel)→(+apply) |

| P | 182 unassigned LRIs (two-unit completeness) | **Deterministic.** The 182 corpus files unassigned by the two-unit partition yield **NO calibration signature and NO third unit** — even an exhaustive `LELR`-magic-scan re-parse assigns 0/182 with 0 third signatures. Split: 4 zero-block + 178 with 1–4 blocks but no 16×field-13 intrinsics (assigned files have ~12 blocks); mechanism = 90 early-walk-termination + 92 walk-complete; spans 2017–2021 (not early-firmware-only). **The "exactly two units, no third" claim is not threatened**; gap is container-format/parser-coverage. Open: whether they carry calibration under a different proto field (extended-parser assignment) — not a third-unit risk. | `laneP_parser_gap_182/` |

| A6 | per-contributor merge SCORE metric `0x36cde0` | **Extends Codex `bundle_lldb_iramp_36cde0_scalar.md`** (which left the metric un-named). Byte-verified constants identify the score as a **CDF 9/7 wavelet-domain, SSIM-class structural-similarity/quality metric**: SSIM stabilizers `0x5fdc50=(0.01,0.03,..)` (K1/K2) on μ/σ²/σ_AB; **CDF 9/7 lifting** α/β/γ/ζ/(1/ζ) byte-exact at `0x5cbfd0..0x5cc040`; returns `sqrt(q1·q2)`. Names the merge-weight metric → clean-room-reimplementable; candidate input to Blocker-5 acceptance. Closed form / SSIM-variant / δ not pinned (LEAD). | `laneA6_score_metric/` |

| A7 | score consumption → Blocker 5 (accept/reject) | **Extends Codex tuple-consumer docs.** Within span `0x36a7d8..0x36a93c` the per-contributor score is a SOFT normalized blend weight: byte-decoded `weight_vec4 = (score + 2·max(score−0.5, 0), score, score, score)` (offset const `0x5a8120 = −0.5`), `mulps` into source, accumulate, `rcpss`-normalize (`Σw·src/Σw`). **The only float gate on the score is a `maxss` clamp — NO hard score-thresholded accept/reject branch** (all conditional jumps are loop bounds). With A6 (SSIM score) ⇒ ghost/trail suppression is **soft** (low-SSIM contributors down-weighted, >0.5 boosted), not a hard reject. Lane semantics of the vec4 + later post-blend stages open. | `laneA7_score_consumption/` |

| B2 | LRI per-camera calibration origins (Blocker 2, input side) | **OBSERVED (byte-verified):** intrinsics live in LRI **Block 3** (smallest 16×field-13); cam0 `fx=fy=3375.884, cx=2084.516(≈4160/2), cy=1541.342(≈3120/2)`; 16 cams cluster into the L16 **5+5+6** focal tiers (fx ≈3370/8300/18700). Stored as tagged protobuf fixed32. **CANDIDATE** (subagent, not all re-verified): 3×3 K layout, distortion coeffs `[0.0326,0.1501,0,0,-0.5774]`, 101+30 LUT, calib date. LRI-side only (binary consumer = Codex's `0x23faf0` thread, untouched). | `laneB2_lri_calibration_origins/` |

## Cross-cutting note for Codex (anchor spec)

Lanes A1/A2/C reported `anchorPassed=TRUE`; Lane B reported `FALSE` — **not a conflict.** `0x3eced0`
is the enclosing **function prologue**; the `mulps → maxps → sqrtps` triplet is **inside** at
`0x3ecfe4`. The anchor instruction in any future spec should reference `0x3ecfe4` (the triplet), not the
`0x3eced0` entry. All four lanes agree the triplet exists inside that function.

## What is NOT done (honest gaps for Codex / future work)

- No runtime backtrace crossing the vtable/std::function indirection (A2's stated gap).
- C6 group-type-2 forward dataflow to pixels, and per-caller guard domination over all 58 `0xf2720`
  sites, are unproven (Lane C proof plan §2/§3 — runtime).
- Lane B observed only the FIRST accumulator hit per render (zero/early tiles); no non-zero
  multi-camera accumulation captured (the known probe-redesign gap from the prior 28mm decider).
- 182/9390 corpus LRIs remain unassigned to a unit under the current parser — **now characterized in
  Lane P:** deterministically shown to yield no third-unit signature (container-format/parser-coverage
  gap, not a hidden camera). Residual open: extended-parser assignment of those 182.
- **Lane A3 decisive question is untraced:** the per-tile inner body `0x369320..0x369ec4` — SUM vs
  SELECT of coverage-passing contributors. Step 0 of A3's plan (static trace of that range) is the
  cheapest next move; no render needed. The `0x80000000` coverage sentinel is a candidate tile-level
  acceptance mechanism worth cross-referencing with the ledger's open acceptance/rejection item.
</content>
