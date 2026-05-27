# LLDB Evidence: Tele C6 Post-Mutation Downstream Rect-Vector Path

**Date:** 2026-05-27
**Status:** admitted evidence for `CLM-C6-001`
**Scope:** canonical tele bridge HDR path through
`tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

The prior post-mutation state-consumer proof showed that the immediate caller
path after `0x3c8f90` consumes the constructed `ctx+0xa0` object, observes
key `15` / C6 inactive, writes state fields `+0x0 = 3` and `+0x4 = 1` to a
state object stored at context `+0xc8`, and queues context `+0x4b0 = 5`.

This probe follows the next immediate caller segment. It answers only this
narrow question: are the proven `context+0xc8` and `context+0x4b0` state values
reread and handed into a live downstream vector builder under complete canonical
tele bridge HDR renders?

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Both runs used `--no-auto-lris`.

## Repo-Local Probe

Reusable harness:

- [c6_postmutation_downstream_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_downstream/c6_postmutation_downstream_probe.py)

LLDB scripts:

- [c6_postmutation_downstream_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_downstream/c6_postmutation_downstream_70mm.lldb)
- [c6_postmutation_downstream_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/c6_postmutation_downstream/c6_postmutation_downstream_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/c6_postmutation_downstream/`.
Both runs produced completed `10432 x 7824` Radiance HDR outputs and JSON
reports:

- `runs/c6_postmutation_downstream/c6_postmutation_downstream_70mm.json`
- `runs/c6_postmutation_downstream/c6_postmutation_downstream_150mm.json`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/c6_postmutation_downstream/c6_postmutation_downstream_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/c6_postmutation_downstream/c6_postmutation_downstream_150mm.lldb
```

## Instrumented Sites

| Site | Probe name | Why included |
|---:|---|---|
| `0x3b22a6` | `context_c8_reload` | reloads the state object from context `+0xc8` |
| `0x3b22b2` | `after_second_state_code_call` | captures return from `0x40b0e0` before the branch test |
| `0x3b22c3` | `fallback_scale_call_3c8c00` | captures the fallback scale-call branch |
| `0x3b22e4` | `scaled_width_store` | captures raw dimensions and computed width before local store |
| `0x3b22ee` | `scaled_height_store` | captures raw dimensions and computed height before local store |
| `0x3b2313` | `context_4b0_read_before` | reads context `+0x4b0` before handoff |
| `0x3b231a` | `context_4b0_read_after` | confirms `r8d` carries the context `+0x4b0` value |
| `0x3b2339` | `rect_vector_builder_call` | caller-side handoff into `0x3c8d00` |
| `0x3c8d00` | `rect_vector_builder_entry` | callee-side entry packet |
| `0x3c8dd5` | `builder_scaled_width_write` | callee writes rounded/scaled width |
| `0x3c8dd8` | `builder_scaled_height_write` | callee writes rounded/scaled height |
| `0x3c8eab` | `builder_first_rect_done` | first 16-byte integer tuple is present |
| `0x3c8f42` | `builder_return` | final vector state at return |

## Static Context

The caller segment immediately after the prior state proof performs this
sequence:

- `0x3b22a6` loads `context+0xc8`.
- `0x3b22ad` calls `0x40b0e0`; `0x3b22b2` tests the returned `eax`.
- If that code is not positive, `0x3b22c3` calls `0x3c8c00` as the fallback
  scale path.
- The caller stores a computed width/height pair at locals `rbp-0x1b0` and
  `rbp-0x1ac`.
- `0x3b2313` reads `context+0x4b0` into `r8d`.
- `0x3b2339` calls `0x3c8d00` with output vector, context, scaled pair, raw
  pair, `r8d`, and a separate rectangle-like input pointer.

Static inspection of `0x3c8d00` shows a vector builder over 16-byte integer
tuples:

- It saves incoming `r8d` to local `rbp-0x3c`.
- It reads the raw pair from `rcx` and the scaled pair from `rdx`.
- It rounds / replaces the scaled pair at `0x3c8dd5` and `0x3c8dd8`.
- It allocates and writes the first 16-byte integer tuple at
  `0x3c8e99..0x3c8ea3`.
- If the saved `r8d` code is at least `2`, it appends additional tuples by
  right-shifting the prior tuple inside `0x3c8edc..0x3c8f40`.
- It returns the output vector at `0x3c8f42`.

The public semantic name of this vector is not proven here.

## Runtime Result

Both tele runs completed with process status `0`.

| Site | `70mm` hits | `150mm` hits |
|---:|---:|---:|
| `0x3b22a6` | `1` | `1` |
| `0x3b22b2` | `1` | `1` |
| `0x3b22c3` | `1` | `1` |
| `0x3b22e4` | `1` | `1` |
| `0x3b22ee` | `1` | `1` |
| `0x3b2313` | `1` | `1` |
| `0x3b231a` | `1` | `1` |
| `0x3b2339` | `1` | `1` |
| `0x3c8d00` | `1` | `1` |
| `0x3c8dd5` | `1` | `1` |
| `0x3c8dd8` | `1` | `1` |
| `0x3c8eab` | `1` | `1` |
| `0x3c8f42` | `1` | `1` |

The state and dimension packets matched in both tele seeds:

| Observation | `70mm` | `150mm` |
|---|---:|---:|
| reloaded `context+0xc8` state field `+0x0` | `3` | `3` |
| reloaded `context+0xc8` state field `+0x4` | `1` | `1` |
| second `0x40b0e0` return code | `0` | `0` |
| fallback `0x3c8c00` branch reached | yes | yes |
| raw pair before scaling | `(4160, 3120)` | `(4160, 3120)` |
| caller computed scaled pair before builder | `(8914, 6685)` | `(8914, 6685)` |
| `context+0x4b0` read before builder | `5` | `5` |
| `r8d` at builder handoff / entry | `5` | `5` |
| builder-rounded scaled pair | `(8896, 6672)` | `(8896, 6672)` |

The final output vector at `0x3c8f42` held five 16-byte integer tuples in both
tele seeds:

| Zoom | Output tuples |
|---|---|
| `70mm` | `(16,16,8848,6640)`, `(8,8,4424,3320)`, `(4,4,2212,1660)`, `(2,2,1106,830)`, `(1,1,553,415)` |
| `150mm` | `(2368,1776,6528,4896)`, `(1184,888,3264,2448)`, `(592,444,1632,1224)`, `(296,222,816,612)`, `(148,111,408,306)` |

## Proven Facts

- The state object stored at context `+0xc8` by the prior post-mutation
  state-consumer path is reread in both canonical tele bridge HDR runs.
- The reread state still has fields `+0x0 = 3` and `+0x4 = 1`.
- A second call to `0x40b0e0` returns `0` in both tele seeds, and the fallback
  `0x3c8c00` branch is reached in both seeds.
- The caller computes scaled dimensions from raw pair `(4160,3120)` to
  `(8914,6685)`, and `0x3c8d00` rounds the scaled pair to `(8896,6672)`.
- The queued `context+0x4b0 = 5` value is reread and passed as `r8d = 5` into
  `0x3c8d00`.
- `0x3c8d00` returns a five-entry vector of 16-byte integer tuples in both
  canonical tele seeds.
- The first tuple and resulting pyramid-like tuple sequence differ between
  `70mm` and `150mm`, while the raw/scaled dimension inputs and level code
  match.

## Non-Conclusions

- This does not prove C6 contributes to final image output.
- This does not prove C6 is globally unused.
- This does not prove the `0x3c90a5` mutation is terminal.
- This does not prove the five-entry vector affects final merge acceptance,
  rejection, crop, or image contribution.
- This does not identify the downstream consumer of the vector returned by
  `0x3c8d00`.
- This does not exclude alternate C6 routes before the mutation, outside this
  post-mutation downstream segment, or outside the focused/tested `0xf2720`
  callsites.
- This does not assign public semantic names to `context+0xc8`,
  `context+0x4b0`, `0x3c8c00`, `0x3c8d00`, or the vector's tuple fields.
