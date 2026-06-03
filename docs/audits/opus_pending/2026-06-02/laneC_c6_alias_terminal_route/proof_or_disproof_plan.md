# proof_or_disproof_plan — Lane C C6 alias/terminal-route

Each item is for Codex (independent validation; runtime allowed for Codex, NOT for this agent).

## §0 — re-extract anchors (machine-deterministic)
- Re-run `otool -arch x86_64 -tV` on the exact sha256 binary; confirm:
  - `0xf2720` body == `movl 0x60(%rdi),%eax; ret`.
  - `0x3c90a5` == `movb $0x0, 0x30(%rax)` and is dominated by `cmpl $0xf,%eax; jne` at 0x3c909d.
  - constructor `0xf2770` dst-store set == the 24-offset list in observations §1.A.
- Confirm anchor triple at 0x3ecfe4 (mulps/maxps/sqrtps). Decide whether the briefing's 0x3eced0 meant
  function-entry (PASS) or expects the triple literally at 0x3eced0 (then re-anchor target).

## §1 — ANGLE 1 (alias/untested-field) closure
DISPROOF target for "+0x68..0xa0 is a live C6-item alias":
- Identify the C6-item RTTI/typeinfo (search `__ZTV`/`__ZTI` near vtable refs used by `0xf2770`),
  get the type's `sizeof`. If sizeof <= 0x10c and 0x68..0xa0 are padding, the blind-read list is
  conclusively NOT the C6 item -> Angle 1 collapses to the constructor field set.
PROOF target for non-covered DEFINED fields actually mattering:
- For getters `0xf2730` (+0x100), `0xf2740` (+0x4c), `0xf2760` (+0x4d): census their callers
  (`grep callq 0xf2730|0xf2740|0xf2760`), and for each caller decide if the value reaches a
  branch/store that affects image selection. Report reader VAs (the briefing's literal ask).
- For the `0xd8..0xfc` block: identify the consumer (it looked like 3-4 optional<int> tuples in the
  constructor); find readers and whether any are pre-fusion.

## §2 — ANGLE 2 (terminal-filter / non-skipping path) closure
For EACH of the 58 `f2720` callers (list in `angle23_f2720_caller_census.log`):
- Determine the enclosing function entry; check whether a `cmpb $0x0, 0x30(<item-reg>)` dominates the
  call on every path (guard-domination). Output a table: caller VA | guarded? | consumer reached.
- Specifically resolve whether any caller in idiom-2 (passes key to `0xf6c60`/`0xe7730`/etc.) lacks a
  dominating +0x30 guard. If found -> that is a terminal-filter CANDIDATE (cleared item still selected).
RUNTIME disproof (Codex only): set a read-watchpoint on item+0x30 after 0x3c90a5 fires during a
four-zoom bridge render; observe whether any post-clear reader returns 0 and STILL proceeds to a
store/kernel. (This agent is forbidden from running it.)

## §3 — ANGLE 3 (alternate route) closure
- Forward dataflow from the group-type-2 key-collection list (`0x150(%r14)` store in §2.B): find where
  that list is consumed; trace whether a list entry's index/key selects a frame buffer that enters an
  image kernel (e.g. reaches 0x3ecfe4 SIMD region or a known merge accumulator).
- Independent route search: `grep` for any function that both (a) calls `0xf2720`/reads item+0x60 and
  (b) computes a buffer pointer passed to a kernel, WITHOUT going through the 58-call census target —
  e.g. inlined +0x60 reads (`movl 0x60(<reg>)` where <reg> provenance == C6 item). Report found-as-LEAD
  or "no static alternate route."
- RUNTIME (Codex only): breakpoint group-type-2 consumers under four-zoom HDR; confirm whether a
  cleared key-15 item ever produces pixels.

## Pass/fail framing for Codex
- A real "terminal-filter exists" verdict requires BOTH: (a) a reader of the cleared item on a
  non-skipping path AND (b) that path reaching an image-effecting store. Static signature alone =
  CANDIDATE only (per Rich's two-condition rule).
