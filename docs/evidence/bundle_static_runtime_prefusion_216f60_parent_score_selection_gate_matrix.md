# Evidence: Prefusion `0x216f60` Parent Score-Selection Gate Matrix

## Scope

This note follows
`bundle_static_runtime_prefusion_216f60_sparse_mirror_score_vector_consumer.md`.
The prior proof joins the `0x219210` callback output vector to its parent
consumer at `0x217a68`, but stops before proving the complete local decision.

This proof closes that local boundary. SHA-pinned installed code plus five
complete LLDB renders show that parent `0x216f60`:

1. selects the minimum callback-return score;
2. rejects when the selected side-output exceeds `0.25`;
3. rejects when the selected side-output exceeds the center side-output;
4. when `r12d > 0`, rejects when the selected score exceeds float32
   `0.8 * center_score`;
5. otherwise materializes the selected 24-byte candidate record, transforms
   its fields through `0x218390` / `0x264980`, and calls `0xf33d0` with
   `r8d = 1`.

The canonical Unit-1 four-focal matrix is joined by one exact-focal Unit-2
`35mm` discriminator. Across those evidence runs, every arithmetic prediction
matches the observed x86 flags, every accepted winner reaches and returns from
`0xf33d0`, and no rejected winner reaches that call.

This is a complete local parent score/side-output selection gate for the
captured invocations. It does not assign public semantic names to either float
vector or the 24-byte record, prove image/source contribution after `0xf33d0`,
close the distributed reducer, or prove final merge acceptance/rejection.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_parent_decision_probe.py`
- LLDB command files:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/parent_decision_28mm.lldb`,
  `parent_decision_35mm.lldb`, `parent_decision_70mm.lldb`,
  `parent_decision_150mm.lldb`, and `parent_decision_unit2_35mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_parent_decision_matrix.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_parent_decision.py`
- Runtime reports and completed HDR outputs:
  `runs/prefusion_216f60_parent_decision/`

No `/tmp` or `/private/tmp` artifact is a dependency.

## Static Decision

The verifier pins:

```text
libcp SHA-256:
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9

window 0x217a68..0x217bc3 SHA-256:
aaaf9c8c42f9340798432511b77c2c65cd042f188f67a78d415612293dba40a7
```

The parent scans callback-return vector `[rbp-0x3f0]` with
`ucomiss candidate,current` / `jae`, leaving the selected byte address in
`rcx`. It then reads the matching side-output from `[rbp-0x410]` and applies:

```text
0x217abe  xmm1 = 0.25f
0x217ac6  ucomiss xmm1, selected_side
0x217ac9  jb 0x217bf8

0x217ad2  ucomiss selected_side, side[center_index]
0x217ad6  ja 0x217bf8

0x217ae3  test r12d, r12d
0x217ae6  jle 0x217aff
0x217ae8  xmm0 = score[center_index]
0x217aed  xmm0 *= 0.8f
0x217af5  ucomiss xmm0, score[selected_index]
0x217af9  jb 0x217bf8
```

For the finite runtime values in this matrix, the accepted predicate is:

```text
selected_side <= 0.25f
and selected_side <= side[center_index]
and (r12d <= 0 or selected_score <= f32(0.8f * score[center_index]))
```

The exact x86 unordered behavior remains encoded by the installed `ucomiss`
and branch sequence: the two `jb` gates also reject unordered operands, while
the middle `ja` gate does not take on unordered operands. No admitted runtime
operand in this matrix is unordered.

On acceptance, `rcx` is converted from the selected score byte offset to its
index, multiplied by the 24-byte record stride, and used at `0x217b0a` to load
the selected record. The local transformation calls are followed by
`0x217bbe -> 0xf33d0`; the runtime call packets all have `r8d = 1`.

## Runtime Matrix

The canonical four-focal runs use Unit-1. The discriminator uses exact-focal
Unit-2 `35mm` file `2018-07-02/L16_01956.lri`.

| Run | Parent packets | Vector counts | Accepted through `0xf33d0` | Side-cap rejects | Ratio rejects |
|---|---:|---|---:|---:|---:|
| Unit-1 `28mm` | 4 | `1089` | 2 | 1 | 1 |
| Unit-1 `35mm` | 4 | `1089` | 3 | 0 | 1 |
| Unit-1 `70mm` | 8 | `21`, `1089` | 3 | 4 | 1 |
| Unit-1 `150mm` | 6 | `21`, `1089` | 3 | 3 | 0 |
| Unit-2 `35mm` | 4 | `1089` | 1 | 2 | 1 |

The observed `1089`-entry packets use center index `544` and `r12d = 2`.
The observed `21`-entry tele packets use center index `10` and `r12d = 0`, so
they bypass the optional score-ratio gate. No packet in this matrix rejects at
the selected-side versus center-side comparison.

These packet counts, selected indices, scores, and rejection frequencies are
evidence-run observations, not stable algorithm constants.

## Index-`505` Correction

The earlier Unit-1 `70mm` consumer proof observed minimum index `505` before
the downstream gates. In this fresh complete `70mm` matrix run, the
corresponding `1089`-entry parent packet again selects index `505`, with:

```text
selected_score       4.601090431
selected_side        0.243055552
center_index         544
center_score         5.654004574
f32(0.8*center)      4.523203850
```

It passes the side cap and center-side comparison, then takes
`0x217af9 -> 0x217bf8` because the selected score exceeds the scaled center
score. It does not materialize the record for `0xf33d0`.

The next `1089`-entry packet selects index `604` with score `4.502223492`,
passes all three gates, reaches the selected-record site with
`rcx == 604`, and completes `0x217bbe -> 0xf33d0 -> 0x217bc3`.

Therefore "minimum callback score" is not equivalent to local acceptance.

## Verification

```bash
python3 -m py_compile \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_parent_decision_probe.py \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_parent_decision.py
bash -n \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_parent_decision_matrix.sh
python3 \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_parent_decision.py
```

Verifier output:

```text
static_parent_decision=OK libcp_sha256=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 window_sha256=aaaf9c8c42f9340798432511b77c2c65cd042f188f67a78d415612293dba40a7
28mm: packets=4 accepted=2 vector_counts=[1089] outcomes=accepted:2,score_ratio_reject:1,side_max_reject:1
35mm: packets=4 accepted=3 vector_counts=[1089] outcomes=accepted:3,score_ratio_reject:1
70mm: packets=8 accepted=3 vector_counts=[21, 1089] outcomes=accepted:3,score_ratio_reject:1,side_max_reject:4
150mm: packets=6 accepted=3 vector_counts=[21, 1089] outcomes=accepted:3,side_max_reject:3
Unit-2 35mm: packets=4 accepted=1 vector_counts=[1089] outcomes=accepted:1,score_ratio_reject:1,side_max_reject:2
```

## Safe Conclusion

Parent `0x216f60` performs a concrete local winner decision over the
`0x219210` callback outputs: minimum score selection, selected-side cap,
selected-side versus center-side comparison, optional selected-score versus
`0.8 * center_score` comparison, then selected 24-byte record
materialization and `0xf33d0` only for accepted winners. The mechanism is
runtime-observed across all four canonical focal tiers and one exact-focal
second-body discriminator.

This admits local decision logic and custody only. Public vector/record names,
the effect after `0xf33d0`, image/source contribution, whole distributed
reducer closure, and final merge acceptance/rejection remain open.
