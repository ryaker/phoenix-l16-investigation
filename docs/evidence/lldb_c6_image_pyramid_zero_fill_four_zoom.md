# LLDB Evidence: C6/Post-Mutation ImagePyramid Zero-Fill Route

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This probe follows the already proven rect-vector/ImagePyramid route one consumer step farther. It answers a narrow question: after the immediate caller builds the five-level `CIAPI::ImagePyramid` at `context+0x538`, does that caller immediately consume the levels, and what does it do with their backing image buffers?

This is not final C6 contribution proof. The wide tiers exercise the same ImagePyramid route, but C6-specific statements in this document apply only to the tele tiers where the prior C6 constructor/mutation/state chain was already proven.

## Tested LRIs

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | Unit B | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Probe Artifacts

Reusable probe harness:

- `tools/lldb_probes/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_probe.py`
- `tools/lldb_probes/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_28mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_35mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_70mm.lldb`
- `tools/lldb_probes/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_150mm.lldb`

Ignored raw outputs:

- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_28mm.json`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_35mm.json`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_70mm.json`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_150mm.json`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_28mm_retry2.log`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_35mm_retry2.log`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_70mm_retry2.log`
- `runs/c6_image_pyramid_zero_fill/c6_image_pyramid_zero_fill_150mm_retry2.log`

Each final `_retry2.log` records `Process ... exited with status = 0` and writes its matching JSON report.

## Static Boundary

Repo-local static inspection of the installed `libcp.dylib` disassembly shows:

- `0x3b2e7a` wraps `context+0x538` as a `CIAPI::ImagePyramid`.
- `0x3b2e86` calls `CIAPI::ImagePyramid::levelCount()`, and the caller compares that count with `context+0x4b0`.
- `0x3b2eb0` indexes each ImagePyramid level.
- `0x3b2ec5`, `0x3b2ed0`, `0x3b2eda`, and `0x3b2ee5` read each level image's `width`, `height`, byte `stride`, and `data` pointer.
- `0x3b2eea..0x3b2f3e` constructs a stack descriptor at `rbp-0x2c0` from that level image. The descriptor covers full image bounds `x0=0`, `y0=0`, `x1=width`, `y1=height`, uses the image data pointer as both `data_ptr` and `origin_ptr`, and converts byte stride to pixel stride for 4-byte elements.
- `0x3b2f45` sets `esi = 4`.
- `0x3b2f54` directly calls `0xf7c0`.
- `0x3b2f59` resumes after that call and then `0x3b2f5c` calls descriptor cleanup helper `0xf4e0`.
- `0xf7c0` reads descriptor data pointer, stride, width, and height. It compares `stride_pixels * bytes_per_pixel` with `width * bytes_per_pixel`; if equal, it calls the bzero-like stub once with `height * stride_pixels * bytes_per_pixel`, otherwise it loops row-by-row.

The runtime descriptors below all have `stride_pixels == width` and `bytes_per_pixel = 4`, so they satisfy the static condition for the contiguous zero-fill branch. The probe intentionally records the direct callsite and after-return state, not hot breakpoints inside global helper `0xf7c0`.

## Runtime Hit Summary

Every canonical seed completed the bridge HDR render under this probe. Every listed site recorded zero LLDB callback read errors.

| Site / event group | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---:|---:|---:|---:|
| `0x3b2abd` `context+0x538` ImagePyramid shared pointer stored | 1 | 1 | 1 | 1 |
| `0x3b2eea` ImagePyramid level image observed | 5 | 5 | 5 | 5 |
| `0x3b2f54` direct zero-fill callsite | 5 | 5 | 5 | 5 |
| `0x3b2f59` after direct zero-fill callsite | 5 | 5 | 5 | 5 |

All twenty `0x3b2f54` callsite packets had `call_target_static = 0xf7c0` and `rsi_bytes_per_pixel = 4`.

## Runtime Descriptor Values

The level image byte stride observed at `0x3b2eea` is `4 * width` in every packet. The descriptor passed at `0x3b2f54` has pixel stride equal to width in every packet.

| Zoom | Descriptor levels `(index,width,height,stride_pixels)` | First 32 bytes before call | First 32 bytes after return |
|---|---|---|---|
| `28mm` | `(0,10432,7824,10432)`, `(1,5216,3912,5216)`, `(2,2608,1956,2608)`, `(3,1304,978,1304)`, `(4,652,489,652)` | all five sampled buffers already zero | all five sampled buffers zero |
| `35mm` | `(0,8320,6240,8320)`, `(1,4160,3120,4160)`, `(2,2080,1560,2080)`, `(3,1040,780,1040)`, `(4,520,390,520)` | level `2` sampled nonzero; levels `0`, `1`, `3`, `4` sampled zero | all five sampled buffers zero |
| `70mm` | `(0,8832,6624,8832)`, `(1,4416,3312,4416)`, `(2,2208,1656,2208)`, `(3,1104,828,1104)`, `(4,552,414,552)` | level `2` sampled nonzero; levels `0`, `1`, `3`, `4` sampled zero | all five sampled buffers zero |
| `150mm` | `(0,4160,3120,4160)`, `(1,2080,1560,2080)`, `(2,1040,780,1040)`, `(3,520,390,520)`, `(4,260,195,260)` | level `1` sampled nonzero; levels `0`, `2`, `3`, `4` sampled zero | all five sampled buffers zero |

For all twenty descriptors:

- `x0 = 0`
- `y0 = 0`
- `x1 = width`
- `y1 = height`
- `field_0x1c = -1`
- `origin_ptr == data_ptr`
- `stride_pixels == width`

The first-32-byte runtime samples are not a full-buffer proof by themselves. The full-buffer zero-fill statement comes from the static `0xf7c0` body combined with the runtime descriptor values that satisfy its contiguous zero-fill condition.

## Proven Facts

- The previously proven `context+0x538` ImagePyramid route is not only built; the caller immediately iterates all five ImagePyramid levels in all four canonical bridge HDR runs.
- For each of the five levels, the caller reads level image `width`, `height`, byte `stride`, and `data`, then constructs a full-image stack descriptor from those values.
- For each of the five descriptors, the caller invokes the direct callsite `0x3b2f54 -> 0xf7c0` with bytes-per-pixel argument `4`.
- Runtime descriptor values satisfy `stride_pixels == width` for all twenty level descriptors, which matches the static contiguous zero-fill condition inside `0xf7c0`.
- The first 32 bytes sampled after return from `0xf7c0` are zero for all twenty level descriptors.
- Three descriptors had nonzero first-32-byte samples immediately before the call and zero first-32-byte samples immediately after return: `35mm` level `2`, `70mm` level `2`, and `150mm` level `1`.

## Non-Conclusions

- This does not prove C6 contributes to the final rendered image.
- This does not prove C6 is excluded from the final rendered image.
- This does not prove the `context+0x538` ImagePyramid buffers are never written after this zero-fill.
- This does not prove the mutation at `0x3c90a5` is terminal.
- This does not prove absence of alternate C6 routes before, outside, or after this route.
- This does not assign public semantic names to the context offsets.
- This does not close final merge acceptance/rejection or ghost-free parity math.
