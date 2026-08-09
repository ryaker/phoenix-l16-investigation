# Parity Blockers

This file lists the unknowns that still block an independent application from
reading an LRI, computing the fully merged image without Lumen code/binaries,
and writing a correctly tagged format readable by modern photo software.

## Rule

If a missing fact could plausibly cause:

- an unreadable or incorrectly decoded LRI
- ghosting
- trails
- contributor misalignment
- wrong camera participation
- wrong framing or crop behavior
- wrong color, tonal response, denoise, or detail reconstruction
- an incorrectly encoded or tagged output image

then it is a parity blocker.

Public names and diagnostic enum labels are not blockers by themselves. They
become blockers only when the underlying operational meaning is needed to
compute or encode the image.

## Current Status (TRUTH 3.0.349)

TRUTH `3.0.349` closes the mechanism behind stock-Lumen index-5 repeat
variation. Executor-parallel G-43 workers perform a non-atomic shared
saturating-u16 payload RMW; same-address/multi-thread writes are observed at
all four canonical focals and the Unit-2 index-5 object has nine live
overlapping workers. A Unit-2 parent-gate repeat also exposes pre-G42
executor-order sensitivity. Forcing generic executor `0x2d30` into its
installed ascending fallback produces exact repeated maps across Unit-1 wide,
Unit-1 tele, and Unit-2 tele and stabilizes the captured pre-G42 operands.
This removes nondeterminism as an implementation-localization ambiguity: use
deterministic reference captures for the next Lumen/Phoenix level-0 operand,
G-42, and G-43 comparisons. It does not reopen any selected-profile formula
claim.

TRUTH `3.0.348` replaces the missing historical Unit-2 tele band statistic
with two fresh Lumen full-map captures and one same-generation Phoenix render.
All `4,322,500` Lumen low/high words replay the admitted range formula, and
Phoenix's dumped bands replay the same formula on its own prior indices. The
parity divergence is already present in level 0's complete lookup before range
propagation, so current range construction is a downstream amplifier, not the
causal origin. This does not reopen `CLM-STEREO-001`; it redirects
implementation validation to level-0 operands, G-42, and G-43.

TRUTH `3.0.347` removes the remaining mode-0 all-patch reconstruction caveat.
All 4,489 clean-room patches now reproduce every one of the `272,484`
pre-combine overlap words exactly, including invalid-source spatial bypass,
fixed float32 overlap constants/order, and independently clipped
auxiliary/target edge statistics. This adds no selected-profile blocker; it
removes an implementation-validation uncertainty inside the already proven
claim.

TRUTH `3.0.346` corrects the selected mode-0 MonoFusion patch arithmetic:
public-vignetting auxiliary mean rather than target mean, target-weighted
Wiener update `w*T+(1-w)*S`, row-before-column inverse stages, signed-int16
low-word flow packing, and exact terminal target/overlap combine. One live
patch, the complete public auxiliary map, all packed flow components, and all
terminal tile cells replay bit-for-bit. Its then-remaining all-patch
overlap-tile reconstruction is closed by TRUTH `3.0.347`.

TRUTH `3.0.345` closes the immediate mode-0 MonoFusion scalar-to-RGB wrapper:
the installed path replaces the AR1335 response coordinate in an exact
response/opponent basis and inverse, using public sensor type and public
black/white levels. Two-body exact-`28mm` runtime replays every checked word;
prior route proof supplies `28/35mm` applicability and `70/150mm` bypass.
This does not change the zero selected-profile blocker count, but it forbids
scalar RGB-ratio reinjection as a parity implementation.

TRUTH `3.0.340` closes the selected-profile blocker reopened at `3.0.339`.
Exact installed/public replay now covers camera-ID-keyed public cross-talk
matrices, image-derived amount selection, installed A/B/C tables, generated
IR, public-AWB matrix preparation, coordinate interpolation, Bayer-neighbor
and boundary behavior, limiter, and output blend. Distinct Unit-1/Unit-2
exact-`28mm` packets replay bit-for-bit, a Unit-1 movable camera supplies a
public-key discriminator, and prior complete Unit-1 four-focal plus
exact-`70mm` Unit-2 runs supply liveness and demosaic custody.
TRUTH `3.0.341` additionally binds sensor type, color-matrix variant presence,
camera group, and scene CCT to their public LRI origins on both bodies.
TRUTH `3.0.342` closes a portable exact mapping for the current-reference
unrefined SSE reciprocal primitive, removing exact division as an implementation
substitute across the admitted demosaic/denoise/MonoFusion/IRAMP formulas.

No selected profile-3 supported-input parity blocker is currently admitted.
The clean-room investigation remains active for end-to-end reconstruction
depth, unsupported/alternate routes, implementation alignment, and validation;
those scopes do not reopen a formula already admitted at its stated boundary.

| Active claim | Blocking unknown |
|---|---|
| - | None |

TRUTH `3.0.338` closed the previously unstated mode-0 MonoFusion operand-
pyramid producer without changing the then-zero selected-profile blocker count.
Both public-LRI-derived level-0 operands and every FastCollapse level through
level 4 replay bit-exactly across two physical exact-`28mm` bodies. The
corrected A2 join includes the admitted full-frame hot-pixel stage; the exact
`2/4/4/4` schedule, kernels, phases, edge clamp, float32 order, and `uint16`
conversion are now admitted. Prior route proof supplies profile-3 `28/35mm`
applicability and `70/150mm` no-MonoFusion exclusion. Captured pyramids are no
longer a permissible clean-room starting point.

TRUTH `3.0.337` closed two additional selected color-camera public-origin
boundaries without changing the then-zero selected-profile blocker count. Complete
captured tiles replay exact public sensor-level normalization and public
`17x13` vignetting for two-body A1 plus a four-model Unit-1 movable camera.
The numerical scope is exact-`28mm`; prior four-focal receipts supply route
incidence. A new end-to-end A1/A3/A4/A5 RAW-to-color replay, all camera keys,
alternate lens modes, and body/firmware attribution are not claimed.

TRUTH `3.0.335` closes the selected default hot-pixel full-frame edge policy.
Installed helper `0x178b0` constructs a six-pixel parity-preserving upper-
median halo from available same-CFA `3x3` lattice samples. Combined with the
admitted rank/LUT/isolation worker, complete runtime replays match all
`12,979,200` output words for Unit-1 exact-`28mm`, Unit-2 exact-`28mm`, and
Unit-1 canonical-`35mm`, spanning three distinct LUT payloads and correction
populations. Prior four-focal liveness supplies selected tele applicability;
canonical tele does not construct MonoFusion. `CLM-STEREO-001` is restored to
`PROVEN` / `SPEC_READY` for the selected profile-3 route.

TRUTH `3.0.334` closes the parallel MonoFusion A1 flow-reference
public-origin reconciliation. Exact public-LRI replay matches every level-0
sample on both physical exact-28mm bodies, and prior route proof supplies the
canonical `28mm`/`35mm` mode-0 versus `70mm`/`150mm` no-MonoFusion scope. It
left the then-active A2 default hot-pixel outer-edge blocker addressed above.

TRUTH `3.0.333` reopened only the selected default hot-pixel full-frame edge
policy. Complete Unit-1 exact-28mm A2 capture refutes two serial residual
filters and a frame-constant isolation selector. One residual per rolling
source row plus selector `(y&1) XOR (phase_x XOR phase_y)` replays all
`12,979,082` samples in the eight-pixel-inset interior exactly. The remaining
118 differences are confined to the global outer eight-pixel frame, where the
installed clipped-region and initialized-ring boundary policy was not yet
bit-closed. TRUTH `3.0.335` supersedes that residual.

TRUTH `3.0.331` closes selected pattern-2 Skip-mask consumption. Nonzero mask
pixels use an all-zero G-42 unary vector but still execute all eight SGM paths,
receive a populated per-pixel Cost-volume record, and use the ordinary
first-minimum hypothesis selector. They are not holes filled by the later
guided 2x upsample. Installed proof plus exact-focal two-body `28mm` branch
and completed-record captures satisfy the admission standard; existing
Unit-1 four-focal receipts supply selected-path liveness.

TRUTH `3.0.330` closes the exact G-42 representation entering G-43. The raw
summed `uint16` cost is multiplied in binary32 by `(1/27)/source_count` and
truncated toward zero in place; selected source count `4` gives exact factor
`0.0092592593282461166f`. There is no per-pixel band-min pedestal. Installed
proof plus exact-focal two-body `28mm` raw-to-recurrence custody satisfy the
admission standard, with prior Unit-1 four-focal G-42/G-43 liveness.

TRUTH `3.0.329` records and closes the next implementation-reconciliation
gap: `0x298ff0` uses a Skip-mask-aware asymmetric 4x4 min/max pool with
offsets `{-1,0,1,2}` on each axis, not the builder's symmetric radius-2
all-pixels fit. Exact installed policy plus the scoped runtime matrix satisfy
the admission standard, so this item does not remain active.

TRUTH `3.0.328` records and closes the implementation-reconciliation gap in
coarse index-5 projection. The selected mode-8 route keeps all source Images
and composed projection records in the fixed `2080x1560` domain; it maps each
coarse reference cell center into that domain using exact steps
`{32,16,8,4,2,1}`. The fitted `H_level=D*H*D^-1` substitute is refuted. This
was a pixel-changing implementation gap, but it is not left active because the
installed formula and complete two-body/four-focal runtime matrix satisfy the
admission standard in the same campaign.

The Final Truth Completion Checklist items are not active blockers:

| Checklist group | Canonical disposition |
|---|---|
| A1-A5 | Exact wavelet, abs-mask, sharpen, bilateral, and NLM constants admitted. |
| B1-B4 | CalibStage `factory/current` and transferred K/R/t slices, Cost-volume operand labels, CCM A/D65/F11 selection, and `lt::CalibDataProcessor` identity admitted. |
| C1-C5 | Terminal whole-State warp feed, SGM tuning, row/pixel/file policy, C6 terminal exclusion, and wide `0x218bc4` path divergence admitted at their stated zoom scopes. |
| D1 | Exact-focal Unit-2 `28mm` constructor-runtime join admitted. |
| E1 | Laplacian clarity transfer, construction, level rule, tonal shaping, and defaults admitted; runtime liveness is Unit-1 `28mm` scope. |

These closures do not silently promote formerly `PARTIAL` claims. The
distributed pre-fusion mechanism and final contributor acceptance/rejection
predicate were explicitly promoted by their later admitted proofs. The parent
`CLM-PREFUSION-001` identity/topology row and `CLM-ZOOM-002` tele-firing row
are likewise explicitly reconciled. Historical detail below may still use
older open-language and is not authoritative over the ledger.

TRUTH `3.0.305` identifies payload slot 15 as conditional
linear-ProPhoto/D50 materialization rather than a photographic look curve.
TRUTH `3.0.306` closes tested profile-3 incidence: the complete Unit-1 quartet
and targeted Unit-2 wide/tele controls select only its exact-copy branch.
Generic unequal-selector formulas remain outside the admitted route, not a
current blocker for it.

TRUTH `3.0.308` proves that initial installed-editor pyramid construction uses
the same profile-3 calibrated IRAMP topology at all four canonical focal
tiers. One scoped Unit-1 28mm brush edit rerenders prepared state without a
fresh IRAMP/stereo/calibration pass. Editor/export pixel identity and general
edit formulas remain reference-only compatibility questions, not blockers for
the base profile-3 LRI-to-modern-image objective.

TRUTH `3.0.309` joins two recovered standalone calibration packages to all
five matching-body calibration payloads in 81 new complete photographs,
expands the public firing-set census to 9,323 complete photographs with no
third topology, and establishes that package-only zoom/HotPixelMap artifacts
are not additional admitted inputs to the selected photograph route. This
adds provenance and scope guards; it does not create or close a pixel formula
blocker.

TRUTH `3.0.311` closes tested 28mm editor-pyramid geometry, the immediate
default level-4 route through exact `lt::PipelineCache` and the per-level Color
pipeline, correct type-13 queue-record custody, and exact installed conditional
BGRA/RGBA byte packing. The exact seven-callback editor/export mapping is
isolated by byte-equal before/after joins; display-specific callback formulas
and alternate DOF/mode behavior remain reference-only compatibility work, not
base profile-3 output blockers.

TRUTH `3.0.312` clean-room replays the selected ACRE core over a complete
`256x256` worker tile byte for byte, admits its exact 1025-value LUT and live
EV, and proves lens/contrast exact no-op incidence for the tested request.
At that checkpoint the following linear-ProPhoto/D50-to-sRGB/D65 conversion,
display index-10 color correction, EV/LUT public origins, and alternate
DOF/mode routes remained reference-only compatibility work. Version `3.0.313`
closes the selected conversion below.

TRUTH `3.0.313` closes the selected suffix through runtime-proved worker
`0xabf20`, matrix branch `0xac600`, and byte-exact clean-room replay of the
complete linear-ProPhoto/D50-to-sRGB/D65 converted tile. Remaining editor work
at that checkpoint was display index-10 color correction, EV/LUT public
origins, and alternate DOF/mode behavior.

TRUTH `3.0.314` closes the selected EV/LUT origins through exact public
capture-normalization arithmetic plus the installed
`tone_mapping.type=light_v1 -> enum 4 -> curve index 1 -> 0x5e41b4` chain.
TRUTH `3.0.315` then closes selected display index-10 color correction from
two-body public `macbeth_data` through the exact optimizer, endpoint selection,
matrix/HSV-map application, and a zero-byte-difference full-image replay at
Unit-1 `28mm` default level 4. Remaining editor work is alternate DOF/mode and
other untested control/focal/level behavior; none is a base profile-3 output
blocker.

TRUTH `3.0.316` closes public mode-1 DOF activation, exact local cache
selection, and one final packed-buffer effect at Unit-1 `28mm`. TRUTH
`3.0.317` additionally closes the installed optical tuple, public
`sensor_data_surface.data_scale` pitch ancestry, exact focus-range formula,
and exact SSE tile-radius bucket formula. TRUTH `3.0.318` closes both installed
vec4/scalar circle-filter specializations. Layered/occlusion composition, modes
`2/3/4`, and other bodies/focals remain reference-only and are not base
profile-3 output blockers.

TRUTH `3.0.321` closes the installed mode-1 layered compositor through exact
layer construction/membership, neighbor opacity, native/scaled blur dispatch,
cubic B-spline resampling, and reverse source-over. TRUTH `3.0.322` closes the
public five-value RenderingMode enum and top-level dispatch, complete live
11-key DebugView selector/target census, and default all-zero QuickSelect mask
plus final blend at Unit-1 `28mm`. Exact debug-object formulas/public meanings,
active QuickSelect generation, nonempty secondary-layer and distinct-rectangle
runtime, other bodies/focals, and general edit semantics remain reference-only
and are not base profile-3 output blockers.

TRUTH `3.0.323` closes one active public QuickSelect packet through observed
binary mask and exact level-4 output support. Internal segmentation, other
packet modes/inputs, Boolean meaning, and committed-selection behavior remain
reference-only.

TRUTH `3.0.324` closes exact installed RefocusSlider Rec.601 conversion,
depth-distance mask, and cyan blend, with exhaustive one Unit-1 `28mm`
runtime replay. Other bodies/focals and remaining editor semantics stay
reference-only.

TRUTH `3.0.325` closes the installed RefocusPoint post-DOF strict-range
predicate and red/alpha blend with exhaustive all-inside and mixed-outcome
Unit-1 `28mm` replays. Other bodies/focals and remaining editor semantics stay
reference-only.

## Active Blockers

