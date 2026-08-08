# Static + Runtime Evidence: Selected Color Normalization And Vignetting

## Question

Can the selected color-camera `StereoISP::CreateStereoImage` path be tied
back to concrete public LRI values through its default Bayer normalization and
post-demosaic lens-shading stages?

This bundle closes those two arithmetic boundaries. It does not claim a new
standalone end-to-end replay of the intervening hot-pixel, cross-talk,
demosaic, or sharpen stages. Exact hot-pixel and `DemosaickLightV1` formulas
are separately admitted; the generic cross-talk row workers are separately
excluded under the canonical tested route.

## Artifacts

- [stage_vector_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/create_stereo_color_public_reconstruction/stage_vector_probe.py)
- [verify_selected_color_tile.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/create_stereo_color_public_reconstruction/verify_selected_color_tile.py)
- [stage_single_camera_lri.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/index5_guidance_channel_origin/stage_single_camera_lri.py)
- `runs/create_stereo_color_public_reconstruction/unit1_28mm_a1/report.json`
- `runs/create_stereo_color_public_reconstruction/unit2_28mm_a1/report.json`
- `runs/create_stereo_color_public_reconstruction/unit1_28mm_key6/report.json`
- Full captured payload tiles beside each report, with SHA-256 values embedded
  in the report and rechecked by the verifier.

Installed `libcp.dylib` SHA-256:
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

The verifier rejects changes in these exact installed ranges:

| Installed range | SHA-256 | Role |
|---|---|---|
| `0x350ff0..0x3510c3` | `8ec80ba2b03d411336dbed25c61066a829ca0b553eef7d40f2b4cea027c2c042` | default Bayer normalization wrapper |
| `0x352ce0..0x352ec4` | `fe6b338cfee353b0b83507588461fdd265ee8d5ed559f790ee3eb6492e4135ad` | normalization executor construction |
| `0x353330..0x35380f` | `07703c08210c43abf944a384c3dc9410c389a5e4bfd11fd01424428a7b6263a7` | normalization row worker |
| `0x108080..0x10827e` | `25059587828cec09a146ffb0221b032c120b15053da8e6b5ba3edb778cedad20` | `vec4x32f,true` vignetting row worker |

It also pins the `0x340a30 -> 0x350ff0` normalization thunk and vtable slots
`0x65ae40/+0x30 = 0x340a30` and
`0x65ca18/+0x30 = 0x345d50`.

## Runtime Selection

The probe stops at `CreateStereoImage` `0x27b7a0`, its color closure worker
`0x27d5b0`, the Bayer stage executor `0x33f180`, and its virtual call
`0x33f3e8`. It selects one closure by the already-public
`CapturedImage+0x60` camera key, walks the sixteen-element installed callback
vector, and captures each selected stage before the next stage executes.

All three selected closures have this exact active order and installed target
set:

| Index | Target | Existing public/static identity |
|---:|---:|---|
| 1 | `0x341770` | default hot-pixel removal |
| 3 | `0x340a30` | default Bayer normalization |
| 5 | `0x342280` | cross-talk wrapper |
| 6 | `0x342c60` | demosaic wrapper |
| 11 | `0x340b00` | default Lab-L sharpen wrapper |
| 12 | `0x345d50` | lens shading |
| 15 | `0x34a610` | tone mapping / conditional materialization |

Each report has one selected executor, seven ordered calls, no probe error,
and complete captured payload descriptors. The key-6 full-LRI run terminates
the process only after writing its complete report, avoiding unrelated later
render work.

## Default Bayer Normalization

For a post-hot-pixel unsigned-16 Bayer storage value `raw`, the selected
stage-3 route uses public `SensorData.black_level` and `white_level`:

```text
span  = f32(white_level - black_level)
scale = f32(1.0f / span)
out   = f32(f32(raw) - f32(black_level)) * scale
```

The final multiplication is binary32. There is no clamp in this worker. All
three captures have public levels `black=42`, `white=1023`, hence
`scale=f32(1/981)`.

| Runtime discriminator | Camera key | Exact storage values | Result |
|---|---:|---:|---|
| Unit-1 exact `28mm` A1 | 0 | 274,432 / 274,432 | bit exact |
| Unit-2 exact `28mm` A1 | 0 | 274,432 / 274,432 | bit exact |
| Unit-1 exact `28mm` movable camera | 6 | 274,432 / 274,432 | bit exact |

