# Session 2: 10-Camera Bayer Merge Investigation — libcp.dylib Static Analysis

Date: 2026-04-13
Resources used: `/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt` (48 MB), `strings_all.txt`, `nm_all.txt`, `fusion_blend_analysis.txt`, `libcp_isp_symbols.txt`.

All addresses in this document are **file-relative** (same as load-relative with slide=0). Prior analysis used a runtime slide of `0x108c7a000`; subtract that from runtime VAs to match the VAs below.

---

## Headline Finding

**The 10-camera → single-Bayer-strip merge is NOT performed inside libcp.dylib.**

FusionCacheBayer receives its image-vector payload **fully-formed from outside** via a `shared_ptr` handed in through its constructor chain. The shared_ptr's underlying object is constructed by code outside libcp (most likely `libImageAPI.dylib` / LRI-decoder or similar), passed in via `CIAPI::Renderer::Create(CIAPI::RendererProfile)` / `requestRenderROI`, and by the time it reaches libcp it is already a single panoramic Bayer entity (or a length-1 vector containing one).

**Phoenix implication:** libcp.dylib is the ISP pipeline ONLY. It has no multi-camera Bayer-domain compositor. The real "camera merge" stage is upstream — in the LRI-decoder binary or done at LRI bake time.

---

## Chain of Custody for `img_vec` (the Bayer image vector)

### Stage A — PackedBayerFusion reads `+0x118` at runtime
`PackedBayerFusion::process` @ **`0x1aab40`** pulls the pre-merged Bayer image(s) from its own `+0x118` field:

```
0x1aabf0: movq 0x118(%r12), %rdi     ; r12=this; img_vec @ +0x118
0x1aabf8: callq 0x1bdfa0              ; std::vector::data() (identity thunk)
0x1aabfd: movq (%rax), %rdi           ; img_vec[0]
0x1aac00: callq 0xe78e0               ; img_vec[0]->field@+0x28 == camera-count N
```

Observed runtime: **N=1 for 132/132 tiles** (from `fusion_blend_analysis.txt`).

### Stage B — PackedBayerFusion constructor (`0x1a89c0`) receives img_vec via shared_ptr arg
The constructor is called with `(rdi=new_PBF, rsi=&shared_ptr, dl=bool_flag)`:

```
0x1a8a3d: movq (%r12), %rax           ; r12 = second arg (shared_ptr slot); read ptr
0x1a8a41: movq %rax, 0x118(%rbx)      ; ★ PBF.img_vec = *(arg2) ★
0x1a8a48: movq 0x8(%r12), %rdi        ; shared_ptr ctrl block
0x1a8a4d: movq %rdi, 0x120(%rbx)      ; PBF+0x120 = ctrl block
0x1a8a4e: callq 0x556314              ; __shared_weak_count::__add_shared (copy ctor)
0x1a8a86: movq (%r12), %rdi           ; reload
0x1a8a8a: callq 0x1bea00              ; get field@+0x44 via indirection
0x1a8a8f: movl %eax, 0x140(%rbx)      ; PBF+0x140 = camera count
```

PackedBayerFusion is thus a **consumer** of a pre-built shared_ptr<ImageSource>. It allocates nothing for the image data; it just copies the shared_ptr.

There is exactly **one caller** of `0x1a89c0`: the wrapper `0x1aa9a0` (derived class, ColorFusionBayer-like), which installs a second vtable after delegation and copies per-camera scale constants (xmm1, xmm2, ints) to self+0x10/+0x20/+0x30/+0x34.

### Stage C — FusionCacheBayer C2 ctor (`0x4064c0`) passes `%r15 = &(FCB+0x8)` to PBF ctor
FusionCacheBayer's body constructor at **`0x4064c0`** (C1 thunk at `0x406960`):

