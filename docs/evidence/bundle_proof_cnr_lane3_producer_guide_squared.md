# Static + Runtime Proof: CNR source-tile lane 3 == guide^2 (D1 producer)

## Scope

This bundle partially closes the **D1** open item
(`phoenix/tools/parity/verify_cnr_alpha_lane.py`): the producer of the CNR
worker source-tile's vec4 **lane 3** (the per-pixel "alpha"/noise-variance
scale that `CLM-DENOISE-002`'s proven worker formula multiplies through as
`meanA` and `AP[c]`).

It proves, for the Unit-1 70mm profile-3 bridge-HDR render (`L16_03434`):

1. **Transform (CLOSED).** The lane-3 plane is written by `libcp` function
   `0x308f50` as `lane3 = guide^2`, per pixel — static disassembly *and*
   runtime bit-exact capture agree.
2. **Dispatch is always data-driven (CLOSED).** The guide-empty arm of the
   dispatcher `0x307ee0` (which would store the constant `1.0f`) is **never
   taken** on the CNR-worker input path. Across 8 dispatch captures the
   producer (`0x308f50`) arm ran every time. Lane 3 is therefore **not** the
   constant `1.0` that Phoenix's `applyCNR()` currently assumes.
3. **Guide geometry (CLOSED).** The guide is a per-tile buffer with an ~8px
   halo (dst tile + 16 in each dim), a half-resolution plane upsampled by
   pixel-doubling (adjacent columns are byte-identical pairs), values in
   `[0.6, 1.0]`.

Still **OPEN** (does not license a Phoenix port yet): the *semantic source* of
the guide plane — which pipeline quantity `0x34b3f0` copies into its local
guide buffer (`rbp-0x160`). Do NOT hand-tune a substitute; identify it by
measurement (next-step recipe below).

## Static evidence (libcp.dylib, x86-64)

Dispatcher `0x307ee0(rdi=dst_image, rdx=guide_image, r8, rcx, r9d, xmm0, xmm1)`:

```
307f4a: cmpq  $0x0, 0x20(%r14)      ; r14 = rdx = guide; +0x20 = data ptr
307f4f: je    0x307f7d              ; (also empty if dims<=0 via pcmpgtq below)
...
307f8b: movl  $0x3f800000, -0x78(%rbp)   ; EMPTY arm -> lane3 := 1.0f (0x232440)
...
307fac: movq  %r14, -0xb8(%rbp)
307fc1: callq 0x308f50              ; NON-EMPTY arm -> producer
```

Producer `0x308f50`, inner loop (`0x309050`):

```
309054: movss  -0xc(%rax,%rdi,4), %xmm0   ; load guide sample
30905a: mulss  %xmm0, %xmm0               ; square
30905e: movss  %xmm0, (%rdx,%rcx,4)       ; store -> dst lane 3 (base +0xc, stride 0x10)
...      (3 more lanes, dst offsets 0x10/0x20/0x30 -> next pixels' lane 3)
```

Image struct layout (both dst and guide): `+0x10` int32 width, `+0x14` int32
height, `+0x18` int32 stride (float elements/row), `+0x20` ptr float32 data.
Guide is 1 float/pixel.

Guide origin at the call site `0x34b6bb`:
```
34b684: movss 0x15d8(%r14), %xmm0    ; scalar arg (runtime 1.0)
34b68d: movss 0x1624(%r14), %xmm1    ; scalar arg (runtime 1.0)
34b6a0: leaq  -0x160(%rbp), %r13     ; guide = LOCAL stack image struct
34b6b8: movq  %r13, %rdx             ; -> arg2 (guide)
34b6bb: callq 0x307ee0
```
The guide local (`rbp-0x160`) is constructed earlier in `0x34b3f0` by the image
helpers at `0x34b591` (`0xf340`) / `0x34b59d` (`0xf4e0`) from the denoise task
object (`arg2 = rbx`) and the render context (`arg1 = r14`).

The copy source is a **member image of the denoise task** `rbx`, resolved at
`0x34b47d..0x34b55b`:

```
34b47d: movq  0x60(%rbx), %rax    ; guide SOURCE data ptr  (task+0x60)
34b481: testq %rax,%rax / je      ; null -> empty guide (NOT taken this frame)
34b48a: pmovsxdq 0x50(%rbx)       ; guide dims (task+0x50), must be > 0
34b4b9: movdqu   0x40(%rbx)       ; guide bounds rect (task+0x40)
34b4c3: movl 0x20(%rbx)/0x24/0x28/0x2c ; crop rect, intersected with bounds
34b500: movl 0x58(%rbx), %ecx     ; guide stride (task+0x58)
34b503: movq 0x68(%rbx), %r9      ; companion ptr (task+0x68)
34b546: leaq (%rax,%rcx,4), %rax  ; data + (crop.y*stride + crop.x) -> temp -0x170
```

