# Bundle Proof: `src1` Payload Runtime Surfaces

## Scope

This note proves only what the installed `libcp.dylib` shows about the first visible runtime surfaces reached from the `0x490`-byte payload constructed by `0x3e2db0 -> 0x3e27a0`.

It proves:

- the constructor at `0x3e27a0` writes a vtable/address point at `0x65f140`
- the first visible slots at that address point are `0x3e53a0`, `0x3e54c0`, and `0x3e2dc0`
- `0x3e53a0` and `0x3e54c0` are payload cleanup / destructor bodies
- `0x3d0120` and `0x3e55f0` are callable-slot plumbing helpers, not reducer bodies
- `0x3e2dc0` is a per-payload setup/config fan-out over the four embedded level subobjects
- `0x40b370` is a property/config loader over visible ISP-style setting names
- `0x40b330` is a float-threshold helper that maps one float into one of four small integer codes
- `0x3e2e90` is a single-object, single-level ROI/process body with level-specific subobject selection
- `0x3e3f90` is an ROI-adjust helper driven by the optional callable slot at payload `+0x170`

A follow-up proof, `bundle_proof_src1_project_roi_worker.md`, bounds the deeper callback worker dispatched by `0x3e2e90`.

It does not prove the exact upstream `src1` / `src2` N-to-1 reducer.

It does not prove a multi-camera pixel-reduction body.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Constructor + vtable bytes:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'memory read --format x --size 8 --count 24 0x65f138' -o 'image lookup -a 0x65f140' -o 'disassemble --start-address 0x3e27a0 --count 240'`
- Destructor bodies:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e53a0 --count 240' -o 'disassemble --start-address 0x3e54c0 --count 240'`
- Callable-slot helpers:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d0120 --count 320' -o 'disassemble --start-address 0x3e55f0 --count 320'`
- Setup/config and ROI/process bodies:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e2dc0 --count 260' -o 'disassemble --start-address 0x40b330 --count 120' -o 'disassemble --start-address 0x40b370 --count 320' -o 'disassemble --start-address 0x3e2e90 --count 620' -o 'disassemble --start-address 0x3e3f90 --count 260'`
- Error-string sites in `0x3e2e90`:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e3d20 --count 80'`

## Proven Facts

### 1. `0x3e27a0` writes a payload address point at `0x65f140`

- At `0x3e27d0..0x3e27d7`, the constructor loads `0x65f140` and writes it to payload `+0`.
- Raw memory at `0x65f138` shows:
  - `0x65f138 = 0x65f160`
  - `0x65f140 = 0x3e53a0`
  - `0x65f148 = 0x3e54c0`
  - `0x65f150 = 0x3e2dc0`
- `image lookup -a 0x65f140` reports only:
  `typeinfo for CIAPI::DirectRenderer + 2896`

Therefore the constructor-written address point is `0x65f140`, and its first visible slots are `0x3e53a0`, `0x3e54c0`, and `0x3e2dc0`.

This note does not infer an exact class name from that `image lookup` summary.

### 2. `0x3e53a0` and `0x3e54c0` are destructor / cleanup bodies

- Both bodies begin by restoring the same `0x65f140` address point to `(%rbx)`.
- Both bodies destroy the four embedded `0xa0`-stride subobjects at payload offsets:
  - `+0x210`
  - `+0x2b0`
  - `+0x350`
  - `+0x3f0`
  through repeated calls to `0x318040`.
- Both bodies release callable-like slots at:
  - `+0x170`
  - `+0x1a0`
  - `+0x1d0`
  - `+0x200`
  using the usual inline-self vs heap-object cleanup pattern.
- Both bodies free the vector rooted at `+0x100` if present.
- `0x3e53a0` tail-calls `0x3ddf70` and returns without deleting `this`.
- `0x3e54c0` calls `0x3ddf70` and then tail-calls `operator delete`.

Therefore `0x3e53a0` is the non-deleting destructor body and `0x3e54c0` is the deleting destructor body for this payload family.

### 3. `0x3d0120` is callable-slot install/move plumbing for the payload subobject at `+0x10`

- The body works on a small object whose active callable pointer lives at `+0x70`, with inline storage rooted at `+0x50`.
- It first destroys any existing callable/object at `+0x70`.
- It then reads the source callable holder from `%rsi`.
- If the source holder is null, it stores null at `+0x70`.
- If the source holder points to an external object, it moves that pointer into `+0x70` and nulls the source.
- If the source holder points to itself, it sets `+0x70 = this+0x50` and invokes virtual slot `+0x18` to clone into the inline storage.

Therefore `0x3d0120` is callable-slot install/move plumbing. It is not a multi-camera reducer body.

### 4. `0x3e55f0` is callable-slot swap/move plumbing

- The body operates on two callable holders whose active object pointers live at `+0x20`.
- It handles the three visible cases:
  - direct external-pointer swap
  - clone-from-inline on one side, then destroy old target on the other
  - temporary clone when both sides are self-held
- The visible virtual calls use slot `+0x18` for clone/copy behavior and slot `+0x20` for destruction/cleanup.

Therefore `0x3e55f0` is callable-slot swap/move plumbing. It is not image reduction math.

