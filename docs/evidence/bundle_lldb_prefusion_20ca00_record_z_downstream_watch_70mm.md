# Evidence: Prefusion `0x20ca00` Record `+0x10` Downstream Watch, Unit-1 70mm

## Scope

This note follows one selected Unit-1 `70mm` `0x20ca00` solved-record
`record+0x10` field after the second post-Solve triple-write site.

It answers a narrow question left by the solve-output discriminator proof:
after the Unit-1 `70mm` run proves the second transform changes the final
triple, does that final `record+0x10` value leave the callback at the same
runtime address?

The answer for this watched field is yes, under a capped watchpoint window. The
same address is touched by the immediate parent scan, later propagation/helper
surfaces, and a downstream positive-record gate at `0x2189c4`, while the watched
4-byte value remains unchanged.

This is one watched field in one Unit-1 `70mm` run. The watchpoint disables at
64 hits. It is not all-record coverage, not whole-render terminality, not
image/source-contribution proof, not reducer closure, and not final
acceptance/rejection.

## Artifacts

- Runtime callback:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_record_z_watch_probe.py`
- LLDB script:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/node_dest_20ca00_record_z_watch_unit1_70mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_record_z_watch_unit1_70mm.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_z_watch.py`
- Raw report/log/HDR:
  `runs/prefusion_20ca00_record_z_watch/`

Input:

```text
/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri
```

The run used profile `3`, export format `3` HDR, and `--no-auto-lris`; it wrote
a complete `10432 x 7824` Radiance HDR output and the JSON report records
process exit status `0`.

## Watchpoint Method

The probe arms at `0x20d737`, after the second post-Solve triple-write block in
the `0x20ca00` callback. It computes the selected triple address using the same
callback locals as the solve-output verifier:

```text
triple_addr = record_begin + 4 * record_offset + 8
record_offset = 5 * gate_index
watch_addr = triple_addr + 8
```

For the admitted run:

```text
gate_index = 3906
record_offset = 19530
watch_addr = 0x7fb2e81b3138
record+0x10 at arm = 3499.366699219
raw bits = deb55a45
```

## Runtime Result

The watchpoint captured 64 read/write stops before disabling at its cap. All
64 stops preserved the watched raw bits `deb55a45`.

| Top VA | Count | Local classification |
|---:|---:|---|
| `0x20c3f9` | `1` | immediate `0x20bd60` parent scan / vector comparison window under State return `0x22ae8c` |
| `0x23a224` | `9` | `0x239e00` / `0x239ac0` propagation positive-record gate window |
| `0x2295b7` | `5` | State-family positive `record+0x10` test window |
| `0x2189c4` | `37` | downstream positive-record gate / transform-score window |
| `0x23d1d3` | `8` | `0x23c5f0` helper positive-record count/test window |
| `0x23d5ed` | `2` | `0x23c5f0` helper materialization branch on positive `record+0x10` |
| `0x23d887` | `2` | `0x23c5f0` helper same-value record-field materialization write |

The first watchpoint stop is:

```text
0x20c3f9 <- 0x22ae8c <- 0x22f3ff <- 0x227063 <- 0x3fc99d
```

The `0x2189c4` downstream stops have stack shape:

```text
0x2189c4 <- 0x21937a <- 0x5f5e <- 0x4f83 <- 0x280e
```

Static disassembly around `0x2189c4` shows the stopped compare follows a
z-lane load from the watched record triple:

```text
0x2189c0  movss  (%rax), %xmm6
0x2189c4  ucomiss %xmm6, %xmm11
0x2189c8  jae    0x218aeb
0x2189ce  movss  -0x8(%rax), %xmm1
0x2189d3  movss  -0x4(%rax), %xmm3
```

This is a positive-record gate/transform-score window. It is not, by itself,
image contribution or final acceptance/rejection proof.

## Verification

Commands:

```bash
bash tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_20ca00_record_z_watch_unit1_70mm.sh
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_record_z_watch_probe.py tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_z_watch.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_record_z_watch.py
```

Verifier output:

```text
report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_20ca00_record_z_watch/record_z_watch_unit1_70mm.json
armed=gate_index=3906 record_offset=19530 z_addr=0x7fb2e81b3138 z=3499.366699219
watchpoint_hits=64 value_changes=0
top_va_counts=0x20c3f9:1,0x2189c4:37,0x2295b7:5,0x23a224:9,0x23d1d3:8,0x23d5ed:2,0x23d887:2
first_touch=0x20c3f9 parent scan under State return 0x22ae8c
downstream_touch=0x2189c4 positive-record gate observed while z remained unchanged
scope=capped 64-hit Unit-1 70mm same-address record+0x10 watch; no terminality or image effect proven
```

## Safe Conclusion

The watched Unit-1 `70mm` `record+0x10` value written by the `0x20ca00`
post-Solve path is not confined to the callback. At the same runtime address
and with unchanged bits, it is sampled by the immediate parent scan, then by
later propagation/helper surfaces, and then by a downstream positive-record
gate / transform-score window at `0x2189c4`.

The admitted scope is capped and representative. It narrows downstream custody
for one solved record field, but it does not prove all-record behavior,
terminality, final image/source contribution, reducer closure, or final
acceptance/rejection.
