# Runtime/Static Evidence: ColorFusionBayer `f`, camera selection, and profile-3 CNR guide

**Date:** 2026-08-11  
**Binary:** installed `libcp.dylib`, SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Runtime inputs:** Unit-1 `28mm` `2018-07-23/L16_02130.lri` and exact-focal
Unit-2 `70mm` `2018-10-25/L16_02894.lri`, profile 3  
**Claim:** `CLM-DENOISE-002` formula/producer/selection addendum

## Research gate

`tools/whatknown.sh` reported the already named addresses/classes as
`DOCUMENTED`, so those results were read and joined rather than rediscovered.
The residual topics `ColorFusion f runtime validation`, `ColorFusionBayer
camera selection`, and `ColorFusionBayer source cameras` returned `NO HITS`.
This bundle addresses those residuals.

## Runtime capture

The reusable harness
`tools/lldb_probes/colorfusion_f_runtime/run_u1_28_stepout.sh` stops at the
function boundary `0x18eb00`. It selects one worker thread, disables the hot
breakpoint while synchronously stepping out, and repeats for the three source
modules of one patch. This avoids another worker stealing the return stop.
Raw float32 operands and results are retained under ignored
`runs/colorfusion_f_runtime/u1_28/`; the durable verifier is
`tools/verifiers/verify_colorfusion_f_runtime.py`.

The captured patch is `[760,504,776,520]`. The source ROIs are respectively
`[838,569,854,585]`, `[771,542,787,558]`, and `[753,521,769,537]`.
The reference transformed-patch bytes are identical for all three calls
(`0cf09c0e...`), while all source hashes differ (`cdb2f217...`,
`53c580a3...`, `0026c41b...`). The reference descriptor
`0x7f867484c9c0` is outside the three-entry source-descriptor vector. Thus the
reference is a separately constructed fixed operand; it is not `source[0]`.

All three calls use the same 256-by-vec4 coefficient block, SHA-256
`1fda8d853dfeb730a34132d1f3559e4d653189639ac75afaa93843b06ca4d5ad`.
Each coefficient is broadcast to four equal lanes and the lane-0 table has
range `[0.5624998807907104,8.650075912475586]` and sum
`360.2383522987366`, matching the installed `0x5d0070` table. The live noise
vector is:

```text
[199.56065368652344, 337.18255615234375,
 193.4521484375, 346.5521545410156]
bits [43478f87, 43a8975e, 434173c0, 43ad46ad]
```

## Exact per-module formula

For each of the 256 transformed coefficients `c` and Bayer lane `j`:

```text
d[c,j]      = f32(reference[c,j] - source[c,j])
d2[c,j]     = f32(d[c,j] * d[c,j])
lambda[c,j] = f32(F[c] * noise[j])
w[c,j]      = f32(rcpps(f32(d2[c,j] + lambda[c,j])) * d2[c,j])
q[c]        = x86_max(x86_max(w[c,0],w[c,2]),
                      x86_max(w[c,1],w[c,3]))
m            = f32(sum_c f32(1.0f - q[c]) in ascending c order)
m            = f32(m * (1.0f/256.0f))
```

`x86_max` means installed `MAXPS/MAXSS` source-on-tie/NaN semantics, not
`std::max`. The scalar `q[c]` is broadcast to all four lanes for both the
coefficient blend and the retention accumulator. This corrects the earlier
static prose that treated four lanes as four independent retention lanes.
Every Bayer lane wins the max on the live patch:

| module | max-lane census | captured/replayed `m` |
|---:|---|---|
| 0 | `[56,76,63,61]` | `0.753570437 / 0x3f40e9fe` |
| 1 | `[63,77,63,53]` | `0.845361352 / 0x3f58699a` |
| 2 | `[56,76,61,63]` | `0.819982529 / 0x3f51ea60` |

The verifier reproduces all three results bit-for-bit using the repo's exact
integer emulation of unrefined x86 `RCPPS`.

