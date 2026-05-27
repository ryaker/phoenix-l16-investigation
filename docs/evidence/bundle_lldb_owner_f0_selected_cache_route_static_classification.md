# Bundle + LLDB Owner `+0xf0` Selected-Cache Route Static Classification Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, static disassembly of selected-cache and
post-route bodies already tied to runtime-proven owner `+0xf0` read-context
routes.

This document follows:

- `bundle_lldb_owner_f0_global_route_census.md`
- `bundle_lldb_owner_f0_global_post_route_families.md`
- `bundle_lldb_owner_f0_global_route_ancestry.md`
- `bundle_lldb_owner_f0_parent_chain_static_classification.md`
- `bundle_lldb_owner_f0_helper_surface_static_classification.md`

The prior runtime proofs supply the live route facts: complete bridge HDR
renders at `28mm`, `35mm`, `70mm`, and `150mm` reach read-context branch sites
`0x3d4842` / `0x3d4864`; those hits fall into caller set `{0x3d0732,
0x3d084d, 0x3ecc5a}` and active callable slot set `{0x3ec960, 0x3e4a80}`.
The post-route proof classifies the immediate caller families as exact-size
cleanup, selected-cache read/rescale through `0x36f800`, and visible-`src1`
one-image normalization through `0x3edb80`.

This document is not a new runtime hit-count proof. It is not a final-output
proof. It is a static installed-bundle classification of the selected-cache and
post-route bodies so these bodies do not get mistaken for final contributor
acceptance/rejection policy.

It proves:

- `0x3d01b0` is a level/ROI-checked tile/read executor that fills a
  caller-provided output descriptor through callback/executor plumbing.
- `0x3d0650` is a selected-cache read path. It either performs an exact-size
  read through `0x3d01b0` and exits, or reads into a temporary descriptor and
  calls `0x36f800` with computed offset/scale pairs.
- `0x3d47d0` is a read-context callback branch router. The active callable
  branch invokes a callable and then expansion; the direct branch reaches the
  same expansion body without the callable. The visible else branch is only
  partially captured here and is not fully classified.
- `0x3d4e10` builds clipped source and destination descriptor views, requires
  matching overlap dimensions, and calls `0x3d50f0`.
- `0x3d50f0` / `0x3d5290` set up an executor that expands 6-byte source rows
  into 16-byte `vec4` destination rows.
- `0x2ff00` wraps row conversion, calls `0xc0410` with `ecx = 0`, copies three
  float channels into destination lanes 0..2, and forces lane 3 to `1.0`.
- The used `0xc0410` `cl == 0` branch converts 16-bit channel words to float32
  words. This supports the existing binary16-bit-pattern bound but does not
  prove public pixel-format names.
- `0x3edb80` performs one-image `sqrt(max(src_vec4, floor_vec4))`
  normalization into a 16-byte destination descriptor.

It does not prove:

- final file/display sink
- final contributor acceptance, rejection, or suppression policy
- public names for pixel formats, row channels, offset/scale fields, or cache
  surfaces
- exact semantic meaning of the selected-cache offset/scale pairs
- that every possible caller or route has been classified
- exact semantic contents of visible `src1` or `src2`

## Inputs

Static proof target:

| What | Path |
|---|---|
| `libcp.dylib` | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |

Runtime route dependency:

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable static LLDB script:

- `tools/lldb_probes/static_owner_f0_selected_cache_route_disasm.lldb`

Rerunnable raw LLDB output under ignored `runs/`:

- `runs/static_owner_f0_selected_cache_route/selected_cache_route_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The script creates a static LLDB target from the installed `libcp.dylib`, then
runs `image lookup` plus address-bounded disassembly around selected-cache and
post-route bodies:

- `0x3d01b0`
- `0x3d47d0`
- `0x3d4e10`
- `0x3d50f0`
- `0x2ff00`
- `0xc0410`
- `0x3edb80`

The `0x3d01b0` disassembly window also captures the selected-cache caller body
at `0x3d0650`.

## `0x3d01b0`: Level/ROI Tile Executor

`image lookup --address 0x3d01b0` resolves to an installed-bundle body
beginning at `0x3d01b0` in the raw output lines `5..10`.

The visible body:

- validates the requested level index
- validates requested ROI bounds
- allocates/resizes the caller-provided output descriptor through `0xf540`
- computes tile ranges and a context object
- calls `0x3d45a0`
- builds a callback object
- dispatches executor helpers `0x5440` and `0x5670`
- throws on unsupported level, out-of-bounds ROI, and empty tile ROI

Raw anchors:

| Fact | Raw line |
|---|---:|
| caller output descriptor allocation via `0xf540` at `0x3d0259` | `53` |
| call to `0x3d45a0` | `112` |
| dispatch through `0x5440` | `140` |
| dispatch through `0x5670` | `162` |
| unsupported-level guard text | `209` |
| out-of-bounds ROI guard text | `219` |
| empty tile ROI guard text | `229` |

Safe classification: level/ROI-checked tile/read executor into a
caller-provided descriptor.

Non-closure: this is not final contributor selection, final merge policy, or
final acceptance/rejection.

## `0x3d0650`: Selected-Cache Read Or Read-Then-Rescale

The broad `0x3d01b0..0x3d0950` static window also captures body `0x3d0650`,
which begins in raw output line `293`.

The visible body:

- allocates/resizes the requested output descriptor through `0xf540`
- compares requested dimensions with the selected level dimensions
- for exact-size requests, calls `0x3d01b0` and jumps directly to cleanup
- for non-exact-size requests, computes scale ratios, transforms/rounds/clamps
  the ROI, clears a temporary descriptor, calls `0x3d01b0`, computes
  offset/scale double pairs, and calls `0x36f800`
- destroys only the temporary descriptor after the rescale path

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3d0650` body starts | `293` |
| requested output descriptor allocation through `0xf540` | `315` |
| exact-size cleanup jump at `0x3d0732` | `360` |
| non-exact-size temporary read through `0x3d01b0` at `0x3d0848` | `428` |
| read-then-rescale call to `0x36f800` at `0x3d08ce` | `456` |

Safe classification: selected-cache level/ROI read with two visible families:
exact-size read and read-then-rescale.

This statically supports the already runtime-observed caller-family labels:

- `0x3d0732`: exact-size cleanup family
- `0x3d084d`: selected-cache read/rescale family

Non-closure: this body does not decide contributor acceptance/rejection.

## `0x3d47d0`: Read-Context Callback Branch Router

`image lookup --address 0x3d47d0` resolves to an installed-bundle body
beginning at `0x3d47d0` in raw output line `533`. The captured window also
shows a small thunk at `0x3d4790` that shifts the callback object pointer by
`+0x8` and jumps to `0x3d47d0`.

The visible body:

- calls `0x3d4920` to derive byte flags
- if the active-callable flag is set, calls a vtable slot and then calls
  `0x3d4e10`
- if the direct flag is set, calls `0x3d4e10` directly
- otherwise enters an array/record-copy path whose tail is outside the captured
  range

Raw anchors:

| Fact | Raw line |
|---|---:|
| thunk at `0x3d4790` jumps to `0x3d47d0` | `508` |
| `0x3d47d0` body starts | `533` |
| call to `0x3d4920` | `557` |
| active-callable branch reaches expansion at `0x3d4842` | `567` |
| direct branch reaches expansion at `0x3d4864` | `576` |

Safe classification: read-context branch router.

Partial-body caveat: the else branch is not fully captured here. This document
does not classify that branch beyond the visible setup/copy behavior.

Non-closure: branch routing is not final contributor acceptance/rejection.

## `0x3d4e10`: Clipped Source/Destination View Builder

`image lookup --address 0x3d4e10` resolves to an installed-bundle body
beginning at `0x3d4e10` in raw output line `597`.

The visible body:

- reads the source object from `(%rsi)`
- reads source descriptor-like fields at source offsets around `+0xf0`,
  `+0x100`, `+0x104`, `+0x108`, `+0x110`, and `+0x118`
