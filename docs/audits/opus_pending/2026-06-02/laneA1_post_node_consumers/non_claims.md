# Lane A1 — Explicit NON-claims

This packet is STATIC disasm only. It does NOT establish any of the following:

1. **NOT the reducer / NOT the merge.** No claim that 0x23faf0, the 0x23c917 widening block,
   0xdb240, or 0x1dc5a0 reduces N camera frames to 1, or combines any image data. None of the
   verified "reducer/merge" criteria (signature accepts N>1 frames AND body reduces N->1 with
   pointed accumulator stores) are met or even tested here.

2. **NO image effect.** Nothing here touches pixels/planes/Bayer/tiles. The fields at
   +0x28..+0xa0 are floats/doubles consistent with a transform/geometry record; their pixel
   relevance is unproven.

3. **NO runtime confirmation.** No process launch, no breakpoint, no register capture. The
   "node lands in stack slot -0x1f8 / -0x378" and "consumer reads +0x28..+0x50" statements are
   static control-/data-flow reads of bytes, NOT observed at runtime. The two producer call
   sites may execute zero, one, or many times per render; that is untested.

4. **Node layout is INFERRED**, not a struct definition. Offsets are labeled from store/load
   widths, not from RTTI or a header.

5. **0x1dc5a0 / 0x1dd3b0 internals not fully decoded** — classified only by prologue + first
   ~60 instructions. Bounded "feeds a 0x48 double matrix into stride-0x28 processing"; the
   downstream effect is a LEAD, not characterized.

6. **No cross-render / four-zoom / two-unit generality.** All of the above is one function in
   one binary build (sha256 b38dc4b3...); nothing about zoom tier or camera count is implied.

7. **The orientation doc chain** (0x23c5f0 -> 0x264440 -> 0x264270 -> 0xf34e0 -> 0x23faf0)
   was used only for orientation; this packet independently re-derived 0x23faf0's caller as
   0x23c5f0 from the binary, but did NOT validate the rest of that chain.
