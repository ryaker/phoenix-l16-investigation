# Session 4 — DemosaickLight V1 vs V2 selector (closes #23)

**Date:** 2026-04-13
**Method:** Static disassembly only (`/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt`), direct libcp.dylib byte reads, typeinfo/vtable walking. **No spike, no LLDB.**

---

## TL;DR

- The old `demosaic_static.txt` claim that RendererProfile 1 defaults to `"light_v2"` is **correct but incomplete**. It IS the Renderer-level default written by the dispatcher at 0x3cbc10 → 0x3cc897. It is **overridden** later by a per-camera sub-pipeline tuning function at 0x40b370 that writes `"light_v1"` or `"light_v2"` based on an internal `PipelineBase::Demosaicking` 4-value enum (offset 0 of the Pipeline object).
- Runtime observation (V1 fires on L16_02130 28mm) is consistent with static analysis: the per-camera dispatcher at 0x40b370 overwrites the Renderer default with `"light_v1"` because the internal enum is ODD (1 = V1/Bayer or 3 = V1/BayerFloat).
- **Pipeline::setDemosaicking at 0x32d510** reads the final config-map string, resolves it via the 9-case registry, and dispatches via jump table at `0x330710`. Enum 7 → lambda `$_25` (installs DemosaickLightV1). Enum 8 → lambda `$_26` (installs DemosaickLightV2).
- **DemosaickLightV2's scalar arg is a HARDCODED 1.0f** at 0x5a8128, loaded by $_26 forwarder. It is **not** reduced from the Vec3<float> WB gains. q456's best-guess priors for the V2 scalar are disproven.

---

## 1. The two registries

Two separate string→enum maps exist:

### Registry A — Pipeline::setDemosaicking 9-case dispatch (0x3277f5–0x327953)

| String | Enum |
|---|---|
| `collapse2` | 2 |
| `collapse4` | 3 |
| `collapse8` | 4 |
| `malvar`    | 6 |
| `light_v1`  | **7** |
| `light_v2`  | **8** |

Enum 0, 1, 5 are unnamed (fall through to duplicate cases in the 9-way jump table).

### Registry B — 4-value `PipelineBase::Demosaicking` (internal, at Pipeline offset 0)

Inferred from 0x40b1d0 enum→string converter and the 0x40c2a0 dispatch function:

| Enum | Meaning | String written |
|---|---|---|
| 0 | V2 / BayerPipelinePayload | `light_v2` |
| 1 | V1 / BayerPipelinePayload | `light_v1` |
| 2 | V2 / BayerFloatPipelinePayload | `light_v2` |
| 3 | V1 / BayerFloatPipelinePayload | `light_v1` |

**Parity rule:** EVEN → V2, ODD → V1. (Same mapping as the 0x40b1d0 converter in the old analysis.)

---

## 2. Two dispatchers write `demosaicking.type`

### Dispatcher 1 — ApplyTuning at 0x3cbc10 (Renderer-level defaults)

Jump table at 0x3cd290, keyed on `[Pipeline+0xc0]-1`:

| RendererProfile | Case | Branch | Default `demosaicking.type` |
|---|---|---|---|
| 1 (lri_process --profile 0) | 0 | 0x3cc897 | `light_v2` (@0x6330dc) |
| 2 (--profile 1) | 1 | 0x3cc906 | `collapse4` (@0x633773) |
| 3 (--profile 2) | 2 | 0x3cc975 | `collapse8` (@0x63377d) |
| 4 (--profile 3) | 3 | 0x3cc9e1 | `collapse2` (@0x632ca1) |

**Note:** I re-verified these by direct byte reads. The old `demosaic_static.txt` had the profile→case mapping slightly off (swapped collapse variants) but correctly identified `light_v2` as the Profile 1 default.

This dispatcher uses `0x31b560` + `0x31ba20` (`optional.value_or(default)`), i.e. it writes the default only if the key isn't already set.

### Dispatcher 2 — per-camera tuning at 0x40b370 / 0x40c2a0 (THE OVERRIDE)

Function 0x40b370 takes `edx` = stage ID, and when edx==5 (demosaicking stage) falls through to the inline writer at 0x40c2a0. The writer:

```
40c2bb: leaq ... → "demosaicking.type"     ; key
40c2dc: callq 0x31b560                      ; get slot
40c2ef: movl (%r12), %eax                    ; r12 = PipelineBase*, read 4-value enum
40c2fd: jump table @ 0x40ce1c (4 entries)
  enum 0 → 0x40c30d → "light_v2"  (@0x6330dc)
  enum 1 → 0x40c61f → "light_v1"  (@0x6330c1)
  enum 2 → 0x40c30d → "light_v2"
  enum 3 → 0x40c61f → "light_v1"
```

