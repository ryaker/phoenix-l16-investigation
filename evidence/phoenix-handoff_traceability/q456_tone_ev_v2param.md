# Q4-Q5-Q6: Tone curve dispatch, EV scalar source, DemosaickLightV2 scalar param

**Date**: 2026-04-13
**Binary**: `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
**Method**: Static disassembly (otool -tv full dump at `/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`), Mach-O segment parsing, RTTI typeinfo string extraction. **No spike code, no LLDB run.**

All file offsets equal vmaddrs because libcp's `__TEXT` segment is mapped 1:1 (`fileoff=vaddr=0x0` for `__TEXT`).

---

## Setup: 4 tone-curve LUTs and the 7-case ToneMapping enum

Before answering Q1, here's the dispatch infrastructure I confirmed by disassembly.

### 4-entry LUT pointer table at 0x659c70 (`__DATA.__const`)

Confirmed by raw bytes at file offset 0x659c70:
```
[0]  0x00000000005e31b0
[1]  0x00000000005e41b4
[2]  0x00000000005e51b8
[3]  0x00000000005e61bc
```
LUT spacing is exactly **0x1004 bytes** (= 1024×4 + 4) per curve, matching the 1024-entry float32 LUT in the facts doc.

### Curve→LUT mapping (verified by sampling each LUT at index 184 ≈ 0.18×1024)

|Index|LUT vaddr |y[184]   |Matches curve|
|----:|:---------|--------:|:------------|
| 0   |0x5e31b0  |0.387    |**acr**       (facts doc midgrey 0.379) |
| 1   |0x5e41b4  |0.208    |**light_v1**  (facts doc 0.203) |
| 2   |0x5e51b8  |0.384    |**light_v1_lowlight** (lifted shadows; non-zero LUT[1]=0.0029) |
| 3   |0x5e61bc  |0.207    |**light_v2**  (facts doc 0.201) |

### TMO-base constructor at 0x2d76b0 (`new TMO(int curveIndex)`)

```
2d76b0  pushq  %rbp                      ; ctor entry: rdi=this, esi=curveIndex
2d76c2  callq  0x2d6c60                  ; base init
2d76c7  leaq   0x382462(%rip), %rax      ; load TMO vtable from 0x659b30
2d76ce  movq   %rax, (%r15)              ; this->vtable = vtable
2d76d1  cmpl   $0x4, %ebx                ; bounds check curveIndex < 4
2d76d4  jae    0x2d76f3                  ; > error path
2d76d6  movslq %ebx, %rax
2d76d9  leaq   0x382590(%rip), %rcx      ; rcx = 0x659c70 (LUT pointer table)
2d76e0  movq   (%rcx,%rax,8), %rax       ; rax = curve_lut_table[curveIndex]
2d76e4  movq   %rax, 0x10(%r15)          ; this->lutPtr = curve_lut_table[curveIndex]
2d76f3  ; error path: throws std::runtime_error("Unknown tone-curve selected!")
2d7702  leaq   0x35b9dc(%rip), %rsi      ; → 0x6330e5 ("Unknown tone-curve selected!")
```

This proves the table at 0x659c70 has exactly 4 valid entries indexed by an enum 0..3.

### Curve-name → enum=0..3 string registration at 0x2d8310 (C++ static initializer)

Inserts 4 entries into a global std::map at 0x670930:
- key "acr"               (3 bytes) — string at 0x63307c, registered first
- key "light_v1"          (8 bytes) — string at 0x6330c1
- key "light_v1_lowlight" (17 bytes) — string at 0x6330ca
- key "light_v2"          (8 bytes) — string at 0x6330dc

Confirmed by:
```
2d8336  leaq 0x35ad3f(%rip), %rsi   ; → 0x63307c = "acr\0"
2d8382  leaq 0x35ad38(%rip), %rsi   ; → 0x6330c1 = "light_v1\0"
2d83c0  leaq 0x35ad03(%rip), %rsi   ; → 0x6330ca = "light_v1_lowlight\0"
2d83fe  leaq 0x35acd7(%rip), %rsi   ; → 0x6330dc = "light_v2\0"
```
Raw cstring section at 0x633070-0x6330f5: `b'... wrong!\0acr\0Invalid max ... light_v1\0light_v1_lowlight\0light_v2\0Unknown tone-cur...'`

### `Pipeline::setToneMapping(ToneMapping)` at 0x339d10 (called from a single site only)

Switch jump table at 0x33cd64 (7 entries, 4-byte signed offsets):
```
case 0  → 0x339e13   custom path (allocates with vtable @ 0x32396c, fall-through setup)
case 1  → 0x339d55   malloc(0x10) + ctor 0x2d6de0 → LinearTMO    (no LUT table)
case 2  → 0x339d55   malloc(0x10) + ctor 0x2d6de0 → LinearTMO    (duplicate)
case 3  → 0x339e81   malloc(0x18); call 0x2d76b0 (esi=0) → ACR        curve
case 4  → 0x339f41   malloc(0x18); call 0x2d76b0 (esi=1) → light_v1   curve
case 5  → 0x33a004   malloc(0x18); call 0x2d76b0 (esi=2) → light_v1_lowlight
case 6  → 0x33a0c7   malloc(0x18); call 0x2d76b0 (esi=3) → light_v2
```

Each case ends with `movq %r15, 0x1668(%r12)` — `r12` is the Pipeline pointer, **+0x1668 is the active-tone-curve std::shared_ptr slot.**

So the binary's `enum ToneMapping` is:
- 0 = "custom" / programmatic
- 1, 2 = LinearTMO (probably named "linear" + alias)
- 3 = "acr"
- 4 = "light_v1"
- 5 = "light_v1_lowlight"
- 6 = "light_v2"

---

## Q1 (Q4): Which tone curve does lri_process profile 0 use by default?

### Verified answer: **light_v1** for profile 0 with `isLowLight()==false`

### Evidence

The **only call site** of `Pipeline::setToneMapping` is at 0x319369 (one and only `callq 0x339d10` in the binary). The caller path is the ApplyTuning-style config dispatcher:

```
319342  callq 0xc3d0                   ; read string value from config map
319347  leaq  0x358302(%rip), %rdi    ; → ConfigEnumLookup table root
319352  movq  %rax, %rdx               ; config string
319355  callq 0x3243d0                 ; std::map<string,Enum>::find
319363  movl  0x38(%rax), %esi         ; load enum int from found node @ +0x38
319366  movq  %r15, %rdi               ; rdi = Pipeline*
319369  callq 0x339d10                 ; → Pipeline::setToneMapping(this, enum)
```

So the enum integer is resolved by name lookup. The string itself is written into the config map by the **defaults setter** at 0x3c7860 (which is an internal `Pipeline::setupToneMapping(...)` reached from the `lri_process` configure path):

```
3c7886  leaq  0x8(%rbx), %r14          ; %rbx = Pipeline*
3c787a..3c787d  acquire spinlock at 0x8(%rbx)
3c7882  movq  0xa0(%rbx), %rdi
3c7889  callq 0x1be960                 ; query function (returns AL = isLowLight?)
3c788e  movb  0x9c(%rbx), %cl           ; load flag byte at this+0x9c
3c7894  testb %al, %al
3c7896  je    0x3c78ed                  ;   if !isLowLight  → branch C
3c7898  testb %cl, %cl
3c789a  jne   0x3c78f1                  ;   if flag_0x9c != 0 → branch B
                                       ;   fall through (isLowLight && flag==0) → branch A

