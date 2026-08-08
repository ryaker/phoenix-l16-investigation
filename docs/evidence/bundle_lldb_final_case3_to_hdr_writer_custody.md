# Bundle + LLDB Proof: Final Case-3 To CLI HDR Writer Custody

## Scope

This proof joins two previously separate final-output runtime surfaces in one
LLDB render:

- final-compositing case `3` callsite `0x3bcf16 -> 0x4182a0`;
- helper `0x4182a0` handoff at `0x418908 -> 0x41e180`;
- CLI HDR writer branch `0x41e599 -> 0x2326a0`;
- virtual writer callsite `0x232731`.

It proves same-render raw custody from case-`3` `record+0x60` dimensions to the
CLI HDR writer descriptor for the canonical Unit-1 four-focal quartet, plus one
exact-focal Unit-2 `28mm` body discriminator. It does not prove pixel
correctness, source contribution, copy-vs-blend behavior, anti-ghosting policy,
final acceptance/rejection, or non-CLI sinks.

## Artifacts

Reusable probe harnesses:

- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/final_case3_to_hdr_writer_custody_probe.py`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_28mm.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_35mm.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_70mm.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_150mm.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_150mm_min.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/case3_writer_unit2_28mm.lldb`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/run_four_zoom.sh`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/run_150_min.sh`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/run_unit2_28.sh`
- `tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/verify_final_case3_to_hdr_writer_custody.py`

Raw reports and logs are under ignored repo-local `runs/`:

- `runs/codex_final_case3_to_hdr_writer_custody/case3_writer_28mm.json`
- `runs/codex_final_case3_to_hdr_writer_custody/case3_writer_35mm.json`
- `runs/codex_final_case3_to_hdr_writer_custody/case3_writer_70mm.json`
- `runs/codex_final_case3_to_hdr_writer_custody/case3_writer_150mm_min.json`
- `runs/codex_final_case3_to_hdr_writer_custody/case3_writer_unit2_28mm.json`
- matching `.log` and `.hdr` files in the same directory

The full-breakpoint `150mm` attempt stopped at the known instrumentation-sensitive
pre-final `EXC_BAD_ACCESS` class before reaching the final path and is not
admitted as a negative result. The admitted `150mm` evidence is the narrower
positive-custody run `case3_writer_150mm_min.json`.

## Inputs

All runs used the installed x86_64 `lri_process` / `libcp.dylib` bundle with
`--profile 3 --export-fmt 3 --no-auto-lris`.

| Scope | Focal | LRI |
|---|---|---|
| Unit-1 canonical | `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| Unit-1 canonical | `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| Unit-1 canonical | `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| Unit-1 canonical | `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |
| Unit-2 discriminator | exact `28mm` | `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` |

## Runtime Results

The verifier command:

```bash
python3 tools/lldb_probes/codex_final_case3_to_hdr_writer_custody/verify_final_case3_to_hdr_writer_custody.py
```

returns:

```text
final case3-to-HDR-writer custody: OK
```

All admitted runs exited with status `0`, had no JSON probe errors, did not hit
the step cap, and emitted files identified by `file` as `Radiance HDR image
data`.

| Run | Full error/return scope | Positive custody sites hit once |
|---|---|---|
| Unit-1 `28mm` | yes | `0x3bcf16`, `0x4182a0`, `0x418908`, `0x41e180`, `0x41e599`, `0x2326a0`, `0x232731`, `0x232733` |
| Unit-1 `35mm` | yes | same |
| Unit-1 `70mm` | yes | same |
| Unit-1 `150mm` | no, positive-custody minimal run | same |
| Unit-2 exact `28mm` | yes | same |

For the full-scope runs, helper normal returns `0x418bfd` and `0x41f9eb` also
hit once, while `0x418d38`, `0x418e27`, `0x41e953`, `0x41e9ea`, `0x41fa93`,
`0x41fad4`, and `0x232758` recorded zero hits. Those zero-hit findings are not
claimed for the `150mm` minimal run.

## Custody Observations

At `0x3bcf16`, the case-`3` record passes:

- `rsi == record+0x10`;
- `r9 == record+0x20`;
- `rcx == record+0x50`;
- `rdx == record+0x60`;
- `r8d == record+0x68 == 3`.

The case-`3` `record+0x60` view has first three `i32` values
`10432, 7824, 3` in every admitted run.

| Run | Case-3 record | `record+0x60` | `0x41e180` stack dims | Writer descriptor | Writer data pointer |
|---|---:|---:|---:|---:|---:|
| Unit-1 `28mm` | `0x7fc030008d10` | `0x7fc030008d70` | `0x3046c72b8` | `0x3046c6950` | `0x7fbed5f00040` |
| Unit-1 `35mm` | `0x7ff584030310` | `0x7ff584030370` | `0x30474a2b8` | `0x304749950` | `0x7ff3b3f00040` |
| Unit-1 `70mm` | `0x7fa906808690` | `0x7fa9068086f0` | `0x3047cd2b8` | `0x3047cc950` | `0x7fa755f00040` |
| Unit-1 `150mm` | `0x7fdbfb8168b0` | `0x7fdbfb816910` | `0x304adf2b8` | `0x304ade950` | `0x7fda7af00040` |
| Unit-2 exact `28mm` | `0x7ff15f857b10` | `0x7ff15f857b70` | `0x3046c72b8` | `0x3046c6950` | `0x7fef5e700040` |

At `0x418908`, helper `0x4182a0` calls `0x41e180` with the same
`record+0x10` address in `rsi`, the same `record+0x20` address in `r9`, format
argument `3` in `r8d`, and stack dimensions whose first two `i32` values are
`10432, 7824`. The third stack word is not stable enough to name.

At `0x41e599`, helper `0x41e180` calls `0x2326a0` with decoded extension
`.hdr`, the same opaque third argument address from case-`3` `record+0x10`, and
a populated image descriptor:

- width `10432`;
- height `7824`;
- stride/count `10432`;
- data pointer nonzero.

At `0x232731`, the virtual writer-call descriptor has:

- width `10432`;
- height `7824`;
- row bytes `166912`;
- bytes-per-pixel field `16`;
- data pointer equal to the `0x41e599` descriptor data pointer.

## Proven Facts

- Under the admitted Unit-1 four-focal scope, case-`3` `record+0x60` dimensions
  are carried in the same render through `0x4182a0`, through the `0x41e180`
  HDR export helper, and into the `0x2326a0` / `0x232731` CLI HDR writer
  boundary.
- Under the admitted Unit-2 exact-`28mm` discriminator, the same custody shape
  is observed on a second physical body.
- For Unit-1 `28mm`, Unit-1 `35mm`, Unit-1 `70mm`, and Unit-2 exact `28mm`,
  the same runs also cover the selected normal-return and alternate/error-path
  zero-hit sites listed above.
- For Unit-1 `150mm`, the admitted run proves positive same-render custody only;
  the broader final writer normal/error scope remains covered by the earlier
  `lldb_final_output_hdr_writer_boundary_four_zoom.md` proof, not by this
  minimal run.

## Non-Claims

- This proof does not inspect or compare final HDR pixel values.
- This proof does not trace writer descriptor bytes back to particular
  `src1` / `src2` contributors or public camera names.
- This proof does not prove copy-vs-blend behavior, anti-ghosting policy,
  source contribution, final merge acceptance/rejection, or reducer closure.
- This proof is scoped to the CLI HDR export path and does not prove GUI,
  preview, display, PPM, DNG, or other writer sinks.
- Zero-hit findings are scoped to the admitted full-scope runs only. The
  `150mm` minimal run is not a zero-hit/error-path proof.

## Operational Note

These LLDB runs were executed outside the Codex sandbox because sandboxed
`debugserver` was denied the task port for `lri_process` on this machine. That
environment note is not evidence about `libcp` behavior.
