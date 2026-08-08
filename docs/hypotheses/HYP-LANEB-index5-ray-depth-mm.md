# HYP-LANEB — Index-5 Ray-Depth Unit Is Millimeters

**Status:** `PROMOTED`  
**Relates to:** Lane B / `CLM-WARP-003` public units for the index-5 depth path  
**Created:** 2026-06-19

## Statement

The one-scalar Triangulator ray depth, generated reciprocal index-5 lookup
values, and `record+0x40` depth descriptor may use millimeters.

## Promotion

Promoted by
[bundle_static_runtime_index5_gdepth_mm_custody_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_gdepth_mm_custody_four_zoom_two_body.md).
The proved dimensional statement is more precise than the original wording:
ray-depth scalars, bounds, and depth-map pixels use `mm`; generated reciprocal
lookup values use `mm^-1`.

## Provenance

This hypothesis was produced by the 2026-06-19 Lane B embedded-protobuf
descriptor sweep and cross-checked against the already-admitted Triangulator
depth-bound and solve-output evidence. At creation, the GDepth strings were
deterministic installed-binary facts while the connection to the internal
index-5 scalar remained an inference. The promoted proof supplies that missing
descriptor, data-pointer, formula, provider, and serializer custody.

## Evidence That Motivates It

- The internal bounds are `[200,640000]` for mode 0 and `[70,40000]` for the
  alternate mode; one complete Unit-1 28mm solve run observes values
  `375.3369..4561.2896`. Those magnitudes are physically plausible as mm.
- The installed public `Stereo` protobuf surface names `depth_format =
  Float32`.
- The installed Google-depth exporter writes `GDepth:Format="RangeInverse"`
  and `GDepth:Units="mm"`.
- The internal scalar is already proven to scale camera ray `(bx,by,1)` in a
  reprojection objective, and `record+0x40` is internally depth-labeled.

Before promotion, none of those facts proved that this internal scalar reached
that exporter without a length-unit conversion.

## Former Proof Gap

The missing proof was a watchpoint or pointer-custody trace plus a verified
formula joining the index-5 / Triangulator scalar or `UpsampleLayer+0x90`
pixels to the GDepth Near/Far serializer. The promoted evidence closes that
gap and excludes an intervening length-unit conversion on the admitted route.

## Completed Proof Plan

1. Exact descriptor-address and data-pointer identity joins all six index-5
   pyramid descriptors and `UpsampleLayer+0x90` to the seven depth-cache
   selections.
2. SHA-pinned worker formulas prove depth-to-reciprocal, reciprocal resize, and
   reciprocal-to-depth conversion with no length-unit conversion.
3. Runtime cache promotion and provider custody join the resulting depth
   descriptor to the GDepth writer, whose live extrema are serialized as
   `GDepth:Near` / `GDepth:Far` with `GDepth:Units="mm"`.

## Former Disproof Criteria

- A proven conversion maps the internal scalar from another unit before GDepth
  serialization.
- The exported GDepth layer is sourced from a different depth product with no
  custody from the index-5 / `record+0x40` path.
- Captured exporter Near/Far values cannot be reconciled with the internal
  values by identity or a verified deterministic conversion.

## Proven Companion

[bundle_static_runtime_index5_public_proto_schema_names.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_public_proto_schema_names.md)
