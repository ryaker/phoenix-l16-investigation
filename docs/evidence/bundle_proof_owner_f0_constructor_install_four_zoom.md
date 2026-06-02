# Bundle Proof: Owner `+0xf0` Callable Installation, Four-Zoom Runtime Scope

## Scope

This note closes a small custody gap between the visible owner constructor surface and the already bounded owner `+0xf0` output sink.

It proves:

- `0x3ea980` is a direct caller of callable-slot helper `0x3d0120`
- immediately before `0x3ea980`, the constructor body builds a stack callable whose first qword normalizes to address point `0x65f5e0`
- installed-bundle table `0x65f5e0` has substantive slot `+0x30 = 0x3ec960`
- immediately after `0x3ea980`, the target object's inline callable storage at `target+0x50` contains address point `0x65f5e0`, and `target+0x70` points back to that inline callable storage
- the same complete bridge HDR runs then reach the already-bounded owner `+0xf0` sink body `0x3ec960` and post-`0x3e5720` site `0x3ecac3`

It does not prove:

- semantic contents of `src1` or `src2`
- the exact pre-fusion merge/reduction mechanism
- public meaning of the owner object or owner `+0xf0`
- final file/display output semantics
- final merge acceptance / rejection logic

## Evidence Inputs

- Static disassembly:
  [tools/libcp_disasm_intel.txt](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/libcp_disasm_intel.txt)
- Static callgraph helper:
  [tools/disasm_callgraph.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/disasm_callgraph.py)
- Runtime probe:
  [owner_f0_constructor_install_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/owner_f0_constructor_install/owner_f0_constructor_install_probe.py)
- LLDB scripts:
  [owner_f0_constructor_install_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/owner_f0_constructor_install/owner_f0_constructor_install_28mm.lldb)
  [owner_f0_constructor_install_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/owner_f0_constructor_install/owner_f0_constructor_install_35mm.lldb)
  [owner_f0_constructor_install_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/owner_f0_constructor_install/owner_f0_constructor_install_70mm.lldb)
  [owner_f0_constructor_install_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/owner_f0_constructor_install/owner_f0_constructor_install_150mm.lldb)
- Runtime JSON reports:
  `runs/owner_f0_constructor_install/owner_f0_constructor_install_28mm.json`
  `runs/owner_f0_constructor_install/owner_f0_constructor_install_35mm.json`
  `runs/owner_f0_constructor_install/owner_f0_constructor_install_70mm.json`
  `runs/owner_f0_constructor_install/owner_f0_constructor_install_150mm.json`

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

## Static Proof

### 1. `0x3ea980` is a direct `0x3d0120` caller

Repo-local static callgraph output:

```text
Callers of 0x3d0120 (3 hits):
  0x3e2b2a  (direct)
  0x3ea980  (direct)
  0x3f05ae  (direct)
```

The previously documented callers were `0x3e2b2a` and `0x3f05ae`; this note covers the remaining constructor-side caller `0x3ea980`.

### 2. The constructor builds a stack callable before the helper call

Installed-bundle disassembly around the constructor body shows:

```asm
0x3ea8fc  call 0x3e0af0
0x3ea930  call 0x3e0b90
0x3ea953  call 0x3ddf30
0x3ea95e  call 0xf32d0
0x3ea96b  lea  rax, [rip + ...]  ; address point 0x65f5e0
0x3ea972  mov  qword ptr [rbp-0x60], rax
0x3ea976  mov  qword ptr [rbp-0x58], r14
0x3ea97a  mov  rdi, r14
0x3ea97d  lea  rsi, [rbp-0x60]
0x3ea980  call 0x3d0120
0x3ea985  ...
```

The runtime proof below confirms this stack callable is installed into the target object.

### 3. Address point `0x65f5e0` selects owner sink body `0x3ec960`

Installed `libcp.dylib` table bytes:

```text
0x65f5e0: 0x3ec8d0 0x3ec8e0 0x3ec8f0 0x3ec920
0x65f600: 0x3ec940 0x3ec950 0x3ec960 0x3ecb50
```

