# Evidence: Numeric CalibStage Public Names, Two Body

## Scope

This bundle closes the numeric name mapping for the two `CalibStage` banks in
the already-proven `lt::CapturedImage` objects selected through `state+0xe0`.

The admitted mapping is:

```text
CalibStage 0 = factory = CapturedImage+0x180..+0x1d3
CalibStage 1 = current = CapturedImage+0x12c..+0x17f
```

This is not inferred from the order of words in an error string. It follows
from the complete installed `0xf33d0` reference census, constructor
initialization, later writer behavior, and post-initialization write watches
on exact-focal samples from both physical calibration bodies.

## Artifacts

- Static/runtime verifier:
  `tools/lldb_probes/calibstage_public_names/verify_calibstage_public_names.py`
- Two-bank watch probe:
  `tools/lldb_probes/calibstage_public_names/calibstage_bank_watch_probe.py`
- Exact-focal LLDB scripts:
  `tools/lldb_probes/calibstage_public_names/unit1_35mm.lldb` and
  `unit2_35mm.lldb`
- Runner:
  `tools/lldb_probes/calibstage_public_names/run_two_body_35mm.sh`
- Durable ignored reports and outputs:
  `runs/calibstage_public_names/unit{1,2}_35mm.{json,log,hdr}`
- Reused constructor reports:
  `runs/state_helpers_23c5f0_f33d0_runtime/state_helper_{28mm,35mm,70mm,150mm}.json`
- Reused Unit-1 mutation report:
  `runs/prefusion_264270_output_watch/output_watch_35mm.json`
- Reused Unit-2 mutation report:
  `runs/prefusion_216f60_accepted_bank_consumer/accepted_bank_consumer_unit2_35mm.json`

The runner checksum-stages each LRI into `/private/tmp` because the current
LLDB child cannot open the external photo volume directly. The source LRIs,
checksums, scripts, JSON reports, logs, and copied completed HDR outputs are
the reproducible inputs and durable artifacts. The scratch copies are not
live evidence dependencies.

## Installed Names and Banks

The pinned installed `libcp.dylib` has SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The `0xf33d0` rejection path references the exact installed string:

```text
wrong CalibStage, must be factory or current
```

`0xf33d0` accepts only numeric selectors `0` and `1`:

```text
selector 0 -> write object+0x180..+0x1d3
selector 1 -> write object+0x12c..+0x17f
other      -> error path
```

Accessor `0xf34e0(object, stage)` returns `object+0x12c` for stage `1` and
`object+0x180` otherwise. Its admitted callers constrain the value to the two
accepted stages. Wrapper `0x264440` sets `edx = 1` before tail-jumping to the
record assembler at `0x264270`.

## Complete Writer Census

Capstone extraction over installed `__text` finds exactly ten code references
to `0xf33d0`. Every reference is a direct call; there is no RIP-relative
address-taking reference and no absolute 64-bit pointer to `0xf33d0` in the
installed bytes.

| Call | Selector | Role |
|---:|---:|---|
| `0x1f1328` | `0` | constructor-side first bank initialization |
| `0x1f134b` | `1` | paired constructor-side second bank initialization |
| `0x21159c` | `1` | later update |
| `0x217bbe` | `1` | accepted-record update |
| `0x22bb23` | `1` | later State update |
| `0x22df45` | `1` | existing-record transfer |
| `0x22e755` | `1` | later State update |
| `0x23d38d` | `1` | normalized BA camera-map write-back |
| `0x3f95d6` | `1` | later update |
| `0x3fa84a` | `1` | later update |

Thus selector `0` is used only to seed the retained baseline. Selector `1` is
seeded from the same packet and is the sole stage used by every installed
non-initial `CalibStage` update.

## Public Calibration Origin

The constructor-side `0x1f0ce0` proof already joins the initialization packet
to public LRI calibration carriers:

```text
LightHeader.module_calibration[camera]
  = FactoryModuleCalibration
  .geometry.per_focus_calibration[]
    .intrinsics.k_mat
    .focus_hall_code
    .extrinsics.canonical.rotation
    .extrinsics.canonical.translation

LightHeader.modules[camera].lens_position
  = live focus-selection input
```

The captured helper evaluates/interpolates the factory per-focus intrinsics at
the live lens position. Wide A1-A5 K/pose packets are exact public calibration
copies; B4/C5 poses are exact public copies; the admitted B/C K packets are
already focus-derived at this edge. This focus-evaluated factory-calibration
packet is copied identically into both banks at construction.

Across the four completed Unit-1 focal reports, the verifier independently
checks `40` object-level selector-0/selector-1 initialization pairs. Every
pair has identical K, pose, and three-integer source bytes.

The retained baseline bank is therefore the installed `factory` stage:
selector `0`, `CapturedImage+0x180`. The second copy is the installed
`current` stage: selector `1`, `CapturedImage+0x12c`, because all later
selection, State transfer, BA camera-map normalization, and write-back work
targets that bank.

## Two-Body Runtime Discriminator

The new complete no-auto-LRIS bridge-HDR runs use exact-focal `35mm` inputs:

| Body | LRI | Full LRI SHA-256 | Calibration prefix |
|---|---|---|---|
| Unit-1 | `2018-12-26/L16_03041.lri` | `71eff3d02b8b85af7f3256895eee0fcca073bb745939534abfd7eac83533b0ba` | `722a6e721636c9c4` |
| Unit-2 | `2018-07-02/L16_01956.lri` | `018aa5af4e94830c495eedb039beb7d3fce8d010c5b034ab9ebe38b2c3eed664` | `223961c6bce6153e` |

Both runs:

- exit `0`;
- write a `10432 x 7824` Radiance HDR output;
- select public camera key `5`;
- arm write-only hardware watches only after the paired constructor copies;
- observe byte-identical factory/current banks when the watches are armed;
- observe zero live-`libcp` writes to the selector-0 / factory bank.

The Unit-2 run observes one selector-1 / current-bank write at post-store PC
`0xf345e`, under:

```text
0xf33d0 <- 0x23c5f0@0x23d392 <- State 0x22e1d0@0x22e249
```

That is the already-bounded normalized same-key write-back path. The Unit-1
key-5 object is not selected for a later update in this particular run, so
both watched banks remain unchanged until allocator teardown. The independent
completed Unit-1 `35mm` outcome-gated report proves two selector-1 changes:
existing-record transfer and normalized BA write-back. The independent
Unit-2 accepted-bank report also records the same `0xf345e` selector-1
mutation and exact source copy.

Allocator clearing after object release touches both watched ranges outside
`libcp`; it is classified as teardown, not a semantic bank update.

## Verification

Command:

```bash
python3 tools/lldb_probes/calibstage_public_names/verify_calibstage_public_names.py
```

Output:

```text
calibstage_public_names=OK mapping=0:factory@+0x180,1:current@+0x12c paired_initializations=40 unit1:current_writes=0,factory_writes=0,unit2:current_writes=1,factory_writes=0
```

## Admission

Admitted for `CLM-WARP-003`, `CLM-PREFUSION-001`, and
`CLM-PREFUSION-002`:

- `CalibStage 0` is the `factory` bank at `CapturedImage+0x180`;
- `CalibStage 1` is the `current` bank at `CapturedImage+0x12c`;
- both are initialized from the same focus-evaluated public
  `FactoryModuleCalibration` packet;
- later State selection, transfer, BA normalization, and write-back update the
  `current` bank while retaining the `factory` baseline.

Claim statuses remain unchanged.

## Non-Claims

- This does not identify either complete 0x54-byte bank as one direct
  protobuf message; some fields are runtime-derived from public calibration.
- This does not name all remaining `CapturedImage` fields.
- This does not name the complete `state+0x448` record.
- This does not establish post-helper image/source contribution, reducer
  closure, or final merge acceptance/rejection.
