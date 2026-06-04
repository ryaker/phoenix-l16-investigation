<!-- orchestrator render-batch plan, 2026-06-04. Ready to launch when the C-group render batch (cgroup-render) frees the SEQUENTIAL render slot. Renders are one-at-a-time only. -->
**Status:** PLAN (not executed). The remaining render-owed staging docs after the C-group batch. **Do NOT
run concurrently with another render** — sequential only (Rich's rule, external disk + Rosetta).

# Next render batch — "color consumption" group (rows 34, 48, 49)

## Two-site color picture (static, established 2026-06-04)
There are **two distinct color-apply sites** (confirmed not call-linked: `0xa9f20` calls `0xaa110/0xf540/
0xa9340`, never `0xbfa20`):
- **`0xbfa20` = fixed Ohta I1I2I3 decorrelation** (1/√3,1/√2,1/√6) — GRADUATED four-zoom (`merge_magnitudes`
  §3): exclude-both → clean exit all 4 tiers ⇒ no per-camera matrix here.
- **`0xa9f20` = per-camera CCM apply**, matrix arg = `*[BayerPipelinePayload+0]+0x14`, reached via the
  captureless `$_58` lambda (`0x346b00` trampoline → `0x3466d0`); sub-applies `0xa9340`. This is the
  "other VA" residual that `merge_magnitudes` §3 explicitly deferred. **NOT yet runtime-read.**

## Tasks (BP-read + write-watchpoint + large-effect differential — all Rosetta-valid; NO read-watchpoints)
1. **rows 48/49 — per-camera CCM confirm at `0xa9f20`** (ALL 4 tiers). BP `0xa9f20`; read the matrix at
   `*[payload+0]+0x14` (and/or at sub-apply `0xa9340`). Confirm it carries a **per-camera CCM** (expect a
   real CCM e.g. cam0 v2 `[0.8996,0.1317,−0.0671; …]` or row-sums `[0.9642,1.0,0.8252]`), NOT I1I2I3.
   Determine which Block-6 variant {0,2,6} is selected (fixed vs per-camera). Use ignore-count if `0xa9f20`
   fires many times; first-hit if few.
2. **row 49 — payload `+0x14` WRITER** (write-watchpoints WORK under Rosetta). Set a WRITE-watchpoint on
   `*[BayerPipelinePayload+0]+0x14` once the payload is allocated (break `0x3184d0`/`0x318dc8` setup, get the
   payload ptr, watch +0x14). Catch the code that copies the parsed LRI Block-6 CCM into the payload — closes
   the end-to-end LRI→runtime-4×4 link (the one piece `ccm_lri_residency_link` left OPEN).
3. **row 34 — AWB reciprocal consumption** at 35/70/150mm (28mm DONE: large effect, trustworthy). Per tier:
   parse B8.19.15 → compute 1/R, 1/B; find the reciprocal heap copies at `Renderer::render` entry
   (`0x390180`); overwrite (e.g. 1/R→0.125), re-render, compare **decoded-pixel** SHA (NOT file hash —
   embedded timestamp/JPEG-entropy trap). Expect the same large channel-collapse as 28mm ⇒ four-zoom
   confirmation that WB = 1/gain folded into the demosaic color matrix. (Large effect ≫ the 0.034 nondet
   floor, so differential is valid here despite the multithread nondeterminism.)

## Method reminders (from W5/W5b + the AWB/CCM probes)
- read-watchpoints DEAD; **write-watchpoints WORK**; pixel-hash differential valid ONLY for large effects
  (libcp output is multithread-nondeterministic, ~48% pixels differ run-to-run, mean floor ~0.034 counts —
  this nondeterminism is itself a SPIKE-ACCEPTANCE finding: validate Phoenix statistically, not by hash).
- ignore-count `-i N` (N below the BP's call count) / conditional `-c` (pointer-cast form) reach mid-render
  with no stampede. Hash DECODED pixels, never the output file.

## Then remaining
After this batch: row 77 (corpus-capped — needs a 182-class "unassigned" LRI not in the 8-seed corpus),
and any Unit-2 RUNTIME (corpus lacks a clean U2 35mm). Those are corpus-limited, not method-limited.