```
0x4064e8: callq 0x402d20              ; FusionCacheBase::FusionCacheBase (base ctor)
0x4064ed: leaq 0x259bcc(%rip), %rax   ; FusionCacheBayer vtable
0x4064f4: movq %rax, (%r13)           ; this->vtable = FCB-vtable
0x4066f8: leaq 0x8(%r13), %r15        ; r15 = &(this+0x8)
0x40670c: callq 0x556398              ; allocate 0x250 bytes (NeutralColor object)
0x4067a5: movl $0x1a0, %edi
0x4067aa: callq 0x556398              ; allocate 0x1a0 = 416 bytes  (PackedBayerFusion)
0x4067b4: movq %rbx, %rdi             ; new PBF
0x4067b7: movq %r15, %rsi             ; &(FCB+0x8) ← shared_ptr slot
0x4067ba: callq 0x1aab00              ; PBF ctor thunk → 0x1aa9a0 → 0x1a89c0
```

So **`FCB+0x8` is the slot whose shared_ptr gets copied into `PBF+0x118`**.

### Stage D — FusionCacheBase ctor (`0x402d20`) initializes `FCB+0x8` from its rsi arg
```
0x402d4f: leaq 0x26846a(%rip), %rax   ; FusionCacheBase base vtable
0x402d56: movq %rax, (%r13)           ; vtable install
0x402d5a: movq (%rbx), %rax           ; rbx = rsi (shared_ptr arg)
0x402d5d: movq %rax, 0x8(%r13)        ; ★ FCB+0x8 = *(shared_ptr)->raw_ptr
0x402d61: movq 0x8(%rbx), %rdi
0x402d65: movq %rdi, 0x10(%r13)       ; FCB+0x10 = shared_ptr ctrl block
0x402d6e: callq 0x556314              ; __add_shared (refcount inc)
0x402dcb-0x402e64: LOOP iterating *((*shared_ptr)+0..+??) reading pairs of 0x10-byte entries
                    — counts items whose +0x10 lookup returns a bit in +0x4,+0x0 mask (>>31)
0x402e78: movb %al, 0x18(%r13)        ; FCB+0x18 = (count != 0x10) as byte
```

The loop at `0x402dcb-0x402e64` iterates over the vector of sources in the ImageVec, inspecting each entry's tags/flags. The special value `0x10` suggests an enum sentinel (likely `CapturedImage::Camera::kMax` or similar with 16 possible camera slots in L16). It sets a "needs something" byte at FCB+0x18 if any camera entry is non-default. **No pixel writing or compositing happens here** — only metadata inspection.

### Stage E — Only ONE call path constructs FCB: `0x3eab4c → 0x406960`
Searched disasm_full.txt exhaustively:
- `callq 0x406960` appears **once**, at `0x3eab4c`.
- `callq 0x4064c0` appears **zero** times (always through C1 thunk).
- `callq 0x402d20` appears **once**, at `0x4064e8` (from inside C2).

So there is a single construction path, entering from the function at `0x3ea540-0x3eac2c` (not a named symbol; I will call it **"CacheManager::finalize"**).

### Stage F — CacheManager::finalize at `0x3eab4c` allocates FCB and supplies `r14+0x170`
```
0x3eab32: movl $0x138, %edi
0x3eab37: callq 0x556398              ; new FCB (312 bytes)
0x3eab3c: movq %rax, %r13             ; r13 = new FCB
0x3eab3f: movq 0x170(%r14), %rsi      ; ★ rsi = *(parent+0x170) = the shared_ptr to source
0x3eab46: movq %r13, %rdi
0x3eab49: movq %r12, %rdx             ; rdx = RendererProfileConfig
0x3eab4c: callq 0x406960              ; FusionCacheBayer::FusionCacheBayer
```

So `r14+0x170` is the shared_ptr originally owned by the parent cache-manager.

### Stage G — Parent ctor at `0x3ea7d0` initializes `+0x170` from arg `r8` (4th non-this arg)
The parent cache-manager class has its constructor at **`0x3ea7d0`** (C1 thunk at `0x3eaf00`). Signature is `(this=rdi, rsi, rdx, rcx, r8=img-vec-shared-ptr, r9=raw-image-factory-shared-ptr)`:

