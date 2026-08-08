# Static/Runtime Evidence: Pre-Fusion Cache RTTI Identity

**Date:** 2026-07-01  
**Status:** VERIFIED; admitted Lane A semantic-identity refinement  
**Bearing:** visible `src1`, direct contributor payloads, and owner `+0x6a8`

## Question

Four-focal runtime evidence distinguished the visible `src1` payload family
at vtable address point `0x65f140` from direct contributor payloads at
`0x65f490`, but intentionally left both semantic types unnamed. The static
provenance chain also left the owner `+0x6a8/+0x6b0` shared object anonymous.

This proof asks whether installed RTTI gives those live objects exact names.

## Artifacts

- Reusable SHA-pinned verifier:
  `tools/lldb_probes/prefusion_cache_rtti_identity/verify_prefusion_cache_rtti_identity.py`
- Reused admitted runtime evidence:
  `lldb_src1_contributor_payload_family_four_zoom.md`
- Reused construction/provenance evidence:
  `bundle_proof_src1_payload_provenance.md`
  and `bundle_proof_src1_owner_cache_selection.md`

No new LLDB render was needed.

## Exact Installed Identities

The verifier resolves each address point through its exact typeinfo object and
name pointer:

| Runtime/static object | Address point | Exact installed type |
|---|---:|---|
| owner `+0x6a8/+0x6b0` shared control/object | `0x66a118` | `std::__1::__shared_ptr_emplace<lt::ImageCaches, ...>` |
| first-map payload returned by `0x3e0af0` | `0x65f140` | `lt::ReferenceImageCache` |
| direct-contributor payload returned by `0x3e0a60` | `0x65f490` | `lt::SourceImageCache` |
| visible `src1` wrapper | `0x65f668`, substantive `+0x30 = 0x3ecc10` | `lt::PipelineCache::initResAmp(bool*)::$_1` |
| visible `src2` wrapper | `0x65f6e8`, substantive `+0x30 = 0x3ecd80` | `lt::PipelineCache::initResAmp(bool*)::$_2` |

The `ReferenceImageCache` callback RTTI also embeds its constructor context:
`RawImageFactory`, one `CapturedImage::Camera`, `StereoAsyncAPI`, and
`Tile<Vec3<Float16>>`. The `SourceImageCache` callback RTTI independently
embeds `RawImageFactory`, one `CapturedImage::Camera`, `LensUndistortCRA`,
and `Tile<vec4x16f>`.

These names are exact installed RTTI, not labels inferred from error strings.

## Construction Join

The verifier pins the existing construction chain:

1. `0x3b3069` allocates the `0x80`-byte shared control/object block.
2. `0x3b30a8` installs the exact `ImageCaches` shared-control address point.
3. The object begins at control `+0x18`.
4. `0x3b30c3 -> 0x3e02d0 -> 0x3dfcc0` constructs it.
5. `0x3b30c8` stores the object at owner `+0x6a8`; `0x3b30d6` stores its
   shared control at `+0x6b0`.
6. `0x3dfcc0` allocates a `0x490`-byte first-map payload and constructs it
   through `0x3e2db0 -> 0x3e27a0`.
7. The exact payload is stored at first-map node `+0x28` and later returned
   by `0x3e0af0`.

The already-admitted four-focal packets identify that returned payload's
vtable as `0x65f140` and the five direct payloads' vtable as `0x65f490`.
Therefore their exact RTTI names apply to the live objects, not merely to
unused installed classes.

## Four-Focal Meaning

Joining the exact types to the admitted camera-key evidence gives:

| Focal family | Visible `src1` | Direct contributor vector |
|---|---|---|
| `28mm`, `35mm` | key `0`, A1 `ReferenceImageCache` | B1..B5 `SourceImageCache` |
| `70mm`, `150mm` | key `8`, B4 `ReferenceImageCache` | C1..C5 `SourceImageCache` |

Thus visible `src1` is the tier-anchor reference-image cache. It is not an
anonymous composite payload and is not just another direct contributor
`SourceImageCache`.

## Verification

```text
static_prefusion_cache_rtti_identity=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
owner+0x6a8=lt::ImageCaches
src1_payload=lt::ReferenceImageCache vtable=0x65f140
direct_contributor_payload=lt::SourceImageCache vtable=0x65f490
visible_wrappers=PipelineCache::initResAmp::$_1/$_2
rtti_entries=5
prefusion_cache_rtti_identity=OK
```

## Admission and Remaining Boundary

Admitted:

- exact `lt::ImageCaches`, `lt::ReferenceImageCache`, and
  `lt::SourceImageCache` names for the already-custody-bound objects;
- exact `PipelineCache::initResAmp::$_1` / `$_2` identities for the visible
  wrappers; and
- visible `src1` as the A1-wide/B4-tele tier-anchor reference cache.

This supersedes older wording that left visible `src1` potentially
"composite-ish" or semantically anonymous.

Still open:

- exact generated-image semantics of visible `src2`;
- complete IRAMP use of reference, secondary, and five source caches;
- exact multi-contributor reduction/normalization policy;
- C6 routing and final acceptance/rejection.

The result narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`; claim status
does not change.
