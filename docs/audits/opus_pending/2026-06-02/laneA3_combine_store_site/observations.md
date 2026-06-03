# Lane A3 — Observations (CORRECTED, machine-verified only)

> See `CORRECTION.md`. The first commit's loop-containment narrative was wrong; this file is the
> corrected, machine-verified version. Every VA/instruction below was grep-confirmed against the dump
> `runs/laneA3_combine_store_site/func_3661b0_accumulator.txt` (reproducible — `commands.txt`).

Source dumps (machine-extracted): `func_365960_outer.txt` (`0x365960`), `func_3661b0_accumulator.txt`
(`0x3661b0`, contains `0x369f80`). VA == file offset. Binary `libcp.dylib` sha256 `b38dc4b3…`.

## O1 — Loop nest enclosing the accumulate (machine-verified branch targets)

```
tile-X loop      0x369140 ........................... 0x369fec  jl 0x369140
  tile-Y loop    0x369160 ......................... 0x369fd9  jl 0x369160
    contributor loop 0x3692f0 ..... 0x369f24  jb 0x3692f0
    (after exit) single Hann accumulate at 0x369f80
```
Confirmed back-branches (grep): `0x369fec jl 0x369140`, `0x369fd9 jl 0x369160`, `0x369f24 jb 0x3692f0`.
The accumulate `0x369f80` is at a higher address than the contributor loop back-branch `0x369f24` and
is reached only after the contributor loop exits (straight-line `0x369f2a..0x369f7f`).

## O2 — Contributor loop is sentinel-gated per-tile coverage (machine-verified)

```
0x3692f0  leaq (%rcx,%rcx,4),%rdx ; 0x3692f4 shlq $0x7,%rdx   ; warp record index, stride 0x280
0x3692f8  movl 0x28(%rdi,%rdx),%eax
0x369306  movq 0x30(%rdi,%rdx),%r12                            ; per-contributor coordinate map ptr
0x36930b  movl (%r12,%rsi,8),%eax
0x36930f  cmpl $0x80000000,%eax                                ; coverage sentinel
0x369314  jne  0x369320                                        ; valid -> process contributor
0x36931b  jmp  0x369f0b                                        ; invalid -> skip to next contributor
```
Loop counter `-0x4358(%rbp)` (`0x369f04 movq -0x4358,%rcx; 0x369f0b incq %rcx`), compared at `0x369f1c`
against a count derived from `(%r9-%rdi)>>7` × magic `0xCCCD…` (i.e. a `0x280`-strided element count;
the warp-record array stride `0x280` is confirmed at `0x368846/0x368853/0x36898c movl $0x280`).
The valid-contributor body runs `0x369320..0x369ec4`, ending `0x369ec4 jmp 0x369f0b` (back to the loop).

## O3 — Shared, loop-invariant output base (machine-verified — unchanged, still correct)

`-0x1710(%rbp)` has exactly three accesses in `0x3661b0`:
```
0x366356  movaps %xmm0,-0x1710(%rbp)   ; zero-init
0x36640c  addq   %rsi, -0x1710(%rbp)   ; ONE pre-loop crop-offset adjust
0x369f65  addq   -0x1710(%rbp),%rdx    ; READ as dest base inside the accumulate
```
No store between any loop top and `0x369f65`. The base is a member-derived cropped view (`0x8(%r15)`
via crop helper `0x374ac0` at `0x3665d5`), not a per-iteration allocation.

## O4 — The accumulate is a Hann overlap-add into the shared base (machine-verified)

```
0x369f4c..0x369f65  dest = (warp_row*stride + col)*16 + base[-0x1710]
0x369f80  movss -0xa0(%rbp,%rsi,4),%xmm0   ; row Hann weight (16 taps, rsi 0..0x10)
0x369f90  movss -0xa0(%rbp,%rcx),%xmm1     ; col Hann weight (16 taps, rcx 0..0x40)
0x369f99  mulss %xmm0,%xmm1
0x369fa1  mulps (%rdi),%xmm1               ; combined-source vec4 * separable weight
0x369fa4  addps (%rdx,%rcx,4),%xmm1        ; += existing output (overlap-add)
0x369fa8  movaps %xmm1,(%rdx,%rcx,4)       ; store back
```
Per output tile this runs once (after the contributor loop), so the `addps` RMW combines **adjacent
tiles' overlapping Hann footprints**, not multiple cameras. The source `(%rdi)` is the prep result of
`0x36e530` (`0x369f34`), fed by whatever the contributor loop produced for this tile.

## Corrected interpretation (LEAD; one sub-question OPEN)

- Cross-camera combination occurs **inside** the contributor loop body `0x369320..0x369ec4`, per tile,
  with a per-(contributor,position) coverage gate on sentinel `0x80000000` (a tile-level acceptance).
- The final write is a single Hann overlap-add into a shared, member-derived output buffer.
- **OPEN / UNVERIFIED:** whether `0x369320..0x369ec4` **sums** valid contributors (true N→1 reduction)
  or **selects** one. This body was not traced. This is the decisive remaining question and is now
  precisely localized.