## Exact cross-module formula

Installed evaluation order is required:

```text
A = 1.0f
B = 0.0f
for k in source-vector order:
    B = f32(B + f32(m[k] * m[k]))
    A = f32(A + f32(1.0f - m[k]))
numerator = f32(f32(A * A) + B)
f_patch   = f32(numerator / f32((N + 1) * (N + 1)))
```

The algebraic shorthand is
`f=(((N+1)-sum(m))^2+sum(m^2))/(N+1)^2`, but reassociating to that shorthand
is not bit-equivalent. The capture and replay agree exactly:

```text
A          = 1.5810856819152832 / 0x3fca6104
B          = 1.9548754692077637 / 0x3ffa395c
A*A+B      = 4.454707145690918  / 0x408e8cf6
f_patch    = 0.2784191966056824 / 0x3e8e8cf6
```

This validates both disputed assumptions: the `+1` is a distinct fixed
reference term, and the ColorFusion second output is `f` before the existing
byte codec. It is not multiplied by `FusionCacheBayer+0xcc` in this producer.

## Camera selection

Installed body `0x1a8d70` is exhaustively pinned by
`tools/verifiers/verify_colorfusion_selection_config.py`. It enumerates
`RawImageFactory` camera IDs and appends a candidate only when all of these
conditions hold:

```text
CapturedImage.is_enabled != 0
candidate_id != target_id
camera_group(candidate_id) == camera_group(target_id)
(sensor_bayer_red_override.x | sensor_bayer_red_override.y) >= 0
```

Constructor `0x1a89c0` stores the target camera ID at object `+0x140`; the
accepted `int32` vector is object `+0x148..+0x158`. Joined to the admitted
public camera maps and target-anchor proof, the deterministic profile-3 sets
are:

| tier | fixed reference | selected source vector, in runtime order | `N` |
|---|---|---|---:|
| wide | A1 / key 0 | A5, A3, A4 / keys 4,2,3 | 3 |
| tele | B4 / key 8 | B2, B5, B1, B3 / keys 6,9,5,7 | 4 |

A2/key 1 is excluded at wide because its public Bayer override is `(-1,-1)`;
the target itself is separately excluded. C cameras are a different group at
tele; C6 is also inactive and carries `(-1,-1)`. Attach-mode runtime capture
at caller `0x1aad62` reads the owning object's target field `+0x140` and
completed source vector `+0x148..+0x150` directly. Unit-1 `28mm` records target
`0` and sources `[4,2,3]`; exact-focal Unit-2 `70mm` records target `8` and
sources `[6,9,5,7]`. These equal the already admitted composed-camera /
RawImageFactory key orders after removing the target and rejected candidates:
wide `A1,A5,A2,A3,A4`, tele `B4,B2,B5,B1,B3`. The selector appends in that
first-occurrence key-list order. A clean-room implementation must preserve it;
sorting by camera ID is not equivalent at float32 accumulation boundaries.

## Raw-to-transformed checkpoint

Reusable attach harness
`tools/lldb_probes/colorfusion_f_runtime/run_u1_28_transform_attach.sh` plus
`transform_attach_probe.py` captures one source stack buffer immediately
before `0x19d05a -> 0x18fe00` and at return `0x19d062`. It disables the hot
entry breakpoint and suspends non-selected workers before the return capture.
The retained packets are:

| input | before SHA-256 | after SHA-256 | replay |
|---|---|---|---|
| Unit-1 28mm wide | `8073f946...b27b07` | `e431ae3a...161aa4e` | 0/1024 float32 words differ |
| Unit-2 70mm tele | `63176ed0...af514` | `6aa68e1c...e2fbea` | 0/1024 float32 words differ |

