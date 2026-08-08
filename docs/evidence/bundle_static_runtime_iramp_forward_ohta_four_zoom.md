# Evidence: IRAMP Forward RGB to I1/I2/I3 Application Point

## Result

G-56 is closed for the canonical profile-3 IRAMP route. The direct contributor
images and the `src2` reference image are converted in place from RGB into the
installed three-channel opponent-color domain inside outer body `0x3661b0`,
before reference/candidate patch preparation, score computation, wavelet
reconstruction, and accumulation.

The earlier suggested application point was wrong: helper `0x36b920` does not
perform the color transform. It copies/prepares the selected reference patch,
computes per-channel absolute/statistical work, and begins spatial CDF 9/7
preparation. A complete disassembly census of `0x36b920..0x36cdd2` contains no
cross-channel shuffle/unpack/blend instruction.

## Exact Formula

Let the input `vec4f` be `(R,G,B,q)`. The installed float32 constants are:

```text
a = 0.5773500204086304
b = 0.7071099877357483
c = 0.40825000405311584
d = 0.8165000081062317
```

The forward transform is evaluated in the installed SIMD add/multiply order:

```text
I1 = a*R + a*G + a*B
I2 = b*R + 0*G - b*B
I3 = c*R - d*G + c*B
q' = q
```

Equivalently, the three coefficient columns loaded into `xmm0..xmm2` are:

```text
R: ( a,  b,  c, 0)
G: ( a,  0, -d, 0)
B: ( a, -b,  c, 0)
```

These are exact installed float32 values, not idealized `1/sqrt(3)`,
`1/sqrt(2)`, `1/sqrt(6)`, and `2/sqrt(6)` constants. A bit-exact clean-room
implementation must retain the listed values and operation order.

The admitted inverse tail at `0x36acf0..0x36adac` loads the same scalar table
as rows, applying the transpose:

```text
R = a*I1 + b*I2 + c*I3
G = a*I1        - d*I3
B = a*I1 - b*I2 + c*I3
```

Its output lane 3 is forced to `1.0`. The forward loops instead preserve the
incoming fourth lane with `blendps 8`.

## Application Points

### Direct contributors

The current direct contributor is materialized through
`0x366f1c -> 0x374ac0`. The in-place forward transform follows at
`0x366fd0..0x3670a8`; the representative even-width pair store is
`0x36705f`.

### `src2` reference

`src2` is materialized earlier through `0x36695a -> 0x374ac0`, then bounded
and cropped at `0x368bbb..0x368c4f`. Its duplicate in-place forward transform
is `0x368ce0..0x368db8`, with representative store `0x368d6f`. Only after that
conversion does `0x3692c6 -> 0x36b920` prepare the transformed reference
patch.

### `src1` guide

`src1` is the separately admitted byte guide/bounds operand. It does not pass
through either forward color-transform loop and is not promoted into the
IRAMP merge color domain.

## Static Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier asserts:

- materialization call targets for direct contributors and `src2`;
- exact custody order from materialization through transform to patch prep;
- matching 14-instruction SIMD transform skeletons at both roles;
- channel selectors `0`, `0x55`, and `0xaa`;
- lane-3 preservation through `blendps 8`;
- exact RIP-relative scalar-table load bytes for both forward columns and
  inverse rows; and
- absence of cross-channel mixing instructions throughout `0x36b920`.

## Runtime Proof

A bounded canonical Unit-1 `28mm` LLDB run captures both live store sites. The
two packets independently contain the exact coefficient columns above. Their
first source vectors are border zero, so the zero-output replay is retained
only as a consistency check; the formula claim rests on the byte-pinned SIMD
body and exact live coefficient capture, not on that degenerate sample.

The verifier also re-runs the existing complete IRAMP terminal verifier. Its
normal-completion reports establish `0x3661b0`, transformed-patch scoring,
weighted accumulation, and inverse shaping liveness at canonical Unit-1
`28mm`, `35mm`, `70mm`, and `150mm`.

## Scope

- Formula and application points: SHA-pinned installed code, invariant across
  body and focal inputs for this binary.
- New coefficient/role capture: canonical Unit-1 `28mm`, both direct and
  `src2` roles.
- Merge-critical route liveness: prior complete canonical Unit-1
  `28/35/70/150mm` reports, machine-reverified by this bundle.
- No Unit-2 transform packet is claimed. The installed loops read no public
  calibration/body/firmware selector, so a second-body replay is not needed
  to establish this fixed arithmetic. This does not assert cross-body pixel
  equality or attribute any capture difference to body or firmware.

## Artifacts

- Probe: `tools/lldb_probes/g56_iramp_forward_ohta/forward_ohta_probe.py`
- LLDB scripts: `tools/lldb_probes/g56_iramp_forward_ohta/forward_{28mm,35mm,70mm,150mm}.lldb`
- Runner: `tools/lldb_probes/g56_iramp_forward_ohta/run_four_zoom.sh`
- Verifier: `tools/lldb_probes/g56_iramp_forward_ohta/verify_g56_iramp_forward_ohta.py`
- Admitted new report: `runs/g56_iramp_forward_ohta/forward_28mm.json`
- Joined four-focal reports: `runs/codex_opus_iramp_terminal_validation/`

## Verification

```bash
python3 tools/lldb_probes/g56_iramp_forward_ohta/verify_g56_iramp_forward_ohta.py
```

Expected terminal line:

```text
g56_iramp_forward_ohta=OK
```

## Rejected Upgrades

- `0x36b920` is not the RGB-to-I1/I2/I3 conversion point.
- Contributor/reference patches are not assumed to arrive in I-domain from an
  upstream public format; the outer IRAMP body converts them explicitly.
- The exact installed constants must not be replaced by ideal irrational
  values when bit parity matters.
- `src1` is not a third color-domain image operand.
- This arithmetic proof is not evidence of body or firmware pixel invariance.
