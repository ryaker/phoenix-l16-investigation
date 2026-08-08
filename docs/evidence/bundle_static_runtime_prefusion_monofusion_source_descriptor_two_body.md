# Bundle + LLDB Evidence: Wide `src2` `lt::MonoFusion` Source Descriptor

## Scope

This proof identifies the optional `FusionCacheBayer+0x20` object, its selected
camera, and its immediate generated-image consequence in visible `src2`.

The merge-critical focal scope is the canonical Unit-1 quartet:

- `28mm`: `2018-07-23/L16_02130`
- `35mm`: `2018-12-26/L16_03041`
- `70mm`: `2019-05-18/L16_03434`
- `150mm`: `2018-07-29/L16_02285`

Body-independence spot checks use exact-focal Unit-2 `28mm`
`2018-07-04/L16_02130` and `70mm` `2018-10-25/L16_02894`.

All six instrumented bridge-HDR renders exited `0` and wrote complete
`10432x7824` Radiance HDR output.

This closes the public installed class name of `FusionCacheBayer+0x20` and the
tested wide/tele source-descriptor split. It does not close the complete
`MonoFusion` worker formula, distributed pre-fusion policy, or final
contributor acceptance/rejection.

**Later closure:** the worker formula and distributed profile-3 policy were
subsequently admitted. The former coefficient-origin boundary below is closed
by `bundle_static_runtime_prefusion_monofusion_color_wrapper_two_body.md`,
which proves the packs are a derived response/opponent basis and its inverse,
not independently named protobuf matrices.

## Artifacts

- Static verifier:
  [verify_monofusion_identity.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_identity/verify_monofusion_identity.py)
- Runtime helper:
  [monofusion_runtime_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_identity/monofusion_runtime_probe.py)
- Runtime report validator:
  [validate_reports.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_identity/validate_reports.py)
- Rerun driver:
  [run_all.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_identity/run_all.sh)
- Six per-seed `.lldb` scripts in the same probe directory
- Ignored raw packets and HDR outputs:
  `runs/prefusion_monofusion_identity/`

Commands:

```bash
python3 tools/lldb_probes/prefusion_monofusion_identity/verify_monofusion_identity.py
tools/lldb_probes/prefusion_monofusion_identity/run_all.sh
python3 tools/lldb_probes/prefusion_monofusion_identity/validate_reports.py
```

