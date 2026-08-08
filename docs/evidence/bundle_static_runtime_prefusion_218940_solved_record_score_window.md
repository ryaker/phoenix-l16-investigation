# Evidence: Prefusion `0x218940` Solved-Record Score Window

## Scope

This note extends the Unit-1 `70mm` `record+0x10` downstream-watch proof for
one selected `0x20ca00` solved-record field.

The earlier packet already proved that the watched final `record+0x10` value
leaves the callback unchanged and is touched 37 times at `0x2189c4`. This note
adds a SHA-pinned static decode of the surrounding `0x218940` helper to answer
one narrower question: what does a finite positive watched value at `0x2189c4`
mean locally?

Answer: in the installed binary, `0x2189c4` is the z-lane compare immediately
before a skip branch. The observed finite positive z is on the fallthrough side
of that branch, so the watched solved-record triple reaches this helper's local
record/transform score body.

This is static-plus-runtime local proof only. It is not a direct branch-step
trace, not all-record behavior, not terminality, not image/source contribution,
not reducer closure, and not final acceptance/rejection.

## Artifacts

- Runtime packet reused:
  `runs/prefusion_20ca00_record_z_watch/record_z_watch_unit1_70mm.json`
- Runtime evidence bundle reused:
  `docs/evidence/bundle_lldb_prefusion_20ca00_record_z_downstream_watch_70mm.md`
- Extended runtime callback:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_record_z_watch_probe.py`
- New verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_218940_solved_record_score_window.py`

No `/tmp` or `/private/tmp` artifact is cited by this proof.

## Runtime Input

The reused packet is the capped Unit-1 `70mm` watch:

```text
/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri
```

The watch arms after `0x20ca00`'s second post-Solve triple write at
`0x20d737`:

```text
gate_index = 3906
record_offset = 19530
z_addr = 0x7fb2e81b3138
record+0x10 = 3499.366699219
raw bits = deb55a45
```

The packet captures 64 read/write stops before the watchpoint cap, with zero
value changes. Of those, 37 stops are at `0x2189c4`. For every `0x2189c4`
sample, register `rax` equals the watched `z_addr`, register `rdx` equals the
selected `gate_index`, and the watched bits remain `deb55a45`.

## Static Window

The verifier SHA-pins installed `libcp.dylib` bytes
`0x218940..0x218b2f`:

```text
sha256 = 3b2eb5366eee74ae3ba8615437b6725658e465710d865fae0eecc6388a21eded
```

The relevant decoded structure is:

```text
0x2189a0  load pair.x
0x2189a5  compare 0.0 with pair.x
0x2189a9  jae 0x218aeb        # skip when pair.x <= 0

0x2189af  load pair.y
0x2189b6  compare pair.y with 0.0
0x2189ba  jbe 0x218aeb        # skip when pair.y <= 0

0x2189c0  load record.z from rax
0x2189c4  compare 0.0 with record.z
0x2189c8  jae 0x218aeb        # skip when record.z <= 0 or unordered

0x2189ce  load record.x
0x2189d3  load record.y
0x2189d8..0x218a9c  transform record x/y/z through rsi+0x24..0x50 fields
0x218adc  accumulate local score sum in xmm10
0x218ae5  update local over-threshold count r9d
0x218ae8  increment local positive-record count r8d
```

Therefore a finite positive runtime z at `0x2189c4` does not take the
`0x2189c8 -> 0x218aeb` skip. It falls through to `0x2189ce`, where this helper
loads the same record's x/y lanes and enters the local transform/score body.

## Verification

Commands:

```bash
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_20ca00_record_z_watch_probe.py tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_218940_solved_record_score_window.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_218940_solved_record_score_window.py
```

Verifier output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
window=0x218940..0x218b2f sha256=3b2eb5366eee74ae3ba8615437b6725658e465710d865fae0eecc6388a21eded
report=/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_20ca00_record_z_watch/record_z_watch_unit1_70mm.json
record_z_gate=z=3499.366699219 z_compare_hits=37 static_positive_fallthrough=0x2189c8_not_taken_to_0x2189ce
static_body=record_xyz plus rsi+0x24..0x50 transform fields feed score_sum_xmm10,over_threshold_count_r9d,positive_record_count_r8d
scope=one capped Unit-1 70mm solved-record runtime packet plus static fallthrough proof; no terminality or image effect proven
```

## Safe Conclusion

For this watched Unit-1 `70mm` solved-record field, the downstream
`0x2189c4` touches are not just opaque reads. The same unchanged finite positive
`record+0x10` value reaches a byte-verified z gate in the `0x218940` helper,
and the installed branch structure places that positive value on the local
record/transform score-body path.

This narrows representative downstream custody from "same-address touch at a
positive-record gate" to "same-address positive solved-record admission into a
local score body." It still does not prove all-record behavior, stable
cross-body/focal incidence, public depth units or names, image/source
contribution, reducer closure, or final acceptance/rejection.
