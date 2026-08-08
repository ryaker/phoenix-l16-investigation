# Static + Runtime Proof: Final-Compositing Case-3 Output Configuration, Four Zooms

## Scope

This note refines the live final-compositing case-`3` path already admitted in
`lldb_final_compositing_case1_case3_boundary_four_zoom.md` and
`lldb_final_output_hdr_writer_boundary_four_zoom.md`.

It asks a narrow Opus-derived validation question: along the canonical CLI
bridge-HDR case-`3` path, what output configuration does helper `0x4182a0`
assemble before handing off to `0x41e180 -> 0x2326a0`?

It proves only tested-path output-configuration custody:

- case-`3` passes record dimensions `10432 x 7824` and format argument `3` into
  `0x4182a0`;
- `0x4182a0` receives output color-space selector value `4`;
- the live helper path uses the format-`3` branch shape and calls `0x41e180`
  with format argument `3`;
- the downstream writer helper receives decoded extension `.hdr`, a populated
  `10432 x 7824` descriptor, row bytes `166912`, and bytes-per-pixel field
  `16`.

It does not prove public enum names, pixel correctness, byte-level
copy-vs-blend behavior, anti-ghosting policy, source contribution, final merge
acceptance/rejection, or non-CLI display/preview/export sinks.

## Repo-Local Artifacts

This proof reuses existing admitted probe artifacts:

- Case-`1`/case-`3` runtime probe:
  `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_boundary_probe.py`
- Case-`1`/case-`3` LLDB scripts:
  `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_28mm.lldb`
  `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_35mm.lldb`
  `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_70mm.lldb`
  `tools/lldb_probes/codex_final_compositing_case1_case3_boundary/case1_case3_150mm.lldb`
- HDR writer-boundary runtime probe:
  `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_boundary_probe.py`
- HDR writer-boundary LLDB scripts:
  `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_28mm.lldb`
  `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_35mm.lldb`
  `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_70mm.lldb`
  `tools/lldb_probes/codex_final_output_hdr_writer_boundary/hdr_writer_150mm.lldb`
- Verifier:
  `tools/verify_final_case3_output_config.py`
- Raw output directories:
  `runs/codex_final_compositing_case1_case3_boundary/`
  `runs/codex_final_output_hdr_writer_boundary/`

No live `/tmp` or `/private/tmp` artifact is cited by this proof.

## Static Anchor

Installed-bundle disassembly for `0x4182a0` shows the branch boundary relevant
to this note:

- `0x41869c` calls an owner virtual slot after loading selector argument
  `0x13`; `0x4186a3` branches to the unexpected-color-space error label
  `0x418d38` only if the returned value is greater than `6`.
- The jump-table arm for returned value `4` loads the string
  `linear_prophoto_rgb`.
- `0x418703` compares `r12d` with `2`, and the `r12d == 2` branch reaches a
  compression-subpath beginning at `0x418797`; that subpath contains the
  compression guard at `0x41880f` and error label `0x418e27`.
- `0x41870d` compares `r12d` with `3`; the `r12d == 3` branch reaches
  `0x418717`, checks / sets `tone_mapping.type` against literal `linear`, and
  joins at `0x418823`.
- `0x4188df..0x418908` passes the assembled local state to `0x41e180` with
  `r8d = r12d`.

This static shape means the runtime `r12d = 3` observations below are not
evidence that the compression guard returned success. They prove the tested CLI
HDR path bypasses the `r12d == 2` compression subpath.

## Runtime Inputs

The reused admitted runtime reports are:

- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_28mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_35mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_70mm.json`
- `runs/codex_final_compositing_case1_case3_boundary/case1_case3_150mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_28mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_35mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_70mm.json`
- `runs/codex_final_output_hdr_writer_boundary/hdr_writer_150mm.json`

All eight admitted reports have exit status `0`, empty `errors`, and no drive
step cap.

## Runtime Results

Verifier command:

```bash
python3 tools/verify_final_case3_output_config.py
```

Output:

```text
28mm: OK dims=10432x7824 format=3 color_selector=4 ext=.hdr row_bytes=166912 bpp=16
35mm: OK dims=10432x7824 format=3 color_selector=4 ext=.hdr row_bytes=166912 bpp=16
70mm: OK dims=10432x7824 format=3 color_selector=4 ext=.hdr row_bytes=166912 bpp=16
150mm: OK dims=10432x7824 format=3 color_selector=4 ext=.hdr row_bytes=166912 bpp=16
```

The verifier checks, for every focal tier:

- `case1_case3` reports hit `0x3bcf16`, `0x4186a3`, `0x4188df`,
  `0x418908`, and `0x418bfd` exactly once;
- the unexpected color-space error label `0x418d38` and unexpected-compression
  error label `0x418e27` both record zero hits;
- the case-`3` call to `0x4182a0` passes `record+0x60` dimensions
  `10432 x 7824` and format argument `3`;
- the `0x4186a3` color-space selector packet records `eax = 4` and `r12d = 3`;
- the `0x418908 -> 0x41e180` call packet records `r8 = 3`;
- the HDR writer-boundary reports hit `0x41e180`, `0x41e599`, `0x2326a0`,
  `0x232731`, `0x232733`, and `0x23274a` exactly once;
- the PPM branch, unexpected export-format path, invalid export-size path, and
  writer no-data path record zero hits;
- `0x41e599 -> 0x2326a0` passes decoded extension `.hdr` and a populated
  descriptor with width `10432`, height `7824`, stride/count `10432`, and a
  nonzero data pointer;
- the virtual writer-call descriptor has width `10432`, height `7824`, row
  bytes `166912`, bytes-per-pixel field `16`, and the same data pointer.

## Proven Facts

1. Under the canonical CLI bridge-HDR quartet, final-compositing case `3`
   reaches helper `0x4182a0` once per render with output dimensions
   `10432 x 7824` and format argument `3`.
2. In every admitted run, the live `0x4182a0` path observes color-space
   selector value `4` at the `0x4186a3` guard and does not reach the
   unexpected-color-space error path.
3. In every admitted run, `0x4182a0` calls `0x41e180` at `0x418908` with
   format argument `3`, then returns normally.
4. Static disassembly plus the live `r12d = 3` packets prove the tested CLI HDR
   case-`3` path takes the format-`3` output-configuration branch and bypasses
   the `r12d == 2` compression subpath containing `0x41880f`.
5. In every admitted run, the downstream writer path receives decoded extension
   `.hdr`, a populated `10432 x 7824` descriptor, row bytes `166912`, and
   bytes-per-pixel field `16`.

## Safe Conclusion

The Opus-derived final-compositing case-`3` lead is now narrower: on the
canonical CLI bridge-HDR path, the live case-`3` record is an HDR writer-bound
output-configuration route. It carries `10432 x 7824` dimensions and format
`3` through `0x4182a0`, observes color-space selector value `4`, bypasses the
format-`2` compression subpath, and reaches the already-admitted `.hdr` writer
boundary with a populated 16-byte-per-pixel descriptor.

This is final-output configuration and writer-custody proof. It is not
copy-vs-blend proof, source-contribution proof, anti-ghosting proof, or final
acceptance/rejection proof.

## Consequence For Blocker Work

Do not describe the live case-`3` helper as an unclassified black box in future
handoffs. For the tested CLI HDR quartet, it is bounded as output
configuration plus HDR writer handoff. The remaining final-policy work is
upstream of this writer boundary: prove where the populated descriptor's pixel
data was assembled, whether source/candidate contributions are accepted or
suppressed before that descriptor, and whether any anti-ghosting / final
acceptance policy remains live outside this case-`3` output-configuration path.
