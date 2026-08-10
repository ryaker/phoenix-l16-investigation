# Static/Runtime Evidence: CNR Lane-3 Byte-Weight Origin

## Scope

This bundle narrows `CLM-DENOISE-002` for canonical profile-3 bridge HDR. It
joins installed-bundle static proof to one completed Unit-1 `70mm`
(`L16_03434`) runtime capture.

It proves the exact source representation and conversion that constructs the
CNR source tile's fourth lane. It does not yet identify the upstream public
name or LRI-derived producer of the byte plane, and it does not generalize the
observed one-plane route beyond the tested render.

## Artifacts

- Probe:
  `tools/lldb_probes/cnr_lane3_producer/guide_origin_probe.py`
- LLDB driver:
  `tools/lldb_probes/cnr_lane3_producer/unit1_70mm_guide_origin.lldb`
- Deterministic verifier:
  `tools/lldb_probes/cnr_lane3_producer/verify_guide_origin.py`
- Rerunnable raw report:
  `runs/cnr_lane3_producer/unit1_70mm_guide_origin.json`

Run:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/cnr_lane3_producer/unit1_70mm_guide_origin.lldb
python3 tools/lldb_probes/cnr_lane3_producer/verify_guide_origin.py
```

The verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`,
six relevant body ranges, four RTTI address points, the LUT, and the runtime
sample replay.

## Installed Custody

Installed RTTI names the owner and cache exactly:

```text
FusionCacheBayer+0xe0 -> shared_ptr<lt::TileCache<unsigned char>>
FusionCacheBayer+0x128 -> shared_ptr<lt::TileCache<float>>
FusionCacheBayer base +0xf0/+0x100 -> shared_ptr<lt::TileStorage>
```

The `FusionCacheBayer` constructor `0x4064c0` constructs the unsigned-byte
cache through `0x3d1f80` and stores it at `+0xe0` at `0x406643`. Its installed
callback RTTI is exactly the constructor's `$_1` callable over
`shared_ptr<lt::Tile<unsigned char>>`.

At `0x406a10`:

1. `0x406b20..0x406b3a` passes `FusionCacheBayer+0xe0` to `0x3d2ca0` and
   extracts level `0` into stack descriptor `rbp-0xf0`.
2. `0x406e78..0x406e98` is the selected Unit-1 70mm one-plane route. It loads
   `sqrtf(FusionCacheBayer+0xcc)` as the scalar and calls `0x1bce50` with the
   byte descriptor.
3. `0x407458` passes the resulting float guide unchanged as argument 9 to
   `0x31acf0`; `0x33f480` installs a cropped view at denoise-task `+0x60`.
4. The previously admitted `0x308f50` producer squares that float guide into
   CNR source lane 3.

The exact selected formula for source byte `b` is therefore:

```text
LUT[0] = float32(0)
LUT[b] = float32(sqrt((b + 1) / 256))  for b in 1..255
guide  = float32(LUT[b] * sqrtf(FusionCacheBayer+0xcc))
lane3  = float32(guide * guide)
```

The tested render has `FusionCacheBayer+0xcc = 1.0f`, so its scalar is
exactly `1.0f`.

The installed LUT begins with a deliberate special case: byte zero maps to
zero, not `sqrt(1/256)`. The later square must remain a binary32 multiply.
Replacing it with the algebraic rational `(b+1)/256` changes 118 of the 256
possible outputs by one ULP. The 256-float LUT SHA-256 is
`d1a4aea24b957fc99d9bf0b9998f0023f073ed385f29266c33861e7f909cc627`;
the 256-float post-square table SHA-256 is
`b850b8957c039ed70ef15fcea2f4d1ec4085cd2935ccf9bd50bc792be4f30a4d`.

## Alternate Installed Combiners

The same installed owner has two additional static combination formulas:

```text
two-plane index = max((((a + 1) * (b + 1)) >> 8) - 1, 0)
three-plane index = max((((a + 1) * (b + 1) * (c + 1)) >> 16) - 1, 0)
guide = float32(LUT[index] * scalar)
```

These bodies are pinned by the verifier at `0x1bcf90` and `0x1bd0a0`.
Their existence is installed-static truth. Their runtime incidence is not
admitted by this Unit-1 70mm capture.

## Runtime Result

The focused Unit-1 70mm report records:

```text
one_plane helper hits captured: 4
two_plane helper hits: 0
three_plane helper hits: 0
runtime one-plane samples replayed exactly: 184
```

The source bytes are spatially doubled, for example
`255,255,254,254,...` and `135,135,135,135,136,136,...`. The corresponding
guide samples are passed by pointer unchanged into the CNR task. Sample byte
`135` yields guide `0.7288689613342285`; the admitted later square yields
lane 3 `0.53125` with the installed operation order.

Verifier output:

```text
binary_sha256=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
source_cache_rtti=lt::TileCache<unsigned char>
owner_rtti=lt::FusionCacheBayer
lut_sha256=d1a4aea24b957fc99d9bf0b9998f0023f073ed385f29266c33861e7f909cc627
lane3_sha256=b850b8957c039ed70ef15fcea2f4d1ec4085cd2935ccf9bd50bc792be4f30a4d
rational_shortcut_mismatches=118
runtime_one_plane_samples=184 skipped_events=2
result=OK
```

## RTTI Correction

The CNR worker receives the RTTI-named
`lt::Internal::Pipeline::setWhiteBalance::$_22` callable as context. Its
vtable thunks do not appear in the CNR execution stack. Therefore the earlier
wording that the guide is produced "inside" that lambda is not admitted.
The exact executing chain is:

```text
FusionCacheBayer::0x406a10
  -> byte TileCache level-0 extraction
  -> 0x1bce50 byte-to-float guide
  -> 0x31acf0 / 0x33f480 task construction
  -> 0x34b3f0 CNR dispatch
  -> 0x308f50 lane3 square
```

## Admission Boundary

Licensed for a clean-room implementation at this scope:

- preserve a `uint8` per-pixel source-weight plane alongside the float source;
- use the installed LUT and exact binary32 multiply order;
- preserve the byte-zero special case;
- do not replace the square with an algebraic rational shortcut.

Still open:

- which upstream Bayer/fusion producer deposits the bytes into the shared
  `lt::TileStorage` and its public semantic name;
- the public origin and selected-profile breadth of scalar
  `FusionCacheBayer+0xcc`;
- one/two/three-plane route incidence across focal tiers and physical bodies;
- complete CNR tile replay after those inputs are closed.
