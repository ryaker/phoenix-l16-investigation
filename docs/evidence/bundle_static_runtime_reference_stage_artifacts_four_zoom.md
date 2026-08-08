# Four-Zoom Undistorted-Plane and Depth-Map Reference Artifacts

## Claim

Installed-bundle RTTI/static custody plus completed Unit-1 profile-3 runtime
captures establish reusable reference artifacts at two validation boundaries:

1. every live direct-contributor `SourceImageCache` undistorted plane, stored as
   a complete camera-scoped RGBA binary16 image; and
2. complete index-5 hypothesis-index/depth, guided-upsampled depth, and final
   full-resolution GDepth maps.

The undistorted planes are byte-deterministic in a complete same-route `28mm`
repeat. The depth maps are not generally deterministic: the `70mm` and `150mm`
repeats land in radically different complete solution classes. Therefore this
evidence closes the old "artifacts unproduced" gap but does not authorize one
golden depth-map hash or close `CLM-VALIDATION-001`.

## Installed Identity

The verified installed binary is SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

- RTTI address point `0x667a20` names the callback inside
  `ImageLensUndistort<filter2, vec4x32f, LensUndistortCRA>`; callback slot
  `+0x30 = 0x262130` enters worker body `0x262170`.
- `0x26159d -> 0x261a50` is the installed undistort-body call.
- `SourceImageCache::$_0` callback `0x3e78d0` calls the wrapper at
  `0x3e79cb -> 0x261050`, then converts the completed float32 tile into the
  cache's `Tile<vec4x16f>` at `0x3e79e8 -> 0x3e82d0`.
- At `0x3e79ed`, owner recovery is `SourceImageCache* = rbx-0xf8`, tile recovery
  is `Tile* = *(r15)`, and the completed image descriptor is `Tile+0xf0`.
- Installed constructor/accessor proof independently establishes
  `SourceImageCache+0x90` as public `CapturedImage::Camera`. That key labels the
  captured owner without relying on allocation order.

The verifier SHA-pins the callback table and these body windows; it does not
infer identity from a human-read disassembly alone.

## Reusable Harness

Undistorted planes:

- `tools/lldb_probes/reference_undistorted_planes/source_cache_tile_probe.py`
- `tools/lldb_probes/reference_undistorted_planes/stitch_source_cache_tiles.py`
- `tools/lldb_probes/reference_undistorted_planes/analyze_undistorted_planes.py`
- `tools/lldb_probes/reference_undistorted_planes/run_unit1_28mm_tiles.sh`
- `tools/lldb_probes/reference_undistorted_planes/run_unit1_remaining_and_repeat.sh`
- ignored raw root: `runs/reference_undistorted_planes/`

Depth/disparity maps:

- `tools/lldb_probes/reference_stage_maps/reference_stage_map_probe.py`
- `tools/lldb_probes/reference_stage_maps/analyze_reference_stage_maps.py`
- `tools/lldb_probes/reference_stage_maps/run_unit1_four_zoom.sh`
- `tools/lldb_probes/reference_stage_maps/run_unit1_repeat_remaining.sh`
- ignored raw root: `runs/reference_stage_maps/`

Combined verifier:

```bash
python3 tools/lldb_probes/reference_undistorted_planes/verify_reference_validation_artifacts.py
```

Expected terminal line: `reference_validation_artifacts=OK`.

## Undistorted Planes

Every focal run observes five public camera owners. Wide uses B1..B5 and tele
uses C1..C5, matching the admitted direct-contributor key vectors. The cache
tile size is `512x512`; edge tiles close the distortion-derived envelope.
Stitching by `(tile_y,tile_x)` produces contiguous little-endian RGBA16F.

