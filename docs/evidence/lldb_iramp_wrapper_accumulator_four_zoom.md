# LLDB Evidence: IRAMP Wrapper And Accumulator Four-Zoom Runtime Hits

## Scope

This note records one bounded runtime fact set from the installed Lumen bundle:
the canonical four-zoom bridge HDR seed files all hit the same visible
`src1` wrapper, `src2` wrapper, contributor wrapper, and IRAMP accumulator
addresses.

It proves four-zoom runtime participation for these visible surfaces:

- `libcp+0x3ecc10`: visible `src1` wrapper read body.
- `libcp+0x3ecd80`: visible `src2` wrapper read body.
- `libcp+0x3eced0`: visible contributor wrapper read body.
- `libcp+0x369fa1`: weighted accumulator instruction inside IRAMP.

It does not prove the exact pre-fusion merge/reduction mechanism behind
`src1` / `src2`.

It does not prove final merge acceptance / rejection logic.

It does not prove that the captured `rbp-0xa0` stack window is a closed-form
weight formula. The stack bytes are recorded as observed runtime bytes only.

## Probe Method

The probe used `arch -x86_64 lldb` against:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`

The target process used:

- `DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `--profile 3 --export-fmt 3`

Each run installed four pending `libcp.dylib` breakpoints:

```text
breakpoint set --shlib libcp.dylib --address 0x3ecc10
breakpoint set --shlib libcp.dylib --address 0x3ecd80
breakpoint set --shlib libcp.dylib --address 0x3eced0
breakpoint set --shlib libcp.dylib --address 0x369fa1
breakpoint modify -G true 1 2 3 4
```

Python breakpoint callbacks captured register/object summaries and wrote JSON.
The callbacks intentionally killed each render after target hit counts were
reached. Therefore the generated HDR files are not image validation artifacts.

LLDB sometimes still displayed a final multi-thread breakpoint stop after the
callbacks fired. The JSON packets, not the terminal stop banner, are the
evidence source. All four JSON packets reported `callback_errors: []` and
`stop_reason: "target_counts_reached"`.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | unit unknown | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Correction note: the former `35mm` row used `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`; direct `LightHeader` decode later proved that path is a 98mm tele-tier sample. The `35mm` row above is the corrected rerun from `/private/tmp/l16_runtime_method_probe_35mm_true.json`; see [lri_35mm_seed_correction_true35_runtime.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lri_35mm_seed_correction_true35_runtime.md).

## Runtime Hit Counts

The callbacks stopped only after their per-address targets were reached.
Counts can exceed targets because multiple render threads can hit before the
process kill is observed.

| Zoom | `0x3ecc10` src1 | `0x3ecd80` src2 | `0x3eced0` contributor | `0x369fa1` accumulator | Callback errors |
|---|---:|---:|---:|---:|---|
| `28mm` | 10 | 10 | 5 | 165 | none |
| `35mm` | 10 | 10 | 10 | 2 | none |
| `70mm` | 10 | 8 | 5 | 14 | none |
| `150mm` | 10 | 10 | 24 | 2 | none |

All four runs resolved the same `libcp` runtime base:

`0x108c7a000`

## Runtime Vtable Slot Observations

For every tested zoom, the captured wrapper objects resolved to the same
vtable regions and the same `+0x30` callable slot targets:

| Runtime surface | Vtable file offset | Captured `vtable+0x30` target |
|---|---:|---:|
| `src1` wrapper object | `0x65f668` | `0x3ecc10` |
| `src2` wrapper object | `0x65f6e8` | `0x3ecd80` |
| contributor wrapper object | `0x65f768` | `0x3eced0` |

This runtime result agrees with the installed-bundle wrapper proof:

[bundle_proof_src_wrappers.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src_wrappers.md)

## First Captured Accumulator Stack Window

The first recorded `0x369fa1` event in each focal run had the same 16-float
window at `rbp-0xa0`:

```text
0.009607375
0.084265202
0.222214907
0.402454883
0.597545147
0.777785182
0.915734828
0.990392685
0.990392625
0.915734768
0.777785003
0.597545207
0.402454793
0.222214788
0.084265202
0.009607345
```

This is a runtime byte observation at the accumulator site only. The formula
that produced the window is not closed by this note.

## Safe Conclusions

- Proven:
  the canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR seed renders all
  reached `libcp+0x369fa1`.
- Proven:
  the canonical four-zoom bridge HDR seed renders all reached the visible
  `src1`, `src2`, and contributor wrapper bodies at `0x3ecc10`, `0x3ecd80`,
  and `0x3eced0`.
- Proven:
  the runtime wrapper objects observed at those hits resolved to vtables
  `0x65f668`, `0x65f6e8`, and `0x65f768`, whose captured `+0x30` slot targets
  were `0x3ecc10`, `0x3ecd80`, and `0x3eced0`.
- Proven:
  the first captured `0x369fa1` accumulator event in each focal run showed the
  same 16-float `rbp-0xa0` stack window.
- Still unproven:
  exact pre-fusion merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  final merge acceptance / rejection logic beyond the weighted accumulator.

## Canonical Consequence

`CLM-MERGE-002` can now be treated as four-zoom runtime-proven for the narrow
claim that IRAMP's weighted accumulator at `0x369fa1..0x369fa8` participates in
the canonical bridge HDR quartet.

This does not close `CLM-PREFUSION-002`, because the visible wrappers and
accumulator do not reveal the exact upstream `src1` / `src2` reducer mechanism.

This does not close final merge-quality logic, because the accumulator site is
arithmetic participation, not proof of all acceptance / rejection decisions
needed to avoid ghosting and trails.
