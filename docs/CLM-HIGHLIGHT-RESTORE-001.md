# CLM-HIGHLIGHT-RESTORE-001 — Lumen's Bayer highlight-restore stage

Status: **CLOSED** (2026-08-03). Kernel math proven and ported; gain-vector source
proven; end-to-end image-quality win measured on the canonical corpus.

Binary of record: `libcp.dylib`
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## 1. Where it sits

Pipeline order (CLM-PIPELINE-001), Bayer stage index 2:

    hot pixel (0x341770) -> HIGHLIGHT RESTORE (0x343e10) -> default Bayer
    normalization/materialization (0x340a30 -> 0x350ff0) -> cross talk (0x342280)
    -> demosaic (0x342c60) -> CNR (0x34b3b0) -> ...

Phoenix insertion point: `tools/phoenix_fuse.cpp`, inside `buildPlane`, between
`depth::hotPixelRemove` and `premerge::demosaickLightV1`. Env gate `PHX_NOHR`
reverts to the previous behaviour.

## 2. The four phase kernels are one kernel

`0x343e10` dispatches on CFA phase through the table at `0x30b801`–`0x30b833`:

    phase (0,0) -> 0x30b9f0    phase (1,0) -> 0x30dcc0
    phase (0,1) -> 0x30ff60    phase (1,1) -> 0x3121f0

A mnemonic-multiset and constant-pool-address-set diff across all four shows the
same math with swapped CFA parity:

    k0 0x30b9f0 insn=2060 distinct_mnem=75 const_refs=21
    k1 0x30dcc0 insn=2056 distinct_mnem=75 const_refs=21
    k2 0x30ff60 insn=2054 distinct_mnem=75 const_refs=21
    k3 0x3121f0 insn=2044 distinct_mnem=72 const_refs=21
    mnemonic diff vs k0:  k1 {mov:2, xorps:2}   k2 {mov:6}
    constant-pool address set diff vs k0:  only_k0=[]  only_kN=[]  (ALL THREE)

All four reference the identical set of 21 constant-pool addresses. One
phase-parametric implementation therefore covers the family, and this was
confirmed empirically: the same code reproduces both the (0,0) and the (1,1)
ground-truth tiles.

## 3. Semantics

Gate: `aux` = 3x3 max filter of the source plane; restore applies where
`aux >= 1007` = `(int)(0.985 * 1023)`.

Per pixel, a full colour triple is synthesized at the centre site, run through the
highlight core, and the centre's own channel is written back.

Green estimate at a non-green site (Hamilton–Adams, integer, `ratio` = Q10 of
`1/c0` for red-keyed and `1/c2` for blue-keyed sites):

    hl = ((2C - W2 - E2) * ratio) >> 10      vl = ((2C - N2 - S2) * ratio) >> 10
    cH = |hl| + |E - W|                      cV = |vl| + |S - N|
    h4 = max(hl, -40) + 2(W + E)             v4 = max(vl, -40) + 2(N + S)
    sel = cH > cV ? v4 : h4 ; sel16 = sel < 0 ? 0 : (sel & 0xFFFF)

Green-centre blocks round-trip `sel16` through `cvttss2si`/`movzx`, i.e. integer
`>> 2`; red/blue-centre blocks use `float(sel16) * 0.25`.

Chroma estimate (`0x30c2a7`–`0x30c318`), four diagonal neighbours for R/B centres,
two axial for green centres:

    w_i = rcp(|g_i - g_c| * (1/981) + 0.009765625)
    est = ( sum_i w_i (v_i * (1/c) - g_i) ) / ( sum_i w_i ) + g_c ,  then * (c/c1)

Highlight core (`0x30c320`–`0x30c4dd`), identical in all four pixel blocks, on the
normalised triple `p = (triple - 42) * norm`:

    w    = clamp( (p - 0.85/c) * (20/3)c , 0, 1 )
    S    = hsum(w)                                  (lane 3 = 0)
    m    = rcp(3.0000100135803223 - S) * hsum((1-w) p)
    r1   = p + w (m - p)
    r2   = p + min(S,1) (max(p,r1) - p)
    maxc = max(r2_0, r2_1, r2_2, 0)                 (0x30c3f1 zeroes lane 3)
    mean = (r2_0 + r2_1 + r2_2) / 3
    d    = p - 0.9 ;  n2 = d_0^2 + d_1^2 + d_2^2    (0x30c42a zeroes lane 3)
    dot  = hsum( (d * rsqrt(n2)) . kdir )
    t    = min(1, max(0, S-1)) * max(0, dot)
    r3   = r2 + t (mean - r2)
    u    = max(S - 2, 0)                            (NOT clamped to 1)
    out  = r3 + u (maxc - r3)
    store = cvttss2si( 42 + out_lane * 981 * c_lane )   bare 16-bit, NO clamp

Everything in the prologue is a function of the per-camera gain vector
`r9 = (c0, 1, c2)`:

    inv0 = 1/c0                     inv2 = 1/c2
    q_red  = (int)(1024 * inv0)     q_blue = (int)(1024 * inv2)     [truncated]
    norm   = (inv0/981, 1/981, inv2/981)
    k085   = (0.85 inv0, 0.85, 0.85 inv2)
    slope  = (20/3) * (c0, 1, c2)
    denorm = 981 * (c0, 1, c2)
    kdir   = normalize( (inv0 - 0.9, 0.1, inv2 - 0.9) )

