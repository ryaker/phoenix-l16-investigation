# C6 ImagePyramid Downstream Liveness Probe

Purpose: test whether the same C6 `context+0x538` ImagePyramid observed on
the proven zero-fill route is later read by downstream libcp code during the
same bridge-HDR render.

Scope:

- Canonical bridge HDR profile only: `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`.
- Four canonical focal tiers: `28mm`, `35mm`, `70mm`, `150mm`.
- Runtime liveness only. A downstream hit proves that the named VA executed and
  read/called through the ImagePyramid path under the tested render. It does
  not prove final image contribution, terminality, or Lumen-quality merge
  sufficiency by itself.

Key captured families:

- `0x3b2f59`: same-render zero-fill checkpoint from the proven route.
- `0x3b7470..0x3b7546`: histogram-like last-level consumer.
- `0x3b77b0..0x3b7ab4`: last-level materializer/repair path.
- `0x3b9820..0x3b9f89`: region/deeper-level consumer path.
- `0x3bdd9b..0x3bde8d`: direct first-image descriptor path.
- `0x3bf3b3..0x3bf419`: virtual consumer path using `ctx+0x5a0`.

Ignored raw outputs belong under:

- `runs/c6_image_pyramid_downstream_liveness/`
