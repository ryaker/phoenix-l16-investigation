# Lane A2 -- Proof / Disproof Plan (for Codex independent validation)

status: NEEDS_CODEX_VALIDATION

The central bounded gap (O8): static DIRECT-call analysis finds NO path from the 0x23faf0 record
family to the image kernels, BUT 3 of 6 kernels (0x2f78e0, 0x3ec960, 0x369f80) are reached via
vtable / std::function indirection that static disasm cannot cross. The plan below targets that gap
and the per-camera-vs-fusion question.

## P1. Close the indirect-call gap (vtable / std::function dispatch)
- Statically: enumerate every vtable slot and every `__function::__func` body in __DATA, build an
  indirect-edge candidate set (slot -> body). Re-run the 0x23faf0-host reachability allowing one
  indirect hop. If still EMPTY, the bound strengthens; if a bridge appears, it is the LEAD.
- Runtime (Codex, single instrumented render, no concurrent renders): set a breakpoint on the
  SourceImageCache lambda entry (0x3ec960) and on 0x2f78e0; capture the backtrace. Check whether any
  frame is one of the 23 0x23faf0-host functions. Backtrace presence/absence is the decisive test.

## P2. Per-camera vs cross-camera for the accumulator chain (O3)
- Runtime: breakpoint 0x3ec960; read the CapturedImage::Camera arg and the output Image<vec4x32f>
  destination pointer each hit. If the SAME destination Image is written by calls carrying DIFFERENT
  camera ids -> evidence of accumulation-into-shared-target (fusion-like). If each camera writes a
  distinct destination -> per-camera production (no fusion here). Count distinct cameras per output
  tile across one render.

## P3. Identity of 0x365960's two equal-length std::vector<16-byte> args (O5)
- Runtime: breakpoint 0x365960 entry; dump rcx and r8 vectors (begin/end, element bytes). Determine
  whether they are src/dst geometry, or two source collections. Equal-length constraint suggests
  paired per-element processing; confirm element type.

## P4. Role of 0x2f78e0 bilateral denoise on the src1/src2 path (O6)
- Runtime: breakpoint 0x2f78e0; capture its Image<vec4x32f>& and the two ImageRef args. Determine
  whether the two ImageRefs are the same image (self denoise) or two distinct source images (which
  would reopen a fusion interpretation). Inspect the 0x2f8584 reciprocal block's divisor source.

## P5. Completeness of the kernel seed set (non_claims #5)
- Statically: scan for other strided-pixel write kernels (movaps/addps into (%rX,%rY,4) with row
  strides) not in the current seed set; re-run reachability with the expanded set.

## Disproof conditions (what would refute this packet's bounded reading)
- D1: a runtime backtrace showing a 0x23faf0-host frame above 0x3ec960 or 0x2f78e0 -> refutes O8's
  "no path" reading (would make the record family image-effecting via indirection).
- D2: 0x3ec960 writing one shared output Image across multiple cameras -> the SourceImageCache chain
  is fusion-bearing, not purely per-camera (refines O3).
- D3: 0x2f78e0 consuming two distinct source images -> bilateral block is a fusion normalizer, not
  pure denoise (refines O6).
