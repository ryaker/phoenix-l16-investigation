# Index-5 Run-to-Run Nondeterminism Mechanism

## Result

Profile-3 index-5 depth nondeterminism is scheduler-induced. The installed
mode-8 G-43 worker performs an unsynchronized non-atomic read/modify/write on
shared Cost-volume payload lanes while multiple workers for the same
`StereoLayer<false>` object are simultaneously active. Task order also changes
pre-G42 prefusion/calibration outcomes on the tested Unit-2 tele input.

It is not caused by the selected Skip-mask RNG, uninitialized G-43 scratch, or
a non-associative floating-point reduction at the shared payload update.

The behavior is suppressible. Forcing generic executor `0x2d30` through its
installed ascending per-index fallback order makes complete `2080x1560`
index-5 maps byte-identical across repeated Unit-1 `28mm`, Unit-1 `150mm`, and
Unit-2 `70mm` runs. The control changes scheduling only; it calls the original
worker callbacks and does not replace their arithmetic.

## Artifacts

- Main verifier:
  `tools/lldb_probes/index5_nondeterminism/verify_index5_nondeterminism.py`
- Exact index-5 capture:
  `capture_index5_interpose.c`, `run_index5_capture.sh`
- Live overlap measurement:
  `measure_mode8_overlap_interpose.c`
- Deterministic executor control:
  `force_executor_2d30_serial_interpose.c`
- Pre-G42 operand/bank capture:
  `run_g42_bank_capture.sh`, `capture_create_stereo_banks_interpose.c`,
  `capture_geometry_banks_interpose.c`, and
  `capture_current_bank_writes_interpose.c`
- Parent-gate repeat:
  `parent_decision_unit2_70mm_r1.lldb`,
  `parent_decision_unit2_70mm_r2.lldb`, and
  `summarize_parent_decision_repeat.py`
- Reused admitted payload arithmetic reports:
  `runs/codex_276860_payload_vector_formula/vector_formula_*.json`
- New ignored runtime artifacts:
  `runs/index5_nondeterminism/`

No `/tmp` or `/private/tmp` artifact is an evidence dependency.

## Installed Bit-Level Race

The verifier pins installed `libcp.dylib`:

```text
SHA-256 b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The exact `0x277a06..0x277a15` window has SHA-256
`7228de99120380b22f6075397f0d8072d558d80ac9e8c772af2f182de2bc76ff`
and decodes as:

```text
0x277a06  movdqu   xmm5, [r9 + 2*rdx]
0x277a0c  paddusw  xmm5, xmm0
0x277a10  movdqu   [r9 + 2*rdx], xmm5
```

There is no `lock` prefix or surrounding synchronization. The accepted
payload-formula proof independently establishes that this computes:

```text
payload = sat_add_u16(previous_payload, directional_increment)
```

The prior four-focal hardware-watch reports show different pthreads writing
the same exact payload address through this store in one render per tier:

| Focal | Shared payload address | Writer pthread IDs |
|---|---|---|
| `28mm` | `0x7fed60800048` | `15369583`, `15369586` |
| `35mm` | `0x7f8bef660048` | `15370425`, `15370431` |
| `70mm` | `0x7f82a2700048` | `15371171`, `15371173` |
| `150mm` | `0x7f8aa3700048` | `15372238`, `15372240`, `15372241` |

A separate low-perturbation Unit-2 `70mm` run counted `4,040` live
`0x276860` calls. Global worker concurrency reached `9`; the object whose
stored `stereo_index` is exactly `5` also reached `9` simultaneously active
workers and recorded distinct pthread IDs. Therefore the same worker object is
executed concurrently, while the worker's installed payload update is a
non-atomic RMW on addresses shared across worker threads. This is a concrete
lost-update/data-race window, not an inference from output variance alone.

## Baseline Reproduction

The unmodified retained Unit-2 `70mm` pair reproduces the supplied statistic
over all `3,244,800` hypothesis indices:

```text
exact       52.878821499%
within 4    94.360761834%
MAE         1.1026919995 indices
max delta   22 indices
```

The selected pattern-2 Skip mask is already proven as an independent
`std::mt19937(5489)` replay equal to every byte at all four canonical focals.
A separate fixed-`std::random_device` interpose records zero calls before the
G-42 capture boundary. RNG therefore does not explain this repeat pair.

The admitted G-43 initialization verifier rechecks complete initialization of
both `Line buf` and `Min cost buf` halves to `u16 2000` and `Pixel buf` to
zero. The shared update above is saturating integer SIMD. This refutes both an
uninitialized G-43 scratch explanation and non-associative float reduction at
the proven shared accumulation site.

## Upstream Scheduler Manifestation

The first captured pre-G42 difference is also scheduler-sensitive. In two
complete LLDB Unit-2 `70mm` runs, camera key 6 reaches the already-admitted
`0x216f60` parent gate with these exact binary32 words:

| Draw | Winner | Score bits/value | Side bits/value | Result |
|---|---:|---|---|---|
| 1 | `11` | `5c674d3f` / `0.8023583889` | `00000000` / `0` | accepted |
| 2 | `0` | `00007041` / `15` | `0000803f` / `1` | side-cap reject |

This is not a threshold ULP. One draw has a valid candidate and the other has
the exact score/side reject sentinel. The accepted key-6 calibration bank is
stable when present; the variable fact is candidate acceptance. The changed
accepted camera set then changes terminal BA writeback and the composed
geometry used by depth.

This evidence proves an upstream executor-order manifestation and its concrete
parent decision, but does not claim the first unsafe instruction inside that
prefusion producer. The exact unsafe instruction is admitted only for G-43.

## Suppression Experiment

Installed executor `0x2d30` has two paths. With the global worker pool present
it jumps to `0x37c0`; its no-pool fallback invokes callback slot `+0x30` in an
ascending integer loop. The verifier pins the complete `0x2d30..0x2de4`
window (SHA-256
`675ff90a57802a8e0583eb941d64210e1c578940c41f47ab2dca9b94ca466691`).

The control interpose forces that installed fallback ordering while preserving
the callback and callback arithmetic. Results:

| Input | Body/focal | Repeats | Exact map SHA-256 |
|---|---|---:|---|
| `L16_02130` | Unit-1 `28mm` | 2 | `bdc5699206c440db724c65cc869496ba0102dc5fbd26298235b780cf482b0c1b` |
| `L16_02285` | Unit-1 `150mm` | 2 | `449328abd0b6674b3cba3eb68dff8f497f588feca4cf425bf1a8d6f5f6f96260` |
| `L16_00010` | Unit-2 `70mm` | 3 | `b7f734aa6f91c2cf337fac520227e3d14f78253d98c8495a25b28ae7f6a5e2d9` |

The controlled Unit-2 pre-G42 pair also has byte-identical five input image
planes, lookup, projection records, local G-42 curve, initial/current bank
sequence, and all numeric geometry fields. Heap-owner pointers inside the
captured `0xa4` records differ by address and are excluded from the numeric
comparison. Both runs accept parent keys `[6,9,5,7]` and perform identical BA
writeback bytes.

Three weaker controls fail:

| Control | Exact | Within 4 | MAE |
|---|---:|---:|---:|
| `HL_NUM_THREADS=1` | `14.8591%` | `81.1825%` | `2.66130` |
| mutex around each `0x276860` call | `15.6118%` | `82.8758%` | `2.54063` |
| `HL=1` + mutex + frozen dynamic calibration | `32.4849%` | `87.3617%` | `1.93609` |

`HL_NUM_THREADS` does not control libcp's generic executor. A mutex prevents
simultaneous worker bodies but leaves acquisition order variable and does not
stabilize upstream executor work. Deterministic order, not mere exclusion, is
the effective suppression.

## Clean-Room Consequence

A clean-room implementation should not reproduce the data race. It may use a
fixed single-thread schedule, or private per-direction/per-task Cost-volume
accumulators followed by a specified fixed-order saturating-u16 reduction.
Either makes the admitted arithmetic deterministic.

For validation, exact formula and artifact checks remain mandatory. An
arbitrary stock Lumen run cannot be required to match one depth-map hash
because its executor race chooses among schedules. A deterministic clean-room
build can require bit-exact repeat equality to its chosen schedule, while
stock-Lumen comparisons retain the admitted focal-specific repeat envelopes.

## Scope

- Installed race arithmetic and same-address multi-thread writes: Unit-1
  `28/35/70/150mm` plus focal/body-independent pinned code.
- Live same-object overlap and parent-gate discriminator: one Unit-2 `70mm`
  input, `L16_00010`.
- Suppression: Unit-1 `28mm`, Unit-1 `150mm`, and Unit-2 `70mm`.
- Not claimed: other libcp builds/firmware, editor-only paths, deterministic
  final Radiance bytes under the control, or the first unsafe instruction in
  every pre-G42 scheduler-sensitive producer.

## Verification

```bash
python3 tools/lldb_probes/codex_276860_payload_vector_formula/validate_vector_formula.py
python3 tools/lldb_probes/g43_direction_vectors/verify_g43_directions.py
python3 tools/lldb_probes/index5_nondeterminism/verify_index5_nondeterminism.py
```

The final verifier terminates with:

```text
random_device_pre_G42_calls=0 result=PROVEN_SCHEDULING_NONDETERMINISM_SUPPRESSIBLE
```