```
0x3ea7e4: movq %r9, %r15
0x3ea7e7: movq %r8, %rbx              ; save r8 = image-vec source ptr
0x3ea7fe: callq 0x3cfd80              ; base class init
0x3ea83a: movq (%rbx), %rax
0x3ea83d: movq %rax, 0x170(%r14)      ; ★ this+0x170 = *(r8).raw_ptr
0x3ea844: movq 0x8(%rbx), %rdi
0x3ea848: movq %rdi, 0x178(%r14)      ; this+0x178 = ctrl block
0x3ea854: callq 0x556314              ; __add_shared
0x3ea85c: movq (%r15), %rax
0x3ea85f: movq %rax, 0x180(%r14)      ; +0x180 = RawImageFactory ptr
0x3ea867: movq 0x8(%r15), %rdi
0x3ea86a: movq %rdi, 0x188(%r14)
0x3ea873: callq 0x556314
```

**Nothing writes pixel data in this constructor.** It stores the shared_ptr, refcounts it, and proceeds to allocate empty per-camera registries (+0x198, +0x1d8, +0x1f8, ...). The image-vector that ends up at `+0x170` is **already fully populated** by whoever passed it to this constructor.

### Stage H — Only ONE caller of the parent ctor: `0x3b3145`
```
0x3b3073: movq %rax, %r13             ; alloc 128-byte child object
0x3b30a8: leaq 0x2b7069(%rip), %rax
0x3b30af: movq %rax, (%r13)           ; vtable install on 128-byte object
0x3b30b3: movq %r13, %r15
0x3b30b6: addq $0x18, %r15             ; r15 = &(child+0x18) - sub-struct address
0x3b30ba: movq %r15, %rdi
0x3b30bd: movq %r14, %rcx             ; arg: some prior object
0x3b30c0: movq %r12, %r9               ; arg: StereoAsync from parent+0xc8
0x3b30c3: callq 0x3e02d0              ; ← init the sub-struct as an ImageVec

... then vtable install on 0x2b0-byte object at 0x3b30ee-0x3b311f ...

0x3b313b: movq %r13, %r8              ; r8 = &(child+0x18)  [NOT 0x170 — wait]
0x3b313e: movq -0x750(%rbp), %r9      ; r9 = prior_rbx+0x678
0x3b3145: callq 0x3eaf00              ; parent_ctor thunk → 0x3ea7d0
```

**Actually the r8 passed at 0x3b3145 is `%r13` (line 0x3b313b `movq %r13, %r8`) which is `&(allocated 128-byte obj) + 0x18`** — i.e., the sub-struct initialized by `0x3e02d0`. This sub-struct IS what ends up at parent+0x170.

### Stage I — `0x3e02d0` → `0x3dfcc0` initializes the 128-byte wrapper from its own rcx arg
```
0x3dfcc0: FusionSrc::ctor(this=rdi, rsi=Vec2<int>, rdx=shared_ptr, rcx=shared_ptr, r8, r9)
0x3dfcee: movq (%r13), %rax           ; r13 = rcx = another shared_ptr
0x3dfcf2: movq %rax, (%rbx)           ; this+0 = shared_ptr raw
0x3dfcf5: movq 0x8(%r13), %rdi
0x3dfcf9: movq %rdi, 0x8(%rbx)
0x3dfd02: callq 0x556314              ; __add_shared
0x3dfd29: movl (%r15), %eax           ; r15 = rsi = Vec2<int>
0x3dfd2c: movl %eax, 0x48(%rbx)        ; ★ this+0x48 = canvas WIDTH
0x3dfd2f: movl 0x4(%r15), %eax
0x3dfd33: movl %eax, 0x4c(%rbx)        ; ★ this+0x4c = canvas HEIGHT
0x3dfd36: movq (%r14), %rax            ; r14 = rdx = another shared_ptr
0x3dfd39: movq %rax, 0x50(%rbx)        ; this+0x50 = raw from rdx
... refcount inc ...
0x3dfd61: movq -0xe0(%rbp), %rax       ; r9 (5th non-this arg)
0x3dfd68: movq (%rax), %rax
0x3dfd6b: movq %rax, 0x60(%rbx)        ; this+0x60 = raw from r9
```

Then a pyramid-construction loop at `0x3dfdd9-0x3dfe84`: iterates **4 times** halving two int dimensions each pass — this builds a **4-level image pyramid size list** for the canvas. This is the **image pyramid descriptor**, not pixel data.