There is a second inline dispatch at 0x40c5dd/0x40ce0c that writes a second key (same V1/V2 parity pattern). Both write unconditionally — they **overwrite** whatever the Renderer dispatcher put there.

Callers: 0x3e2dee/0x3e2e13/0x3e2e38/0x3e2e5d/0x3e783b/0x403837. Only the one at **0x403837 sets edx=5** (the demosaic stage). It's inside function 0x402d20 — a **per-camera sub-pipeline factory** that:
- Calls `0x1be960` (the SAME `isLowLight()` probe used by the tone-mapping dispatcher at 0x3c7860, per `q456_tone_ev_v2param.md`)
- Runs a 5-bucket EV/ISO threshold classifier (0x403016–0x403054)
- Walks a sorted per-camera threshold table (0x4036a0–0x4036c9) and selects one entry

The exact code path that writes 1 (V1/Bayer) into `(%PipelineBase+0)` is inside this classifier. I did NOT fully trace it in this session; **it is very likely driven by the same `isLowLight()` flag that drives the tone-curve selector at 0x3c7860 PLUS an additional per-camera EV/ISO cascade**. UNVERIFIED: exact condition.

---

## 3. `Pipeline::setDemosaicking` dispatch (0x32d510)

Called from one site: `callq 0x32d510` at 0x318897 (inside ApplyTuning consumer at 0x3184d0). The enum comes from a `std::map::find` node load at 0x318891 (`movl 0x38(%rax), %esi`).

Function body at 0x32d510 saves `esi` → `[rbp-0xc64]`, runs several config-map setup blocks, then at 0x32db09–0x32db28 does:

```
mov  ecx, [rbp-0xc64]         ; enum 0..8
cmp  ecx, 0x8
ja   default/error
lea  rcx, [rip+0x2bef]         ; jump table base = 0x330710
movslq (rcx, rax*4), rax
add  rax, rcx
jmp  rax
```

**Jump table at 0x330710 (verified by raw byte read):**

| Enum | JT Target | Installs vtable | Lambda | Registry string |
|---|---|---|---|---|
| 0 | 0x32dd98 | — | (custom/empty path) | — |
| 1 | 0x32db2a | 0x65b948 | `$_25` | — |
| 2 | 0x32dded | 0x65bbb8 | `$_28` | `collapse2` |
| 3 | 0x32de38 | 0x65bc38 | `$_29` | `collapse4` |
| 4 | 0x32de83 | 0x65bcb8 | `$_30` | `collapse8` |
| 5 | 0x32dece | 0x65bd38 | `$_31` | — |
| 6 | 0x32df19 | 0x65bb38 | `$_27` | `malvar` |
| **7** | **0x32db2a** | **0x65b948** | **`$_25`** | **`light_v1`** |
| **8** | **0x32df64** | **0x65bab8** | **`$_26`** | **`light_v2`** |

Cases 1 and 7 share target 0x32db2a — **enum=1 and enum=7 both install lambda `$_25`**. $_25 is therefore the sole "Vec3<float> WB-gains lambda". $_26 is the sole "float scalar lambda".

Lambda typeinfo strings verified via `typeinfo_ptr = *(vtable - 8)` → `name = *(typeinfo+8)`:
- 0x65b948 → `…Pipeline15setDemosaicking…$_25…RKNS2_4Vec3IfEEEEE` (takes Vec3)
- 0x65bab8 → `…Pipeline15setDemosaicking…$_26…RKNS2_4Vec3IfEEEEE` (takes Vec3)
- 0x65bb38 → `…$_27…` (malvar)
- 0x65bbb8..0x65bd38 → `$_28`..`$_31` (collapse2/4/8, unnamed)

---

## 4. Lambda forwarders — the V1/V2 call sites

Vtable slot 3 (offset +0x18) of each `__func<>` object is the `operator()` forwarder. Raw disasm:

### $_25 forwarder at 0x342b80 (installed for enum=1 AND enum=7 = "light_v1"):
```asm
0x342b80: pushq %rbp
0x342b81: movq  %rsp, %rbp
0x342b84: movq  %rsi, %rdi        ; shift args: dst Image<vec4x32f>&
0x342b87: movq  %rdx, %rsi        ; src Image<float> const&
0x342b8a: movq  %rcx, %rdx        ; Vec2<int> const&
0x342b8d: movq  %r8,  %rcx        ; Vec3<float> const& (WB gains — passed through)
0x342b90: popq  %rbp
0x342b91: jmp   0x2eb560           ; → DemosaickLightV1 driver
```

