# Bundle + Reused LLDB Proof: Prefusion Node-Destination Same-Address `0x20ca00` Source-Copy Custody, Four Zooms

## Scope

This note reuses the admitted runtime packets from
`bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md` and adds a
repo-local verifier for a narrower downstream subset.

It proves that one finite coordinate pair copied into the
`0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal
tier is later:

1. observed at the same runtime address before the `0x21b923` x-lane sentinel store,
2. observed at that same address as full `(-1.0, -1.0)` at `0x21b930`,
3. and source-read at that same address by `0xe0ae0` under caller return
   `0x20d309`, the second local vector-copy site inside `0x20ca00`.

This links copied node-destination identity into the `0x20ca00` second local
copy as a source element. It does not prove the copied destination address,
`source_index == gate_index`, the later `0x20d363` positive-coordinate gate,
whole-vector terminality, image effect, source contribution, reducer closure,
or final acceptance/rejection.

## Repo-Local Artifacts

- Source runtime packets:
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.json`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.json`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.json`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.json`
- Source HDR outputs:
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_28mm.hdr`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_35mm.hdr`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_70mm.hdr`
  `runs/prefusion_node_dest_sentinel_custody/node_dest_sentinel_custody_150mm.hdr`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_source_copy.py`

No new LLDB run is introduced by this note. The verifier rechecks a subset of
the previously admitted same-address custody JSON.

## Static / Runtime Anchors

The upstream same-address path is admitted by
`bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md`:

`0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector copy destination finite pair -> same runtime address at `0x21b923` / `0x21b92a` -> full `(-1.0, -1.0)` at `0x21b930`.

The downstream `0x20ca00` second local copy site is admitted and statically
anchored by `bundle_lldb_prefusion_20ca00_copied_sentinel_gate_four_zoom.md`:

```text
0x20d2f9: leaq 0x28(%rbx), %rsi
0x20d2fd: leaq -0xe0(%rbp), %rdi
0x20d304: callq 0xe0ae0
0x20d309: return site after the second local vector copy
```

The new verifier selects only watchpoint samples whose stopped PC is inside the
`0xe0ae0` unrolled source-read family, whose caller frame is `0x20d309`, and
whose watched address equals the already-admitted copied node-destination match.

## Runtime Results

| Zoom | LRI | Same matched address | Copied finite bytes | `0x20d309` source-read stops | `0xe0ae0` stopped PCs | Pair bytes at source read |
|---|---|---:|---|---:|---|---|
| `28mm` | `L16_02130` | `140155791054176` | `000055440080bd43` | `52` | `0xe0bb2`, `0xe0bb7` | `000080bf000080bf` |
| `35mm` | `L16_03041` | `140300397906096` | `0000904200008443` | `53` | `0xe0bbd`, `0xe0bc3` | `000080bf000080bf` |
| `70mm` | `L16_03434` | `140217007577136` | `00005e440000c143` | `41` | `0xe0bd5`, `0xe0bdb` | `000080bf000080bf` |
| `150mm` | `L16_02285` | `140444801498272` | `0020864400c02b44` | `42` | `0xe0bbd`, `0xe0bc3` | `000080bf000080bf` |

Decoded copied-pair values for the admitted matches:

| Zoom | Copied pair value | Copy site |
|---|---|---|
| `28mm` | `(852.0, 379.0)` | `copy_a_ret_22a61f` |
| `35mm` | `(72.0, 264.0)` | `copy_a_ret_22a61f` |
| `70mm` | `(888.0, 386.0)` | `copy_a_ret_22a61f` |
| `150mm` | `(1073.0, 687.0)` | `copy_a_ret_22a61f` |

## Admission Checks

The repo-local verifier rechecks clean completion of the source packets, the
same-address copied node-destination match, full-sentinel bytes after
sentinelization, and same-address `0xe0ae0 <- 0x20d309` source reads:

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_20ca00_source_copy.py
28mm: OK same_addr=140155791054176 copy20d309_source_reads=52 e0ae0_pcs=0xe0bb2,0xe0bb7 copied_hex=000055440080bd43
35mm: OK same_addr=140300397906096 copy20d309_source_reads=53 e0ae0_pcs=0xe0bbd,0xe0bc3 copied_hex=0000904200008443
70mm: OK same_addr=140217007577136 copy20d309_source_reads=41 e0ae0_pcs=0xe0bd5,0xe0bdb copied_hex=00005e440000c143
150mm: OK same_addr=140444801498272 copy20d309_source_reads=42 e0ae0_pcs=0xe0bbd,0xe0bc3 copied_hex=0020864400c02b44
```

The source same-address verifier still passes:

```text
$ python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_node_dest_sentinel_custody.py
28mm: OK copy_vectors=4 copied_addrs=1770 after_store_full=1 matches=1 watch_hits=64 downstream_vas=3 unique_after=1
35mm: OK copy_vectors=4 copied_addrs=5087 after_store_full=1 matches=1 watch_hits=64 downstream_vas=3 unique_after=1
70mm: OK copy_vectors=4 copied_addrs=10197 after_store_full=1 matches=1 watch_hits=64 downstream_vas=6 unique_after=1
150mm: OK copy_vectors=4 copied_addrs=1398 after_store_full=1 matches=1 watch_hits=64 downstream_vas=6 unique_after=1
```

## Proven Facts

1. The admitted source runtime packets completed cleanly and satisfy the existing node-destination same-address custody verifier.
2. In each canonical focal tier, one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination is later the same address sentinelized to full `(-1.0, -1.0)`.
3. In each canonical focal tier, that exact same address is then read by `0xe0ae0` with caller frame `0x20d309`, the second local vector copy inside `0x20ca00`.
4. Every admitted `0x20d309` source-read sample for that address still reads `000080bf000080bf`.

## Safe Conclusion

The same-address chain now extends from copied node-destination pair through
sentinelization into the `0x20ca00` second local vector copy as a source
element:

`copied finite node-destination pair -> same-address sentinel rewrite -> same-address 0xe0ae0 source read under 0x20d309`

This narrows one more State-family downstream copy surface for the representative
pairs. It remains source-copy custody only; the destination slot, local gate
selection, image/source-contribution consequence, all-pairs coverage, final
acceptance/rejection, and reducer closure remain open.
