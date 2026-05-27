# Bundle + LLDB Owner `+0xf0` Helper-Surface Static Classification Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, static disassembly of helper surfaces exposed
by the already proven owner `+0xf0` read-context parent-chain route.

This document follows:

- `bundle_lldb_owner_f0_global_route_ancestry.md`
- `bundle_lldb_owner_f0_parent_chain_static_classification.md`

The prior ancestry proof supplies the runtime fact: complete bridge HDR renders
at `28mm`, `35mm`, `70mm`, and `150mm` reach the parent chains from read-context
branch sites `0x3d4842` / `0x3d4864`. The parent-chain static classification
then bounds the immediate bodies. This document classifies selected helper
surfaces beneath those bodies.

It is not a new runtime hit-count proof. It is not a final-output proof. It is a
static installed-bundle classification intended to prevent route-plumbing helper
bodies from being mistaken for final merge policy.

It proves:

- `0x31b110` is a source image / source RAW / optional STD domain adapter into
  `0x33fb30`. It checks source/RAW/STD availability and domain compatibility,
  prepares ROI/default fields, and calls `0x33fb30`. It is not the final merge
  reducer or final acceptance/rejection policy.
- `0xfe720` allocates and fills a vector of 16-byte rectangle/ROI records from
  source rectangle, clip rectangle, and scale fields. It is a geometry/grid
  helper, not image merge or acceptance logic.
- `0x106cb0` is a vignetting-data Optional/tree reader plus float-buffer
  interpolation/normalization constructor. It is not contributor selection,
  final output, or final acceptance/rejection.
- `0x33fb30`, `0x340160`, and `0x3403f0` are source/region descriptor-prep
  helper surfaces. The captured `0x33fb30` and `0x3403f0` windows are partial
  static bodies, so this proof only classifies the visible prefix behavior.
- `0x2e20` is a generic callback/executor dispatch helper.
- `0xf3570` and nearby siblings are captured-image owner accessors.
- `0x3b9660` maps ROI coordinates to tile bounds and rejects empty tile ROIs.
- `0x3c6ac0` itself returns `owner+0xa0`; the adjacent switch helper must not be
  conflated with direct calls to `0x3c6ac0`.
- `0x1bea20`, `0x1bea00`, and `0x1be970` are small field-copy / map-key /
  shared-object lookup helpers.
- The inspected `0xf540` prefix continues to support the prior `CLM-WARP-001`
  result: it resizes/clears descriptors and is not the packed pair-grid writer.

It does not prove:

- exact semantic contents of visible `src1` or `src2`
- final file/display sink
- downstream row-image/final policy after the classified caller/helper families
- final contributor acceptance, rejection, or suppression policy
- public names for fields, weights, offsets, or pixel formats
- that no reducer or final policy exists elsewhere

## Inputs

Static proof target:

| What | Path |
|---|---|
| `libcp.dylib` | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |

Runtime ancestry dependency:

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable static LLDB script:

- `tools/lldb_probes/static_owner_f0_helper_surface_disasm.lldb`

Rerunnable raw LLDB output under ignored `runs/`:

- `runs/static_owner_f0_helper_surface/helper_surface_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The script creates a static LLDB target from the installed `libcp.dylib`, then
runs `image lookup` plus address-bounded disassembly around helper surfaces
exposed by the parent-chain classification:

- `0x31b110`
- `0xfe720`
- `0x106cb0`
- `0x33fb30`
- `0x340160`
- `0x3403f0`
- `0x2e20`
- `0xf3570`
- `0x3b9660`
- `0x3c6ac0`
- `0x1bea20`
- `0x1bea00`
- `0x1be970`
- `0xf540`

## `0x31b110`: Source/RAW/STD Adapter Into `0x33fb30`

`image lookup --address 0x31b110` resolves to an installed-bundle body beginning
at `0x31b110` in the raw output lines `5..10`.

The visible body:

- saves incoming arguments from `rdi`, `rsi`, `rdx`, `rcx`, `r8`, and `r9`
- validates source image availability
- validates source RAW image availability
- validates optional STD image domain compatibility
- computes ROI/default fields from the `r8`/`r12` record fields
- calls descriptor helper `0x318090`
- calls `0x33fb30` at `0x31b344`

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x31b110` body starts | `10` |
| `0x31b344` calls `0x33fb30` | `138` |
| empty source-image guard | `158` |
| empty source-RAW guard | `167` |
| Input/STD domain-mismatch guard | `190` |

Safe classification: source image / source RAW / optional STD domain adapter
into `0x33fb30`.

Non-closure: this is not final contributor selection, not final merge policy,
and not final acceptance/rejection.