### 5. `0x3e2dc0` is a per-payload setup/config fan-out, not a reducer body

- The body calls `0x3ddf30` repeatedly on `%rbx` before each per-level fan-out step.
- It dispatches four calls to `0x40b370`, using the embedded payload subobjects at:
  - `+0x210` with `edx = 0`
  - `+0x2b0` with `edx = 2`
  - `+0x350` with `edx = 3`
  - `+0x3f0` with `edx = 4`
- After those four calls, it calls `0xf32d0`, reads one float from the returned object, passes that float to `0x40b330`, and stores the integer result into payload `+0xf4`.

Therefore the visible body of `0x3e2dc0` is setup/config work over four embedded per-level subobjects plus one small quantized setting write. It does not expose N-to-1 image reduction.

### 6. `0x40b330` is a float-threshold helper

- The body initializes `%eax = 0x11`.
- It then compares `%xmm0` against successive constants and may replace the return with:
  - `0x21`
  - `0x41`
  - `0x81`

Therefore `0x40b330` maps one float input to one of four small integer codes. This is a threshold/quantization helper, not a reducer.

### 7. `0x40b370` is a property/config loader over visible ISP-style setting names

- The body visibly receives five arguments in `%rdi`, `%rsi`, `%edx`, `%rcx`, and `%r8`.
- The visible body repeatedly constructs strings and queries properties through helpers such as `0x31b560`, `0x31ba20`, and `0x31bb10`.
- The directly observed strings include:
  - `demosaicking.type`
  - `light_v2`
  - `auto_white_balance.type`
  - `manual_temp`
  - `auto_white_balance.neutral_temp`
  - `auto_white_balance.neutral_tint`

Therefore `0x40b370` is a property/config loader over ISP-style settings. In the visible installed-bundle body it does not present a vector-of-cameras or N-to-1 reduction shape.

### 8. `0x3e2e90` is a single-object, single-level ROI/process body

- The entry signature is visibly:
  - `%rdi = this`
  - `%rsi = output object`
  - `%rdx = ROI-like rectangle`
  - `%ecx = level`
- At `0x3e2ec2`, the body rejects `level >= 4`.
- The error path at `0x3e3d3f` throws `Unsupported level`.
- At `0x3e2ec8..0x3e2f19`, it computes `1 << level` and scales the incoming ROI coordinates by that factor.
- If payload byte `+0xf0` is nonzero, it calls `0x3e3f90` to adjust the ROI before continuing.
- It then clamps against payload dimensions at `+0xa8/+0xac`.
- The empty-ROI path at `0x3e3d8d` throws `Empty AABB!`.
- It calls `0x1bdc80` using payload fields `+0x98` and `+0x90`.
- It selects the per-level subobject by:
  `this + 0x210 + level * 0xa0`
- It reads the property `denoising.type`, normalizes it with `0x31bbd0`, and compares against `none`.
- The visible body then continues through level/ROI/image processing work, including a later LUT-building section beginning at `0x3e3810`.

Therefore `0x3e2e90` is a large single-object, single-level ROI/process body. In the visible installed-bundle body it is not direct proof of a multi-camera reducer.

### 9. `0x3e3f90` is an ROI-adjust helper driven by the optional callable at payload `+0x170`

- The body first reads payload `+0x170`.
- If that slot is null, it falls back to a null local callable path.
- If that slot points to an external object, it invokes virtual slot `+0x10`.
- If that slot is the inline self-held object rooted at `+0x150`, it invokes virtual slot `+0x18`.
- The result is passed through `0x260b70`, then rounded and converted to integers.
- The visible arithmetic snaps the coordinates to even-aligned boundaries before writing:
  - output `x0` at `(%r15)`
  - output `y0` at `0x4(%r15)`
  - output `x1` at `0x8(%r15)`
  - output `y1` at `0xc(%r15)`

Therefore `0x3e3f90` is an ROI-adjust helper built around the optional callable slot at payload `+0x170`. It is not exposed image-reduction math.

## Safe Conclusion

- Proven:
  the `0x490`-byte payload built by `0x3e27a0` has a constructor-written address point at `0x65f140`.
- Proven:
  the first visible payload slots are destructor bodies plus one substantive visible virtual body at `0x3e2dc0`.
- Proven:
  the visible payload-adjacent helpers `0x3d0120`, `0x3e55f0`, `0x3e2dc0`, `0x40b330`, `0x40b370`, `0x3e2e90`, and `0x3e3f90` are callable/config/ROI-process surfaces.
- Still unproven:
  the exact `src1` / `src2` N-to-1 reducer body, its full input shape, and its math.

## Consequence For Blocker Work

Future anchor pre-fusion work should not treat these first visible payload runtime surfaces as reducer closure.

The payload runtime surfaces are now bounded as cleanup, callable-slot management, per-level config loading, quantized setting selection, and single-level ROI/process work.

The deeper worker reached from this ROI/process body is separately bounded in `bundle_proof_src1_project_roi_worker.md`.

The parity blocker remains elsewhere and may close only when a different surface is proven to have real N-to-1 input shape or real reduction math.
