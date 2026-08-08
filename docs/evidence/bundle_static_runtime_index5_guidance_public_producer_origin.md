# Static/Runtime Evidence: Index-5 Guidance Public Producer Origin

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B public-producer refinement  
**Bearing:** `StereoLayer<false>+0x240` `Images[0]` and `+0x288` `Guidance`

> **Corrective supersession (2026-07-16):** The descriptor/cache custody in
> this document remains valid. Its section "`ConvertToYUV` Is a Separate
> Route" misidentified enclosing body `0x27aef0` from nested RTTI and is
> refuted by direct call/callback/full-plane proof. `CreateStereoImage` calls
> `0x27adc0` at `0x27bff0`; callback worker `0x27ce60` is RTTI-named
> `StereoISP::ConvertToYUV::$_0`, and its output is the float source packed
> into key `0`. See
> `bundle_static_runtime_index5_guidance_yuv_formula_two_body.md`.

## Question

Prior proof names target `+0x288` as `Guidance` and proves that it reuses the
first `Images` descriptor. It does not name the public image producer behind
that descriptor.

This proof asks whether `Images[0]` can be traced to a concrete public
`StereoISP` operation and whether the descriptor installed in the keyed cache
is the same descriptor later supplied to `StereoLayer`.

## Artifacts

- Reusable LLDB harness:
  `tools/lldb_probes/index5_guidance_channel_origin/`
- Static/runtime verifier:
  `tools/lldb_probes/index5_guidance_channel_origin/verify_guidance_channel_origin.py`
- Rerunnable raw report:
  `runs/index5_guidance_channel_origin/guidance_origin_28mm.json`
- Reused four-focal first-Images proof:
  `docs/evidence/bundle_static_runtime_index5_cost_operand_names_four_zoom.md`
- Reused two-body camera/calibration proof:
  `docs/evidence/bundle_static_runtime_index5_composed_geometry_public_origins_two_body.md`

The LLDB harness terminates immediately after the first complete cache
insertion. Exit status `9` is therefore expected and is checked by the
verifier.

## Exact Public Producer

Installed RTTI names `0x27b7a0` through callback objects constructed inside
that body. The demangled enclosing signature is:

```text
lt::StereoISP::CreateStereoImage(
  lt::Image<lt::vec4x8ui>&,
  lt::Image<unsigned short> const&,
  lt::CapturedImage const&,
  lt::CalibData const&,
  lt::CalibData const&,
  lt::Vec2<int> const&,
  lt::SoftISP const&,
  lt::SoftISP const&,
  lt::Vec3<float> const&,
  lt::Image<lt::vec4x32f>&,
  lt::CalibData const&,
  bool,
  bool
)
```

The verifier independently pins:

- the full raw RTTI name at `0x5dba20`;
- the nested `CreateStereoImage::$_2` name at `0x5dbb30`;
- callback vtable address points `0x6591a8` and `0x659228`;
- callback workers `0x27d950` and `0x27dc80`; and
- the complete `0x27b7a0..0x27cdc0` installed code range.

This names the product only as the first public argument:
`Image<vec4x8ui>` produced by `StereoISP::CreateStereoImage`. It does not
rename its four components as RGBA, YUV, or any other channel convention.

## `ConvertToYUV` Is a Separate Route

The installed `StereoISP::ConvertToYUV` RTTI can now be classified without
using it as suggestive evidence:

```text
0x3f4700
  -> 0x27aef0 StereoISP::ConvertToYUV
  -> descriptor copy at 0x3f4840
  -> shared descriptor at state+0x270
  -> optional-image argument at 0x3ff43c -> 0x2681b0
```

`0x2681b0` saves that optional argument in `rbx`. Its type-`0`
`StereoLayer` branch at `0x268222..0x268268` does not forward `rbx`; it calls
`0x26ba90` with the keyed Images vector, composed-record vector, and flags
vector. The type-`1` Upsample branch beginning at `0x268270` is the branch
that reads the optional descriptor.

The verifier pins the `ConvertToYUV::$_0` RTTI, vtable `0x6590a8`, worker
`0x27d1a0`, call at `0x3f47f8`, `state+0x270` store, dispatcher handoff, and
branch split. Therefore the named `ConvertToYUV` product is not the
`StereoLayer Images[0]` descriptor admitted here. This rejects the
RTTI-adjacency shortcut; it does not rule out independently proving similar
component mathematics inside `CreateStereoImage`.

## Producer-to-Cache Custody

The installed chain is:

```text
0x3fc750
  -> 0x3f4b90
     -> 0x27b7a0 StereoISP::CreateStereoImage
  -> 0xf340 copy returned Image<vec4x8ui> descriptor
  -> 0x224f30 insert descriptor by camera key
```

At `0x3f5086`, `0x3f4b90` passes its caller-owned output descriptor as the
first argument to `0x27b7a0`. `0x3fc750` then copies that descriptor into the
shared cache payload and calls `0x224f30`.

The runtime capture observes:

- producer call/return sites `0x3f5086/0x3f508b`;
- the expected caller stack through `0x3fc750`;
- key `0`;
- root/node writers `0x225004/0x22504a`;
- one completed producer event and one payload assignment; and
- exact equality of all 48 descriptor bytes before cache insertion.

The matched descriptor carries `2080x1560` geometry and identical nonzero
data pointers.

## Cache-to-Images Custody

`0x226410` is the keyed cache accessor:

- root at cache object `+0x78`;
- integer key at tree node `+0x20`; and
- shared payload at node `+0x28/+0x30`.

`0x3ff050` iterates the composed-camera key order, calls `0x226410`, and
appends each returned shared image descriptor to its first vector. It passes
that vector through:

```text
0x3ff43c -> 0x2681b0 -> 0x26ba90
```

At `0x26bad4..0x26baeb`, `0x26ba90` copies that first vector directly into
`StereoLayer+0x240`. The installed label proof names `+0x240` exactly
`Images`.

The previously admitted four-focal order therefore supplies:

| Focal tier | `Images[0]` / `Guidance` public producer |
|---|---|
| `28mm`, `35mm` | A1 `CapturedImage` -> `StereoISP::CreateStereoImage` -> `Image<vec4x8ui>` |
| `70mm`, `150mm` | B4 `CapturedImage` -> `StereoISP::CreateStereoImage` -> `Image<vec4x8ui>` |

The same construction path supplies public `CalibData` and `SoftISP`
arguments. Existing two-body proof independently verifies the public
per-camera calibration carriers and composed camera order on Unit-1 four
focals plus the Unit-2 exact-28mm discriminator.

## Runtime Scope

Direct descriptor equality is captured on the canonical Unit-1 `28mm` seed.
The installed producer/copy/cache/accessor path is shared code, and the
accepted four-focal proof establishes live `Images[0] -> Guidance` reuse.

No direct Unit-2 `CreateStereoImage` breakpoint packet is admitted here.
Attempts on exact-28mm and exact-35mm Unit-2 seeds repeatedly lost the LLDB
debugserver connection at launch with this hot producer breakpoint, while
the existing Unit-2 composed-geometry harness completed on the exact-28mm
seed. The body discriminator therefore remains the admitted public-input and
camera-order proof, not a claimed second descriptor-equality capture.

## Verification

```text
static_index5_guidance_channel_origin=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
public_producer=lt::StereoISP::CreateStereoImage(lt::Image<lt::vec4x8ui>&, lt::Image<unsigned short> const&, lt::CapturedImage const&, lt::CalibData const&, lt::CalibData const&, lt::Vec2<int> const&, lt::SoftISP const&, lt::SoftISP const&, lt::Vec3<float> const&, lt::Image<lt::vec4x32f>&, lt::CalibData const&, bool, bool)
convert_to_yuv_route=separate state+0x270 optional Upsample input; not StereoLayer Images
runtime=Unit-1 28mm key=0 descriptor=2080x1560 CreateStereoImage_output==cached_payload
index5_guidance_channel_origin=OK
```

The adjacent cost-operand and composed-geometry verifiers remain green.

## Admission and Remaining Boundary

Admitted:

- exact public producer name and output type for `Images[0]` and therefore
  reused `Guidance`;
- exact tier-anchor `CapturedImage` identity: A1 wide, B4 tele;
- producer-output -> keyed cache -> `StereoLayer Images[0]` custody; and
- generated-product status: Guidance is not a direct calibration protobuf
  field, although public `CapturedImage`, `CalibData`, and `SoftISP` inputs
  feed its construction.

Still open:

- public component/channel semantics inside `vec4x8ui`;
- complete names/custody for every remaining Cost-volume recurrence source,
  temporary, cap, and baseline;
- stable full-map Cost-volume distributions;
- final source contribution and acceptance/rejection; and
- whole-State and selector-bank identities.

In particular, this proof does not convert the adjacent installed
`StereoISP::ConvertToYUV` RTTI into custody and does not name the Guidance
components Y/U/V.
