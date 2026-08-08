# Bundle Static/Runtime Evidence: Raw Sensor Layout and RAW10 Decode

## Scope

This proof closes the clean-room input contract for the raw sensor surfaces
used by the canonical LRI corpus:

- public packed format name;
- raster dimensions, row stride, per-plane byte span, and block slot layout;
- camera-to-raw-block partitions;
- public Bayer red-site override and resulting Bayer phase;
- exact packed-10-bit unpack arithmetic.

The corpus check covers exact-focal `28mm`, `35mm`, `70mm`, and `150mm`
representatives from both calibration bodies. Runtime corroboration is one
complete Unit-1 `28mm` profile-3 decoder-entry census. The installed decoder
is body/focal independent.

This proof does not assign public semantic roles to every non-raw LELR block,
close black/white-level calibration, or close demosaic math.

## Artifacts

- Static verifier:
  [verify_raw_sensor_layout.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py)
- Runtime probe:
  [runtime_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/raw_sensor_layout/runtime_probe.py)
- Runner:
  [run_probe.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/raw_sensor_layout/run_probe.sh)
- Rerunnable reports:
  `runs/raw_sensor_layout/`

Run:

```bash
tools/lldb_probes/raw_sensor_layout/run_probe.sh
```

Accepted result:

```text
PASS raw sensor layout lris=8 raw_surfaces=84 format=RAW_PACKED_10BPP runtime_reports=1
```

## Installed-Bundle Identity

The verifier requires installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The embedded `camera_module.proto` descriptor has serialized SHA-256:

```text
b6f688e5e96edb6721b0a80040e0fec1fc61a59f6893fdcaef7b54d408797b1f
```

It publicly names
`.ltpb.CameraModule.Surface.FormatType` value `7` as:

```text
RAW_PACKED_10BPP
```

The installed decoder bodies are independently byte-pinned:

| Body | SHA-256 |
|---|---|
| `0xf4d90..0xf53c1` packed-surface path | `5ecf39316b3efdeb5a2b795f8b6b94a8a46d25eca2860114895ddb6f62eb629e` |
| `0xf6cf0..0xf72a1` unpack dispatch | `36dfeb7980bc88c21ff0ce4141e86f2828826a960af51bf45b270c0cd7d1df8c` |
| `0xf7b10..0xf7c3a` row variant | `ea66e4af68cad2d792ce99e661592a1afa7a537a73ca2211f95dd24b46bb10cf` |
| `0xf7c40..0xf7d29` row variant | `eb71578ba62ac530d249be8badb88bafa1c4158d757c29129613a9e91919ff33` |
| `0xf7d30..0xf7ea8` row variant | `77aeaab90c1a869d65fd37344af4c43aa1dd82cfed58221e40d75e372dc2fdf0` |
| `0xf7eb0..0xf7fcb` row variant | `1df4a55308e19a6b1227f76d58cc3b36e60c51298cd1096a7b0fe1ff37d7df22` |

`0xf4d90` allocates the 16-bit destination and calls `0xf6cf0`; `0xf6cf0`
selects one of the four row-order/flip variants. The arithmetic is identical
apart from output traversal direction.

## Exact Raw Geometry

Every one of the `84` public raw surfaces has:

```text
width       = 4160
height      = 3120
format      = 7 = RAW_PACKED_10BPP
row_stride  = 5200 bytes = 4160 * 10 / 8
image_bytes = 16,224,000 = 5200 * 3120
```

Within each raw LELR block:

```text
slot_bytes       = 0xf7a000 = 16,228,352
slot_gap         = 0x1100 = 4,352
surface offset   = 32 + slot_index * 0xf7a000
message offset   = surface_count * 0xf7a000
```

All eight files have public horizontal and vertical flip fields absent/false.

The stable raw partitions are:

```text
wide block 0: A1 A5 B2 B4 B5  = keys 0,4,6,8,9
wide block 2: A2 A3 A4 B1 B3  = keys 1,2,3,5,7

tele block 0: B2 B4 B5 C5     = keys 6,8,9,14
tele block 2: B1 B3 C2        = keys 5,7,11
tele block 3: C1 C3 C4 C6     = keys 10,12,13,15
```

Wide files have `11` LELR blocks and `10` raw surfaces. Tele files have `12`
LELR blocks and `11` raw surfaces. This is file-layout scope: canonical
profile 3 later disables C6 independently.

## Exact Unpack Formula

The installed row bodies decode each consecutive ten-byte group as one
little-endian 80-bit word containing eight adjacent 10-bit pixels:

```text
pixel[i] = (little_endian_80bit_group >> (10*i)) & 0x3ff
           for i = 0..7
```

Equivalently, for bytes `b0..b9`:

```text
p0 = b0       | ((b1 & 0x03) << 8)
p1 = (b1>>2)  | ((b2 & 0x0f) << 6)
p2 = (b2>>4)  | ((b3 & 0x3f) << 4)
p3 = (b3>>6)  | ( b4         << 2)
p4 = b5       | ((b6 & 0x03) << 8)
p5 = (b6>>2)  | ((b7 & 0x0f) << 6)
p6 = (b7>>4)  | ((b8 & 0x3f) << 4)
p7 = (b8>>6)  | ( b9         << 2)
```

This is not the alternate MIPI grouping that stores four high-byte samples
followed by one shared low-bit byte. The verifier checks both formula forms
for deterministic basis vectors and decodes a real ten-byte sample from every
one of the `84` surfaces.

## Bayer Phase

The public
`CameraModule.sensor_bayer_red_override = Point2I{x,y}` is decoded as signed
`int32`, then mapped to the repeating 2x2 red site. The mapping is stable
across both bodies and all exact-focal representatives:

| Cameras | Red site | Phase |
|---|---:|---|
| `B1`, `B5`, `C1`, `C3` | `(0,0)` | `RGGB` |
| `A1`, `A3`, `A4` | `(1,0)` | `GRBG` |
| `A5` | `(0,1)` | `GBRG` |
| `B2`, `B3`, `B4`, `C2`, `C4`, `C5` | `(1,1)` | `BGGR` |
| `A2`, `C6` | `(-1,-1)` | monochrome |

## Runtime Corroboration

A native LLDB ignore-count breakpoint stops on the tenth call to `0xf4d90`
without executing Python in the live callback. The stopped Unit-1 `28mm`
frame reports:

```text
packed decoder calls = 10
requested size       = 4160 x 3120
row stride           = 5200
flip/order flag      = 0
```

The breakpoint is then disabled and the renderer exits normally. Python only
reads the already stopped frame, avoiding the known debugger timing
perturbation from hot callback probes.

## Consequence

A clean-room reader can locate every public raw plane in the tested two-body,
four-focal corpus, unpack it bit-exactly to 16-bit samples, and assign the
correct Bayer or monochrome phase. Remaining input-side blockers begin after
this boundary: calibration-level normalization and the exact
`DemosaickLightV1` image reconstruction formula.
