# LLDB Evidence: C6/Post-Mutation ImagePyramid Tele Data-Watch Grid

**Date:** 2026-05-28
**Status:** admitted negative-scope evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This probe expands the representative C6/post-mutation ImagePyramid data-watch
test from one selected byte range per run to a tele-focused grid. After the
zero-fill return site `0x3b2f59`, each run arms a hardware read/write
watchpoint on one 8-byte range of one zero-filled ImagePyramid level, then lets
the render complete.

This is data-driven evidence: it can catch later reads or writes through aliases
or helpers that a static callsite probe might miss. It is still not whole-buffer
terminality proof.

## Tested LRIs

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Probe Artifacts

Reusable probe harness:

- `tools/lldb_probes/c6_image_pyramid_data_watch_grid/README.md`
- `tools/lldb_probes/c6_image_pyramid_data_watch_grid/c6_image_pyramid_data_watch_grid_probe.py`
- `tools/lldb_probes/c6_image_pyramid_data_watch_grid/run_grid.sh`

Ignored raw outputs:

- `runs/c6_image_pyramid_data_watch_grid/c6_image_pyramid_data_watch_grid_70mm_l{0..4}_{first,middle,last}.json`
- `runs/c6_image_pyramid_data_watch_grid/c6_image_pyramid_data_watch_grid_150mm_l{0..4}_{first,middle,last}.json`
- matching `.log` files in `runs/c6_image_pyramid_data_watch_grid/`

Admitted final run IDs:

- `70mm`: status directory `runs/c6_image_pyramid_data_watch_grid/status/20260527T203949/`
- `150mm`: status directory `runs/c6_image_pyramid_data_watch_grid/status/20260527T204303/`, with clean replacement for `150mm` level `2` last at `status/20260527T204733/`

Interrupted or failed attempts are not cited as evidence.

## Grid Definition

For each tele seed, the probe covers all five ImagePyramid levels. For each
level, it watches three 8-byte ranges:

- `first`: offset `0`
- `middle`: aligned midpoint of the inferred `stride_pixels * height * 4` byte span
- `last`: final 8 bytes of the inferred byte span

Runtime descriptors satisfy `stride_pixels == width` for every admitted grid
cell.

## Runtime Summary

Every admitted grid cell has:

- `process_exit_status = 0`
- `errors = []`
- `drive_hit_step_cap = false`
- `target_level_hits = 1`
- `watchpoints_armed = 1`
- `watchpoint_hits = 0`
- summed LLDB watchpoint hit count `0`
- `watched_bytes_at_arm.all_zero = true`

| Zoom | Level | Descriptor `(width,height,stride_pixels)` | Watched offsets | Result |
|---|---:|---|---|---|
| `70mm` | `0` | `(8832,6624,8832)` | `0`, `117006328`, `234012664` | all zero at arm; zero later watch hits |
| `70mm` | `1` | `(4416,3312,4416)` | `0`, `29251576`, `58503160` | all zero at arm; zero later watch hits |
| `70mm` | `2` | `(2208,1656,2208)` | `0`, `7312888`, `14625784` | all zero at arm; zero later watch hits |
| `70mm` | `3` | `(1104,828,1104)` | `0`, `1828216`, `3656440` | all zero at arm; zero later watch hits |
| `70mm` | `4` | `(552,414,552)` | `0`, `457048`, `914104` | all zero at arm; zero later watch hits |
| `150mm` | `0` | `(4160,3120,4160)` | `0`, `25958392`, `51916792` | all zero at arm; zero later watch hits |
| `150mm` | `1` | `(2080,1560,2080)` | `0`, `6489592`, `12979192` | all zero at arm; zero later watch hits |
| `150mm` | `2` | `(1040,780,1040)` | `0`, `1622392`, `3244792` | all zero at arm; zero later watch hits |
| `150mm` | `3` | `(520,390,520)` | `0`, `405592`, `811192` | all zero at arm; zero later watch hits |
| `150mm` | `4` | `(260,195,260)` | `0`, `101392`, `202792` | all zero at arm; zero later watch hits |

## Proven Facts

- In the canonical `70mm` and `150mm` bridge HDR tele runs, all five zero-filled ImagePyramid levels can be watched at first/middle/last 8-byte ranges after `0x3b2f59`.
- Across the 30 admitted tele grid cells, each watched 8-byte range is zero at arming time.
- Across the 30 admitted tele grid cells, no watched 8-byte range records a later hardware read/write watchpoint hit before clean render completion.

## Non-Conclusions

- This does not prove whole-buffer read/write absence for the ImagePyramid backing buffers.
- This does not prove no later access occurred through unprobed byte ranges.
- This does not prove absence of data-pointer aliases, generic consumers, or indirect consumers.
- This does not prove final C6 image contribution/exclusion.
- This does not prove terminality of the `0x3c90a5` mutation or absence of alternate C6 routes.

## Next Evidence Path

The remaining C6 closure path is no longer "try one representative data
watchpoint." It is now one of:

- expand sampled byte ranges further if whole-buffer sampling confidence is needed
- prove alias/consumer absence structurally around the zero-filled buffers
- trace non-focused direct `0xf2720` or non-`0xf2720` C6 routes
- prove the mutation/filter/zero-fill chain is terminal for canonical bridge HDR
