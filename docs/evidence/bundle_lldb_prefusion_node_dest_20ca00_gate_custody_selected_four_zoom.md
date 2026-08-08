# Bundle + LLDB Proof: Prefusion Node-Destination Same-Address `0x20ca00` Gate Custody, Selected Four-Zoom Representatives

## Scope

This note extends:

- `bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md`
- `bundle_lldb_prefusion_node_dest_20ca00_source_copy_four_zoom.md`
- `bundle_lldb_prefusion_node_dest_20ca00_source_index_four_zoom.md`
- `bundle_lldb_prefusion_20ca00_copied_sentinel_gate_four_zoom.md`

The earlier same-address proof stopped at the `0x20ca00` second local vector
copy as a source read. The earlier copied-slot gate proof reached the
`0x20d363` positive-coordinate gate for one `70mm` watched sentinel, but did
not carry the prior `0x22a61a` copied node-destination identity into that gate
trace.

This selected-representative proof joins those boundaries:

1. a finite pair is copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f`
   node-vector destination,
2. that same runtime address is rewritten to full `(-1.0, -1.0)` through
   `0x21b923` / `0x21b92a`,
3. `0xe0ae0` source-reads that same address under caller return `0x20d309`,
4. the source index equals the parent `0x20ca00` gate index,
5. a destination watchpoint follows the computed copied slot,
6. the copied destination is read at `0x20d363` while still full sentinel,
7. and the branch steps to skip target `0x20d565`.

That full chain is admitted for one selected `28mm` representative and one
selected `70mm` representative. The selected `35mm` and `150mm` packets are
scoped no-match observations only.

This is representative local gate-skip custody. It is not all-pairs proof,
whole-vector terminality, image/source-contribution proof, reducer closure, or
final acceptance/rejection.

## Repo-Local Artifacts

- Shared probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_node_dest_sentinel_custody_probe.py`
- Selected LLDB scripts:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_28mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_35mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_70mm.lldb`
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_gate_target_150mm.lldb`
- Selected runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_gate_selected_four_zoom.sh`
- Generic consistency verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_gate_custody.py`
- Selected evidence verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_gate_selected_custody.py`
- Selected raw reports:
  `runs/prefusion_node_dest_20ca00_gate_target_custody/node_dest_20ca00_gate_target_28mm.json`
  `runs/prefusion_node_dest_20ca00_gate_target_custody/node_dest_20ca00_gate_target_35mm.json`
  `runs/prefusion_node_dest_20ca00_gate_custody/node_dest_20ca00_gate_70mm.json`
  `runs/prefusion_node_dest_20ca00_gate_target_custody/node_dest_20ca00_gate_target_150mm.json`
- Selected HDR outputs:
  the matching `.hdr` files beside those JSON reports.

The target index lists in the target scripts are instrumentation steering
derived from previously observed gate-index windows. They are not admitted as
public semantics or exhaustive gate-index sets.

## Static Anchors

The admitted installed-bundle windows are:

```text
0x22a61a: callq 0xe8e70
0x22a61f: return after node-vector copy

0x21b923: write x lane = -1.0
0x21b92a: write y lane = -1.0
0x21b930: completed pair after sentinel writes

0x20d2f9: leaq 0x28(%rbx), %rsi
0x20d2fd: leaq -0xe0(%rbp), %rdi
0x20d304: callq 0xe0ae0
0x20d309: return after second local vector copy