So the guide is exactly the image the **denoise task holds at `+0x60`** (data)
/ `+0x58` (stride) / `+0x50` (dims) / `+0x40` (bounds) / `+0x20..0x2c` (crop) —
confirming the standing D1 lead ("which pointer arg2's task struct holds at
+0x60").

### Task-level capture (runtime, `unit1_70mm_lane3_v2.json`)

Breaking at `0x34b3f0` entry (`rdi = render context`, `rsi = denoise task`)
reads the task guide directly. Three consecutive tasks (same context
`0x7fcb2a808220`):

| task | guide dims | stride | bounds | native mean / range |
|------|-----------|--------|--------|---------------------|
| 1 | 522x522 | 522 | [0,0,522,522] | 0.9985 / [0.998,1.0] |
| 2 | 524x524 | 532 | [-8,-8,524,524] | 0.614 / [0.603,0.619] |
| 3 | 524x524 | 532 | [-8,-8,524,524] | 0.530 / [0.480,0.593] |

Findings that further bound the guide:

- The guide is **per-tile**, not a single full-image plane: each task carries
  its own guide dims (~522-524, i.e. tile + 8px halo) and a **distinct heap
  buffer** (`0x7fcb18240040`, `0x7fcb304d42e0`, `0x7fcb20bac2e0`). So the guide
  is produced per tile inside the fusion loop, not cropped from one image.
- It is nearest-neighbour upsampled from **half resolution**: values repeat in
  identical 2x2 blocks (row0==row1, columns in pairs).
- It **tracks tile brightness**: near 1.0 on the bright tile, ~0.5 on a mid
  tile. It is NOT a per-pixel luma of the CNR source RGB (offline test of
  `lane3` vs the tile's own squared RGB lanes 0-2: corr ~0.4, large residual).
- The CNR route runs **inside the FusionCacheBayer / visible-`src2` chain**:
  full stack `0x34b3f0 <- 0x33f480(vtable+0x30 virtual call at 0x33f94f)
  <- 0x31acf0 <- 0x406a10 <- 0x3ebb80 <- 0x3eca39 <- 0x3d47d0`. `0x406a10 ->
  0x31acf0` is exactly Codex's proven 70mm/150mm src2 branch
  (`lldb_src2_406a10_branch_four_zoom.md`).

### Remaining open link (and a static/runtime caveat)

The runtime denoise task is a **heap object** (`task_rsi` = `0x3045dcca0`,
`0x30465fca0`, `0x3041c4ca0`), reached with return address `0x33f951` inside
`0x33f480`. But the static form of `0x33f480` at that return site passes a
**stack** local (`leaq -0x1e0(%rbp), %rsi` at `0x33f948`) and never writes
`task+0x60`. Those do not reconcile: the static path I read does not correspond
to the runtime heap task (either the disassembled and runtime libcp differ for
this outer function, or the reached target is a thunk/other slot). So the guide
producer is NOT closed by static reading of `0x33f480`, and that stack-local
trace is explicitly NOT asserted here.

Naming the per-tile guide producer is therefore the remaining step, and the
right instrument is a **runtime watchpoint / breakpoint on the heap task's
`+0x60`** (or on the guide buffer's allocation) to catch who writes it — not a
static sweep. What is proven and portable-blocking stands: `lane3 = guide^2`,
guide is data-driven per tile, half-res, brightness-tracking, at
`denoise_task+0x60` in the FusionCacheBayer path.

**Confirmed that Codex has NOT closed this.** The `CLM-DENOISE-002` ledger row
closes the CNR worker formula, the public vector origins, the SVD matrix
helper, and the *separate* `range_scale` image (which has lane 3 = 0, so it is
not this guide). The CNR source-tile lane-3/guide producer is absent from that
closure; D1 is open in Codex's ledger as well.

## Runtime evidence

Probe: `tools/lldb_probes/cnr_lane3_producer/lane3_producer_probe.py`
Driver: `tools/lldb_probes/cnr_lane3_producer/unit1_70mm_lane3.lldb`
Report: `runs/cnr_lane3_producer/unit1_70mm_lane3.json`

- 8/8 dispatches took the producer arm (`guide_empty_arm=false`).
- Guide tiles: `532x520`, `522x522`, `532x532`, `520x532` (dst `516x512`,
  `514x514`, `516x516`, `512x516`) — tile + 16px halo.
- Guide row0 samples arrive in identical pairs, e.g.
  `0.87945, 0.87945, 0.88167, 0.88167, 0.88388, 0.88388, ...` (half-res
  pixel-doubling). Per-tile guide means span `0.680 .. 0.999`; floors `0.60 ..
  0.88`.
- Square confirmed bit-for-bit at `0x30905e`: `xmm0` (value about to store) =
  `0.773438, 0.777344, 0.781250, ...` whose square roots
  `0.879453, 0.881671, 0.883883, ...` equal the guide row0 samples exactly.
- Scalar dispatch args `xmm0=xmm1=1.0` (identity gains this frame).

Consistency with the prior D1 clue: the earlier captured alpha (lane-3) tile
floor `0.30859375 = 79/256` implies a guide floor `sqrt(0.30859) = 0.5556`;
this frame's brighter tiles give higher guide floors (`0.60..0.88`), same
`guide^2` law. `meanA` range over the D1 corpus `[0.3023, 1.9325]` is the range
of `mean(guide^2)` across tiles/zooms — consistent with a data-driven guide, not
a constant.

## RTTI naming of the producing stage (runtime, `unit1_70mm_lane3_v4.json`)

Resolving `0x34b3f0`'s `rdi` (arg1, the "context" object) through the Itanium
C++ ABI (`obj -> vtable -> typeinfo -> name`) names the producer's owning
scope. Bit-exact demangled type of `rdi`:

```
std::__1::__function::__func<
    lt::Internal::Pipeline::setWhiteBalance(lt::Internal::PipelineBase::AWB)::$_22,
    ...,
    void (lt::SoftISP::Stats&,
          lt::Image<unsigned short> const&,
          lt::CapturedImage const&,
          lt::Rectangle<int> const&)>
```

So the CNR body `0x34b3f0` (and thus the lane-3 `guide^2` production) runs
**inside `lt::Internal::Pipeline::setWhiteBalance`'s per-tile lambda `$_22`**,
whose call signature is
`void(SoftISP::Stats&, Image<unsigned short> const&, CapturedImage const&, Rectangle<int> const&)`.
This is a NAMED public pipeline stage. It is coherent with the CNR data space:
the CNR input is squared *AWB'd* RGB (`p_c = s_c^2`), and this is the AWB
(setWhiteBalance) stage itself, walking a 16-bit `Image` tile-by-tile (the
`Rectangle`) with the `CapturedImage` and a `SoftISP::Stats` accumulator.

The task's own `+0x00/+0x08` object pointers did not resolve to RTTI names
(raw buffers / non-polymorphic), so the naming anchor is the enclosing
`setWhiteBalance $_22` lambda, not the task struct.

Consequence for the port: the guide is no longer an anonymous fusion buffer —
it is a working image inside the named setWhiteBalance/AWB stage, over inputs
(`Image<unsigned short>`, `CapturedImage`, AWB `Stats`) that **Phoenix also
has**. The guide's half-res, smooth, brightness-tracking `[0.48,1.0]` profile
is consistent with a normalized/downsampled version of that 16-bit image (or a
`Stats`-derived map).

## What this licenses / forbids

- LICENSED: recording that Phoenix's `applyCNR()` assumption "lane 3 is
  IRAMP-forced to 1.0, so meanA:=1" is **disproven** for the CNR-worker path;
  and that the producing stage is `lt::Internal::Pipeline::setWhiteBalance`'s
  `$_22` lambda over `Image<unsigned short>` + `CapturedImage` + AWB `Stats`.
- FORBIDDEN (still): porting a lane-3 plane into Phoenix. `guide^2` and the
  producing stage are proven, but WHICH of the three lambda inputs the guide
  derives from, and its exact normalization to `[~0.48,1.0]`, is not yet
  proven. Coding `lane3 = (somePhoenixPlane)^2` before that is settled would be
  the hand-tuned substitute the D1 verifier warns against.

## Next-step recipe (name the exact guide input)

Instrument the `setWhiteBalance $_22` lambda body: at `0x34b3f0` the three
inputs are reachable (Image<u16>, CapturedImage, Rectangle passed to the
lambda's `operator()` up-stack). Capture each input's dims/data at the tile,
and match the half-res guide (`task+0x60`) to a downsample of one of them by
content (`first_row_sha256` / value correlation). Confirm the normalization
that maps 16-bit image values into the guide's `[~0.48,1.0]`. Extend to
four-zoom + two-body for Codex-grade closure. NOT a static sweep (the outer
functions' static form does not match this runtime).