- clips the source view against caller/source bounds
- computes a source data pointer using 6-byte element addressing
- reads the destination descriptor from `context+0x10`
- clips the destination view against the context destination descriptor
- computes a destination data pointer using 16-byte element addressing
- requires source and destination overlap dimensions to match
- calls `0x3d50f0` only after the size equality checks pass
- throws `"src / dst size mismatch!"` otherwise
- destroys temporary descriptors and returns

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3d4e10` body starts | `597` |
| call to `0x3d50f0` at `0x3d5029` | `737` |
| mismatch guard text | `753` |

Safe classification: clipped source-to-destination view builder and size gate
for the 6-byte-to-16-byte expansion worker.

Non-closure: this is not a final output sink or acceptance/rejection policy.

## `0x3d50f0` / `0x3d5290`: 6-Byte Rows To 16-Byte `vec4` Rows

`image lookup --address 0x3d50f0` resolves to an installed-bundle body
beginning at `0x3d50f0` in raw output line `784`.

The visible setup body:

- allocates/resizes the destination descriptor with element size `0x10`
- builds a callback object
- dispatches executor `0x5670`

The visible row worker at `0x3d5290`:

- computes destination row pointers using 16-byte output stride
- computes source row pointers using 6-byte input stride
- reads the row width from the source descriptor
- calls a converter pointer for each row

Raw anchors:

| Fact | Raw line |
|---|---:|
| destination allocation through `0xf540` at `0x3d5133` | `803` |
| executor dispatch through `0x5670` at `0x3d5184` | `825` |
| row worker `0x3d5290` starts | `924` |
| row converter call through `*(%rax)` at `0x3d52e6` | `950` |

Safe classification: executor setup and row dispatcher for expansion from a
6-byte source descriptor to a 16-byte `vec4` destination descriptor.

Non-closure: this is pixel representation plumbing, not final policy.

## `0x2ff00`: Row Converter Wrapper

`image lookup --address 0x2ff00` resolves to an installed-bundle body beginning
at `0x2ff00` in raw output line `1010`.

The visible body:

- chunks each row into 1024-pixel blocks
- calls `0xc0410` with `ecx = 0` for full chunks and tail chunks
- copies three converted 32-bit float words into destination lanes 0..2
- writes lane 3 as `0x3f800000`, i.e. float `1.0`

Raw anchors:

| Fact | Raw line |
|---|---:|
| full-chunk call to `0xc0410` at `0x2ff85` | `1046` |
| lane 3 forced to `0x3f800000` at `0x2ffc1` | `1061` |
| tail call to `0xc0410` at `0x30025` | `1083` |

Safe classification: row converter wrapper that expands packed three-channel
16-bit source data into 16-byte `vec4` rows with lane 3 forced to `1.0`.

Non-closure: this does not name the public pixel format.

## `0xc0410`: Used `cl == 0` 16-Bit Channel To Float32 Conversion Branch

`image lookup --address 0xc0410` resolves to an installed-bundle body beginning
at `0xc0410` in raw output line `1105`.

The visible body contains multiple branches. The runtime proof for the owner
`+0xf0` downstream consumer observed `ecx/cl = 0`, so this document admits only
the `cl == 0` branch as used by that proven route.

The visible used branch:

- jumps to the `cl == 0` vector path at `0xc05a1`
- loads 16-bit words and widens/masks them in SIMD chunks
- converts assembled values into float32 lanes
- contains a scalar tail beginning at `0xc0800`
- in scalar tail, extracts sign bit 15 into float sign bit 31
- checks low-range/subnormal-like cases against `0x3ff`
- handles normal/high-range cases using threshold `0x7bff`
- writes 32-bit float words

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0xc0410` body starts | `1105` |
| `cl == 0` jump target `0xc05a1` | `1194` |
| scalar tail starts at `0xc0800` | `1327` |
| scalar tail stores 32-bit float word at `0xc0849` | `1347` |

Safe classification: the used branch decodes 16-bit channel words to float32
values. This supports the existing binary16-bit-pattern bound from the reverse
conversion path.

Non-closure: this proof does not assign public pixel-format names, and it does
not admit the nonzero-`cl` branch as used by this route.

## `0x3edb80`: One-Image `sqrt(max())` Normalization

`image lookup --address 0x3edb80` resolves to an installed-bundle body
beginning at `0x3edb80` in raw output line `1516`.

The visible body:

- allocates/resizes a destination descriptor with element size `16`
- reads the wrapped source descriptor
- reads a default/floor vector from wrapper field `+0x10`
- loops over rows and columns
- applies `maxps` with the default/floor vector
- applies `sqrtps`
- stores the normalized `vec4` result into the destination descriptor

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3edb80` body starts | `1516` |
| destination allocation through `0xf540` at `0x3edbba` | `1535` |
| first visible `maxps` / `sqrtps` pair | `1602`, `1603` |
| later vector `maxps` / `sqrtps` pairs | `1648`, `1649`, `1719`, `1720` |
| normal return at `0x3edeb1` | `1740` |

Safe classification: one-image row-wise normalization,
`dst_vec4 = sqrt(max(src_vec4, floor_vec4))`.

Non-closure: this is not contributor acceptance/rejection and is not final
file/display output.

## Canonical Consequence

The owner `+0xf0` selected-cache/post-route layer is now statically bounded as
tile read, branch routing, clipped descriptor expansion, 16-bit channel
conversion, read/rescale, and one-image normalization plumbing.

This narrows the remaining final-policy search: final contributor acceptance,
rejection, or suppression should not be assigned to `0x3d01b0`, `0x3d0650`,
`0x3d47d0`, `0x3d4e10`, `0x3d50f0`, `0x3d5290`, `0x2ff00`, `0xc0410`, or
`0x3edb80` based on the current proof.

The remaining blocker still exists. Public pixel-format names, public
offset/scale semantics, downstream row-image/final policy, and final
acceptance/rejection remain unresolved.