### $_26 forwarder at 0x343180 (installed for enum=8 = "light_v2"):
```asm
0x343180: pushq %rbp
0x343181: movq  %rsp, %rbp
0x343184: movss 0x264f9c(%rip), %xmm0   ; load constant float
                                         ; target = 0x34318c + 0x264f9c = 0x5a8128
                                         ; bytes at 0x5a8128 = 00 00 80 3f = 1.0f
0x34318c: movq  %rsi, %rdi        ; dst
0x34318f: movq  %rdx, %rsi        ; src
0x343192: movq  %rcx, %rdx        ; Vec2<int>
0x343195: popq  %rbp
0x343196: jmp   0x2eba10           ; → DemosaickLightV2 driver
```

**Critical finding for q456:** The `float` arg to DemosaickLightV2 is the **hardcoded constant 1.0f** at 0x5a8128. It is NOT reduced from the Vec3<float> WB gains at all — the Vec3 arg is simply discarded, and `xmm0 = 1.0f` is passed unconditionally. The q456 hypotheses (green-channel gain, mean R+B gain, green-relative chroma) are all disproven. The V2 scalar is a **regularization/quality constant** baked into the binary.

**The driver addresses** `0x2eb560` (V1) and `0x2eba10` (V2) are consistent with session3's runtime finding: session3 vtable-walk resolved V1 operator() bodies at 0x2ed580/0x2eeb20/0x2f0240, which are the phase-variant bodies that 0x2eb560 eventually dispatches to.

---

## 5. Why V1 fires on L16_02130 28mm (static prediction reconciled with runtime)

Chain of events per capture:

1. Renderer constructor writes `RendererProfile=1` at `[Pipeline+0xc0]`.
2. ApplyTuning at 0x3cbc10 reaches case 0x3cc897 → writes `demosaicking.type = "light_v2"` **as default only** into the Pipeline's config map at `[Pipeline+0xe0]`.
3. Per-camera sub-pipeline factory 0x402d20 runs for each camera module. It reads `isLowLight()`, runs an EV/ISO classifier, walks a per-camera threshold table, and (based on a condition I have NOT fully traced) writes the 4-value `PipelineBase::Demosaicking` enum into `(int*)(Pipeline+0x0)`. For L16_02130 28mm (normally exposed AR1335 uint16 Bayer), the written value is **1** (V1/BayerPipelinePayload).
4. Function 0x40b370 at edx=5 reads this enum via 0x40c2ef/0x40c5cf and **overwrites** the config-map `demosaicking.type` slot with `"light_v1"` (via 0x40c634 or 0x40c6f1 — both install the same string).
5. ApplyTuning consumer at 0x3184d0 → 0x318897 reads the final string `"light_v1"`, looks it up in Registry A → enum 7, calls `Pipeline::setDemosaicking(pipeline, 7)`.
6. Jump table at 0x330710 entry 7 → 0x32db2a → installs lambda `$_25` (vtable 0x65b948) into pipeline slot `[pipeline+0x1540]`.
7. At render time, `$_25`'s forwarder at 0x342b80 shifts args and `jmp 0x2eb560` → DemosaickLightV1 family fires.

This chain is consistent with session3 runtime: V1 hit counts 176/636/299 across `<0,0>`/`<1,0>`/`<1,1>` phase variants; zero V2 hits across all four variants.

**V2 would fire only if the per-camera factory wrote enum 0 or 2 (even parity)**, which requires the classifier at 0x402d20 to take a different branch. Since `isLowLight()` presumably returns false for a normal capture, yet V1 still fires, the classifier's V1 choice is **the default for normally-exposed AR1335 BGGR uint16 Bayer captures** — NOT a low-light override. UNVERIFIED: does V2 ever fire on any capture in this 2.3.0 build? Possible that V2 is DEAD CODE in this build, reserved for a future update (analogous to the tone-curve `light_v2` path which q456 found is reachable only via `flag_0x9c != 0` — a flag no code path sets in this build).

---

## 6. Phoenix action

**Phoenix must implement DemosaickLightV1 only** for renderer-profile 0 and normally-exposed AR1335 captures. DemosaickLightV2 is not reached at runtime in the 2.3.0 build under any observed condition.

However, to match the binary's dispatch surface (for parity-testing and future captures):

1. **Short-term (pragmatic):** Implement V1 only. Session 3 runtime proves V1 is the only one that fires. The V1 body takes `(Image<vec4x32f>& dst, Image<float> const& src, Vec2<int> const& phase_offset, Vec3<float> const& wb_gains)` and is templated on `<bayer_x:int, bayer_y:int>` phase pair. Phoenix needs all three BGGR variants: `<0,0>`, `<1,0>`, `<1,1>`. (Session 3 shows `<0,1>` is dormant on L16_02130.)

