# Bundle Proof: `StereoLayer<false>::runPass` Cost Path, Four-Zoom Runtime Scope

## Scope

This note extends `bundle_proof_src1_678_virtuals_and_record_consumer.md`.

It proves:

- `0x276790` is the `StereoLayer<false>::runPass(int)` action operator body already located through vtable `0x667cc8`
- `0x276790` dispatches to `0x276860` when `StereoLayer+0xc == 8` and to `0x277e70` otherwise
- `0x276860` and `0x277e70` are static sister worker bodies that build a per-tile state object through `0x275630` and route to projection/sampling cost kernels `0x2730c0` or `0x2732f0`
- `0x275630` is an in-place per-tile state builder, not an exposed N-to-1 reducer
- under the tested bridge HDR path, the canonical `28mm`, `35mm`, `70mm`, and `150mm` LRIs all hit the `0x276790 -> 0x276860 -> 0x275630 -> 0x2732f0` path
- under those same tested full renders, `0x277e70` and `0x2730c0` had zero hits

It does not prove:

- the exact upstream `src1` / `src2` N-to-1 reducer
- full depth/cost algorithm semantics for a clean-room implementation
- that `0x277e70` or `0x2730c0` are dead code outside the tested bridge HDR conditions

## Evidence Inputs

- Static disassembly:
  [tools/libcp_disasm_intel.txt](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/libcp_disasm_intel.txt)
- Runtime binary:
  `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`
- Runtime dylib:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Runtime method:
  `arch -x86_64 lldb` breakpoints on the listed `libcp` VAs, with positive-hit breakpoints capped at 20 hits and zero-hit breakpoints left enabled through full render exit.

## Runtime Test Conditions

All runtime findings in this note are scoped to:

- bridge binary: `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`
- renderer profile: `--profile 3`
- export format: `--export-fmt 3`
- full bridge output: `10432x7824`
- LLDB-launched x86_64 process under Rosetta
- date run: `2026-05-04`

Canonical LRIs tested:

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Correction note: the former `35mm` row used `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`; direct `LightHeader` decode later proved that path is a 98mm tele-tier sample. The `35mm` row above is the corrected true-35mm rerun from `/private/tmp/l16_stereolayer_cost_firsthit_true35/results.json`.

Positive breakpoint counts are capped at `20`; a value of `20` means `>=20`, not exactly 20.

Zero-hit breakpoints in this run were not capped and remained enabled until full render exit.

## Static Proof

### 1. `0x276790` is a mode dispatcher

Disassembly lines:
`tools/libcp_disasm_intel.txt:608230`

`0x276790`:

- loads the captured layer from `function_object+0x8`
- calls the optional callable at `layer+0xb0`; when that callable returns nonzero, the function returns
- reads `layer+0x74`, the captured integer pointer, and another captured pointer
- compares `dword ptr [layer+0xc]` to `8`
- tail-jumps to `0x276860` when equal
- tail-jumps to `0x277e70` otherwise

The branch target addresses are direct disassembly facts:

| Condition | Target |
|---|---:|
| `layer+0xc == 8` | `0x276860` |
| `layer+0xc != 8` | `0x277e70` |

### 2. `0x276860` and `0x277e70` both build per-tile state through `0x275630`

Mode-8 worker `0x276860`:

- starts at `tools/libcp_disasm_intel.txt:608301`
- copies entries from `StereoLayer+0x240/+0x248`
- builds local vectors through helpers including `0x275210` and `0x275470`
- calls `0x26a790`
- allocates and zeroes a temporary buffer sized from `StereoLayer+0x23c`
- calls `0x275630` at `0x276bd4`

Default worker `0x277e70`:

- starts at `tools/libcp_disasm_intel.txt:609507`
- follows the same broad setup shape
- calls `0x275630` at `0x2781cc`

This proves both branch bodies share the same per-tile state-builder spine.

### 3. `0x275630` is an in-place state builder

Disassembly lines:
`tools/libcp_disasm_intel.txt:607157`

`0x275630`:

- writes incoming pointers into output slots `+0x00`, `+0x08`, `+0x10`, and `+0x18`
- initializes a vector at output `+0x28`
- reads a packed input from the stack argument and stores a broadcast pattern at output `+0x40`
- initializes a second vector at output `+0x80`
- verifies matching vector counts before the first push loop
- pushes padded 16-byte records into the `+0x28` vector
- builds packed reciprocal-scale records into the `+0x80` vector
- returns to the caller

The visible body does not read multiple source images and reduce them into one output image. It builds a state object consumed later by the worker.

This function is not the `src1` / `src2` N-to-1 reducer.

### 4. The worker bodies route to `0x2730c0` or `0x2732f0`

Mode-8 worker call sites:

| VA | Target |
|---:|---:|
| `0x27710f` | `0x2730c0` |
| `0x2773dc` | `0x2732f0` |

Default worker call sites:

| VA | Target |
|---:|---:|
| `0x278773` | `0x2730c0` |
| `0x278a57` | `0x2732f0` |

The mode-8 worker sets a flag before the branch:

- `0x276c33`: compares a computed count to `4`
- `0x276c41`: checks `byte ptr [layer+0x20]`
- `0x276cb2`: ANDs those two conditions into the branch flag
- `0x2770e3..0x2770ea`: if that flag is zero, routes to `0x2732f0`; otherwise calls `0x2730c0`

This proves the two cost-kernel entry points are conditional specializations under the worker body.

