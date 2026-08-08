# Bundle Static/Runtime Evidence: Visible `src2` Source Camera Identity

## Scope

This proof follows the one source selected inside
`FusionCacheBayer::0x406a10`, before its wide/tele descriptor-materialization
branch:

```text
FusionCacheBayer+0x8 RawImageFactory
  -> 0x1bea00 camera key
  -> 0x1be970 keyed shared-object lookup
  -> lt::CapturedImage
```

It proves that the selected source is A1/key `0` at wide and B4/key `8` at
tele on both physical bodies. It does not prove the resulting level-1 image is
a direct protobuf field or that no additional generated state affects its
pixels.

## Artifacts

- Runtime probe and scripts:
  [src2_source_camera_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_src2_source_camera_identity/src2_source_camera_probe.py),
  [run_two_body_tiers.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_src2_source_camera_identity/run_two_body_tiers.sh)
- Deterministic verifier:
  [verify_src2_source_camera_identity.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_src2_source_camera_identity/verify_src2_source_camera_identity.py)
- Raw rerunnable logs:
  `runs/prefusion_src2_source_camera_identity/{unit1_28mm,unit1_70mm,unit2_28mm,unit2_70mm}.log`

Run:

```bash
bash tools/lldb_probes/prefusion_src2_source_camera_identity/run_two_body_tiers.sh
python3 tools/lldb_probes/prefusion_src2_source_camera_identity/verify_src2_source_camera_identity.py
```

## Static Custody

The verifier pins the installed binary SHA-256 and the
`0x406b3f..0x406b62` source-lookup window:

```text
0x406b3f  load FusionCacheBayer+0x8
0x406b43  call 0x1bea00
0x406b48  retain derived camera key
0x406b4b  reload FusionCacheBayer+0x8
0x406b59  call 0x1be970 keyed lookup
```

The returned shared control block has address point `0x665eb8`, whose exact
installed RTTI is:

```text
std::__1::__shared_ptr_emplace<
  lt::CapturedImage,
  std::__1::allocator<lt::CapturedImage>
>
```

## Runtime Result

The probes terminate at the first accepted visible-`src2` lookup. Extra
accepted Unit-1 28mm samples caused by concurrent threads are identical and
are not algorithm counts.

| Body | Tier | Derived key | Returned `CapturedImage+0x60` | Active | `FusionCacheBayer+0x18` |
|---|---|---:|---:|---:|---:|
| Unit-1 | 28mm | `0` / A1 | `0` / A1 | `1` | `1` |
| Unit-1 | 70mm | `8` / B4 | `8` / B4 | `1` | `0` |
| Unit-2 | 28mm | `0` / A1 | `0` / A1 | `1` | `1` |
| Unit-2 | 70mm | `8` / B4 | `8` / B4 | `1` | `0` |

Every accepted shared control address point is `0x665eb8`.

## Consequence

Joined to the exact `PipelineCache::processLevel1` identity:

```text
visible src2
  = PipelineCache::processLevel1 materialization
  sourced from tier-anchor CapturedImage
    A1 wide
    B4 tele
```

The level-1 descriptor is generated through `FusionCacheBayer` and source
adapter/validation helpers. Its public origin is therefore the named
tier-anchor `CameraModule`/`CapturedImage`, while the descriptor itself is an
internal generated image, not a direct LRI field.

This closes source-camera identity on the discriminating two-body/two-tier
matrix. Complete generated pixel math and distributed reduction/acceptance
policy remain open.
