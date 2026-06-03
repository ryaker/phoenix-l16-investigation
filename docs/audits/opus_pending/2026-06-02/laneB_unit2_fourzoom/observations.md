# observations — Lane B Unit-2 four-zoom IRAMP coefficient capture

status: NEEDS_CODEX_VALIDATION. Weak language only. No authority.

## Unit-1 REFERENCE (kept separate; NOT re-measured this session)

Hann-16 table captured last session on Unit-1 / 28mm (from spawn prompt):

```
0.009607 0.084265 0.222215 0.402455 0.597545 0.777785 0.915735 0.990393
0.990393 0.915735 0.777785 0.597545 0.402455 0.222215 0.084265 0.009607
```

## Unit-2 CAPTURES (this session)

Probe target: `libcp_base+0x369fa4` = `addps (%rdx,%rcx,4),%xmm1` (IRAMP
accumulator per spawn prompt). 16 floats read at `$rbp-0xa0` at the FIRST hit.
Renders run STRICTLY SEQUENTIALLY. libcp.dylib sha256 b38dc4b3...

Cross-unit discipline: Unit-1 reference above and Unit-2 captures below are kept
strictly separate; no averaging/merging across units.

### 28mm — Unit-2 /Volumes/Base Photos/Light/2018-07-04/L16_02130.lri

- log: `runs/laneB_unit2_fourzoom/28mm_L16_02130.log`
- result json: `runs/laneB_unit2_fourzoom/28mm_L16_02130_result.json`
- libcp_base: `0x108c7a000`  bp_va: `0x108fe3fa4` (`addps (%rdx,%rcx,4),%xmm1`)
- state_after_continue: 5 (5 = stopped at first hit)
- anchorPassed: False (anchor at 0x109066ed0 is a function prologue on this binary)
- regs at first hit: rdi=0x30453ba40 rdx=0x7f9ad0008040 rax=0x30453ba40 rsi=0x0 rcx=0x0 rip=0x108fe3fa4 rbp=0x30453e700
- backtrace[0:6]: #0 ___lldb_unnamed_symbol_3661b0 -> #1 ___lldb_unnamed_symbol_365960 -> #2 ___lldb_unnamed_symbol_3ec770 -> #3 ___lldb_unnamed_symbol_3ec960 -> #4 ___lldb_unnamed_symbol_3d47d0 -> #5 ___lldb_unnamed_symbol_5440

Captured 16-float accumulator tile at `$rbp-0xa0` (verbatim float32):

```
0.009607374668121338
0.08426520228385925
0.22221490740776062
0.4024548828601837
0.5975451469421387
0.7777851819992065
0.9157348275184631
0.9903926849365234
0.9903926253318787
0.9157347679138184
0.7777850031852722
0.5975452065467834
0.40245479345321655
0.22221478819847107
0.08426520228385925
0.00960734486579895
```

**OBSERVED vs Unit-1 Hann-16: MATCH to 6 decimal places** (maxdiff 0.00e+00)

### 35mm — Unit-2 /Volumes/Base Photos/Light/2018-10-28/L16_03041.lri

- log: `runs/laneB_unit2_fourzoom/35mm_L16_03041.log`
- result json: `runs/laneB_unit2_fourzoom/35mm_L16_03041_result.json`
- libcp_base: `0x108c7a000`  bp_va: `0x108fe3fa4` (`addps (%rdx,%rcx,4),%xmm1`)
- state_after_continue: 5 (5 = stopped at first hit)
- anchorPassed: False (anchor at 0x109066ed0 is a function prologue on this binary)
- regs at first hit: rdi=0x3041a68f0 rdx=0x7fd6915e0040 rax=0x3041a68f0 rsi=0x0 rcx=0x0 rip=0x108fe3fa4 rbp=0x3041a95b0
- backtrace[0:6]: #0 ___lldb_unnamed_symbol_3661b0 -> #1 ___lldb_unnamed_symbol_365960 -> #2 ___lldb_unnamed_symbol_3ec770 -> #3 ___lldb_unnamed_symbol_3ec960 -> #4 ___lldb_unnamed_symbol_3d47d0 -> #5 ___lldb_unnamed_symbol_5cd0

Captured 16-float accumulator tile at `$rbp-0xa0` (verbatim float32):

```
0.009607374668121338
0.08426520228385925
0.22221490740776062
0.4024548828601837
0.5975451469421387
0.7777851819992065
0.9157348275184631
0.9903926849365234
0.9903926253318787
0.9157347679138184
0.7777850031852722
0.5975452065467834
0.40245479345321655
0.22221478819847107
0.08426520228385925
0.00960734486579895
```

