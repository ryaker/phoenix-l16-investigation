# Exact Portable Emulation Of Reference `rcpss` / `rcpps`

## Result

The unrefined SSE reciprocal approximation used throughout the installed
pipeline now has an exact integer-only clean-room bit formula for the current
Rosetta reference platform. It is no longer necessary to substitute exact
IEEE division or retain a captured lookup table.

The same formula reproduces scalar `rcpss` and every tested packed `rcpps`
lane exactly.

## Reusable Oracle

- `tools/validation/dump_x86_rcpss.c`
- `tools/validation/verify_x86_rcp_emulation.sh`
- generated, ignored artifacts under `runs/rcpss_emulation/`

The C harness is compiled as x86_64, ad-hoc signed so macOS permits Rosetta
translation, and executes `_mm_rcp_ss` and `_mm_rcp_ps` as the runtime oracle.

## Exact Normal Formula

Let a finite normal float32 input have bit fields:

```text
sign      = bits & 0x80000000
exponent  = (bits >> 23) & 0xff
fraction  = bits & 0x007fffff
```

For `1 <= exponent <= 252`, the approximation ignores the low 12 fraction
bits. Define:

```text
i = fraction >> 12                  // 0..2047
d = 4097 + 2*i
q = round_to_nearest_integer(2^25 / d)
  = (2^25 + floor(d/2)) // d         // d is odd; no tie

output_exponent = 253 - exponent
output_fraction = (q - 4096) << 11
output_bits = sign | (output_exponent << 23) | output_fraction
```

This is equivalently a 2,048-bin midpoint reciprocal:

```text
midpoint_i = (4097 + 2*i) / 4096
approx = round((1/midpoint_i) * 8192) / 8192
```

but the integer form avoids host floating-point and rounding dependence.

An exhaustive exponent-127 dump contains exactly 2,048 runs of 4,096 input
mantissas each, proving the ignored-low-12-bit partition. Every observed result
has its low 11 fraction bits clear. Exponent-126 output differs only by the
expected output-exponent increment, proving the normalized table is shared.

Representative mappings are:

```text
1.0f       0x3f800000 -> 0x3f7ff000
0.5f       0x3f000000 -> 0x3ffff000
1.5f       0x3fc00000 -> 0x3f2aa000
rcpss(981) 0x3a859800 -> 0x44754800
```

The last value is the exact reciprocal seed used by the admitted A1
MonoFusion reference normalization.

## Special Values

The observed current-reference behavior is:

```text
exponent == 0                    -> signed infinity
finite exponent >= 253           -> signed zero
positive/negative infinity       -> positive/negative zero
NaN                              -> payload/sign preserved, quiet bit set
```

Thus float32 subnormal inputs are treated as signed zero and reciprocal
underflow is flushed. These branches are included in the portable formula.

## Exhaustive Verification

The self-test covers:

```text
2 signs
254 finite-normal input exponents
2048 top-mantissa bins
6 representative low-12-bit values per bin
12 zero/subnormal/infinity/NaN cases
= 6,242,316 cases
```

For every case:

```text
software_bits == x86 rcpss bits == x86 rcpps lane bits
```

The test completes with:

```text
rcpss_software_formula=OK cases=6242316
```

## Claim Consequence And Scope

This closes the portable reciprocal primitive needed by the already admitted
`CLM-DEMOSAIC-002`, `CLM-DENOISE-001`, `CLM-PREFUSION-002`, and
`CLM-MERGE-005` formulas wherever their installed bodies specify unrefined
`rcpss` or lane-wise `rcpps`. It does not change their operation order,
route/focal coverage, inputs, or claim status.

Exact runtime scope is the current Apple-Silicon Rosetta x86_64 reference
platform used for the retained Lumen probes. Intel documents only an error
bound for this instruction family, so this bundle does not assert that every
historical native-Intel microarchitecture must return the same approximation
bits. A portable Phoenix implementation can deliberately use the admitted
integer mapping to reproduce the current reference deterministically on any
host.

## Reproduction

```bash
tools/validation/verify_x86_rcp_emulation.sh
```