## Nearby `0x31b470` Wrapper

The adjacent body begins at `0x31b470` in the broad `0x31b650..0x31baa0`
window. It prepares source/ROI state and dispatches to one of two helper
variants:

- `0x340160` at raw line `246`
- `0x3403f0` at raw line `252`

Safe classification: related source/ROI wrapper. It is a neighbor in the same
helper range and should not be treated as the exact `0x3bb822` call target
unless a runtime or caller proof names it.

## `0xfe720`: 16-Byte Rectangle/ROI Record Grid Builder

`image lookup --address 0xfe720` resolves to an installed-bundle body beginning
at `0xfe720` in raw lines `682..687`.

The visible body:

- derives width and height from an input rectangle
- clears the output vector at `rdi`
- allocates `width * height * 16` bytes
- initializes each 16-byte record to zero
- reads scale floats from `r8`
- converts scaled bounds to integers
- clamps bounds against the clip rectangle in `rdx`
- writes four int32 fields per 16-byte record
- carries edge fields between neighboring records

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0xfe720` body starts | `687` |
| allocation call after size calculation | `720` |
| main loop branches to return/finish region | `771` |
| scaled-bound conversion begins in visible loop | `799` |
| normal return region starts | `939` |

Safe classification: rectangle/ROI record-grid construction and clamping.

Non-closure: this body does not inspect image pixels and does not implement
final merge acceptance/rejection.

## `0x106cb0`: Vignetting Data Constructor / Interpolator

`image lookup --address 0x106cb0` resolves to an installed-bundle body beginning
at `0x106cb0` in raw lines `991..996`.

The visible body:

- initializes destination descriptor/object fields
- repeatedly calls owner accessor `0xf3570`
- checks Optional-present flags before reading data
- copies dimensions and payload fields from Optional/tree nodes
- allocates float buffers
- initializes buffers through zeroing / `memset_pattern16`
- performs linear interpolation between float buffers
- performs normalization/division transforms over float buffers
- throws on empty Optionals and invalid vignetting data sizes

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x106cb0` body starts | `996` |
| first visible call to `0xf3570` | `1017` |
| repeated calls to `0xf3570` | `1026`, `1046`, `1056`, `1069`, `1100`, `1125` |
| empty Optional guards | `1843`, `1852`, `1861`, `1922`, `1931`, `1947`, `1956` |
| invalid vignetting-data guards | `1874`, `1883`, `1984` |

Safe classification: vignetting-data Optional/tree reader plus float-buffer
interpolation/normalization constructor.

Non-closure: this body does not prove contributor acceptance/rejection or final
row-image/output policy.

## `0x33fb30`: Descriptor Clipping / Region Prep Prefix

`image lookup --address 0x33fb30` resolves to an installed-bundle body beginning
at `0x33fb30` in raw lines `1986..1991`.

The captured prefix:

- initializes multiple local descriptor blocks to zero
- clips a first descriptor to nonnegative bounds
- derives shifted data pointers from source dimensions/stride/data fields
- wraps/destroys adjusted descriptors through `0xf340` / `0xf4e0`
- clips a second descriptor similarly
- begins reading vector-like records from offsets near `0x10c0..0x10c8`
- starts a loop using reciprocal of a record field

Safe classification: descriptor clipping / region preparation prefix with
record-table setup.

Partial-body caveat: the captured static range ends at `0x33fe00`, so this
document does not classify the entire body.

## `0x340160`: Two-Byte Source Descriptor Region Adapter

`image lookup --address 0x340160` resolves to an installed-bundle body beginning
at `0x340160` in raw lines `2143..2148`.

The visible body:

- zeros a local descriptor/work area
- clips a descriptor from an input source descriptor
- builds a 2-byte-element adjusted descriptor
- converts an int rectangle to floats
- calls shared iterator/helper `0x33f180`
- calls `0xf840` with element size `4`
- destroys temporary wrappers through `0xf4e0`

Safe classification: 2-byte source descriptor region adapter feeding shared
per-source iterator work.

Non-closure: this is not final merge policy.

## `0x3403f0`: Alternate Region Helper Prefix

`image lookup --address 0x3403f0` resolves to an installed-bundle body beginning
at `0x3403f0` in raw lines `2310..2315`.

The captured prefix:

- follows the same broad clipping/descriptor-prep shape as `0x340160`
- reads vector records from offsets near `0x14e0..0x14e8`
- computes row/offset values using reciprocal fields

Safe classification: alternate source/region helper prefix with record-based
row/offset preparation.

Partial-body caveat: the captured static range ends at `0x340650`, so this
document does not classify the entire body.

