# LLDB Evidence: Visible `src1` Lower Virtual Target Census Four-Zoom

This note records a repo-local LLDB runtime probe that extends the earlier
first-captured visible-`src1` lower producer proof.

The proof is intentionally narrow:

- it starts only after the first visible `src1` secondary-callable handoff at
  `libcp+0x3e4b09`
- it observes lower branch sites and virtual call sites reached after that gate
- it caps each lower site at `512` hits so complete renders can finish
- capped virtual-call counts are lower bounds, not algorithm constants
- zero-hit observations are scoped to these complete gated bridge-HDR runs

It does not prove semantic `src1` contents, camera membership, C6 routing,
reducer closure, or final merge acceptance / rejection logic.

## Repo-Local Artifacts

Reusable probe harness:

- [src1_virtual_target_census_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_target_census_probe.py)
- [src1_virtual_census_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_census_28mm.lldb)
- [src1_virtual_census_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_census_35mm.lldb)
- [src1_virtual_census_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_census_70mm.lldb)
- [src1_virtual_census_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_virtual_target_census/src1_virtual_census_150mm.lldb)

Rerunnable raw outputs are under ignored repo-local custody:

- `runs/src1_virtual_target_census/src1_virtual_census_28mm.json`
- `runs/src1_virtual_target_census/src1_virtual_census_35mm.json`
- `runs/src1_virtual_target_census/src1_virtual_census_70mm.json`
- `runs/src1_virtual_target_census/src1_virtual_census_150mm.json`

## Canonical Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

All four runs used:

