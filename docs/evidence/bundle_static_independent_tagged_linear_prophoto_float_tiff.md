# Installed Matrix + Independent Proof: Tagged Linear-ProPhoto Float TIFF

## Result

The remaining clean-room output contract is closed by an independent,
self-describing TIFF mapping:

```text
container:        classic little-endian TIFF
dimensions:       final placed image dimensions
photometric:      RGB
samples/pixel:    3
bits/sample:      32,32,32
sample format:    IEEE float
planar config:    contiguous
orientation:      top-left (1)
compression:      none (lossless)
alpha:            absent
pixel mapping:    final vec4x32f lanes 0,1,2 -> TIFF R,G,B unchanged
color profile:    embedded linear-ProPhoto RGB ICC v4
```

Lane 3 is the internal working/normalization lane already excluded from the
Radiance writer. Negative, greater-than-one, and ordinary finite float32 RGB
values are preserved bit for bit by this TIFF contract.

The generated profile and fixture are deterministic:

```text
ICC SHA-256:  4bb6a2f6de50a01d76893448562f862f223b339744102354271418b42e3b2f1b
TIFF SHA-256: 5c3ac14d1b6711a94a2e7d25584eccfb7b0a0656f2dabe5f70c63edd892b87c8
```

## Installed Color Definition

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The bundle carries the exact compact ProPhoto RGB-to-XYZ float32 matrix at
file/VA `0x5aae20`. Expanding its two structural zeroes gives:

```text
[ 0.7976748943328857,  0.13519169390201569, 0.03135339915752411 ]
[ 0.2880401909351349,  0.7118741273880005,  0.00008569999772589654 ]
[ 0,                   0,                   0.8252099752426147  ]
```

Normalizing the matrix columns gives the installed primaries:

```text
R = (0.7347000195, 0.2652999805)
G = (0.1595999868, 0.8404000132)
B = (0.0366000502, 0.0001000410)
```

Normalizing the row sums gives the installed D50 white:

```text
W = (0.3456691847, 0.3584961892)
```

These values independently identify the installed
`linear_prophoto_rgb` selector's exact colorimetry. The ICC is generated from
these bundle-extracted chromaticities with gamma-`1.0` red, green, and blue
TRCs. ICC's mandatory D50 PCS and s15Fixed16 tag representation produce the
expected tiny quantization:

```text
ICC white xy = (0.3457029220, 0.3585375328)
```

The verifier checks all three ICC colorants against the installed primaries,
checks all three TRCs are linear, checks the profile ID, and checks the
embedded profile bytes exactly match the generated profile.

## Independent Fixture

The verifier writes this `2 x 3` RGB float32 payload:

```text
(-0.125,  0,    0.5)   (1,     1.25, 4)     (0.125, 0.25, 0.375)
( 8,      0.75, 0.25)  (0.03125, -1,  2)     (0.9,   0.8,  0.7)
```

An independent TIFF parse reproduces the 72 payload bytes exactly. This
explicitly proves that the chosen container does not apply transfer
encoding, clamp negative channels, clamp HDR values, quantize to integers, or
reorder RGB.

The file carries:

```text
ImageWidth              3
ImageLength             2
BitsPerSample           32,32,32
SampleFormat            IEEEFP,IEEEFP,IEEEFP
Photometric             RGB
PlanarConfiguration     contiguous
Orientation             top-left
InterColorProfile       exact 644-byte ICC
```

At full Phoenix dimensions, three float32 channels require about `0.98 GB`,
below classic TIFF's 4 GiB offset ceiling. A clean-room implementation may
stream strips or use lossless Deflate without changing pixel or color
semantics; the admitted minimal contract uses uncompressed strips.

## Reader Validation

The deterministic fixture is independently accepted by:

- `tifffile`, which parses the tags and reproduces every float bit;
- `tiffinfo`, which reports IEEE floating point and an ICC profile;
- `exiftool`, which reports 32-bit float RGB and profile description
  `Phoenix Linear ProPhoto RGB`;
- ImageMagick `identify`, which reports TIFF, floating-point quantum data,
  top-left orientation, and the 644-byte ICC profile;
- macOS ImageIO through `sips`, which reports:

```text
pixelWidth: 3
pixelHeight: 2
format: tiff
samplesPerPixel: 3
bitsPerSample: 32
space: RGB
profile: Phoenix Linear ProPhoto RGB
```

This is a concrete modern host photo framework reading the output, not just a
structural TIFF parser.

## Reproduction

```bash
python3 tools/output_tagged_export/verify_tagged_linear_prophoto_tiff.py
```

Artifacts:

- `tools/output_tagged_export/verify_tagged_linear_prophoto_tiff.py`
- `runs/output_tagged_export/phoenix_linear_prophoto.icc`
- `runs/output_tagged_export/phoenix_linear_prophoto_float32.tiff`
- `runs/output_tagged_export/verification.json`

No Lumen code or binary participates in profile or TIFF generation. The
installed dylib is read only to verify the source RGB-to-XYZ constants.

## Consequence

Together with:

- admitted final linear-ProPhoto float-row custody;
- exact final placement for every orientation present in complete profile-3
  inputs; and
- the exact legacy Radiance writer formula;

this independent mapping closes `CLM-OUTPUT-002` for the clean-room
LRI-to-merged-image application. The Radiance route remains a byte-parity
reference; tagged 32-bit-float RGB TIFF is the admitted modern readable
output contract.
