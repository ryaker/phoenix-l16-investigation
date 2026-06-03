<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** one claim failed re-extraction (a detail; core stands) — see correction at end; treat that item as LEAD

## 0x374ac0 — src2 margin zero-fill sink: callback identity + column-margin question

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` (Mach-O x86_64). All VAs re-extractable via `arch -x86_64 lldb --batch -o 'target create <lib>' -o 'disassemble --start-address 0x374ac0 --count 230'`.

### Q1 — vtable slot called at 0x374cf1
OBSERVED chain (raw lines):
- `0x374cce  movq -0xb0(%rbp), %rax`  (arg2 saved here at +33: `movq %rsi,%r14`/`movq %r14,-0xb0(%rbp)`)
- `0x374cd5  movq 0x20(%rax), %rdi`   -> callable object = **+0x20 of arg2 (the src2 descriptor)**
- `0x374cd9  testq %rdi,%rdi` / `0x374cdc je 0x374ff1`  -> null target throws
- `0x374ce2  movq (%rdi), %rax`       -> vtable ptr
- `0x374ce5  movq 0x30(%rax), %rax`   -> **slot at byte offset +0x30 (index 6)**
- `0x374ce9  leaq -0x80(%rbp), %rsi` ; `0x374ced leaq -0x38(%rbp), %rdx`  -> args = two constructed rect structs
- `0x374cf1  callq *%rax`

The null-guard branch lands at `0x374ff6 callq __cxa_allocate_exception` then `0x374ffb ... typeinfo for std::__1::bad_function_call`. That throw is emitted by an empty `std::function::operator()`; so the +0x20 object is a **std::function-like callable** and vtable[+0x30] is its dispatch. Plausible role: a tile/region invalidate-or-notify sink that receives the clipped ROI region list (`-0x80`) and the inset rect (`-0x38`). It is NOT a plain "get base pointer" accessor — it is handed region descriptors, not asked to return a pointer.

(Prior committed evidence `docs/evidence/bundle_proof_pair_grid_roi_transform.md:105` already states `object->0x20->vtable[+0x30]`; this packet adds the std::function identification, the exact arg structs passed, and the immutability-check coupling below.)

### Q2 — column margins vs full rows: BOTH are cleared (4 __bzero loops)
- TOP full rows: `0x374d70..0x374d88` — `__bzero(rbx, r14)`, advance `rbx += r13` (`r13 = 0x18(desc) << 4` = row stride in bytes). Whole rows above the ROI band.
- BOTTOM full rows: `0x374fc0..0x374fd4` — `__bzero(rbx, r13)`, advance `rbx += r12`. Whole rows below the ROI band.
- LEFT column margin: `0x374e70..0x374eb4` (reached via +757/+800 when top edge `r13d > eax`) — per-row `__bzero` of a left sub-row band, advancing `rbx` by full row stride each iteration. This clears a **column strip**, not a full row.
- RIGHT column margin: `0x374f30..0x374f4e` (reached via +1019 branch) — per-row `__bzero(rbx, r12)`, advance `rbx += rcx` (row stride). Right column strip per row.

So the answer is explicit: 0x374ac0 clears **left AND right column margins** in addition to top/bottom full rows. Element size is 16 bytes (`shlq $0x4` everywhere; `0x374c0d addq 0x20(%rax),%r12` after `shlq $0x4,%r12`), i.e. 4x f32 per pixel; `+0x18`=row stride (elements), `+0x20`=data base, `+0x10/+0x14`=dims.

### Q3 — copy vs pure clear
OBSERVED: every data-writing instruction in 0x374ac0 is one of the 4 `__bzero` stubs (`0x555eb2`). There is no `memcpy`/`movdqu`-store of src2 pixels to any other buffer; the only movdqu/pinsrd activity (`0x374b9a..0x374c4f`) builds the local 16-byte region/clip structs that are passed to f540/the callback. Therefore 0x374ac0 is a **pure margin-clear of src2's own buffer** — no src2->elsewhere data copy. Supporting LEAD: the `0x375024` branch (taken when the value the callback was expected to preserve, `-0x60(%rbp)`, changes) raises `"image generator modifed immutable output!"` (`0x37503b`), i.e. the callback must NOT relocate/alter the buffer base — consistent with a notify/lock sink over the existing buffer rather than a copy.

### Scope NOT investigated
- I did not runtime-resolve which concrete class furnishes vtable[+0x30] at 0x374cf1 under a live four-zoom bridge run (static only; the +0x20 object's RTTI was not chased to a class name). LEAD, not OBSERVED, on the sink's concrete semantics (invalidate vs notify).
- I did not confirm src2==arg2 maps to the merge "src2" of CLM-PREFUSION-002; I only used the caller-arg roles given in the scaffold. The "src2 descriptor" naming is inherited from the THREAD/prior doc, not independently tied to the merge here.
- I did not trace f540/f4e0 fully (sampled f540 head only; classified as struct reserve/destruct, LEAD).

## Verifier correction(s) — load-bearing
- **0x374e70 / 0x374e79 / 0x374ea4 / 0x374eb4**: 0x374e70: movq %rcx,%r14 (NOT movq %rbx,%rdi as claimed). The movq %rbx,%rdi is at 0x374e73. | 0x374e79: callq 0x555eb2 (__bzero) CORRECT | 0x374ea4: incq %r12 CORRECT | 0x374eb4: jl 0x374e70 CORRECT. The loop structure and __bzero call are real, but the first claimed VA (0x374e70) has the wrong instruction attributed to it -- the actual instruction at 0x374e70 is movq %rcx,%r14, a loop-top register save, not the rdi load.
