# Bundle Proof: `StereoLayer<false>::compute()` Cost Sibling, Four-Zoom Runtime Scope

## Scope

This note extends:

- `bundle_proof_src1_678_virtuals_and_record_consumer.md`
- `bundle_proof_stereolayer_runpass_cost_path_four_zoom.md`

It proves:

- the installed function-object vtable at address point `0x667c28` is a `StereoLayer<false>::compute()` lambda with operator slot `+0x30 = 0x274b10`
- `0x274b10` tail-jumps into worker body `0x2727f0` after loading the captured layer pointer from `function_object+0x8`
- static worker body `0x2727f0` is a sibling cost/projection body that shares the `0x275630` state builder and `0x2730c0` / `0x2732f0` projection-cost targets
- under complete `--no-auto-lris` bridge HDR renders of the canonical `28mm`, `35mm`, `70mm`, and `150mm` LRIs, the `0x274b10 -> 0x2727f0` compute-lambda surface and its adjacent setup helpers had zero hits
- the same runs hit the `StereoLayer<false>::runPass(int)` controls `0x276790 -> 0x276860 -> 0x2773dc -> 0x2732f0`, proving the probe was attached to live StereoLayer cost activity

It does not prove:

- that `0x2727f0`, `0x272100`, or `0x272640` are dead code outside the tested bridge HDR / no-auto-LRIS path
- that `0x276790`, `0x276860`, `0x2732f0`, or any sibling cost body is the `src1` / `src2` merge/reduction closure
- full clean-room depth/cost semantics for `StereoLayer<false>`
- the exact pre-fusion merge/reduction mechanism behind `src1` / `src2`

## Evidence Inputs

- Static disassembly:
  [tools/libcp_disasm_intel.txt](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/libcp_disasm_intel.txt)
- Runtime probe:
  [tools/lldb_probes/stereolayer_compute_cost_path/stereolayer_compute_cost_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_compute_cost_path/stereolayer_compute_cost_probe.py)
- LLDB scripts:
  [compute_cost_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_compute_cost_path/compute_cost_28mm.lldb)
  [compute_cost_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_compute_cost_path/compute_cost_35mm.lldb)
  [compute_cost_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_compute_cost_path/compute_cost_70mm.lldb)
  [compute_cost_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_compute_cost_path/compute_cost_150mm.lldb)
- Runtime JSON reports:
  `runs/stereolayer_compute_cost_path/compute_cost_28mm.json`
  `runs/stereolayer_compute_cost_path/compute_cost_35mm.json`
  `runs/stereolayer_compute_cost_path/compute_cost_70mm.json`
  `runs/stereolayer_compute_cost_path/compute_cost_150mm.json`

## Runtime Test Conditions

All runtime findings in this note are scoped to:

- bridge binary: `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`
- renderer profile: `--profile 3`
- export format: `--export-fmt 3`
- `.lris` auto-loading: disabled with `--no-auto-lris`
- full bridge output: `10432x7824`
- LLDB-launched x86_64 process under Rosetta
- date run: `2026-06-01`

Canonical LRIs tested:

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Positive breakpoint counts were disabled after a cap of `64`. Counts above `64` are still lower bounds; multi-threaded stops can overshoot the cap before LLDB disables the breakpoint.

## Static Proof

### 1. `0x667c28` is the installed `StereoLayer<false>::compute()` lambda vtable

A direct qword scan of the installed `libcp.dylib` finds pointers to wrapper slots `0x274b10`, `0x274b20`, and `0x274b40`:

| Target VA | Installed pointer file/VA location |
|---:|---:|
| `0x274b10` | `0x667c58` |
| `0x274b20` | `0x667c60` |
| `0x274b40` | `0x667c68` |

The surrounding installed table is:

| Address | Value |
|---:|---:|
| `0x667c20` | `0x667c70` |
| `0x667c28` | `0x274a80` |
| `0x667c30` | `0x274a90` |
| `0x667c38` | `0x274aa0` |
| `0x667c40` | `0x274ad0` |
| `0x667c48` | `0x274af0` |
| `0x667c50` | `0x274b00` |
| `0x667c58` | `0x274b10` |
| `0x667c60` | `0x274b20` |
| `0x667c68` | `0x274b40` |

The typeinfo object at `0x667c70` names:

`NSt3__110__function6__funcIZN2lt11StereoLayerILb0EE7computeEvEUlRKNS2_9RectangleIiEEiE_NS_9allocatorIS9_EEFvS8_iEEE`

The adjacent lambda typeinfo name at `0x5daf70` is:

`ZN2lt11StereoLayerILb0EE7computeEvEUlRKNS_9RectangleIiEEiE_`

This proves the installed function-object table is the `StereoLayer<false>::compute()` rectangle lambda, not the already-documented `runPass(int)` lambda.

### 2. `0x274b10` is the operator wrapper and tail-jumps to `0x2727f0`

Disassembly lines:
`tools/libcp_disasm_intel.txt:606334`

`0x274b10`:

- loads `qword ptr [rdi+0x8]` into `rdi`
- tail-jumps to `0x2727f0`

This proves `0x2727f0` is reached through the installed `compute()` function-object operator wrapper.

Direct callgraph output found no `call` callers of `0x2727f0`; the observed direct static transfer is the tail jump from wrapper `0x274b10`.

