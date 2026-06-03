# Lane B — Unit-2 four-zoom IRAMP accumulator coefficient cross-unit re-check

**status: NEEDS_CODEX_VALIDATION**
**lane:** B
**created:** 2026-06-02
**authority:** NONE. This is a quarantine research packet. Weak language only.

## Question

At the IRAMP accumulator instruction `libcp_base+0x369fa4`
(`addps (%rdx,%rcx,4),%xmm1`), the 16 stack-local coefficient floats at
`$rbp-0xa0` were captured on Unit-1 / 28mm last session and matched a Hann-16
window. This packet asks: for each of the four **Unit-2** twin seeds, does the
runtime accumulator coefficient tile at the FIRST `0x369fa4` hit match the
Unit-1 Hann-16 table, to float precision?

This is a cross-UNIT runtime check. Unit-1 and Unit-2 results are kept strictly
separate. See `non_claims.md` for what this does NOT claim.

## OBSERVED result (weak language)

| Zoom  | Unit-2 LRI | first-hit captured | OBSERVED vs Unit-1 Hann-16 |
|-------|-----------|--------------------|----------------------------|
| 28mm  | 2018-07-04/L16_02130 | yes (state 5) | match to 6 dp (maxdiff 0.0) |
| 35mm  | 2018-10-28/L16_03041 | yes (state 5) | match to 6 dp (maxdiff 0.0) |
| 70mm  | 2020-07-14/L16_03434 | yes (state 5) | match to 6 dp (maxdiff 0.0) |
| 150mm | 2018-07-07/L16_02285 | yes (state 5) | match to 6 dp (maxdiff 0.0) |

CANDIDATE / LEAD: on this libcp.dylib (sha256 b38dc4b3...), all four Unit-2
zooms appear to USE the same Hann-16 accumulator tile at `0x369fa4` as the
Unit-1/28mm reference. NEEDS_CODEX_VALIDATION.

## anchorPassed = FALSE (reported honestly, scope-bound)

The spawn-prompt anchor expectation was: disassemble `libcp_base+0x3eced0`,
confirm `mulps -> maxps -> sqrtps`. On THIS libcp.dylib, `libcp_base+0x3eced0`
(VA 0x109066ed0) disassembles to a FUNCTION PROLOGUE
(`pushq %rbp; movq %rsp,%rbp; pushq r15..rbx; subq $0x28,%rsp; movq %rsi,%rbx;
movss 0x10(%rdi),%xmm0; movaps %xmm0,-0x40(%rbp); ...; callq 0x10904ad20`),
NOT a mulps/maxps/sqrtps SIMD body. So **anchorPassed = False** for all four
runs. The anchor offset in the spawn prompt does not match this binary (stale
offset or different reference base). This does NOT invalidate the 0x369fa4
capture: that breakpoint bound to exactly 1 location and stopped cleanly at
the IRAMP accumulator on every run (state 5), with a stable backtrace
(`#0 sym_3661b0 -> #1 sym_365960 -> #2 sym_3ec770 -> #3 sym_3ec960 ...`).
The mismatch is in the verification anchor, not the probe target.

## Method (reproducible)

Manual-stop pattern, NO breakpoint script-callback (an exception inside a BP
callback aborts the inferior with a spurious `Cannot open` + status 1):

1. stop at `main`
2. compute `libcp_base` (iterate modules, match `libcp.dylib`,
   `GetObjectFileHeaderAddress().GetLoadAddress`)
3. disassemble anchor at `base+0x3eced0` (record mnemonics -> anchorPassed)
4. create a BARE breakpoint at `base+0x369fa4`; delete the `main` breakpoint
5. `process continue` -> lldb stops at the FIRST hit (manual stop)
6. read 16 floats at `$rbp-0xa0` + regs (rdi rdx rax rsi rcx rip rbp) + a short
   backtrace; write a per-zoom RESULT json from inside lldb (Python file I/O so
   the capture persists regardless of stdout / any later teardown)

Renders were run STRICTLY SEQUENTIALLY, one at a time.

## Known runtime quirk encountered

`lri_process` intermittently prints `Cannot open: <input.lri>` and exits status
1 BEFORE reaching the accumulator. OBSERVED to be a stdio/timing interaction:
the identical `.lldb` script fails ~always when lldb stdout is wrapped in a
nested-subshell `| tee`, and succeeds (3/3, then 1/1 per zoom) when lldb is run
directly. Mitigation: run lldb directly with a retry loop; the RESULT json is
only written on a real first-hit stop. The render path itself is genuine:
console shows `LRIS auto-detected`, `[profile=3 fmt=3(HDR) +lris]`,
`LRIS state loaded.` before the accumulator hit.

## 150mm note (scope-bound)

150mm is documented as possibly SIGABRT under instrumentation. In THIS run it
did NOT crash: we stop at the FIRST `0x369fa4` hit (state 5) and quit before any
later-stage code that might abort runs. No signal/abort line appeared in the
150mm log. This is NOT a claim that 150mm "never" crashes — only that this
single first-hit capture completed cleanly.

## Files

- `manifest.json` — lane, libcp sha256, the 4 Unit-2 LRI paths
- `commands.txt` — exact commands
- `observations.md` — per-zoom verbatim 16-float tile + OBSERVED match/differ
- `non_claims.md` — scope bounds (NOT a universality / reducer / merge claim)
- `proof_or_disproof_plan.md` — how Codex can validate or refute
- probe scripts: `tools/lldb_probes/opus_pending/laneB_unit2_fourzoom/`
- raw logs + result json: `runs/laneB_unit2_fourzoom/`
