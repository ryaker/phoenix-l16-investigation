# LLDB Evidence: C6/Post-Mutation Rect-Vector Consumer and ImagePyramid Construction

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This probe follows the previously proven post-mutation rect-vector path one consumer step farther. It answers a narrow question: after `0x3c8d00` returns the five-entry rect vector, does the immediate caller consume that vector, and what concrete structure is built from it?

This is not final C6 contribution proof. The wide tiers exercise the same rect-vector/ImagePyramid route, but C6-specific statements in this document apply only to the tele tiers where the prior C6 mutation/state chain was already proven.

## Tested LRIs

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Probe Artifacts

Reusable probe harness:

- `tools/lldb_probes/c6_rect_vector_consumer/c6_rect_vector_consumer_probe.py`
- `tools/lldb_probes/c6_rect_vector_consumer/c6_rect_vector_consumer_28mm.lldb`
- `tools/lldb_probes/c6_rect_vector_consumer/c6_rect_vector_consumer_35mm.lldb`
- `tools/lldb_probes/c6_rect_vector_consumer/c6_rect_vector_consumer_70mm.lldb`
- `tools/lldb_probes/c6_rect_vector_consumer/c6_rect_vector_consumer_150mm.lldb`

Ignored raw outputs:

- `runs/c6_rect_vector_consumer/c6_rect_vector_consumer_28mm.json`
- `runs/c6_rect_vector_consumer/c6_rect_vector_consumer_35mm.json`
- `runs/c6_rect_vector_consumer/c6_rect_vector_consumer_70mm.json`
- `runs/c6_rect_vector_consumer/c6_rect_vector_consumer_150mm.json`

## Static Boundary

Repo-local static inspection of the installed `libcp.dylib` disassembly shows:

- `0x3b237c` reads the first 16-byte tuple from the local vector returned by the earlier `0x3c8d00` call.
- The loop at `0x3b23b0..0x3b29e1` uses five rect tuples and writes context vectors at `context+0x4c0`, `+0x4d8`, `+0x4f0`, `+0x508`, `+0x520`, and `+0x560`.
- `context+0x4c0` holds `(x2 - x1, y2 - y1)` delta dimensions derived from the rect tuples.
- `context+0x520` holds the rect origins `(x1, y1)`.
- `0x3b2a94` calls `0x3982b0` with the `context+0x4c0` delta-dimension vector.
- `0x3982b0` iterates the `(width, height)` pair vector and creates one `CIAPI::Image` per pair through the local image-construction path.
- The returned shared-ptr-like result is stored at `context+0x538`, wrapped through `CIAPI::ImagePyramid` construction, checked with `ImagePyramid::levelCount()`, and then read level-by-level.
- The caller subsequently stores nonzero downstream object pointers at `context+0x6c8`, `+0x678`, `+0x6a8`, `+0x688`, `+0x698`, and `+0x6b8`.

## Runtime Hit Summary

Every canonical seed completed the bridge HDR render under this probe. Every listed site recorded zero LLDB callback read errors.

| Site / event group | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---:|---:|---:|---:|
| `0x3b2339` rect-vector builder call | 1 | 1 | 1 | 1 |
| `0x3b237c` rect-vector return / first tuple load | 1 | 1 | 1 | 1 |
| `0x3b23bf` loop state-code check | 5 | 5 | 5 | 5 |
| `0x3b23d1` loop body entry | 5 | 5 | 5 | 5 |
| `0x3b29e1` loop backedge | 5 | 5 | 5 | 5 |
| `0x3b2a94` call from caller into `0x3982b0` | 1 | 1 | 1 | 1 |
| `0x3982b0` ImagePyramid builder entry | 1 | 1 | 1 | 1 |
| `0x398342` image-level create call | 5 | 5 | 5 | 5 |
| `0x3b2e8b` `ImagePyramid::levelCount()` return | 1 | 1 | 1 | 1 |
| `0x3b2eea` observed level image | 5 | 5 | 5 | 5 |

The final context summary had `context+0x4b0 = 5`, `context+0x4b4 = 512`, `context+0x4b8 = 512`, nonzero `context+0x538` shared-ptr control/pointee, five private ImagePyramid image entries, and nonzero object pointers at `context+0x678`, `+0x688`, `+0x698`, `+0x6a8`, `+0x6b8`, and `+0x6c8` in all four runs.

## Rect Vector To ImagePyramid Values

