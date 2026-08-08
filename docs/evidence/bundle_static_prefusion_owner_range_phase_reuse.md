# Bundle Static Proof: Prefusion Owner Range `+0x78/+0x7c` Phase Reuse

## Scope

This note records a deterministic installed-binary guardrail found while
following the `0x20ca00` / Triangulator solved-depth path.

It proves only writer order and local field reuse:

- State body `0x22ae60` calls `0x20ada0` with `*(state_body_this+0x08)+0x10`,
  then later calls `0x20bd60` with the same owner pointer.
- `0x20ada0` writes owner `+0x78/+0x7c` after computing reciprocal extrema over
  pre-solve range-like pairs.
- `0x20bd60` later writes the same owner `+0x78/+0x7c` after reducing positive
  solved `record+0x10` values from the owner record vector.

This proves `+0x78/+0x7c` are phase-reused owner summary slots in this path.
It does not prove a public field name, downstream read, final contribution, or
image effect.

## Artifacts

- Static verifier:
  [verify_owner_range_phase_reuse_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_owner_range_phase_reuse_static.py)
- Full-text direct numeric-read census:
  [scan_field_displacements_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/scan_field_displacements_static.py),
  [verify_owner_range_direct_numeric_read_census_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_owner_range_direct_numeric_read_census_static.py)
- Rejected exploratory live watch harness:
  [prefusion_owner_range_watch_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_owner_range_watch_probe.py),
  [owner_range_watch_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/owner_range_watch_28mm.lldb),
  [run_owner_range_watch_28mm.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_owner_range_watch_28mm.sh)

The exploratory LLDB watch is not admitted. Its durable log stopped at
`process launch` with `lost connection` and produced no JSON/HDR report.
The runner now removes stale JSON/HDR outputs and fails quickly on that exact
log signature rather than leaving LLDB apparently active.

## Static Boundary

The verifier pins three byte windows in the installed `libcp.dylib`:

| Window | Bytes | SHA-256 |
|---|---:|---|
| `0x22ae60..0x22aea8` | `72` | `0a8dacb37c3f85d410e739acd61a022779574fb58236d75d64c0d30d49191e99` |
| `0x20ada0..0x20af6e` | `462` | `055143c7598f1fa61b9d58491161bf30974af36a040af77c41372101c240fe87` |
| `0x20c330..0x20c4ba` | `394` | `9bdcc9c3c8bbbc1e780087428cb6d7be8cf7c402b7b043ba9ad349681665d408` |

The State body order is:

```text
0x22ae66  rbx = *(rdi+0x08)
0x22ae6a  rdi = *(rbx+0x10)
0x22ae6e  call 0x20ada0
...
0x22ae83  rdi = *(rbx+0x10)
0x22ae87  call 0x20bd60
```

The pre-solve summary writer in `0x20ada0` stores reciprocal extrema:

```text
0x20af4b  divss xmm3, xmm1
0x20af4f  divss xmm2, xmm0
0x20af53  movss dword ptr [r15 + 0x78], xmm3
0x20af59  movss dword ptr [r15 + 0x7c], xmm2
```

The later parent scan in `0x20bd60` stores positive solved-record extrema:

```text
0x20c490  movss xmm0, dword ptr [rbx + 0x10]
0x20c49d  minss xmm3, xmm0
0x20c4a1  maxss xmm2, xmm0
0x20c4ae  movss dword ptr [r15 + 0x78], xmm3
0x20c4b4  movss dword ptr [r15 + 0x7c], xmm2
```

This second writer is the same parent-scan window already used by
[bundle_static_prefusion_20ca00_record_range_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_prefusion_20ca00_record_range_custody.md)
to prove immediate reduction of positive `record+0x10` values.

## Direct Numeric-Read Census

The SHA-pinned verifier disassembles installed `__TEXT.__text` and enumerates
every direct floating/vector numeric memory read whose encoded displacement is
exactly `+0x78` or `+0x7c`. There are 15:

| Sites | Bounded record family |
|---|---|
| `0x9db99`, `0x9df38` | 4x4-double matrix input |
| `0xea8a1` | `0xa0`-byte record move |
| `0x101c00` | transform record passed as caller stack local at both direct callsites |
| `0x1c7596` | three-double vector magnitude |
| `0x21d142` | `0x40`-stride double-array reduction |
| `0x24006f`, `0x240995`, `0x2409d0` | already-bounded State/source-record composition families |
| `0x24e79d`, `0x24e7fe` | `0x88`-byte record-copy helpers |
| `0x3a47f7`, `0x3aba07`, `0x3abad9` | four-int rectangle reductions |
| `0x3c74ef` | mutex-protected `tone_mapping.sharpening` config path |

There is no direct same-displacement floating/vector numeric read in
`0x20ada0..0x20c4ba` or in State caller `0x22ae60`. None of the 15 candidates
is the proven Triangulator owner summary object. This excludes a direct
same-base numeric consumer as the next custody edge; it does not exclude an
alias, adjusted base pointer, integer bit-copy, or indirect accessor.

## Non-Claims

- This does not prove any later consumer reads owner `+0x78/+0x7c`.
- The direct-read census does not prove that no alias, adjusted pointer,
  integer bit-copy, or indirect helper consumes the pair.
- This does not assign public units or public LRI/protobuf names.
- This does not prove that every displacement `+0x78/+0x7c` access in the
  binary refers to this owner object.
- This does not change the admitted public-meaning gap for the index-5
  reciprocal ray-depth hypothesis grid.

## Verification

Command:

```bash
python3 -m py_compile tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_owner_range_phase_reuse_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_owner_range_phase_reuse_static.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_owner_range_direct_numeric_read_census_static.py
```

Output:

```text
binary=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
state_body_22ae60=0x22ae60..0x22aea8 sha256=0a8dacb37c3f85d410e739acd61a022779574fb58236d75d64c0d30d49191e99
pre_solve_summary_20ada0=0x20ada0..0x20af6e sha256=055143c7598f1fa61b9d58491161bf30974af36a040af77c41372101c240fe87
post_solve_summary_20c330=0x20c330..0x20c4ba sha256=9bdcc9c3c8bbbc1e780087428cb6d7be8cf7c402b7b043ba9ad349681665d408
0x22ae60 order=owner(*(state+0x08)+0x10) -> 0x20ada0, then same owner -> 0x20bd60
0x20ada0 writes owner+0x78/+0x7c after reciprocal extrema over pre-solve ranges
0x20bd60 later writes owner+0x78/+0x7c after positive solved record+0x10 extrema
scope=static writer/order proof only; no downstream read or public-field name proven
```

The direct-read verifier additionally reports:

```text
direct_numeric_reads=15
owner_writer_family_direct_numeric_reads=0
state_22ae60_direct_numeric_reads=0
scope=no direct same-displacement floating/vector numeric consumer identified; aliases, adjusted pointers, integer bit-copies, and indirect accessors remain open
```