**Again — no pixel writes.** The function stores shared_ptrs, canvas dimensions, and pyramid levels. Everything else it does is copy shared_ptrs from its arguments.

### Summary of the custody chain

```
<outside libcp.dylib>          # Producer of the panoramic Bayer shared_ptr
  │ passes shared_ptr<ImageGenerator<T>> via RendererProfile / setInputDataStream
  ▼
CIAPI::Renderer::Create @ 0x390540 → lt::RendererPrivate::RendererPrivate
  │ stashes shared_ptr somewhere
  ▼
CacheManager::setup (calls 0x3dfcc0 with rcx=shared_ptr)  ──→ allocates 128B wrapper
  ▼
CacheManager::finalize @ 0x3b3073: stores wrapper at parent_rbx+0x6a8
  │ then calls parent_ctor @ 0x3ea7d0 with r8 = &(rbx+0x6a8)
  ▼
parent_ctor @ 0x3ea7d0: this+0x170 = *(r8)  [shared_ptr copy]
  ▼
CacheManager::finalize @ 0x3eab4c: calls FCB ctor with rsi = r14+0x170
  ▼
FusionCacheBayer::C2 @ 0x4064c0 → FusionCacheBase::ctor @ 0x402d20:
  FCB+0x8 = *(rsi) = the shared_ptr raw ptr
  ▼
FusionCacheBayer::C2 then alloc'ates PBF, calls PBF ctor with rsi = &(FCB+0x8)
  ▼
PackedBayerFusion ctor @ 0x1a89c0:
  PBF+0x118 = *(rsi) = same shared_ptr raw ptr  ← THE img_vec
  ▼
PackedBayerFusion::process @ 0x1aab40 reads PBF+0x118 → img_vec[0] → N field
```

At **every** stage in libcp.dylib, the image-vector is only **copied by shared_ptr**. No stage inside libcp writes pixels into it, allocates its backing store, or iterates over the 10 physical cameras to composite them.

---

## Merge Algorithm — What we KNOW and DON'T know

**KNOW (from fusion_blend_analysis.txt):**
- FusionCacheBayer's vfunc3 sees `N=1` on 132/132 tiles in the L16_02586 production render.
- The `N≥2` blend path exists in the binary (`0x406c7a: jb 0x406e4c`; linear weighted-average formula `sqrt(width*height*exposure)`) but was never triggered.
- FusionCacheBayer receives pre-merged Bayer data.

**KNOW (this investigation):**
- No libcp function writes pixels into `PBF+0x118` / `FCB+0x8`.
- No libcp class with names like "Stitch", "Panorama", "Compose", "Canvas", "Assemble", or "Merge" exists (checked strings table exhaustively — only hits are protobuf and libjpeg-turbo artifacts).
- Every Bayer-domain ISP stage (`ImageCorrectBayerPhaseAR1335`, `RemoveCrossTalkGeneric`, `RemoveVignettingGeneric`, `RestoreHighlightsBayer`, `LinearizeAndColorScaleImageDelegate`) takes a **single** `CapturedImage const&` argument — confirming each stage operates on one image.
- `lt::ImageResolutionAmp` (@ mangled symbol, no bare address — callers take `Image<vec4x32f>&`) is **POST-demosaic** (RGBA, not Bayer) — that's the A1-as-base + B-series super-resolution stage, not the 10-camera Bayer merge.

**DON'T KNOW (static analysis cannot resolve these):**
1. Whether the producer of the shared_ptr is `libImageAPI.dylib`, the Lumen app itself, or an LRI-baked buffer.
2. Whether `img_vec[0]` is truly ONE panoramic Bayer strip, or is a single `ImageGenerator` that lazily fetches per-camera tiles from the LRI on demand (possibility: lazy fetch means the "merge" is hidden inside `ImageGenerator<T>::getTile(rect)` implementations NOT in libcp.dylib).
3. The exact pixel operation that produces the canvas — **because it doesn't live in libcp.dylib at all.**

---

## Merge-Algorithm Hypothesis (best guess, UNVERIFIED)

Given the structural evidence, the most plausible architecture is:

> **The 10-camera panoramic canvas is a *virtual* image lazily evaluated per-tile.**
> `img_vec[0]` is a single `lt::ImageGenerator<uint16_t>` (Bayer) that holds internal state for all 10 cameras (calibration, warp fields, extrinsics). When libcp asks for tile `(x0,y0,x1,y1)` of it via `ImageGenerator::getTile()`, the generator's implementation (in a DIFFERENT binary) runs the per-camera Catmull-Rom project + composite logic and returns a single Bayer tile back.
>
> libcp.dylib sees only the `ImageGenerator` handle and the tile-data it produces. The camera count `N=1` observed inside FusionCacheBayer IS the correct answer — there's only one `ImageGenerator` in the vector — because the 10-camera complexity is hidden behind the `ImageGenerator` interface.

The fact that `fusion_*` config keys live under `tone_adjust.*` (noted in the task context) + FusionCacheBayer's weighting formula `sqrt(w*h*exposure)` also fits this hypothesis: `FusionCacheBayer` is the **HDR-bracket fuser** for multi-exposure brackets captured by the same 16-camera set, not a cross-camera compositor.

---

## Confirmed Call Graph (VAs in file-relative form)

```
CIAPI::Renderer::render @ 0x390180 (exported)
 └─ lt::RendererPrivate::requestRenderROI (hidden — not directly searched here)
     └─ [thread-pool dispatch]
         └─ CacheManager::finalize (unnamed @ 0x3ea540; uses parent+0x170 extensively)
             ├─ 0x3b3073:  alloc 128B FusionSrc wrapper
             │   └─ 0x3b30c3 → 0x3e02d0 → 0x3dfcc0 (FusionSrc::ctor)
             │       ↑ this+0x48/+0x4c = canvas W/H
             │       ↑ this+0x50,+0x60 = shared_ptrs copied from rdx, r9 args
             │       ↑ 4-level pyramid size list built
             ├─ 0x3b3145 → 0x3eaf00 → 0x3ea7d0 (parent_cache_ctor)
             │   ↑ this+0x170 = *(r8) = &(FusionSrc wrapper)
             └─ 0x3eab4c → 0x406960 → 0x4064c0 (FusionCacheBayer::C2)
                 ├─ 0x4064e8 → 0x402d20 (FusionCacheBase::ctor)
                 │   ↑ FCB+0x8 = *(rsi)   ← receives shared_ptr from r14+0x170
                 ├─ 0x40670c: alloc 0x250 NeutralColor object
                 ├─ 0x4067aa: alloc 0x1a0 PackedBayerFusion
                 └─ 0x4067ba → 0x1aab00 → 0x1aa9a0 → 0x1a89c0 (PBF::ctor)
                     ↑ PBF+0x118 = *(&FCB+0x8) = SAME shared_ptr raw ptr
                     ↑ PBF+0x140 = *(img_vec)->+0x44 = camera count field

=== At render time ===

FusionCacheBayer::process (vfunc3) @ 0x406a10
 ├─ 0x406c6a: queries PBF+0x8 → camera count N from img_vec[0]+0x28
 └─ (N=1 path) → 0x1aab40 PackedBayerFusion::process
     ├─ 0x1aabf0: reads img_vec @ PBF+0x118
     ├─ 0x1aabf8: .data()[0]
     ├─ 0x1aac00: img_vec[0]->+0x28 = N (camera count, observed = 1)
     └─ 0x1aad5d: calls 21KB Halide tile kernel @ 0x19c790
```

---

## Phoenix Status & Recommended Next Actions

**libcp.dylib is exonerated** as the location of the 10-camera Bayer merge. Further RE work must target:

1. **libImageAPI.dylib** (or equivalent sibling) — check its export table for `ImageGenerator<uint16_t>` subclasses with per-camera state.
2. **LRI decoder** — verify whether the "panoramic canvas" Bayer strip is:
   - (a) already baked into the LRI file at capture time (so libcp just reads it), or
   - (b) assembled lazily by a generator in libImageAPI at first-tile request, or
   - (c) assembled eagerly at LRI open by libImageAPI before handing the shared_ptr down.
