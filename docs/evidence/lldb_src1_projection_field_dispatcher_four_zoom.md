# Visible `src1` Projection Field Dispatcher, Four-Zoom Runtime Proof

**Date:** 2026-05-21
**Status:** admitted evidence candidate for `CLM-PREFUSION-001` / `CLM-C6-001`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This note runtime-tests the already statically bounded projection field-pack
dispatcher beneath the visible `src1` payload constructor:

- dispatcher entry `libcp+0x3f6170`
- same-category branch `libcp+0x3f61ca -> 0x3f6200`
- cross-category branch `libcp+0x3f61e1 -> 0x3f6940`

Prior installed-bundle proof showed `0x3e27a0` calls `0x3f6170` to produce the
fields consumed by the live `0x3e42e0` projection callable. This runtime proof
asks which keys reach the dispatcher and whether tele key `15` / C6 appears at
this boundary.

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination.

## Repo-Local Probes

Reusable harness:

- [projection_field_dispatcher_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/projection_field_dispatcher/projection_field_dispatcher_probe.py)

LLDB scripts:

- [projection_field_dispatcher_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/projection_field_dispatcher/projection_field_dispatcher_28mm.lldb)
- [projection_field_dispatcher_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/projection_field_dispatcher/projection_field_dispatcher_35mm.lldb)
- [projection_field_dispatcher_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/projection_field_dispatcher/projection_field_dispatcher_70mm.lldb)
- [projection_field_dispatcher_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/projection_field_dispatcher/projection_field_dispatcher_150mm.lldb)

Raw rerunnable outputs are under ignored `runs/projection_field_dispatcher/`.

## Instrumented Sites

| VA | Probe label | Meaning captured by probe |
|---:|---|---|
| `0x3f6170` | `dispatcher_entry_3f6170` | dispatcher entry, captures `edx` key and caller |
| `0x3f61b8` | `dispatcher_class_compare_3f61b8` | captures key class and state class immediately before branch choice |
| `0x3f61ca` | `same_branch_call_3f61ca` | callsite into same-category producer |
| `0x3f61e1` | `cross_branch_call_3f61e1` | callsite into cross-category producer |
| `0x3f6200` | `same_entry_3f6200` | same-category producer entry |
| `0x3f6940` | `cross_entry_3f6940` | cross-category producer entry |

## Four-Zoom Runtime Result

All four complete renders exited with status `0`. No probe reported runtime read
errors.

Each zoom produced the same total branch shape:

| Zoom | dispatcher entries | class compares | same-branch calls / entries | cross-branch calls / entries |
|---|---:|---:|---:|---:|
| `28mm` | `7` | `7` | `2 / 2` | `5 / 5` |
| `35mm` | `7` | `7` | `2 / 2` | `5 / 5` |
| `70mm` | `7` | `7` | `2 / 2` | `5 / 5` |
| `150mm` | `7` | `7` | `2 / 2` | `5 / 5` |

Observed keys and branch classes:

| Zoom | observed keys | same-category key | cross-category keys | same key class/state class | cross key class/state class |
|---|---|---:|---|---|---|
| `28mm` | `0, 5, 6, 7, 8, 9` | `0` | `5..9` | `0 / 0` | `1 / 0` |
| `35mm` | `0, 5, 6, 7, 8, 9` | `0` | `5..9` | `0 / 0` | `1 / 0` |
| `70mm` | `8, 10, 11, 12, 13, 14` | `8` | `10..14` | `1 / 1` | `2 / 1` |
| `150mm` | `8, 10, 11, 12, 13, 14` | `8` | `10..14` | `1 / 1` | `2 / 1` |

Observed dispatcher entry callers:

| Key class | Caller VA(s) | Observed role in this probe |
|---|---|---|
| same-category visible key | `0x3e2910`, `0x3eb2fc` | the visible anchor key appears twice |
| cross-category direct keys | `0x3e05fa` | each direct contributor key appears once |

## Safe Conclusions

- The `0x3f6170` projection field-pack dispatcher is live under the canonical
  bridge HDR quartet.
- At `28mm` and `35mm`, it sees visible key `0` plus direct keys `5..9`.
- At `70mm` and `150mm`, it sees visible key `8` plus direct keys `10..14`.
- Tele key `15` / C6 is not observed at this dispatcher boundary under the
  tested complete bridge HDR runs.
- This runtime result matches the already proven visible-anchor/direct-key
  split from nearby `src1` lookup and direct-contributor evidence.
- This excludes `0x3f6170` / `0x3f6200` / `0x3f6940` as a positive C6-routing
  observation under the canonical tele bridge HDR runs.

## Non-Conclusions

- This does not prove C6 is unused. Existing evidence still proves C6 fires in
  the tested tele LRIs.
- This does not identify C6's positive routing destination.
- This does not prove `0x3f6170` never sees key `15` in other render profiles,
  other LRIs, or non-bridge paths.
- This does not identify public calibration field names or LRI field origins
  for the projection field pack.
- This does not identify the exact semantic contents of `src1` / `src2` or the
  exact upstream merge/reduction mechanism.