| Focal | Camera | Stitched size | SHA-256 |
|---|---|---:|---|
| `28mm` | B1 | `4774x3631` | `d1a150a642e6a9aa64c47da668fa86b1ec8caae5e1f8d796a1d003117b9769b3` |
| `28mm` | B2 | `4764x3616` | `2d61ca786e1c29003e004ebd1a403073087b4116c9515b888ec8140af5e181dc` |
| `28mm` | B3 | `4764x3616` | `43d0ebefa86eec411a489600a5d073825b02a291a543f78c794e0c930b7641ed` |
| `28mm` | B4 | `4318x3260` | `179a5d69a4f0cdcd68ac1097780db853fbdadf014d750190ccae2448f10300f6` |
| `28mm` | B5 | `4739x3596` | `279bece18ecad776bb66ea3448ae9e335bf271e1fba319b38e99516f5cde1188` |
| `35mm` | B1 | `4784x3636` | `372a81a8a0e8aced41ab56aa7cfacc29a5e647176239fed83d7e4bd8417cc5d0` |
| `35mm` | B2 | `4719x3580` | `21f3b91800739cbe8abc062a4e49cd31fa281aa72e5b59f30975c7a7cd43171a` |
| `35mm` | B3 | `4769x3626` | `e5b0b230849d4321e6666c0410f7f916a398ca1f5257e8a3bcf76d0196a4494f` |
| `35mm` | B4 | `4328x3260` | `f8783e1b2c68d3379ee2e736222a65bc699b42ae04a5252d39075831643db9ed` |
| `35mm` | B5 | `4739x3591` | `17e159822c06f31e156dcc9d7db09a7802c561177f3c63f728c4142d4170c4bb` |
| `70mm` | C1 | `4217x3186` | `07055c34cecc0eb8aeb57f4f865f10b7afe8a9f30da348482a92b90f0d06e07e` |
| `70mm` | C2 | `4178x3134` | `c23951f0f20d8e32f40fcfe8e90c99f0515a7626c422e57f65f13c84cf53e6c2` |
| `70mm` | C3 | `4170x3177` | `c96610a63bc97fc9ba6750ecedc021d039d6a2c7d343a00013ba1e85b0c7bbdd` |
| `70mm` | C4 | `4217x3216` | `ed769ca719ae4eee88026a5b6095492b0c6f8d71b7e793eaf7025985458df5cd` |
| `70mm` | C5 | `4174x3160` | `1cd84d2eaf732fd0c5320b2a764a8b19fdfa01b23e851cd6bacc71948e51064e` |
| `150mm` | C1 | `4161x3164` | `97fc5e1eafd6a57791bd39ad16734d22302f02ec80970942343aa30a86e36e52` |
| `150mm` | C2 | `4118x3109` | `6b65986e7cd8bd8eb0099f0fa8d6ce508a440cc25638af69368f2a4a1abf196f` |
| `150mm` | C3 | `4140x3134` | `ea89092cd3bf45c823cc201f4d9bef88db95bfa976a85da5b3d5bc5051b8c5bb` |
| `150mm` | C4 | `4161x3152` | `2ec5a139f10503e74307b098fe3d189fe2e98ee02cfe251e6eea850e2f462c95` |
| `150mm` | C5 | `4174x3160` | `ab23cac8e775a11bc7d773b89ff24d1ea3d622cd1711e692382aaab852809796` |

The second complete `28mm` render reproduces all five sizes and all five
hashes exactly. This is direct same-input stage determinism evidence; no body
or firmware invariance is inferred.

## Depth / Disparity Artifacts

Each base run captures:

| Artifact | Type | Size |
|---|---|---:|
| index-5 minimum-cost hypothesis index | `uint16` | `2080x1560` |
| index-5 depth | float32 millimeters | `2080x1560` |
| guided-upsampled depth | float32 millimeters | `4160x3120` |
| final GDepth | float32 millimeters | `10432x7824` |

Base-run SHA-256 values are retained in
`runs/reference_stage_maps/analysis.json` and verified with their exact byte
counts. Same-route repeat comparison gives:

| Focal | Map | Unequal fraction | Max abs | RMSE |
|---|---|---:|---:|---:|
| `28mm` | hypothesis index | `0.00209196` | `8` indices | `0.100088` |
| `28mm` | index-5 depth | `0.00209196` | `29.9910 mm` | `0.369287 mm` |
| `28mm` | final GDepth | `0.00304180` | `26.75 mm` | `0.342100 mm` |
| `35mm` | all four maps | `0` | `0` | `0` |
| `70mm` | hypothesis index | `0.998707` | `1356` indices | `66.4584` |
| `70mm` | index-5 depth | `0.998707` | `639092.98 mm` | `227301.02 mm` |
| `70mm` | final GDepth | `0.994374` | `113340.70 mm` | `50981.35 mm` |
| `150mm` | hypothesis index | `1.0` | `56` indices | `33.6582` |
| `150mm` | index-5 depth | `1.0` | `17627.60 mm` | `5848.44 mm` |
| `150mm` | final GDepth | `1.0` | `13441.82 mm` | `5890.26 mm` |

Both members of every pair are complete, finite, correctly shaped maps from
successful full renders. The tele differences therefore refute the prior
assumption that these stages admit one deterministic map per LRI. They do not
prove that two samples exhaust the possible map classes.

## Admission Scope

- Runtime scope: canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` profile-3
  no-auto-LRIS renders.
- Static scope: installed SHA-pinned `libcp.dylib` only.
- Camera scope: every live direct contributor in each tested tier, B1..B5 wide
  and C1..C5 tele.
- Repeat scope: all four depth-map stages at all four focal tiers; all five
  undistorted planes repeated at `28mm`.
- Unit/body scope: Unit-1 only. These are fixed-input validation artifacts, not
  a calibration-invariance claim.
- Claim consequence: `CLM-VALIDATION-001` remains `PARTIAL/BLOCKER`, narrowed
  from missing artifacts to an intermediate-depth repeat-distribution and
  acceptance-policy gap.

