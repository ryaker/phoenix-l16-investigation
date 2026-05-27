# LLDB IRAMP Partner Gate Four-Zoom Evidence

**Date:** 2026-05-12
**Status:** Partial evidence admitted for canonical review.
**Scope:** Corrected canonical bridge HDR quartet only.

This document verifies the local IRAMP partner-vector gate around `libcp+0x3692dc..0x3692e4` and the first SAD instruction at `libcp+0x3694b1`.

It does not prove the upstream logic that decides when a partner record is inserted.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harnesses now live in the repo:

- `tools/lldb_probes/iramp_partner_gate/gate_first_probe.py`
- `tools/lldb_probes/iramp_partner_gate/sad_first_probe.py`
- `tools/lldb_probes/iramp_partner_gate/gate_*_first_*.lldb`
- `tools/lldb_probes/iramp_partner_gate/sad_first_*.lldb`

Generated render outputs go under ignored `runs/iramp_partner_gate/`.

The earlier `/private/tmp/l16_*` probe scripts and outputs were deleted after the harness was moved into the repo.

## Static Proof

Installed bundle: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The local gate:

```asm
0x3692ce  movq -0x1800(%rbp), %rdi
0x3692d5  movq -0x17f8(%rbp), %r9
0x3692dc  cmpq %rdi, %r9
0x3692df  movl $0x0, %ecx
0x3692e4  je 0x369f2a
0x3692f0  leaq (%rcx,%rcx,4), %rdx
```

Interpretation:

- `[rbp-0x1800]` is the local vector begin pointer.
- `[rbp-0x17f8]` is the local vector end pointer.
- `begin == end` jumps to `0x369f2a`.
- `begin != end` falls through to the block-matching path.

The first SAD instruction on the fall-through path:

```asm
0x3694b1  mpsadbw $0x0, %xmm7, %xmm6
```

The empty-vector target reaches the already known accumulator region:

```asm
0x369f2a  movl %r8d, %r12d
0x369f34  callq 0x36e530
0x369f80  movss -0xa0(%rbp,%rsi,4), %xmm0
0x369fa1  mulps (%rdi), %xmm1
0x369fa4  addps (%rdx,%rcx,4), %xmm1
0x369fa8  movaps %xmm1, (%rdx,%rcx,4)
```

Partner-record stride:

```asm
0x366a83  shlq $0x7, %rax
0x366a87  leaq (%rax,%rax,4), %rdi
0x368846  movl $0x280, %esi
0x368853  addq $0x280, %rbx
0x36885a  movq %rbx, -0x17f8(%rbp)
```

Interpretation:

- Allocation size is `N * 0x280`.
- Append / end-pointer advance is `+0x280`.
- Runtime `diff / 0x280` is the local partner-record count for this vector.

## Runtime Proof Summary

| Zoom | Empty gate observed | Non-empty gate observed | First SAD observed | Notes |
|---|---:|---:|---:|---|
| `28mm` | yes, `diff=0` | yes, `diff=640`, `1 * 0x280` | yes | all from repo-local probes |
| `35mm` | not proven | yes, `diff=640`, `1 * 0x280` | yes | empty-only run was stopped at 8 percent without a hit; no absence claim |
| `70mm` | yes, `diff=0` | yes, `diff=640`, `1 * 0x280` | yes | all from repo-local first-hit probes |
| `150mm` | not proven | yes, `diff=1920`, `3 * 0x280` | yes | empty-only start-under-LLDB run hit known instrumentation race before gate; no absence claim |

## Runtime Packets

### 28mm

Empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 28mm empty gate L16_02130 2018-07-23
gate {'rbp': 12956436224, 'begin': 140226664108544, 'end': 140226664108544, 'diff': 0, 'npartners': 0, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 28mm empty gate L16_02130 2018-07-23
```

Non-empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 28mm nonempty gate L16_02130 2018-07-23
gate {'rbp': 12958045952, 'begin': 140504480228864, 'end': 140504480229504, 'diff': 640, 'npartners': 1, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 28mm nonempty gate L16_02130 2018-07-23
```

First SAD:

```text
L16_SAD_PROBE_BEGIN 28mm L16_02130 2018-07-23
sad {'rbp': 12955899648, 'rcx': 140261579188801, 'rdi': 140261579188801, 'r9': 4294967280}
L16_SAD_PROBE_END 28mm L16_02130 2018-07-23
```

### 35mm

Non-empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 35mm nonempty gate L16_03041 2018-12-26
gate {'rbp': 12954826160, 'begin': 140460530110976, 'end': 140460530111616, 'diff': 640, 'npartners': 1, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 35mm nonempty gate L16_03041 2018-12-26
```

First SAD:

```text
L16_SAD_PROBE_BEGIN 35mm L16_03041 2018-12-26
sad {'rbp': 12954289584, 'rcx': 140166804474586, 'rdi': 140166804474586, 'r9': 4294967280}
L16_SAD_PROBE_END 35mm L16_03041 2018-12-26
```

### 70mm

Empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 70mm empty gate L16_03434 2019-05-18
gate {'rbp': 12955362736, 'begin': 140438736518656, 'end': 140438736518656, 'diff': 0, 'npartners': 0, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 70mm empty gate L16_03434 2019-05-18
```

Non-empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 70mm nonempty gate L16_03434 2019-05-18
gate {'rbp': 12955362736, 'begin': 140651287052800, 'end': 140651287053440, 'diff': 640, 'npartners': 1, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 70mm nonempty gate L16_03434 2019-05-18
```

First SAD:

```text
L16_SAD_PROBE_BEGIN 70mm L16_03434 2019-05-18
sad {'rbp': 12958045616, 'rcx': 140329735029005, 'rdi': 140329735029005, 'r9': 4294967280}
L16_SAD_PROBE_END 70mm L16_03434 2019-05-18
```

### 150mm

Non-empty gate:

```text
L16_GATE_FIRST_PROBE_BEGIN 150mm nonempty gate L16_02285 2018-07-29
gate {'rbp': 12954289584, 'begin': 140200115227136, 'end': 140200115229056, 'diff': 1920, 'npartners': 3, 'aligned_0x280': True}
L16_GATE_FIRST_PROBE_END 150mm nonempty gate L16_02285 2018-07-29
```

First SAD:

```text
L16_SAD_PROBE_BEGIN 150mm L16_02285 2018-07-29
sad {'rbp': 12958045616, 'rcx': 140346788413700, 'rdi': 140346788413700, 'r9': 4294967280}
L16_SAD_PROBE_END 150mm L16_02285 2018-07-29
```

## Failed / Non-Admitted Attempts

- Combined `gate_oneshot_70mm.lldb` crashed at `libcp+0x2e945d` before any gate packet. This is treated as instrumentation failure only.
- `gate_empty_first_150mm.lldb` also crashed at `libcp+0x2e945d` before any gate packet. This is treated as instrumentation failure only.
- `gate_empty_first_35mm.lldb` reached 8 percent without a hit and was stopped manually. This is not evidence of absence.

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- The local IRAMP partner gate compares vector begin/end at `0x3692dc`.
- The empty-vector branch target is `0x369f2a`, which proceeds to the same accumulator region around `0x369fa1`.
- The non-empty path falls through toward the SAD chain beginning at `0x3694b1`.
- Partner-record elements are `0x280` bytes.
- Runtime non-empty partner-vector states and first SAD hits are observed at `28mm`, `35mm`, `70mm`, and `150mm`.
- Runtime empty partner-vector states are observed at `28mm` and `70mm`.

## Not Proven Here

- Runtime empty-gate hits at `35mm` or `150mm`.
- The upstream rule that decides whether a `0x280` partner record is inserted.
- The contents of the `0x280` partner record.
- WTA, sub-pixel refinement, bilinear sample, or final acceptance/rejection math.
- Any claim that 28mm never runs SAD. The 28mm first-SAD probe refutes that absolute.
