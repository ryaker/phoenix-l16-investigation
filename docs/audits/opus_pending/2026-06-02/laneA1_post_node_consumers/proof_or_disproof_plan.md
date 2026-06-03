# Lane A1 — Proof / disproof plan for Codex (RUNTIME)

Goal: confirm/refute that the static "consumer" actually reads the node fields produced by
0x23faf0 at runtime, and that the produced node reaches the RB-tree record.

Binary: `/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process` driving libcp.dylib
(sha256 `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`).
Use `arch -x86_64 lldb`. Use `process continue` (NOT thread continue). NO auto-continue=true.

## Experiment 1 — capture the dst-node pointer at producer return
1. `b 0x23c6da` (call site 1) and `b 0x23cbbc` (call site 2).
2. On hit, read the dst-node arg: `frame.FindRegister("rdi")` — but rdi is loaded by `leaq`
   immediately before the call, so instead read the effective address:
   - site 1: dst = `rbp - 0x1f8`  -> `expr (void*)($rbp - 0x1f8)`
   - site 2: dst = `rbp - 0x378`  -> `expr (void*)($rbp - 0x378)`
3. Set a hardware WATCHPOINT on dst+0x30 (4 bytes, write) to confirm 0x23faf0 actually writes
   the transform region during the call. Expect the watchpoint to fire inside 0x23faf0
   (around 0x240105/0x23fb63 stores). Record the written value.

## Experiment 2 — confirm the consumer READS those bytes
1. Keep dst pointer P from Exp.1 (site 1, P = rbp-0x1f8 captured at 0x23c6da).
2. After the producer returns (`process continue` to 0x23c6df), set a READ watchpoint on
   `P + 0x30` (4 bytes) and on `P + 0x50`.
3. `process continue`. PASS if a read watchpoint fires at an instruction in
   `0x23c855..0x23c98a` (the cvtps2pd widening block) BEFORE the next producer call or function
   return. Record the firing PC. FAIL/INCONCLUSIVE if it never fires (means the static slot
   mapping is wrong or that block is dead under this capture).

## Experiment 3 — confirm widened values land in the r14 RB-tree record
1. `b 0x23c952` (first `movups %xmm1,0x28(%r14)`).
2. On hit: `expr -- (void*)$r14` to get record base R. Dump `R+0x28..R+0xa0` as doubles
   AFTER the block (b 0x23c98e) and compare to `cvtps2pd` of P+0x00..P+0x50 floats.
   PASS if R[+0x28] == (double)P[+0x00], R[+0x88] == (double)P[+0x24], etc.
3. `b 0xdb240`; on hit `expr -- (void*)$rsi` should equal R (the same record being inserted
   into the tree). Confirms the produced-node-derived record is the RB-tree node.

## Suggested capture
- 28mm anchor first: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`
- then 70mm `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` to check call-count/zoom.
- Count how many times each producer site (0x23c6da, 0x23cbbc) fires per render — informs
  whether this is per-camera, per-tier, or per-render. (Static cannot answer this.)

## Disproof conditions
- If the read watchpoints in Exp.2 NEVER fire under any tested capture -> the static
  consumer mapping is refuted (these slots are not re-read; node may be consumed only by the
  RB-tree pointer copy, not by field reads).
- If 0xdb240's rsi != R -> the produced record is not the tree node; re-trace the pointer.