2. **Medium-term (defensive):** Also implement V2 as a fallback, parameterized with a **hardcoded scalar 1.0** (matching the $_26 forwarder). V2 takes `(Image<vec4x32f>&, Image<float> const&, float=1.0)` — do NOT derive the scalar from WB gains.

3. **Selector:** Phoenix's renderer should expose a `demosaicking.type` string config key with values `"light_v1"` / `"light_v2"` and default it to `"light_v1"` for AR1335 uint16 Bayer. There is no need to implement the full 0x402d20 classifier — a simple rule works: AR1335 uint16 Bayer → V1.

4. **Do NOT implement** `collapse2/4/8` or `malvar` unless Phoenix also supports lri_process `--profile 1/2/3`. These are fast preview paths for the fast-render profiles.

---

## 7. UNVERIFIED

1. **Exact condition inside 0x402d20** that writes enum=1 into the Pipeline's offset 0. The function uses `isLowLight()` + a 5-bucket EV/ISO classifier + a per-camera threshold table walker. Given runtime shows V1 fires regardless, the dominant path appears to always write V1 (at least on this build). LLDB probe: break on 0x40b370, dump `*(int*)rdi` on entry, and log the value across a full L16_02130 render. If all hits show enum=1 regardless of camera, the selector is effectively hardcoded to V1 on AR1335 in this build.
2. **Is V2 reachable at all in 2.3.0?** Session 3 saw 0 V2 hits. Possibly dead code (like `flag_0x9c` for tone mapping). LLDB probe: break on 0x343180 (the $_26 forwarder) across a variety of captures to see if V2 ever fires. If never: V2 is dead in this build.
3. **The PipelineBase::Demosaicking enum field location.** I claimed offset 0 based on `movl (%r12), %eax` inside 0x40b370 with r12 = Pipeline*. Verified by cross-referencing 0x40b1d0 enum→string converter which uses the same 0..3 range. But the exact constructor that writes 0/1/2/3 into offset 0 I did not pin down.
4. **Case 1 of the setDemosaicking jump table** (JT[1]=0x32db2a) is unreachable via Registry A (no string maps to enum 1), but enum 1 is syntactically valid. It may be a placeholder / debug-only entry. Since it shares code with case 7 ("light_v1"), it's safe to treat enum 1 and 7 as synonyms for V1.
5. **V2 driver at 0x2eba10** was not verified to actually invoke DemosaickLightV2 bodies. I inferred this from: (a) $_26 forwarder calls it, (b) $_26 is the only lambda installed for `light_v2` (enum 8), (c) old `demosaic_static.txt` confirmed DemosaickLightV2 typeinfo exists. But I did not trace 0x2eba10 → DemosaickLightV2<X,Y> operator() bodies statically.

---

## 8. Key offsets (updated from demosaic_static.txt)

| Offset | Role |
|---|---|
| 0x32d510 | `Pipeline::setDemosaicking(enum)` function entry |
| 0x330710 | setDemosaicking 9-case jump table |
| 0x342b80 | Lambda `$_25` operator() forwarder (→ V1 at 0x2eb560) |
| 0x343180 | Lambda `$_26` operator() forwarder (→ V2 at 0x2eba10 with scalar=1.0) |
| 0x5a8128 | Hardcoded `float 1.0f` constant used as V2 scalar arg |
| 0x65b948 | Lambda `$_25` __func<> vtable base (leaq target) |
| 0x65bab8 | Lambda `$_26` __func<> vtable base |
| 0x3277f5 | Registry A builder: strings → 9-case enum |
| 0x40b370 | Per-camera tuning function (overrides `demosaicking.type`) |
| 0x40c2a0 | Inline `demosaicking.type` writer branching on 4-value enum |
| 0x40ce1c | First 4-case jump table inside 0x40c2a0 |
| 0x402d20 | Per-camera sub-pipeline factory (calls 0x40b370 with edx=5) |
| 0x3cbc10 | ApplyTuning / Renderer-profile dispatcher (writes default only) |
| 0x3cc897 | Profile 1 branch — writes default `"light_v2"` |
| 0x318897 | Only caller of `Pipeline::setDemosaicking` (reads config → enum → setter) |
| 0x1be960 | `isLowLight()` probe (shared with tone-mapping dispatcher) |

---

## Artifacts

- This document.
- Jump-table entries verified by reading raw bytes of libcp.dylib.
- Vtable typeinfo names extracted from __DATA struct walks.
- V2 scalar constant `1.0f` at 0x5a8128 verified by float32 byte read.
