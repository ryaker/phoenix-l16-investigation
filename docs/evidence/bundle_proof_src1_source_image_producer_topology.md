# Bundle Proof: Visible `src1` Source-Image Producer Topology

## Scope

This note bounds the installed-bundle path that produces the source-image
object handed to the already-proven visible-`src1` projection worker.

It builds on:

- [lldb_src1_worker_projection_record_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_worker_projection_record_four_zoom.md)
- [bundle_proof_src1_project_roi_worker.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_project_roi_worker.md)

It proves:

- the deeper visible-`src1` `0x3e2e90` path feeds worker callback field
  `+0x08` from its stack source-image local
- that local is produced through keyed cache helpers and wrapper bodies at
  `0x1bdc80`, `0x1be750`, `0x31af30`, and `0x31acf0`
- `0x31af30` wraps a single source image through ROI clipping and then calls
  `0x33ede0`
- `0x31acf0` validates source size / image-domain compatibility and then calls
  `0x33f480`
- the lower helper family at `0x33ede0`, `0x33f480`, `0x33fb30`, `0x340160`,
  and shared inner body `0x33f180` builds clipped region records and iterates
  vectors of per-source callback objects
- the shared inner body invokes each per-source object's vtable slot `+0x30`
  when object field `+0x20` is non-null

It does not prove:

- the semantic contents of visible `src1`
- the camera identities represented by the source-image producer vectors
- that `0x1be270` is or is not a public `StackFusion` algorithm
- that the per-source virtual callbacks are the final merge/reduction closure
- the exact upstream merge/reduction mechanism behind `src1` / `src2`
- C6 routing
- final merge acceptance / rejection logic

## Bundle + Commands

Binary:

`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

Commands:

```bash
arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x31acf0 --end-address 0x31af30'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x31af30 --end-address 0x31b110'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x1bdc80 --end-address 0x1be850'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x1be270 --end-address 0x1be750'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x33ede0 --end-address 0x340500'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x33f180 --end-address 0x33f500'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x33f480 --end-address 0x33fb30'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x33fb30 --end-address 0x340160'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x31abd0 --end-address 0x31acf0'

arch -x86_64 lldb --batch \
  -o 'target create "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"' \
  -o 'disassemble --start-address 0x318090 --end-address 0x3185a0'
