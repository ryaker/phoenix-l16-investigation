

> **RUNTIME-RESOLVED 2026-06-03 (`laneA5_output_finalization/colormatrix_runtime_const_RESOLVED.md`):** the "runtime-populated" wording here is superseded. A single 28mm render with a write-watchpoint on `0x671980` shows ZERO render-time writes — the matrix is written ONCE at C++ static-init from a literal pool and is a FIXED CONSTANT = the Ohta/PCA I1I2I3 decorrelation basis ([1/√3..],[1/√2,0,-1/√2],[1/√6,-2/√6,1/√6]). It is `__bss`-resident but constant (relocated by a global constructor), NOT per-render-computed and NOT LRI-derived.
