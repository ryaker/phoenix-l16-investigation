# Bundle Proof: Prefusion Callable Gate, Four-Zoom Runtime Scope

## Scope

This note extends the prefusion reducer exclusion chain.

It proves:

- the prefusion state constructor at `0x22fbf0` installs an inline callable pointer at `state+0x220`
- the constructor writes `state+0x220 = state+0x200` and writes vtable address point `0x6673f0` at `state+0x200`
- vtable address point `0x6673f0` has slot `+0x30 = 0x230220`, and `0x230220` is a trivial false-return body
- runtime samples from the canonical four-zoom bridge HDR quartet reached the heavier prefusion gate sites with `state+0x220 == state+0x200`
- those runtime samples used vtable address point `0x66b0f0`
- vtable address point `0x66b0f0` has slot `+0x30 = 0x230640`, and `0x230640` is also a trivial false-return body
- the sampled callable-gate sites are therefore gate/predicate surfaces, not the missing `src1` / `src2` N-to-1 reducer

It does not prove:

- the exact upstream `src1` / `src2` N-to-1 reducer
- callable-gate replacement behavior outside the sampled bridge HDR conditions
- that zero-hit downstream sister gates are dead code outside the tested conditions

## Evidence Inputs

- Static disassembly:
  [tools/libcp_disasm_intel.txt](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/libcp_disasm_intel.txt)
- Runtime result JSON:
  `/private/tmp/l16_prefusion_callable_gate_probe/results.json`
- Corrected true-35mm runtime result JSON:
  `/private/tmp/l16_prefusion_callable_gate_probe_true35/results.json`
- Runtime binary:
  `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`
- Runtime dylib:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Runtime method:
  `arch -x86_64 lldb` breakpoints on the listed `libcp` VAs, with sampled positive-hit breakpoints capped at 10 hits.

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

Correction note: the former `35mm` row used `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`; direct `LightHeader` decode later proved that path is a 98mm tele-tier sample. The `35mm` row above is the corrected true-35mm rerun.

All four renders exited `0`.

## Static Proof

### 1. The constructor initializes `state+0x220` to an inline callable object

Disassembly lines:
`tools/libcp_disasm_intel.txt:542795`

At `0x22fd5f`, the constructor writes:

- `state+0x220 = r12`
- `r12` was set to `state+0x200` at `0x22fd39`

At `0x22fd66..0x22fd6d`, the constructor writes:

- vtable address point `0x6673f0` to `state+0x200`

Therefore the constructor-installed callable pointer is inline in the state object, not a separate image reducer object.

### 2. The constructor-installed vtable has a false-return `+0x30` slot

Static vtable bytes:

| Address | Value |
|---|---|
| `0x6673f0` | `0x2301b0` |
| `0x6673f8` | `0x2301c0` |
| `0x667400` | `0x2301d0` |
| `0x667408` | `0x2301f0` |
| `0x667410` | `0x230200` |
| `0x667418` | `0x230210` |
| `0x667420` | `0x230220` |

The slot at address-point `+0x30` is:

`0x6673f0 + 0x30 = 0x667420 = 0x230220`

`0x230220`:

```asm
push rbp
mov rbp, rsp
xor eax, eax
pop rbp
ret
```

Therefore the constructor-default callable's `+0x30` body returns false.

### 3. The runtime-sampled vtable has a false-return `+0x30` slot too

Runtime samples at the inspected gate sites did not use `0x6673f0`; they used address point `0x66b0f0`.

Static vtable bytes:

| Address | Value |
|---|---|
| `0x66b0f0` | `0x2305d0` |
| `0x66b0f8` | `0x2305e0` |
| `0x66b100` | `0x2305f0` |
| `0x66b108` | `0x230610` |
| `0x66b110` | `0x230620` |
| `0x66b118` | `0x230630` |
| `0x66b120` | `0x230640` |

The slot at address-point `+0x30` is:

`0x66b0f0 + 0x30 = 0x66b120 = 0x230640`

`0x230640`:

```asm
push rbp
mov rbp, rsp
xor eax, eax
pop rbp
ret
```

Therefore the runtime-sampled callable's `+0x30` body also returns false.

## Runtime Proof

The probe sampled these gate sites:

| Label | VA | Register basis |
|---|---:|---|
| selector gate | `0x24200d` | `state = r13`, `callable = rdi` |
| `0x244560` initial gate | `0x24459b` | `state = r14`, `callable = rdi` |
| `0x244560` second gate | `0x24477b` | `state = r14`, `callable = rdi` |
| `0x245a40` gate | `0x245b29` | `state = rbx`, `callable = rdi` |
| downstream gate A | `0x24c34f` | `state = r15`, `callable = rdi` |
| downstream gate B | `0x24d64e` | `state = r14`, `callable = rdi` |

For every sampled non-empty gate record:

- `callable == state+0x200`
- `state+0x220 == callable`
- runtime vtable minus slide = `0x66b0f0`
- runtime slot `+0x30` minus slide = `0x230640`

### Runtime hit counts

Counts are from completed full renders. A value of `10` means the breakpoint cap was reached, so the count is `>=10` under this probe.

| Zoom | `0x24200d` | `0x24459b` | `0x24477b` | `0x245b29` | `0x24c34f` | `0x24d64e` |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `>=10` | `4` | `4` | `5` | `>=10` | `0` |
| `35mm` | `>=10` | `4` | `4` | `5` | `>=10` | `0` |
| `70mm` | `>=10` | `4` | `4` | `5` | `0` | `>=10` |
| `150mm` | `>=10` | `4` | `4` | `5` | `0` | `>=10` |

The `0x24c34f` / `0x24d64e` split is zoom-scoped under these conditions:

- `28mm` samples reached `0x24c34f`
- `35mm` samples reached `0x24c34f`
- `70mm` and `150mm` samples reached `0x24d64e`

The zeroes in this table are scoped to this probe and these full renders only.

## Safe Conclusion

The prefusion callable gate is now bounded under the tested bridge HDR path:

- the state object carries an inline callable pointer at `state+0x220`
- sampled gate calls across the canonical quartet resolve to `state+0x200`
- sampled gate calls dispatch to a trivial false-return body through vtable `0x66b0f0`, slot `+0x30 = 0x230640`
- the constructor-default inline vtable `0x6673f0` has the same false-return shape at slot `+0x30 = 0x230220`

This closes the callable-gate surface as an exclusion point.

It does not close the exact `src1` / `src2` N-to-1 reducer.

The reducer search should not reopen `0x22fbf0`, `state+0x220`, `0x6673f0`, `0x66b0f0`, `0x230220`, `0x230640`, or the sampled callable-gate tests at `0x24200d`, `0x24459b`, `0x24477b`, `0x245b29`, `0x24c34f`, and `0x24d64e` as reducer closure points unless future evidence proves a different runtime scope with real N-to-1 input shape and reducer math.