- `tools/lri_process`
- `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- `--profile 3 --export-fmt 3`
- `arch -x86_64 lldb -b -s <script>`

## Probe Shape

The gate breakpoint is:

| Site | Role |
|---|---|
| `0x3e4b09` | visible `src1` secondary callable passes the `0x490` payload to `0x3e2e90` |

After the first gate hit, the probe enables these branch sites:

| Site | Static branch target |
|---|---|
| `0x3e3279` | `0x31af30` |
| `0x3e34e2` | `0x31acf0` |
| `0x3e3653` | `0x31acf0` |

It also enables these lower virtual-call sites:

| Site | Static body |
|---|---|
| `0x33f3e8` | inside `0x33f180` |
| `0x33f94f` | inside `0x33f480` |
| `0x33ffd4` | inside `0x33fb30` |

For each lower virtual hit, the JSON records:

- general-purpose registers
- vector begin/end/index fields, using site-specific register conventions
- first `0x40` bytes of the record at `rsi`
- stack frames normalized to `libcp` VA where applicable
- the callable object's vtable pointer normalized to `libcp` VA
- the effective target read from `qword[vtable + 0x30]`, normalized to `libcp` VA

## Completion

All four runs exited normally and did not hit the drive step cap.

| Zoom | Process exit | Gate callbacks | LLDB gate hit count | Drive steps | Drive step cap |
|---|---:|---:|---:|---:|---|
| `28mm` | `0` | `1` | `4` | `2` | `false` |
| `35mm` | `0` | `1` | `6` | `1` | `false` |
| `70mm` | `0` | `1` | `3` | `1` | `false` |
| `150mm` | `0` | `1` | `6` | `1` | `false` |

The callback gate count is the probe's stateful accepted gate count. The LLDB
gate hit count may be higher because multiple threads can reach the breakpoint
before the callback disables it.

## Branch Hits

These counts are complete for the gated runs because none reached the `512`
site cap.

| Zoom | `0x3e3279 -> 0x31af30` | `0x3e34e2 -> 0x31acf0` | `0x3e3653 -> 0x31acf0` |
|---|---:|---:|---:|
| `28mm` | `48` | `0` | `0` |
| `35mm` | `48` | `0` | `0` |
| `70mm` | `48` | `0` | `0` |
| `150mm` | `24` | `0` | `0` |

Scoped interpretation: under these complete first-visible-`src1`-gated bridge
HDR runs, only the `0x3e3279 -> 0x31af30` branch was observed. This is not a
global proof that the other branches are dead.

## Virtual Site Counts

Each nonzero `512` means the site hit the probe cap and was then disabled.
Those counts are lower bounds. A `0` means zero hits under this exact gated run.

| Zoom | `0x33f3e8` in `0x33f180` | `0x33f94f` in `0x33f480` | `0x33ffd4` in `0x33fb30` |
|---|---:|---:|---:|
| `28mm` | `>=512` | `>=512` | `>=512` |
| `35mm` | `>=512` | `>=512` | `>=512` |
| `70mm` | `>=512` | `>=512` | `0` |
| `150mm` | `>=512` | `>=512` | `0` |

This supersedes any interpretation of the earlier first-hit proof as saying
`0x33f94f` or `0x33ffd4` never fire. The earlier proof remains valid only as a
first-captured-path proof.

## Capped-Window Effective Target Families

The tables below list the effective virtual target families observed before a
site hit its `512` cap. They are not guaranteed to be exhaustive full-render
target sets.

### `0x33f3e8` In `0x33f180`

All four zooms observed the same eleven effective target families before cap:

| Vtable VA | `qword[vtable + 0x30]` target VA |
|---|---|
| `0x65ae40` | `0x340a30` |
| `0x65aec8` | `0x340b00` |
| `0x65b3c8` | `0x341770` |
| `0x65b5c8` | `0x342280` |
| `0x65b9c8` | `0x342c60` |
| `0x65bdb8` | `0x343620` |
| `0x65bf18` | `0x343e10` |
| `0x65c818` | `0x345a10` |
| `0x65ca18` | `0x345d50` |
| `0x65d978` | `0x34a610` |
| `0x65de38` | `0x34b3b0` |

The previously captured `0x65b3c8/+0x30 = 0x341770` target is one member of
this broader capped-window family.

### `0x33f94f` In `0x33f480`

`28mm` and `35mm` observed these six effective target families before cap:

| Vtable VA | `qword[vtable + 0x30]` target VA |
|---|---|
| `0x65af48` | `0x340bf0` |
| `0x65afc8` | `0x340cc0` |
| `0x65b648` | `0x342360` |
| `0x65ba48` | `0x3430d0` |
| `0x65ca98` | `0x345f30` |
| `0x65d9f8` | `0x34a780` |

`70mm` and `150mm` observed those six plus these three additional target
families before cap:

| Vtable VA | `qword[vtable + 0x30]` target VA |
|---|---|
| `0x65be38` | `0x3438d0` |
| `0x65c898` | `0x345ae0` |
| `0x65deb8` | `0x34b8a0` |

### `0x33ffd4` In `0x33fb30`

`28mm` and `35mm` observed these six effective target families before cap:

| Vtable VA | `qword[vtable + 0x30]` target VA |
|---|---|
| `0x65b148` | `0x340f70` |
| `0x65b1c8` | `0x341040` |
| `0x65bea8` | `0x343b80` |
| `0x65c998` | `0x345c80` |
| `0x65da68` | `0x34a8f0` |
| `0x65df28` | `0x34b970` |

`70mm` and `150mm` had zero `0x33ffd4` hits under the same gated complete-run
probe.

## Proven Facts

- The lower visible-`src1` source-producer runtime path is broader than the
  first-captured `0x33f3e8 -> 0x65b3c8/+0x30 = 0x341770` packet.
- Under the completed gated four-zoom runs, `28mm` and `35mm` reached
  `0x33f3e8`, `0x33f94f`, and `0x33ffd4`.
- Under the completed gated four-zoom runs, `70mm` and `150mm` reached
  `0x33f3e8` and `0x33f94f`; `0x33ffd4` had zero hits.
- The observed first-visible-`src1` branch path was `0x3e3279 -> 0x31af30` for
  all four zooms under this gated probe.
- The observed virtual targets are per-source callable families beneath the
  already-bounded source-image producer topology. This does not expose a proven
  multi-input reducer or final acceptance policy.

## Non-Claims

This evidence does not prove:

- the semantic camera membership of `src1`
- the semantic camera membership of `src2`
- C6 routing
- a complete full-render target census after the `512` caps
- public names for these per-source callback families
- the exact pre-fusion merge/reduction mechanism
- final ghost/trailer suppression logic

## Next Proof Boundary

The next safe step is static/runtime classification of the newly observed
effective target families, especially the additional `0x33f94f` and `0x33ffd4`
families. Closure still requires evidence of real multi-input merge/reduction
shape or equivalent distributed selection/acceptance math; the current target
census alone is not closure.
