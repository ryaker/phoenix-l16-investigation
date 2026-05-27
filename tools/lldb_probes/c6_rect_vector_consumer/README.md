# C6 Rect-Vector Consumer Probe

This probe records the runtime consumer chain after the C6 post-mutation rect vector builder at `libcp+0x3c8d00`.

Scope:

- Capture the rect vector returned to `PropertyAccessor::transform()` at `libcp+0x3b237c`.
- Capture the five-level loop that derives context vectors at `context+0x4c0`, `+0x4d8`, `+0x4f0`, `+0x508`, `+0x520`, and `+0x560`.
- Capture the `ImagePyramid` construction call at `libcp+0x3b2a94` / `libcp+0x3982b0`.
- Capture the created pyramid level dimensions and the immediate downstream context object stores at `+0x678`, `+0x688`, `+0x698`, `+0x6a8`, `+0x6b8`, and `+0x6c8`.

Raw reports are written to ignored `runs/c6_rect_vector_consumer/`.