Kernel literals (`tools/readconst.py`): `0x5f3e28 = (3.0000100135803223, 0.0,
0.009765625, 0.009765625)`, `0x5f3e40 = (-0.9,-0.9,-0.9,-0.9)`,
`0x5aae88 = (0.33333334, 0.66666669, 38.667, 0.0088564521)`.

## 4. The per-camera gain vector `c` — PROVEN

`c` reaches the kernel as `r9` via `0x343ed9: mov rcx,[rbx]` -> `call 0x30b770` at
`0x343ef8` -> `0x30b784: mov r14,rcx` -> stored into the closure at `[rax+0x20]`.

It is **the camera's neutral RAW response at the scene white**:

    M_blend = D65.color_matrix + ccm_alpha * (A.color_matrix - D65.color_matrix)
    q       = M_blend * XYZ(scene_xy)          (NON-transposed)
    c       = (q0/q1, 1, q2/q1)

Two facts pinned the convention from the LRI's own data rather than by assumption:

1. The `[hrconv]` probe applied all four variants (`M`, `M^T`, `M^-1`,
   `(M^-1)^T`) to the D65 white `(0.31271, 0.32902)` and compared against each
   camera's OWN stored `rg_ratio`/`bg_ratio`. Only plain `M` reproduces them
   (cam 0: stored `(0.505174, 0.696266)` vs `M` `(0.514507, 0.695704)`; `M^T`,
   `M^-1`, `(M^-1)^T` are off by factors of 2–6).
2. Lanes 3–4 of Lumen's 16-float `r9` struct are `(0.34749818, 0.35518271)` —
   exactly the scene xy Phoenix's Robertson solve already produces.

Result, against the four distinct cameras captured on `L16_03041`
(`ccm_alpha = 0.251384`, `scene_xy = (0.3475, 0.3552)`):

    captured (0.5555472, 1, 0.6055743)  cam  6  Mblend@scene (0.5555469, 1, 0.6055744)
    captured (0.5550174, 1, 0.5953865)  cam  7  Mblend@scene (0.5550171, 1, 0.5953866)
    captured (0.5426871, 1, 0.5913603)  cam  5  Mblend@scene (0.5426869, 1, 0.5913604)
    captured (0.5568259, 1, 0.6148009)  cam  8  Mblend@scene (0.5568257, 1, 0.6148010)

All four to 1e-6. It is the **global** anchor `ccm_alpha`, not a per-camera
Robertson solve — `Mpc@scene` diverges in the 4th decimal and does not match.

Rejected en route, with receipts:

* **Linear blend of the stored `rg_ratio`/`bg_ratio` endpoints.** Structurally the
  right family (solved alphas land in 0.22–0.32, bracketing `ccm_alpha`) but no
  camera matched a capture in both channels. Those stored ratios are the same
  quantity evaluated *at* the endpoints; the value at an intermediate illuminant
  is not the linear blend of them.
* **Per-camera Robertson solve.** `alpha_pc` ranged 0.2376–0.3196 and was strictly
  worse than the global alpha on the two cleanest assignments.

## 5. Numeric fidelity

x86 `rcpps`/`rcpss`/`rsqrtps` are ~12-bit approximations. Modelled five
quantizations; truncating the f32 mantissa to 12 explicit bits (`u &= 0xFFFFF800`)
beats exact IEEE division on every tile:

    exact     t0 99.6768%  t2 97.8718%  t3 95.0320%
    trunc12   t0 99.7582%  t2 98.5349%  t3 96.6485%   <-- adopted
    round12   t0 99.6643%  t2 96.4979%  t3 94.2711%
    round11   t0 99.6393%  t2 96.3208%  t3 93.9376%
    round14   t0 99.6738%  t2 97.8616%  t3 95.1720%

`trunc12` is deterministic and portable to arm64. Bit-exactness beyond this is
unattainable and would be the wrong target: the ground-truth tiles were captured
under Rosetta 2, so the "hardware" `rcpps` in the capture is itself an emulation.
±1 DN is below the original binary's own cross-host determinism floor.

## 6. Verification

C++ port (`engine/depth/highlight_restore.{h,cpp}`) against the six Lumen
ground-truth tile pairs, via `tools/lldb_probes/highlight_restore/hr_cxx_check.cpp`:

    tile0 590x462 phase=[1,1]  exact=99.7582%  |d|<=1=100.0000%  maxdiff=1
    tile1 626x456 phase=[1,1]  exact=97.1459%  |d|<=1=100.0000%  maxdiff=1
    tile2 450x630 phase=[0,0]  exact=98.5349%  |d|<=1=100.0000%  maxdiff=1
    tile3 618x474 phase=[1,1]  exact=96.6485%  |d|<=1=100.0000%  maxdiff=1
    tile4 468x626 phase=[0,0]  exact=98.7252%  |d|<=1=100.0000%  maxdiff=1
    tile5 678x680 phase=[1,1]  exact=99.2408%  |d|<=1=100.0000%  maxdiff=1

100% of pixels within ±1 DN on every tile, and the independently-inferred CFA
phase matches Lumen's reported phase on all six.

## 7. Caveats

* A 4-pixel border is left unrestored (the kernel's taps reach ±3, and Lumen's
  policy at the true frame border is not yet proven). 4 px of 4160x3120.
* Lane 5 of the `r9` struct (`0.79767489`, identical across all cameras) is still
  unidentified. Lanes 14–15 are `(0.34566918, 0.35849619)` — the 28mm-proven
  Phoenix fallback `scene_xy`, i.e. a second, different white point in the same
  struct; unused by this kernel.