Therefore:

```text
0x65f5e0 + 0x30 = 0x65f610
qword[0x65f610] = 0x3ec960
```

The body `0x3ec960` is already bounded by [bundle_lldb_iramp_caller_output_descriptor_sink.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_iramp_caller_output_descriptor_sink.md) as the owner `+0xf0` output-descriptor sink for the `0x3e5720` row-conversion output.

## Runtime Proof

Breakpoints:

| Label | VA | Role |
|---|---:|---|
| `constructor_entry_3ea7d0` | `0x3ea7d0` | constructor body entry under test |
| `visible_payload_lookup_callsite_3ea8fc` | `0x3ea8fc` | nearby visible-payload lookup callsite |
| `owner_f0_callable_install_callsite_3ea980` | `0x3ea980` | `0x3d0120` callable-install callsite |
| `owner_f0_callable_install_return_3ea985` | `0x3ea985` | immediately after callable installation |
| `owner_f0_sink_entry_3ec960` | `0x3ec960` | installed owner `+0xf0` sink entry |
| `owner_f0_sink_after_3e5720_3ecac3` | `0x3ecac3` | owner sink post-`0x3e5720` site |

Runtime result:

| Zoom | Exit | Constructor | Lookup | Install call | Install return | Sink entry | Sink post-`0x3e5720` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `1` | `1` | `1` | `1` | `>=96` | `>=96` |
| `35mm` | `0` | `1` | `1` | `1` | `1` | `>=96` | `>=96` |
| `70mm` | `0` | `1` | `1` | `1` | `1` | `>=96` | `>=96` |
| `150mm` | `0` | `1` | `1` | `1` | `1` | `83` | `83` |

The `>=96` entries reached the probe hit cap and were disabled. The `150mm` sink sites did not reach the hit cap; `83` is the observed complete-render count in this probe.

Every run:

- exited with status `0`
- had no JSON probe errors
- did not hit the drive-step cap
- wrote a `10432x7824` HDR output

### Installation-state invariant

For every zoom, the first captured install callsite sample at `0x3ea980` showed:

- `rdi` = target object
- `rsi` = stack callable
- stack callable first qword normalized to module VA `0x65f5e0`

For every zoom, the first captured return sample at `0x3ea985` showed:

- target inline callable storage at `target+0x50` first qword normalized to module VA `0x65f5e0`
- field value at `target+0x70` equals `target+0x50`

Runtime normalized table:

| Zoom | Stack callable address point at `0x3ea980` | Post-install address point at `target+0x50` | Field value at `target+0x70` equals `target+0x50` |
|---|---:|---:|---|
| `28mm` | `0x65f5e0` | `0x65f5e0` | yes |
| `35mm` | `0x65f5e0` | `0x65f5e0` | yes |
| `70mm` | `0x65f5e0` | `0x65f5e0` | yes |
| `150mm` | `0x65f5e0` | `0x65f5e0` | yes |

Verification command run after report generation:

```text
PASS owner_f0_constructor_install reports: four focal tiers exited 0 and match constructor/install invariants
```

## Safe Conclusion

The constructor-side `0x3ea980 -> 0x3d0120` caller installs callable address point `0x65f5e0` into the target object's inline callable storage across complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders.

Because installed address point `0x65f5e0` has substantive slot `+0x30 = 0x3ec960`, this ties the live `0x3ea7d0` constructor surface to the already bounded owner `+0xf0` output-descriptor sink family.

This narrows custody and prevents `0x3ea980` from remaining an unexplained `0x3d0120` caller. It does not close `CLM-PREFUSION-002`, does not identify semantic `src1` / `src2` contents, and does not prove final merge acceptance / rejection.

## Remaining Unknowns

- The exact pre-fusion merge/reduction mechanism remains open.
- The semantic owner fields behind the installed callable are not named.
- Owner `+0xf0` downstream row-image/final policy remains open after the already classified sink, expansion, route, and resample families.
- Public pixel-format names and final file/display semantics remain open.
