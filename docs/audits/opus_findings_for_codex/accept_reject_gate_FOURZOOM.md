> GRADUATED to four-zoom OBSERVED (2026-06-03, W1b — four_zoom_data_W1b.md). gate+0.25 ceiling fire 4-zoom; 35mm near-boundary 0.2485; gate2/3 still untriggered. Scope=first-hit/tier, Unit-1.

<!-- provenance: runtime probe agent abe3fd62 (single 70mm render) + static, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine). OBSERVED runtime backtrace + thresholds extracted; the
gate identity is a STRONG LEAD (runtime-anchored to confirmed vtable, not yet live-watched at the branch).

# Lane D — final merge ACCEPT/REJECT gate LOCATED (prefusion candidate scoring)

## How it was found (un-fenced: runtime backtrace crosses the __const indirect dispatch)
`0x218e20` (the score/fraction array-filler) is reached via an indirect function-ptr in `__const 0x6580b0`
slot +0x30 — static couldn't find its caller. A runtime BP + backtrace (70mm render) crossed it:
`0x218e20` runs as a **pooled parallel-for task body** — backtrace = `0x5ed0` (generic parallel-for worker:
`lock xaddl` work-counter, then `callq *0x30(%rax)` = the task body) → `0x4de0` (thread-pool scheduler) →
`0x2770` (pthread trampoline). So the immediate caller is the thread pool, NOT the gate.

## The gate = the SPAWNER `0x216f60`, block `0x217ab9..0x217af9` (LEAD, runtime-anchored)
The runtime `call *0x30(rax)` ⇒ `rax = vtable 0x6580b0`; that vtable is LEA-installed ONLY at `0x2179d9`
inside `0x216f60` (the `eax==0` branch). `0x216f60` (frame 0x6c8):
1. Allocates the polymorphic scoring functor; stores stack arrays into it — **fraction array `-0x410` →
   functor+0x38** (matches the filler's `*(rbx+0x38)` fraction store), score region `-0x3f0/-0x430`
   (matches the filler's `*(rbx+0x18)` mean-score store at `0x218f88`).
2. `0x217a42 callq 0x5670` — spawns the recursive divide-and-conquer parallel-for (runs `0x218e20` per tile).
3. Joins (`0x217a47..0x217a65`).
4. `0x217a68..0x217aa2` — scans score array `-0x3f0` for the extreme element (argmax/argmin via
   `ucomiss (%rcx),%xmm0; jae`) → selects the best candidate index.
5. **THREE REJECT GATES on the selected index (`0x217ab9..0x217af9`):**
   - `0x217ab9` load fraction `-0x410[idx]`; `0x217ac9 jb 0x217bf8` ⇒ **REJECT if fraction < 0.25**
     (const `0x5a8200` = 0.25).
   - `0x217ad2 ucomiss (rsi,rdx,4),xmm0; 0x217ad6 ja 0x217bf8` ⇒ **REJECT if fraction > a 2nd array elem.**
   - `0x217ae8.. movss score; mulss 0.8 (const 0x5d5350); ucomiss; jb 0x217bf8` ⇒ **REJECT if 0.8·score <
     comparator.**
   - all rejects → `0x217bf8` = array free/teardown chain (drops the candidate).
   - **ACCEPT** path `0x217aff+`: reads the 24-byte-stride record array `-0x430`, calls `0x218390` →
     `0x264980` → `0xf33d0` (records the accepted contributor).

## Extracted thresholds (clean-room-relevant)
- Fraction floor = **0.25** (`0x5a8200`).
- Score scale-before-compare = **0.8** (`0x5d5350`).
- Gate 2 = relational vs a 2nd fraction-array element (no literal).

## Reframe of `0x216f60` (reconciles the earlier "geometry builder" read)
`0x216f60` is the **prefusion candidate ACCEPT/REJECT orchestrator**: builds candidate transform/records →
spawns parallel scoring (`0x218e20` filler + `0x218b30` stats reducer) → joins → argmax → thresholds →
accept (`0xf33d0`) or drop. The earlier `geom_record_consumer_static.md` view (record-builder, callers
`0x22aaf0`/`0x22d250`) is the record-building half of the same function.

## OBSERVED vs LEAD
- OBSERVED: 70mm hits the path (28mm `L16_02130` ran to 100% but `0x218e20` NEVER fired ⇒ prefusion-state
  path is TELE-gated); backtrace `0x5ed0→0x4de0→0x2770`; immediate caller = thread pool (no gate there).
- LEAD (static, anchored to runtime-confirmed vtable `0x6580b0` + the +0x38 field match): `0x216f60` is the
  spawner and `0x217ab9..0x217af9` is the gate. NOT yet live-watched at the branch.

## Next (clean upgrade LEAD→OBSERVED)
BP `0x217ab9` on a 70mm render; read xmm0 (fraction) + which `jb/ja` branch is taken per candidate; confirm
the 0.25 / 0.8 thresholds fire and tally accept vs reject counts. One render; breakpoints work.

## LIVE CONFIRMATION (runtime probe a3d739f, single 70mm render) — gate is OBSERVED; gate1 = 0.25 CEILING
BP `0x217ab9` fired **8×** in one 70mm render. Live fractions (xmm0): `0.0, 0.0013, 0.0, 0.9174, 0.2762,
0.6656, 1.0, 0.8238`. Outcome via fall-through BPs (pass1=0x217acf, pass2=0x217adc, accept=0x217aff,
call=0x217bbe): **gate1 rejected 5, gate2 rejected 0, gate3 rejected 0, accepted 3** (all 3 reached
`0xf33d0`). accept:reject = **3:5**.
- **CORRECTION to the earlier LEAD:** gate1 `0x217ac6 ucomiss %xmm0(frac),%xmm1(0.25); 0x217ac9 jb 0x217bf8`
  ⇒ CF=1 when 0.25 < frac ⇒ **reject when fraction > 0.25**. It is a **CEILING, not a floor**: the 5 rejected
  were exactly the 5 fractions >0.25; the 3 kept were the 3 ≤0.25. So low-fraction (consistent) candidates
  survive; high-fraction (high threshold-exceed / disagreement) candidates are dropped.
- Constants confirmed LIVE (read from process memory during render): `0x5a8200`=0.25, `0x5d5350`=0.8.
- Gate2/gate3 executed but rejected 0 of the 3 survivors this run ⇒ their reject DIRECTION is present-but-
  untriggered here (only gate1's reject was empirically exercised). Small sample (8), one 70mm Unit-1 seed.
- Status upgrade: the gate location + gate1 threshold/direction are now **OBSERVED**; gate2/gate3 reject
  semantics remain LEAD (untriggered).

## Reconciliation vs committed evidence (this ADVANCES PAST Codex's frontier — not a redo)
Codex's committed `bundle_static_prefusion_sentinel_216f60_scan_count_window.md` maps `0x216f60` only over
`0x216f60..0x217110` (the positive-(x,y)-pair SCAN-COUNT / sentinel-filter window) and explicitly states it
"does NOT prove ... final acceptance / rejection semantics" (and `lldb_state_machine_return_runtime_four_zoom.md`:
"does not prove that any State value is an acceptance, rejection ... acceptance/rejection policy"). The gate
found here is at `0x217ab9..0x217af9` — AFTER `0x217110`, the next section — and the accept consumer is
`0xf33d0` (CalibStage write). So this lane resolves the exact "final acceptance/rejection semantics" that
Codex's committed evidence left OPEN: the post-scan argmax + 0.25 exceed-fraction ceiling (+2 gates) decides
accept→write candidate into the current CalibStage vs reject→teardown. Codex to validate.
