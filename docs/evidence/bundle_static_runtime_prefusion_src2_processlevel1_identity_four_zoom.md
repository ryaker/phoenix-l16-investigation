# Bundle Static/Runtime Evidence: Visible `src2` Is `PipelineCache::processLevel1`

## Scope

This proof gives exact installed names to the visible `src2` wrapper and its
four-focal runtime-bound worker. It joins SHA-pinned RTTI and vtable bytes to
the already captured complete-render packets.

It proves:

- visible `src2` wrapper address point `0x65f6e8` is
  `lt::PipelineCache::initResAmp(bool*)::$_2`;
- its callable slot `+0x30` is wrapper body `0x3ecd80`;
- that wrapper calls `0x3ebb80`, then the one-image normalization body
  `0x3edb80`;
- `0x3ebb80` installs callback address point `0x65f7e8`;
- RTTI names that callback as the `ImageWarpClamped` lambda inside
  `lt::PipelineCache::processLevel1(Image<vec4x32f>&, Rectangle<int> const&)`;
- its callable slot `+0x30` is worker `0x3ed2e0`, already observed at
  `28mm`, `35mm`, `70mm`, and `150mm`;
- the adjacent direct-contributor wrapper address point `0x65f768` is the
  distinct `lt::PipelineCache::initResAmp(bool*)::$_3`, whose slot `+0x30`
  is `0x3eced0`.

This exact name narrows visible-`src2` semantics to PipelineCache level-1
materialization. It does not by itself assign a public LRI field name to the
source image returned by `FusionCacheBayer::0x406a10`, prove that level 1 is a
multi-camera reduction, or close the distributed IRAMP reduction policy.

## Artifacts

- Verifier:
  [verify_src2_processlevel1_identity.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_src2_processlevel1_identity/verify_src2_processlevel1_identity.py)
- Installed binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Reused complete-render packets:
  `runs/src2_executor_target/src2_executor_target_28mm.log`,
  `src2_executor_target_35mm_hwcomplete.log`,
  `src2_executor_target_70mm_hwcomplete.log`, and
  `src2_executor_target_150mm_hwcomplete.log`
- Prior runtime method:
  [lldb_src2_executor_target_four_zoom_scope.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_executor_target_four_zoom_scope.md)
- Prior source-descriptor custody:
  [lldb_src2_descriptor_origin_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_descriptor_origin_four_zoom.md)

Run:

```bash
python3 tools/lldb_probes/prefusion_src2_processlevel1_identity/verify_src2_processlevel1_identity.py
```

## Static Identity

The verifier checks the full installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and independent hashes over the relevant wrapper, callback-construction,
callback-table, and worker-entry byte windows.

RTTI at address point `0x65f6e8` is exactly:

```text
std::__1::__function::__func<
  lt::PipelineCache::initResAmp(bool*)::$_2,
  ...,
  bool(lt::Image<lt::vec4x32f>&, lt::Rectangle<int> const&)
>
```

Its slot `+0x30` is `0x3ecd80`. Direct-call decoding proves:

```text
0x3ecd80 wrapper
  -> 0x3ebb80
  -> 0x3edb80 one-image normalization
```

The callback installed by `0x3ebb80` at `0x3ec410` has address point
`0x65f7e8`. Its exact RTTI context is:

```text
lt::Internal::ImageWarpClamped<
  (lt::ResamplerFilter)2,
  lt::vec4x32f,
  lt::PipelineCache::processLevel1(...)::$_4,
  ...
>
```

The callback slot `+0x30` is `0x3ed2e0`.

The adjacent address point `0x65f768` is independently named
`PipelineCache::initResAmp(bool*)::$_3`, and its slot `+0x30` is
`0x3eced0`. Therefore the process-level-1 `src2` wrapper and the direct
contributor wrapper are not the same callable.

## Runtime Join

The verifier re-parses the accepted summaries and full packets from the four
complete-render probes:

| Seed | Accepted gate | Accepted dispatch | Worker entry | Callback table | Worker |
|---|---:|---:|---:|---:|---:|
| `28mm` | `1` | `1` | `1` | `0x65f7e8` | `0x3ed2e0` |
| `35mm` | `1` | `4` | `1` | `0x65f7e8` | `0x3ed2e0` |
| `70mm` | `1` | `1` | `1` | `0x65f7e8` | `0x3ed2e0` |
| `150mm` | `1` | `1` | `1` | `0x65f7e8` | `0x3ed2e0` |

All four packets contain an empty error list. Hit totals are observations of
those probe runs, not algorithm constants.

## Admitted Meaning

The visible `src2` callable is no longer semantically anonymous:

```text
PipelineCache::initResAmp::$_2
  -> PipelineCache::processLevel1
  -> ImageWarpClamped<filter 2, vec4x32f>
  -> one-image normalization
```

Joined to prior custody, `processLevel1` obtains its one source descriptor
through `PipelineCache+0x1d8`, exact object family `lt::FusionCacheBayer`,
vtable slot `+0x18 = 0x406a10`.

The public meaning boundary is still important. The installed name establishes
the PipelineCache level and resampling operation. It does not name the
descriptor as raw, reference, fused, or final output, and it does not establish
which public LRI calibration fields determine all of its contents.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`:

- visible `src1` is the exact tier-anchor `lt::ReferenceImageCache`;
- visible `src2` is exact `lt::PipelineCache::processLevel1` materialization
  over one `FusionCacheBayer`-produced descriptor;
- direct contributor callables are the distinct `initResAmp::$_3` path over
  `lt::SourceImageCache` objects.

`CLM-PREFUSION-002` remains open because the complete distributed
reference/level-1/five-source reduction and acceptance policy is not yet
closed.