`tools/verifiers/verify_colorfusion_transform_runtime.py` performs the replay
with installed exact constants `0x3f3504f3`, `0x3eb504f3`, `0x3fb504f3`, and
`0x3effffff`, replicated predict/update edges, interleaved smooth/detail
packing, rows then columns at strides `1,2,4,8`, and a float32 store after
each installed operation. This proves ColorFusion uses the normalized
5/3-family transform; it is not the unnormalized `0.5/0.25` lifting currently
implemented in Phoenix `colorfusion.cpp`.

## `FusionCacheBayer+0xcc` and the actual CNR lane

The static verifier also pins the complete profile-3 selector chain:

1. admitted profile-3 Demosaicking config `(3,1)` makes `0x40b2b0` return
   false, retaining the key-2/key-4 tuning map;
2. public `LightHeader.sensor_data.type=SENSOR_AR1335(2)` is decremented to
   index 1 and mapped through exact table `[2,2,2,4,4]` to key 2;
3. public analog gain is multiplied by exact `100.0f` to select one of five
   24-byte rows; and
4. the row is copied to `FusionCacheBayer+0xc8..+0xdc`.

The key-2 table at `0x60a988` has exact gain rows `775,500,400,200,100`; field
1, copied to `+0xcc`, is exact `1.0f` in every row. The alternative key-4
values are `1.7,1.35,1.2,0.75,0.5`, so `+0xcc=1` is scoped to profile 3 with
public AR1335 type 2, not a universal installed constant.

The downstream lane remains quantized and must not be simplified to raw `f`:

```text
b      = max(trunc_float_to_int(f32(f * 256.0f)) - 1, 0)
LUT[0] = 0.0f
LUT[b] = f32(sqrt(f32((b + 1) / 256.0f)))  for b > 0
guide  = f32(LUT[b] * sqrtf(+0xcc))
lane3  = f32(guide * guide)
```

For the captured patch, raw `f=0x3e8e8cf6` encodes to byte `70` and decodes
to `lane3=0x3e8dffff` (`0.2773437202`), not back to raw `f`. The old phrase
"exact inverse" and the old equality `lane3=f` are therefore refuted.

## Direct Phoenix audit

`tools/verifiers/colorfusion_phoenix_capture_replay.cpp` was compiled against
live Phoenix commit `2e2625c` without modifying Phoenix. Its current scalar
API gives module results `0x3f63f1c3`, `0x3f6ea0db`, and `0x3f6cc4ea`, versus
the installed results above. Even when supplied the captured Lumen `m`
values, current `colorFusionWeight` returns `0x3e8e8cf7`, one ULP high.

The causes are concrete:

- Phoenix accepts 256 scalar coefficients instead of 256 `vec4` coefficients;
- it ignores the live four-lane noise vector and the installed max reduction;
- it seeds `acc=256` and subtracts weights rather than adding ordered
  `f32(1-q)` terms from zero; and
- it initializes `A=N+1` and subtracts `m`, changing float32 association.

Its local forward transform is also not the normalized lifting implementation
already present in `monofusion.cpp`; the new two-body wide/tele raw checkpoint
replays the normalized transform at all 1024 float32 words per packet and
directly rejects Phoenix's current unnormalized local implementation.

## Scope and status

- Runtime formula bit replay: Unit-1 `28mm`, one patch, all three wide source
  modules.
- Runtime transform and direct camera-order replay: Unit-1 `28mm` wide and
  exact-focal Unit-2 `70mm` tele; `0/1024` transform-word differences each.
- Static formula/selection/config: installed-bundle scope, body/focal
  independent for this exact binary and profile-3 AR1335 inputs.
- Tier breadth: existing Unit-1 wide `N=3` and Unit-2 tele `N=4`, joined to
  admitted four-focal A1/B4 anchor and public camera/group maps.
- Not closed here: a whole-tile ColorFusion replay from raw public inputs,
  complete CNR tile replay, four-focal integration, or final Phoenix image
  parity. `CLM-DENOISE-002` remains `PARTIAL/BLOCKER` despite the exact
  producer formula and ordered camera inputs being implementation-ready.