```

## Runtime Link To Visible `src1`

Runtime proof already ties the first captured visible-`src1` worker packet to:

- visible `src1` secondary callable `0x3e4a80`
- handoff into `0x3e2e90`
- callback worker `0x3e4c50`
- source image / output image / default vector / projection record / weight
  table callback fields
- payload-internal projection callable slot `+0x30 = 0x3e42e0`

This note does not re-prove those four-zoom runtime facts. It uses them as the
reason the static producer path below matters.

## `0x3e2e90` Source-Image Local

Existing installed-bundle proof already bounds `0x3e2e90` as the single-object
single-level ROI/process body beneath visible `src1`.

Relevant already-admitted anchors:

- entry arguments are `rdi = payload`, `rsi = output`, `rdx = ROI`, and
  `ecx = level`
- `0x3e2ec2`: rejects `level >= 4`
- `0x3e301d`: computes the per-level subobject as
  `payload + 0x210 + level * 0xa0`
- `0x3e2ffe`: calls `0x1bdc80`
- `0x3e3192`: calls `0x1be750`
- `0x3e3279`: calls `0x31af30`
- `0x3e34e2`: calls `0x31acf0`
- `0x3e3653`: calls `0x31acf0`
- the callback builder later writes the stack source-image local into callback
  field `+0x08`, which runtime proof observes as the source image consumed by
  worker `0x3e4c50`

Safe conclusion: the visible worker's `+0x08` source image is not a free-floating
unknown. It is produced by the `0x3e2e90` source-image local and the helper paths
below. This does not identify semantic `src1` contents.

## Keyed Cache Helper At `0x1bdc80`

`0x1bdc80` is a keyed cache/helper entry used by `0x3e2e90`.

Instruction anchors:

- locks a mutex at object `+0x18`
- searches a tree rooted at object `+0x60` by the incoming key
- missing key throws `Requested camera module not found!`
- calls `0xe78e0` on the object stored at `*(object)`
- one branch calls `0xe6ba0`, `0xf38f0`, `0x1bdfb0`, and `0xf36f0`
- another branch searches the same keyed tree and can call `0x1be270`
- the non-empty tree path returns the node `+0x28/+0x30` shared-ptr-like pair
  into the output pointer

Safe conclusion: `0x1bdc80` is a keyed camera/cache lookup and lazy population
surface. Its exact public class name is not proven by this note.

## Stack-Mode Helper At `0x1be750`

`0x1be750` is another keyed helper reached from `0x3e2e90`.

Instruction anchors:

- checks `0xe78e0(*(object))`
- if the returned count is `<= 1`, throws
  `Gain map not available in non-stack mode.`
- locks object `+0x18`
- searches the same object `+0x60` tree by key
- if the found node payload is empty, calls `0x1be270`
- returns node `+0x38/+0x40` into the output shared-ptr-like pair
- missing key throws `map::at:  key not found`

Safe conclusion: `0x1be750` is stack-mode gated and returns a keyed node
payload distinct from the `0x1bdc80` `+0x28/+0x30` return pair.

## Vector Builder / Updater At `0x1be270`

`0x1be270` is reached from both keyed helper families.

Instruction anchors:

- `0x1be291..0x1be29d`: calls `0xe6ba0` with the object root, a camera index
  argument, and the incoming key
- `0x1be2f3..0x1be300`: calls `0xe78e0` and loops while the loop index is
  below that count
- `0x1be306..0x1be311`: calls `0xe6ba0` for each loop index
- `0x1be316..0x1be37c`: inspects the returned image-like handle and can call
  `0xf38f0` / `0xf36f0`
- `0x1be398..0x1be427`: appends shared-ptr-like pairs into local vectors
- `0x1be4c7..0x1be502`: missing keyed nodes throw `map::at:  key not found`
- `0x1be5ae..0x1be5c5`: calls `0x1b7d80` using a node object, local vectors,
  and the first returned shared-ptr-like pair
- `0x1be5f3..0x1be5fe`: calls `0x1bd1e0` with found node field `+0x38`

Safe conclusion: `0x1be270` loops over the count returned by `0xe78e0`, builds
vectors of shared image-like handles, and updates keyed node state. This note
does not assign it the semantic name `StackFusion`, because that name is not
proven by these instructions alone.

## ROI / RAW-Image Validator At `0x31abd0`

`0x31abd0` validates and clips the source image / ROI inputs used by the wrapper
bodies.

Instruction anchors:

- `0x31abd9..0x31abfe`: rejects an empty source RAW image or non-positive
  dimensions and can throw `empty source RAW image!`
- `0x31ac00..0x31ac3e`: clips the incoming ROI against source dimensions and
  writes an output rect
- `0x31ac5c..0x31ac63`: requires the resulting rect to have positive width and
  height
- `0x31aca9..0x31acd3`: failed positive-area check throws
  `invalid output ROI!`

Safe conclusion: `0x31abd0` is ROI/source-image validation and clipping, not
merge/reduction closure.

## Single-Source Wrapper At `0x31af30`

`0x31af30` is one producer wrapper used by `0x3e2e90`.

Instruction anchors:

- `0x31af4e..0x31af55`: calls `0x3184d0`
- `0x31af5a..0x31af64`: calls `0x31abd0`
- `0x31af6d..0x31af7b`: calls `0x318090`
- `0x31af84..0x31b02f`: builds a clipped source-image region record from the
  source image-like object and clipped ROI
- `0x31b02f..0x31b04b`: zero-initializes another local region/vector record
- `0x31b04b..0x31b067`: passes the prepared records to `0x33ede0`

Call at `0x31b067`:

- `rdi`: object returned by `0x3184d0`
- `rsi`: destination/source-image local passed into `0x31af30`
- `rdx`: shared-ptr-like target returned by `0x318090`
- `rcx`: clipped source-image region record
- `r8`: original source image-like object
- `r9`: clipped output ROI record
- stack argument: zero/default region/vector record

Safe conclusion: `0x31af30` wraps one source image-like object into the lower
producer at `0x33ede0`. It is not, by itself, an exposed merge/reduction formula.

## Source-Size / Domain Wrapper At `0x31acf0`

`0x31acf0` is another producer wrapper used by `0x3e2e90`.

Instruction anchors:

- `0x31ad17..0x31ad38`: requires `r8` rect width/height to match the source
  image dimensions at incoming `rdx+0x10/+0x14`; mismatch throws
  `invalid source size!`
- `0x31ad45..0x31ade0`: if the optional image/region argument is non-empty,
  validates coordinate/domain compatibility against the source image
- `0x31aee9..0x31af15`: failed compatibility throws
  `Bayer/STD image domain mismatch`
- `0x31ade6..0x31ae1d`: calls `0x3184d0`, `0x31abd0`, and `0x318090`
- `0x31ae22..0x31ae41`: calls `0x33f480` with the prepared object,
  destination image local, source image, source region, clipped ROI, and optional
  region data

Safe conclusion: `0x31acf0` validates a source-size and optional-domain
relationship before routing into `0x33f480`. It is a stronger validation wrapper
than `0x31af30`, not an identified final reducer.

## Selector At `0x318090`

`0x318090` selects or constructs the shared-ptr-like object later passed to the
lower producer.

Instruction anchors:

- `0x3180a3..0x3180aa`: checks whether `input+0x38` already contains a target
- `0x3180db..0x3180e1`: if empty, calls `0x318190`
- `0x3180ac..0x318108`: otherwise checks a sensor/type value through `0xf2730`
  and a table-driven branch over `*(input+0x38+0x198)`
- `0x318108..0x318121`: copies `input+0x38/+0x40` into the output
- `0x31812f..0x318159`: invalid cases throw
  `invalid sensor type in stats object!`

Safe conclusion: `0x318090` is selection / construction plumbing for the lower
producer object. It does not expose source-image semantics.

## Lower Producer At `0x33ede0`

`0x33ede0` is reached from `0x31af30`.

Instruction anchors:

- `0x33ee15..0x33eec7`: clips a 16-bit source-image-like region and computes
  a data pointer using stride and `base + index * 2`
- `0x33eee5..0x33eef3`: wraps that region with `0xf340`
- `0x33eef8..0x33efbd`: clips a second image-like region and computes a data
  pointer using `base + index * 4`
- `0x33efc4..0x33efce`: wraps that second region with `0xf340`
- `0x33efd3..0x33f03d`: converts an input rect to floats, selects object vector
  `rdi + 0x880`, and calls shared inner body `0x33f180`
- `0x33f049..0x33f058`: copies the produced local image/result into the caller's
  destination through `0xf840`

Safe conclusion: `0x33ede0` prepares clipped image regions, dispatches through
the shared vector-iteration body, and materializes a destination image/result.

## Shared Per-Source Iterator At `0x33f180`

`0x33f180` is the shared inner body called by multiple lower producers.

Instruction anchors:

- `0x33f1bb..0x33f1c9`: reads a vector begin/end pair from incoming `rsi`
- `0x33f1c9..0x33f24a`: computes per-source integer offsets using adjacent
  vector entries and object fields `+0x30`, `+0x34`, and `+0x38`
- `0x33f270..0x33f279`: for each vector entry, reads the object pointer and
  skips the virtual call if object field `+0x20` is null
- `0x33f2ab..0x33f3bb`: computes scaled input and output rectangle fields and
  writes a per-source record at the output record pointer
- `0x33f3c2..0x33f3e8`: loads object field `+0x20`, then calls that object's
  vtable slot `+0x30`
- `0x33f413..0x33f450`: advances to the next vector entry until the vector end

Safe conclusion: `0x33f180` is a per-source callback iterator. It contains an
important multi-entry loop, but the loop body delegates through per-source
virtual slot `+0x30`; this note does not identify those callback targets or
promote the loop to final merge/reduction closure.

## Lower Producer At `0x33f480`

`0x33f480` is reached from `0x31acf0`.

Instruction anchors:

- `0x33f4bf..0x33f58f`: clips and wraps one image-like region
- `0x33f5a2..0x33f667`: clips and wraps a second image-like region
- `0x33f68d..0x33f77c`: converts caller rect values to floats and computes
  per-source offsets over vector fields at `object+0x460/+0x468`
- `0x33f7e0..0x33f7eb`: iterates that vector and skips entries whose
  object field `+0x20` is null
- `0x33f81e..0x33f939`: computes per-source source/output rectangle fields
- `0x33f941..0x33f94f`: loads object field `+0x20` and calls vtable slot `+0x30`
- `0x33f9cc..0x33f9e2`: copies the produced local image/result into the caller's
  destination through `0xf840`

Safe conclusion: `0x33f480` has the same structural shape as the other lower
producers: region preparation, vector iteration, per-source virtual dispatch,
then destination materialization.

## Sibling Lower Producers

`0x33fb30`, `0x340160`, and `0x3403f0` are sibling bodies in the same family.

Observed facts:

- `0x33fb30` clips one 16-byte-stride image-like region, clips one 4-byte-stride
  image-like region, iterates vector fields at object `+0x10c0/+0x10c8`, and
  calls each per-source object's vtable slot `+0x30` at `0x33ffd4`
- `0x340160` clips a 16-bit image-like region, uses vector fields at
  object `+0xca0`, calls `0x33f180`, and copies only `0x4` bytes into the
  destination through `0xf840`
- `0x3403f0` starts with the same clipped-region preparation shape but was not
  decoded to completion in this note

Safe conclusion: these are related producer surfaces. They strengthen the family
shape, but only the `0x31af30 -> 0x33ede0` and `0x31acf0 -> 0x33f480` edges are
directly tied here to the visible `0x3e2e90` source-image producer path.

## What Is Now Proven

- The visible-`src1` worker source image is produced by a concrete helper stack,
  not by an unnamed opaque blob.
- The helper stack contains keyed cache lookup / lazy population, stack-mode
  keyed gain-map-style access, ROI/source validation, lower region producer
  wrappers, and a per-source callback iterator.
- The lower producer family has real multi-entry vector loops, but its visible
  body delegates per-source work through vtable slot `+0x30`.

## What Remains Unknown

- Which per-source callback vtables and slot targets are used at the
  `0x33f180`, `0x33f480`, and sibling virtual call sites during the canonical
  four-zoom bridge HDR renders.
- Whether those callback targets contain the still-missing upstream
  merge/reduction behavior or only more projection/materialization work.
- The camera membership and semantic payload contents represented by the
  source-image producer vectors.
- The exact relation, if any, between this source-image producer family and C6
  tele routing.

## Next Proof Path

The next clean proof step is runtime capture of the per-source virtual-call
targets reached from the visible `src1` path:

- `0x31af30` / `0x31acf0` branch participation per canonical zoom
- `0x33f3e8` inside `0x33f180`
- `0x33f94f` inside `0x33f480`
- `0x33ffd4` inside `0x33fb30` if that sibling body is reached

The capture should record:

- caller backtrace proving visible-`src1` ancestry
- object pointer
- object `+0x20`
- vtable address point for object `+0x20`
- vtable slot `+0x30` target
- vector begin/end count
- branch/site identity
- zoom and LRI path

Only after those targets are known should this branch be classified as reducer,
non-reducer, or distributed selection/materialization.
