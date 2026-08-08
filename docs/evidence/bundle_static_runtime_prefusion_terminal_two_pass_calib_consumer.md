# Bundle Proof: Terminal Two-Pass CalibStage Consumer

## Scope

This bundle advances the admitted wide calibration-record path one bounded
consumer step beyond the BA camera-map normalization and selector-1
CalibStage write-back proved in
`bundle_static_runtime_prefusion_wide_minimum_selector_calibstage_transfer.md`.

It asks one exact question:

> Does terminal State `0x22e1d0`'s second `0x23c5f0` pass read the same
> per-camera selector-1 bank written by normalization in its first pass?

The answer is yes for the outcome-gated Unit-1 `35mm` transaction. Separate
complete Unit-1 and Unit-2 exact-focal `35mm` controls prove that the terminal
two-pass keyed call topology is shared by both physical units.

## Durable Artifacts

- Outcome-gated probe:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/prefusion_264270_output_watch_probe.py`
- Focused outcome runner:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/run_264270_output_watch_35mm.sh`
- Outcome verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_264270_output_watch.py`
- Two-body control probe:
  `tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/terminal_two_pass_probe.py`
- Two-body control runner:
  `tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/run_two_body_35mm.sh`
- Two-body control verifier:
  `tools/lldb_probes/prefusion_terminal_two_pass_calib_consumer/verify_two_pass.py`
- Rerunnable ignored outputs:
  `runs/prefusion_264270_output_watch/output_watch_35mm.{json,log,hdr}` and
  `runs/prefusion_terminal_two_pass_calib_consumer/unit{1,2}_35mm.{json,log,hdr}`

No `/tmp` artifact is a live evidence dependency.

## Static Boundary

The verifier independently decodes the installed Mach-O and checks:

- `0x22e244 -> 0x23c5f0`, returning at `0x22e249`;
- `0x22e283 -> 0x23c5f0`, returning at `0x22e288`;
- internal selector-1 assembly calls
  `0x23c6c0`, `0x23cba6`, and `0x23d226` to wrapper `0x264440`;
- normalized write call `0x23d38d -> 0xf33d0`;
- exact `0x264440` wrapper bytes that set `edx = 1` and tail-jump to
  `0x264270`;
- SHA-256
  `8cbfdfb06337fa3a47975a4c72e2fa42149d04729aa2d4567afa2e589ea2a171`
  for installed bytes `0x22e20e..0x22e287`.

The two `0x23c5f0` calls receive identical `rdi`, `rsi`, `rdx`, `rcx`,
`r8d = 1`, and `r9d = 11` arguments. The first call can change shared
per-camera calibration objects before the second call begins.

## Exact Outcome-Gated Custody

The completed Unit-1 `35mm` packet follows public camera key `5`:

1. In terminal pass 1, under outer return `0x22e249`, the normalized
   `0x23d38d -> 0xf33d0` call writes object
   `0x7fc835a06de0` selector-1 bank `+0x12c..+0x17f`.
2. The destination object's `+0x60` key, helper local key, selected-node key,
   and copied BA-map node key are all `5`. Earlier admitted evidence binds
   this carrier to public `CameraModule.id`.
3. The post-call bank equals the exact concatenation of the three normalized
   source slices and differs from its pre-call bytes.
4. At the second terminal helper callsite `0x22e283`, the complete 84-byte
   bank and key are still bit-identical to the pass-1 post-write snapshot.
5. Six selector-1 assembly callsites are observed before the tracked object
   is reached. At pass-2 callsite `0x23cba6`, `rsi` equals the exact object
   address, key remains `5`, and the complete source bank equals the pass-1
   post-write bank byte for byte.
6. Stack ancestry is
   `0x23cba6 <- 0x22e288 <- 0x22f3ff`, proving this is the second terminal
   helper pass rather than another `0x23c5f0` caller.

The focused outcome verifier passes the complete existing custody chain and
the new post-write assertions:

```text
static_264270_output_watch=OK
35mm: ... decision=retain_existing_and_transfer
```

## Two-Body Control

Complete no-auto-LRIS exact-focal `35mm` renders were run for:

| Physical unit | LRI | Pass-1 assembly reads | Pass-2 assembly reads | Banks changed between pass observations |
|---|---|---:|---:|---:|
| Unit-1 | `2018-12-26/L16_03041` | 19 | 19 | 14 |
| Unit-2 | `2018-07-02/L16_01956` | 19 | 19 | 12 |

Both runs have the same ordered keyed route:

```text
0x23c6c0: key 0
0x23cba6: keys 1..9
0x23d226: keys 1..9
```

For every paired pass-1/pass-2 position, the callsite, source object identity,
source key, and selector-1 wrapper are equal. Bank values are allowed to
differ: the controls intentionally establish shared mechanism/topology, not
universal numeric calibration values. Neither control run took the
outcome-gated normalized-write branch, so they are not used as duplicate
post-write custody proof.

Verifier output:

```text
unit1_35mm=OK ... changed_banks_between_passes=14
unit2_35mm=OK ... changed_banks_between_passes=12
terminal_two_pass_calib_consumer=OK
```

## Admission

Admitted for `CLM-PREFUSION-001` and `CLM-PREFUSION-002`:

- terminal State `0x22e1d0` is a two-pass calibration-helper sequence;
- one exact same-public-camera-key normalized selector-1 bank written in
  pass 1 is consumed byte-identically through `0x264440` in pass 2;
- the two-pass keyed assembly topology is shared by the tested exact-focal
  Unit-1 and Unit-2 `35mm` renders.

Claim status remains `PARTIAL`.

## Non-Claims

- This does not prove an image or source-image effect.
- This does not identify the complete selected record with a public protobuf
  field name.
- This does not prove every camera key or focal tier takes the normalized
  write branch.
- This does not close the distributed `src1` / `src2` reducer or final merge
  acceptance/rejection.
