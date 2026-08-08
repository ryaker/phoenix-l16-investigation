# Reused LLDB Proof: Prefusion Node-Destination Tele Scan/Score Identity

## Scope

This note reuses the raw packets from
`bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md` to answer a
narrower Lane A question:

For the representative tele node-destination coordinate pair already proven to
be copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination
and later rewritten to `(-1.0, -1.0)` at the same runtime address, do the
sampled `0x216f60` scan/count and `0x218b30` score/materialization stops also
refer to that exact same address?

The answer is yes for the admitted `70mm` and `150mm` samples. This proof is
tele-only and same-address-only. It does not prove all copied node-destination
pairs, wide-tier scan/score identity, same-address branch-step at `0x218bc4`,
whole-vector terminality, image effect, source contribution, reducer closure,
or final acceptance/rejection. Later fresh-run proof in
[bundle_lldb_prefusion_node_dest_218bc4_branch_custody_tele.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_prefusion_node_dest_218bc4_branch_custody_tele.md)
adds the same-address branch effect for one representative pair per tele tier.

## Repo-Local Artifacts

- Reused runtime reports:
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.json`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.json`
- Reused HDR outputs:
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.hdr`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.hdr`
- Reused harness:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- New verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_tele_scan_score_identity.py`

The local static/runtime boundary docs used for interpretation are:

- `bundle_static_prefusion_sentinel_216f60_scan_count_window.md`
- `bundle_lldb_prefusion_sentinel_score_guard_tele.md`
- `bundle_lldb_prefusion_sentinel_score_guard_branch_step_tele.md`
- `bundle_static_runtime_prefusion_sentinel_score_guard_local_loop_tele.md`

No `/tmp` or `/private/tmp` artifact is cited by this proof.

## Runtime Input Reused

The reused `prefusion_node_dest_sentinel_custody` run arms one watchpoint per
canonical focal tier only after the probe has linked:

`finite node-destination copy -> same-address x/y sentinel stores -> full (-1.0, -1.0) at 0x21b930`

This note uses only the tele tiers because those are the tiers whose
same-address watchpoint samples reach the scan/count and score/materialization
families in this run.

| Zoom | LRI | Exit | Step cap | JSON errors | Pair index | Copied bytes | Scan/count sampled PCs | `0x218bc4` guard-operand samples | Watchpoint samples |
|---|---|---:|---|---:|---:|---|---|---:|---:|
| `70mm` | `L16_03434` | `0` | `false` | `0` | `774` | `00005e440000c143` | `0x217048`, `0x217064` | `9` | `64` |
| `150mm` | `L16_02285` | `0` | `false` | `0` | `20` | `0020864400c02b44` | `0x217035`, `0x21703a` | `8` | `64` |

The matched runtime addresses are:

| Zoom | Matched address | Copied pair | Full-sentinel bytes at later samples |
|---|---:|---|---|
| `70mm` | `140217007577136` | `(888.0, 386.0)` | `000080bf000080bf` |
| `150mm` | `140444801498272` | `(1073.0, 687.0)` | `000080bf000080bf` |

## Static Anchors

The scan/count interpretation is inherited from
`bundle_static_prefusion_sentinel_216f60_scan_count_window.md`. Installed-bundle
disassembly shows the local `0x216f60` vector/scalar count paths count only
pairs where both lanes are positive and require at least eight counted entries
before continuing.

The score/materialization guard interpretation is inherited from
`bundle_lldb_prefusion_sentinel_score_guard_tele.md`,
`bundle_lldb_prefusion_sentinel_score_guard_branch_step_tele.md`, and
`bundle_static_runtime_prefusion_sentinel_score_guard_local_loop_tele.md`.
Those prior admitted proofs show that sampled tele sentinel operands at
`0x218bc4` branch to `0x218cb8` and bypass the local positive-coordinate body.
This reused same-address proof does not add branch-step packets for the exact
addresses listed above; it proves those exact addresses reach the same
`0x218bc4` guard-operand site while still full sentinel. The later fresh-run
companion cited above adds exact-address branch-step packets for the same pair
indices in new process instances.

## Validation

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_tele_scan_score_identity.py
70mm: OK same_addr=140217007577136 pair_index=774 copied_hex=00005e440000c143 scan_pcs=0x217048,0x217064 score_guard_hits=9 watch_hits=64
150mm: OK same_addr=140444801498272 pair_index=20 copied_hex=0020864400c02b44 scan_pcs=0x217035,0x21703a score_guard_hits=8 watch_hits=64
```

The verifier rechecks clean completion, no drive step cap, no probe errors,
Radiance HDR output custody, one same-address sentinel match per tele tier,
finite copied pair bytes, full-sentinel bytes after the y-lane store, full
sentinel bytes for every watchpoint sample, and exact matched-address identity
for the sampled scan/count and `0x218bc4` score-guard stops.

## Proven Facts

1. In the admitted `70mm` run, copied node-destination pair index `774` at
   address `140217007577136` changes from finite bytes
   `00005e440000c143` to full-sentinel bytes `000080bf000080bf`.
2. In that same `70mm` run, the exact same address is sampled inside the
   `0x216f60` scan/count window at `0x217048` and `0x217064` while still full
   sentinel.
3. In that same `70mm` run, the exact same address is sampled at the
   `0x218b30` score/materialization guard operand site `0x218bc4` nine times
   while still full sentinel.
4. In the admitted `150mm` run, copied node-destination pair index `20` at
   address `140444801498272` changes from finite bytes
   `0020864400c02b44` to full-sentinel bytes `000080bf000080bf`.
5. In that same `150mm` run, the exact same address is sampled inside the
   `0x216f60` scan/count window at `0x217035` and `0x21703a` while still full
   sentinel.
6. In that same `150mm` run, the exact same address is sampled at the
   `0x218b30` score/materialization guard operand site `0x218bc4` eight times
   while still full sentinel.

## Safe Conclusion

For one representative copied node-destination coordinate pair per tele tier,
the same runtime address is now linked through:

`0x22a61a node-vector destination copy -> same-address sentinel rewrite -> same-address tele scan/count reads -> same-address 0x218bc4 score-guard operand reads`

This strengthens the custody story for the sampled tele route by removing an
address-identity gap between node-destination sentinelization and the already
bounded scan/count and score/materialization local surfaces.

It remains only sampled local non-count / guard-operand evidence. It is not
whole-vector terminality, image-effect proof, source-contribution proof,
reducer closure, or final acceptance/rejection.