0x20d34d: movq -0xe0(%rbp), %r15
0x20d354: movq -0x2a0(%rbp), %rax
0x20d35e: ucomiss (%r15,%rax,8), %xmm0
0x20d363: jae 0x20d565
```

The probe reconstructs the source index from the `e0ae0` source-vector header,
reads the parent gate index from the `0x20ca00` frame, computes the destination
slot from the live source/destination cursors, and only arms the destination
watchpoint when `source_index == gate_index`.

## Selected Runtime Results

| Zoom | Selected copied pair indices | Copied finite bytes for positive/sole representative | Source watch hits | `0x20d309` source-copy packets | Index matches | Gate traces | Scope |
|---|---|---|---:|---:|---:|---:|---|
| `28mm` | `264`, `287`, `5394` | index `5394`: `0040ea4400007a44` | `1292` | `1258` | `1` | `1` | exact representative gate skip |
| `35mm` | `3673`, `5411`, `5577` | none positive | `16384` | `2185` | `0` | `0` | source-watch cap reached |
| `70mm` | `77`, `740`, `1114`, `1139` | index `77`: `0020a74400007042` | `478` | `393` | `1` | `1` | exact representative gate skip |
| `150mm` | `240` | index `240`: `00002a440000ee43` | `2364` | `0` | `0` | `0` | full-render no source-copy hit for this watched address |

For both positive representatives:

- the copied finite pair address equals the later sentinelized source-watch address,
- `expected_source_pair == source_watch_addr`,
- the source index equals the copied pair index,
- the parent gate index equals that same index,
- the copied destination reads `000080bf000080bf` when armed,
- the later gate computes the same destination address,
- the gate pair still reads `000080bf000080bf`,
- runtime flags are `CF=0`, `ZF=0`, `PF=0`,
- and one instruction step from `0x20d363` reaches `0x20d565`.

The positive indices are:

- `28mm`: `source_index == gate_index == 5394`
- `70mm`: `source_index == gate_index == 77`

The selected `35mm` no-match is capped and is not an exhaustive negative. The
selected `150mm` pair at index `240` is watched through the completed render
without a watchpoint cap, but that proves only that this one address was not
source-read by the second `0x20ca00` local copy in that run.

## Admission Check

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_gate_selected_custody.py
28mm: OK index=5394 same_address=3 source20d309=1258 watch_hits=1292 gate_hits=1
35mm: OK targeted=3 source20d309=2185 watch_hits=16384 source_cap=1 gate_hits=0
70mm: OK index=77 same_address=4 source20d309=393 watch_hits=478 gate_hits=1
150mm: OK targeted=1 source20d309=0 watch_hits=2364 source_cap=0 gate_hits=0
```

The verifier checks clean process completion, Radiance HDR custody,
same-address copied-pair identity, finite copied bytes, completed sentinel
bytes, source/gate index equality for the positive representatives, computed
destination identity, sentinel bytes at the destination gate, runtime branch
flags, and the exact `0x20d363 -> 0x20d565` branch step.

## Proven Facts

1. The selected `28mm`, `35mm`, `70mm`, and `150mm` reports exit cleanly,
   avoid the drive step cap, contain no probe errors, and have matching
   Radiance HDR outputs.
2. For selected `28mm` copied pair index `5394`, the same runtime address is
   copied into the node-vector destination, sentinelized, source-read by the
   second `0x20ca00` local copy, copied to a computed destination slot, selected
   by gate index `5394`, and skipped by `0x20d363 -> 0x20d565` while still full
   sentinel.
3. For selected `70mm` copied pair index `77`, the same runtime custody chain
   reaches gate index `77` and the same sentinel skip branch.
4. The selected `35mm` representatives have no source/gate index match before
   the `16384` source-watch cap.
5. The selected `150mm` copied/sentinelized pair at index `240` has no
   `0x20d309` source-copy observation during the completed uncapped watch run.

## Safe Conclusion

The prior same-address node-destination source-copy proof can now be extended
through destination-slot identity and the local positive-coordinate gate for
one selected `28mm` representative and one selected `70mm` representative:

`copied finite node-destination pair -> same-address sentinel rewrite -> same-address 0x20ca00 source read -> copied destination slot -> same-slot sentinel gate read -> 0x20d565 skip`

This removes the local `0x20ca00` gate outcome as an unknown for those two
representatives only. It does not prove that all sentinelized pairs reach this
gate, that all such pairs are terminal, that `35mm` or `150mm` have no matching
representative, or that the skip determines final image/source contribution.
