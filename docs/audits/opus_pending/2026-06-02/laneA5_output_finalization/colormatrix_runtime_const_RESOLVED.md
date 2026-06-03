# Lane A5 — RUNTIME-RESOLVED: the `__bss 0x671980` 3x3 is a FIXED constant (I1I2I3 basis)

**Status:** `NEEDS_CODEX_VALIDATION`. Method: **single runtime LLDB render** (`lri_process --profile 3` on
the 28mm Unit-1 seed) + static corroboration. This **supersedes the "runtime-populated (per-render)"
implication** in `laneA_prefusion_reducer_static/matrix_36acf0_bss_storage.md` (wave-3): the matrix IS in
`__bss`, but it is written ONCE at C++ static-init from a literal pool and is a **fixed constant**, NOT
computed per-render and NOT derived from the LRI.

## Prediction tested (REFUTED)
Predicted H-COMPUTED: the matrix is computed per-render from the LRI color calibration (Block-6 CCM/spectral).
**Refuted.** Runtime probe verdict = **H-CONST**.

## OBSERVED (single 28mm render, watchpoint on `libcp_loadbase+0x671980`)
- **Zero write-watchpoint hits during the entire render** (0%→100%). Value at `main` (post static-init,
  pre-render) == value at exit, unchanged.
- Matrix value:
  ```
  row0 [ 0.57735,  0.57735,  0.57735]   = [1/√3, 1/√3, 1/√3]   (luminance axis), rowsum 1.7320
  row1 [ 0.70711,  0.0,     -0.70711]   = [1/√2, 0, -1/√2]     (R−B opponent),   rowsum 0
  row2 [ 0.40825, -0.81650,  0.40825]   = [1/√6, -2/√6, 1/√6]  (R−2G+B opponent),rowsum 0
  ```
  This is the **Ohta/PCA `I1I2I3` orthonormal colour-decorrelation rotation** — a standard published
  transform, not a white-balance/CCM matrix.

## Static corroboration (LEAD)
Single writer = a C++ global constructor (calls `___cxa_atexit` at `libcp+0x374505` just before the stores):
- `libcp+0x37450a movaps 0x5f2380(%rip-rel),%xmm0` → store `0x671980` (slots 0–3)
- `libcp+0x374518 movaps 0x5f2390(%rip-rel),%xmm0` → store `0x671990` (slots 4–7)
- `libcp+0x374526 movl $0x3ed10625,0x6719a0(%rip-rel)` (=0.40825) → slot 8
Source operands are fixed `__const` literals, no LRI data dependency. These are the ONLY 3 store sites to
`0x671980..0x6719a4`; 34 other refs are reads (consumers `0x366f48`, `0x3672c7`, `0x368c60`, `0x36ac7d`).

## Clean-room relevance (important)
The post-merge "color matrix" is a **fixed mathematical constant** (I1I2I3 decorrelation basis), not
proprietary per-LRI calibration. ⇒ Phoenix reimplements the I1I2I3 transform **from the formula**
(Rule #0 source class 2: published/derivable) — no libcp bytes, no LRI dependence. It is used by the
detail-transfer/denoise stage (`0x36ac7d` consumer), consistent with lane-3 guided-detail-transfer.

## Scope / not done
- ONE render, ONE seed (28mm Unit-1, `--profile 3`). Not re-run on 35/70/150mm, Unit-2, other profiles, or
  DirectRenderer. Watchpoint was 4 bytes on slot 0 (slots 1–8 not independently watched; the 16-byte
  `movaps` writers touch slot 0, so a slot-only partial writer is unlikely but untested).
- Static-init store runs pre-main (before breakpoint); the non-zero literal value at `main` is OBSERVED
  proof it was written by then. Writer-identity = LEAD (static disasm, not single-stepped).