### 3. `0x2727f0` is a sibling projection/cost worker body

Disassembly lines:
`tools/libcp_disasm_intel.txt:604044`

The visible body:

- copies entries from `StereoLayer+0x240/+0x248`, starting after the first entry
- reads `StereoLayer+0x270` to select either a constant at `0x5a9b04` or vector state at `StereoLayer+0x40`
- calls `0x26a790`
- calls `0x275630` at `0x2729b0`
- computes a branch flag from `computed_count == 4` and `StereoLayer+0x20`
- iterates the incoming rectangle / ROI argument
- uses a byte mask at `StereoLayer+0x220/+0x228`
- reads record/index data through `StereoLayer+0x130/+0x138`
- calls `0x2730c0` at `0x272c84` when the branch flag passes
- calls `0x2732f0` at `0x272ca9` otherwise
- scales the 16-bit result buffer by the reciprocal count factor and fills trailing entries from static bytes at `0x5a8e70`

This body shares the same cost-builder / cost-kernel family already bounded in the `runPass(int)` proof. The visible body is cost/projection work, not an exposed multi-source image reducer closure.

### 4. Adjacent setup helpers are statically bounded but not live in the tested renders

Direct callgraph output:

| Target | Direct caller(s) |
|---:|---|
| `0x272100` | `0x26b038`, `0x26f383` |
| `0x272640` | `0x26f571` |

Static inspection bounds these as adjacent setup/write-helper surfaces:

- `0x272100` is called after local descriptor/string setup at `0x26b038` and `0x26f383`
- `0x272640` is called at `0x26f571` after local descriptor movement into `r12+0x208`; its visible error strings include `no data to write for "` and `"!`

Their runtime status is captured below; no positive semantic claim is made beyond these visible/static boundaries.

## Runtime Proof

Breakpoints:

| Label | VA | Role |
|---|---:|---|
| `compute_setup_caller_a_26b038` | `0x26b038` | direct caller of `0x272100` |
| `compute_setup_caller_b_26f383` | `0x26f383` | direct caller of `0x272100` |
| `compute_write_guard_caller_26f571` | `0x26f571` | direct caller of `0x272640` |
| `compute_setup_helper_272100` | `0x272100` | adjacent setup helper |
| `compute_write_guard_272640` | `0x272640` | adjacent write/helper guard |
| `compute_lambda_operator_274b10` | `0x274b10` | installed `compute()` lambda operator wrapper |
| `compute_worker_entry_2727f0` | `0x2727f0` | `compute()` worker entry |
| `compute_state_builder_callsite_2729b0` | `0x2729b0` | `0x275630` callsite inside `0x2727f0` |
| `compute_count4_cost_callsite_272c84` | `0x272c84` | `0x2730c0` callsite inside `0x2727f0` |
| `compute_general_cost_callsite_272ca9` | `0x272ca9` | `0x2732f0` callsite inside `0x2727f0` |
| `runpass_action_control_276790` | `0x276790` | live `runPass(int)` control |
| `runpass_mode8_control_276860` | `0x276860` | live mode-8 worker control |
| `runpass_default_control_277e70` | `0x277e70` | default worker control |
| `runpass_count4_cost_callsite_27710f` | `0x27710f` | `0x2730c0` callsite inside mode-8 worker |
| `runpass_general_cost_callsite_2773dc` | `0x2773dc` | `0x2732f0` callsite inside mode-8 worker |

Runtime result:

| Zoom | Exit | `0x26b038` | `0x26f383` | `0x26f571` | `0x272100` | `0x272640` | `0x274b10` | `0x2727f0` | `0x2729b0` | `0x272c84` | `0x272ca9` | `0x276790` | `0x276860` | `0x277e70` | `0x27710f` | `0x2773dc` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `66` | `66` | `0` | `0` | `65` |
| `35mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `67` | `67` | `0` | `0` | `64` |
| `70mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `64` | `66` | `0` | `0` | `64` |
| `150mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `65` | `64` | `0` | `0` | `64` |

Every run:

- exited with status `0`
- wrote a `10432x7824` HDR output
- had no JSON probe errors
- did not hit the drive-step cap
- sampled the live `runPass(int)` control path with `layer+0xc == 8`

The zero-hit compute-surface results are scoped to these complete `--no-auto-lris` bridge HDR renders only.

## Safe Conclusion

The `StereoLayer<false>::compute()` lambda surface at `0x667c28/+0x30 = 0x274b10 -> 0x2727f0` is now bounded as an installed sibling of the already-known `runPass(int)` cost path.

The static body shares the same projection/sampling cost family, and the tested bridge HDR quartet did not execute it or its adjacent setup helpers under no-auto-LRIS conditions. The live control path remains `StereoLayer<false>::runPass(int)` mode-8 cost work.

This narrows the reducer search by preventing the `0x2727f0` sibling from being treated as a newly found merge/reduction closure under the tested conditions. It does not close `CLM-PREFUSION-002`.

## Remaining Unknowns

- Exact `src1` / `src2` reducer body, inputs, outputs, and math remain unproven.
- `0x2727f0`, `0x272100`, and `0x272640` remain live installed code with zero hits only under the tested bridge HDR / no-auto-LRIS scope.
- Exact clean-room projection/sampling cost translation for the `StereoLayer<false>` cost family remains separate from the merge reducer blocker.
