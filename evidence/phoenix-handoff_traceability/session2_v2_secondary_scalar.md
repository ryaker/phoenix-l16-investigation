# Session 2: V2 Secondary Scalar Consumer — 0x2f16d0

## Target
`DemosaickLightV2<0,0>` at 0x2f0df0 computes `xmm0 = *(r15+0x10) × -0.02f`, stores it to `-0x7c(%rbp)` inside a stack struct `[rbp-0xc0 .. rbp-0x80]`, then calls 0x2f16d0 with:
- `rdi` = `&[rbp-0xc0]` (struct pointer)
- `esi` = image width (`(rbx)[8] - (rbx)[0]`)

The `-0.02 × scalar` float is **stored in the struct at offset +0x44 BEFORE the call**, but 0x2f16d0 itself never reads xmm0 or any floats.

## 0x2f16d0 — Function Identification
**VA range:** 0x2f16d0 – 0x2f17fb (0x12c bytes / ~75 instructions + error tail to 0x2f183f)

**Prologue:** `push rbp; push r14; push rbx; sub rsp, 0x20` — leaf-ish, 3 callee-saved.

**This is NOT an `Image<float>` constructor.** It is a **buffer re-allocator / initializer** for a Halide-style `halide_buffer_t`-alike descriptor. Pseudocode:

```c
void realloc_buffer(buf_t* b /*rdi=rbx*/, int width /*esi*/) {
    b->dims      = 2;                              // [rbx+0x00]
    b->width_pad = width + 4;                      // [rbx+0x04]  (esi+=4)
    b->stride_y  = (width+4) * b->height;          // [rbx+0x0c]
    int ch       = b->channels;                    // [rbx+0x18]
    b->pow2_ch   = next_pow2(ceil(4/ch));          // [rbx+0x10]  bsrl trick
    int bytes    = ceil(width*height*4 / 64) * 64; // 64B-aligned
    b->row_bytes = bytes;                          // [rbx+0x14]
    size_t need  = 4 + bytes*4 * pow2_ch;          // r14
    if (need > b->capacity /*[rbx+0x20]*/) {
        if (b->raw_ptr) free(b->raw_ptr);          // callq 0x7760
        b->raw_ptr = aligned_alloc(64, need);      // callq 0x7720
        if (!b->raw_ptr) throw ...;                // 0x2f17fc tail
        b->capacity = need;
    }
    // Compute aligned data pointer + fill sentinel
    b->data = b->raw_ptr + align_offset;           // [rbx+0x28]
    for (i=0; i<pow2_ch*pow2_ch_hi; i++)
        ((int*)b->data)[i] = 0x7FFFFFFF;           // INT_MAX / +inf-ish sentinel
}
```

Error tail (0x2f17fc–0x2f183f) constructs a `std::runtime_error("std::bad_alloc"-class)` via calls 0x55622a / 0x7820 / 0x556290 / 0x555eac (standard `__cxa_throw` wrap).

## What Happens to the -0.02 × Scalar
**Nothing, inside 0x2f16d0.** The scalar is stashed in the outer struct (offset 0x44 from struct base) and read LATER by downstream Halide-generated code that consumes the buffer descriptor. 0x2f16d0's only job is to size, allocate, and zero-sentinel-fill the float plane — it's setting up the output buffer that a subsequent Halide kernel will populate using the -0.02 scalar as a fixed-point scale factor (consistent with a demosaic edge-weight constant ~`-1/50`, matching AHD-style color-difference smoothing).

## Conclusion for Phoenix
**Phoenix can IGNORE 0x2f16d0.** It is not demosaic math — it is a `halide_buffer_t` realloc+init helper shared across many kernels. The `-0.02 × scalar` itself is a **real demosaic parameter** (stored for downstream Halide stages, NOT consumed here), so:

- **0x2f16d0:** ignore — Phoenix's own buffer allocator replaces this entirely.
- **The -0.02 × `*(r15+0x10)` scalar:** needs replication in the demosaic math kernel proper. It is NOT a padding/bounds-extension value; it is an edge-weight coefficient fed to the subsequent Halide kernel via the buffer descriptor's scalar-param slot at +0x44.

**Next investigation target:** find the Halide kernel that reads `buf->scalar_0x44` — that's where the real -0.02 math lives. Likely one of the kernels called in the loop body at 0x2f0f00–0x2f1491 (0x2f1840 and 0x2f1c00 are strong candidates — they're called 6× per row-pair inside the fusion loop).
