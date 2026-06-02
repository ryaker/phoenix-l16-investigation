# Bundle Proof: `HigherWarpDebug::renderDebugView` Helper Callers, Four-Zoom Runtime Scope

## Scope

This note classifies a newly surfaced high-address caller family that touches already-important helper targets:

- `0x42cb5d -> 0x3f6170`
- `0x42cbc2 -> 0x3f7040`
- `0x42cc5a -> 0x3e55f0`

It proves:

- installed-bundle static evidence binds the local callback tables at `0x6609e8` and `0x660a68` to `lt::HigherWarpDebug::renderDebugView(...)` lambda/typeinfo names
- under complete `--no-auto-lris` bridge HDR renders of the canonical `28mm`, `35mm`, `70mm`, and `150mm` LRIs, the probed debug-view entry/callsite/callback addresses had zero hits
- the same runs hit live controls at `0x3e05f5 -> 0x3f6170` and `0x3eb72d -> 0x3f7040` five times per tier, proving the probe was attached to the live helper family

It does not prove:

- that `HigherWarpDebug::renderDebugView` is dead code outside the tested bridge HDR / no-auto-LRIS path
- that `0x3f6170`, `0x3f7040`, or `0x3e55f0` are debug-only helpers
- the exact `src1` / `src2` merge/reduction mechanism
- final merge acceptance / rejection logic

## Evidence Inputs

- Static disassembly:
  [tools/libcp_disasm_intel.txt](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/libcp_disasm_intel.txt)
- Runtime probe:
  [higherwarpdebug_renderdebugview_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_probe.py)
- LLDB scripts:
  [higherwarpdebug_renderdebugview_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_28mm.lldb)
  [higherwarpdebug_renderdebugview_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_35mm.lldb)
  [higherwarpdebug_renderdebugview_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_70mm.lldb)
  [higherwarpdebug_renderdebugview_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_150mm.lldb)
- Runtime JSON reports:
  `runs/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_28mm.json`
  `runs/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_35mm.json`
  `runs/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_70mm.json`
  `runs/higherwarpdebug_renderdebugview/higherwarpdebug_renderdebugview_150mm.json`

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

Positive breakpoint counts were disabled after a cap of `96`; no breakpoint reached the cap in these runs.

## Static Proof

### 1. `0x42c140` is the visible debug-view body boundary under inspection

The static disassembly at `tools/libcp_disasm_intel.txt:1015997` shows body entry `0x42c140`.

The direct static callgraph reports no direct `call` callers of `0x42c140`. That is not proof of dead code, because the body may be reached indirectly; runtime coverage below is the scoped liveness check.

### 2. The high-address body calls the same helper targets that needed classification

At `tools/libcp_disasm_intel.txt:1016562`, the body:

- calls `0x3ebaf0` at `0x42cb35`
- passes a key from `dword [[rbp-0x2258] + 4*r15]`
- calls `0x3f6170` at `0x42cb5d`
- calls `0x3ebaf0` again at `0x42cb9c`
- calls `0x3f7040` at `0x42cbc2`
- selects local callback table `0x6609e8` or `0x660a68` based on `byte [r12+0x20]`
- calls `0x3e55f0` at `0x42cc5a`

This statically explains why the high-address sites mattered: they are apparent direct callers into helper families already present in merge-adjacent proofs.

### 3. The selected callback tables are `HigherWarpDebug::renderDebugView` lambdas

Static LLDB memory reads against the installed `libcp.dylib` show:

| Address | Value |
|---:|---:|
| `0x6609e8` | `0x430050` |
| `0x6609f0` | `0x430060` |
| `0x6609f8` | `0x430070` |
| `0x660a00` | `0x4300b0` |
| `0x660a08` | `0x4300d0` |
| `0x660a10` | `0x4300e0` |
| `0x660a18` | `0x4300f0` |
| `0x660a20` | `0x430180` |
| `0x660a28` | `0x4301a0` |
| `0x660a38` | `0x613810` |
| `0x660a50` | `0x6138c0` |
| `0x660a68` | `0x4301b0` |
| `0x660a70` | `0x4301c0` |
| `0x660a78` | `0x4301d0` |
| `0x660a80` | `0x430200` |
| `0x660a88` | `0x430220` |
| `0x660a90` | `0x430230` |
| `0x660a98` | `0x430240` |
| `0x660aa0` | `0x4302e0` |
| `0x660aa8` | `0x430300` |
| `0x660ab8` | `0x613930` |
| `0x660ad0` | `0x6139e0` |