No claim-ledger parity blocker is currently admitted for the selected
canonical profile-3, structurally complete local-LRI scope. This statement is
scope-bound: unselected compatibility arms and newly demonstrated
image-changing behavior still require their own evidence before admission.

TRUTH `3.0.296` closes `CLM-COMPAT-002`. Both complete `28mm`/tele variants
execute tele primary stereo/range/upsample, C6 clear, five cross-category warp
records, `C1..C5` IRAMP with tele scale, and the public 150mm crop. The complete
`74mm`/wide variant executes MonoFusion mode 0, wide scorer/stereo, no C6
clear, five cross-category warp records, `B1..B5` IRAMP with wide scale, and
its public 35mm-family crop. All complete HDR; the two tele exceptions span
both calibration signatures. One Unit-1 tele render has zero live scorer calls
after family-B selection, retained as scoped no-candidate incidence.

Historical note: TRUTH `3.0.284` reopened this scoped blocker and TRUTH
`3.0.285` left it unchanged while reconciling stale reference-only rows. A
full `9,438`-file public
LightHeader census proves that all `9,242` complete inputs use exactly two
complete firing sets, keyed without exception by public reference camera:
`A1 -> wide` (`6,078`) and `B4 -> tele` (`3,164`). Two complete `28mm` inputs
use the tele set and one complete `74mm` input uses the wide set, and all
three successfully write full profile-3 Radiance HDR. They are supported
inputs, so they cannot remain excluded as generic non-baseline compatibility.
The two 28mm/tele files carry the exact canonical 150mm public crop, while
the 74mm/wide file carries a 35mm-family public crop; focal alone is therefore
not a safe framing selector either.
Installed selector proof now closes candidate scorer-family choice directly
from public reference camera (`0 -> family A`, `8 -> family B`). The remaining
route/crop/warp work described at that version is completed by the TRUTH
`3.0.296` admission above.

Everything after this current-status section and before the exit criteria is
closure history. A sentence there saying that work "remains open" records the
boundary at that evidence stage; it does not override the live blocker count
or reopen a later ledger admission.

TRUTH `3.0.283` closes `CLM-STATE-001` by a 13-verifier operational audit.
The consumed State/CapturedImage/CalibStage/derived-record fields and their
downstream formulas are closed; anonymous padding, numeric labels, and fields
without a demonstrated image consumer are excluded rather than guessed.

`CLM-DENOISE-002` is removed from the blocker table at TRUTH `3.0.274`.
SHA-pinned selected-worker proof and two-body post-store replay close the
radius-2/radius-4 formulas and callback field roles, joined to prior Unit-1
four-focal liveness and store mechanics. This does not assign public names to
internal callback fields or generalize unobserved kernel-size arms.

The selected index-5 Skip-mask predicate leaves `CLM-STEREO-001` at TRUTH
`3.0.275`: installed/static proof, direct Unit-1 `28mm` pattern receipt, exact
task capture, and byte-identical Unit-1 four-focal replay close pattern `2`.
At that version, Guidance lane semantics and disparity-direction convention
remained blocking.

TRUTH `3.0.276` closes the disparity-direction convention with installed
splice proof and all 67 accepted Unit-1 four-focal recurrence packets. The
remaining stereo-policy blocker at that version was exact Guidance component
meaning.

TRUTH `3.0.278` closes Guidance component meaning and live SoftISP
configuration as exact `[R,0.5*(G1+G2),B,1]` under four-focal `collapse2`.
The load-bearing default hot-pixel pre-stage is narrowed through rank-6,
`4*LUT` threshold, marker, and exact isolation-policy proof. TRUTH `3.0.279`
closes the Bayer noise-LUT generator with a 4096-word bit-exact replay. Its
rank-neighborhood coordinates remain the stereo blocker.

TRUTH `3.0.280` recorded a focused-patch two-residual interpretation and
temporarily removed `CLM-STEREO-001` from the blocker table. TRUTH `3.0.333`
supersedes that conclusion with complete-frame runtime proof: the worker forms
one rolling-row rank residual, uses a row-varying isolation selector, and is
exact over the eight-pixel-inset Unit-1 exact-28mm interior. Its global outer
eight-pixel policy and sufficient cross-body/focal validation remain active.

TRUTH `3.0.326` corrects the terminal component identity:
`[R,0.5*(G1+G2),B,1]` is pre-YUV collapse2. Direct custody and
complete scene/two-body plane replay close the subsequent
`StereoISP::ConvertToYUV` stage and final Guidance `[Y,U,V,1]`.

`CLM-INPUT-001` closes raw block location, `RAW_PACKED_10BPP` unpacking, and
Bayer/mono phase across exact-focal representatives from both calibration
bodies. It removes the former head-of-path raw-layout blocker, but not the
post-unpack normalization work.

`CLM-DEMOSAIC-002` closes exact four-phase `DemosaickLightV1` taps, corrected
red/blue-first and green-refined guide ownership, source-only phase clamps,
derived-plane virtual halos, residual guards, supplied-gain use, and
output-channel arithmetic. The corrective admission includes full-frame exact
replay on both physical units at exact-`28mm`.
`CLM-AWB-001` now separately closes the public four-gain origin, dual LRI
container layouts, reciprocal RGB decode, and both live consumers.
`CLM-RESAMPLE-001` closes the exact 64-phase Catmull-Rom table, signed-16.16
phase/index policy, separable stores, boundary clamping, and selected-cache
offset/scale derivation.
`CLM-WARP-004` closes the public Brown-Conrady coefficient order and
center/normalization mapping, public CRA pixel-size radius basis, 30-sample
correction construction, cubic Lagrange interpolation, exact 4096-entry
table, integer-radius consumer, and path-scoped `valid_roi` exclusion.
`CLM-VALIDATION-001` now contains measured four-tier final-output repeat
envelopes, 20 complete camera-scoped undistorted-plane references, and all 16
complete four-focal depth/disparity base artifacts. A `28mm` undistorted-plane
repeat is byte-identical, while four-focal depth-map repeats refute a single
deterministic golden, with especially large tele solution-class changes. It
remains blocking for a sufficiently sampled intermediate-map distribution and
its clean-room acceptance policy.

TRUTH `3.0.282` supersedes that remaining validation paragraph. Ten complete
index-5 index/depth samples per focal establish the focal-specific class and
pair distributions, while a 129,792,000-pixel verifier proves exact
index-to-depth lookup coupling. The validation policy rejects both one tele
golden hash and broad nearest-map acceptance, layering exact map invariants,
deterministic stage checks, and final focal-specific output envelopes.
`CLM-VALIDATION-001` is `PROVEN` / `SPEC_READY` and removed from the blocker
table.
`CLM-OUTPUT-002` now contains the exact canonical RGBE byte writer and
formula-level final placement for every orientation value present in complete
profile-3 inputs. The installed RGB-to-XYZ matrix and independently validated
linear-ProPhoto float-TIFF mapping close the self-describing modern export;
it is no longer a blocker.
`CLM-CORRECTION-001` contains exact public `17x13` crosstalk/vignetting grid
names, two-body byte-exact vignetting-profile construction, and exact
vignetting row sampling. Its former cross-talk exclusion is superseded at
TRUTH `3.0.339`, and TRUTH `3.0.340` closes the selected scalar-true path from
public RAW/matrix inputs through the demosaic-consumed output. Alternate
profiles/specializations remain outside that selected-profile admission.
`CLM-LRI-001` now contains the complete installed `LightHeader` /
`ViewPreferences` / `GPSData` record contract, file-order preference merge,
four-tier live crop/exposure-target formulas, flash/GPS image exclusions, and
a no-unknown-field census of all `9,242` structurally complete local LRIs,
and is no longer a blocker. The `2,906` direct versus `6,336` wrapped
preference split is firmware-era layout, not body causation.

The common MonoFusion mode-1 scalar body used by Renderer profiles `1/2` is
formula-closed at TRUTH `3.0.336`; remaining alternate-profile and GUI/editing
semantics stay tracked by partial `CLM-COMPAT-001` as `REFERENCE_ONLY`. Initial profile-3 GUI pyramid
construction now has a four-focal IRAMP-topology join; one `28mm` brush edit
proves prepared-state reuse only for that tested edit. Exact display packing,
conditional GL byte order, and the immediate tested default level-4
PipelineCache/Color-pipeline route are closed; its exact seven active callbacks
are named and byte-bounded. Selected display index-10 color correction is now
closed at Unit-1 `28mm` default level 4. Public mode-1 DOF activation and one
final-buffer effect are also closed at a scoped Unit-1 `28mm` treatment. The
optical range and tile-radius formulas are closed, and circle filtering,
including its clamped-edge policy, is now exact too. TRUTH `3.0.321` closes
the installed mode-1 layer constructor, neighbor-opacity law, native/scaled
blur dispatch, cubic B-spline resampler, and reverse source-over composition
with scoped Unit-1 `28mm` runtime. TRUTH `3.0.322` additionally closes the
public five-mode enum/dispatch, all eleven live DebugView selector targets,
and the default QuickSelect mask/blend. TRUTH `3.0.323` closes one active public
stroke through binary mask and exact output support. TRUTH `3.0.324` closes
exact RefocusSlider visualization math, and TRUTH `3.0.325` closes the exact
RefocusPoint post-DOF range overlay. TRUTH `3.0.336` closes mode-1's exact
five-tap split, confidence gate, both-axis boundary extension, invalid fallback,
and final scalar blend with scoped two-body runtime. Debug-object formulas/public meanings,
internal QuickSelect segmentation and commit behavior, nonempty
secondary-layer and distinct-rectangle runtime, other bodies/focals, and
untested control/level behavior are not closed.
Supported non-baseline LRI captures
are tracked separately by `CLM-COMPAT-002`.

The sections below are retained as prior merge-campaign closure history and
scope guards.

### Closed: Exact pre-fusion merge/reduction mechanism behind `src1` / `src2`

- Claim ID: `CLM-PREFUSION-002`
- Naming note:
  `N-to-1 reducer` is a search shorthand, not a proof that Lumen must contain one tidy reducer closure. The real mechanism may be distributed across scoring, selection, warp, accumulation, and acceptance stages.
- Why it mattered:
  parity cannot be frozen while the upstream anchor-group behavior behind `src1` / `src2` is still unresolved.