The installed-bundle verifier pins `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## Installed Class Identity

### Construction and custody

The nonzero `FusionCacheBayer+0x18` constructor branch:

1. allocates a `0x250`-byte object at `0x406707`;
2. initializes it through `0x40676b -> 0x1b17b0 -> 0x1b1360`;
3. stores it at `FusionCacheBayer+0x20` at `0x406774`.

The object is distinct from `FusionCacheBayer+0x120`, whose `0x1aab00`
constructor installs the RTTI-backed `lt::ColorFusionBayer` object.

### `lt::MonoFusion` proof

`FusionCacheBayer::0x406970`:

- initializes `FusionCacheBayer+0x120` through `0x1ab2d0`;
- when `FusionCacheBayer+0x18 != 0`, loads `+0x20` and tail-calls `0x1b17c0`.

Body `0x1b17c0` contains the unique installed guard string:

`Called MonoFusion::initialize() twice!`

It constructs callbacks at address points `0x657be0` and `0x657c68`. Their
exact RTTI names contain, respectively:

```text
lt::MonoFusion::initialize(bool const*)::$_0
lt::MonoFusion::initialize(bool const*)::$_2
```

The body commits `object+0x240 = 1` at `0x1b2722`.

`FusionCacheBayer::0x406a10` later loads `+0x20` at `0x406c0a` and calls
`0x1b3530`. The static verifier pins `0x1b3530 -> 0x1b37a0` and the same
object layout. Therefore:

```text
FusionCacheBayer+0x20 = lt::MonoFusion
0x1b17c0 = MonoFusion initialization body
0x1b3530 = MonoFusion immediate process/body wrapper
```

## Camera Selection

The initialization loop in `0x1b17c0`:

- enumerates camera IDs from the retained `RawImageFactory`;
- rejects inactive `CapturedImage+0x30` records;
- keeps records in the target camera's `0xf6c60` group;
- reads the already public
  `CameraModule.sensor_bayer_red_override.{x,y}` pair through `0xf2750`;
- appends IDs with a negative/sign-bit pair to the int32 vector at
  `MonoFusion+0xc0`.

This is the semantic purpose of the earlier `FusionCacheBayer+0x18` scan and
optional-object gate: it detects whether the target camera group has an
eligible mono-fusion camera.

## Runtime Matrix

| Body / focal | `+0x20` stores | Mono target | `MonoFusion+0xc0` IDs | `MonoFusion+0x20` image | sampled process calls | downstream adapter |
|---|---:|---|---|---|---:|---|
| Unit-1 `28mm` | 1 | A1 / `0` | A2 / `[1]` | `4160x3120` | 16 | `0x31b110` |
| Unit-1 `35mm` | 1 | A1 / `0` | A2 / `[1]` | `4160x3120` | 16 | `0x31b110` |
| Unit-1 `70mm` | 0 | none | none | none | 0 | `0x31acf0` |
| Unit-1 `150mm` | 0 | none | none | none | 0 | `0x31acf0` |
| Unit-2 `28mm` | 1 | A1 / `0` | A2 / `[1]` | `4160x3120` | 16 | `0x31b110` |
| Unit-2 `70mm` | 0 | none | none | none | 0 | `0x31acf0` |

The 16 counts are probe capture caps, not algorithm constants or exhaustive
tile counts.

At every captured wide process entry:

- `MonoFusion+0x240 = 1`;
- the selected-ID vector remains `[1]`;
- the generated output and both input descriptors are readable and
  same-shaped;
- the output backing pointer is non-null and does not alias either input.

At every captured wide `0x40721b -> 0x31b110` call, `%rdx` equals the current
`0x406a10` frame's `rbp-0x190` `MonoFusion` output descriptor. The distinct
anchor descriptor passed in `%r9` has a different non-null backing pointer.

The canonical tele pair and Unit-2 tele discriminator have zero
`MonoFusion` construction, initialization, and process hits and use only the
direct `0x407458 -> 0x31acf0` adapter.

## Immediate Pixel Formula

`0x1b3530` first calls still-open worker `0x1b37a0`, which populates a
four-float output image `p` and a same-shaped scalar image `m`. It then applies
the following exact per-pixel transform:

```text
q =
    p.r * object[0x114,0x120,0x12c]
  + p.g * object[0x118,0x124,0x130]
  + p.b * object[0x11c,0x128,0x134]

s = (m - object[0xf0][1]) / object[0xf8]

out.rgb =
    s   * object[0x138,0x144,0x150]
  + q.g * object[0x13c,0x148,0x154]
  + q.b * object[0x140,0x14c,0x158]

out.a = p.a
```

The loop is bounded by the generated output descriptor width and height and
writes one 16-byte vector per pixel.

This proves the immediate post-worker color/mono transform. It does not assign
public protobuf names to the two 3x3 coefficient packs or close the internal
`0x1b37a0` image-generation/fusion formula.

## Admitted Consequence

The outer visible-`src2` worker remains exactly:

```text
PipelineCache::processLevel1
  -> ImageWarpClamped<ResamplerFilter=2, vec4x32f>
```

That worker resamples one generated source descriptor. The descriptor's
upstream semantics are now tier-dependent:

- wide `28mm` / `35mm`: A1 target plus A2 `lt::MonoFusion` generated image,
  adapted through `0x31b110`;
- tele `70mm` / `150mm`: direct B4 tier-anchor route through `0x31acf0`, with
  no `MonoFusion` object under the tested complete renders.

Therefore "one-source resampling worker" remains correct only for the outer
`processLevel1` worker shape. It must not be generalized into "the wide
source descriptor has one camera of ancestry."

## Remaining Boundary

- Whether any noncanonical capture enables a different ID set.
- Alternate-profile/editor generalization beyond the later scoped admissions.
