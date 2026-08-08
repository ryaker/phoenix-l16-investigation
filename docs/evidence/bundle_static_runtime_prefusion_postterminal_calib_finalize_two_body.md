# Bundle Proof: Post-Terminal Calibration Finalizer

## Scope

This bundle follows terminal higher-group State `0x22e1d0` after its admitted
two-pass calibration-helper sequence. It distinguishes:

- the normal post-state calibration-object finalizer; and
- the optional JPEG/overlay diagnostic body at `0x227b00`.

It does not claim that calibration has no image effect elsewhere. It bounds
only the visible continuation after the terminal higher-group State machine.

## Artifacts

- Probe:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/postterminal_probe.py`
- Exact-focal two-body scripts:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/unit1_35mm.lldb`
  and
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/unit2_35mm.lldb`
- Runner:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/run_two_body_35mm.sh`
- Verifier:
  `tools/lldb_probes/prefusion_postterminal_calib_finalize/verify_postterminal.py`
- Rerunnable ignored outputs:
  `runs/prefusion_postterminal_calib_finalize/unit{1,2}_35mm.{json,log,hdr}`

No `/tmp` artifact is a live dependency.

## Static Identity

The verifier checks installed Mach-O call targets and bytes:

- `0x2277b3 -> 0x22f0f0`: run the higher-group State machine;
- `0x2277c5 -> 0x227b00`: optional diagnostic body;
- `0x3fe505 -> 0x227380`: run the complete higher-group calibration body;
- `0x3fe538 -> 0x226240`: mandatory post-calibration finalizer;
- `0x22637f -> 0x239a90`: construct the replacement calibration sibling;
- `0x226388`: store that replacement at owner `+0x28`;
- `0x3f7733 -> 0x22e9f0`: later owner destruction;
- `0x22ea9c..0x22eaa8`: load owner `+0x28`, then clear it to zero;
- `0x3fbcae -> 0x3fe820`: run the enclosing processing State machine.

Installed RTTI/vtable bytes bind `0x65fff8 -> 0x3fe460` to slot `+0x30` of:

```text
StereoAsyncAPI::start::$_3::operator()(int) const::$_7
```

The function returns high-level `ProcessingState` value `8`. The enclosing
State machine was constructed with target value `8`, so this is the final
registered processing-state body.

The SHA-256 of installed bytes `0x3fe460..0x3fe54e` is:

```text
7c98ec5f98ee6438614802c0915439fdd0f091dec27ccd03170c6c8ed7b062bd
```

The verifier also Capstone-decodes and pins the complete replacement
constructor:

```text
0x239a90..0x239ab7
  sha256=de1eb9c3a668ed7014c4ff7e3a99e8e07aad632beca2f31d3ee4d3f2de3a35f8
0x2399a0..0x239a80
  sha256=46f06252560ef1638eebe13db828b33f7bced9e3758b2e4d37790d22998ae68b
```

`0x239a90` zero-initializes the replacement and tail-jumps to `0x2399a0`.
The decoded body writes only replacement fields
`+0x00/+0x08/+0x10/+0x18/+0x20/+0x28/+0x30/+0x38` and stack storage. Its
only call/tail-call targets are libc++ shared-reference add/release stubs
`0x556314` and `0x556320`; it does not copy the replacement `this` pointer as
a value. Thus this constructor body does not itself publish a separate alias
of the replacement object.

The `0x230790`, `0x2307f0`, `0x230830`, and `0x230870` helpers visible after
the inner State-machine call are recursive tree/container destruction
surfaces. The normal `0x3fe460` continuation then resets/releases local state,
calls `0x226240`, and returns `8`.

The optional `0x227b00` body contains installed strings `"src_"`, `".jpg"`,
`"overlay_hi.jpg"`, and `"overlay_lo.jpg"`. It is guarded at `0x2277b8` by
owner byte `+0x10d`.

## Two-Body Runtime

Complete no-auto-LRIS exact-focal `35mm` runs:

| Physical unit | LRI | owner `+0x10d` | `0x227b00` hits | Finalizer | Processing-machine return |
|---|---|---:|---:|---:|---:|
| Unit-1 | `2018-12-26/L16_03041` | `0` | `0` | `1` | `1` |
| Unit-2 | `2018-07-02/L16_01956` | `0` | `0` | `1` | `1` |

For both runs:

- `0x2277b8` is reached once after terminal higher-group State completion;
- the diagnostic flag is zero and `0x227b00` is not entered;
- the exact owner at `0x3fe50a` is passed to `0x226240`;
- `0x226240` constructs and installs a different non-null sibling pointer at
  owner `+0x28`;
- the caller-post boundary `0x3fe53d` reads the exact replacement pointer;
- the enclosing processing State machine returns normally to `0x3fbcb3`,
  whose visible continuation signals a condition variable and can report
  status through an optional callback.

One read/write hardware watch was armed only after the replacement pointer was
visible at caller-post boundary `0x3fe53d`. Both bodies produce the same
complete later-touch sequence:

| Stop | VA | Slot value | Meaning |
|---:|---:|---|---|
| 1 | `0x22eaa0` | replacement pointer unchanged | pre-store stop at owner destructor's `mov $0, owner+0x28` |
| 2 | `0x22eaa8` | `0` | post-store stop; pointer slot cleared |

Both stacks contain caller return `0x3f7738 -> 0x22e9f0`. There are no earlier
read or write stops. Static code immediately releases fields of the saved
sibling and deletes it after clearing the owner slot.

Observed pointer values are process-local evidence, not constants:

```text
unit1_35mm=OK owner=0x7fc0be016880 overlay_hits=0
  sibling=0x7fc09c0055c0->0x7fc0bbf58020
unit2_35mm=OK owner=0x7fdd17978c80 overlay_hits=0
  sibling=0x7fdd160149a0->0x7fdd16155910
postterminal_calib_finalize=OK
```

## Admission

Admitted for `CLM-PREFUSION-001` and `CLM-PREFUSION-002`:

- the terminal higher-group calibration path is the final
  `StereoAsyncAPI::ProcessingState` lambda (`$_7`) and returns target state
  `8`;
- under the tested exact-focal Unit-1 and Unit-2 `35mm` bridge-HDR runs, its
  post-state continuation skips the optional JPEG/overlay diagnostic body;
- the normal continuation finalizes/replaces an internal calibration sibling
  through `0x226240 -> 0x239a90`, then performs completion signalling/status
  work;
- the installed replacement constructor does not itself publish a separate
  alias: it initializes its own fields and calls only shared-reference-count
  helpers;
- the finalized sibling pointer receives no later touch through its exact
  owner slot before owner destruction clears and releases it.

Claim status remains `PARTIAL`.

## Non-Claims

- Zero overlay hits are scoped to the two tested no-auto-LRIS runs.
- This does not prove the diagnostic route can never execute.
- This does not prove the finalized calibration sibling has no later consumer
  through an alias copied by code outside or after the replacement
  constructor.
- This does not establish a source-image contribution, distributed reducer,
  or final merge acceptance/rejection rule.