- What is already known:
  visible `src1` is now exact tier-anchor `ReferenceImageCache`; exact visible-`src2` generated-image semantics remain partial.
  The canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR quartet all hit the visible `src1` wrapper (`0x3ecc10`), visible `src2` wrapper (`0x3ecd80`), contributor wrapper (`0x3eced0`), and IRAMP accumulator (`0x369fa1`) surfaces.
  The first visible installed-bundle wrapper bodies at `0x3ecc10` and `0x3ecd80` do not by themselves close the reducer blocker.
  Four-zoom runtime proof now identifies `PipelineCache+0x8` as a five-entry packed `(int32 width, int32 height)` level-vector header, not an image/composite pointer. `28mm` / `35mm` use entry `0 = 10432x7824`; `70mm` / `150mm` use entry `0 = 8896x6672`; all four use entry `1 = 4160x3120`, and the visible `src1` / `src2` wrapper dimension fields are populated from that entry `1`.
  The post-wrapper `initResAmp` branch at `0x3eb3c0` now bounds `PipelineCache+0x258` and `PipelineCache+0x270` as per-key record/wrapper construction, not exposed reducer math.
  The visible `PipelineCache+0x270` per-key wrapper read path is single-payload ROI/tile processing plus square-root normalization, not exposed reducer math.
  The visible `src1` read path is map/tree lookup, checked single-source level/ROI tile read, and one-image square-root normalization, not exposed reducer math.
  The visible `src1` payload returned by `0x3e0af0` is now provenance-bound to `PipelineCache+0x170`, the caller's `+0x6a8/+0x6b0` shared-ptr-like pair, the `0x3dfcc0` map/tree builder, and the `0x3e2db0 -> 0x3e27a0` `0x490`-byte payload constructor; this still does not expose reducer math.
  The visible `src1` payload constructor path is now runtime-confirmed across the corrected canonical quartet: `0x3dfcc0 -> 0x3e2db0 -> 0x3e27a0` is live, the constructor key is `0` at `28mm` / `35mm` and `8` at `70mm` / `150mm`, the constructor receives the same four-entry level vector `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`, and the success packet produces the same `0x490` / `0x65f140` / `0x65f388` visible payload family; this is constructor/provenance evidence, not payload-composition closure.
  The visible `src1` lookup key is now runtime-bounded across the corrected canonical quartet: key `0` at `28mm` / `35mm`, and key `8` at `70mm` / `150mm`; this is a lookup-key fact, not payload-composition closure.
  The visible `src1` payload family is now runtime-bounded across the corrected canonical quartet: visible `src1` lookups return `0x490` payloads with vtable address point `0x65f140`, while adjacent direct contributor lookups return `0x1f0` payloads with vtable address point `0x65f490`; this proves the two paths are different payload families, not what the `src1` payload semantically contains.
  SHA-pinned RTTI/control-block proof now closes those exact identities: owner `+0x6a8/+0x6b0` is `shared_ptr<lt::ImageCaches>`, vtable `0x65f140` is `lt::ReferenceImageCache`, vtable `0x65f490` is `lt::SourceImageCache`, and the visible wrappers are `PipelineCache::initResAmp::$_1/$_2`. Joined to the admitted keys, visible `src1` is A1 `ReferenceImageCache` at `28mm` / `35mm` and B4 `ReferenceImageCache` at `70mm` / `150mm`; direct source caches are B1..B5 or C1..C5. Older "composite-ish src1" shorthand is superseded.
  Installed constructor/accessor proof also closes visible `src1` to exactly one public `CapturedImage::Camera` origin and one `RawImageFactory` lookup key: A1/key `0` wide, B4/key `8` tele. The remaining N-to-1 search boundary is outside `ReferenceImageCache` construction, in the outer IRAMP policy over reference, generated-secondary, and five direct-source inputs.
  SHA-pinned IRAMP custody plus four-focal complete-render probes now names that outer division of labor: `src1` is the coarse byte registration guide and grid-bounds operand, `src2` is the full-vector reference/baseline patch, and each direct source/warp pair is a candidate. Both `0x36cde0` score and `0x36e530` scale-normalized inverse reconstruction have complete clean-room formulas, exhaustive installed-body census closes local candidate/sentinel policy with no score threshold, and a return-only score intervention closes final-file consequence. Installed selector proof and the profile matrix formally exclude MonoFusion mode `1` from canonical profile 3: wide uses mode `0`, tele constructs no MonoFusion.
  Follow-up SHA-pinned RTTI plus admitted four-focal executor packets now name visible `src2` as `PipelineCache::initResAmp::$_2 -> PipelineCache::processLevel1 -> ImageWarpClamped<ResamplerFilter=2, vec4x32f>`, callback `0x65f7e8/+0x30 = 0x3ed2e0`. Direct contributors use distinct `initResAmp::$_3` at `0x65f768/+0x30 = 0x3eced0`. The outer worker resamples one generated descriptor; its tested tier-dependent ancestry is now closed below.
  A two-body/two-tier runtime join closes the target camera behind that descriptor: `FusionCacheBayer::0x406a10` derives and looks up active A1/key `0` at wide and B4/key `8` at tele as exact `lt::CapturedImage` objects. Pinned installed-class proof plus complete Unit-1 four-focal and Unit-2 28mm/70mm packets identify optional `FusionCacheBayer+0x20` as `lt::MonoFusion`: wide targets A1 and selects only A2/key `1`; tele has zero MonoFusion activity and uses direct B4. Follow-up static/LRI plus Unit-1 28mm/35mm and Unit-2 28mm runtime decodes production-profile mode `0` public A1/A2 exposure/analog source normalization, installed type-3 VST origins, initializer scaling, normalized 5/3 lifting with exact boundaries/packing, exact coefficient weights, patch-noise/Wiener math, half-Hann overlap-add, final scalar blend, and secondary-map callback. Corrective constructor proof refutes the different public type-2 LRI VST rows as coefficient custody. The later profile matrix excludes mode `1` from canonical profile `3`.
  The payload-internal secondary callable at `+0x60` is now bounded too: visible `src1` payloads use address point `0x65f388` with substantive slot `0x3e4a80`, while direct contributor payloads use address point `0x65f4d8` with substantive slot `0x3e78d0`; this proves another structural split, not payload-composition closure.
  The visible `src1` secondary callable is now runtime-confirmed live across the corrected canonical quartet: first captured packets hit `0x3e4a80`, reached it from the already-bounded `0x3d01b0` tile-read / `0x5440` executor path through callback worker `0x3d47d0`, and passed the same `0x490` payload to `0x3e2e90` at `0x3e4b09`; this proves live handoff for the first captured tile, not payload-composition closure.
  The first captured worker/projection-record path under that visible `src1` handoff is now runtime-bounded across the corrected canonical quartet: packets reach worker `0x3e4c50` through `0x3e4b0e <- 0x3d4842`, worker callback fields contain source image / output image / default vector / projection record / weight table, and the first captured projection record uses payload-internal index `0` to load `payload+0x150` from visible-payload field `+0x170`, with callable address point `0x65f188` and slot `+0x30 = 0x3e42e0`; this proves topology for the first captured worker packet, not semantic `src1` contents or camera identity.
  The now-proven `0x3e42e0` callable target is statically decoded as a two-float coordinate transform over payload fields `+0xf8/+0xfc`, `+0x100`, and `+0x118..+0x140`; it is not a reducer, and its public field semantics / LRI origins remain unproven.
  The `0x3e42e0` field-pack producer is now statically bounded: `0x3e27a0` calls dispatcher `0x3f6170`, which routes to same-category `0x3f6200` or cross-category `0x3f6940`; both branches converge on `0x145580` / `0x144f50`, and `0x144a70` forces the radius table consumed by `0x3e42e0` to `4096` floats. Four-zoom runtime proof now also bounds this dispatcher boundary under complete bridge HDR runs with `.lris` auto-loading disabled: observed keys are `0,5..9` at `28mm` / `35mm` and `8,10..14` at `70mm` / `150mm`; tele key `15` is not observed at this boundary. This is field-origin topology and tested-route exclusion, not `src1` semantic-content closure or C6 routing closure.
  The direct `0xe59a4 -> 0xf2770` constructor callsite is now runtime-bounded under complete four-zoom bridge HDR runs: wide seeds construct keys `0,4,6,8,9,1,2,3,5,7`; tele seeds construct keys `6,8,9,14,5,7,11,10,12,13,15`; all captured items are initially active at item `+0x30 = 1`; input `+0x30` equals output item `+0x60`; and input `+0x28/+0x18` carries the same two-int pair later observed at item `+0x58/+0x5c`. Tele key `15` / C6 is therefore constructed active in this path.
  SHA-pinned schema/copy proof plus all `42` admitted constructor events now names that pair as public `CameraModule.sensor_bayer_red_override.{x,y}`, with A2/key `1` the unique wide `(-1,-1)` override and C6/key `15` the unique tele `(-1,-1)` override. Exact-focal Unit-2 public carriers preserve the same pattern; selector purpose and downstream policy remain open.
  Hardware write-watchpoint proof now shows tele key `15` / C6 later changes from item `+0x30 = 1` to `0` at writer `libcp+0x3c90a5` inside body `0x3c8f90` in both canonical tele seeds. Static inspection of that body shows the local gate clears key `15` when the grouped context `+0x44` value is not group ordinal `2`.
  A focused 24-site direct `0xf2720` callsite census under complete `70mm` and `150mm` bridge HDR runs now shows identical key-15 observations at both tele seeds: active key-list helper hits at `0x1bdbab` / `0x1bdbdd`, active mutation-body hits at `0x3c9043` / `0x3c9098`, and later inactive key-15 hits at `0x3b2143`, `0x402df7`, and `0x40d219`. Follow-up mutation-identity proof ties those active helper/mutation observations, the `0x3c90a5` store, immediate inactive `0x3c90a9` state, and later inactive `0x3b2143` observation to the same tracked key-15 item pointer per tele run; helper `0x1bdb60` itself is key-list construction bookkeeping. A remaining-direct 34-site census covers the rest of the static direct `call 0xf2720` inventory and finds additional active key-15 observations only at constructor-adjacent key/container/tree materialization sites `0xe327e`, `0xe32f3`, `0xe4063`, `0xe5fd9`, and `0xe6020`, plus inactive key-15 observations at shared-object lookup site `0xe6be0`. Together, the focused and remaining-direct proofs cover all 58 static direct `call 0xf2720` sites under the canonical tele bridge HDR path. A same-byte post-mutation read/write watchpoint proof then observes 18 later stops per canonical tele render on the tracked key-15 `item+0x30` byte; every stop still sees `0`, and the stopped libcp VAs include active-byte gates outside the direct `0xf2720` inventory. A selected-field watch further bounds watched `+0x58..+0x5f`, `+0x60..+0x67`, and `+0x100..+0x107` ranges, including pre-output `+0x60` and `+0x64` reads and cleanup-only stops for the watched pair and type/adjoining ranges. This proves direct-key-query/helper census coverage, same-byte inactive state at observed later byte consumers, and selected-field custody, not image-buffer contribution, terminal filtering, untested-field/alias absence, or all alternate-route absence.
  The direct payload candidate loop immediately upstream of `0x3e05f5 -> 0x3f6170` is now runtime-bounded under the same complete bridge HDR / no-auto-LRIS scope: it visits keys `0..9` at `28mm` / `35mm`, all with `object+0x30 = 1`; it visits keys `5..15` at `70mm` / `150mm`; tele key `15` / C6 has post-mutation `object+0x30 = 0` and skips before active-pass, class-compare, cross-category, and dispatcher-call sites. This proves one tested C6 filter point, not global C6 non-use or alternate-route closure.
  The stereo-side keyed-record loop inside the `0x3f2c40` constructor branch is now runtime-bounded under the same complete bridge HDR / no-auto-LRIS scope: it visits keys `0..9` at `28mm` / `35mm`, all with `object+0x30 = 1`; it visits keys `5..15` at `70mm` / `150mm`; tele key `15` / C6 has post-mutation `object+0x30 = 0` and skips before the post-gate path and before both tested `0xf2720` getter callsites at `0x3f30ca` and `0x3f3104`. This proves a second tested C6 filter point, not global C6 non-use or alternate-route closure.
  The visible `src1` worker source-image producer topology is now statically bounded: keyed helpers `0x1bdc80` / `0x1be750`, vector builder/updater `0x1be270`, ROI/source validator `0x31abd0`, wrappers `0x31af30` / `0x31acf0`, lower producers `0x33ede0` / `0x33f480`, and shared per-source iterator `0x33f180` participate in producing the source-image local later handed to worker callback field `+0x08`. Gated four-zoom runtime proof now identifies the first captured visible-`src1` descendant branch as `0x3e3279 -> 0x31af30 -> 0x33ede0 -> 0x33f180`, reaching virtual site `0x33f3e8` with vtable address point `0x65b3c8` and slot `+0x30 = 0x341770`; static inspection bounds `0x341770` to per-source region-adapter / record-update work, not reducer closure. Installed-bundle proof also bounds `0x341770` helper `0x2e8680` to one-source Bayer/RAW region-helper work with callback vtable `0x659fc0` and substantive slot `0x2e8cc0`; this is still region/source preparation, not merge/reducer closure.
  Four-zoom runtime proof now bounds the keyed-helper/vector-builder boundary under complete bridge HDR runs with `.lris` auto-loading disabled: `0x1bdc80` and count site `0x1bdcfb` are live, every summarized invocation saw `0xe78e0` count `1`, while `0x1be750`, the helper lazy callsites into `0x1be270`, and direct builder sites `0x1be270` / `0x1be291` / `0x1be2fb` / `0x1be306` have zero hits under the canonical quartet. Tele helper keys observed on this boundary are `5..14`, with no key `15`.
  Follow-up gated runtime census expands the lower producer evidence beyond the first captured target: after the first visible-`src1` `0x3e4b09` gate, complete bridge HDR runs observe `0x3e3279 -> 0x31af30` at all four zooms, observe lower virtual sites `0x33f3e8` and `0x33f94f` at all four zooms, and observe `0x33ffd4` at `28mm` / `35mm` with zero `0x33ffd4` hits at `70mm` / `150mm` under the same gated runs. The nonzero virtual-site counts hit the probe's `512` cap, so they are lower bounds and target-family lists are capped-window observations, not exhaustive full-render totals; this still proves dispatch breadth, not semantic `src1` contents or reducer closure.
  Installed-bundle static classification now bounds the inspected visible bodies from that capped lower target-family set to thunk / descriptor / region / materialization / cache / executor surfaces rather than reducer closure or final contributor acceptance/rejection. Follow-up runtime/static proof binds the two prior indirect-call gaps under the first-visible-`src1` gate: `0x342d99` resolves `0x65b948/+0x30 = 0x342b80 -> 0x2eb560`, and `0x3449f0` resolves `0x65c798/+0x30 = 0x345920 -> 0x2f53d0` across the canonical quartet.
  A further gated runtime/static proof bounds the immediate `0x2f53d0` helper chain: `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`, `0x3066d0`, and postbranch `0xab590` are live in capped windows across the canonical quartet, while `0x3048b0` has zero hits under accepted gated probes; static inspection bounds the chain to validation, descriptor/vector setup, bilateral-kernel-size dispatch, callback-object dispatch through `0x5440`, and one row-executor dispatch through `0x5670`.
  Follow-up installed-bundle static classification bounds those executor callback bodies to local descriptor transform / filtering / interpolation / normalization / accumulation surfaces; this is not reducer closure. Follow-up runtime proof now bounds the selected `0x2f6420` callback arm under that same first-visible-`src1` gate: complete accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs select `0x2fb320` at `0x2f67e2 -> 0x5440`, while the hypothesis-relevant `0x2f78e0` arm and normalize sites `0x2f8584`, `0x2f859f`, and `0x2f85a5` have zero hits under that tested route; this narrows the live helper path, not semantic reducer closure or global `0x2f78e0` absence. Follow-up runtime worker proof bounds the selected `0x2fb320` body itself as readable same-shaped descriptor-like fields `+0x08/+0x10/+0x18`, a `vec4` coefficient pointer at `+0x20`, and approximate reciprocal-normalized weighted `vec4` stores at `0x2fbf05`; this is local descriptor/filter/store mechanics, not reducer closure.
  The visible `src2` hot path is runtime-bounded across the corrected canonical quartet to a tiered `PipelineCache+0x1e0` resample-state object; outer worker `0x3ed2e0` resamples one generated descriptor. Its producer splits to A1/A2 `lt::MonoFusion` wide versus direct B4 tele. Production-profile mode `0` generation is formula-bounded through public A1/A2 exposure/analog source normalization, installed type-3 VST constants, normalized 5/3 coefficient Wiener fusion with exact boundaries/packing, overlap-add, final scalar blend, and the secondary-map callback. Reachable compatibility mode `1` is formally outside canonical profile `3`.
  The first visible payload runtime surfaces beneath that constructor are also bounded away from closure: `0x3e53a0` / `0x3e54c0` are destructors, `0x3d0120` / `0x3e55f0` are callable-slot helpers, `0x3e2dc0` / `0x40b370` / `0x40b330` are setup/config work, `0x3e2e90` / `0x3e3f90` are single-level ROI/process helpers, and the deeper `0x3e2e90` worker at `0x3e4c50` is a single-source projection / 4x4 SIMD resampling worker.
  The owner cache-selection layer is also bounded away from closure: `+0x6a8/+0x6b0` feeds the `+0x688/+0x690` construction through `0x3eaf00 -> 0x3ea7d0`, `0x3b0740` selects `owner+0x688` or `owner+0x6b8`, and `0x3d0650` dispatches one selected cache through level/ROI read and rescale work rather than exposed merge/reduction math.
  The constructor-side owner `+0xf0` callable-install custody edge is now bounded too: `0x3ea980 -> 0x3d0120` installs stack callable address point `0x65f5e0` into target inline storage, and installed `0x65f5e0/+0x30 = 0x3ec960`; complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs prove that install state and then reach the already-bounded owner `+0xf0` sink body. This is custody, not reducer closure or final output semantics.
  The owner alternate-cache/helper setup surface is also bounded away from closure: optional `+0x698/+0x6a0` is constructed through `0x3d8b70 -> 0x3d8780` from `+0x6a8` and `+0x678`, and `+0x6b8/+0x6c0` is constructed through `0x3f06f0 -> 0x3f04d0` from `+0x688`, `+0x698`, and a `0x18`-byte state block.
  The visible `+0x678/+0x680` constructor and immediate runtime surfaces are now bounded further: `0x3f2c40` builds keyed records, seeds six descriptor/layer entries, constructs `this+0x280`, and allocates bitset storage; `0x3f75e0`, `0x3f7a40`, `0x3f7b20`, `0x3f7c00`, and `0x3f7ec0` are stop/cleanup, level-gate, callable-slot, byte-count, and record/buffer-materialization surfaces.
  The selected `+0x40` and `+0x90` virtual targets reached from `0x267e80`, `0x267fb0`, `0x268480`, and `0x2684a0` are now bounded as setters/accessors; `0x3f8b30` is now bounded as a consumer/writer of `0x3f7ec0` materialized record/buffer output.
  The located `StereoLayer<false>::runPass(int)` action body is now bounded too: `0x276790` dispatches on `layer+0xc`; both worker bodies route through `0x275630` into `0x2730c0` / `0x2732f0`; `0x275630` is a per-tile state builder; and the canonical four-zoom bridge HDR quartet all hit `0x276790 -> 0x276860 -> 0x275630 -> 0x2732f0` with `layer+0xc == 8`. Under those same tested full renders, `0x277e70` and `0x2730c0` had zero hits. These are scoped runtime facts and do not prove those addresses are dead code.
  The sibling `StereoLayer<false>::compute()` lambda surface is now bounded as installed table `0x667c28`, operator wrapper `0x274b10`, and worker `0x2727f0`; static inspection shows it shares the `0x275630` / `0x2730c0` / `0x2732f0` projection-cost family, while complete no-auto-LRIS bridge HDR probes across `28mm`, `35mm`, `70mm`, and `150mm` record zero hits for that compute surface and adjacent setup helpers `0x272100` / `0x272640` under the tested path. This is a scoped exclusion, not dead-code proof or reducer closure.
  The high-address callers `0x42cb5d -> 0x3f6170`, `0x42cbc2 -> 0x3f7040`, and `0x42cc5a -> 0x3e55f0` are now classified as part of a `HigherWarpDebug::renderDebugView` local callback surface; complete no-auto-LRIS bridge HDR probes across `28mm`, `35mm`, `70mm`, and `150mm` record zero hits for the debug-view entry/callsite/callback sites while live controls at `0x3e05f5` and `0x3eb72d` hit five times per tier. This is a scoped exclusion, not global dead-code proof and not a debug-only classification for the shared helpers.
  The sampled prefusion callable gate is bounded as a predicate/exclusion surface: static proof shows `state+0x220 = state+0x200` with constructor vtable `0x6673f0` and false-return slot `0x230220`; four-zoom bridge HDR runtime samples reached live inline callable vtable `0x66b0f0` and false-return slot `0x230640`.
  The upstream `CalibDataProcessor::State ()` runner family is now runtime-live rather than static-only: the corrected body list is `0x229df0`, `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80`, `0x22bdf0`, `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, and `0x22e1d0`; all thirteen hit under complete accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders with full-render count pattern `(1,1,4,4,4,1,1,1,5,5,5,5,1)`; this is entry-liveness and caller-context proof, not public State semantics or reducer closure. `0x247390` is refuted as a State body and belongs to an adjacent `SparseLNR::markInliers(..., void(int,int,int))` callback table.
  Installed-bundle static proof now further bounds the terminal corrected State body `0x22e1d0` as keyed vector/tree/object-lookup/helper dispatch over per-key records, returning State value `9`, and bounds `0x22f0f0` as the shared dispatcher that stores returned State values at `r14+0x6c` and can notify a callback at `r14+0xe0`; this narrows the State-machine branch but still does not expose direct reducer closure or public State semantics.
  Follow-up no-auto-LRIS runtime proof now bounds the ordered State-return skeleton at that dispatcher path: all four canonical bridge HDR runs record `38` paired `0x22f3f6` / `0x22f3ff` calls, exit cleanly with `10432x7824` HDR output, and share the identical reference-group return sequence `2,3,3,3,3,6,6,6,6,4,4,4,4,7,8,9` followed by higher-group return sequence `1,1,1,1,1,3,3,3,3,3,6,6,6,6,6,5,5,5,5,5,8,9` when grouped by runtime order. This removes runtime return ordering as an unknown for the tested dispatcher path; public State meanings, image effect, source contribution, reducer closure, and final acceptance/rejection remain open.
  Follow-up exact-body static proof now bounds all thirteen State operator bodies as direct-call helper surfaces with zero indirect calls; dispatcher `0x22f0f0` retains the expected indirect dispatch calls. The exact bodies have zero direct calls to the listed known IRAMP/wrapper/owner-route VAs. This moves the search out of the State shells and into helper-family semantics / downstream image effect, not into treating the State bodies themselves as direct known merge entries.
  Follow-up helper static/runtime proof now bounds State helper `0x23c5f0` and selector-gated `0xf33d0`: `0xf33d0` has selector `0` / selector `1` field-copy paths into two destination offset banks, complete no-auto-LRIS four-zoom runs hit `0x23c5f0` exactly four times per render from State bodies `0x22af80` and `0x22e1d0`, and the static `0x23c5f0 -> 0xf33d0` callsite at `0x23d38d` / return `0x23d392` is live with selector `1` across all four focal tiers. Complete installed-writer census plus exact-focal two-body bank watches now map selector `0` to installed `factory` at `CapturedImage+0x180` and selector `1` to installed `current` at `+0x12c`; both start from the same focus-evaluated public factory-calibration packet, and later State/BA updates target current. Complete bank-field and public State meanings, image effect, source contribution, reducer closure, and final acceptance/rejection remain open.
  Follow-up exit-snapshot proof now bounds `0x23c5f0` post-`0xf33d0` local integer coverage and normal-exit local tree shape across complete no-auto-LRIS four-zoom runs. Every tested run pairs four entries with four pre-destroy exits, and the local tree snapshots have no traversal truncation; the captured `rbp-0x4e0` values and node `i32_0x20` sets split wide versus tele as documented in the evidence bundle. This narrows local helper custody, but public field semantics, helper transitive behavior, image effect, reducer closure, and final acceptance/rejection remain open.
  Follow-up `0xf34e0` match proof now shows the objects populated by the live `0x23c5f0 -> 0xf33d0` selector-`1` path are reused internally by `0x23c5f0 -> 0x264440 -> 0x264270 -> 0xf34e0` before helper exit. All four focal tiers match nine prior destination objects and `204` selector-`1` `0xf34e0` calls per run. This narrows transitive helper custody, but post-`0x23c5f0` image effect, source contribution, reducer closure, and final acceptance/rejection remain open.
  The next bounded selector-helper tranche beneath the dispatcher layer is still only integer-index permutation, vector copy, bitset materialization, and bitset-driven record promotion.
  The callback object built after that selector-helper tranche is not a new `CalibDataProcessor::State()` runner; it uses the adjacent `SparseLNR::markInliers` / `0x247390` callback table.
  The candidate block-geometry helper family is coordinate / geometry / active-block state work, not exposed reducer math; follow-up four-zoom runtime proof bounds the admitted `0x25d090` effect as block-owned pair-vector growth plus descriptor-build / geometry-predicate / active-byte gating.
  The visible `0x258fe0` / `0x2598a0` feature-selection lane is feature / pyramid / candidate-record and scaled coordinate-output work, not exposed reducer math.
  The downstream `0x24c320` / `0x24d610` candidate-scoring family is also bounded: under the corrected canonical four-zoom bridge HDR quartet, `28mm` and true-`35mm` reached `0x24c320` and not `0x24d610`, while `70mm` and `150mm` reached `0x24d610` and not `0x24c320`; both entry bodies consume `0x24`-stride candidate records, perform bounds / projection / local SIMD patch scoring, and write `0x2c`-stride result or sentinel records.
  Follow-up four-zoom runtime proof now binds those candidate-scorer output records to the shared `0x2439b0` record-state gate by exact output-vector pointer continuity: `28mm` / `35mm` use family A (`0x667788/+0x30 -> 0x24c2d0 -> 0x24c320`) with output vector at scorer-context `+0x18`, while `70mm` / `150mm` use family B (`0x667808/+0x30 -> 0x24d5c0 -> 0x24d610`) with output vector at scorer-context `+0x28`; every captured family gate call and matched `0x2439b0` entry carries the same vector pointer and record count. This is scorer-output custody, not reducer closure.
  Follow-up four-zoom record-state histogram proof now bounds `0x2439b0` itself as a live record-state gate for those custody-bound scorer-output vectors: admitted `28mm` / `35mm` family-A runs are unchanged at the before/after boundary, while admitted `70mm` / `150mm` family-B runs promote target-2 records from state `3` to state `4` (`19` records at `70mm`, `12` records at `150mm`). Static proof ties the promotion stores to `0x243b2c` for target `1` and `0x243cac` for target `2`; the runtime mutation observed here matches the target-2 store path. Under this exact-vector probe, sampled downstream entries `0x241fd0` and `0x2416d0`, plus sampled store sites `0x241828`, `0x2422a6`, and `0x242306`, did not match the known scorer-output vector. This is boundary behavior, not public state semantics, reducer closure, or final acceptance/rejection.
  Follow-up tele hardware data-watch proof now shows selected records promoted by `0x2439b0` from `(state=3,target=2)` to `(state=4,target=2)` are not terminal bookkeeping under the admitted canonical tele runs: two representative promoted records were watched at `70mm`, two representative promoted records were watched at `150mm`, both runs completed cleanly, the watched fields were read by downstream code, and at least one watched record per tele seed advanced to `(state=5,target=2)` through `0x2416d0` (`0x241d35` store / `0x241d3b` stop at `70mm`; `0x241d64` store / `0x241d6a` stop at `150mm`). This is watched-record downstream-consumer proof, not all-record coverage, public state semantics, downstream image effect, reducer closure, or final acceptance/rejection.
  Follow-up tele selected-index proof now shows promoted target-2 record indices captured at `0x2439b0` later enter concrete `0x2416d0` selected-index vectors in clean canonical `70mm` / `150mm` renders, and the small promoted sets captured by that probe reach `(state=5,target=2)` stores. This is selected-index/state-relabel proof for admitted promoted sets, not public acceptance semantics, downstream image effect, reducer closure, or final acceptance/rejection.
  Follow-up tele later-watch proof now shows watched promoted records that become `(state=5,target=2)` continue downstream into `0x244560` and the already-bounded `0x25d090` candidate block-geometry / active-block helper family under clean canonical `70mm` / `150mm` renders. This is later state/candidate/geometry flow, not downstream image effect, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom block-geometry-effect proof now bounds `0x25d090` as active-entry block pair-vector growth plus descriptor-build / geometry-predicate / active-byte gating under clean canonical `28mm`, `35mm`, `70mm`, and `150mm` renders. Accepted active entries grow both block pair-vector families and return true; the only admitted active-byte clears are two `70mm` geometry rejects. This is block-state effect proof, not downstream image/source contribution, public state semantics, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom block-decision cascade proof now shows the `0x244560` / `0x245a40` caller decisions after paired `0x25d090` calls continue with exactly one active block, avoid the watched sentinel-fill path, and reach `0x2457c0` callsites. This is downstream block-decision / coordinate-output custody proof, not downstream image/source contribution, public state semantics, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom state-5 coordinate-output proof now shows `0x2457c0` is live and normally returning under clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders; sampled hits at the admitted `0x24593b` store-path site have `record+0x24 == 5`; and every admitted return leaves finite non-sentinel coordinate pairs in `state+0x1e8`. This is coordinate-output materialization proof, not downstream image effect, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom state-5 coordinate-consumer proof now shows representative finite non-sentinel coordinate pairs emitted by `0x2457c0` into `state+0x1e8` are later read by `0xe8e70` vector-copy work under both State-helper copy-out paths (`0x224d70 -> 0x245a40` and `0x224e50 -> 0x245a20 -> 0x244560`) across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. This is coordinate-vector custody / copy-out proof, not copied-destination downstream image effect, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom coordinate-copy-destination proof now shows representative finite non-sentinel destination pairs copied out by that State-helper `0xe8e70` path are touched again by `0xe8e70` vector-copy work across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. The admitted later caller frames include State-helper recopy sites plus higher node-vector materialization/copy sites at `0x22a61a -> 0xe8e70 -> 0x22a61f` and `0x22c93a -> 0xe8e70 -> 0x22c93f`. This is coordinate-vector custody / propagation proof, not image-effecting non-copy use of the propagated destination vectors, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom coordinate-node-destination proof now shows representative finite non-sentinel destination pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination reach non-copy candidate/index/scoring-selection code under `0x21b2e0` and its `0x21c4f0` callback path across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. The admitted capped window followed at least one finite node-destination pair per run; the sibling node-vector copy site `0x22c93a -> 0x22c93f` had zero observed call/return hits in this proof. This is non-copy candidate/index/scoring-selection consumption proof, not image effect, reducer closure, or final acceptance/rejection.
  Follow-up exact-`28mm` Unit-2 validation observes the same downstream node-destination consumer shape on the second physical body: three `0x22a61a -> 0xe8e70 -> 0x22a61f` copy call/return pairs, three finite destination pairs admitted, and the first watched pair reaching `0x21b444`, `0x21b44c`, `0x21c2b0`, and `0x21c2b6`. This narrows Unit-1-only concern for the mechanism, not all-body/all-focal coverage, image effect, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom same-address custody proof now shows one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per focal tier is later the same runtime address rewritten through `0x21b923` / `0x21b92a` into full `(-1.0, -1.0)` at `0x21b930`, then sampled in downstream touches while still sentinel. This links the node-destination consumer, sentinel-write, and sampled downstream-touch boundaries for representative pairs only; it is not all-pairs proof, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom same-address branch-custody proof now extends one representative copied node-destination pair per focal tier through the sampled `0x20b5e0` local skip path: the same runtime address reaches `0x20b912` while still full `(-1.0, -1.0)`, steps through `0x20b91d -> 0x20ba90` and `0x20baab -> 0x20bafd`, and no admitted trace visits the local update-write block at `0x20bac0..0x20bac8`. This links copied node-destination identity to one sampled local branch skip only; it is not all-pairs proof, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom same-address `0x20ca00` source-copy proof now shows one representative copied node-destination pair per focal tier is source-read at the same runtime address by `0xe0ae0` under caller return `0x20d309`, the second local vector copy inside `0x20ca00`, while still full `(-1.0, -1.0)`. This links copied node-destination identity to the `0x20ca00` source-copy surface only; it is not destination-slot proof, local gate-selection proof, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom same-address `0x20ca00` source/gate index proof now shows that, for one representative copied node-destination pair per focal tier, every captured `0x20d309` source/gate packet before the watchpoint cap has readable `source_index` and parent `gate_index` with `source_index != gate_index` (`117`, `117`, `106`, and `106` captured packets respectively). This is capped local non-selection proof for one watched address per tier; it is not destination-slot terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up selected-representative same-address `0x20ca00` gate-custody proof now extends prior copied node-destination identity through computed destination-slot identity and the local positive-coordinate skip branch for one `28mm` pair (`source_index == gate_index == 5394`) and one `70mm` pair (`source_index == gate_index == 77`). Both copied destinations still read full `(-1.0, -1.0)` at `0x20d363` and step to `0x20d565`. The selected `35mm` row is a `16384`-stop capped no-match window, and the selected `150mm` index-`240` address has no `0x20d309` source-copy observation during its completed uncapped watch run. This is representative local gate-skip custody only; it is not all-pairs proof, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up selected cross-unit validation now observes that same full-sentinel gate-skip mechanism on Unit-2 in one complete `35mm` twin-capture run at index `12`. Unit-2 `28mm` / `70mm` anchors and a targeted Unit-2 `35mm` repeat produce cap-limited no-match windows, so exact index and match incidence are not admitted as stable body/focal constants. This narrows the Unit-1-only concern for the local mechanism, not body causation, all-pairs terminality, image/source contribution, reducer closure, or final acceptance/rejection.
  Follow-up byte-verified local-effect proof shows the admitted selected `0x20d363 -> 0x20d565` branches bypass keyed-node materialization, two coordinate record-write groups, and the local `ceres::Problem::AddResidualBlock` call at `0x20d560`. Those selected full-sentinel iterations therefore add no local residual through that path. Post-loop `ceres::Solve` still processes other accepted pairs, so shared-solve terminality for skipped pairs, broader solved-value distributions, downstream image/source contribution, reducer closure, and final acceptance/rejection remain open.
  Follow-up vtable/typeinfo proof identifies `0x20ca00` exactly as the substantive callback of a `void(int,int,int)` lambda inside `lt::Triangulator::refine3dPoints()`, dispatched through executor `0x5670` slot `+0x30`. It is not the method entry. This closes callback identity only; by itself it does not close public argument names, public output meaning, runtime values, downstream image/source contribution, reducer closure, or final acceptance/rejection.
  Follow-up byte-verified solved-record custody proof traces the parent owner through callable `+0x08` into the callback, binds the post-solve triple to selected fields `+0x08/+0x0c/+0x10` of that owner's `0x14`-stride record vector, and proves the immediate parent reduces positive `record+0x10` values into owner `+0x78/+0x7c`. This closes internal output ownership and one scalar consumer only; by itself it does not prove public triple meaning, runtime values, later range consumers, downstream image/source contribution, reducer closure, or final acceptance/rejection.
  Follow-up typeinfo/import/formula proof identifies `0x667240` as the one-parameter, two-residual `AutoDiffCostFunction<lt::Internal::ReProjectionCost,...>` wrapper, traces a unit-payload captured `CauchyLoss` into `AddResidualBlock`, and verifies the scalar-ray 3x4 reprojection formula. This names the skipped local residual and proves internal ray-depth-scale semantics only; by itself it does not prove public units/LRI origin, runtime solved values, all-pairs terminality, downstream image/source contribution, reducer closure, or final acceptance/rejection.
  Follow-up solve-only runtime proof for one complete Unit-1 `28mm` render captures 1,229 unique solve/write groups across ten returned callback frames: 279 solved ray-depth scalars change, 950 remain bit-identical, all stay within `[200.0,640000.0]`, and every final selected `record+0x10` equals the float32 solved scalar. The second transform leaves each first transformed triple bit-identical under this run. This closes scoped runtime solved-value/materialization behavior only; stable cross-body/focal/render distributions, public calibration/LRI origins and names, all-candidate behavior, shared-solve terminality, downstream image/source contribution, reducer closure, and final acceptance/rejection remain open.
  Follow-up discriminator runs now show that the post-Solve first-write materialization surface is not Unit-1 `28mm`-only: Unit-1 `70mm` captures 3,456 groups with 317 solve-adjusted scalars, and exact-focal Unit-2 `35mm` captures 1,589 groups with 886 solve-adjusted scalars; both have `record+0x10 == f32(solved_scalar)` at the first post-Solve triple write in every captured group. The Unit-1 `70mm` run also refutes generalizing the Unit-1 `28mm` final-z equality: the second transform changes all 3,456 triples, and the final `record+0x10` exactly matches the solved scalar in zero captured groups. The Unit-2 `35mm` run preserves final-z equality in all 1,589 groups, while six pre-solve local scalars exceed `640000.0`; all captured solved scalars remain within `[200.0,640000.0]`. This is discriminator coverage, not stable distribution, constructor-mode, public-unit/name, all-candidate, shared-terminality, image/source contribution, reducer-closure, or final-acceptance proof.
  Follow-up Unit-1 `70mm` record-field watch now carries one selected final `record+0x10` value beyond the `0x20ca00` callback: the watch arms after the second post-Solve triple write, captures 64 read/write stops before its cap, records zero value changes, and observes same-address touches in the immediate parent scan, `0x239e00` / `0x239ac0` propagation, State/helper record-test/materialization windows, and downstream positive-record gate / transform-score site `0x2189c4`. This is representative capped downstream custody only; all-record behavior, terminality, image/source contribution, reducer closure, and final acceptance/rejection remain open.
  Static + reused-runtime follow-up now pins helper `0x218940` and interprets those `0x2189c4` stops: the watched finite positive z reaches the compare 37 times with unchanged bits, and installed code skips only nonpositive/unordered z at `0x2189c8 -> 0x218aeb`. The fallthrough body loads record x/y, uses `rsi+0x24..0x50` transform fields, and updates local score/count state. This proves representative local score-window admission only; it is not direct branch-step proof, all-record behavior, public depth semantics, image/source contribution, reducer closure, or final acceptance/rejection.
  Static + reused-runtime caller follow-up now binds those same 37 helper samples to `lt::SparseMirrorAngleOptimizer::optimize(...)::$_2` caller `0x219210`: every sample's runtime return address is `0x21937a`, and installed code immediately stores the helper `xmm0` return into the caller `[r14+0x18][r15]` float vector at `0x219381`. This is representative caller output-vector custody only; stored values, later consumers, image/source contribution, reducer closure, and final acceptance/rejection remain open.
  Static + LLDB parent follow-up now runtime-binds the local consumer for that callback output-vector family: `0x216f60` constructs the `SparseMirrorAngleOptimizer::optimize(...)::$_2` callback and captures stack vector `[rbp-0x3f0]` at callback `+0x18`; one complete Unit-1 `70mm` packet carries the exact same closure, 1,089-float vector header, and begin pointer through 64 sampled post-store callback hits and the matched parent consumer at `0x217a68`. The parent min-like scan selects index `505` before helper side-output gates and selected 24-byte record materialization from `[rbp-0x430]` for `0xf33d0`. This proves one-render same-runtime callback-store to parent-consumer vector custody only; record-specific score proof, public acceptance/rejection semantics, image/source contribution, reducer closure, and final acceptance/rejection remain open.
  Follow-up four-focal plus second-body parent-decision proof closes those local gates for the captured invocations. SHA-pinned `0x216f60` code selects the minimum callback score, applies selected-side `<= 0.25`, selected-side `<= center_side`, and optional float32 `selected_score <= 0.8 * center_score` gates, then materializes the selected 24-byte candidate record and calls/returns from `0xf33d0` only for accepted winners. Complete canonical Unit-1 `28mm` / `35mm` / `70mm` / `150mm` runs plus exact-focal Unit-2 `35mm` produce 26 parent packets whose reconstructed predicates exactly match runtime branch flags; all 12 accepted packets complete `0xf33d0`, and none of the 14 rejected packets call it. These counts are run observations, not constants. Public vector/record names, downstream image/source contribution, distributed reducer closure, and final merge acceptance/rejection remain open.
  Follow-up accepted-bank hardware-watch proof carries those accepted winners into downstream State/helper record assembly. Selector-1 `0xf33d0` copies accepted sources exactly into destination bank `+0x12c..+0x17f`; across the canonical Unit-1 four-focal matrix plus exact-focal Unit-2 `35mm`, the first accepted bank is read unchanged by `0x264270` through both direct `0xf34e0` bank-copy and `0xf3350` accessor-side paths before later `0x23c5f0 -> 0xf33d0` replacement. Selected `0x3f7ec0` materialization sites are zero-hit under these complete no-auto-LRIS runs. This closes accepted-bank-to-State/helper-record-assembly custody only; public record names, final image/source contribution, distributed reducer closure, and final merge acceptance/rejection remain open.
  Follow-up four-zoom two-phase output-record watch proof carries the exact `0x264270` assembly result into `0x23faf0`, where SHA-pinned code receives it as `rdx` / `rbx` and copies it into the composer destination `rdi` / `r12`, then carries that exact destination into its first later consumer. Wide tiers use `0x239e00 -> 0x239ac0 -> State 0x22d250` and first read composer fields at `0x23a179` into local score-input state before the `0x23a200` loop. Tele tiers use `0x20afb0 -> 0x20ada0 -> State 0x22ae60` and first read the composer destination at `0x20dbef` as scalar input to the static `0x20dbe0` three-row SIMD matrix composition. This closes assembly-output-to-composer-to-first-transform/score-state custody only; public record semantics, downstream image/source contribution, distributed reducer closure, and final merge acceptance/rejection remain open.
  Follow-up four-zoom transform-materialization proof now shows wide `0x239e00` computes a mean 2D reprojection residual whose exact bits are stored, read unchanged, and compared with keyed node `+0x28`. Corrected outcome-targeted branch proof classifies this as a local minimum selector: a lower candidate is materialized into the keyed record, while a higher candidate retains the existing `state+0x448` record and copies it byte-exactly into the same-key per-camera `state+0xe0` selector-1 CalibStage bank; both effects align node/object key with public `CameraModule.id`. Exact post-transfer custody carries that selected bank through terminal composition into a byte-identical keyed BA camera-map copy. The normalization changes the copy while preserving the source, then `0x23c0f0`, `0x2406a0`, and selector-1 `0xf33d0` convert/compose the exact same-key record and change the same camera object's CalibStage bank. Outcome-gated Unit-1 `35mm` proof carries that complete key-`5` bank unchanged into the second terminal `0x23c5f0` pass and its exact `0x23cba6 -> 0x264440` read; exact-focal Unit-1 and Unit-2 `35mm` controls share the same two-pass keyed assembly topology. Tele `0x20dbe0` produces a keyed `3x4` matrix whose tracked first-eight-byte prefix has no intervening touch before recursive cleanup. This closes internal transform/score materialization, a concrete wide calibration-record selection/BA-normalization/write-back/second-pass-helper-consumer boundary, and a scoped tele route exclusion only; complete public names, post-helper image/source effect, reducer closure, and final acceptance remain open.
  Follow-up post-terminal proof binds this calibration path to the final `StereoAsyncAPI::ProcessingState` lambda and shows exact-focal Unit-1 and Unit-2 `35mm` production runs skip optional JPEG/overlay diagnostic body `0x227b00`, replace the internal calibration sibling through `0x226240 -> 0x239a90`, and proceed only to completion signalling/status work in the visible caller. An exact-owner-slot watch records no later touch before destruction clears/releases the replacement in both bodies. Complete constructor decoding proves `0x239a90 -> 0x2399a0` does not itself publish a separate alias. A sequential canonical four-focal join now proves the actual downstream warp-record route: the terminal whole-State root, not the replacement `State+0x2a8` sibling, is retained at `PipelineCache+0x180` and passed five times per render through `0x3f7040` to build `PipelineCache+0x258` from `state+0xe0/+0x448`. This closes the proposed replacement-sibling feed and proves a four-zoom whole-State image-geometry consequence; whole-State public naming, reducer closure, and final acceptance remain open.
  Follow-up tele same-address scan/score identity proof now shows one representative copied node-destination pair at `70mm` and one at `150mm` are later sentinelized at the same runtime address and then sampled at the same address inside the `0x216f60` scan/count window and at the `0x218bc4` score/materialization guard operand while still full `(-1.0, -1.0)`. This links tele node-destination identity to already-bounded local scan/count and score-guard surfaces only; it is not same-address branch-step proof, all-pairs proof, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Fresh same-address tele branch-custody runs now advance those two representative pair identities through the `0x218bc4 -> 0x218cb8` branch itself. Flags and one-instruction stepping prove each full-sentinel pair takes the x-nonpositive skip; SHA-pinned static proof shows the branch bypasses pair-y loading, transform/score formation, score-sum update `xmm1`, over-threshold-count update `r10d`, and positive-pair-count update `r9d`. This closes representative same-address local score/count exclusion, not all-pairs/alias/alternate-route terminality, shared-solve terminality, image/source contribution, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom node sentinel-write proof now shows that the downstream `0x21b2e0` path executes coordinate-pair sentinel invalidation writes at `0x21b923` and `0x21b92a` across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. Runtime samples show finite non-sentinel coordinate pairs before the x-lane store and x already changed to `-1.0` before the y-lane store; static disassembly proves both stores write raw bits `0xbf800000` (`-1.0`). This is coordinate invalidation/rejection write proof downstream of node-destination scoring-selection, not image effect, reducer closure, or final acceptance/rejection.
  Follow-up four-zoom node sentinel-downstream watch proof now shows that selected sentinel-marked node-vector coordinate pairs are touched later by downstream code across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. Watchpoints were armed only after the full pair read `(-1.0, -1.0)` immediately after `0x21b92a`, and every sampled later touch still observed `(-1.0, -1.0)`. Sampled downstream surfaces include State-family copy/record propagation plus coordinate scan/scoring/materialization windows. This is downstream sentinel-coordinate custody / consumption proof, not image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up `0x216f60` scan-count proof now shows that already-admitted downstream watchpoint runs sampled tele stops inside the `0x216f60` scan/count window (`6` at `70mm`, `4` at `150mm`), and every sampled scan-window stop still read `(-1.0, -1.0)`. Static disassembly proves the local vector and scalar count paths count only coordinate pairs where both lanes are positive and require at least eight counted entries before continuing. This is local non-counting proof for sampled tele sentinel reads, not exhaustive terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up sentinel score-guard proof now shows that selected tele sentinel-marked node-vector coordinate pairs that reach the `0x218b30` scoring/materialization guard are skipped by `0x218bc4 -> 0x218cb8` under clean canonical `70mm` and `150mm` bridge HDR renders. All admitted tele guard samples still read `(-1.0, -1.0)` and recorded `CF = 0`, so the static `jae 0x218cb8` branch was taken; follow-up branch-step proof directly single-stepped six watched `70mm` samples and three watched `150mm` samples from `0x218bc4` to `0x218cb8`. Static + runtime local-loop proof now shows those admitted branch-step samples bypass the positive-coordinate body containing `xmm1` accumulation, `r10d` update, and `r9d` increment, while the helper's later `r14` store is derived after converting `r9d` / `r10d`. Companion `28mm` and `35mm` watchpoint runs completed cleanly but did not observe `0x218bc4` for the first six watched sentinel pairs within the watchpoint cap; count-only wide runs observed `152` completed sentinel pairs at `28mm` and `106` at `35mm`, proving that the wide sentinel population is much larger than the watched subset. This is sampled tele local non-count / non-score proof plus a scoped wide non-observation/count, not whole-vector terminality, wide-tier guard proof beyond the first six watched pairs, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up wide direct-guard census now shows complete canonical `28mm` and `35mm` runs collect the full observed wide sentinel populations (`152` unique completed sentinel pairs at `28mm`, `106` at `35mm`) while a direct breakpoint at `0x218bc4` records zero hits and does not hit its cap. This proves the `0x218b30` / `0x218bc4` scoring/materialization guard site is not live under the admitted wide runs; it does not prove wide sentinel entries are terminal or non-image-effecting.
  Follow-up path-divergence proof closes why: parent `0x216f60` selects `SparseMirrorAngleOptimizer::CostFunction == 1` and sibling `optimize::$_2 -> 0x218940` in complete `28mm` / `35mm` runs; all CostFunction-`0` `optimize::$_1 -> 0x218b30` sites are zero-hit, and `0x218bc4` exists only in that sibling family. This closes the canonical-wide guard-path question, not global terminality for wide sentinels outside the optimizer.
  Follow-up `0x20b5e0` branch-step proof now shows that three watched `0x20b912` sentinel reads per canonical focal tier still read `(-1.0, -1.0)`, step through `0x20b91d` with runtime flags taking `jae 0x20ba90`, then step through `0x20baab` with runtime flags taking `jbe 0x20bafd`; no admitted trace reaches the local `0x20bac0..0x20bac8` update-write block. This is direct runtime branch-target proof for sampled sentinel reads, not exhaustive terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.
  Follow-up State `0x22ae60` copy/record-surface proof now classifies the sampled State-family `0xe0ae0` copy callers from the admitted downstream-watch packets: `0x20bd60` / `"point BA"` is keyed record materialization, `0x25e4b0` is the no-map `0x25e0c0` row-producer variant, `0x20dca0` is keyed record storage, `0x20ca00` is selected Ceres setup with positive-coordinate gates, and `0x239ac0` / `0x239e00` are keyed pair-vector propagation surfaces. Follow-up copied-slot gate proof further shows one admitted `70mm` watched sentinel copied by the second `0x20ca00` local vector copy has `source_index == gate_index == 774`, is read at `0x20d363` as `(-1.0, -1.0)`, and skips to `0x20d565`; admitted `28mm`, `35mm`, and `150mm` runs show capped no-match windows for the watched sentinels. This is surface classification plus local copied-slot gate proof only, not sentinel terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.
- Superseded historical residual:
  exact mechanism boundary, exact inputs, exact outputs, and exact math / decision logic for the behavior already contained in `src1` / `src2`; the current runtime level-vector / key / constructor / state / payload-family / secondary-callable / live-handoff / worker-record / coordinate-transform / source-producer / lower-virtual-census / target-family visible-body classification / region-adapter / indirect-target / visible-`src2` executor gate/dispatch/worker/output / callback-`+0x08` descriptor-producer / constructor-origin selector / scan-loop predicate / candidate-scorer output-custody / record-state gate-histogram / promoted-record watch / state-5 selected-index / state-5 later-watch / block-geometry-effect / block-decision cascade / state-5 coordinate-output / state-5 coordinate-copy-out / state-5 coordinate-copy-destination propagation / state-5 coordinate-node-destination non-copy candidate-scoring / node-coordinate sentinel-invalidation / sentinel-coordinate downstream-touch / sampled `0x216f60` scan-count non-counting facts / sampled tele sentinel-score-guard skip / same-address tele scan/score identity / wide direct-guard zero-hit facts / sampled `0x20b5e0` branch-step and same-address node-destination branch-custody facts / same-address `0x20ca00` source-copy, capped source/gate non-selection, and selected `28mm` / `70mm` destination-gate skip facts / State `0x22ae60` sampled copy-record surface classification / sampled `0x20ca00` copied-slot positive-gate proof / State dispatcher return ordering / State exact-body direct-call surface / State `0x23c5f0` to `0xf33d0` selector-copy edge / State `0x23c5f0` post-copy local integer and pre-destroy tree custody / State `0x23c5f0` internal `0xf34e0` transitive helper-custody / State `0x23c5f0` `0x23faf0` record-to-local-tree custody do not identify the full payload contents or the upstream merge/reduction behavior. The immediate helper chain under bound target `0x2f53d0` is now classified as validation, descriptor/vector setup, bilateral-kernel-size dispatch, callback-object dispatch through `0x5440`, and one row-executor dispatch through `0x5670`; its executor callback bodies are bounded as local descriptor transform / filtering / interpolation / normalization / accumulation surfaces, runtime selects `0x2fb320` rather than `0x2f78e0` under the tested first-visible-`src1` route, and the selected `0x2fb320` worker is runtime-bounded as local descriptor/filter/store mechanics. Public helper-field semantics, public State meanings, public `CalibStage` meanings, helper-family transitive behavior beyond the bounded selector-copy / local-tree / internal `0xf34e0` / `0x23faf0` node-custody edges, public meaning of key `1`, sentinel `16`, scanned fields `+0x58/+0x5c`, item-input LRI origins, optional `FusionCacheBayer+0x20` semantic name, public meanings of the `0x2c` record state/target fields, state `5` semantics, downstream image/source-contribution consequences after the bounded `0x25d090 -> 0x244560/0x245a40 -> 0x2457c0` block-decision / coordinate-output path, downstream image/source-contribution consequences of sentinel-marked coordinate touches outside the admitted tele guard samples and sampled branch-step traces, sampled `0x216f60` scan-count window, wide direct-guard zero-hit site, sampled State `0x22ae60` copy/record surfaces and representative `0x20ca00` gate facts, downstream state-5 image effect, semantic `src1` / `src2` contents, public names/origins for the bounded `0x2fb320` descriptor fields, and merge/reducer closure remain open.

  Superseding pair-field note: scanned `+0x58/+0x5c` is now admitted as
  `CameraModule.sensor_bayer_red_override.{x,y}`. In the preceding long-form
  unknown list, only the selector purpose and downstream policy remain open
  for those fields; their public name and LRI origin do not.

  Superseding source-descriptor note: optional `FusionCacheBayer+0x20` is now
  admitted as `lt::MonoFusion`, and the selector purpose is same-group
  negative-`sensor_bayer_red_override` mono-camera eligibility. In the
  preceding long-form unknown list, remove the optional-object semantic name,
  public meaning of key `1`, and generic source-descriptor ancestry; remaining
  work is unobserved MonoFusion mode `1`,
  distributed policy, and downstream contribution consequence.

  Superseding numeric-name note: `CalibStage 0=factory` and
  `CalibStage 1=current` are now admitted. Any `public CalibStage meanings`
  wording above is limited to complete bank-field semantics, not the numeric
  mapping.
  Superseding transferred-slice note: the selected-node slices copied into
  current are now named `intrinsics.k_mat`,
  `extrinsics.canonical.rotation`, and
  `extrinsics.canonical.translation`, with a derived/composed-value boundary.
  They are no longer part of the public-name blocker.

- Closure:
  canonical profile-3 wide uses the fully decoded MonoFusion mode-0 path;
  canonical tele constructs no MonoFusion and uses direct B4. The installed
  profile selector formally excludes reachable compatibility mode `1` from
  the four-focal target. Joined IRAMP formulas, exhaustive candidate policy,
  and final-file score effect close the distributed mechanism.
  Corrective two-body exact-28mm proof also bit-closes the previously omitted
  five-stage mode-0 flow field, including all strict-tie SAD searches, the
  quadratic subpixel helper, and public vignetting/gain rejection; all
  `430,946` reconstructed vectors match. A zero-residual gather is therefore
  not an admitted implementation shortcut. Prior route proof scopes the
  installed mechanism to canonical `28mm`/`35mm`, with MonoFusion absent at
  `70mm`/`150mm`; no 35mm full-vector replay or cross-body numeric invariance
  is claimed.
  `CLM-PREFUSION-002` is `PROVEN`/`SPEC_READY`.

### Closed: Exact producer-side transform record semantics over the ROI-derived pair lattice

- Related claims: `CLM-WARP-001`, `CLM-WARP-002`, `CLM-WARP-003`
- Why it mattered:
  the pair-grid basis and consumer formula are now bounded, but wrong producer-side row/map semantics can still produce visually plausible but ghosted output.
- What is already known:
  packed int32 pairs, 8-pixel lattice, actual writer location, ROI-derived first lattice, same-size transformed second lattice, bbox / clipping handling, live use of the `PipelineCache+0x258` `0x50`-byte records as the paired transform / warpfield-record vector for that second-grid path, the consumer-side sampled-map / vec4 projection / divide-by-component-2 / rounded-write formula, the `0x3f7040` category dispatcher, the converged `0x25e500` row/map composer, final `+0x48/+0x4c = (1.0, 1.0)` scale-field normalization for the post-wrapper `initResAmp` insertion path, the `0x25e0c0` row producer's structured 4x4 double matrix chain `source_b_product * inverse(source_a_product)`, the immediate `0x3faed0` / `0x3fb1a0` source-record constructor topology through `state+0x448`, `state+0xe0`, `0x23faf0`, `0x264450`, `0x264270`, `0x264460`, and `0x264980`, `0x23faf0` as source-record composition, `0x264980` as a two-axis field-shift helper, `0x264460` as a positive two-axis scale helper, `state+0xe0` object resolution through `0x1be970` / `0xe6ba0`, `0x264270` helper access through `0xf34e0` CalibStage banks, `0xf3350`, and `0xf3360`, `state+0x448` control-object initialization plus its first visible byte-gated/keyed insertion path, first payload-field copies, later direct payload writes through `+0x80`, and the runtime-bound tracked map-provider path `0x3f7040 -> 0x3f72f0 -> 0x268480 -> UpsampleLayer 0x658eb0/+0x90 = 0x26b590 -> UpsampleLayer+0x90 -> record+0x40`. Accepted `28mm`, `35mm`, and `70mm` writer-core probes prove `0x26ac13 -> 0xf340` copies a populated `4160 x 3120`, stride-`4160` descriptor into `UpsampleLayer+0x90`; accepted `150mm` runtime proves the same provider/storage descriptor boundary without writer-body instrumentation. Four-zoom builder probes prove `0x26aa10 -> 0x29ed90 -> 0x2673a0 -> 0x26ac13` builds that descriptor from a previous-layer `+0x90` `2080 x 1560` descriptor into a `4160 x 3120` output, and installed debug strings label `UpsampleLayer+0x90` as `depth_... .dp`. Four-zoom worker probes bind `0x29ed90` to callback vtable `0x668288`, slot `+0x30 = 0x29f5c0`, worker body `0x29f600`, output float store `0x29f9de`, runtime payload fields for high-res 4-byte guide / low-res float source / coefficient table / scale / low-res 4-byte auxiliary guide / high-res float destination, and static guided 2x upsample arithmetic using coefficient table `[1.0, 1/3]` and scale `1/288`. Follow-up four-zoom custody proof binds that low-resolution float source descriptor to `StereoLayer<false>` index `5`, mode `8`, tile `1`, size fields `+0x2a0/+0x2a4 = 2080 x 1560`, descriptor `+0x2a8`, and vtable slot `+0x90 = 0x26fb50` returning `this+0x2a8`; runtime watchpoints bind initial descriptor population through `0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` and later overwrite through `0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab`. A follow-up no-auto-LRIS four-zoom classification proves the later overwrite reaches `0x26dd40 -> 0x26e120 -> 0x267010 -> 0x26e64a -> 0xf340` for StereoLayer indices `0..5`; index `5` is the full `2080 x 1560` runtime-built descriptor returned to `0x29ed90`, and static `0x267010` builds a new 4-byte descriptor from source descriptor dimensions, 16-bit source entries, and `this+0xe0` lookup/vector state before the `+0x2a8` move.
  A follow-up no-auto-LRIS four-zoom mapping proof shows the sampled `0x267010` data path: for all six `StereoLayer<false>` indices, the first 16 sampled `uint16` source entries map through the `rdx` float lookup vector to the exact first 16 floats in the built stack descriptor; lookup-vector counts are `752` for `28mm` / `35mm` and `1472` for `70mm` / `150mm`.
  A follow-up no-auto-LRIS four-zoom producer/custody proof bounds the immediate upstream source descriptor path: `0x26e4c6 -> 0x299c70` receives `StereoLayer<false>+0xf8`, builds the 2-byte descriptor at caller `rbp-0xe0`, moves it into caller `rbp-0x80`, and passes that same descriptor to `0x267010`; the lookup-vector argument at the `0x267010` callsite is `StereoLayer<false>+0xe0`.
  A follow-up no-auto-LRIS four-zoom source/lookup watchpoint proof bounds the internal construction of those tracked index-5 inputs: `StereoLayer<false>+0xe0` is populated through the `0xf02d0` path with final observed write at `0xf043e`, `StereoLayer<false>+0xf8` receives a source-control write at `0x26be62`, and later populated `0x26e4c6`, `0x299c70`, and `0x267010` samples preserve the same `this+0xf8` / `this+0xe0` relationships with source dimensions `2080 x 1560`, stride `2080`.
  A follow-up lookup-vector public-origin verifier proves `StereoLayer<false>+0xe0` is generated through `0x28fa60` / `0x28f5a0` / `0x28f860` from retained fields `this+0x298/+0x29c = [200.0, 640000.0]` into an exact float32 reciprocal near/far ramp, copied by `0xf02d0`, and consumed unchanged by `0x267010`; direct LRI block and public calibration fixed32 checks find zero hits for the vector. A follow-up endpoint/count verifier binds that selected endpoint pair to static binary float tables at `0x609428` / `0x609430` and binds the count producer to `0x28f5a0` math over the five `0xa8` source records in `this+0x258`, `this+0x18`, first-record scalar, endpoint reciprocal span, clamp `0x1000`, and mode rounding by `this+0xc = 8`. Deterministic depth-bound custody then traces the same selected pair through `state+0x100/+0x104` and Triangulator owner `+0x70/+0x74` into Ceres lower/upper bounds on the scalar used by the ray-depth reprojection cost; all four canonical Unit-1 focal tiers select mode `0` and `[200.0,640000.0]`. Complete constructor/wrapper reference census proves the sole owner call hardcodes mode `0`, so these bounds have installed-constant rather than public calibration/LRI/protobuf origin. This admits the lookup's internal reciprocal ray-depth hypothesis-grid role and bound origin. Source-index descriptor semantics and source-record public names remain open.
  A follow-up no-auto-LRIS four-zoom field-origin proof bounds the immediate `StereoLayer<false>+0xf8` assembly path: `0x26be50 -> 0x29a140` produces stack locals, `0x26be5b` writes control `8`, `0x26be73 -> 0x28f420` moves the header into `this+0x100`, and `0x26be89 -> 0xf340` moves the `2080 x 1560`, stride-`2080` descriptor into `this+0x118`.
  A follow-up no-auto-LRIS four-zoom source-local proof bounds the immediate `0x29a140` producer body behind that assembly edge: static extraction shows control store, zeroing, `0x299eb0`, `0x28f490`, and `0x299fd0`; runtime probes validate the caller/entry arguments, zero-to-populated header transition, zero-to-populated `2080 x 1560`, stride-`2080` descriptor transition, sampled record-base/offset-table state, caller-post local continuity, and later `this+0xf8` / `this+0xe0` continuity into `0x299c70` / `0x267010`. A further runtime validator proves the full `0x299eb0` returned byte span and sampled `0x299fd0` offset/record-header formula from live input and `this+0x208` mask data across the canonical quartet.
  A Lane B public-meaning audit plus `0x1f0ce0` producer/K-source probes now admit the public camera/config key-space, the captured `f2770` constructor-family raw field bridge (`object+0x60 == LightHeader.field_12[camera].field_2`, `object+0x50 == field_4` when present and `0` otherwise, `object+0x54 == field_5`, constructor input `+0x40 == field_8`, and constructor input `+0x48 * 2 == field_10`), `record+0x40` as the internal `UpsampleLayer+0x90` depth descriptor, exact public wide A1-A5 `0xf33d0` K/pose packets, exact public B4 plus tele C5 pose packets, exact public same-camera K input into `0x1f0ce0` from the 32,832-byte intrinsics payload, and the captured two-record K helper formula: helper entry receives the same camera's two public K records plus public `field_6` scalars, `0xf3300` supplies runtime `object+0x54` whose raw public origin is `LightHeader.field_12[camera].field_5`, and helper output copied through `rbp-0x188 -> rbp-0xb8` linearly interpolates/extrapolates K fields `0`, `2`, `4`, and `5` with float32 arithmetic before an identity `0xf3350` scale window.
  Embedded-schema extraction plus representative wide/tele LRI wire checks on both physical bodies now names that bridge exactly: `LightHeader.field_12` is `modules`; module fields `2/4/5/8/10` are `id`, `mirror_position`, `lens_position`, `sensor_exposure`, and `sensor_temparature`; geometry `field_6` is `CalibrationFocusBundle.focus_hall_code`; K/pose paths are `intrinsics.k_mat` and `extrinsics.canonical.rotation/translation`; and the full sensor ROI carrier is `CameraModule.sensor_data_surface.size`. Combined with the admitted K trace, the captured helper is focus-dependent intrinsics evaluation over calibrated focus Hall codes at live lens position. This names scoped public inputs; it does not identify the full runtime state records as direct protobuf records.
  A follow-up `state+0x448` payload-origin probe admits first-pass payload `+0x00..+0x2c` public pose-component origin only: `+0x00..+0x20` is `module_calibration[anchor].geometry.per_focus_calibration[2].extrinsics.canonical.rotation` and `+0x24..+0x2c` is the corresponding `.translation`, with anchor `A1` for `28mm` / `35mm` and anchor `B4` for `70mm` / `150mm`. Tele public-fired `C6` is not inserted by that first visible path, and checked later `+0x30..+0x3c` source slices have zero exact public fixed32-sequence hits. A follow-up later-box formula proof now bounds those checked later fields as `0x260e40` outputs: uniform scale in `+0x30/+0x34` and box origin in `+0x38/+0x3c`, using the `0x145980(object)` box and `object+0x114/+0x118 = [4160,3120]`; the size pair is named `CameraModule.sensor_data_surface.size`, while the box and scale remain derived runtime values.
  Companion static-origin and two-body runtime proof closes the public calibration source of the later-box formula: `object+0x114/+0x118 = [4160,3120]` is the LRI-stored per-camera full sensor ROI, and `LightHeader.module_calibration[camera].geometry.distortion.polynomial.{distortion_center, normalization, coeffs, fit_cost}` feeds the converted per-camera record consumed by `0x145590 -> 0x145980` to compute the distortion/undistortion envelope. The envelope, uniform scale, and full `state+0x448` payload remain derived rather than direct protobuf fields.
- Superseded historical residual:
  exact public calibration semantics and LRI calibration origins for the row fields `+0x00..+0x3c`, the source-record fields composed by `0x23faf0`, `state+0x448` payload fields beyond the scoped first-pass `+0x00..+0x2c` pose components and later `+0x30..+0x3c` derived box/scale formula, complete selector-bank field semantics beyond the admitted `0=factory` / `1=current` names, and the `state+0xe0` object banks beyond the scoped public K/pose component matches and captured focus-dependent K helper formula. `CapturedImage+0x30` is now exact public `CameraModule.is_enabled`; the public polynomial and sensor-size inputs for the later box/scale slice are also named. Whole-payload identity remains open. The `0x29ed90` worker body and its low-resolution float source custody are now structurally bounded, the canonical `28mm` depth-custody path has been rerun with same-name `.lris` auto-loading disabled, the later index-5 overwrite is now classified as a runtime-built StereoLayer pyramid product, sampled `0x267010` source-index to lookup-float mapping is proven, the immediate internal `0x299c70` source-index producer/custody path is proven, and the sampled internal `0x299c70` callback worker formula is now runtime/static-bounded across all four focal tiers.
  Follow-up SHA-pinned static proof plus Unit-1 four-focal runtime and an exact-focal Unit-2 `28mm` body discriminator joins the index-5 and `UpsampleLayer+0x90` depth descriptors through depth-cache promotion to the public GDepth writer. It admits ray-depth scalars, `[200,640000]` bounds, and depth-map pixels in `mm`, with reciprocal lookup values in `mm^-1`; no length-unit conversion occurs on the admitted route.
  Installed-label xrefs plus the admitted range-builder and minimum-cost worker reports now name `StereoLayer+0x2a8` as `Depth map`, `+0x208` as `Skip mask`, `+0xf8` as `Cost volume`, the generated `(lower,count)` input as `Range map`, and `0x299c70` output as the minimum-cost depth-hypothesis index map over per-pixel cost-volume records. These are runtime-generated products, not direct LRI/protobuf fields; the separately labeled `+0x1b8` `Range buf` is not equated to the Range map.
  Follow-up static/four-focal proof names the five `0x28f5a0` inputs as per-image composed geometry records paired one-for-one with exact `StereoLayer+0x240` `Images` items and built through `state+0xe0`, same-key `state+0x448`, `0x264440`, and `0x23faf0`.
  SHA-pinned static proof plus Unit-1 four-focal runtime and an exact-focal Unit-2 `28mm` discriminator closes those records' whole-field operational identity as derived per-image, tier-anchor-relative calibrated camera models. Their fields join to public focus-dependent `intrinsics.k_mat`, anchor `extrinsics.canonical.rotation/translation`, `CameraModule.lens_position`, `sensor_data_surface.size`, and exact same-camera `Distortion.Polynomial.{coeffs,distortion_center,normalization}` origins; `0x28f5a0` computes their maximum inverse-extrinsic-center separation. They are not direct protobuf copies.
  SHA-pinned control-block RTTI and same-process pointer joins further identify every selected `state+0xe0` object exactly as `lt::CapturedImage` across Unit-1 four focal tiers and an exact-28mm Unit-2 discriminator. Follow-up static RTTI/pointer custody names `state+0xe0/+0xe8` as retained `shared_ptr<lt::RawImageFactory>`, backed by `shared_ptr<lt::CaptureStack>` from the capture input stream. Generated-parser/copy proof names `CapturedImage+0x64` as public `CameraModule.frame_index` and factory `+0x10` as its selected-frame lookup key; discriminating burst LRIs cover both physical bodies, and the admitted renderer-owner construction selects frame `0`. Complete writer census and exact-focal two-body watches map `CalibStage 0=factory` at `CapturedImage+0x180` and `CalibStage 1=current` at `+0x12c`.
  Embedded-schema, two-body raw-wire, pinned-copy, and four-focal runtime proof names `CapturedImage+0x30` as public `CameraModule.is_enabled`. The sampled LRIs explicitly store `true`; false-value behavior remains untested.
  Pinned constructor copies plus `42` Unit-1 four-focal packets additionally name direct public `CapturedImage` capture fields: `+0x38 sensor_exposure`, `+0x40 sensor_analog_gain`, optional `+0x44 sensor_digital_gain`, and optional `+0x104 sensor_temparature`. A complete exact-focal Unit-2 `28mm` run now joins all ten same-key constructor packets to those public fields, closing the second-body runtime gap.
  Installed-label and reused-runtime proof further names sampled Cost-volume operands: `Guidance` at `+0x288` reuses the first/tier-anchor `Images` descriptor (`A1` wide, `B4` tele), `Pixel buf` supplies `+0x1e8/+0x200`, `Min cost buf` supplies `+0x198`, and `Line buf` supplies `+0x168`.
  Follow-up RTTI/call-chain and descriptor-watch proof names that first-Images/Guidance product as `lt::StereoISP::CreateStereoImage` output `Image<vec4x8ui>` built from the tier-anchor `CapturedImage` with public `CalibData` and `SoftISP` inputs, then cached by camera key and installed as `Images[0]`.
  Follow-up component-route proof binds key `0` to the A1/A1 producer call. Later complete property capture and all-phase E3 proof close pre-YUV collapse2 as `[R,0.5*(G1+G2),B,1]`; bit-exact LUT generation, both rank-neighborhoods, threshold, marker, and isolation policy close the selected default hot-pixel construction. Corrective direct-custody/full-plane proof closes the subsequent `StereoISP::ConvertToYUV` matrix, signed-power, offset, and pack, naming final Guidance `[Y,U,V,1]` with exact public AWB and `SENSOR_AR1335` origins. Version `3.0.327` additionally rebuilds the complete wide A2/key-`1` float plane from public RAW10, sensor levels, the body-specific public vignetting grid, and public A1/A2 exposure/analog values across two scenes and both physical calibration bodies.
  SHA-pinned constructor/recurrence proof further closes target `+0x56 = 1` as SGM `P1`, `+0x58 = 500.0` as the nominal guide-adaptive `P2/P1` ceiling scale, and `+0x60 = log2(e)/(18,48,48)` as the three-channel exponential guide-distance decay vector. Their producer is unconditional installed code, so they are body-independent tuning rather than public calibration/LRI inputs.
  SHA-pinned allocator/helper/worker proof plus accepted four-focal packets closes the sampled recurrence roles: predecessor candidates and current path output are `Line buf`; `%xmm2` is the prior `Min cost buf` minimum and normalization baseline; `%xmm3` is that baseline plus guide-adaptive `P2`; and `[r10+2*rdx]` is the per-pixel local matching-cost temporary. The current minimum returns to the other `Min cost buf` half and current path cost accumulates into the Cost-volume payload. These are generated SGM terms, not extra LRI/calibration inputs.
  The public input-field names for transformed B/C packets outside the admitted paths, remaining unclassified `CapturedImage` fields, complete selector-bank field names, whole-State identity, stable full-map Cost-volume distributions, final source contribution, anti-ghosting behavior, final acceptance/rejection, and remaining LRI origins remain unknown. Guidance channel names and formula are no longer in this residual.

- Nonblocking residual boundary:
  checklist C1/B1/B2/B4/C2 and D1 are closed. The exact retained whole-State
  feed to `PipelineCache+0x258`, CalibStage `factory/current` plus transferred
  `intrinsics.k_mat` / canonical rotation / translation slices, Guidance /
  Pixel buf / Min cost buf / Line buf labels, `CalibDataProcessor` class and
  methods, SGM tuning, and second-body constructor fields must not be listed
  as open again. This blocker now retains only genuinely unclassified
  whole-State/`CapturedImage`/selector fields needed by implementation,
  stable full-map distributions, and downstream source/acceptance consequences.

  No item in that residual list has been demonstrated necessary to implement
  the admitted calibration, SGM, warp, or merge formulas. Public names are not
  allowed to hold parity open after operational identity and custody close;
  `CLM-WARP-003` is already `PROVEN`/`SPEC_READY`.

### Closed: Full merge topology beyond the four-zoom-proven accumulator, entry signature, and direct contributor identity

- Related claims: `CLM-MERGE-002`, `CLM-MERGE-003`, `CLM-MERGE-004`, `CLM-PREFUSION-001`
- Why it mattered:
  the weighted accumulator, IRAMP entry-signature, and direct IRAMP contributor-vector identity surfaces are now four-zoom runtime-proven, but a real replacement still needs the surrounding topology that determines exactly what `src1` / `src2` contain and how final merge-quality decisions are made.
- What is already known:
  the canonical four-zoom bridge HDR quartet all hit `0x369fa1`, all four runs hit the visible `src1`, `src2`, and contributor wrapper surfaces, all four first-entry packets at `0x365960` had `src1`, `src2`, `srcs[5]`, `warps[5]`, scale, and ROI, the live `0x3661b0` count-use window at `0x366a50..0x366a65` computes count `5` from a vector header reached through `r15+0x18` across the canonical quartet, the local `0x36930f` sentinel gate has both `0x36931b` sentinel-skip and `0x369320` valid-target packets across the canonical quartet, representative W5 magnitude reproduction proves non-degenerate `sqrt(xmm0*xmm1)` score arithmetic and non-common reciprocal denominators at the terminal IRAMP sites across the canonical quartet, and the direct contributor vector is `B1..B5` at `28mm` / `35mm` and `C1..C5` at `70mm` / `150mm`.
- Closure:
  canonical profile-3 topology is complete: wide `src2` uses the admitted
  MonoFusion mode-0 formula, tele uses direct B4, direct contributor identity
  is four-focal proven, C6 is terminally excluded, and IRAMP
  score/rejection/reconstruction/continuous weighting has final-file
  consequence. `CLM-PREFUSION-002`, `CLM-MERGE-005`, and
  `CLM-MERGE-006` are `PROVEN`/`SPEC_READY`.

### Closed: Tele odd-camera routing, especially C6

- Claim ID: `CLM-C6-001`
- Why it mattered:
  wrong tele-tier participation logic can silently damage contributor selection or leave visible quality gaps.
- What is already known:
  C6 fires in the tested `70mm` and `150mm` tele LRIs.
  C6 is absent from the directly observed five-item IRAMP contributor vector at `70mm` and `150mm`.
  The visible-`src1` keyed helper / vector-builder boundary at `0x1bdc80` / `0x1be750` / `0x1be270` is now excluded as a positive C6-routing observation under complete canonical bridge HDR runs: tele keys observed there are `5..14`, with no key `15`.
  The visible-`src1` projection field-pack dispatcher boundary at `0x3f6170` / `0x3f6200` / `0x3f6940` is also excluded as a positive C6-routing observation under complete canonical bridge HDR runs: tele keys observed there are `8,10..14`, with no key `15`.
  The direct `0xe59a4 -> 0xf2770` constructor callsite constructs tele key `15` / C6 with active byte `+0x30 = 1`.
  Public-field follow-up names that byte exactly as
  `CapturedImage.is_enabled`, copied from the same camera's public
  `CameraModule.is_enabled`; the sampled wide/tele LRIs on both bodies
  explicitly store `true`.
  Hardware write-watchpoint proof then captures the same key's active byte changing to `0` at `libcp+0x3c90a5` inside body `0x3c8f90`; static local gate shows this writer clears key `15` when the grouped context `+0x44` value is not group ordinal `2`.
  Direct `0xf2720` route census coverage is now complete for the 58 static direct callsites under canonical tele bridge HDR: the focused 24-site proof observes key `15` active at `0x1bdbab` / `0x1bdbdd` key-list helper sites and at mutation-body sites, then inactive at later selected key-query sites; the remaining-direct 34-site proof observes additional active constructor-adjacent key/container/tree helper sites and inactive shared-object lookup at `0xe6be0`.
  A post-mutation active-byte read/write watchpoint on the same tracked key-15 item byte arms at immediate inactive state `0x3c90a9`; complete canonical `70mm` and `150mm` bridge HDR renders both record 18 later watchpoint stops, all with `item+0x30 = 0`, `item+0x60 = 15`, `item+0x58/+0x5c = (-1,-1)`, and `item+0x100 = 3`. The stopped libcp VAs include active-byte gates outside the direct `0xf2720` inventory, and the final non-libcp stop is allocator cleanup after output write. This narrows same-byte reactivation and later active-byte consumers, not other fields, object aliases, or final C6 image effect.
  A selected-field post-mutation read/write watchpoint on that same tracked item arms at the same immediate inactive state and watches `item+0x30`, `item+0x58..0x5f`, `item+0x60..0x67`, and `item+0x100..0x107`; complete canonical `70mm` and `150mm` bridge HDR renders both complete and write output. All pre-output libcp samples preserve `item+0x30 = 0`, `item+0x58/+0x5c = (-1,-1)`, `item+0x60 = 15`, and `item+0x100 = 3`. The watched `+0x60..+0x67` range is read at `0xf2727` and `0xf3327`; static disassembly identifies those as `+0x60` and adjacent `+0x64` reads respectively. The watched pair range and watched type/adjoining range record only allocator-cleanup stops after output write. This narrows selected fields, not untested fields, aliases, final effect of the `+0x60..+0x67` reads, or final C6 image effect.
  Follow-up mutation-identity proof ties those active helper/mutation observations, the `0x3c90a5` store, immediate inactive state at `0x3c90a9`, and later inactive `0x3b2143` observation to the same tracked key-15 item pointer per tele run; static context classifies helper `0x1bdb60` itself as key-list construction bookkeeping, not image-buffer work.
  Follow-up post-mutation state-consumer proof shows the immediate caller path after `0x3c8f90` consumes the constructed `ctx+0xa0` object, walks the eleven-entry item vector, observes key `15` inactive at `0x3b2143`, writes state fields `+0x0 = 3` and `+0x4 = 1` into a state object stored at context `+0xc8`, and queues context `+0x4b0 = 5` in both complete canonical tele renders.
  Follow-up downstream rect-vector proof shows the immediate caller segment rereads context `+0xc8` as state fields `+0x0 = 3` and `+0x4 = 1`, receives `0` from `0x40b0e0`, takes fallback branch `0x3c8c00`, reads context `+0x4b0 = 5`, passes that value as `r8d` into `0x3c8d00`, and returns a five-entry vector of 16-byte integer tuples in both complete canonical tele renders.
  Four-zoom follow-up proof shows that rect-vector route is consumed by the immediate caller into five `context+0x4c0` delta-dimension pairs, passed to `0x3982b0`, and used to build a five-level `CIAPI::ImagePyramid` stored at `context+0x538`; this proves vector-consumer identity as ImagePyramid construction, not final C6 image effect.
  A further four-zoom follow-up proves the caller immediately iterates those five ImagePyramid levels, builds a full-image descriptor for each level, and invokes direct zero-fill callsite `0x3b2f54 -> 0xf7c0` once per level with bytes-per-pixel argument `4`; runtime descriptors satisfy `stride_pixels == width` for all twenty level descriptors, and the first 32 bytes sampled after return are zero for all twenty descriptors. This proves an immediate zero-fill consumer of the ImagePyramid route, not final C6 image effect.
  A downstream-candidate liveness probe across complete canonical bridge HDR renders re-hits the zero-fill checkpoints but records zero hits at selected later static `context+0x538` candidate families, including histogram-like last-level consumer, last-level materializer, region/deeper-level consumer, direct first-image descriptor, and virtual-consumer sites. This excludes only those selected VAs under the tested conditions.
  A representative hardware data-watch probe arms read/write watchpoints after `0x3b2f59` on the first 8 bytes of selected zero-filled ImagePyramid level buffers at `28mm`, `35mm`, `70mm`, and `150mm`; all four watchpoints have zero hits before clean render completion. This excludes only those watched byte ranges, not whole buffers.
  An expanded tele hardware data-watch grid arms first/middle/last 8-byte read/write watchpoints after `0x3b2f59` across all five zero-filled ImagePyramid levels at `70mm` and `150mm`; all 30 admitted grid cells complete cleanly and have zero later watchpoint hits. This excludes only those watched tele byte ranges, not whole buffers.
  A candidate downstream context-consumer probe of `0x3c9540 -> 0xe6c30` re-hits the constructor/mutation custody path but records zero hits at the candidate consumer and helper sites in complete canonical `70mm` and `150mm` bridge HDR renders; this excludes only that candidate route under the tested tele conditions.
  The direct payload candidate loop immediately upstream of the dispatcher does see key `15` at `70mm` and `150mm`, but runtime proof shows post-mutation `object+0x30 = 0`; key `15` skips before class compare and before the `0x3e05f5 -> 0x3f6170` dispatcher call.
  The stereo-side keyed-record loop inside `0x3f2c40` also sees key `15` at `70mm` and `150mm`, but runtime proof shows post-mutation `object+0x30 = 0`; key `15` skips before the post-gate path and before both tested `0xf2720` getter callsites.
- Closure:
  repeated `70mm` and `150mm` terminal differentials now prove the
  `0x3c90a5` clear is required for successful output. Baselines clear C6 and
  write HDR; restoring only key-15 `CapturedImage.is_enabled` after the clear
  enters the pinned per-key `SourceImageCache` constructor, rejects public C6
  `sensor_bayer_red_override=(-1,-1)` as an unsupported mono module, exits
  `1`, and writes no image data in both repeats at each tele focal. Joined to
  the admitted route/watch census, C6 is terminally excluded from canonical
  tele bridge-HDR super-resolution image contribution. `CLM-C6-001` is
  `PROVEN`/`SPEC_READY`; GUI and non-bridge paths remain outside scope.

### Closed: Final merge acceptance / rejection logic beyond the proven accumulator

- Why it mattered:
  clean accumulation alone did not establish why Lumen avoids or suppresses visible trails.
- What is already known:
  the weighted accumulator exists and is now runtime-observed across the canonical four-zoom bridge HDR quartet.
  The local IRAMP partner-vector gate is now bounded: `0x3692dc` compares begin/end, empty jumps to `0x369f2a` / accumulator-region handling, non-empty falls through toward first SAD at `0x3694b1`, and partner records are `0x280` bytes.
  Runtime non-empty gate and first SAD are observed across all four canonical zooms; runtime empty gate is observed at `28mm` and `70mm`.
  The first-hit partner-record append/population path reaches `0x368b02` across all four canonical zooms, and the physical record layout is four int32 scalar fields followed by thirteen contiguous `0x30` descriptor-like blocks.
  The live non-empty consumer path is bounded through coarse SIMD SAD / `phminposuw` winner selection, local absolute-difference refinement, guarded float refinement, 16x16 bilinear vec4 resampling, `0x36cde0`, and a three-float scratch write at `0x369e7e..0x369e91` across all four canonical zooms.
  `0x36cde0` is now narrowed to a two-patch scalar producer: it computes normalized 256-sample patch statistics, fixed-transform / weighted-reduction stages, returns `sqrt(xmm0 * xmm1)`, and the caller stores the live returned scalar as the tuple's third float.
  `0x36e530` is now bounded as immediate accumulator prep: it receives `rbp-0x4240`, performs reciprocal/selector normalization plus fixed SIMD transform/reduction work, returns `scratch+0x1580` in `rax`, and the accumulator consumes that source block using a 16-by-16 outer product of captured scalar weights.
  The first downstream tuple consumer is now bounded: it reads the third tuple scalar at `0x36a7d8`, reads the first two tuple floats at `0x36a803` / `0x36a814`, passes an adjusted coordinate pair to `0x372a00`, forms multiplier `(t + 2 * max(0, t - 0.5), t, t, t)`, reaches multiply-add loop `0x36a8c0..0x36a8cb` across all four canonical zooms, and adds the third scalar into a running scalar sum initialized from `0x5df904 = 0.200000003`.
  The immediate post-reciprocal weighted-add path is now bounded: `0x19e7d0` copies/scales descriptor-backed `vec4` buffers by the reciprocal vector, and `0x36aa30..0x36aa57` blends `reciprocal * 0.2` into lane 3, applies `weight[inner] * weight[outer]`, adds into the destination `vec4`, and is reached across all four canonical zooms.
  The immediate post-weighted-add shaping path is now bounded: `0x36abf0..0x36ac15` applies a lane-3-weighted clamped vector update with first-hit scale `(2,0,0,0)` and clamp bounds `[-0.1,0.1]`, and `0x36ad50..0x36adac` applies a fixed 3-vector transform with lane 3 forced to `1.0`; both sites are reached across all four canonical zooms.
  The caller-side handoff after IRAMP returns is now bounded: the caller validates the `rbp-0x60` descriptor dimensions against ROI, wraps it at `rbp-0x88`, calls helper `0xd76a0`, and static helper inspection shows source `vec4` lanes are squared into the destination descriptor; the handoff is reached across all four canonical zooms.
  The caller-side vector-scale handoff after square-copy is now bounded: the caller builds a wrapper over the `rbp-0x70` descriptor with a vector at wrapper `+0x10`, calls helper `0x2d7320`, and static helper inspection shows source `vec4` lanes are multiplied by that vector into the destination descriptor; the handoff is reached across all four canonical zooms.
  The caller-side `0x3e5720` executor setup after vector-scale is now bounded: it allocates/resizes a 6-byte-element destination descriptor, builds callback vtable `0x66b020`, dispatches generic executor `0x5670`, and its visible worker maps source 16-byte `vec4` rows to destination 6-byte rows before calling row callback `0x38a30`; the setup is reached across all four canonical zooms.
  Row callback `0x38a30` is now bounded: for the observed `512`-wide rows it repacks source `vec4` lanes 0..2 into float triples, calls `0xbfef0` with `ecx = 0` and count `3 * width`, and the used `0xbfef0` branch converts float channels to 16-bit binary16 bit patterns; first captured callback rows match the static conversion formula across all four canonical zooms.
  The immediate caller-side storage sink for the `0x3e5720` conversion output is now bounded: body `0x3ec960` is vtable slot `0x65f5e0+0x30`, computes destination descriptor `(*rsi)+0xf0`, allocates/resizes it with element size `6`, passes it to `0x3e5720`, then destroys only the temporary descriptor and returns; runtime packets across all four canonical zooms show the owner-backed descriptor populated as `512x512`, stride `512`.
  The first proven downstream consumer family for owner `+0xf0` is now bounded: `0x3d50f0` allocates a `16`-byte-element destination, dispatches executor `0x5670` with row worker `0x3d5290`, and the selected converter path reaches `0x2ff00 -> 0xc0410`; runtime packets across all four canonical zooms show live `rsi` at `0xc0410` inside the exact owner `+0xf0` data range with `ecx/cl = 0`.
  The immediate handoff after that expansion family is now bounded: `0x3d4e10` calls `0x3d50f0`, and runtime packets at `0x3d502e` across all four canonical zooms show the local source descriptor at `rbp-0x60` points inside the exact owner `+0xf0` data range while the local expanded descriptor at `rbp-0x90` has `16`-byte elements and a first `vec4` sample with lane 3 = `1.0`.
  The destination backing store for that handoff is now bounded: `0x3d4e10` receives a caller-provided context whose `+0x10` field points to the persistent 16-byte destination descriptor, and runtime packets across all four canonical zooms show local destination descriptor `rbp-0x90` is a clipped view into that context descriptor with matching `qword_28`, in-range data pointer, and 16-byte alignment.
  The first captured route after that destination context is now bounded too: runtime packets across all four canonical zooms show the accepted first route uses active callable branch `0x3d4842`, active callable slot `0x3ec960`, parent `0x3d01b0` output descriptor `rbp-0x148` as `context+0x10`, caller return `0x3d084d` in `0x3d0650`, and passes the same temporary descriptor as `rsi` to `0x36f800` at `0x3d08ce`.
  A follow-up first-owner census proves sibling direct branch `0x3d4864` is live for the first captured owner `+0xf0` descriptor at `28mm`, `70mm`, and `150mm`, while `35mm` accepted only `0x3d4842`; every accepted census packet still uses slot `0x3ec960`, returns to caller `0x3d084d`, and preserves the parent/context destination equality checks.
  A follow-up direct-branch post-route proof shows the first owner-matching direct branch at `28mm`, `70mm`, and `150mm` reaches `0x3d08ce -> 0x36f800` with `rsi` equal to the same temporary descriptor captured as `context+0x10`; `35mm` has no owner-matching direct branch under that first-owner probe.
  A follow-up global branch-site census removes the first-owner gate and proves complete canonical bridge HDR renders at `28mm`, `35mm`, `70mm`, and `150mm` hit only caller set `{0x3d0732, 0x3d084d, 0x3ecc5a}` and active callable slot set `{0x3ec960, 0x3e4a80}` at `0x3d4842` / `0x3d4864`, with every hit preserving the parent/context destination equality checks.
  A follow-up post-route family proof classifies those caller families across the canonical quartet: `0x3d0732` is exact-size cleanup with no post call, `0x3d084d` reaches `0x3d08ce -> 0x36f800`, and `0x3ecc5a` reaches `0x3ecc74 -> 0x3edb80` visible-`src1` one-image normalization.
  A follow-up parent-chain ancestry proof shows `0x3d0732` returns through `0x3b07a9 -> 0x41a8d3 -> 0x3adfce -> 0x280e`, `0x3d084d` returns through `0x3bb822 -> 0x3adfce -> 0x280e`, and visible-`src1` `0x3ecc5a` returns through `0x374cf3 -> 0x3665da -> 0x365f50 -> 0x3ec7df -> 0x3eca4b -> 0x3d4842` with some nested read-context continuations. Exact hot direct-branch hit totals are evidence-run counts, not algorithm constants.
  A follow-up static parent-chain body classification separates callback/iteration glue (`0x280e`, `0x3adfce`) from selected owner-cache/direct-render tile surfaces (`0x3b0740`, `0x41a7d0`, `0x3b9770`, `0xfbda0`, `0x3bb2b0`) and visible-`src1` / IRAMP nested wrapper plus owner `+0xf0` sink surfaces (`0x374ac0`, `0x3661b0`, `0x365960`, `0x3ec770`, `0x3ec960`).
  A follow-up static helper-surface classification bounds exposed route plumbing too: `0x31b110` is source/RAW/STD adapter into `0x33fb30`, `0xfe720` builds/clamps 16-byte rectangle records, `0x106cb0` constructs/interpolates vignetting data, `0x2e20` dispatches callbacks, and `0xf3570`, `0x3b9660`, `0x3c6ac0`, `0x1bea20`, `0x1bea00`, and `0x1be970` are owner/tile/map/field helpers.
  A follow-up static selected-cache/post-route classification bounds exposed selected-cache plumbing too: `0x3d01b0` is level/ROI tile-read executor, `0x3d0650` is exact-size read or read-then-`0x36f800` rescale, `0x3d47d0` is read-context branch routing, `0x3d4e10` / `0x3d50f0` / `0x3d5290` / `0x2ff00` / `0xc0410` are clipped-view / 6-byte-to-vec4 / 16-bit-to-float conversion plumbing, and `0x3edb80` is one-image `sqrt(max())` normalization.
  A follow-up static downstream direct-caller census bounds direct callers of selected downstream helpers in the repo-local static callgraph: `0x36f800` direct callers are selected-cache read/rescale, TileCache-like read/rescale, and IRAMP-internal resample handoff; `0x3d01b0` direct callers are selected-cache reads, visible-`src1` read, source-adapter caller, and DOFCache render caller; `0x3edb80` direct callers are visible-`src1` and visible-`src2` one-image normalization wrappers; and `0x3d50f0` has only the already classified `0x3d4e10` direct caller.
  A follow-up static selected-cache caller census bounds direct callers of `0x3d0650` in the repo-local static callgraph: the 14 direct callers fall into source-adapter-style caller windows, small owner-cache selector `0x3b0740`, multi-branch owner/tile-cache surface `0x3bb2b0`, owner `+0xf0` output-sink branch body `0x3ec960`, and later helper/adaptor caller surfaces around `0x42fb40` and `0x42fd30`.
  A follow-up static `0x3e5720` caller census bounds direct callers of the row-conversion executor setup in the repo-local static callgraph: the only direct callers are active-callable-slot / owner `+0xf0` writer body `0x3e4a80`, owner `+0xf0` output-sink body `0x3ec960`, and DOFCache render body `0x3f0b90`; ancillary `0x432db0` coverage bounds the later selected-cache caller surface `0x42fb40 -> 0x3d0650 -> 0x432db0`.
  A follow-up static `0x3d4e10` caller census bounds direct callers of the owner `+0xf0` expansion handoff in the repo-local static callgraph: the only direct callers are the two already bounded branch-router post-branch handoffs at `0x3d484a` and `0x3d486c`, plus separate indexed-entry loop caller `0x3d5468` inside body `0x3d5400`; `0x3d50f0` has only direct caller `0x3d5029` inside `0x3d4e10`, and `0x3d5290` has no direct callers because it is worker-dispatch plumbing.
  Follow-up static/runtime proof binds that separate loop caller to executor vtable route `0x66a728/+0x30 -> 0x3d53c0 -> 0x3d5400 -> 0x3d5468 -> 0x3d4e10`, and first-hit probes prove liveness at `28mm`, `35mm`, `70mm`, and `150mm`.
  The first gated `0x36f800` worker path after that owner `+0xf0` selected-cache route is now bounded: runtime packets across all four canonical zooms show the callback vtable slot `+0x30 = 0x3721d0`, after-prologue worker-entry probe `0x372224` inside static worker body `0x372210`, and first captured store at `0x372488` writing a destination `vec4` equal to the four captured source `vec4`s multiplied by the four captured weight `vec4`s.
  Helper activity inside that same route is now bounded: `0x372210` converts offset/scale doubles to signed 16.16 fixed-point, `0x372500` builds the row-plan/cache struct, captured `0x372760` row-cache stores match the reconstructed 4-tap horizontal `vec4` formula across all four canonical zooms, and fresh first-dispatch row-plan packets capture all four unique worker regions per zoom with only the middle row-cache segment predicted/live in that dispatch.
  Full-render row-cache segment reachability is now bounded under the canonical quartet: leading/trailing `0x372760` store sites are live at `28mm` and `70mm`, and have zero hits at `35mm` and `150mm` under the tested canonical bridge HDR runs.
- Closure:
  `bundle_static_runtime_iramp_candidate_policy_four_zoom.md` exhaustively
  closes all local projection, record, sentinel, boundary, and continuous-score
  decisions in installed `0x3661b0`. A return-only `t=0` intervention then
  proves final Radiance-file consequence at canonical Unit-1 `35mm` and
  `70mm`, separated from repeated-render floors by `1742.937x` and `3.317x`.
  Joined to complete four-focal score-use and descriptor-to-writer custody,
  this establishes the final policy on profile-3 CLI HDR: surviving
  non-sentinel contributors are continuously weighted, then downstream work
  is image-domain shaping/cache/resample/output with no later per-contributor
  predicate. `CLM-MERGE-005` and `CLM-MERGE-006` are
  `PROVEN`/`SPEC_READY`. Direct differential scope is `35mm`/`70mm`; the
  `28mm`/`150mm` scope is the joined same-mechanism custody/liveness proof.

## Exit Criteria

A blocker may be removed only when:

1. The claim is upgraded in `CLAIM_LEDGER.md`.
2. Zoom scope is explicit.
3. The implementation consequence is clear.
4. The result is usable in `LUMEN_PARITY_SPEC.md` without prose caveats.
