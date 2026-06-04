<!-- provenance: l16-investigator finder (static disasm) + orchestrator independent re-extraction of load-bearing VAs, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm; finder-produced, orchestrator-VERIFIED — load-
bearing VAs + the I1I2I3 constant re-extracted, see "Verification"). **Resolves the open residual in
`ccm_consumption_runtime_INCONCLUSIVE.md`** (which couldn't pin the CCM apply site at runtime): gives Codex
exact breakpoint targets and explains why the entry-time proto perturbation was inert. Binary `libcp.dylib`.

# Lane B2 — CCM apply site located: per-camera 4×4 path + the fixed-I1I2I3 decoy

## Breakpoint targets for Codex (apply lambda invoke entries)
| Apply | Invoke ENTRY (BP here) | Per-pixel multiply | Matrix source |
|---|---|---|---|
| **4×4** (exported ns) — the PER-CAMERA CCM path | **`0xbfa20`** | `0xbfad0` inner | `[rdi+0x8]` (capture+0x8) → rows `[m]/[m+0x10]/[m+0x20]/[m+0x30]` |
| 3×3 `$_2` (planar→packed) — the FIXED-matrix decoy | `0x300570` | SIMD `0x3009a0`/scalar `0x300ab0` | `[rdi+0x18]` |
| 3×3 `$_3` (packed→planar) | `0x304170` | SIMD `0x3045f0`/scalar `0x3046f0` | `[rdi+0x18]` |

## The wired per-camera CCM pixel path (OBSERVED, verified call edges)
`lt::Internal::Pipeline::setColorCorrection $_58` (BayerPipelinePayload invoke `0x3466d0`) →
**matrix source = `*[BayerPipelinePayload+0] + 0x14`** (9 floats; `0x3467a3 add rbx,0x14`) → `0x3467b4 mov
rdx,rbx` (matrix arg) → **`0x3467ba call 0xa9f20`** (tiled CCM-apply orchestrator) → builds a std::function
(vtable `0x6527c0`; capture `+0x10`=dst, `+0x18`=src, `+0x20`=matrix) → tile worker `0xbf4a0` → `0xbf511 call
[r11]` (matrix on stack) → inner apply `0xbfa20` (4×4). **Matrix flow:** payload→`[obj+0x14]`→rdx→closure
`+0x20`→stack→apply `[rdi+0x8]`. ⇒ the per-camera CCM is delivered through the closure capture, NOT the
render-entry proto buffer — **this is why `ccm_consumption_runtime_INCONCLUSIVE`'s entry-time perturbation at
`0x390180` was inert** (it overwrote the wrong copy).

## 4×4 apply body `0xbfa20` (OBSERVED, re-extracted exact)
`0xbfa47 mov rcx,[rdi+0x8]` (matrix) → 4× `movups [rcx], [rcx+0x10], [rcx+0x20], [rcx+0x30]` (rows) →
`0xbfa90 mov rdx,[rdi+0x10]`(src)/`0xbfa94 mov rsi,[rdi+0x18]`(dst) → inner: `shufps 0x0/0x55/0xaa/0xff`
broadcast each channel × `mulps` × 4 matrix vectors + `addps` ×3 → store. **Genuine 4×4 matrix·vec4** (all 4
input channels feed each output). Matrix read from a runtime struct field, NOT immediate.

## The FIXED-matrix DECOY (must not be mistaken for the per-camera CCM)
The 3×3 `$_2` construction at `0x2fe03b` wraps a **fixed colorspace-decorrelation matrix** from global
`0x670b00`, initialized at `0x304880` from constants at file `0x5f2380`. Re-extracted bytes:
`[0.57735, 0.57735, 0.57735, 0.70711, 0.0, -0.70711, 0.40825, -0.8165, 0.0]` =
**I1I2I3 / Ohta orthonormal basis** (row0 = luma `1/√3·[1,1,1]`; row1 = `1/√2·[1,0,-1]`; row2 =
`1/√6·[1,-2,?]`). This is a FIXED transform, **not** the LRI Block-6 per-camera CCM. ⇒ a runtime BP on
`0x300570` alone fires on this fixed transform too; **prefer the 4×4 path `0xbfa20` (via `0xa9f20`)** for the
per-camera CCM, or filter `0x300570` hits by `[rdi+0x18]==0x670b00`.

## Cross-check vs lane-b2 __bss find (CORROBORATION)
This independently re-finds the **same I1I2I3/Ohta basis** that [[lane-b2-lri-calibration-origins]] found at
`__bss 0x671980` ("post-merge color matrix = fixed I1I2I3, written once at static-init"). Two independent
discoveries (`0x670b00`/`0x5f2380` here vs `0x671980` there, ~0xE80 apart) of the same fixed decorrelation
basis ⇒ strongly confirms libcp uses a FIXED I1I2I3 colorspace transform (clean-room: reimplement from the
published formula, NOT per-LRI), DISTINCT from the per-camera CCM (4×4 path above).

## Verification (orchestrator independent re-extraction)
- `0xbfa20` matrix `[rdi+0x8]` + 4 row `movups` + `shufps 0x0/55/aa/ff` + `mulps`×4 + `addps`×3 — EXACT match.
- `setColorCorrection $_58`: `0x3467a3 add rbx,0x14`, `0x3467b4 mov rdx,rbx`, `0x3467ba call 0xa9f20` — EXACT.
- Fixed matrix `0x5f2380` decoded — I1I2I3 basis confirmed. **⚠ verify-before-trust catch:** finder reported
  the **9th** constant as `0.40825`; my re-read gives **`0.0`** (row2 = `[1/√6, -2/√6, 0.0]`). Likely a
  vec4-padding/storage-layout difference; the Ohta-basis conclusion is unaffected (rows 0/1 + first 2 of row2
  unambiguous), but the exact 9th element / storage stride is a residual.

## Residuals (NEEDS_CODEX_VALIDATION)
- Trace `*[BayerPipelinePayload+0]+0x14` back to LRI Block-6 CCM parsing (where `ColorCorrection.matrix` is
  populated) — finder confirmed it's the matrix delivered to apply, but NOT the LRI link (out of static scope).
- Which of `$_58..$_63` (Bayer/BayerFloat/Color/SoftISP) fire under four-zoom bridge at runtime (Codex domain).
- Confirm `0xbf4a0`'s `call [r11]` resolves to the 4×4 `0xbfa20` (vs a 3×3) at runtime (indirect dispatch).
- Exact 9th constant + storage stride of the fixed I1I2I3 matrix (0.0 vs 0.40825 discrepancy above).
- The lea-xref sites `0x300c04`/`0x304854`/`0xbfb24` are `target_type()` accessors, NOT apply bodies (finder
  correction — bodies are at the entries in the table).
