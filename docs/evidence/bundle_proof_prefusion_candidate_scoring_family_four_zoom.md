# Bundle Proof: Prefusion Candidate-Scoring Family, Four-Zoom Runtime

## Scope

This note extends the prefusion merge/reduction exclusion chain below the sampled callable gate.

It proves only the installed-bundle and four-zoom bridge HDR facts for:

- `0x24c320`
- `0x24d610`
- local scoring helpers `0x24cf90`, `0x24e070`, and `0x24e350`
- the runtime split observed on the corrected canonical `28mm`, `35mm`, `70mm`, and `150mm` LRIs

It does not prove that the exact `src1` / `src2` pre-fusion merge/reduction mechanism has been found.

## Bundle + Commands

- Binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Runtime probe artifact:
  `/private/tmp/l16_prefusion_candidate_scoring_probe/results.json`
- Corrected true-35mm runtime artifact:
  `/private/tmp/l16_prefusion_candidate_scoring_probe_true35/results.json`
- Runtime probe command:
  `arch -x86_64 lldb -b -s /private/tmp/l16_prefusion_candidate_scoring_probe.lldb`
- Static disassembly source:
  `tools/libcp_disasm_intel.txt`
- Static regions inspected:
  `0x24c320..0x24cf8d`, `0x24cf90..0x24d500`, `0x24d610..0x24e068`, `0x24e070..0x24e74c`, `0x255840..0x255b61`

## Runtime Scope

The LLDB run used the canonical bridge HDR quartet and rendered full `10432x7824` HDR outputs through:

`tools/lri_process <lri> <out.hdr> --profile 3 --export-fmt 3`

All four runs exited `0`.

Breakpoints with hit counts equal to their configured cap are lower bounds. Breakpoints below cap are exact for this run.

| Zoom | LRI | Exit | `0x24c320` entry | `0x24d610` entry | `0x24cf90` helper | `0x24e070` helper | `0x24e350` helper |
|---|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `>=50` | `0` | `>=20` | `0` | `0` |
| `35mm` | `L16_03041` | `0` | `>=50` | `0` | `>=20` | `0` | `0` |
| `70mm` | `L16_03434` | `0` | `0` | `>=50` | `>=20` | `>=20` | `>=20` |
| `150mm` | `L16_02285` | `0` | `0` | `14` | `>=20` | `>=20` | `11` |

Correction note: the former `35mm` row used `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`; direct `LightHeader` decode later proved that path is a 98mm tele-tier sample. The `35mm` row above is the corrected true-35mm rerun from `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`.

Important scope note:

- `0x24cf90` is a shared helper. Static call-site search shows calls at `0x24cd81`, `0x24ead0`, `0x24ec36`, and `0x24f037`.
- Therefore a `0x24cf90` runtime hit does not by itself prove that the `0x24c320` entry body fired.
- The four-zoom routing claim above is based only on entry breakpoints at `0x24c320` and `0x24d610`.

## Proven Static Facts

### 1. `0x24c320` is a candidate scorer and 0x2c-byte record writer

`0x24c320` starts from an object pointer and candidate index.

Visible structure:

- `0x24c339` loads state from object offset `+0x00`.
- `0x24c33c..0x24c354` reads `state+0x220`, calls vtable slot `+0x30`, and exits early if the gate returns true.
- `0x24c35a..0x24c376` reads the candidate coordinate pair from the vector at object offset `+0x08`; the stride arithmetic is `index + 8*index`, then `4 * (...)`, i.e. `0x24` bytes per record.
- `0x24c379..0x24c39a` bounds-checks that candidate pair against a rectangle loaded from object offset `+0x10`.
- `0x24c3a0..0x24c4b4` projects two related coordinate positions through scale/matrix fields at object offsets `+0x20`, `+0x28`, and `+0x30`.
- `0x24c4b8..0x24c50a` bounds-checks the projected positions against the rectangle at object offset `+0x38`.
- `0x24c554..0x24c7d0` copies a local multi-row window from the image/map object at object offset `+0x48` into stack storage.
- `0x24c814` calls `0x255880` to build a step / search descriptor from two coordinate pairs and a rectangle.
- `0x24c9d0..0x24ca6a` scans local 0x100-byte windows with SIMD byte-difference scoring, then tracks best and second-best scores / coordinates.
- `0x24cb23..0x24cb4f` writes a sentinel output record with packed `-1.0` float fields and state `1`.
- Valid output paths at `0x24ce50..0x24cea9` and `0x24cf11..0x24cf55` write a `0x2c`-byte record into the vector at object offset `+0x18`.

The visible output record fields are:

- `+0x00`: candidate / record index
- `+0x04`, `+0x08`: source or local coordinate floats
- `+0x0c`, `+0x10`: projected / candidate coordinate floats
- `+0x14`, `+0x18`: integer coordinate pair
- `+0x1c`, `+0x20`: scalar scores
- `+0x24`: classification / state code
- `+0x28`: secondary classification / mode code

Therefore the visible body is candidate scoring plus fixed-record output. It is not an exposed multi-image merge/reduction body.

### 2. `0x24d610` is a sibling candidate scorer and 0x2c-byte record writer

`0x24d610` has the same broad shape as `0x24c320`, but with a different object layout and a deeper search helper path.

Visible structure:

