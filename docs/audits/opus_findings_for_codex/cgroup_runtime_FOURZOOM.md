<!-- GRADUATED finding. provenance: C-group runtime render batch (cgroup-render a34f8fffd4305cdd8) using native drain-count + first-hit reads, all VAs on-disk-re-verified, 2026-06-04. Consolidates + graduates rows 12/67/70/73/76 and carries TWO load-bearing corrections. -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to four-zoom OBSERVED** (Tier 1). Runtime LLDB across the
canonical tiers via the **native drain-count** harness (`breakpoint command add -o "continue"` → read
`breakpoint list` hit-count) and first-hit reads. **METHOD CORRECTION (2026-06-04, supersedes the original
"python drops hits" note):** the earlier 0-counts were a **breakpoint-BINDING artifact, not a python-callback
flaw** — BPs set on raw **file VAs** never bound through the ASLR slide (lldb "unresolved, hit count 0"). Set
**module-relative** (`breakpoint set --shlib libcp.dylib --address 0xVA`), even a python in-frame callback
captures every hit with ZERO drops. The reusable rule: **always set BPs module-relative** so they bind through
ASLR; a raw `--address` on this PIE dylib silently fails and looks like "doesn't fire." (Native-vs-python is
NOT the proven discriminator.) Output via `.hdr`/`--profile 3` (full Renderer; `--export-fmt` is overridden by
the output file extension).

# C-group runtime — four-zoom (merge-projection, gates, calib-link, lane-E topology)

## ⚠ TWO CORRECTIONS (prior claims REFUTED)
1. **Level L2-4 (`0x3d0650`) FIRES on every tier — the "L2-4=0 / only L0,L1 / zoom-independent" claim is
   REFUTED.** The prior 0 came from UNBOUND breakpoints (raw file-VA, not bound through ASLR — see method
   correction above), not a real absence. Native counts (reproducible): see §4. The merge
   runs a genuine multi-level pyramid (L0+L1+L2-4), and the counts are **tier-VARYING**, not invariant.
2. **gate2/gate3 (`0x217acf`/`0x217ae3`, inside `0x216f60`) DO FIRE — refutes W1b "untriggered at 28mm."**
   28mm=3/3, 35mm=3/3, 70mm=4/4 hits; 150mm=0/0 (that render took a notably shorter ~3s path) — scope-bound
   0-under-tested-conditions, NOT "never fires."

## 1. Merge-projection radial table `0x3e42e0` ≈ IDENTITY (row12) — four-zoom
Table at `*(*(rsi+8)+0x100)`, indexed `table[radius]`, applied as a scale multiplier at `0x3e43cc`.
| Tier | table[0..7] | far samples | verdict |
|---|---|---|---|
| 28mm | ~1.000000–1.000005 | [1000]=1.0023, [2000]=1.0084, [4095]=0.9999 | ≈identity |
| 35mm | ~1.000000–1.000005 | ≡28mm | ≈identity |
| 70mm | (prior wave) | — | ≈identity (≤0.06%) |
| 150mm | 1.000000 exact | [2000]=1.0016, [4095]=0.9998 | ≈identity (tighter) |
Max deviation ≤0.84% mid-radius (vs tens-of-% for a real distortion LUT). ⇒ **undistort is a SEPARATE
pre-merge stage (`0x261940`), NOT re-applied at merge-projection** — confirmed all tiers.

## 2. Post-merge color matrix = fixed I1I2I3, four-zoom bit-verified (row25)
WRITE-watchpoint on the matrix (the live const is at **`0x5f2380`** `__const`; the consumed `__bss 0x671980`
is its static-init copy — note `0x671980` is zerofill so its *file* offset reads as an adjacent ASCII string):
**0 write hits on 35/70/150mm** (+ 0 on 28mm prior), matrix bits `3f13cd36 3f13cd36 3f13cd36 3f350529 …`
= I1I2I3 opponent-color decorrelation on every tier. Static-init ⇒ tier-invariant, now bit-confirmed 4-tier.
(Also see `merge_magnitudes_FOURZOOM` §3.)

## 3. gate2/gate3 fire + calib↔merge link REFUTED (rows 70, 67) — four-zoom
- **Gates fire** (native count): 28/35/70mm = 3/3, 3/3, 4/4; 150mm = 0/0 (short path, scope-bound). Confirms
  the gate2/gate3 reject semantics (`gate2_gate3_reject_semantics`) are LIVE, not dead code.
- **Calib-State (`%rdi`@`0x216f60`) vs merge-projection (`%rsi` & `*(rsi+8)`@`0x3e42e0`): SAME_OBJECT = NO,
  ∅-overlap on all tiers** (28/35/150 + 70 prior). The direct calib→merge object link is **REFUTED** four-zoom
  (the calibration-refinement State and the pixel-merge projection state are distinct objects).

## 4. Lane-E topology runtime tally (rows 73, 76) — four-zoom (native counter)
**Level dispatcher** (`0x3ec9dc` selects: L0=`0x3ec770`, L1=`0x3ebb80`, L2-4=`0x3d0650`):
| Tier | L0 | L1 | L2-4 |
|---|---|---|---|
| 28mm | 297–300 | 341–346 | 362–366 (2-run reproducible) |
| 35mm | 232 | 280 | 232 |
| 70mm | 220 | 266 | 246 (native re-measure 2026-06-04; prior 221/48/0 = python hit-drop) |
| 150mm | 63 | 80 | 59 |
**Collector** (`0x3bf820` per-tile result collector; `0x3bfc40` intrusive 0x80-byte-node list insert):
| Tier | collector 0x3bf820 | node 0x3bfc40 |
|---|---|---|
| 35mm | 240 | 313 |
| 70mm | 252 | 323 |
| 150mm | 60 | 101 |

## Scope / residuals
- Tallies: dispatcher native ALL FOUR tiers (70mm re-measured 2026-06-04 = 220/266/246, replacing the
  python-hit-drop 221/48/0); collector 35/70/150 native (28mm prior). Matrix/projection = single mid-render
  read per tier. Unit-1 only. gate 150mm 0-hits is tier-conditional, not universal.
- Did not investigate WHY L2-4 fires (only that it does); the pyramid-level semantics are a follow-on.
