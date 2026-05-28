# LLDB Evidence: C6/Post-Mutation ImagePyramid Representative Data Watch

**Date:** 2026-05-28
**Status:** admitted negative-scope evidence for `CLM-C6-001`
**Scope:** canonical bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This probe tests the actual backing storage behind the proven zero-filled
`context+0x538` ImagePyramid route. After the zero-fill return site `0x3b2f59`,
it arms a hardware read/write watchpoint on the first `8` bytes of one selected
ImagePyramid level's data pointer, then lets the render continue.

This is stronger than another static callgraph exclusion because it can catch
later reads/writes through aliases or unrecognized helpers. It is still not a
whole-buffer terminality proof: each run watches only one 8-byte range.

## Tested LRIs And Watched Levels

| Zoom | LRI | Unit | Watched level | Watched descriptor `(width,height,stride_pixels)` |
|---|---|---|---:|---|
| `28mm` | `L16_02130` | Unit A | `0` | `(10432,7824,10432)` |
| `35mm` | `L16_03041` | Unit B | `2` | `(2080,1560,2080)` |
| `70mm` | `L16_03434` | Unit A | `2` | `(2208,1656,2208)` |
| `150mm` | `L16_02285` | Unit B | `1` | `(2080,1560,2080)` |

The `35mm`, `70mm`, and `150mm` watched levels were selected because the
previous zero-fill evidence observed nonzero first-32-byte samples immediately
before zero-fill at those levels. The `28mm` zero-fill evidence had all sampled
levels already zero before the call, so level `0` was selected as the full-size
representative.

## Probe Artifacts

Reusable probe harness:

- `tools/lldb_probes/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_probe.py`
- `tools/lldb_probes/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_28mm_l0.lldb`
- `tools/lldb_probes/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_35mm_l2.lldb`
- `tools/lldb_probes/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_70mm_l2.lldb`
- `tools/lldb_probes/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_150mm_l1.lldb`

Ignored raw outputs:

- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_28mm_l0.json`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_35mm_l2.json`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_70mm_l2.json`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_150mm_l1.json`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_28mm_l0.log`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_35mm_l2.log`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_70mm_l2.log`
- `runs/c6_image_pyramid_data_watch/c6_image_pyramid_data_watch_150mm_l1.log`

Each cited log records `Process ... exited with status = 0` and writes its JSON
report.

## Runtime Summary

Every run armed exactly one hardware read/write watchpoint. Every run completed
with process exit status `0`. No run recorded callback errors.

| Zoom | Target level hit at `0x3b2f59` | Watchpoints armed | Watchpoint hits | Initial watched sample after zero-fill |
|---|---:|---:|---:|---|
| `28mm` level `0` | 1 | 1 | 0 | first 32 bytes all zero |
| `35mm` level `2` | 1 | 1 | 0 | first 32 bytes all zero |
| `70mm` level `2` | 1 | 1 | 0 | first 32 bytes all zero |
| `150mm` level `1` | 1 | 1 | 0 | first 32 bytes all zero |

## Proven Facts

- In each of the four canonical bridge HDR runs, the probe reached the selected level's `0x3b2f59` zero-fill return point and armed a hardware read/write watchpoint on that level's data pointer.
- At arming time, the selected level descriptor had `stride_pixels == width`, `origin_ptr == data_ptr`, and a first-32-byte sample of all zeros.
- The watched first `8` bytes of the selected ImagePyramid level data pointer had zero hardware watchpoint hits before render completion in all four runs.

## Non-Conclusions

- This does not prove the whole selected buffer was never read or written.
- This does not prove the other ImagePyramid levels' backing buffers were never read or written.
- This does not prove no later access occurred through a different byte range in the same buffer.
- This does not prove final C6 image contribution/exclusion.
- This does not prove terminality of the `0x3c90a5` mutation or absence of alternate C6 routes.

## Next Evidence Path

To move from representative negative evidence toward terminality proof, repeat
the same hardware-watchpoint method over additional byte ranges:

- first/middle/last ranges for every ImagePyramid level in the tele seeds
- at least one wide-tier control run per sampled range family
- any range that records a hit should be followed by stack classification of
  the hit PC and parent chain
