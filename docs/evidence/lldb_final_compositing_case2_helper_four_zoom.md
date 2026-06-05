# LLDB Proof: Final-Compositing Case-2 Helper Path Across Four Zooms

## Scope

This proof follows the final-compositing queue/drain liveness and switch-census
proofs by drilling into the live post-gather case `2` target inside `0x3bca90`.

It proves only tested-path branch/callsite reachability and local operand shape
for the case-`2` helper route:

- case `2` target `0x3bd308`;
- call edge `0x3bd30e -> 0x3bf2f0`;
- helper-internal callsites / branch sites inside `0x3bf2f0`;
- return to the post-helper append callsite at `0x3bd31d`.

It does not prove public record semantics, helper body semantics, final file /
display sink, byte-level copy-vs-blend behavior, anti-ghosting policy, final
output semantics, or final merge acceptance/rejection.

## Artifacts

Reusable probe harness:

- `tools/lldb_probes/codex_final_compositing_case2_helper/case2_helper_probe.py`
- `tools/lldb_probes/codex_final_compositing_case2_helper/case2_helper_28mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case2_helper/case2_helper_35mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case2_helper/case2_helper_70mm.lldb`
- `tools/lldb_probes/codex_final_compositing_case2_helper/case2_helper_150mm.lldb`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_compositing_case2_helper/case2_helper_28mm.json`
- `runs/codex_final_compositing_case2_helper/case2_helper_35mm.json`
- `runs/codex_final_compositing_case2_helper/case2_helper_70mm.json`
- `runs/codex_final_compositing_case2_helper/case2_helper_150mm.json`
- matching `.log` and `.hdr` files in the same directory

The admitted reports were produced by isolated LLDB invocations of the matching
per-zoom scripts. A whole-quartet wrapper was intentionally not admitted because
direct per-focal LLDB commands were reliable while the wrapper launch context
reproducibly failed to open the external LRI volume on this machine.

## Inputs

All runs used the same installed x86_64 binary/framework set and the canonical
four LRIs:

| Zoom | LRI |
|---|---|
| `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Each launch passed `--profile 3 --export-fmt 3 --no-auto-lris` and completed a
`10432x7824` HDR write under LLDB.

## Runtime Results

All four admitted runs exited normally with no probe errors and without hitting
the step cap. Each run recorded eight breakpoint stops.

| Site | Name | 28mm | 35mm | 70mm | 150mm |
|---|---|---:|---:|---:|---:|
| `0x3bd308` | case-2 target | 1 | 1 | 1 | 1 |
| `0x3bd31d` | post-helper append callsite | 1 | 1 | 1 | 1 |
| `0x3bf2f0` | helper entry | 1 | 1 | 1 | 1 |
| `0x3bf331` | optional `0x3b5b50` callsite | 1 | 1 | 1 | 1 |
| `0x3bf344` | `0x3b6070` callsite | 1 | 1 | 1 | 1 |
| `0x3bf354` | `0x3b07c0` callsite | 1 | 1 | 1 | 1 |
| `0x3bf382` | `0x3ba0a0` callsite | 1 | 1 | 1 | 1 |
| `0x3bf39a` | `0x3b9820` callsite | 0 | 0 | 0 | 0 |
| `0x3bf3be` | ImagePyramid constructor branch | 0 | 0 | 0 | 0 |
| `0x3bf419` | owner `+0x5a0` callback branch | 0 | 0 | 0 | 0 |
| `0x3bf481` | owner `+0x640` callback branch | 0 | 0 | 0 | 0 |
| `0x3bf49a` | completion-flag write branch | 0 | 0 | 0 | 0 |
| `0x3bf4b8` | helper return | 1 | 1 | 1 | 1 |
| `0x3bf4c7` | invalid-request error branch | 0 | 0 | 0 | 0 |
| `0x3bf50f` | bad-function branch | 0 | 0 | 0 | 0 |
| `0x3bf55a` | bad-function branch | 0 | 0 | 0 | 0 |

## Case-2 Record Fields

At helper entry, the case-`2` record had the following captured fields:

| Zoom | `i32+0x00` | `i32+0x10` | `i32+0x14` | `i32+0x20` | `i32+0x24` | `i32+0x28` | `u64+0x20` | `u64+0x28` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | 2 | 1 | 0 | 3912 | 2 | 0 | 8589938504 | 0 |
| `35mm` | 2 | 1 | 0 | 3120 | 2 | 0 | 8589937712 | 0 |
| `70mm` | 2 | 1 | 0 | 3312 | 2 | 0 | 8589937904 | 0 |
| `150mm` | 2 | 1 | 0 | 1560 | 2 | 0 | 8589936152 | 0 |

The `u64+0x20` values are the captured 64-bit view over the adjacent `i32+0x20`
and `i32+0x24` fields. This table records the observed layout only; it does not
assign public semantic names to those fields.

## Owner / Branch-Gate Observations

At helper entry, the captured owner bytes `+0x4a2`, `+0x4a4`, `+0x721`, and
`+0x722` were all `0` in all four admitted runs. Owner pointers `+0x5a0` and
`+0x640` were also `0` in all four admitted runs.

At the live `0x3bf382 -> 0x3ba0a0` callsite, owner pointers `+0x508`,
`+0x538`, `+0x688`, and `+0x8a0` were nonzero in all four admitted runs, while
owner pointers `+0x5a0` and `+0x640` remained `0`.

The record field `u64+0x28` was `0` in all four admitted runs, matching the
zero-hit completion-flag write branch at `0x3bf49a` under this tested path.

## Proven Facts

- The case-`2` target `0x3bd308` is runtime-live once per canonical
  bridge-HDR render at `28mm`, `35mm`, `70mm`, and `150mm`.
- The live case-`2` path calls helper `0x3bf2f0` once per admitted run and
  returns to the post-helper callsite at `0x3bd31d`.
- Inside helper `0x3bf2f0`, the tested path reaches callsites `0x3bf331`,
  `0x3bf344`, `0x3bf354`, and `0x3bf382` once per admitted run.
- Under these admitted runs, the helper reaches the `0x3ba0a0` callsite
  `0x3bf382` and records zero hits at the alternate `0x3b9820` callsite
  `0x3bf39a`.
- Under these admitted runs, the ImagePyramid constructor branch, owner
  `+0x5a0` callback branch, owner `+0x640` callback branch, completion-flag
  write branch, invalid-request branch, and two bad-function branches all record
  zero hits.

## Non-Claims

- Zero-hit findings are scoped to the tested canonical CLI bridge-HDR quartet;
  they are not universal "never fires" claims for every Lumen path.
- This proof does not identify public names or semantics for the case-`2`
  record fields.
- This proof does not classify helper bodies `0x3b5b50`, `0x3b6070`,
  `0x3b07c0`, or `0x3ba0a0`.
- This proof does not cover live switch cases `1`, `3`, `11`, or `16`.
- This proof does not identify final file/display sink, copy-vs-blend behavior,
  final output semantics, anti-ghosting policy, or final merge
  acceptance/rejection.
