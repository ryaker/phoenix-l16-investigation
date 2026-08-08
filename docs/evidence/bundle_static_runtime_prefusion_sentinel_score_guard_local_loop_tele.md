# Static + Runtime Proof: Prefusion Sentinel Score-Guard Local Loop Effect, Tele Samples

## Scope

This note follows
`bundle_lldb_prefusion_sentinel_score_guard_branch_step_tele.md`.

The branch-step proof already shows that selected watched tele sentinel
coordinate pairs stop at `0x218bc4` and single-step directly to `0x218cb8`.
This note asks the next narrower question: what local loop work does that skip
target bypass in the installed `0x218b30` body?

It proves only that, for the admitted watched `70mm` / `150mm` branch-step
samples, the `0x218bc4 -> 0x218cb8` branch bypasses the local
positive-coordinate body that accumulates `xmm1`, updates `r10d`, and increments
`r9d`; the same static body later derives the value stored through `r14` from
`r9d` and `r10d`. This is local non-count / non-score evidence for those
sampled sentinel iterations.

It does not prove all sentinel entries, whole-vector terminality, image-level
source contribution, public acceptance semantics, semantic `src1` / `src2`
contents, reducer closure, or final acceptance / rejection.

## Repo-Local Artifacts

- Runtime branch-step probe:
  `tools/lldb_probes/prefusion_sentinel_score_guard/prefusion_sentinel_score_guard_probe.py`
- Runtime branch-step LLDB scripts:
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_branch_70mm.lldb`
  `tools/lldb_probes/prefusion_sentinel_score_guard/sentinel_score_guard_branch_150mm.lldb`
- Runtime branch-step verifier:
  `tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard_branch_step.py`
- Local-loop verifier:
  `tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard_local_loop.py`
- Static disassembly input:
  `runs/prefusion_node_sentinel_downstream_watch/static_disasm_218b30_218f90.log`
- Runtime JSON / HDR inputs:
  `runs/prefusion_sentinel_score_guard_branch_step/`

No `/tmp` or `/private/tmp` artifact is cited by this proof.

## Static Anchor

Installed-bundle disassembly of `0x218b30` shows the local loop structure:

```asm
0x218bc0: ucomiss (%rdx,%rbx,8), %xmm0
0x218bc4: jae    0x218cb8
0x218bca: movss  0x4(%rdx,%rbx,8), %xmm3
0x218bd0: ucomiss %xmm0, %xmm3
0x218bd3: jbe    0x218cb8
...
0x218ca4: addss  %xmm3, %xmm1
0x218cab: addl   %ecx, %r10d
0x218cae: incl   %r9d
...
0x218cb8: incq   %rbx
...
0x218cd6: cvtsi2ss %r9d, %xmm2
...
0x218cf2: cvtsi2ss %r10d, %xmm2
0x218cfb: movss  %xmm2, (%r14)
```

The verifier checks these address/instruction anchors from the static
disassembly log and checks ordering: the `xmm1` accumulation, `r10d` update,
and `r9d` increment lie between the `0x218bc4` branch and its `0x218cb8`
target, while the later `r14` store is derived after the `r9d` / `r10d`
conversions.

## Runtime Inputs

This note reuses the admitted branch-step reports:

- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_70mm.json`
- `runs/prefusion_sentinel_score_guard_branch_step/sentinel_score_guard_branch_150mm.json`

Both runs completed with exit status `0`, no probe errors, no drive step cap,
and Radiance HDR outputs.

## Runtime Results

| Zoom | LRI | Branch-step traces | Sentinel operand | Direct branch target |
|---|---|---:|---|---|
| `70mm` | `L16_03434` | `6` | `000080bf000080bf` | `0x218cb8` |
| `150mm` | `L16_02285` | `3` | `000080bf000080bf` | `0x218cb8` |

Every admitted trace still reads the watched pair as `(-1.0, -1.0)`, records
runtime flags with `CF = 0`, and single-steps from `0x218bc4` to `0x218cb8`.

Verifier output:

```text
$ python3 tools/lldb_probes/prefusion_sentinel_score_guard/verify_sentinel_score_guard_local_loop.py
70mm: OK local_loop_skip_traces=6 skip_target=0x218cb8 sentinel_pairs=6
150mm: OK local_loop_skip_traces=3 skip_target=0x218cb8 sentinel_pairs=3
```

The verifier rechecks the static disassembly anchors, clean runtime completion,
HDR output custody, exact branch-trace counts, still-sentinel operands, runtime
flags, and direct branch targets.

## Proven Facts

1. The static `0x218b30` loop sends nonpositive x-lane inputs from `0x218bc4`
   directly to `0x218cb8`.
2. The same skip target bypasses the y-lane read and the local body containing
   `xmm1` accumulation, `r10d` update, and `r9d` increment.
3. The same body later derives the value stored through `r14` after converting
   `r9d` and `r10d`.
4. In the admitted `70mm` branch-step run, six watched sentinel-coordinate
   stops at `0x218bc4` step directly to `0x218cb8`.
5. In the admitted `150mm` branch-step run, three watched
   sentinel-coordinate stops at `0x218bc4` step directly to `0x218cb8`.

## Safe Conclusion

For the admitted tele samples, watched `(-1.0, -1.0)` sentinel coordinate pairs
that reach the `0x218b30` guard are not just branch-skipped in the abstract:
they bypass the local positive-coordinate accumulation/count body that feeds
this helper's later score/count store.

This moves the sampled tele guard fact from "branch target reached" to "local
non-count / non-score for those sampled iterations." It still does not prove
whole-vector terminality, image-level contribution, reducer closure, or final
acceptance / rejection.
