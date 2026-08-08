# AWB Public Origin And Reciprocal Policy

**Claim target:** `CLM-AWB-001`  
**Installed binary:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Method:** embedded-schema extraction, complete local-LRI corpus census,
SHA-pinned static arithmetic, and stopped-frame public-value joins  
**Scope:** canonical Unit-1 `28/35/70/150mm`, exact-focal Unit-2 `28mm`
runtime discriminator, all eight exact-focal/two-body public inputs, and all
`9,438` local corpus files for container/layout coverage

## Result

The renderer's live RGB white-balance multiplier has the public LRI origin:

```text
LightHeader.view_preferences.awb_gains.r
LightHeader.view_preferences.awb_gains.g_r
LightHeader.view_preferences.awb_gains.g_b
LightHeader.view_preferences.awb_gains.b
```

For every structurally complete LRI in the local corpus, `g_r == g_b`. The
operational triplet is:

```text
awb_rgb = (
    float32(1.0f / awb_gains.r),
    float32(1.0f / awb_gains.g_r),
    float32(1.0f / awb_gains.b)
)
```

The same triplet is supplied to the four-phase Bayer/demosaic path and applied
after the IRAMP square-copy. The post-square vec4 is
`(awb_rgb.r, awb_rgb.g, awb_rgb.b, 1.0)`. There is no gain interpolation on
this route.

## Public Schema

The installed serialized `view_preferences.proto` descriptor begins at file
offset `0x5caa70`, has SHA-256
`fdc7259f0c4ef618574bfcc1af27a9cc5baeb0dad08636e939228dc52be8a14a`,
and proves:

| Message | Field | Public name | Type |
|---|---:|---|---|
| `.ltpb.ViewPreferences` | 7 | `awb_mode` | `AWBMode` enum |
| `.ltpb.ViewPreferences` | 15 | `awb_gains` | `ChannelGain` |
| `.ltpb.ViewPreferences.ChannelGain` | 1 | `r` | required float |
| same | 2 | `g_r` | required float |
| same | 3 | `g_b` | required float |
| same | 4 | `b` | required float |

Enum value `0` is `AWB_MODE_AUTO`.

## Two LRI Container Layouts

The corpus contains two public encodings of the same message:

1. legacy LRIs store `ViewPreferences` directly in its own LELR protobuf
   payload;
2. later LRIs store it as field `19`, `LightHeader.view_preferences`, in a
   sparse LightHeader payload.

This is a container-layout difference, not a schema or gain-policy difference.
The verifier discovers the message by schema shape rather than fixed block
index; observed AWB blocks occur at indices `7`, `8`, and `9`.

## Complete Corpus Census

The verifier scans all `9,438` local `.lri` files by seeking across declared
LELR records:

| Result | Count |
|---|---:|
| Structurally complete files with exactly one AWB message | `9,242` |
| Legacy direct `ViewPreferences` layout | `2,906` |
| Wrapped `LightHeader.view_preferences` layout | `6,336` |
| Unequal `g_r/g_b` pairs | `0` |
| Explicit `awb_mode` fields | `0` |
| Structurally incomplete files without a unique AWB message | `196` |
| Structurally complete files without AWB | `0` |

The `196` exclusions have only `0..4` decodable records and none closes at the
declared file size. A representative file is rejected by `lri_process` as a
corrupted record before pipeline setup. They do not establish a render-time
fallback policy for valid input.

Because `awb_mode` is absent, protobuf enum-default behavior selects
`AWB_MODE_AUTO`. The already-computed `awb_gains` values are nevertheless
present and are what the renderer consumes. No render-time scene estimator is
needed to reproduce a structurally complete corpus input.

## Installed Arithmetic

The SHA-pinned body `0x3510f0..0x351330`:

1. reads the three stored internal gains;
2. divides float32 `1.0` by each;
3. packs the reciprocals with lane 3 equal to `1.0`;
4. passes that vector into the image-materialization path.

The SHA-pinned post-square body `0x3ec960..0x3ecb10` calls `0x1bea20`, copies
the three AWB values from the retained object, and constructs the same vec4
before the admitted `0x2d7320` channel multiply.

## Runtime Join

Five stopped-frame runs capture both:

- `DemosaickLightV1` driver `0x2eb560`, where the reciprocal triplet is
  supplied with the public Bayer phase; and
- `0x3eca61`, immediately before the post-square triplet is packed into vec4.

Each captured triplet equals the float32 reciprocal of the same LRI's public
`awb_gains` fields exactly:

| Runtime scope | Public `(r,g,b)` | Live reciprocal `(r,g,b)` |
|---|---|---|
| Unit-1 28mm | `(1.7178390,1,1.5888386)` | `(0.58212674,1,0.62939054)` |
| Unit-1 35mm | `(1.7190851,1,1.6020590)` | `(0.58170480,1,0.62419671)` |
| Unit-1 70mm | `(1.8127948,1,1.5831292)` | `(0.55163443,1,0.63166040)` |
| Unit-1 150mm | `(1.7636282,1,1.6007433)` | `(0.56701291,1,0.62470978)` |
| Unit-2 28mm | `(1.6482948,1,1.7789507)` | `(0.60668761,1,0.56212914)` |

The demosaic and post-square captures occur on potentially different worker
threads, but both independently match the public values.

## Reproduction

```bash
tools/lldb_probes/awb_public_origin/run_probe.sh

python3 tools/lldb_probes/awb_public_origin/verify_awb_public_origin.py \
  --require-runtime \
  --corpus-root "/Volumes/Base Photos/Light" \
  --json-out runs/awb_public_origin/verification_corpus.json
```

Current focused result:

```text
PASS AWB public origin lris=8 runtime=5 corpus=9438
```

## Scope And Exclusions

- **Four-zoom:** public values are parsed at Unit-1 `28/35/70/150mm`; exact
  reciprocal runtime joins cover the same quartet.
- **Two-body:** public parsing covers both bodies at all four exact focals;
  Unit-2 `28mm` supplies an independent runtime discriminator with materially
  different values.
- **Closed:** public names/wire path, legacy/current layout, mode default for
  every complete corpus LRI, reciprocal decode, demosaic custody, post-square
  custody, and valid-input fallback question.
- **Not claimed:** the capture-time hardware algorithm that originally chose
  the stored gains, behavior for a synthetically authored non-AUTO/unequal-green
  message absent from the corpus, or repair of structurally corrupt LRIs.

The earlier shorthand `Block-8 f19.f15` described one observed physical
placement but was not a public schema name and did not cover legacy direct
messages. It is superseded by the public paths above.