- `0x24d638` loads state from object offset `+0x00`.
- `0x24d63b..0x24d653` reads `state+0x220`, calls vtable slot `+0x30`, and exits early if the gate returns true.
- `0x24d659..0x24d676` reads the candidate coordinate pair from object offset `+0x08`, again using `0x24`-byte stride arithmetic.
- `0x24d679..0x24d6d2` applies two-stage bounds checks using rectangles / offsets at object offsets `+0x18`, `+0x10`, and `+0x20`.
- `0x24d6d8..0x24d811` projects the candidate through scale/matrix fields at object offsets `+0x30`, `+0x38`, and `+0x40`, then derives a normalized direction / distance value.
- `0x24d835..0x24dabd` copies a local multi-row window from the object at offset `+0x50` into stack storage.
- `0x24daf0..0x24db45` accumulates local window sums.
- `0x24dbee` calls `0x255880`.
- `0x24dc0c` calls `0x24e070`, which performs a local search and returns a best pair plus scores.
- `0x24de55` conditionally calls `0x24e350`, which builds another local patch descriptor and calls `0x24e070` internally.
- `0x24dc45..0x24dc79` writes the sentinel `0x2c`-byte record to the output vector at object offset `+0x28`.
- Valid output paths at `0x24df2c..0x24df87` and `0x24dffd..0x24e031` write the same `0x2c`-byte record shape as the `0x24c320` family.

Therefore `0x24d610` is also candidate scoring plus fixed-record output, not exposed merge/reduction closure.

### 3. `0x255880` builds a coordinate-step descriptor, not a merge/reduction body

`0x255880` is called by both scorer families.

Visible structure:

- It receives a rectangle and two coordinate pairs.
- It tests whether both pairs are in bounds.
- It computes deltas, absolute / normalized direction components, and step count fields.
- It writes a small descriptor to the output pointer at offsets `+0x00..+0x1c`.
- Failure paths zero that descriptor.

It has no visible image-buffer traversal or multi-source accumulation.

### 4. `0x24cf90`, `0x24e070`, and `0x24e350` are local patch/search scoring helpers

`0x24cf90`:

- initializes the best-pair output to `-1`
- copies an 8-row local patch / window from an image/map object into caller-provided storage
- accumulates local byte sums with SIMD instructions
- scans candidate windows, computes byte-difference scores, and updates best coordinate / score outputs

`0x24e070`:

- initializes its best-pair output to `-1`
- walks a search rectangle described by the caller
- compares 0x100-byte local windows with SIMD byte-difference / absolute-difference scoring
- updates best coordinate and best / second-best score fields

`0x24e350`:

- builds a larger local patch descriptor from image/map rows
- accumulates local patch sums
- clamps a search rectangle
- calls `0x24e070`
- returns the nested best pair and scores to its caller

These helpers score local image / map patches and candidate positions. They do not expose multi-camera image generation or merge/reduction math.

## Runtime Samples

The runtime probe captured concrete candidate / score samples:

- `28mm` entry samples at `0x24c320` used candidate vector offset `+0x08`, bounds rect `[4, 4, 253, 191]`, output vector offset `+0x18`, and `state+0x220 == state+0x200`.
- `28mm` `0x24cf90` return samples produced best pairs such as `[154, 12]`, `[89, 24]`, and `[62, 40]`, with float score pairs such as `3.6614585 / 3.984375`.
- `35mm` entry samples at `0x24c320` used candidate vector offset `+0x08`, bounds rect `[4, 4, 254, 191]`, output vector offset `+0x18`, and `state+0x220 == state+0x200`.
- `35mm` `0x24cf90` return samples produced best pairs such as `[163, 15]`, `[79, 40]`, and `[80, 50]`, with float score pairs such as `5.265625 / 9.755208969116211`.
- `70mm` and `150mm` entry samples at `0x24d610` used candidate vector offset `+0x08`, output vector offset `+0x28`, and `state+0x220 == state+0x200`.
- `70mm` and `150mm` `0x24e070` / `0x24e350` return samples produced best-pair and score outputs, for example `70mm` `[79, 16]` with score pair `[2283, 2323]`, and `150mm` `[154, 100]` with score pair `[340, 686]`.

These runtime samples confirm the static interpretation: the observed work is candidate scoring / local search / fixed-record output.

## Safe Conclusion

- Proven:
  under the tested full bridge HDR renders, the `28mm` canonical LRI reached `0x24c320` and did not reach `0x24d610`.
- Proven:
  under the tested full bridge HDR renders, the corrected true-`35mm` canonical LRI reached `0x24c320` and did not reach `0x24d610`.
- Proven:
  under the tested full bridge HDR renders, the `70mm` and `150mm` canonical LRIs reached `0x24d610` and did not reach `0x24c320`.
- Proven:
  `0x24c320` and `0x24d610` are candidate scorer / fixed-record writer bodies over `0x24`-stride candidate inputs and `0x2c`-stride output records.
- Proven:
  `0x24cf90`, `0x24e070`, and `0x24e350` are local patch/search scoring helpers.
- Still unproven:
  the exact `src1` / `src2` pre-fusion merge/reduction mechanism, inputs, outputs, and math.

## Consequence For Blocker Work

Future anchor pre-fusion work should not cite `0x24c320`, `0x24d610`, `0x24cf90`, `0x24e070`, or `0x24e350` as merge/reduction closure.

The merge/reduction blocker remains elsewhere and may only close when a surface is proven to have real multi-camera input shape, distributed merge/reduction behavior, or equivalent reduction math.

Additional proven caution:

- static call-site search shows `0x24cf90` is called by bodies outside `0x24c320`
- this note does not decode or bound every caller of `0x24cf90`
- helper hits must not be promoted into entry-body hits without an entry breakpoint
