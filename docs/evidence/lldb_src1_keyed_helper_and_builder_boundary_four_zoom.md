# Visible `src1` Keyed Helper And Builder Boundary, Four-Zoom Runtime Proof

**Date:** 2026-05-21
**Status:** admitted evidence candidate for `CLM-PREFUSION-001` / `CLM-C6-001`
**Scope:** bridge HDR path through `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

## Purpose

This note tests a bounded C6-routing candidate beneath the already-proven
visible `src1` source-image producer topology:

- keyed cache helper `libcp+0x1bdc80`
- stack-mode helper `libcp+0x1be750`
- shared vector builder / updater `libcp+0x1be270`

Prior installed-bundle proof showed these functions are structurally reachable
from the visible `src1` `0x3e2e90` source-image local. This runtime proof asks
which of those sites are actually reached in complete canonical bridge HDR
renders, and which camera keys are observed there.

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All runs used `--no-auto-lris` to avoid same-name `.lris` sidecar
contamination. This matters for the canonical `28mm` seed, where a same-name
sidecar exists.

## Repo-Local Probes

Reusable harnesses:

- [src1_keyed_helpers_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_keyed_helpers/src1_keyed_helpers_probe.py)
- [src1_source_builder_indices_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_source_builder_indices/src1_source_builder_indices_probe.py)

LLDB scripts:

- [src1_keyed_helpers_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_keyed_helpers/src1_keyed_helpers_28mm.lldb)
- [src1_keyed_helpers_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_keyed_helpers/src1_keyed_helpers_35mm.lldb)
- [src1_keyed_helpers_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_keyed_helpers/src1_keyed_helpers_70mm.lldb)
- [src1_keyed_helpers_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_keyed_helpers/src1_keyed_helpers_150mm.lldb)
- [src1_source_builder_28mm_nogate.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_source_builder_indices/src1_source_builder_28mm_nogate.lldb)
- [src1_source_builder_35mm_nogate.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_source_builder_indices/src1_source_builder_35mm_nogate.lldb)
- [src1_source_builder_70mm_nogate.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_source_builder_indices/src1_source_builder_70mm_nogate.lldb)
- [src1_source_builder_150mm_nogate.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_source_builder_indices/src1_source_builder_150mm_nogate.lldb)

Raw rerunnable outputs are under ignored `runs/src1_keyed_helpers/` and
`runs/src1_source_builder_indices/`.

## Instrumented Sites

Keyed helper sites:

| VA | Meaning captured by probe |
|---:|---|
| `0x1bdc80` | cache helper entry |
| `0x1bdcfb` | cache helper after `0xe78e0` count return |
| `0x1bde2b` | cache helper lazy call to `0x1be270` |
| `0x1bde5e` | cache helper tree return path |
| `0x1be750` | stack helper entry |
| `0x1be770` | stack helper after `0xe78e0` count return |
| `0x1be7ff` | stack helper lazy call to `0x1be270` |
| `0x1be82e` | stack helper tree return path |

Direct builder sites:

| VA | Meaning captured by probe |
|---:|---|
| `0x1be270` | builder function entry |
| `0x1be291` | initial `0xe6ba0` lookup setup |
| `0x1be2fb` | post-`0xe78e0` loop-count check |
| `0x1be306` | per-index `0xe6ba0` loop lookup setup |

## Four-Zoom Runtime Result

All eight complete renders exited with status `0`. No probe reported runtime
read errors.

| Zoom | `0x1bdc80` hits | `0x1bdcfb` hits | `0x1be750` hits | lazy `0x1be270` callsite hits | direct `0x1be270` body hits | observed helper keys | observed `0xe78e0` counts |
|---|---:|---:|---:|---:|---:|---|---|
| `28mm` | `359` | `359` | `0` | `0` | `0` | `0..9` | `1` |
| `35mm` | `359` | `359` | `0` | `0` | `0` | `0..9` | `1` |
| `70mm` | `298` | `298` | `0` | `0` | `0` | `5..14` | `1` |
| `150mm` | `274` | `274` | `0` | `0` | `0` | `5..14` | `1` |

Detailed zero-hit helper sites in every keyed-helper run:

- `0x1bde2b`: cache-helper lazy call to `0x1be270`
- `0x1bde5e`: cache-helper later tree-return path
- `0x1be750`: stack-helper entry
- `0x1be770`: stack-helper count-return site
- `0x1be7ff`: stack-helper lazy call to `0x1be270`
- `0x1be82e`: stack-helper later tree-return path

Detailed zero-hit direct-builder sites in every direct-builder run:

- `0x1be270`
- `0x1be291`
- `0x1be2fb`
- `0x1be306`

## Safe Conclusions

- Under the tested bridge HDR path, the keyed source-image helper activity is
  limited to the `0x1bdc80` cache-helper entry and its immediate
  post-`0xe78e0` count site.
- Every summarized invocation observed `0xe78e0` count `1`.
- The stack-mode helper `0x1be750` is zero-hit across the canonical four-zoom
  bridge HDR quartet under this probe.
- The vector builder / updater body `0x1be270` is zero-hit across the canonical
  four-zoom bridge HDR quartet under direct no-gate probes.
- The lazy callsites from `0x1bdc80` and `0x1be750` into `0x1be270` are also
  zero-hit across the canonical four-zoom bridge HDR quartet.
- The tele helper key set observed here is `5..14`; key `15` is not observed at
  `70mm` or `150mm`.
- Combined with the existing camera-ID mapping evidence where C6 is key/camera
  `15`, this excludes the tested `0x1bdc80` / `0x1be750` / `0x1be270` helper
  boundary as a positive C6-routing observation on the canonical tele bridge HDR
  runs.

## Non-Conclusions

- This does not prove C6 is unused. Existing evidence still proves C6 fires in
  the tested tele LRIs.
- This does not identify C6's positive routing destination.
- This does not prove these helpers never fire in other Lumen profiles or other
  camera files.
- This does not change the installed-bundle static topology proof: `0x1be270`
  remains statically reachable from helper branches, but it was not live under
  these complete bridge HDR runs.
- This does not identify the exact `src1` / `src2` semantic contents or the
  final merge/reduction closure.
