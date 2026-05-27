# Bundle Proof: `initResAmp` Per-Key Wrapper Read Path

## Scope

This note proves what the installed `libcp.dylib` exposes about the visible read path of the per-key wrapper pairs stored in `PipelineCache+0x270..+0x280`.

It does not prove the exact upstream N-to-1 reducer behind `src1` / `src2`.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Per-key payload constructor:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3e74e0 --count 280'`
- Per-key wrapper vtable bytes:
  `xxd -g 8 -u -s 0x65f700 -l 0x220 /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Per-key wrapper visible methods:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ece40 --count 260'`
- Per-key wrapper method continuation:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3ed1d0 --count 45'`
- Checked level / ROI tile helper:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d0d20 --count 180'`
- Checked level / ROI tile helper ending and error paths:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d1000 --count 100'`
- ROI extent helper used by the same payload family:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'disassemble --start-address 0x3d0b50 --count 110'`
- Symbol lookups:
  `lldb --batch -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' -o 'image lookup -a 0x65f490' -o 'image lookup -a 0x65f768' -o 'image lookup -a 0x3eced0' -o 'image lookup -a 0x3d0d20'`

## Proven Facts

### 1. The `PipelineCache+0x270` wrapper read path starts from the per-key payload made by `0x3e74e0`

- The prior post-wrapper evidence proved that `0x3e0330` allocates a `0x1f0`-byte object initialized through `0x3e77d0`, and that `0x3e77d0` is a thunk to `0x3e74e0`.
- `libcp+0x3e759e` writes the address point `0x65f490` into the constructed `0x1f0`-byte object.
- `libcp+0x3e75a8..0x3e7622` copies fixed fields from the constructor's stack/input record into the object at offsets including `+0xf8`, `+0xfc`, `+0x100..+0x110`, `+0x118`, `+0x11c`, and `+0x120..+0x140`.
- `libcp+0x3e7631..0x3e7634` initializes a subobject at `object+0x148`.
- `libcp+0x3e766b..0x3e7672` calls `0x3d0c90` on `object+0x10` with a local callback object whose address point is `0x65f4d8`.
- `libcp+0x3e7649..0x3e764e` checks two fields returned through `0xf2750`; if the OR is negative, `0x3e7708..0x3e773c` throws `"Super-res does not support mono modules!"`.
- Therefore the per-key map payload returned later by `0x3e0a60` is a concrete constructed object with fixed copied fields and a callable slot; this constructor body is setup/state work, not reducer closure.

### 2. The `PipelineCache+0x270` wrapper vtable address point is `0x65f768`

- The `initResAmp` wrapper allocation writes address point `0x65f768` into wrapper `+0x20` before storing the wrapper pair into `PipelineCache+0x270..+0x280`.
- The installed vtable bytes around `0x65f768` contain this visible method sequence:
  `0x3ece40, 0x3ece50, 0x3ece60, 0x3ece90, 0x3eceb0, 0x3ecec0, 0x3eced0, 0x3ed200, 0x3ed220`.
- The small methods at `0x3ece40`, `0x3ece50`, `0x3ece60`, `0x3ece90`, `0x3eceb0`, and `0x3ecec0` are no-op, delete, clone, copy, no-op, and delete-shaped plumbing.
- The first substantive visible read-like body in this vtable region is `0x3eced0`.

### 3. `0x3eced0` calls one payload path, then normalizes the destination buffer in place

- `libcp+0x3ecee4` reads one float from wrapper `+0x10`; this is the per-key float copied into the wrapper during the `0x3eb84a..0x3eb8a7` allocation path.
- `libcp+0x3eceed..0x3ecef7` reads the wrapper payload pointer from wrapper `+0x8`, adds `0x10`, sets `ecx = 0`, and calls `0x3d0d20`.
- The call to `0x3d0d20` uses the original destination object in `rsi` and the original third argument in `rdx`; the visible call shape is one payload/subobject path plus destination and ROI-like argument, not a vector of image inputs.
- `libcp+0x3ecefc..0x3ecf14` resizes the destination through `0xf540` using width and height read from destination fields `+0x10/+0x14`.
- `libcp+0x3ecf26..0x3ed1e5` walks the destination pixel buffer through destination fields `+0x10`, `+0x14`, `+0x18`, and `+0x20`.
- The SIMD loop multiplies destination pixel vectors by a vector built from the wrapper float and a shared constant, clamps with `maxps` against zero, applies `sqrtps`, and writes the result back into the same destination buffer.
- `libcp+0x3ed1e5` returns byte `1`.
- Therefore the visible `0x3eced0` body is a one-payload read path followed by in-place square-root normalization.

### 4. `0x3d0d20` is a checked single-payload level / ROI tile path

- `libcp+0x3d0d51..0x3d0d6a` rejects a negative or out-of-range level index; the error path at `0x3d103d` throws `"Requested level is not supported!"`.
- `libcp+0x3d0d70..0x3d0d9d` checks the requested ROI fields for non-negative origin and in-bounds extent; the error path at `0x3d1075` throws `"Requested ROI is out-of-bounds!"`.
- `libcp+0x3d0da3..0x3d0dc9` derives destination dimensions from the checked ROI and calls `0xf540` to size the destination.
- `libcp+0x3d0dd5..0x3d0e55` computes tile bounds from the payload/cache dimensions and the ROI.
- If that tile range is empty, `0x3d10ad` throws `"No tiles in ROI!"`.
- `libcp+0x3d0e5b..0x3d0f28` builds a work-list/callback object around one payload/cache path, the ROI, and the destination.
- `libcp+0x3d0f67..0x3d0f9b` builds a second callback object and dispatches it through the generic executor at `0x5670`.
- The visible `0x3d0d20` body contains checked level/ROI tile scheduling for one payload/cache path. It does not expose N-to-1 image reduction or a multi-source contributor vector.

### 5. `0x3d0b50` is ROI extent arithmetic for the same payload family

- `0x3d0b50` reads dimensions and level/tile indices from its input structures.
- The body computes clamped extents with integer multiplies, compares, conditional moves, and subtractions.
- It writes two 32-bit extent values to its output at `(%rdi)` and `0x4(%rdi)`, then returns that output pointer.
- This supports the same checked ROI/tile framing story. It does not expose reducer math.

## Safe Conclusion

- Proven:
  the visible `PipelineCache+0x270` wrapper read path uses one per-key payload pointer and one per-key float, calls a checked level/ROI tile helper, then applies in-place square-root normalization to the destination buffer.
- Proven:
  the checked helper `0x3d0d20` is bounded to level/ROI validation, destination sizing, tile-range construction, callback setup, and generic executor dispatch for one payload/cache path.
- Still unproven:
  exact reducer body, exact reducer inputs, exact reducer outputs, and exact reducer math behind `src1` / `src2`.

## Consequence For Blocker Work

The `PipelineCache+0x270` per-key wrapper read path should be treated as another exclusion surface for `CLM-PREFUSION-002`. It is now bounded to single-payload ROI/tile processing plus square-root normalization, not reducer closure.
