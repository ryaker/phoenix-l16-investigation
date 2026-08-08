# Tele Firing Topology: Two-Body Public Headers and Runtime Join

**Date:** 2026-07-02  
**Status:** VERIFIED; admission-ready for `CLM-ZOOM-002`  
**Scope:** Exact-focal `70mm` / `150mm` public LRI headers on both physical
calibration bodies, plus completed canonical Unit-1 runtime at both tele
focals.

## Question

Does the canonical `150mm` path start from only six C cameras, or from five B
cameras plus six C cameras?

## Reproducer

```bash
./tools/lldb_probes/zoom_tele_firing_topology/run_verify.sh
```

The reusable verifier:

1. invokes the existing public protobuf/LRI parser on exact-focal `70mm` and
   `150mm` files from both calibration signatures;
2. requires public `LightHeader.modules[camera]` camera IDs `5..15`, named
   `B1..B5,C1..C6`, in all four files;
3. rechecks the existing completed `0xe59a4 -> 0xf2770` constructor reports at
   canonical Unit-1 `70mm` and `150mm`;
4. requires all eleven constructed `CapturedImage` items to have initial
   `is_enabled = 1`; and
5. requires completed `10432x7824` Radiance HDR output from both runtime runs.

Current output:

```text
PASS tele firing topology public=Unit1+Unit2@70/150 runtime=Unit1@70/150 set=B1..B5,C1..C6
```

The machine-readable report is regenerated at
`runs/zoom_tele_firing_topology/report.json`.

## Public LRI Result

| Calibration signature | Focal | Public fired camera IDs | Public names |
|---|---:|---|---|
| Unit-1 `722a6e72...` | `70` | `5..15` | `B1..B5,C1..C6` |
| Unit-1 `722a6e72...` | `149` (`150mm` tier) | `5..15` | `B1..B5,C1..C6` |
| Unit-2 `223961c6...` | `70` | `5..15` | `B1..B5,C1..C6` |
| Unit-2 `223961c6...` | `149` (`150mm` tier) | `5..15` | `B1..B5,C1..C6` |

These are per-file calibration-signature assignments. Date folders and
same-name files are not used as unit identity.

## Runtime Result

The admitted canonical Unit-1 constructor reports contain eleven paired
pre/post events at each tele focal:

```text
70mm:  keys {5,6,7,8,9,10,11,12,13,14,15}, all initial is_enabled=1
150mm: keys {5,6,7,8,9,10,11,12,13,14,15}, all initial is_enabled=1
```

Both runs completed and wrote `10432x7824` HDR output. This is runtime proof
that the public tele firing set enters `libcp` construction as `5B+6C`, not
merely a render-free header interpretation.

## Admission Consequence

`CLM-ZOOM-002` can be stated positively: canonical `150mm` firing topology is
`B1..B5 + C1..C6`; the old `6C only` account is false. The companion `70mm`
result verifies the same tele-tier mechanism, and the two-body public-header
check eliminates a single-calibration-body concern.

This does **not** say all eleven cameras survive every later gate. In
particular, separate admitted `CLM-C6-001` evidence proves that C6/key `15` is
later cleared and excluded from the canonical merge route. Firing topology,
direct IRAMP contributor identity, and final contributor survival remain
distinct stages.

Capture dates and possible camera-firmware differences are not controlled by
this proof. Agreement across the two calibration bodies is corroboration of
the public topology only; no difference or cause is attributed to body or
firmware.

## Joined Evidence

- `docs/evidence/bundle_static_lane_b_crossunit_lri_public_carriers.md`
- `docs/evidence/lldb_capturedimage_f2770_origin_four_zoom.md`
- `docs/evidence/bundle_static_runtime_capturedimage_is_enabled_public_origin_two_body.md`
- `docs/evidence/bundle_static_runtime_c6_terminal_filter_differential_tele.md`