3. **LLDB probe** (if static analysis of libImageAPI is insufficient): set a watchpoint on the 8-byte value at `PBF+0x118` immediately after its constructor returns, then walk the shared_ptr to find the underlying class's RTTI typeinfo. From the typeinfo name you can identify the producing module and its constructor.
4. **Binary diff** the LRI file layout at offset 0 vs a known panoramic Bayer strip size (canvas 10432×7824 × 2 bytes = 163 MB per frame) — if that much data is in the LRI, the merge is baked; if not, it's lazy.

---

## UNVERIFIED items (flagged explicitly)

- [UNVERIFIED] The field at `img_vec[0]+0x28` is camera-count `N`. It may instead be `num_frames`, `num_bracket_exposures`, or `num_images_in_this_shared_ptr_vector`. The prior runtime observation of `N=1` for all 132 tiles is consistent with any of these interpretations.
- [UNVERIFIED] The 128-byte wrapper at `r13+0x18` constructed by `0x3dfcc0` is the actual slot that ends up at `parent+0x170` — I inferred this from the `r8` register flow but did not walk every intermediate save/restore of r13 across the ~700 lines of `CacheManager::finalize`.
- [UNVERIFIED] Exact name of the parent cache-manager class. It has fields at +0x170 (img_vec ptr), +0x180 (RawImageFactory ptr), +0x198 (lock?), +0x1d8 (atomic?), +0x258/+0x268/+0x278 (std::vector triples), +0x6a8 (FusionSrc wrapper ptr), +0x678 (earlier prep object), etc. Best guess: `lt::ImageCaches` or a non-exported `lt::FusionSourceCache`.
- [UNVERIFIED] Whether `ImageResolutionAmp` is called per-tile from within the canvas path. The mangled symbol was found in the string table but I did not look up its body address — it's known from prior analysis to be post-demosaic RGBA so not the Bayer-merge we're looking for.

---

## Answer to the 6 Deliverable Items

1. **Stage/function that performs the 10-camera → single-Bayer-strip merge**: **NOT PRESENT in libcp.dylib.** The merge is performed by a different binary (likely libImageAPI.dylib) and the result enters libcp as a shared_ptr via `CIAPI::Renderer::Create`/`setInputDataStream`.

2. **Call chain from CIAPI::Renderer::render down to the merge**: See "Confirmed Call Graph" above. Inside libcp the chain terminates at `PackedBayerFusion::process` reading `PBF+0x118` — which was populated during construction by a shared_ptr copy from an EXTERNAL producer.

3. **Merge algorithm**: **Cannot be determined from libcp.dylib alone.** Best hypothesis: the 10-camera merge is hidden behind a lazy-evaluated `lt::ImageGenerator<uint16_t>` whose `getTile()` implementation lives outside libcp. The weighted-blend formula inside FusionCacheBayer's N≥2 path (`sqrt(w*h*exposure)`) is for **HDR exposure brackets**, not cross-camera compositing — which explains why `fusion_*` config keys live under `tone_adjust.*`.

4. **Which stage owns `img_vec[0]` population**: **None in libcp.dylib.** The ownership chain inside libcp is: external producer → `CIAPI::Renderer::Create` → `CacheManager` (parent+0x170) → `FusionCacheBayer` (FCB+0x8) → `PackedBayerFusion` (PBF+0x118). Every stage is a shared_ptr copy — NOT an allocation, write, or composition.

5. **UNVERIFIED items**: flagged above in "UNVERIFIED items" section.

6. **Next action if static analysis insufficient**: Use LLDB to walk the shared_ptr at `PBF+0x118` to its RTTI typeinfo. Specifically:
   ```
   b 0x1aab40                          # PackedBayerFusion::process entry
   # run render
   (lldb) memory read --size 8 $r12+0x118  # get img_vec ptr
   (lldb) memory read --size 8 <ptr>        # get vtable
   (lldb) image lookup --address <vtable-8> # RTTI typeinfo
   (lldb) image lookup --name __ZTI<mangled> # class name
   ```
   If the class is in libImageAPI.dylib, disassemble that binary next. If it's in the main Lumen executable, disassemble Lumen's code that calls `CIAPI::Renderer::Create` or `setInputDataStream`.