These are complete captured descriptor-storage comparisons, including stride,
not three hand-picked pixels. The input is explicitly the stage-3
post-hot-pixel payload. Joining it all the way back to packed public RAW uses
the separately admitted RAW10 and selected default hot-pixel formulas.

## Public Vignetting Selection

The lens stage's live settings are `multiplier=1.0`, `inverse=false` for all
three captures. The selected public calibration is vector entry
`LightHeader.module_calibration[camera_key]`; its own public `camera_id` is
not assumed to equal that vector index.

| Runtime discriminator | Public key -> calibration `camera_id` | Models | Public position | Interpolated-profile SHA-256 |
|---|---|---:|---:|---|
| Unit-1 A1 | `0 -> 12` | 1 | `lens_position=10640` | `6a59286359fc8616d346a4ff19473560ada25dc3c8d9bdd77ec2e27d69655307` |
| Unit-2 A1 | `0 -> 4` | 1 | `lens_position=12144` | `d12c119be2e3c99d12bf1a4ddd818352095f6b3d6f995d38537f307ee8cd21a3` |
| Unit-1 movable key 6 | `6 -> 9` | 4 | `mirror_position=400` | `f01371066acb5fb53a366ce4ba614fba8cd179ab0223754ffe76fc2bd2d950b9` |

The one-model fixed cameras select their only public `17x13` model. The
movable camera uses the already-admitted public model-interpolation routine at
`CameraModule.mirror_position`; its four-model result is a genuine selector
discriminator, not a fixed-camera coincidence.

## Exact Lens Worker Replay

The post-demosaic lens worker samples the shaped `17x13` profile in the fixed
half-resolution domain `W=2080`, `H=1560`, so both grid spacings are exactly
`130`. This domain is selected by the exact replay; the full-sensor
`4160x3120`/spacing-260 alternative does not describe the captured worker.

For output storage column/row `(c,r)` and the captured mapped rectangle:

```text
x = f32(mapped_left * 0.5f) + f32(c)
y = f32(mapped_top  * 0.5f) + f32(r)
```

Descriptor origins cancel between local-coordinate and storage-coordinate
conversion; they are not an extra image offset. The installed worker then:

1. floors and clamps the profile cell to `[0,15] x [0,11]`;
2. computes row interpolation in binary32;
3. computes the x slope in binary32;
4. performs the visible x multiply/add in binary64 and converts once to
   binary32;
5. multiplies RGB by that binary32 factor in binary32 and preserves alpha
   bit-for-bit.

| Runtime discriminator | Mapped rectangle | RGB lanes exact | Alpha |
|---|---|---:|---|
| Unit-1 A1 | `[1536,1024,2048,1536]` | 196,608 / 196,608 | bit preserved |
| Unit-2 A1 | `[1536,1024,2048,1536]` | 196,608 / 196,608 | bit preserved |
| Unit-1 movable key 6 | `[2048,0,2560,512]` | 196,608 / 196,608 | bit preserved |

The two A1 runs differ in physical-body calibration identity and all selected
profile bytes. The key-6 run differs in camera, tile rectangle, descriptor
origin, model count, public selector, profile bytes, and factor range. All
three nevertheless match every captured RGB lane.

As an additional scoped observation, stage-11 input and stage-12 input
artifacts have identical SHA-256 values in all three selected tiles. This is
exact no-change incidence for those tiles only; it is not a global sharpen
pass-through claim.

## Admission Boundary

- Installed formula scope: pinned normalization and vignetting worker bodies.
- Numerical runtime scope: exact-`28mm` Unit-1 A1, exact-`28mm` Unit-2 A1,
  and Unit-1 movable key 6 from the same exact-`28mm` LRI.
- Existing route join: prior complete Unit-1 four-focal stage-order and
  correction liveness supplies canonical route incidence; this bundle does
  not claim four-focal numerical equality.
- Proven consequence: selected color-camera stage-3 normalization and
  stage-12 vignetting are reconstructible from public sensor levels,
  calibration-vector order, public camera key, public lens/mirror position,
  and public `17x13` model values.
- Not claimed: a new end-to-end public RAW-to-final-color plane replay;
  pixel cross-talk from descriptor changes; other vignetting inverse/multiplier
  modes; every camera key; numeric body/firmware invariance; or general
  sharpen pass-through.

This is admitted as a scoped `CLM-STEREO-001` / `CLM-CORRECTION-001`
addendum. Both parent claims remain `PROVEN` / `SPEC_READY`.