**OBSERVED vs Unit-1 Hann-16: MATCH to 6 decimal places** (maxdiff 0.00e+00)

### 70mm — Unit-2 /Volumes/Base Photos/Light/2020-07-14/L16_03434.lri

- log: `runs/laneB_unit2_fourzoom/70mm_L16_03434.log`
- result json: `runs/laneB_unit2_fourzoom/70mm_L16_03434_result.json`
- libcp_base: `0x108c7a000`  bp_va: `0x108fe3fa4` (`addps (%rdx,%rcx,4),%xmm1`)
- state_after_continue: 5 (5 = stopped at first hit)
- anchorPassed: False (anchor at 0x109066ed0 is a function prologue on this binary)
- regs at first hit: rdi=0x3045be8f0 rdx=0x7f7bc3a88040 rax=0x3045be8f0 rsi=0x0 rcx=0x0 rip=0x108fe3fa4 rbp=0x3045c15b0
- backtrace[0:6]: #0 ___lldb_unnamed_symbol_3661b0 -> #1 ___lldb_unnamed_symbol_365960 -> #2 ___lldb_unnamed_symbol_3ec770 -> #3 ___lldb_unnamed_symbol_3ec960 -> #4 ___lldb_unnamed_symbol_3d47d0 -> #5 ___lldb_unnamed_symbol_5cd0

Captured 16-float accumulator tile at `$rbp-0xa0` (verbatim float32):

```
0.009607374668121338
0.08426520228385925
0.22221490740776062
0.4024548828601837
0.5975451469421387
0.7777851819992065
0.9157348275184631
0.9903926849365234
0.9903926253318787
0.9157347679138184
0.7777850031852722
0.5975452065467834
0.40245479345321655
0.22221478819847107
0.08426520228385925
0.00960734486579895
```

**OBSERVED vs Unit-1 Hann-16: MATCH to 6 decimal places** (maxdiff 0.00e+00)

### 150mm — Unit-2 /Volumes/Base Photos/Light/2018-07-07/L16_02285.lri

- log: `runs/laneB_unit2_fourzoom/150mm_L16_02285.log`
- result json: `runs/laneB_unit2_fourzoom/150mm_L16_02285_result.json`
- libcp_base: `0x108c7a000`  bp_va: `0x108fe3fa4` (`addps (%rdx,%rcx,4),%xmm1`)
- state_after_continue: 5 (5 = stopped at first hit)
- anchorPassed: False (anchor at 0x109066ed0 is a function prologue on this binary)
- regs at first hit: rdi=0x3046418f0 rdx=0x7fc272778040 rax=0x3046418f0 rsi=0x0 rcx=0x0 rip=0x108fe3fa4 rbp=0x3046445b0
- backtrace[0:6]: #0 ___lldb_unnamed_symbol_3661b0 -> #1 ___lldb_unnamed_symbol_365960 -> #2 ___lldb_unnamed_symbol_3ec770 -> #3 ___lldb_unnamed_symbol_3ec960 -> #4 ___lldb_unnamed_symbol_3d47d0 -> #5 ___lldb_unnamed_symbol_5cd0

Captured 16-float accumulator tile at `$rbp-0xa0` (verbatim float32):

```
0.009607374668121338
0.08426520228385925
0.22221490740776062
0.4024548828601837
0.5975451469421387
0.7777851819992065
0.9157348275184631
0.9903926849365234
0.9903926253318787
0.9157347679138184
0.7777850031852722
0.5975452065467834
0.40245479345321655
0.22221478819847107
0.08426520228385925
0.00960734486579895
```

**OBSERVED vs Unit-1 Hann-16: MATCH to 6 decimal places** (maxdiff 0.00e+00)

## Summary table (OBSERVED)

| Zoom  | first-hit | anchorPassed | OBSERVED vs Unit-1 Hann-16 (6 dp) |
|-------|-----------|--------------|-----------------------------------|
| 28mm  | state 5   | False        | MATCH (maxdiff 0.0) |
| 35mm  | state 5   | False        | MATCH (maxdiff 0.0) |
| 70mm  | state 5   | False        | MATCH (maxdiff 0.0) |
| 150mm | state 5   | False        | MATCH (maxdiff 0.0) |

All four Unit-2 captures are float32-identical to each other and to the Unit-1
Hann-16 reference at 6 dp. This is a runtime OBSERVATION of which tile the
accumulator reads on Unit-2; see non_claims.md for scope bounds.
