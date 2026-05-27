# Stereo Candidate Gate / C6, Four-Zoom Runtime Proof

**Date:** 2026-05-21
**Status:** admitted evidence candidate for `CLM-C6-001` and the visible
`+0x678/+0x680` / `0x3f2c40` constructor branch
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This note runtime-tests the keyed-record loop inside the already-bounded
`0x3f2c40` constructor branch, historically labeled by older tooling as the
`StereoAsyncAPI` C2 constructor.

The tested question is narrow:

Does tele key `15` / C6 enter this stereo-side candidate/keyed-record loop, and
if so, does it pass the `object+0x30` byte gate into the downstream keyed-record
insert/copy calls?

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

- [stereo_candidate_gate_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereo_candidate_gate/stereo_candidate_gate_probe.py)

LLDB scripts:

- [stereo_candidate_gate_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereo_candidate_gate/stereo_candidate_gate_28mm.lldb)
- [stereo_candidate_gate_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereo_candidate_gate/stereo_candidate_gate_35mm.lldb)
- [stereo_candidate_gate_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereo_candidate_gate/stereo_candidate_gate_70mm.lldb)
- [stereo_candidate_gate_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereo_candidate_gate/stereo_candidate_gate_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/stereo_candidate_gate/`.

## Static Gate Shape

Installed-bundle disassembly around the tested loop:

```asm
3f3090: 4d 39 f4                      cmpq   %r14, %r12
3f3093: 0f 84 b9 00 00 00             je     0x3f3152
3f30a0: 41 8b 14 24                   movl   (%r12), %edx
3f30a4: 49 8b b5 e0 00 00 00          movq   0xe0(%r13), %rsi
3f30ab: 4c 89 ff                      movq   %r15, %rdi
3f30ae: e8 bd b8 dc ff                callq  0x1be970
3f30b3: 48 8b bd c8 fb ff ff          movq   -0x438(%rbp), %rdi
3f30ba: 80 7f 30 00                   cmpb   $0x0, 0x30(%rdi)
3f30be: 74 6d                         je     0x3f312d
3f30c0: 48 8b 85 48 f8 ff ff          movq   -0x7b8(%rbp), %rax
3f30ca: e8 51 f6 cf ff                callq  0xf2720
3f30cf: 89 85 c4 fb ff ff             movl   %eax, -0x43c(%rbp)
3f30df: e8 ec a9 f9 ff                callq  0x38dad0
3f30ee: e8 9d e4 e4 ff                callq  0x241590
3f30fd: 48 8b bd c8 fb ff ff          movq   -0x438(%rbp), %rdi
3f3104: e8 17 f6 cf ff                callq  0xf2720
3f3109: 89 85 c0 fb ff ff             movl   %eax, -0x440(%rbp)
3f3119: e8 b2 a9 f9 ff                callq  0x38dad0
3f3128: e8 83 e4 e4 ff                callq  0x2415b0
3f312d: ...                           cleanup / advance
```

The runtime probe captures the loop key, the resolved object pointer, the
`object+0x30` byte at `0x3f30ba`, the post-gate path at `0x3f30c0`, and the two
`0xf2720` getter callsites at `0x3f30ca` and `0x3f3104`.

## Instrumented Sites

| VA | Probe label | Meaning captured by probe |
|---:|---|---|
| `0x3f2c40` | `constructor_entry_3f2c40` | constructor branch entry |
| `0x3f30a4` | `loop_key_loaded_3f30a4` | current int32 key from the loop vector |
| `0x3f30ba` | `object_flag_compare_3f30ba` | object pointer in `rdi` and byte at `object+0x30` |
| `0x3f30c0` | `active_flag_pass_3f30c0` | branch path reached only after nonzero `object+0x30` |
| `0x3f30ca` | `first_getter_call_3f30ca` | first `0xf2720(object)` getter call after the gate |
| `0x3f3104` | `second_getter_call_3f3104` | second `0xf2720(object)` getter call after the gate |

## Four-Zoom Runtime Result

All four complete renders exited with status `0`. No probe reported runtime read
errors, and no run hit the probe's step cap.

| Zoom | loop keys | `object+0x30` zero keys | keys reaching post-gate path | keys reaching both getter calls |
|---|---|---|---|---|
| `28mm` | `0..9` | none | `0..9` | `0..9` |
| `35mm` | `0..9` | none | `0..9` | `0..9` |
| `70mm` | `5..15` | `15` | `5..14` | `5..14` |
| `150mm` | `5..15` | `15` | `5..14` | `5..14` |

Total site counts:

| Zoom | constructor entries | loop keys | object-byte compares | active-byte passes | first getter calls | second getter calls |
|---|---:|---:|---:|---:|---:|---:|
| `28mm` | `1` | `10` | `10` | `10` | `10` | `10` |
| `35mm` | `1` | `10` | `10` | `10` | `10` | `10` |
| `70mm` | `1` | `11` | `11` | `10` | `10` | `10` |
| `150mm` | `1` | `11` | `11` | `10` | `10` | `10` |

Tele key `15` details:

| Zoom | key | `object+0x30` byte | active pass | first getter call | second getter call |
|---|---:|---:|---:|---:|---:|
| `70mm` | `15` | `0` | `0` | `0` | `0` |
| `150mm` | `15` | `0` | `0` | `0` | `0` |

Representative raw sample fields for key `15`:

| Zoom | runtime `object` pointer | `object+0x30` byte |
|---|---:|---:|
| `70mm` | `140242008023584` | `0` |
| `150mm` | `140268619873200` | `0` |

The pointer values are process-local evidence samples, not algorithm constants.

## Safe Conclusions

- The `0x3f2c40` constructor branch is live once per canonical bridge HDR render
  in the four tested zooms.
- The tested stereo-side keyed-record loop visits keys `0..9` at `28mm` and
  `35mm`; every visited key has `object+0x30 = 1`.
- The tested stereo-side keyed-record loop visits keys `5..15` at `70mm` and
  `150mm`.
- At `70mm` and `150mm`, key `15` reaches this loop, but its `object+0x30` byte
  is `0`, so it takes the `0x3f30be -> 0x3f312d` skip before the post-gate path
  and before both `0xf2720` getter callsites.
- At `70mm` and `150mm`, keys `5..14` are the only keys from this loop that
  pass the byte gate and reach both getter callsites.
- Combined with existing camera-ID evidence that maps key `15` to C6, this
  proves C6 is filtered at this stereo-side keyed-record gate under the
  canonical tele bridge HDR runs.

## Non-Conclusions

- Later constructor/watchpoint proof establishes the tele key `15`
  `object+0x30 = 0` value observed here as post-constructor mutated state:
  key `15` is constructed with item `+0x30 = 1` and later cleared at
  `libcp+0x3c90a5`.
- This does not prove C6 is unused globally.
- This does not prove no alternate C6 path exists outside this tested
  stereo-side keyed-record loop.
- This does not prove the public semantic name of `object+0x30`.
- This does not identify semantic `src1` / `src2` contents.
- This does not close producer-side pair-grid public semantics.
- This does not close final merge acceptance / rejection logic.
- This does not prove the same key behavior under non-bridge profiles, other
  render/export modes, or untested LRIs.
