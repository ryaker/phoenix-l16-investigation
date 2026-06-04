<!-- provenance: l16-investigator finder (static disasm + byte-search) + orchestrator re-extraction, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC; finder + orchestrator-verified). ADVANCES but does NOT
fully close the LRI Block-6 → runtime CCM link from `ccm_apply_site_located.md` — the actual `+0x14` writer
stays OPEN (runtime). Binary `libcp.dylib`.

# Lane B2 — CCM is LRI-resident + payload-delivered (4×4); the `+0x14` writer remains OPEN

## VERIFIED (re-extracted this pass)
- **CCM constants ABSENT from the binary** ⇒ LRI-residency confirmed: per-camera row-sums `0.9642` = **0 hits**,
  `0.8252` = **0 hits** (`0.82521` = 1 incidental hit in an unrelated dense coeff table). Method-validated: the
  byte-search DOES find baked matrices — the fixed I1I2I3 basis is present at `0x5f2380` — so 0 hits is real
  absence, not a broken scan. (Clean-room Rule #0: CCM parsed from LRI at render time.)
- **The `$_58` apply lambda is CAPTURELESS:** trampoline `0x346b00` = `mov rbp,rsp; 0x346b04 mov rdi,rsi;
  0x346b08 jmp 0x3466d0` — it DISCARDS the `std::function` `this` and forwards only the payload (rsi). ⇒ the
  matrix is NOT carried in the std::function; it can ONLY come from the payload. Confirms matrix arg =
  `*[BayerPipelinePayload+0]+0x14` (`0x346797 mov rbx,[r15]; 0x3467a3 add rbx,0x14; 0x3467b4 mov rdx,rbx;
  0x3467ba call 0xa9f20`).
- **Matrix is stored/applied as 4×4 (3×3 promoted):** `0xbfa20` loads four 16-byte rows
  (`movups [rcx], [rcx+0x10], [rcx+0x20], [rcx+0x30]`) = `lt::ImageApplyColorMatrix` `Matrix<float,4,4,true>`
  variant. The padding row/col (1.0/0.0) is added by a 3→4 promotion (LEAD: `insertps`+1.0f near orchestrator
  `0xaa260`, UNVERIFIED candidate).
- **`setColorCorrection` stage-registration = `0x335620`** (re-extracted: `0x335634 mov r14d,esi`,
  `0x33564c cmp r14d,0x3`, jump table `0x337134`) — takes a pipeline-TYPE selector (esi∈{0..3}), **NO
  ColorCorrection argument**: it installs the apply STAGES with identity defaults (a construct/reset path),
  NOT the matrix writer. Single caller `0x318dc8` (render-setup); pipeline factory `0x3184d0` (alloc 0x16f0).

## REFUTED prediction
"The Pipeline holds the CCM matrix as a member set by a `setColorCorrection(ColorCorrection)` setter." FALSE:
the pipeline offsets that looked like a CC (`+0x2e0..+0x318`, `+0xf40..+0xf78`) actually hold a
`std::function<void(BayerPipelinePayload&)>` object (inline buffer + fn-ptr + data + size); the "default"
`0x3f800000`=1.0f bytes are small-buffer contents, not a matrix. The CCM lives in the PAYLOAD, not the Pipeline.

## STILL OPEN (the one piece NOT closed)
- **The render-time writer of `*[BayerPipelinePayload+0]+0x14`** — the code that copies the 4×4 into the
  payload from the parsed LRI Block-6 `ColorCorrection`. NOT isolated statically (lives in the large templated
  payload/dispatch builder downstream of `0x3184d0`/`0x318dc8`). Resolve via a **runtime watchpoint on
  `payload.field0+0x14`** (Codex domain) or a deeper trace. ⇒ the LRI-bytes → runtime-4×4 link is
  end-to-end INFERRED (both ends OBSERVED: LRI Block-6 f2.2/f2.3 parsed; payload+0x14 consumed by apply), but
  the connecting copy is unproven.
- 3×3→4×4 promotion site (the `0xaa260 insertps` candidate) — unverified.
- Whether `$_59..$_63` (BayerFloat/Color/SoftISP) read the same `+0x14` offset (only `$_58`/Bayer verified).
