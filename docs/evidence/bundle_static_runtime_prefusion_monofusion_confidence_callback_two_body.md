# MonoFusion Secondary-Map Callback Formula

**Date:** 2026-07-02  
**Claim:** `CLM-PREFUSION-002` addendum  
**Scope:** installed `libcp.dylib`; canonical Unit-1 wide route plus an exact-focal
Unit-2 wide discriminator; explicit four-zoom route boundary below

## Question

Mode-0 MonoFusion already had an admitted coefficient Wiener confidence
scalar and a second output-map accumulation, but the installed callback that
converted patch confidence aggregates into the overlap-added scalar was not
decoded. This proof closes that callback formula.

## Reusable Proof

The probe and deterministic verifiers are:

```text
tools/lldb_probes/prefusion_monofusion_worker/
  confidence_unit1_35mm.lldb
  confidence_unit2_28mm.lldb
  monofusion_worker_probe.py
  run_confidence.sh
  validate_confidence_reports.py
  verify_monofusion_worker.py
```

Rerun and verify with:

```bash
tools/lldb_probes/prefusion_monofusion_worker/run_confidence.sh
python3 tools/lldb_probes/prefusion_monofusion_worker/validate_confidence_reports.py
python3 tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py
```

Raw reports are written under ignored
`runs/prefusion_monofusion_worker/`. The dedicated probe intentionally stops
after a bounded callback packet; it is callback-formula evidence, not an
output-completion claim. Complete route/output evidence remains in the prior
MonoFusion two-body/four-focal bundles.

## Installed Formula

The initializer window `0x1b1c70..0x1b1d10` is SHA-256:

```text
10dd2deb34960747494d774ca83982e582f928b4a99760fcb3edeeffdaf64a8f
```

It constructs callback RTTI:

```text
std::__1::__function::__func<
  lt::MonoFusion::initialize(unsigned char const*)::$_0,
  ...,
  float(float,float)>
```

The callback target is `0x1b33a0`; exact window
`0x1b33a0..0x1b33ca` has SHA-256:

```text
0ab16d967217c807212c8b57f2b7a30c73ce035aed6ea08c167209eec400a5b5
```

Let:

- `N` be the MonoFusion source count;
- `C` be the same-group non-mono count;
- `R` be the installed sensor response;
- `alpha = C / (N*R + C)`;
- `c_i` be the already-proven Wiener confidence for source patch `i`.

Mode `0` accumulates:

```text
X = sum_i(1 - c_i)
Y = sum_i(c_i^2)
```

An invalid source overlap contributes the same aggregates as `c_i=0`.
The initializer captures:

```text
p0 = alpha
p1 = 1 - alpha
p2 = 1 / N
p3 = (1-alpha)^2 * C / (N^2 * R)
```

The installed callback computes, in float32 operation order:

```text
secondary_patch =
    (p0 + p1*X*p2)^2 + p3*Y

  = (alpha + (1-alpha)*sum_i(1-c_i)/N)^2
    + ((1-alpha)^2*C/(N^2*R))*sum_i(c_i^2)
```

`0x18d530` then overlap-adds this scalar with the same separable 16x16
half-Hann taps into the secondary output image.

## Runtime Equality

Both admitted packets observed `N=1`, `C=4`, and
`R=2.3183400630950928`. The four captured parameters were identical:

```text
alpha       = 0.6330776214599609
1-alpha     = 0.36692237854003906
1/N         = 1.0
p3          = 0.23229040205478668
```

Unit-1 exact-35mm captured 22 calls. One nontrivial packet was:

```text
X=0.038676679134368896
Y=0.9241425395011902
result=0.6336265206336975
```

Unit-2 exact-28mm captured 23 nontrivial calls. A representative packet was:

```text
X=0.02221369743347168
Y=0.9560660719871521
result=0.6332587003707886
```

Every captured result equals the installed expression bit-for-bit as
float32. Both bodies bind the same RTTI, target `0x1b33a0`, and parameter
tuple.

The two LRIs have different capture dates and may differ in camera firmware
or other capture-era state. Therefore this proof treats the observed
cross-body equality as an implementation discriminator only; it does not
attribute any LRI-value difference or equality to body identity alone.

## Four-Zoom Scope and Admission

Prior admitted complete-route proof establishes that canonical Unit-1
`28mm` and `35mm` use this exact production-profile mode-0 MonoFusion worker,
while canonical `70mm` and `150mm` construct no MonoFusion and take direct
B4. This installed callback formula therefore closes the secondary-map
residual for both active wide tiers; it is explicitly absent, not assumed,
at the two tele tiers. Exact-focal Unit-2 `28mm` independently checks the
second body hash.

Admit the callback formula and overlap-add consequence as a
`CLM-PREFUSION-002` addendum. A later exhaustive basis-matrix proof closes
transform boundaries and packing. Unobserved mode `1` and the outer
distributed selection/reduction and final contributor acceptance policy
remain open.