| Zoom | `0x3c8d00` rect tuples `(x1,y1,x2,y2)` | `context+0x4c0` / `0x3982b0` pairs | Observed ImagePyramid levels `(index,width,height,stride)` |
|---|---|---|---|
| `28mm` | `(0,0,10432,7824)`, `(0,0,5216,3912)`, `(0,0,2608,1956)`, `(0,0,1304,978)`, `(0,0,652,489)` | `(10432,7824)`, `(5216,3912)`, `(2608,1956)`, `(1304,978)`, `(652,489)` | `(0,10432,7824,41728)`, `(1,5216,3912,20864)`, `(2,2608,1956,10432)`, `(3,1304,978,5216)`, `(4,652,489,2608)` |
| `35mm` | `(992,816,9312,7056)`, `(496,408,4656,3528)`, `(248,204,2328,1764)`, `(124,102,1164,882)`, `(62,51,582,441)` | `(8320,6240)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` | `(0,8320,6240,33280)`, `(1,4160,3120,16640)`, `(2,2080,1560,8320)`, `(3,1040,780,4160)`, `(4,520,390,2080)` |
| `70mm` | `(16,16,8848,6640)`, `(8,8,4424,3320)`, `(4,4,2212,1660)`, `(2,2,1106,830)`, `(1,1,553,415)` | `(8832,6624)`, `(4416,3312)`, `(2208,1656)`, `(1104,828)`, `(552,414)` | `(0,8832,6624,35328)`, `(1,4416,3312,17664)`, `(2,2208,1656,8832)`, `(3,1104,828,4416)`, `(4,552,414,2208)` |
| `150mm` | `(2368,1776,6528,4896)`, `(1184,888,3264,2448)`, `(592,444,1632,1224)`, `(296,222,816,612)`, `(148,111,408,306)` | `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`, `(260,195)` | `(0,4160,3120,16640)`, `(1,2080,1560,8320)`, `(2,1040,780,4160)`, `(3,520,390,2080)`, `(4,260,195,1040)` |

For all four zooms, the observed ImagePyramid level dimensions exactly match the `context+0x4c0` delta-dimension pairs passed into `0x3982b0`.

## Additional Context Vectors

| Zoom | `context+0x520` origins | `context+0x4d8` scaled dims | `context+0x4f0` output dims |
|---|---|---|---|
| `28mm` | `(0,0)`, `(0,0)`, `(0,0)`, `(0,0)`, `(0,0)` | `(10432,7824)`, `(5216,3912)`, `(2608,1956)`, `(1304,978)`, `(652,489)` | `(10432,7824)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `35mm` | `(992,816)`, `(496,408)`, `(248,204)`, `(124,102)`, `(62,51)` | `(10432,7824)`, `(5216,3912)`, `(2608,1956)`, `(1304,978)`, `(652,489)` | `(10432,7824)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `70mm` | `(16,16)`, `(8,8)`, `(4,4)`, `(2,2)`, `(1,1)` | `(8896,6672)`, `(4448,3336)`, `(2224,1668)`, `(1112,834)`, `(556,417)` | `(8896,6672)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `150mm` | `(2368,1776)`, `(1184,888)`, `(592,444)`, `(296,222)`, `(148,111)` | `(8896,6672)`, `(4448,3336)`, `(2224,1668)`, `(1112,834)`, `(556,417)` | `(8896,6672)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |

## Proven Facts

- The previously proven tele post-mutation rect-vector builder output is not dead at the return boundary in the canonical `70mm` and `150mm` bridge HDR runs.
- The same rect-vector consumer route is also live in the canonical `28mm` and `35mm` bridge HDR runs; those wide-tier observations are route coverage, not C6 evidence.
- The caller consumes the five returned rect tuples, derives five `context+0x4c0` delta-dimension pairs, and passes those pairs to `0x3982b0`.
- `0x3982b0` builds a five-level ImagePyramid structure from those five pairs.
- `ImagePyramid::levelCount()` returns `5` in all four canonical runs and matches `context+0x4b0 = 5`.
- The returned ImagePyramid shared pointer is stored at `context+0x538`.
- The caller installs downstream nonzero object pointers at `context+0x6c8`, `+0x678`, `+0x6a8`, `+0x688`, `+0x698`, and `+0x6b8` in all four runs.

## Non-Conclusions

- This does not prove C6 contributes to the final rendered image.
- This does not prove C6 is excluded from the final rendered image.
- This does not prove the mutation at `0x3c90a5` is terminal.
- This does not prove absence of alternate C6 routes before, outside, or after this route.
- This does not assign public semantic names to the context offsets.
- This does not close final merge acceptance/rejection or ghost-free parity math.
