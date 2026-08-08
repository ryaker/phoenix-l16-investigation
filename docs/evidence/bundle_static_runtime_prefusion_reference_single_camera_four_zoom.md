# Static/Runtime Evidence: `src1` Reference Cache Has One Public Camera Origin

**Date:** 2026-07-02  
**Status:** VERIFIED; admitted as a bounded `CLM-PREFUSION-001/002` refinement  
**Scope:** installed bundle plus canonical Unit-1 `28mm`, `35mm`, `70mm`, `150mm`

## Question

Visible `src1` is already proven to be `lt::ReferenceImageCache`, keyed A1 at
wide and B4 at tele. This proof asks whether that cache hides a
multi-camera/composite source or instead retains exactly one public camera
origin.

## Reusable Verifier

`tools/lldb_probes/prefusion_reference_single_camera/verify_reference_single_camera.py`

The verifier SHA-pins:

- `ReferenceImageCache` base constructor `0x3ddd50..0x3dde52`;
- raw-image accessor `0x3ddf30..0x3ddf6b`;
- derived constructor head `0x3e27a0..0x3e28cb`; and
- all five constructor-lambda RTTI records at address points
  `0x65f188`, `0x65f208`, `0x65f288`, `0x65f308`, and `0x65f388`.

It also pins every relevant `0x1be970` direct-call target and the exact
instructions carrying the camera key.

## Installed Public Identity

Each constructor-lambda RTTI record contains the same exact constructor:

```text
lt::ReferenceImageCache(
  vector<Vec2i> const&,
  Vec2i const&,
  shared_ptr<TileStorage> const&,
  shared_ptr<RawImageFactory> const&,
  lt::CapturedImage::Camera,
  shared_ptr<StereoAsyncAPI> const&)
```

There is exactly one `lt::CapturedImage::Camera` parameter. This is an
installed RTTI type, not a semantic guess from an error string.

## Exact Key Custody

The derived constructor at `0x3e27a0`:

1. saves incoming `r9d` to `r15d`;
2. calls base constructor `0x3ddd50` without replacing `r9d`; and
3. passes the saved `r15d` key to `RawImageFactory` lookup `0x1be970` at
   `0x3e2879`.

The base constructor:

1. saves the same incoming `r9d` key at cache `+0x90`;
2. saves the one `RawImageFactory` shared pointer at `+0x98/+0xa0`;
3. uses that key for lookups at `0x3dddbd` and `0x3dde15`; and
4. derives level-0 dimensions from the returned same-key image.

Accessor `0x3ddf30` reloads the same `+0x98` factory and `+0x90` key and
calls `0x1be970` again. No camera vector or second camera key participates in
these constructor/accessor paths.

## Four-Zoom Runtime Join

The admitted constructor packets in
`lldb_src1_payload_constructor_live_four_zoom.md` bind this exact installed
constructor to the visible `src1` payload:

| Canonical seed | Runtime constructor key | Public camera |
|---|---:|---|
| Unit-1 `28mm` | `0` | A1 |
| Unit-1 `35mm` | `0` | A1 |
| Unit-1 `70mm` | `8` | B4 |
| Unit-1 `150mm` | `8` | B4 |

Those packets also bind the resulting object to vtable address point
`0x65f140`, whose exact installed RTTI is `lt::ReferenceImageCache`.

The four canonical files are one physical calibration body. This proof does
not compare numerical image content between bodies. Capture date and
potential camera-firmware differences therefore cannot be attributed to body
identity here. Existing exact-focal Unit-2 checks elsewhere establish the
broader algorithm family but are not needed to prove the installed
one-Camera constructor contract.

## Verification Output

```text
reference_single_camera_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
type=lt::ReferenceImageCache
constructor_camera_parameters=1 public_type=lt::CapturedImage::Camera
camera_storage=base+0x90 raw_image_factory=base+0x98/+0xa0
same_key_raw_image_lookups=base_ctor:2 derived_ctor:1 accessor:1
reference_single_camera=OK
```

## Admitted Boundary

Admitted:

- visible `src1` has one concrete public camera origin;
- it is A1 at canonical `28mm` / `35mm` and B4 at canonical `70mm` /
  `150mm`; and
- `ReferenceImageCache` construction/access does not itself perform an
  N-to-1 camera reduction.

Not admitted:

- complete pixel-generation math inside every `ReferenceImageCache`
  callback;
- the outer IRAMP policy combining `src1`, generated `src2`, and the five
  `SourceImageCache` contributors;
- distributed scoring, selection, normalization, or final acceptance.

`CLM-PREFUSION-002` therefore remains `OPEN/BLOCKER`, but the remaining
search boundary moves outside `src1` construction and into the load-bearing
IRAMP distributed policy.
