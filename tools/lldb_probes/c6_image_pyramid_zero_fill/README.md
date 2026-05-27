# C6 ImagePyramid Zero-Fill Probe

Purpose: follow the proven rect-vector/ImagePyramid route one instruction
family farther, from the five `CIAPI::ImagePyramid` levels into the immediate
descriptor zero-fill helper call at `libcp+0x3b2f54 -> libcp+0xf7c0`.

Scope:

- Canonical bridge HDR profile only: `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`.
- Four canonical focal tiers: `28mm`, `35mm`, `70mm`, `150mm`.
- This is route/descriptor proof only. It does not prove C6 final image
  contribution or exclusion.

Captured sites:

- `0x3b2eea`: caller has read one ImagePyramid level's `width`, `height`,
  `stride`, and `data` pointer.
- `0x3b2f54`: caller invokes `0xf7c0` with a stack descriptor made from that
  level image and bytes-per-pixel argument `4`.
- `0x3b2f59`: caller resumes after `0xf7c0`.

The probe intentionally avoids breakpoints inside global helper `0xf7c0`.
That helper is hot outside this route. Static disassembly proves `0x3b2f54`
calls `0xf7c0`; runtime proof is gathered at the direct callsite and immediately
after return.

Ignored raw outputs belong under:

- `runs/c6_image_pyramid_zero_fill/`
