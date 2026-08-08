# Evidence: Prefusion `0x216f60` Accepted-Bank Downstream Custody Matrix

## Scope

This note follows
`bundle_static_runtime_prefusion_216f60_parent_score_selection_gate_matrix.md`.
That proof closes the local score/side-output gate and shows accepted winners
reach selector-1 `0xf33d0`. This note asks what happens to the resulting
destination bank.

SHA-pinned static code and hardware read/write watchpoints now prove:

1. every captured accepted `0x216f60 -> 0xf33d0` call exactly copies its three
   input records into destination selector-1 bank `destination+0x12c..+0x17f`;
2. the first accepted bank in each evidence run is later read unchanged by
   `0x264270`;
3. those pre-overwrite reads include both the direct `0xf34e0`-returned bank
   copy path and the later `0xf3350` accessor-side read;
4. a later `0x23c5f0 -> 0xf33d0` selector-1 call can overwrite the same bank,
   after which `0x264270` continues reading the replacement value.

This extends accepted-winner custody into the State/helper calibration-record
assembly path. It does not prove image-buffer contribution, public semantics
for the accepted record, whole reducer closure, or final merge
acceptance/rejection.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_accepted_bank_consumer_probe.py`
- LLDB command files:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/accepted_bank_consumer_28mm.lldb`,
  `accepted_bank_consumer_35mm.lldb`, `accepted_bank_consumer_70mm.lldb`,
  `accepted_bank_consumer_150mm.lldb`, and
  `accepted_bank_consumer_unit2_35mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_accepted_bank_consumer_matrix.sh`
- Verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_accepted_bank_consumer.py`
- Runtime reports and completed HDR outputs:
  `runs/prefusion_216f60_accepted_bank_consumer/`

No `/tmp` or `/private/tmp` artifact is a dependency.

## Static Copy Boundary

The verifier pins:

```text
libcp SHA-256:
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9

0xf33d0..0xf349d SHA-256:
ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8

0x264270..0x264370 SHA-256:
4a70e92075516bbfa5f0e05b10449fe15a39a0d661baf885bbf9b317dc26cc0e
```

Selector `1` at `0xf3440` writes:

```text
source rsi[0x00..0x23] -> destination[0x12c..0x14f]
source rdx[0x00..0x23] -> destination[0x150..0x173]
source rcx[0x00..0x0b] -> destination[0x174..0x17f]
```

The runtime verifier captures every accepted call at `0x217bbe`, snapshots all
three sources, snapshots the complete 84-byte destination bank after return at
`0x217bc3`, and requires exact byte equality.

## Static Consumer

`0x264270` receives destination local `rbx`, source object `r15`, and selector
`r14d`. Its first three `0xf34e0` calls obtain the selected bank and copy:

```text
bank +0x00..+0x23 -> local +0x00..+0x23
bank +0x48..+0x53 -> local +0x24..+0x2f
bank +0x24..+0x47 -> local +0x30..+0x53
```

It then uses `0xf3360` / `0xf3350` calibration accessors for the later
distortion/scale portion of the assembled record.

The hardware watch covers the first eight bytes of the first accepted
selector-1 bank. A reported stop PC of `0x26429c` follows the direct
`movups [rax]` bank read at `0x264299`. A reported stop PC of `0x26434d`
follows the accessor-side read at `0x264348`. Both sites preserve the watched
bits before the first later overwrite.

## Runtime Matrix

| Run | Accepted `0xf33d0` calls | Total watch stops | Pre-overwrite stops | Direct bank reads | Accessor-side reads |
|---|---:|---:|---:|---:|---:|
| Unit-1 `28mm` | 2 | 23 | 8 | 4 | 4 |
| Unit-1 `35mm` | 2 | 22 | 2 | 1 | 1 |
| Unit-1 `70mm` | 4 | 46 | 16 | 8 | 8 |
| Unit-1 `150mm` | 3 | 46 | 16 | 8 | 8 |
| Unit-2 `35mm` | 2 | 23 | 8 | 4 | 4 |

Every pre-overwrite sample preserves the first accepted bank's original bits.
Every run includes `0x239e00` propagation ancestry among those reads. The
broader Unit-1 tele samples also include `0x20ada0`, `0x20b5e0`, `0x20bd60`,
`0x22ae60`, `0x22af80`, and `0x23c5f0` caller ancestry.

The first later selector-1 overwrite is reported at PC `0xf345e`, immediately
after the `0xf3457` store to destination `+0x12c`; its stack is under
`0x23c5f0 -> 0xf33d0`. Later unchanged reads of the replacement bits again
reach `0x264270`. Final non-libcp value changes are allocator cleanup after HDR
output.

The watched values, accepted-call totals, and stop counts are evidence-run
observations, not stable constants.

## Scoped `0x3f7ec0` Exclusion

The initial candidate consumer was the visible `0x3f7ec0` record/buffer
materialization body. Breakpoints at its two `0xf34e0` callsites and six
immediate materialization-helper callsites record zero hits in all five
complete no-auto-LRIS evidence runs. This excludes those selected sites only
under the tested scope; it is not dead-code proof.

## Verification

```bash
python3 -m py_compile \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_216f60_accepted_bank_consumer_probe.py \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_accepted_bank_consumer.py
bash -n \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_216f60_accepted_bank_consumer_matrix.sh
python3 \
  tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_216f60_accepted_bank_consumer.py
```

Verifier output:

```text
static_accepted_bank_consumer=OK libcp_sha256=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 f33d0_sha256=ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8 copy_sha256=4a70e92075516bbfa5f0e05b10449fe15a39a0d661baf885bbf9b317dc26cc0e
28mm: accepted_calls=2 watch_hits=23 pre_overwrite=8 direct_reads=4 accessor_reads=4 value_changes=2 stereo_sites=0
35mm: accepted_calls=2 watch_hits=22 pre_overwrite=2 direct_reads=1 accessor_reads=1 value_changes=1 stereo_sites=0
70mm: accepted_calls=4 watch_hits=46 pre_overwrite=16 direct_reads=8 accessor_reads=8 value_changes=2 stereo_sites=0
150mm: accepted_calls=3 watch_hits=46 pre_overwrite=16 direct_reads=8 accessor_reads=8 value_changes=2 stereo_sites=0
Unit-2 35mm: accepted_calls=2 watch_hits=23 pre_overwrite=8 direct_reads=4 accessor_reads=4 value_changes=2 stereo_sites=0
```

## Safe Conclusion

The accepted `0x216f60` winner is not merely copied into an otherwise inert
temporary. Selector-1 `0xf33d0` installs its transformed records into a
destination object's `+0x12c..+0x17f` bank, and the first accepted bank in
every admitted run is read unchanged by `0x264270` before later State-helper
replacement. This mechanism is observed across all four canonical focal tiers
and one exact-focal second-body discriminator.

The proof closes accepted-bank-to-State/helper-record-assembly custody only.
It does not establish public record names, final image/source contribution,
distributed reducer closure, or final merge acceptance/rejection.