Installed string extraction from the same binary maps those string addresses to:

| String address | Extracted name |
|---:|---|
| `0x613810` | `NSt3__110__function6__funcIZN2lt15HigherWarpDebug15renderDebugViewERNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEERKNS2_4Vec2IiEEE3$_0NS_9allocatorISG_EEFNSC_IfEEffEEE` |
| `0x6138c0` | `ZN2lt15HigherWarpDebug15renderDebugViewERNS_5ImageINS_8vec4x32fEEERKNS_9RectangleIiEERKNS_4Vec2IiEEE3$_0` |
| `0x613930` | `NSt3__110__function6__funcIZN2lt15HigherWarpDebug15renderDebugViewERNS2_5ImageINS2_8vec4x32fEEERKNS2_9RectangleIiEERKNS2_4Vec2IiEEE3$_1NS_9allocatorISG_EEFNSC_IfEEffEEE` |
| `0x6139e0` | `ZN2lt15HigherWarpDebug15renderDebugViewERNS_5ImageINS_8vec4x32fEEERKNS_9RectangleIiEERKNS_4Vec2IiEEE3$_1` |

The static classification is therefore limited to the local callback tables and the body region that selects them. It does not rename the shared helpers themselves.

## Runtime Proof

Breakpoints:

| Label | VA | Role |
|---|---:|---|
| `debug_entry_42c140` | `0x42c140` | debug-view body entry under test |
| `debug_source_lookup_callsite_42cb35` | `0x42cb35` | first local call to `0x3ebaf0` |
| `debug_fieldpack_callsite_42cb5d` | `0x42cb5d` | local call to `0x3f6170` |
| `debug_source_lookup_callsite_42cb9c` | `0x42cb9c` | second local call to `0x3ebaf0` |
| `debug_map_provider_callsite_42cbc2` | `0x42cbc2` | local call to `0x3f7040` |
| `debug_callback_executor_callsite_42cc5a` | `0x42cc5a` | local call to `0x3e55f0` |
| `debug_callback_a_operator_4300f0` | `0x4300f0` | substantive operator slot from table `0x6609e8/+0x30` |
| `debug_callback_b_operator_430240` | `0x430240` | substantive operator slot from table `0x660a68/+0x30` |
| `live_fieldpack_control_3e05f5` | `0x3e05f5` | known live `0x3f6170` callsite control |
| `live_map_provider_control_3eb72d` | `0x3eb72d` | known live `0x3f7040` callsite control |

Runtime result:

| Zoom | Exit | Debug entry | `0x42cb35` | `0x42cb5d` | `0x42cb9c` | `0x42cbc2` | `0x42cc5a` | `0x4300f0` | `0x430240` | Live `0x3e05f5` | Live `0x3eb72d` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `5` | `5` |
| `35mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `5` | `5` |
| `70mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `5` | `5` |
| `150mm` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `0` | `5` | `5` |

Every run:

- exited with status `0`
- wrote a `10432x7824` HDR output
- had no JSON probe errors
- did not hit the drive-step cap
- sampled live stack contexts for both control callsites

The zero-hit debug-view results are scoped to these complete `--no-auto-lris` bridge HDR renders only.

## Safe Conclusion

The high-address direct callers `0x42cb5d -> 0x3f6170`, `0x42cbc2 -> 0x3f7040`, and `0x42cc5a -> 0x3e55f0` are now classified as part of a `HigherWarpDebug::renderDebugView` local callback surface and bounded away from the canonical bridge HDR path under the tested no-auto-LRIS conditions.

This prevents those high-address callers from contaminating the `src1` / `src2` reducer search as unexplained live merge-adjacent activity. It does not close `CLM-PREFUSION-002`, does not prove global non-liveness, and does not weaken the already-proven live helper paths at `0x3e05f5` and `0x3eb72d`.

## Remaining Unknowns

- Exact `src1` / `src2` reducer body, inputs, outputs, and math remain unproven.
- The tested zero-hit result is limited to canonical bridge HDR with `.lris` auto-loading disabled.
- Other render modes or explicit debug-view use may still execute this family.
- Shared helpers `0x3f6170`, `0x3f7040`, and `0x3e55f0` remain live in non-debug paths; only the `0x42c140` / `0x42cbxx` / `0x4300xx` debug-view surface is excluded under this tested path.