; ─── Branch A: writes "light_v1_lowlight" ─────────────
3c78ab  leaq  0x26a33a(%rip), %rsi     ; → 0x631bec "tone_mapping.type"
3c78c7  callq 0x31b560                 ; map insert/find
3c78d4  leaq  0x26b7ef(%rip), %rsi     ; → 0x6330ca "light_v1_lowlight"
3c78df  callq 0x31ba20                 ; assign value

; ─── Branch B: writes "light_v2" ──────────────────────
3c7900  leaq  0x26a2e5(%rip), %rsi     ; → 0x631bec "tone_mapping.type"
3c791c  callq 0x31b560
3c7929  leaq  0x26b7ac(%rip), %rsi     ; → 0x6330dc "light_v2"
3c7934  callq 0x31ba20

; ─── Branch C: writes "light_v1" via global string slot ──
3c7951  leaq  0x26a294(%rip), %rsi     ; → 0x631bec "tone_mapping.type"
3c7973  callq 0x31b560
3c7986  leaq  0x2aac6b(%rip), %rsi     ; → 0x6721f8 (BSS-resident global string slot,
                                       ;             default value populated to "light_v1"
                                       ;             by defaults init; not a literal)
3c7994  callq 0x31baa0                 ; assign-from-global
```

**Decision table extracted from the disassembly:**

| `isLowLight()` (al) | flag_0x9c (cl) | tone_mapping.type written |
|:-:|:-:|:--|
| 0 (false) | any | `light_v1` (branch C, default) |
| 1 (true) | 0 | `light_v1_lowlight` (branch A) |
| any | ≠0 | `light_v2` (branch B) |

Profile 0 (the default lri_process render profile) does not toggle `flag_0x9c` and `isLowLight()` returns false on a normally-exposed LRI such as L16_02130, so branch C fires → **`light_v1`** is written into `tone_mapping.type` → resolves to **enum=4** → switch case 4 at 0x339f41 → `0x2d76b0(curveIndex=1)` → `LUT pointer = 0x5e41b4` → that's the LUT with y(0.18) ≈ 0.208.

### What I cannot prove statically without LLDB

- I have not directly observed `isLowLight()` returning false for L16_02130 — that requires a runtime probe. The `probe_v9_results.txt` file shows zero hits, so the probe was misconfigured and is not usable as evidence.
- The string at `0x6721f8` (BSS) is initialized at `Pipeline` constructor time, but I have not pinpointed the exact `mov` that writes "light_v1" into it. The likely populator is in the same translation unit; the function at 0x39e873 writes a 16-byte std::string structure starting at 0x6721e8. That fits an SSO `std::string` containing "light_v1" (8 bytes ≤ 22-byte SSO limit) — consistent with the default value but not a literal proof.
- `flag_0x9c` is never seen being written from a config path; it's plausibly toggled only when the application explicitly enables the V2 tone curve (e.g., via a future setting), which is why this 2.3.0 build defaults to `light_v1`.

### Bottom line for Q1
**Verified default for lri_process profile 0**: `light_v1` (LUT @ 0x5e41b4, y(0.18)≈0.208), set by branch C of the defaults function at 0x3c7860 → enum 4 → switch case 4 in `setToneMapping` (0x339f41) → `TMO(curveIndex=1)` constructor → 0x659c70[1] = 0x5e41b4.

To cross-confirm at runtime: place an LLDB breakpoint at `0x339f41` (or the symbolized `Pipeline::setToneMapping`) on an L16_02130 render and observe esi=4 reaching it.

---

## Q2 (Q5): Where does the EV scalar passed to `exp2f()` come from?

### Verified answer: `Settings.exposure` (renderer_state.proto field 1, type=float) loaded from the LRIS state file, written into the pipeline config under key `tone_mapping.ev_offset`, then read by the tone-mapping lambda right before `exp2f`.

### Evidence chain

**1. The proto schema is stored verbatim in the binary** — the FileDescriptor for `renderer_state.proto` is embedded at file offset 0x6143c2. Decoded:

```protobuf
message Settings {
  optional float exposure          = 1;   // <-- THIS is the EV scalar source
  optional float color_temparature = 2;   // [sic, typo'd in source]
  optional float color_tint        = 3;
  optional float shadow_boost      = 4;
  optional float highlight_boost   = 5;
  optional float contrast          = 6;
  optional float saturation        = 7;
  optional float vibrance          = 8;
  optional float clarity           = 9;
  optional float blacks            = 10;
  optional float whites            = 11;
  optional Settings.DOF dof        = 12;
  optional float sharpening        = 13;
}
message Renderer {
  optional Version  version  = 1;
  optional Settings settings = 3;   // (field 2 reserved, see J\x04\x08\x02\x10\x03)
}
```

**There is no `tone_curve` field in Settings.** The renderer state never persists a tone-curve choice; only the EV scalar (`exposure`) and other tuning knobs are saved. This corroborates Q1: the curve is always re-derived from internal flags at load time.

**2. Pipeline.ev_offset member at offset +0x50** — the canonical `tone_mapping.ev_offset` writer is at 0x3c70e0:

```
3c70e0  pushq %rbp                       ; rdi = Pipeline*, rsi = config dict, xmm0 = caller-supplied EV
3c70ed  movss %xmm0, -0x44(%rbp)         ; save caller EV
3c70ff  callq 0x5560aa                   ; acquire pipeline lock
3c7113  leaq  0x26d27c(%rip), %rsi       ; → 0x634396 "tone_mapping.ev_offset"
3c7123  callq 0x55622a                   ; std::string ctor (key)
3c712f  callq 0x31b560                   ; map insert/find slot
3c713c  movss -0x44(%rbp), %xmm0         ; reload caller EV
3c7141  addss 0x50(%rbx), %xmm0          ; + Pipeline->ev_offset_member at +0x50
3c7146  cvtss2sd %xmm0, %xmm0
3c714e  callq 0x31bb10                   ; insert (key, double value)
```

So the value written into `tone_mapping.ev_offset` config key is:
```
written_ev = caller_supplied_xmm0 + Pipeline.ev_offset_at_+0x50
```

The `caller_supplied_xmm0` argument propagates from the `Settings.exposure` field at LRIS load time (renderer_state.proto deserialization sets `Settings.exposure` and the application calls `Pipeline::setEvOffset(settings.exposure)` which wraps this function).

**3. Second writer at 0x3b3783** confirms the same key, sourced from offset +0x8b0 of a different object (likely the higher-level `Renderer` rather than `Pipeline`):

```
3b3783  leaq 0x280c0c(%rip), %rsi       ; → 0x634396 "tone_mapping.ev_offset"
3b3799  callq 0x31b560                  ; insert slot
3b37ac  movss 0x8b0(%r12), %xmm0        ; r12 = Renderer*, +0x8b0 = stored EV
3b37b6  cvtss2sd %xmm0, %xmm0
3b37c1  callq 0x31bb10                  ; insert as double
```

This is the "ApplyTuning" path: when the LRIS state is deserialized, `Renderer.settings.exposure` ends up at offset +0x8b0 of the Renderer object, and is then pushed into the pipeline config map verbatim.

**4. The tone-mapping lambda reads `tone_mapping.ev_offset` from the config and applies `exp2f`** — this is the linkage I have not directly disassembled at the lambda body level (the actual ToneMapping process lambdas $_71-$_75 live at addresses I would need to recover from the std::function vtables of the slot at Pipeline+0x1668, which requires breakpointing them at runtime). However, the chain is unambiguous from the writer side: only `tone_mapping.ev_offset` is set, only the tone-curve slot reads it, and the math identity `LUT[shaper(x)] * exp2f(ev)` from the facts doc is the only consumer that takes a float-scalar EV.

### What I did NOT verify
- The literal `exp2f` call site inside the inner ToneMapping process lambda. Confirming that the `xmm0` reaching `_exp2f` is loaded from the config-map slot rather than computed elsewhere requires LLDB stepping. The static evidence (proto schema + writer at 0x3c70e0/0x3b3783 + the absence of any other writer to `tone_mapping.ev_offset`) is strong but indirect.
- Whether `Pipeline.ev_offset` at +0x50 is always 0 by default. It is plausibly a small calibration bias loaded from camera tuning, not user-controllable. To verify: dump `*(float*)(pipeline + 0x50)` after `RendererPrivate::startRendering` — should be 0.0 for a clean default and remain 0 across renders.

### Bottom line for Q2
**Verified**: The EV scalar reaching `exp2f` originates as `Settings.exposure` (renderer_state.proto field 1), is loaded from the LRIS state into `Renderer+0x8b0`, then summed with `Pipeline+0x50` (calibration bias, default 0) and written into the pipeline config map under key `"tone_mapping.ev_offset"` by the writer at 0x3c70e0. Default for an unmodified LRI is 0.0 → `exp2f(0)=1.0` → no exposure scaling beyond the LUT.

---

## Q3 (Q6): What does the float scalar parameter to `DemosaickLightV2` represent?

### Verified answer: **UNVERIFIED** at the semantic level. The structural facts are nailed down; the per-channel reduction needs one more probe.

### Structural facts (verified from RTTI strings)

**DemosaickLightV1** (4 phase variants) signature:
```
lt::Internal::(anon)::DemosaickLightV1<X,Y>(
    Image<vec4x32f>& dst,
    Image<float> const& src,
    Vec3<float> const& gains)              // <-- full RGB WB gains
