# Direct Payload Candidate Gate / C6, Four-Zoom Runtime Proof

**Date:** 2026-05-21
**Status:** admitted evidence candidate for `CLM-PREFUSION-001` / `CLM-C6-001`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This note runtime-tests the direct payload candidate loop around
`libcp+0x3e0330` after two other plausible C6 routes were excluded:

- visible `src1` keyed-helper / vector-builder boundary:
  `0x1bdc80` / `0x1be750` / `0x1be270`
- visible `src1` projection field-pack dispatcher boundary:
  `0x3f6170` / `0x3f6200` / `0x3f6940`

The tested question is narrow:

Does tele key `15` / C6 enter this candidate loop, and if so, where does it stop
before the already-observed projection dispatcher call at `0x3e05f5 -> 0x3f6170`?

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probe

Reusable harness:

- [direct_payload_candidate_gate_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/direct_payload_candidate_gate/direct_payload_candidate_gate_probe.py)

LLDB scripts:

- [direct_payload_candidate_gate_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/direct_payload_candidate_gate/direct_payload_candidate_gate_28mm.lldb)
- [direct_payload_candidate_gate_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/direct_payload_candidate_gate/direct_payload_candidate_gate_35mm.lldb)
- [direct_payload_candidate_gate_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/direct_payload_candidate_gate/direct_payload_candidate_gate_70mm.lldb)
- [direct_payload_candidate_gate_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/direct_payload_candidate_gate/direct_payload_candidate_gate_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/direct_payload_candidate_gate/`.

## Static Gate Shape

Installed-bundle disassembly around the tested gate:

```asm
3e03e0: 45 8b 2e        movl  (%r14), %r13d
3e03f0: e8 7b e5 dd ff  callq 0x1be970
3e03f5: 48 8b 85 ...    movq  -0x98(%rbp), %rax
3e0403: 8a 58 30        movb  0x30(%rax), %bl
3e0406: 48 85 ff        testq %rdi, %rdi
3e0410: 84 db           testb %bl, %bl
3e0412: 0f 84 ...       je    0x3e0880
3e0418: ...             active-flag pass path
3e0450: ...             key-class/state-class branch
3e05f5: e8 ...          callq 0x3f6170
```

The runtime probe captures the loop key after load, the `object+0x30` byte at
`0x3e0406`, the flag test at `0x3e0410`, the class-compare path, and the
dispatcher call/return pair.

## Instrumented Sites

| VA | Probe label | Meaning captured by probe |
|---:|---|---|
| `0x3e0330` | `constructor_entry_3e0330` | loop-owner entry |
| `0x3e03e3` | `loop_key_loaded_3e03e3` | key in `r13d` immediately after `movl (%r14), %r13d` |
| `0x3e0406` | `object_flag_loaded_3e0406` | `bl` after `movb 0x30(%rax), %bl`; also reads `object+0x30` |
| `0x3e0410` | `active_flag_test_3e0410` | active-byte branch test |
| `0x3e0418` | `active_flag_pass_3e0418` | branch path after nonzero active byte |
| `0x3e0450` | `class_compare_3e0450` | key class versus state class |
| `0x3e0456` | `cross_class_pass_3e0456` | cross-category path after class mismatch |
| `0x3e05f5` | `dispatcher_call_3e05f5` | callsite into `0x3f6170` |
| `0x3e05fa` | `dispatcher_return_3e05fa` | return from `0x3f6170` |

## Four-Zoom Runtime Result

All four complete renders exited with status `0`. No probe reported runtime read
errors.

| Zoom | loop keys | `object+0x30` zero keys | same-class skipped keys | cross-class dispatcher keys |
|---|---|---|---|---|
| `28mm` | `0..9` | none | `0..4` | `5..9` |
| `35mm` | `0..9` | none | `0..4` | `5..9` |
| `70mm` | `5..15` | `15` | `5..9` | `10..14` |
| `150mm` | `5..15` | `15` | `5..9` | `10..14` |

Total site counts:

| Zoom | loop keys | object-byte loads | active-byte passes | class compares | cross passes | dispatcher calls / returns |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `10` | `10` | `10` | `10` | `5` | `5 / 5` |
| `35mm` | `10` | `10` | `10` | `10` | `5` | `5 / 5` |
| `70mm` | `11` | `11` | `10` | `10` | `5` | `5 / 5` |
| `150mm` | `11` | `11` | `10` | `10` | `5` | `5 / 5` |

Tele key `15` details:

| Zoom | key | `object+0x30` byte | active test | active pass | class compare | dispatcher call |
|---|---:|---:|---:|---:|---:|---:|
| `70mm` | `15` | `0` | `1` | `0` | `0` | `0` |
| `150mm` | `15` | `0` | `1` | `0` | `0` | `0` |

Representative raw sample fields for key `15`:

| Zoom | runtime `object` pointer | `object+0x30` byte |
|---|---:|---:|
| `70mm` | `140385216153504` | `0` |
| `150mm` | `140195944125744` | `0` |

The pointer values are process-local evidence samples, not algorithm constants.

## Safe Conclusions

- This direct candidate loop is live under the canonical bridge HDR quartet.
- At `28mm` and `35mm`, the loop visits keys `0..9`; every key has
  `object+0x30 = 1`.
- At `70mm` and `150mm`, the loop visits keys `5..15`.
- At `70mm` and `150mm`, key `15` reaches the loop, but its `object+0x30` byte
  is `0`, so it takes the `0x3e0412 -> 0x3e0880` skip before class compare and
  before the `0x3e05f5 -> 0x3f6170` dispatcher call.
- At `70mm` and `150mm`, keys `10..14` are the only cross-category keys from
  this loop that reach the dispatcher call.
- Combined with existing camera-ID evidence that maps key `15` to C6, this
  proves C6 is filtered at this direct candidate gate under the canonical tele
  bridge HDR runs.

## Non-Conclusions

- Later constructor/watchpoint proof establishes the tele key `15`
  `object+0x30 = 0` value observed here as post-constructor mutated state:
  key `15` is constructed with item `+0x30 = 1` and later cleared at
  `libcp+0x3c90a5`.
- This does not prove C6 is unused globally.
- This does not prove no alternate C6 path exists outside this direct candidate
  loop.
- This does not prove the public semantic name of `object+0x30`.
- This does not identify semantic `src1` / `src2` contents.
- This does not close final merge acceptance / rejection logic.
- This does not prove the same key behavior under non-bridge profiles, other
  render/export modes, or untested LRIs.