## `0x2e20`: Callback / Executor Dispatch Helper

`image lookup --address 0x2e20` resolves to an installed-bundle body beginning
at `0x2e20` in raw lines `2445..2450`.

The visible body:

- allocates a callback object when the owner branch is present
- calls helper `0x37c0`
- can invoke callback vtable slot `+0x28`
- otherwise invokes callback vtable slot `+0x30` through supplied callback
  objects
- has a loop form that repeatedly invokes slot `+0x30`

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x2e20` body starts | `2450` |
| callback object allocation | `2470` |

Safe classification: generic callback/executor dispatch helper.

Non-closure: no pixel math, merge policy, or acceptance/rejection is proven
inside this helper.

## `0xf3570`: Captured-Image Owner Accessor Family

`image lookup --address 0xf3570` resolves to an installed-bundle body beginning
at `0xf3570` in raw lines `2535..2540`.

The visible body:

- reads owner pointer `object+0xa0`
- if present, calls an owner method with `object+0x60`
- if absent, throws the captured-image owner guard

Nearby siblings repeat the same shape with different owner methods, and one
neighbor returns `object+0x1d8`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0xf3570` body starts | `2540` |
| owner-missing guard | `2557`, `2589`, `2620` |

Safe classification: captured-image owner accessor family.

## `0x3b9660`: ROI-To-Tile Bounds Helper

`image lookup --address 0x3b9660` resolves to an installed-bundle body beginning
at `0x3b9660` in raw lines `2650..2655`.

The visible body:

- divides ROI coordinates by tile-size fields
- clamps tile bounds against per-level dimensions
- writes four int32 tile-bound fields to the destination
- throws on empty tile ROI

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3b9660` body starts | `2655` |
| empty tile ROI guard | `2722` |

Safe classification: ROI-to-tile bounds helper.

## `0x3c6ac0`: Direct Owner Field Accessor

`image lookup --address 0x3c6ac0` resolves to an installed-bundle body beginning
at `0x3c6ac0` in raw lines `2735..2740`.

The body at `0x3c6ac0` itself:

- computes `owner+0xa0`
- returns

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3c6ac0` body starts | `2740` |
| `leaq 0xa0(%rdi), %rax` | `2742` |

The adjacent `0x3c6ad0` body is a larger lock/switch/Optional helper and
contains an empty Optional guard at raw line `2811`, but direct-render calls to
`0x3c6ac0` must not be described as if they executed the neighboring switch
body.

Safe classification for `0x3c6ac0`: direct `owner+0xa0` field accessor.

## `0x1bea20`, `0x1bea00`, `0x1be970`: Field-Copy / Map-Key / Lookup Helpers

`0x1bea20` begins at raw lines `2829..2834`. The visible body copies three
int32 fields from offsets `+0x74`, `+0x78`, and `+0x7c` into the destination.

`0x1bea00` begins at raw lines `2886..2891`. The visible body loads `*rdi` and
tailcalls helper `0xe6cf0`.

`0x1be970` begins at raw lines `2905..2910`. The visible body calls `0xe6ba0`
with a pointer plus key-like fields, checks that a resulting pointer is present,
and throws on invalid image pointer.

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x1bea20` body starts | `2834` |
| `0x1bea00` body starts | `2891` |
| `0x1be970` body starts | `2910` |
| invalid image pointer guard | `2933` |

Safe classification: small field-copy, map-key, and shared-object lookup
helpers.

## `0xf540`: Descriptor Resize/Clear Prefix, Not Pair-Grid Writer

The captured `0xf540` prefix appears at raw lines `2951..3025`. It resizes or
clears descriptor storage using target dimensions from `rsi`, handles zero
dimensions and existing storage, and does not show packed pair writes.

Safe classification: descriptor allocation/resize prefix. This reinforces the
existing `CLM-WARP-001` claim that `0xf540` is not the dst-coordinate pair-grid
writer.

Partial-body caveat: the captured range ends at `0xf620`.

## Canonical Consequence

This proof removes several attractive but wrong next-search targets from the
final-policy lane:

- `0x31b110` is adapter/prep into `0x33fb30`.
- `0xfe720` is rectangle-grid construction.
- `0x106cb0` is vignetting-data construction/interpolation.
- `0x2e20` is callback dispatch.
- `0xf3570`, `0x3b9660`, `0x3c6ac0`, `0x1bea20`, `0x1bea00`, and `0x1be970`
  are owner/tile/map/field helper surfaces.

The remaining final-policy search should move downstream or sideways from these
classified helper surfaces, not repeatedly re-open them as reducer candidates.