### 5. `0x2730c0` is a projection/sampling cost specialization that can delegate to `0x2732f0`

Disassembly lines:
`tools/libcp_disasm_intel.txt:604566`

`0x2730c0`:

- reads state vector metadata from `state+0x10`
- if the computed count is greater than `3`, calls `0x2732f0` at `0x273103`
- otherwise allocates a `0x20`-byte temporary coordinate array
- loops over the requested hypothesis count
- reads per-hypothesis scalar data
- combines that scalar with per-record fields and SIMD row records
- performs a perspective-divide pattern
- clamps projected coordinates against per-image bounds
- calls `0x275c70` at `0x27329e`
- writes a 16-bit result to the caller-provided output at `0x2732ba`

This visible body is a projection/sampling cost specialization. It is not the upstream `src1` / `src2` N-to-1 reducer.

### 6. `0x2732f0` is the general projection/sampling cost body

Disassembly lines:
`tools/libcp_disasm_intel.txt:604709`

`0x2732f0`:

- reads state vector metadata from `state+0x10`
- loops over state records
- reads per-record projection rows and image metadata
- reads per-hypothesis scalar data
- performs SIMD multiply/add projection through per-record rows
- performs perspective divide
- clamps projected coordinates against per-image bounds
- bilinear-samples image memory through four neighboring row loads and `pavgb` blending
- accumulates bounded unsigned-byte differences into 16-bit / 32-bit lanes
- writes accumulated 16-bit results through the caller-provided output pointer

This is a per-hypothesis projection/sampling cost body. It is not the upstream `src1` / `src2` N-to-1 reducer.

### 7. `0x275c70` is a bilinear/difference helper

Disassembly lines:
`tools/libcp_disasm_intel.txt:607606`

`0x275c70`:

- converts projected float coordinates to integer/subpixel selections
- loads four neighboring image rows around each projected coordinate
- uses `pavgb`, masks, and shifts to blend subpixel samples
- computes bounded unsigned-byte differences between sampled vectors
- accumulates weighted sums and returns a scalar result

This helper belongs to the projection/sampling cost path.

It is not the upstream `src1` / `src2` N-to-1 reducer.

## Runtime Proof

Breakpoints:

| Label | VA | Cap |
|---|---:|---:|
| `runpass_action_276790` | `0x276790` | `20` |
| `mode8_worker_276860` | `0x276860` | `20` |
| `default_worker_277e70` | `0x277e70` | `20` |
| `pertile_state_builder_275630` | `0x275630` | `20` |
| `projection_cost_count4_2730c0` | `0x2730c0` | `20` |
| `projection_cost_general_2732f0` | `0x2732f0` | `20` |

Runtime result:

| Zoom | Exit | `0x276790` | `0x276860` | `0x277e70` | `0x275630` | `0x2730c0` | `0x2732f0` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `>=20` | `>=20` | `0` | `>=20` | `0` | `>=20` |
| `35mm` | `0` | `>=20` | `>=20` | `0` | `>=20` | `0` | `>=20` |
| `70mm` | `0` | `>=20` | `>=20` | `0` | `>=20` | `0` | `>=20` |
| `150mm` | `0` | `>=20` | `>=20` | `0` | `>=20` | `0` | `>=20` |

Layer-mode samples:

| Zoom | sampled `0x276790` layer pointer | sampled `layer+0xc` | sampled `0x276860` layer pointer | sampled `layer+0xc` |
|---|---:|---:|---:|---:|
| `28mm` | `0x7fefb1a0f710` | `8` | `0x7fefb1a0f710` | `8` |
| `35mm` | `0x7f84c3227190` | `8` | `0x7f84c3227190` | `8` |
| `70mm` | `0x7fba9d713a70` | `8` | `0x7fba9d713a70` | `8` |
| `150mm` | `0x7fbd75111cf0` | `8` | `0x7fbd75111cf0` | `8` |

The runtime results prove that, for the tested canonical bridge HDR quartet, `0x276790` reaches the mode-8 worker and the general projection/sampling cost body.

The runtime zeroes prove only this:

- `0x277e70` had zero hits under these four tested bridge HDR renders.
- `0x2730c0` had zero hits under these four tested bridge HDR renders.

The runtime zeroes do not prove those VAs are dead code.

## Safe Conclusion

The `StereoLayer<false>::runPass(int)` action branch is now bounded further:

- `0x276790` is a branch dispatcher over `layer+0xc`
- the tested bridge HDR quartet enters the `layer+0xc == 8` branch
- that branch reaches `0x276860`
- `0x276860` builds per-tile state through `0x275630`
- the tested bridge HDR quartet reaches `0x2732f0`
- `0x2732f0` is a projection/sampling cost body

This path is not the missing `src1` / `src2` N-to-1 reducer.

The remaining `src1` / `src2` reducer search should not reopen:

- `0x276790`
- `0x276860`
- `0x277e70`
- `0x275630`
- `0x2730c0`
- `0x2732f0`
- `0x275c70`

as closure points unless a future proof directly shows N-to-1 reducer input shape and reducer math at one of those addresses under a different scope.

## Remaining Unknowns

- Exact `src1` / `src2` reducer body, inputs, outputs, and math remain unproven.
- Exact clean-room projection/sampling cost translation for `0x2732f0` remains separate from the merge reducer blocker.
- `0x277e70` and `0x2730c0` remain live code addresses with zero hits only under the tested bridge HDR quartet.
