# Evidence: Tele Node-Destination `0x218bc4` Guard Branch Custody

## Scope

This note extends the admitted same-address tele scan/score identity proof for
one representative copied node-destination pair at `70mm` and one at `150mm`.
It proves that each watched pair, still full `(-1.0,-1.0)`, takes the
`0x218bc4 -> 0x218cb8` positive-coordinate skip branch and therefore does not
contribute to this loop's local score sum or two local counters.

This is representative same-address branch-effect proof for two Unit-1 tele
captures. It is not all-pairs terminality, a public acceptance semantic, an
image/source-contribution result, reducer closure, or final acceptance.

## Artifacts

- Reused/extended runtime callback:
  [prefusion_node_dest_sentinel_custody_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py)
- LLDB scripts:
  [node_dest_218bc4_branch_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_218bc4_branch_70mm.lldb),
  [node_dest_218bc4_branch_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_218bc4_branch_150mm.lldb)
- Runner:
  [run_218bc4_branch_tele.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_218bc4_branch_tele.sh)
- Runtime verifier:
  [verify_node_dest_218bc4_branch_custody.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_218bc4_branch_custody.py)
- Static effect verifier:
  [verify_218bc4_guard_effect_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_218bc4_guard_effect_static.py)
- Raw reports/logs/HDR outputs:
  `runs/prefusion_node_dest_218bc4_branch_custody/`

## Runtime Custody

Both no-auto-LRIS renders complete with process status `0`, no probe errors,
no drive-step cap, and valid Radiance HDR output.

| Tier | Copied pair index | Pair at copy | Same address at guard | Branch |
|---|---:|---:|---:|---:|
| `70mm` | `774` | finite, `00005e440000c143` | full `(-1,-1)` | `0x218bc4 -> 0x218cb8` |
| `150mm` | `20` | finite, `0020864400c02b44` | full `(-1,-1)` | `0x218bc4 -> 0x218cb8` |

For each tier, the verifier joins:

```text
finite pair copied into 0x22a61a destination
  -> same address x-store at 0x21b923
  -> same address y-store at 0x21b92a
  -> full sentinel at that address
  -> same-address hardware watch stop at 0x218bc4
  -> rflags after ucomiss: CF=0, jae taken
  -> one-instruction branch step lands at 0x218cb8
```

Each report has one admitted sentinel match, one armed watchpoint, one
`0x218bc4` guard trace, and no observed non-skip guard trace for the watched
pair. The pair stays full sentinel in every sampled downstream watch stop.

## Static Local Effect

The installed-binary verifier SHA-pins and Capstone-decodes
`0x218b77..0x218cbe`.

`xmm0` is zeroed before the loop. The two coordinate gates are:

```text
0x218bc0  ucomiss xmm0, pair.x
0x218bc4  jae 0x218cb8          # skip when pair.x <= 0

0x218bca  load pair.y
0x218bd0  ucomiss pair.y, xmm0
0x218bd3  jbe 0x218cb8          # skip when pair.y <= 0
```

The skipped interval `0x218bca..0x218cb4` contains the local transform/score
work and these concrete effects:

```text
0x218ca4  xmm1 += min(abs(score), threshold)  # local score sum
0x218cab  r10d += (abs(score) > threshold)    # over-threshold count
0x218cae  r9d++                               # positive-pair count
```

The common target `0x218cb8` increments only the loop index. Therefore the two
watched full-sentinel pairs skip pair-y loading, transform/score formation,
score accumulation, threshold-count increment, and positive-pair-count
increment in this local loop.

## Admission

Safe statement:

```text
For one same-address sentinelized node-destination pair in each canonical tele
render, the full (-1,-1) pair takes the x<=0 branch at 0x218bc4 directly to
0x218cb8 and contributes nothing to this loop's local score sum,
over-threshold count, or positive-pair count.
```

This closes the branch consequence that was left open by the earlier operand
samples. It does not prove that every sentinelized pair reaches this loop,
that no alias or alternate route consumes the pair, that the pair is terminal
for the shared Triangulator solve, or that C6/final image contribution is
excluded.

No second-body rerun is needed for this admission: the local branch mechanism
is byte-defined and the claim is limited to the two watched Unit-1 tele pairs.
Cross-unit work becomes relevant only before generalizing pair incidence or
terminal behavior.

## Verification

Commands:

```bash
bash tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_218bc4_branch_tele.sh
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_218bc4_guard_effect_static.py
```

Output:

```text
70mm: OK same_addr=140470039189552 pair_index=774 copied_hex=00005e440000c143 guard_hits=1 watch_hits=3 branch=0x218bc4->0x218cb8
150mm: OK same_addr=140541631275168 pair_index=20 copied_hex=0020864400c02b44 guard_hits=1 watch_hits=3 branch=0x218bc4->0x218cb8

window=0x218b77..0x218cbe sha256=0fe5e4f6ee87a19218f9338dafb89427748bbb6f2b9776b1bd28747e94eee89b
guard=x<=0@0x218bc4 or y<=0@0x218bd3 -> 0x218cb8
skip_interval=0x218bca..0x218cb4
skipped_effects=score_sum_xmm1,over_threshold_count_r10d,positive_pair_count_r9d
```