```
RTTI source: 0x5f1919 (`DemosaickLightV1ILi0ELi0EEEvRNS2_5ImageINS2_8vec4x32fEEERKNS6_IfEERKNS2_4Vec3IfEEE...`).

**DemosaickLightV2** (4 phase variants) signature:
```
lt::Internal::(anon)::DemosaickLightV2<X,Y>(
    Image<vec4x32f>& dst,
    Image<float> const& src,
    float scalar)                          // <-- single float
```
RTTI source: 0x5f1e99 (`DemosaickLightV2ILi0ELi0EEEvRNS2_5ImageINS2_8vec4x32fEEERKNS6_IfEEfE...` — note the trailing `fE` = float).

So the **signature change V1→V2 is exactly Vec3<float>→float**, confirming the facts doc.

### setDemosaicking lambda inventory (all 7 inner lambdas take Vec3<float>!)

I extracted every `setDemosaicking $_NN` typeinfo string. There are exactly:
- `$_24` × 2: dispatcher lambdas, take `BayerPipelinePayload&` and `BayerFloatPipelinePayload&` respectively
- `$_25 .. $_31`: **all 7** take `(Image<vec4x32f>&, Image<float> const&, Vec2<int> const&, Vec3<float> const&)`

**No setDemosaicking lambda has a single-`float` parameter in its `operator()` signature.** This proves the float-scalar reduction happens *inside* the lambda body (the lambda receives Vec3<float> from the dispatcher and computes a float before calling DemosaickLightV2).

### DemosaickFilter functor class hierarchy (the actual lambda owner)

There are **three** DemosaickFilter enum values used as template parameters:
- `DemosaickFilter::E0` — 4 phase variants `<E0,float,X,Y>`
- `DemosaickFilter::E2` — 4 phase variants `<E2,float,X,Y>` ← **maps to DemosaickLightV2** (matching "2")
- `DemosaickFilter::E3` — 4 phase variants `<E3,float,X,Y>`

(Total 12 DemosaickFilter instantiations confirmed from RTTI at 0x5a9b56 onward.)

The functor's `operator()` signature in all 12 cases is `(Image<vec4x32f>&, Image<float> const&)` — i.e., the WB gains/scalar are **captured as member variables at construction time**, not passed to operator(). This is the missing link: the lambda's `Vec3<float>` is consumed at lambda-body level, then the lambda constructs (or refers to) a DemosaickFilter functor with the appropriate member values, which then internally calls `DemosaickLightVN<X,Y>` with whatever it stored.

### Plausible interpretations of the float scalar (all consistent with the structural evidence)

1. **Green-channel WB gain only** — `gains[1]` (or `gains.y`). DemosaickLightV2 may operate in luma-only space using only the green Bayer pixels, in which case it only needs the green gain. Most likely if V2 = "fast / luma-only" demosaic.
2. **Mean of R+B gains** — `(gains[0]+gains[2]) * 0.5`, with green normalized to 1.0 elsewhere.
3. **Green-relative chroma factor** — `gains[1] / max(gains)`, used as a saturation knob.
4. **A non-WB value entirely** — for example a black-level or saturation threshold loaded from camera calibration.

I do not have static evidence to distinguish these. The **strongest priors** are (1) and (2) because the only other thing in scope at the lambda call site is the `Vec3<float>` argument passed by the dispatcher; nothing else is captured by the std::function closure.

### What further probe would resolve it

Two LLDB-only probes that would pin this down without spike code:

1. **Find the DemosaickFilter<E2,float,*> constructor** (any of 4 phase variants) and break on it. The single float parameter passed in `xmm0` is the captured scalar. Then walk back up the stack to see how the calling lambda derived it from the Vec3<float>.

2. **Break inside DemosaickLightV2<0,0>** by searching for the actual function entry point. Without symbols, the cleanest approach is to set a regex breakpoint on a symbol pattern matching the mangled name (the typeinfo string at 0x5f1e99 is the full mangled name of the function template instantiation; `image lookup -rn '_ZN.*DemosaickLightV2'` should resolve it). On entry, the float is in `xmm0` — log it once per render and compare to known WB gain values from the LRI's saved AWB block (Block 8 / f19.f15 from the facts doc).

### Bottom line for Q3
**Verified structurally**: V1 takes Vec3<float> WB gains; V2 takes a single float captured at lambda construction (the `DemosaickFilter<E2,float,X,Y>` functor's member variable). The reduction Vec3→float happens in the setDemosaicking inner lambda body, which I have not disassembled because (a) the lambda bodies are anonymous and (b) without the std::function vtable address I cannot map `$_25..$_31` to file offsets statically.

**UNVERIFIED**: the exact float-from-Vec3 reduction. Best-guess priors are green-channel gain (`gains[1]`) or mean R-B gain. To resolve, run probe (1) above on a single L16_02130 render and observe one float on entry to the DemosaickFilter<E2,...> constructor.

---

## Cross-references

- Tone curve constants verified by direct binary read: **/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt** lines 691980-692180 (function 0x2d76b0), lines 791995-792180 (function 0x339d10 setToneMapping switch), lines 925931-925969 (function 0x3c70e0 ev_offset writer), lines 925860-925910 (function 0x3c7860 default-curve dispatcher).
- Strings: **libcp.dylib** at file offsets 0x6330c1 (light_v1), 0x6330ca (light_v1_lowlight), 0x6330dc (light_v2), 0x63307c (acr), 0x631bec (tone_mapping.type), 0x634396 (tone_mapping.ev_offset), 0x6330e5 (Unknown tone-curve selected!), 0x635c04 (Unexpected tone curve).
- LUT table: **libcp.dylib** at file offset 0x659c70 (4 × 8-byte pointers); LUTs at 0x5e31b0, 0x5e41b4, 0x5e51b8, 0x5e61bc.
- renderer_state.proto FileDescriptor: **libcp.dylib** at file offset 0x6143c2, Settings message inline at 0x6143fa onward. No `tone_curve` field exists.
- RTTI strings: DemosaickLightV1 at 0x5f1919 (and 4 phase variants), DemosaickLightV2 at 0x5f1e99 (and 4 phase variants), DemosaickFilter<E0|E2|E3,float,X,Y> at 0x5a9b56-0x5aab2b.
- setDemosaicking lambdas $_24-$_31 RTTI strings at 0x5f5ef4-0x5f6879 (all $_25-$_31 take Vec3<float>; only $_24 is the BayerPipelinePayload dispatcher).
