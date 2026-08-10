# Phoenix L16 — TRUTH

**Version**: 3.0.350
**Status**: Canonical root truth rebuilt from admitted claims only. Full clean-room investigation remains active; the earlier checklist-complete state was narrower than the project exit criterion.

## Canonical Authority

- Human-readable root summary: `docs/TRUTH.md`
- Claim-level authority: `docs/canonical/CLAIM_LEDGER.md`
- Merge-critical subset: `docs/canonical/MERGE_CRITICAL_TRUTH.md`
- Active unknowns that still block parity: `docs/canonical/PARITY_BLOCKERS.md`
- Four-zoom validation rule: `docs/corpus/VALIDATION_POLICY.md`
- Audit note for the superseded v2 root truth: `docs/canonical/TRUTH_RECONCILIATION.md`

If this file and the claim ledger ever disagree, the ledger wins.

## Rules

- This file may summarize only claims already admitted into the canonical ledger.
- `PARTIAL` claims stay scope-bound. They do not become closed prose here.
- `0 hits` findings keep their tested-path scope.
- Merge-critical closure requires explicit zoom coverage for `28mm`, `35mm`, `70mm`, and `150mm`.
- Older truth narratives are preserved by git history, not by leaving stale truth in the main path.
- Durable audit/probe evidence must be repo-owned: audit registers under `docs/audits/`, proof docs under `docs/evidence/`, reusable probes under `tools/lldb_probes/`, and rerunnable raw outputs under ignored `runs/`. `/tmp` and `/private/tmp` are not valid long-term evidence locations.

## Objective

The project goal is a formula-level specification sufficient to build a new
application that:

- uses no Lumen code or binaries at build time or runtime;
- accepts an LRI as input;
- independently computes the fully merged image; and
- writes at least one correctly tagged format readable by modern photo apps.

No implementation-required input origin, constant, formula, branch policy,
pixel/color transform, or output encoding may remain unknown. Output quality
must achieve:

- no ghosting
- no trailers
- no contributor misregistration
- correct framing and crop behavior
- stable behavior at `28mm`, `35mm`, `70mm`, and `150mm`

## Full Clean-Room Status

The prior A-E completion checklist closed the requested merge and final-stage
items, but it did not close the whole input-to-output implementation. It must
not be used as an investigation exit criterion.

Version `3.0.350` corrects the former selected-CNR completeness claim. The
admitted RGB/matrix worker, bilateral stages, range-scale construction, and
route remain valid at their stated scopes, but the CNR source tile has a live
fourth lane that Phoenix cannot yet reconstruct. Installed `0x308f50` writes
that lane as `guide^2`; eight Unit-1 `70mm` dispatches all take the data-driven
arm and never the constant-`1` empty-guide arm. The guide is a per-tile,
half-resolution/pixel-doubled image carried by the denoise task at `+0x60`,
and RTTI places its production inside
`lt::Internal::Pipeline::setWhiteBalance::$_22`. Its exact source among that
lambda's `SoftISP::Stats`, `Image<unsigned short>`, and `CapturedImage` inputs,
and the normalization that yields the observed guide values, remain open.
`CLM-DENOISE-002` is therefore `PARTIAL` / `BLOCKER`; substituting lane 3 with
constant `1` or a brightness-correlated proxy is forbidden.

Version `3.0.331` closes selected pattern-2 Skip-mask consumption at levels 4
and 5. A zero mask byte computes the admitted normalized G-42 local cost; a
nonzero byte zeroes that pixel's active `uint16` local-cost vector. Both arms
then execute the same eight-direction G-43 recurrence, accumulate a per-pixel
Cost-volume record, and use the ordinary first-minimum worker to emit an
absolute depth-hypothesis index. Exact-focal Unit-1 and Unit-2 `28mm` captures
prove adjacent mask-`0`/mask-`255` local vectors and nonzero completed records
for both pixels. Pattern 2 therefore sparsifies the photometric unary term,
not the Depth-map output. The later guided 2x upsample consumes an already
complete `2080x1560` index-5 Depth map; it does not fill the three nonzero-mask
positions. Installed proof is body/focal independent, existing receipts cover
pattern-2 selection at levels 4/5 and Unit-1 four-focal mask/argmin liveness.

Version `3.0.330` closes the representation passed from G-42 local matching
into G-43 SGM. G-42's summed `uint16` cost is scaled in place by binary32
`float32((1/27)/source_count)` and converted with truncation toward zero; the
selected five-image route has four projected sources and exact factor
`0.0092592593282461166f`. G-43 reads the resulting `uint16` lanes directly
from the same temporary. There is no per-pixel band-min subtraction between
G-42 and G-43; the later saturating subtraction is the standard prior-path
minimum term inside the admitted SGM recurrence. Installed proof is
body/focal independent, exact raw-to-normalized-to-recurrence replay covers
Unit-1 and Unit-2 exact-`28mm`, and existing G-42/G-43 receipts supply
Unit-1 `28/35/70/150mm` liveness.

Version `3.0.329` closes the omitted `0x298ff0` predecessor-pool formula in
G-40. For levels 1 through 5, Lumen first converts the prior Depth map to its
hypothesis-index descriptor and pools that descriptor over the clamped
asymmetric 4x4 footprint `dx,dy in {-1,0,1,2}`. A source index participates
only when the corresponding prior `Skip mask` byte is nonzero. The outputs are
the surviving minimum and maximum, or `(65535,0)` when no source survives.
The later range-builder samples those tables and separately applies
hypothesis-index padding `1`. This refutes a symmetric radius-2 pool and an
all-pixels pool. Installed-static proof is body/focal independent; exact
five-transition replay is Unit-1 `28mm`, and kernel/liveness receipts cover
Unit-1 `28/35/70/150mm` plus exact-focal Unit-2 `28mm`.

Version `3.0.328` closes the newly demonstrated coarse-level index-5
projection gap. Selected profile-3 mode-8 levels `0..5` have Guidance
dimensions `65x49`, `130x98`, `260x195`, `520x390`, `1040x780`, and
`2080x1560`, with `StereoLayer+0x1c` steps `{32,16,8,4,2,1}`. All five
sampled `Images` remain fixed `2080x1560` products, all four projection-record
scales remain exactly `(1,1)`, and each source's full projection record is
unchanged across levels. For level coordinate `(u_L,v_L)`, Lumen first computes
`u=min(step*u_L+floor(step/2),2079)` and
`v=min(step*v_L+floor(step/2),1559)`, then applies the already-admitted
full-domain float32 correspondence. It does not construct
`H_level=D*H*D^-1` or sample coarse source-image pyramids. Installed-static
proof plus complete exact-focal `28/35/70/150mm` runtime captures on both
physical calibration bodies establish this scope; body-specific coefficients
are not claimed equal.

Version `3.0.327` formula-closes the wide-tier A2/key-`1` public RAW path
feeding `StereoISP::CreateStereoImage`. Exact public-LRI replay uses RAW10,
`SensorCharacterization.black_level/white_level`, the runtime-indexed public
`17x13` vignetting grid at exact `(260,260)` node spacing, and public A1/A2
exposure/analog gain. The normalization is
`f32(f32(raw-black)*f32(1/(white-black)))` with no black clamp; vignetting
uses float32 vertical interpolation followed by the installed double
horizontal multiply/add and float32 conversion. A2's public
`relative_brightness` is bypassed because its admitted
`sensor_bayer_red_override=(-1,-1)` supplies the sentinel-invalid gate, so
the final scalar is the A1/A2 exposure-energy ratio alone. Complete replay
matches all `38,937,600` pixels across canonical Unit-1 `28mm`, independent
Unit-1 `L16_06689`, and exact-focal Unit-2 `28mm`; Unit-2 has distinct RAW,
calibration record ID, vignetting grid, and scale. The next conversion is
exactly `[mono,mono,mono,1]`. Existing Unit-1 `28/35mm` path custody supplies
canonical wide-tier applicability; tele does not invoke this A2 branch.

Version `3.0.326` corrects and formula-closes selected key-0 index-5 Guidance.
The previously admitted collapse2 output `[R,0.5*(G1+G2),B,1]` is the
pre-YUV float intermediate, not the bytes sampled by G-42. Direct installed
call/callback custody proves `CreateStereoImage` invokes
`StereoISP::ConvertToYUV` before its direct byte pack. Public
`LightHeader.sensor_data.type=SENSOR_AR1335(2)` selects installed response
`[0.215550005,0.432307005,0.352142990]`, while each LRI's public
`ViewPreferences.awb_gains` supplies the exact reciprocal matrix input. The
SHA-pinned matrix construction, signed fast-`1/2.2` power, byte-domain
`[0,128,128,0]` offset, forced lane-3 one, and nearest-even/saturating pack
reproduce all 16 matrix words, all `12,979,200` float words, and all
`12,979,200` packed bytes in each of canonical Unit-1 `28mm`, independent
Unit-1 `L16_06689`, and exact-focal Unit-2 `28mm`. Existing four-focal
producer/cost-volume custody supplies `28/35/70/150mm` applicability. Final
Guidance is `[Y,U,V,1]`; the prior exclusion of `ConvertToYUV` and terminal
`[R,G,B,1]` identity are superseded.

Version `3.0.320` strengthens the index-5 correspondence admission with one
direct Unit-1 `28mm` same-render packet. The active mode-8 run captures all
five `CreateStereoImage` descriptors, all four composed projection records,
the complete 752-float ray-depth lookup, and winning indices `25/115/84` at
reference pixels `(1040,780)`, `(520,390)`, and `(1560,1170)`. The installed
formula replays their four source coordinates exactly with no probe errors.
The earlier separate-capture repeat selected `25/116/85`; that one-index
variation is within the admitted index-5 runtime nondeterminism and does not
alter the correspondence formula.

Version `3.0.319` closes the selected profile-3 mode-8 index-5 plane-sweep
correspondence. Reference coordinates `(u,v)` live directly in the
`2080 x 1560` StereoLayer level; no full-resolution factor of two is applied.
The five sampled operands are calibrated-undistorted
`StereoISP::CreateStereoImage` `vec4u8` products, not native/distorted sensor
planes or the separate source-cache RGBA16F undistorted-plane artifacts. For
each non-anchor source, Lumen constructs
`H = (Ksrc4 * [Rsrc|tsrc]) * inverse(Kref4 * [Rref|tref])`, stores
`float32(transpose(H))`, and evaluates
`P = H * [u*d, v*d, d, 1]^T`, where `d` is float32 ray depth in millimeters.
The source sample is `(P.x/P.z + 0.25f, P.y/P.z + 0.25f)`, followed by the
installed clamp, truncation, half-pixel phase, and rounded-byte `pavgb`
    interpolation policy. The fixed G-42 operand is the tier anchor's own
    key-0 Guidance (`A1` wide, `B4` tele), exactly `[Y,U,V,1]` after the
    collapse2-to-`ConvertToYUV` path; it is not a generated multi-camera composite. Formula
liveness is four-focal Unit-1, with the geometry-record mechanism independently
verified on exact-`28mm` Unit-2. The three published Unit-1 `28mm` numeric
examples are deterministic joins of separately completed SHA-pinned captures,
not same-stop runtime observations.

Version `3.0.309` admits the recovered two-body calibration-package corpus.
Calibration signatures prove the user-supplied `Unit 1` / `Unit 2` folder
labels are reversed relative to canonical body names. Each standalone
package's five calibration-role payload digests exactly occurs in every
matching-body new photograph. The public SensorData payload and its exact
`42/1023/2` levels plus 28 VST-row semantics are invariant across all `9,323`
complete old-plus-new photographs spanning both bodies and observed firmware
groups. The package-only zoom files omit distortion and differ from final
geometry at movable-camera `angle_optical_center_mapping`; package-only
HotPixelMaps decode one measurement per camera but are absent from complete
photographs, whose 830 fired-camera records all set `sensor_dpc_on=true`.
Clean-exit Unit-1 `64mm` wide, `71mm` tele, and old-firmware `150mm` runs
record zero hits through the separate installed hot-pixel-leakage route. That
three-run exclusion does not replace the admitted default dynamic hot-pixel
formula or make standalone calibration files required profile-3 inputs. The
new corpus adds 61 wide and 20 tele photographs and no third firing topology.

Version `3.0.315` closes selected editor display index-10 color correction at
tested Unit-1 `28mm` default level-4 scope. Embedded schema and exact-photo
extraction identify the source as body-specific
`ltpb.ColorCalibration.macbeth_data`: both physical bodies carry 42 records
(`14 cameras x A/D65/F11 x 24 patches`) and zero same-camera/type payloads are
equal across bodies. Installed constants and formulas join those public
patches to the fixed Macbeth target, neutral-patch normalization, weighted
least-squares seed, Ceres 1.12 line-search/BFGS/CIEDE2000 solve,
white-normalized endpoint matrix, and periodic 126-control thin-plate-spline
HSV map. A clean-room cost/model exercised through the public Ceres 1.12 API
matches all nine raw and all nine
stored endpoint float32 words. Runtime ownership uniquely selects public
camera `0`, A/type-0 and D65/type-2; distinct reciprocal-temperature helpers
produce exact map alpha `0x3e7aaa6b` and matrix alpha `0x3e7aaa6d`. The live
custom-RGB-to-`linear_prophoto_rgb` conversion plus HSV-map application replays
all `5,101,248` bytes of the retained stage-10 image. This is one display
request, not four-focal merge-critical proof; alternate DOF/cache modes,
profiles `1/2`, other controls/focals/levels, and complete edit semantics
remain reference-only.

Version `3.0.314` closes the selected editor ACRE EV/LUT public-origin gap at
tested Unit-1 `28mm` default level-4 scope. Installed request-builder code
writes `tone_mapping.ev_offset = log2f(f3fc0(CapturedImage))`; the already
admitted public-field formula makes this exactly
`log2f((ViewPreferences.image_integration_time_ns *
ViewPreferences.image_gain) / (CameraModule.sensor_exposure *
CameraModule.sensor_analog_gain))` in float32 order. The retained public packet
replays scale `2.000147819519043` and EV `1.0001065731048584` bit exactly.
Installed schema/dispatch proof separately maps public property
`tone_mapping.type=light_v1` to enum `4`, ACRE curve index `1`, and exact LUT
`libcp+0x5e41b4`. The merged public `ViewPreferences.ev_offset=0` accessor has
zero hits on this run and is not the observed ACRE value. Display index-10
color correction remained open at that checkpoint; version `3.0.315` closes
the selected path. Alternate cache/mode behavior remains reference-only.

Version `3.0.313` closes the selected editor ACRE color-conversion suffix.
Runtime generic-worker custody proves selector tuple `(5,2)` chooses
`0xabf20` and matrix branch `0xac600`, converting fixed
linear-ProPhoto/D50 ACRE output to the live sRGB/D65 display packet. The exact
D50-to-D65 adaptation and runtime-composed 3x3 matrices are captured.
Independent clean-room replay of the generated matrix plus exact fast sRGB
transfer matches all `1,048,576` bytes of the installed post-conversion tile
(`da688132...`). Combined with version `3.0.312`, the complete selected
index-15 operation is formula- and byte-closed at this scope. At that
checkpoint display index-10 color correction, EV/LUT public origins, and
alternate cache/mode behavior remained reference-only unknowns; version
`3.0.314` closes the selected EV/LUT origins.

Version `3.0.312` formula-closes the selected editor ACRE core at tested
Unit-1 `28mm` default level-4 scope. Installed RTTI and runtime custody join
`lt::TMO_ACRE` through `TMO_ACR::process::$_0` worker `0x2d7a30`; the live
object supplies float32 EV `1.0001065731048584` and exact 1025-float LUT at
`libcp+0x5e41b4`. Independent clean-room replay matches all `1,048,576` bytes
of one installed pre-color-conversion `256x256` vec4 tile using the exact
piecewise toe, table interpolation, rank-preserving midpoint reconstruction,
SSE reciprocal approximation, and alpha copy. Full-image stage hashes also
prove live lens-shading and contrast callbacks are exact no-ops on this
request. The following color conversion was selected but not yet replayed at
that checkpoint; version `3.0.313` closes it. Display index-10 color
correction, EV/LUT public origins, and alternate cache/mode behavior remained
reference-only unknowns there; version `3.0.314` closes the selected EV/LUT
origins.

Version `3.0.311` closes the installed editor's immediate default display
route and corrects its queue-record identity without claiming editor/export
pixel identity. A clean-exit Unit-1
`28mm` profile-3 RenderType-1 run exposes a five-level packed pyramid from
`10432x7824` through `652x489`; a hardware write watch identifies
`libcp+0x27e0d0` and exactly replays one live four-float pixel as nearest/even
`sat_u8(255*p)`, with opaque alpha. SHA-pinned installed Lumen proof shows
public `RendererBase::setProperty(ParamInt(10), value)` selects GUI byte
order: normal supported `GL_BGRA` uses `[B,G,R,A]`, while fail-safe/fallback
`GL_RGBA` uses `[R,G,B,A]`; both upload as `GL_UNSIGNED_BYTE`. The live parent
record is type `13`, priority `2`, from `RendererPrivate::requestRenderROI::$_12`;
type `4` is the separate public `Renderer::serialize` route. Installed RTTI and
runtime custody identify float producer `RendererPrivate::$_2` at `0x3bb2b0`.
For the tested default level-4 mode-0 request, equal request/DOF threshold
floats select exact `lt::PipelineCache` at `RendererPrivate+0x688`, followed by
the five-entry per-level Color pipeline vector at `+0x870` and
`0x31b110 -> 0x33fb30`, before packing. Byte-exact captures prove this
in-place call is the complete difference between the tested HDR-writer float
input and editor float image. Its exact active indices are
`3,10,11,12,13,14,15`: default color scaling, `setColorCorrection`, sharpen,
`setLensShading`, `setToneAdjust`, `setContrastAdjust`, and `setToneMapping`.
Display-specific formula/parameter closure for the unclosed callbacks,
alternate DOF/mode behavior, the host-specific active GL branch, and complete
edit semantics remain reference-only unknowns.

Version `3.0.308` partially closes the Lumen editor compatibility boundary.
Installed-app call-graph proof shows `ImageEditor` owns a profile-3 Renderer
and a `DepthEditor` over that exact Renderer; successful depth edits schedule
RenderType-1 pyramid requests. Complete GUI-style coarse-to-fine runs at
canonical Unit-1 `28/35/70/150mm` reach the admitted IRAMP `src1`, `src2`, and
five-contributor wrapper topology, with MonoFusion live only at wide. In one
scoped Unit-1 `28mm` synthetic brush run, the five post-edit requests record
zero IRAMP, wrapper, MonoFusion, stereo-index, or calibration-composition
hits, showing prepared-state reuse for that edit. This does not establish
editor/export pixel identity, every edit formula, or profiles `1/2`.

Version `3.0.307` independently re-extracts the Pile-2 constants and schema
details that had been verified outside the canonical ledger. It records the
full SHA-256 digests for the Unit-1 four-focal shared intrinsics, distortion,
and depth-config payloads; publishes all 28 installed type-3 panchromatic VST
rows as exact float32 words; and proves `packed=true` from installed protobuf
descriptors for four repeated-float calibration fields. Payload equality is
Unit-1 four-focal scope; the VST and schema facts are installed-static. No
Unit-2 payload equality or body/firmware cause is inferred.

Version `3.0.306` closes slot-15 branch incidence for the tested canonical
profile-3 route. Complete Unit-1 `28/35/70/150mm` runs execute `4,684`
equal/copy branches and zero unequal conversions. Complete exact-focal Unit-2
`28mm` adds `1,476` equal copies and zero conversions; an exact-`70mm` Unit-2
tele discriminator joins one positive exact-config equal-path sample to a
separate complete Bayer/BayerFloat mismatch-only zero-hit render. Thus slot
15 is an observed exact no-op on those routes. Generic unequal-selector
formulas, alternate profiles/GUI paths, and body/firmware causation remain
outside the admission.

Version `3.0.305` classifies payload index `15` beyond its misleadingly broad
`setToneMapping` setter name. The Bayer, BayerFloat, and Color wrappers only
compare the current descriptor color config to a fixed singleton and, on
difference, invoke `ImageConvertColorSpace` in place. Installed schema plus
direct installed-constructor execution identify the target as selector-`5`
`linear_prophoto_rgb`, D50 white, the exact ProPhoto RGB-to-XYZ float32
matrix, and adaptation mode `1`. Matching configs select `0xab940`, build an
exact identity adaptation, and preserve negative/HDR RGB plus lane 3 bit for
bit. Therefore no fitted nonlinear look/tone curve belongs at this slot.
Existing Unit-1 `28/35/70/150mm` target sets establish wrapper liveness;
at that version, actual equal/unequal branch incidence and unequal
source-config distribution remained open. Version `3.0.306` closes incidence
for the tested profile-3 routes above.

Version `3.0.304` adds the previously floating clarity placement. Installed
`Pipeline::setToneAdjust` RTTI, record placement, and call edges put
Laplacian clarity at fixed index `13` for Bayer, BayerFloat, and Color: after
index-11 Lab-L sharpen and index-12 lens shading where present, before
index-15 tone mapping. The shared clarity body is runtime-live on Unit-1
`28mm`; variant placement is installed-static and focal/body independent.

Version `3.0.303` closes per-payload callback/dependency order. The installed
`Pipeline` uses a fixed sixteen-record permutation, and each Bayer,
BayerFloat, or Color loop invokes populated callbacks in ascending index.
Public setter RTTI gives exact stage identities. Wide Color is `AWB/color
scale -> CNR -> adaptive desaturation -> denoise -> Lab-L sharpen -> tone
map`; tele Color is zero-hit under the scoped Unit-1 gated runs, while tele
BayerFloat inserts CNR/adaptive/denoise after demosaic and before sharpen.
Bayer's complete eleven-stage order and both BayerFloat orders are in the
admitted bundle. This is lazy descriptor-dependency order beneath the visible
source producer, not an eager global pixel timeline. Runtime target sets cover
Unit-1 `28/35/70/150mm`; no Unit-2 or body/firmware cause is claimed.

Version `3.0.302` closes the public unsharp packet and exact kernel-width
policy. The constructor packet is copied directly as
`(sensor_analog_gain, grain_power, grain_sigma, sharpening,
sharpening_scale)`; it is not generated by an image-local seven-way selector.
Public `vibrance` chooses one of three surrounding helpers at exact float32
thresholds around `1`, but every helper passes the same packet when
`sharpening > 1e-6`. Installed `0x35f5c0` reads gain, sharpening, and scale:
gain selects exact piecewise base-width curves; sharpening is both the Lab-L
DoG amount and a clamped width interpolation over `4..16`; scale multiplies
both Gaussian sigmas. The exact float32 formula and 3/5/7-tap thresholds are
in the admitted evidence bundle. Retained constructor censuses cover Unit-1
`28/35/70/150mm`; complete generated-kernel/sigma replay is Unit-1 `28mm`.

Version `3.0.301` closes the generated selected-denoise `range_scale` image.
The same payload field proven at demosaic as public reciprocal
`ViewPreferences.awb_gains.{r,g_r,b}` enters `0xefa50`; public per-capture
`CameraModule.sensor_analog_gain` selects a lower-bound row from the installed
28-row RGB SensorGainVars table. In exact float32 order, source RGB is
normalized by installed black/white `42/1023`, evaluated through installed
`red/green/blue.{a,b}`, floored at variance `1e-5`, square-rooted, and then
propagated as independent variance through the fixed Ohta matrix. The second
stage square-roots again and applies floor `(0.0025,0,0,0)`. Preserve both
sqrt/square stages for parity. Installed bodies and constants are SHA-pinned;
`0x2f4470` is live at all four canonical Unit-1 focal tiers, all retained
Unit-1 four-focal and exact-35mm Unit-2 config packets carry exact
`0.0025f`, and final selected range-scale custody is replayed on two bodies.
Installed SensorGainVars numeric rows are not LRI-public rows.

Version `3.0.298` closes the non-anchor `CreateStereoImage` affine-fit
formula. Samples with `C3>0.95f` feed separate float32 Welford means and
second moments; each population covariance uses an explicitly rounded
float32 `1/count` and multiply, then promotes to double and adds `0.001 I`.
With lower Cholesky factors, the exact transfer is
`A=chol(cov_target)*inverse(chol(cov_source))` and
`b=mean_target-A*mean_source`; fewer than 100 valid samples on either side
returns identity. The selected caller initializes both surrounding 3x3
matrices to identity. A retained Unit-1 `28mm` A5-to-A1 packet replays all
sixteen emitted float32 matrix words exactly. Installed formula proof is
focal/body independent and prior four-focal `CreateStereoImage` custody
supplies route applicability; coefficients remain per-image data-derived,
with no body or firmware cause claimed.

Version `3.0.297` closes the public movable-mirror constructor formula. The
live public `CameraModule.mirror_position` enters the type-0 normalized
quadratic inverse from `MirrorActuatorMapping`; all packets in both observed
physical calibration signatures set both segment flags false and select
`r_minus`. Public `MirrorSystem` fields then produce the reflected camera as
`R = F * Q^T * (I-2nn^T)` and `t=-R*C`, where `F` is the exact
`flip_img_around_x` row-sign convention. Unit-1 retained `28/35mm` packets
match final float32 `R,t` bit-for-bit for movable B1/B2/B3/B5; dedicated
Unit-1 `70/150mm` runs match all eight movable B/C cameras with zero public
and angle error, at most `3.73e-14` double pose error, and bit-exact float32
copies. Exact-focal Unit-2 `70mm` repeats all eight under the second
calibration signature. The geometric movable set is
`B1,B2,B3,B5,C1,C2,C3,C4`; selected tele B4/C5 are fixed. Type 1, later
current-bank adjustment, and body/firmware causation remain outside scope.

Version `3.0.296` closes the supported profile-3 focal/topology exceptions.
Two complete `28mm`/tele LRIs spanning both physical calibration signatures
execute the tele stereo/range/upsample route, use direct C1..C5 IRAMP
contributors, clear C6, apply tele scale and public 150mm crop, and complete
HDR. The Unit-2 `74mm`/wide exception executes A1/A2 MonoFusion mode 0,
family-A scoring, direct B1..B5 IRAMP contributors, wide scale, and the public
35mm-family crop. A Unit-1 mode-1/family-B exception has zero live scorer
calls in its completed run and stays scope-bound. Full-corpus selectors were
rechecked over all `9,242` complete LRIs without assigning body/firmware
causation.

Version `3.0.295` closes the forward RGB-to-I1/I2/I3 application points.
Direct contributors are transformed after their `0x374ac0` materialization;
cropped `src2` is transformed before `0x36b920` patch preparation. Both use
exact float32 `I1=a(R+G+B)`, `I2=b(R-B)`, and `I3=cR-dG+cB`, preserve lane 3,
and load `a=0.5773500204086304`, `b=0.7071099877357483`,
`c=0.40825000405311584`, and `d=0.8165000081062317`; the inverse uses the
transpose. Installed proof is body/focal independent, live Unit-1 `28mm`
captures both roles, and existing reports reverify route liveness at all four
canonical focal tiers.

Version `3.0.294` closes G-38's undistort-envelope builder. Public
Brown-Conrady polynomial and CRA pixel-scale inputs produce 30 radial samples;
the installed four-point cubic maps distorted pixel radius to undistorted
radius. The builder sweeps left/right edges at 91 vertical samples and
top/bottom edges at 121 horizontal samples, takes the inner valid extrema, and
uses float32 SSE truncation to form the half-open integer box. Clean-room
replay matches 20 canonical Unit-1 boxes across `28/35/70/150mm` plus five
exact-`70mm` Unit-2 boxes. Exact Unit-1 A1 and Unit-2 B4 4096-entry
distortion tables and all 20 retained four-focal RGBA16F undistorted reference
planes reverify. The downstream uniform scale/origin formula was already
admitted; no public field name is assigned to this derived envelope and no
body/firmware cause is claimed.

Version `3.0.293` closes G-37's focus-dependent intrinsics bracket policy.
The installed `0x1f96e0` helper stably sorts public
`per_focus_calibration[].focus_hall_code` values, carries the corresponding
`intrinsics.k_mat` indices, and evaluates K fields `{0,2,4,5}` at live
`CameraModule.lens_position`. One record copies directly; two records use
the sole pair for interpolation or extrapolation; three records use pair
`(0,1)` when `x<h1` and pair `(1,2)` otherwise, with no endpoint clamp.
The exact implementation evaluates float32 slope/intercept form and rejects a
selected Hall separation below `0.001`. Every camera in eight exact-focal
`28/35/70/150mm` LRIs spanning both physical calibration signatures carries
exactly two records, correcting the handoff's three-bundle premise. Retained
complete Unit-1 four-focal runtime packets replay that observed branch
bit-for-bit; the one/three-record policies are installed static proof, with no
three-record corpus incidence claimed.

Version `3.0.292` closes G-49's local IRAMP sub-pixel refinement formula. A
row-major `3x3` integer SAD neighborhood feeds a coupled two-variable
quadratic solve, not two independent parabolic fits. The installed body
conditionally removes only the cross term when its preliminary determinant
is non-positive, recomputes the denominator, returns `(0,0)` on exact zero,
and otherwise solves both offsets in float32. It retains the pair only when
both strict guards satisfy `abs(offset)<1.0`; failure resets both to zero
rather than clamping. All 96 captured Unit-1 `28/35/70/150mm` packets replay
bit-for-bit and cover zero-denominator, accepted, and unit-guard-rejected
branches. Installed formula scope is body/focal independent; no Unit-2 G-49
packet is claimed.

Version `3.0.291` closes G-40's selected mode-8 per-level hypothesis
construction. Level 0 seeds every pixel with lower index `0` and the complete
reciprocal ray-depth lookup extent. Levels 1 through 5 generate per-pixel
`(lower,count)` Range-map records from the prior Depth map / Skip mask, track
the maximum upper endpoint, and commit
`ceil(max_pixel_upper/8)*8` as the global active extent. Stable Unit-1
`28/35/70/150mm` producer-store captures observe respectively
`[752,632,272,256,256,256]`, `[752,752,752,752,752,752]`,
`[1472,1408,1392,1328,1200,1152]`, and `[1472,48,48,48,48,48]` across
levels `0..5`. Those sequences are scene observations, not constants; a
clean-room implementation computes them per input. Installed formula scope is
body/focal independent, and prior exact-focal Unit-2 `28mm` proof validates
the same range-builder formula; no Unit-2 per-level commit packets are
claimed.

Version `3.0.290` closes G-43's selected SGM direction and initialization
policy. Each signed sweep evaluates four paths. The positive predecessors are
`(-1,0),(-1,-1),(0,-1),(1,-1)` and the negative sweep uses their opposites,
so the selected route is eight-path SGM, not the four-path placeholder. Fully
censused `35mm` wide and `70mm` tele levels execute all positive tasks before
all negative tasks; tasks inside a sign group remain executor-parallel. The
complete two-half `Line buf` and `Min cost buf` allocations initialize to
`u16 2000`, `Pixel buf` initializes to zero, and eight path outputs aggregate
with saturating-u16 addition. Installed proof is focal/body independent and
prior worker liveness covers Unit-1 `28/35/70/150mm`; no Unit-2 G-43 packet is
claimed.

Version `3.0.349` explains why repeated stock-Lumen depth maps differ. The
installed G-43 payload accumulation at `0x277a06..0x277a15` is a non-atomic
shared saturating-u16 RMW. Different pthreads write the same exact payload
address at every canonical focal tier, and a Unit-2 `70mm` overlap run records
nine simultaneously active workers on the exact index-5 StereoLayer object.
This is a concrete executor data race, not Skip-mask randomness,
uninitialized G-43 scratch, or a floating-point reduction. A separate
Unit-2 parent-gate repeat also shows pre-G42 executor-order sensitivity as a
key-6 valid candidate (`score=0.8023583889`, side `0`) versus exact reject
sentinel (`score=15`, side `1`); the first unsafe instruction in that upstream
producer is not claimed. Forcing generic executor `0x2d30` through its
installed ascending fallback stabilizes all captured pre-G42 operands and
produces byte-identical `2080x1560` maps in two Unit-1 `28mm`, two Unit-1
`150mm`, and three Unit-2 `70mm` repeats. Thus the observed depth
nondeterminism is scheduler-induced and suppressible. A clean-room build must
use deterministic task order or private path accumulators with fixed-order
reduction rather than reproduce Lumen's race.

Version `3.0.289` closes G-42's selected index-5 plane-sweep operand pairing
and local-cost metric. Every source `k` is projected and bilinear-sampled as a
3x3 byte patch, then compared with the fixed unprojected `Images[0]` /
Guidance anchor patch, A1 wide or B4 tele. Per-channel absolute differences
are capped by `(2,6,6,0)`, saturating-u16 summed over nine samples, multiplied
by the per-source four-lane weight table, rounded by `+16`, shifted right by
five, horizontally summed, and capped at `65535`; each resulting source cost
is then added to the Cost-volume `u16` modulo `65536`. Unit-1 `28/35/70mm`
packets replay bit-for-bit, while installed proof is focal/body independent
and the prior exact-body route census supplies `150mm` liveness. At that
version, the SGM direction census and per-level hypothesis construction were
still separate; versions `3.0.290` and `3.0.291` close them for the selected
route. Rare supported-input compatibility remains separate.

Version `3.0.288` closes G-61's remaining Laplacian-clarity construction and
tonal-shaping math. The installed total-plane rule is
`clamp(trunc(log2(min(W,H))-2),2,6)`. Gaussian reduction uses exact float32
kernel `(0.05,0.25,0.4,0.25,0.05)` with edge-clamped stride-2 sampling;
expansion uses exact parity weights, stores negative details
`Expand(G_next)-G`, and reconstructs by `Expand(R)-detail`. The five public
shadow/highlight/percentile fields drive exact log-sample envelopes, with
`shadows=highlights=1` neutral. Two complete Unit-1 `28mm` read-watch renders
prove every field consumer live. The retained 543-square packet produces six
total planes and callback detail levels `0..4`, exactly matching the static
rule. Formula scope is installed static same-mechanism; runtime liveness is
Unit-1 `28mm`.

Version `3.0.287` closes the selected unsharp worker formula and domain.
Installed `SharpenLineFactory<float>` modifies only the CIE Lab `L*` scalar
plane as `L + clamp(amount*(G_positive(L)-G_negative(L)),-20,20)`. The amount
is constructor field `+0x0c` copied to object `+0x68`; complete four-focal
constructor censuses observe configured amounts `{0.5,1.0}`, and the first
live worker packet at every tier uses `1.0` and replays bit-for-bit. A complete
Unit-1 `28mm` census captures the exact generated 3/7-tap kernels for all seven
observed constructor families. Public `sharpening` and `sharpening_scale`
reach the parent render packet; the downstream image-local packet-selection
rule remains outside this admission.

Version `3.0.286` closes the selected PatchNLM weight formula. The installed
callback sums componentwise absolute differences over sixteen `vec4` patch
samples, reduces that four-lane sum to scalar `D`, and applies the
componentwise tent `w=max(0,1-max(0,D-V)*rcpps(V))` with
`V=16*coefficient*range_scale[pixel]`. It accumulates `w*source` and `w`,
normalizes RGB with an unrefined packed reciprocal, and restores lane 3 from
the preserve source. The caller constructs
`coefficient=strength*(1,config+0x0c,config+0x0c,1)`; accepted Unit-1 28mm
runtime gives `(1.4,2.8,2.8,1.4)` and exactly replays a sloped live packet.
The formula is installed-static same mechanism; prior route census supplies
Unit-1 four-focal and exact-35mm Unit-2 liveness.

Version `3.0.255` admits the raw input boundary:

```text
4160 x 3120, row stride 5200, RAW_PACKED_10BPP
surface offset = 32 + slot * 0xf7a000
pixel[i] = (little_endian_80bit_group >> (10*i)) & 0x3ff
```

Exact-focal representatives from both calibration bodies establish the raw
block partitions and stable public Bayer/mono phase map. Installed decoder
proof is body/focal independent; direct runtime corroboration is Unit-1
`28mm`.

Version `3.0.256` first admitted the `DemosaickLightV1` residual-interpolation
structure. Version `3.0.344` corrects its local-replay interpretation and
provides full-frame closure. The supplied RGB gains are applied on the public
CFA phase. Source reads use phase-preserving endpoint extension; derived guide
rows remain virtual. A 21-tap green-site `P` guide feeds a first four-direction
correction at red/blue sites (`H=P` at green), then a refined four-direction
correction at green sites (`A=H` at red/blue). `P/H/A` use finite halos of
four/three/one pixels. Residual `B=S-A` has virtual vertical rows and asymmetric
horizontal guards. Channel-matched residuals are inverse-gradient interpolated
and added to `A`. The stabilizers are `max_gain/1024` and
`max_gain*5/512`; output is RGBA float32 with alpha `1`. Installed code uses
unrefined SSE reciprocals and instruction-ordered float32 reductions. Exact
clean-room replay matches all `51,916,800` RGBA words on each physical unit at
exact-`28mm`; public phase carriers cover both bodies at all four focal tiers.

Version `3.0.257` admits the public white-balance origin and decode. Complete
LRIs carry `ViewPreferences.awb_gains.{r,g_r,g_b,b}` either as a legacy direct
LELR payload or at `LightHeader.view_preferences`. All `9,242` structurally
complete local inputs have `g_r==g_b`; the gain-bearing message omits
`awb_mode`, while the separate merged preference tail explicitly supplies
`AWB_MODE_AUTO (0)`. The `196` no-message files all have unclosed/corrupt
LELR streams. The renderer uses float32 `(1/r,1/g_r,1/b)` without
interpolation at both the demosaic and post-square consumers. Runtime joins
cover Unit-1 `28/35/70/150mm` and exact-focal Unit-2 `28mm`.

Version `3.0.258` admits the exact separable four-tap resampler. Its
`64 x 4` float32 table is the Catmull-Rom cubic-convolution kernel at
`t=p/64`, with source taps `floor(x)-1..floor(x)+2`; signed 16.16 coordinates
select phase `(fixed>>10)&63` and clamp source indices at image boundaries.
The instruction-ordered 4096-byte table has SHA-256
`a5e2489fcfbf711cfec05d3ae2b165f970aec02d8d72a2c7c61bdb43ac174b9f`
and matches a complete runtime capture byte for byte. The selected-cache
caller derives scale as selected-level pixels per requested pixel and offset
as the requested source origin relative to a two-pixel-expanded temporary
ROI; these are derived operational values, not missing public fields.

Version `3.0.259` admits the exact public distortion path. Public
`Distortion.Polynomial.coeffs` are ordered `[k1,k2,p1,p2,k3]` and evaluated
as five-coefficient Brown-Conrady in coordinates normalized by public
`distortion_center` and `normalization`. Public
`Distortion.CRA.pixel_size` converts integer pixel radius to physical sensor
radius. Thirty float32 correction samples at `0.1` spacing feed four-point
cubic Lagrange interpolation into the 4096-entry radial factor table
`1+correction/radius`; the consumer truncates and clamps its radius index to
`0..4095`. Unit-1 A1 and Unit-2 B4 tables replay byte for byte from their
different public calibration payloads. Public carriers were checked at all
four exact focal tiers on both bodies; `Polynomial.valid_roi` is not retained
or consumed by this table path.

Version `3.0.260` admits the first quantitative reference-validation floor.
Ten complete final-output repeats at each canonical Unit-1 focal tier produce
180 pairwise measurements. Their decoded-output class counts are `2`, `5`,
`10`, and `5` at `28/35/70/150mm`; maximum normalized linear-RGB RMSE is
`0.0109204`, `0.0109248`, `0.0423124`, and `0.0130886`, respectively. The
repeat distribution is focal-dependent and refutes the old unqualified
`~0.034 counts` floor. This is a `PARTIAL` admission: undistorted-plane
references and complete depth/disparity maps remain open.

Version `3.0.261` admits the exact canonical CLI Radiance writer. Finite
float32 RGB is converted with `frexp(max(rgb))`, float32 scale
`fraction*256/max`, truncating clamped channel products to RGB bytes and
storing `exponent+128`; negative channels clamp to zero. The file is
`10432x7824`, top-down and left-to-right, with a legacy flat four-byte RGBE
body despite the `32-bit_rle_rgbe` header label. macOS ImageIO reads the
result. The parent output claim remains `PARTIAL` because the emitted file
does not self-tag its proved linear-ProPhoto primaries and alternate final
image placement has not yet been excluded.

Version `3.0.262` admits correction-stage liveness and the public calibration
boundary. Every canonical focal tier executes all installed
`RemoveVignettingGeneric` specializations and the public-data constructor.
`FactoryModuleCalibration.vignetting` publicly contains a `17x13` grid of
4x4 `crosstalk` matrices and one or four hall-code-keyed `17x13` scalar
vignetting profiles. The constructor clamps or brackets public
`CameraModule.mirror_position`, float32-interpolates the 221 profile values,
and the row worker
bilinearly samples the shaped profile to multiply image lanes. This remains
`PARTIAL`: exact profile shaping, crosstalk application, and IR-model table
roles are not yet formula-closed.

Version `3.0.263` excludes cross-talk pixel application from the tested
canonical profile-3 quartet. All four RTTI-proved
`RemoveCrossTalkGeneric<{vec4x32f,float},{false,true}>` row workers record zero
hits in complete `28/35/70/150mm` renders, even though cross-talk property
reads occur. This is a path-scoped exclusion, not a binary-wide claim.

Version `3.0.264` admits exact public vignetting-profile construction.
`CapturedImage+0x60` selects `LightHeader.module_calibration[]` by vector
position, while public `CameraModule.mirror_position` selects or brackets its
hall-code models. Interior interpolation preserves upper-relative float32
arithmetic `t=(h-h1)/(h0-h1)` and `V=t*V0+(1-t)*V1`; shaping is
`S=(V-1)*m+1`, optionally divided by `V`. Twenty-four complete `17x13`
runtime profiles from Unit-1 `28mm` and Unit-2 `70mm` replay byte for byte.
The calibration-record order differs across the bodies and must not be
replaced by a `camera_id` lookup. Exact row-coordinate/bilinear replay remains
the correction blocker.

Version `3.0.265` closes canonical sensor/optical correction. The installed
row workers sample the shaped profile on the mapped `(16,12)` interval grid;
a stopped vec4 store replays the float32/double bilinear factor and RGB
products exactly while preserving alpha. Combined with four-tier liveness,
two-body public-profile replay, and four-tier zero hits at every concrete
cross-talk worker, `CLM-CORRECTION-001` is `PROVEN` / `SPEC_READY`.

Version `3.0.266` closes the complete LELR input contract. Installed record
types are `0=LightHeader`, `1=ViewPreferences`, and `2=GPSData`; partial
preferences merge field-by-field in file order. All `9,242` structurally
complete local LRIs use only those public schemas and carry raw, geometry,
vignetting, sensor, color, device, preference, and GPS roles; the other `196`
files are structurally incomplete. Four-focal runtime joins replay public
crop and exact float32 exposure-target scale
`(image_integration_time_ns*image_gain)/(sensor_exposure*sensor_analog_gain)`.
Flash calibration is not copied into CaptureStack image state, and GPS is
metadata-only on the tested HDR route. The direct/wrapped preference split is
firmware-era layout, not body causation. Non-normal final orientation remains
an output-placement validation item.

Version `3.0.267` closes public orientation placement for every value present
in the complete local corpus. Installed `TransformImpl` maps values `1/2` to
opposite 90-degree affine transforms, preserves the landscape
`10432x7824` writer canvas, and emits full selected-level ROI
`[0,0,8320,6240]`. At that level,
`sx=float32(6240/10432)` and `sy=float32(8320/7824)`; clockwise destination
coordinates map to `(sy*y-2^-13, 6240-sx*x)`, while counter-clockwise maps to
`(8320-sy*y, sx*x)`. Exact-35mm runtime on Unit-2 clockwise and Unit-1
counter-clockwise carries those matrices unchanged through
`CIAPI::Renderer::writeImage` and final helper `0x4182a0`. The remaining
output blocker is a correctly tagged modern export for the proved
linear-ProPhoto pixels, not final placement for supported profile-3 inputs.

Version `3.0.268` closes the output contract. The installed compact
RGB-to-XYZ matrix at `0x5aae20` independently yields ProPhoto primaries and a
D50 white point. A deterministic independent ICC v4 with linear RGB TRCs is
embedded in a classic little-endian TIFF carrying contiguous three-channel
IEEE float32 RGB, top-left orientation, and no transfer encoding or
quantization. Negative and greater-than-one fixture values round-trip bit for
bit; `tifffile`, `tiffinfo`, `exiftool`, ImageMagick, and macOS ImageIO all
accept the file and its profile. `CLM-OUTPUT-002` is therefore `PROVEN` /
`SPEC_READY`; the exact Radiance route remains a byte-parity reference while
tagged float TIFF is the admitted modern output.

Version `3.0.269` narrows `CLM-DENOISE-002` to a partial admission. Unit-1
`28/35/70/150mm` profile-3 bridge-HDR route census proves the live
`setDenoising` split (`0x345c80` wide, `0x345ae0` tele, shared
`0x345920/0x345a10`), the live algorithm chain
`0x2f53d0 -> 0x2f6420 -> 0x2fb320`, `0x3066d0`, `0x3070a0`, `0x3070e0`,
`0x307d90`, and CNR families `0x34b970` wide / `0x34b8a0` tele into
`0x34b3f0 -> 0x307ee0 -> 0x308520 -> 0x3085a0` with args
`(1.0,1.0,42,1023)`. Exact-35mm Unit-2 validates the wide family but uses low
endpoint `43` and additionally hits sibling `0x2fd070`. At that version, the
CNR formula, public parameter origins/names, and `0x2fd070` selector remained
blocking.

Version `3.0.270` strengthens that partial CNR admission. SHA-pinned static
inspection plus Unit-1 `28/35/70/150mm` and exact-35mm Unit-2 runtime replay
prove the live `0x3085a0` worker envelope: source-tile second moments and
lane-3 products feed a noise/shaping vector from `low_endpoint/1023`,
reciprocal-power-of-four `levelVar`, and four internal CNR vectors; `rsqrtps`
normalizes the 3x3 helper-input matrix; the final store is
`q' = q0*row0 + q1*row1 + q2*row2` with alpha zero. Unit-1 uses low endpoint
`42`, and exact-35mm Unit-2 uses `43`. At that version, `V10..V40` were
still anonymous, alongside the clean-room internals of
`0x309270 -> 0x309d50` and the Unit-2 `0x2fd070` selector.

Version `3.0.271` closes the CNR vector-origin gap. `V10` is reciprocal
public `LightHeader.view_preferences.awb_gains.{r,g_r,b}` with alpha `1`, and
`V20` is the derived reciprocal square. `V30` and `V40` are installed RGB
SensorGainVars `red/green/blue.{a,b}` selected by public
`LightHeader.image_reference_camera -> modules[].sensor_analog_gain` through
`int(float32(gain * 100.0))` lower_bound row selection. Unit-1
`28/35/70/150mm` selects installed row `100`; exact-35mm Unit-2 selects row
`400`. The tested LRIs carry public type-2 rows with matching schema names,
but those public row values are not byte-equal to the live installed
coefficients. Remaining CNR blockers are the clean-room internals of
`0x309270 -> 0x309d50` and the Unit-2 `0x2fd070` selector.

Version `3.0.272` closes the CNR matrix-helper gap for the live path.
SHA-pinned static proof plus Unit-1 `28/35/70/150mm` and exact-35mm Unit-2
runtime samples prove helper mode `0x14` is a 3x3 two-sided SVD equivalent:
the helper output blocks `A` and `B` are orthonormal, singular values `S` are
nonnegative and descending, and the input reconstructs as
`transpose(B) * diag(S) * A`. Runtime proof covers 18 helper samples with
maximum reconstruction error `2.79e-09` and independent singular-value error
`1.86e-09`. The only remaining CNR blocker is the Unit-2 exact-35mm
`0x2fd070` sibling-arm selector.

Version `3.0.273` closes that selector-cause gap without over-promoting the
callback-family formula. SHA-pinned installed proof shows `0x2f6420` is a
bilateral-kernel-size dispatcher: on the observed `r9b=0` table, kernel size
`5` selects callback address point `0x65a768` / worker `0x2fb320`, while
kernel size `9` selects address point `0x65a868` / worker `0x2fd070`. Fresh
exact-35mm two-body runtime discriminators show Unit-1 samples stay on helper
kernel `5` and `0x2fb320`, while Unit-2 samples include helper kernels `5`
and `9` and the `0x2fd070` worker returns through the selector's kernel-9
case. The Unit-2 extra arm is therefore a parameterized kernel-size
selection, not an unexplained body/firmware route fork. The remaining denoise
question for clean-room parity is the exact selected bilateral callback-family
formula/field roles for the `0x2fb320` and live `0x2fd070` siblings, unless a
future proof excludes that helper family from final image consequence.

Version `3.0.274` closes the selected bilateral formula and callback roles.
The selected `r9b=0` workers use radius `2` at `0x2fb320` and radius `4` at
`0x2fd070`. Callback `+0x08` is the per-pixel range-scale descriptor, `+0x10`
the source descriptor, `+0x18` the destination descriptor, and `+0x20` the
coefficient vector. For each uniformly weighted square neighbor, the worker
uses the maximum absolute RGB difference, a componentwise tent against
`coefficient*range_scale[p]`, a float32 `1e-6` weight floor, and packed
unrefined `rcpps` normalization; expanded out-of-bounds source samples are
zero-filled. SHA-pinned static proof plus 24 complete two-body post-store
samples replay the formula with maximum output delta `0.000453353` from the
deterministic exact-division surrogate. Prior runtime proof supplies Unit-1
`28/35/70/150mm` liveness and final-store coverage; direct full-neighborhood
replay is Unit-1 `35mm` plus exact-35mm Unit-2. `CLM-DENOISE-002` is
`PROVEN` / `SPEC_READY` for this admitted stage scope. The generated
range-scale origin remained outside version `3.0.274` and is closed by version
`3.0.301`; other anonymous upstream configuration custody, if
image-relevant, remains governed by `CLM-STATE-001`. Neither admission assigns
protobuf names to internal callback fields or generalizes unobserved
kernel-size arms.

Version `3.0.275` closes the selected index-5 Skip-mask population policy.
A fresh Unit-1 `28mm` receipt proves `StereoLayer` index 5 selects installed
`sampling_pattern = 2`; a focused worker capture proves 768 distinct tasks on
an exact 32-by-24 grid, step `2`, with `64 x 64` interior tiles and explicit
right/bottom edge tiles. The builder fills `0xff`, each task independently
seeds standard MT19937 with `5489`, and two `[0,1]` draws choose one zero byte
per 2x2 cell. A clean-room replay equals all `3,244,800` bytes of the captured
Unit-1 `28/35/70/150mm` masks, with 811,200 zeros, 2,433,600 `0xff` bytes, and
SHA-256 `1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba`.
`CLM-STEREO-001` remains `PARTIAL` / `BLOCKER` for Guidance
component semantics and exact disparity-direction lane convention; this
admission does not invent polarity names or generalize unselected patterns.

Version `3.0.276` closes the index-5 disparity/hypothesis lane convention.
Across all 67 accepted Unit-1 four-focal recurrence packets, the two
predecessor `Line buf` pointers differ by four bytes and their overlapping
words agree. The installed shift/blend therefore assembles unpenalized current
`d`, while `P1` is applied exactly to `d-1` and `d+1`. Sampled records use
hypothesis step `1`; increasing index follows the admitted reciprocal-spaced
lookup from `640000 mm` toward `200 mm`. Consequently `d-1` is farther/lower
inverse depth and `d+1` is nearer/higher inverse depth. `CLM-STEREO-001`
remains `PARTIAL` / `BLOCKER` only for Guidance component semantics.

Version `3.0.277` corrects the Guidance component-route operand identity.
SHA-pinned sole-caller and callee proof shows that the live `0/0` and `4/0`
pairs are source/anchor camera keys resolved through the same `state+0xe0`
CapturedImage map, not output color-space selectors. The Unit-1 `28mm` calls
are therefore A1/A1 direct pack and A5/A1 fitted three-channel color match.
The installed `output color-space` schema is a separate static fact and does
not name the live Guidance components. The sampled direct A1 route and its
key-`0` custody remain valid; `CLM-STEREO-001` remains `PARTIAL` / `BLOCKER`
for exact `C0..C2` semantics and universal `C3=1`.

Version `3.0.278` closed the then-observed collapse2/configuration gap. Complete Unit-1
four-focal property captures plus exact-focal Unit-2 `28mm` select
`demosaicking.type=collapse2`, `hot_pixel_removal.type=default`, native white
point, and no output color-space/color-correction/tone/denoise stage. Pinned
all-phase E3 workers prove the pre-YUV intermediate is exactly
`[R, 0.5*(G1+G2), B, 1]`. Version `3.0.326` supersedes the old terminal-pack
interpretation by proving the following inlined `ConvertToYUV` stage. The live default hot-pixel pre-stage is
load-bearing; focused installed/runtime proof closes its rank-6 statistic,
`residual > 4*Bayer-noise-LUT[candidate]` marker threshold, `0x8000` marker
encoding, and final two-branch spatial isolation predicate. The remaining
`CLM-STEREO-001` blocker is narrower: exact coordinate neighborhoods for both
rank residual stages remain open. No four-focal hot-pixel formula closure is
claimed.

Version `3.0.279` closed the `0xed830 -> 0xee510` Bayer noise-LUT generator.
Double-precision clipped-Gaussian shaping from installed `SensorGainVars`
`{a,b}` is followed by float32 black/cliff linear extension and white-level
scaling. The clean-room replay uniquely selects installed gain row `150`,
maps live lanes `[green,blue,red,green]`, and equals all `4096` captured
float32 words bit-for-bit. At that checkpoint, the focused-patch interpretation
incorrectly treated two apparent rank residuals as the remaining gap; version
`3.0.333` supersedes that interpretation.

Version `3.0.280` recorded a focused-patch formula and promoted
`CLM-STEREO-001` to `PROVEN` / `SPEC_READY`. Complete-frame runtime capture in
version `3.0.333` refutes that promotion: the worker forms one rolling-row
rank residual, and the earlier apparent second residual was not a serial
filter stage. The `3.0.280` status is historical only.

Version `3.0.333` corrects that focused-patch interpretation. Complete
Unit-1 exact-28mm A2 pre/post capture proves the worker forms one rank-6
residual per rolling source row, not two serial residual filters, and selects
the isolation branch with `(y&1) XOR (phase_x XOR phase_y)`. Version `3.0.335`
closes its former boundary residual: `0x178b0` supplies a six-pixel halo by
projecting out-of-frame coordinates to the nearest same-parity edge coordinate
and taking the upper median of available same-CFA `3x3` lattice samples at
offsets `{-2,0,2}`. Complete Unit-1 exact-`28mm`, Unit-2 exact-`28mm`, and
Unit-1 canonical-`35mm` replays match all `12,979,200` output words per run,
over three distinct LUT payloads and correction populations. The installed
formula is phase-parametric; prior four-focal liveness supplies selected tele
applicability, while canonical tele does not construct MonoFusion.
`CLM-STEREO-001` is restored to `PROVEN` / `SPEC_READY` for the selected
profile-3 route; unselected SoftISP/sampling-pattern/profile arms remain
compatibility scope.

Version `3.0.281` admits complete stage-reference artifacts. Installed RTTI
and cache custody identify `SourceImageCache`'s completed public-camera-keyed
undistort boundary; canonical Unit-1 captures provide 20 complete RGBA16F
planes for B1..B5 at `28/35mm` and C1..C5 at `70/150mm`. A second complete
`28mm` run reproduces all five plane sizes and hashes byte-for-byte. Complete
four-focal captures also provide the index-5 `2080x1560` hypothesis-index and
depth maps, `4160x3120` guided-upsampled depth, and `10432x7824` final GDepth.
Same-route repeats refute a single deterministic depth-map golden: `35mm` is
byte-identical, `28mm` differs locally, while `70mm` and `150mm` settle into
radically different complete finite solution classes. `CLM-VALIDATION-001`
remains `PARTIAL/BLOCKER`, now narrowed to intermediate-map repeat-class
characterization and an acceptance policy rather than missing artifacts.

Version `3.0.282` closes that validation-policy gap. Ten complete index-5
hypothesis-index/depth samples per focal tier produce exact class counts
`4/2/10/10` at `28/35/70/150mm` and 45 pair measurements per tier. Tele
normalized depth RMSE reaches about `1.397`, so map-distance envelopes are
explicitly diagnostic rather than permissive pass thresholds. The exact
stage oracle is instead structural and formula-coupled: all `129,792,000`
checked pixels have an in-range index and bit-exact
`depth_mm = reciprocal_ray_depth_lookup[index]`, are finite, and stay in
`[200,640000] mm`. Canonical parity validation layers those exact map and
undistorted-plane checks with deterministic formula/routing/geometry/artifact
checks and the admitted focal-specific final-output repeat envelopes. This
promotes `CLM-VALIDATION-001` to `PROVEN` / `SPEC_READY`.

Version `3.0.283` closes the final live State/object blocker by reconciling
the broad historical residual list against 13 independent installed-static
and runtime verifier families. The image-consequential State path now has a
public processor identity, retained RawImageFactory/CaptureStack ownership,
named public `CapturedImage` inputs, exact factory/current CalibStage K/R/t
transfer semantics, whole composed-camera-record operational identity, and a
four-focal/two-body terminal State-to-`PipelineCache+0x258` publication join.
The alleged downstream residuals are independently closed by exact
Guidance/SGM, IRAMP candidate/reconstruction, and validation claims. Numeric
State labels, padding, and fields with no demonstrated image consumer are
explicitly nonblocking. `CLM-STATE-001` is `PROVEN` / `SPEC_READY`.

Version `3.0.284` reopens one supported-input compatibility blocker after a
full `9,438`-file public firing-set census. All `9,242` structurally complete
LRIs use exactly `A1 -> A1..A5,B1..B5` (`6,078`) or
`B4 -> B1..B5,C1..C6` (`3,164`), but two complete `28mm` files use the tele
set and one complete `74mm` file uses the wide set. All three exceptions
complete profile-3 `10432x7824` Radiance renders. Focal length is therefore
not a universal camera-family selector; exact variant reducer/stereo/C6 and
crop/warp routing is now `CLM-COMPAT-002`, `PARTIAL` / `BLOCKER`.
SHA-pinned installed proof further closes candidate scorer-family selection:
public reference camera `0` selects family A and `8` selects family B without
consulting focal. Other family-specific variant routes remain open.

Version `3.0.285` reconciles three stale narrow rows against stronger admitted
claims. `CLM-MERGE-001` is a four-focal proven negative architecture fact
under the exact parent/IRAMP topology; `CLM-ZOOM-001` is a proven 35mm subset
of four-tier `CLM-ZOOM-003`; and `CLM-CCM-001` is proven for canonical profile
3 because missing-CCM A2 is inside wide MonoFusion while C6 is terminally
excluded. These reconciliations do not change blocking `CLM-COMPAT-002`.

The live blocker set is the `BLOCKER` set in
`docs/canonical/CLAIM_LEDGER.md`. The profiles-`1/2` MonoFusion mode-1 scalar
body is formula-closed at version `3.0.336`; remaining alternate-profile and
GUI/editing semantics remain reference-only under `CLM-COMPAT-001`; its
initial profile-3 editor topology is now four-focal verified, while the tested
post-brush cache-reuse result is Unit-1 `28mm` only. Exact editor packing and
the immediate tested default display route are installed-static plus Unit-1
`28mm` verified; the exact seven-stage editor/export mapping is isolated, while
the selected ACRE core and tested lens/contrast no-op incidence are now closed.
The selected ACRE EV/LUT public origins are also closed at tested Unit-1 `28mm`
default level-4 scope. Version `3.0.315` additionally closes selected display
index-10 color correction, including its public two-body calibration origin,
optimizer, endpoint interpolation, and full-image byte replay at that same
request scope. Alternate cache/mode behavior remains open.
`PARITY_BLOCKERS.md` and `WSJF_PRIORITY.md` order that work.

## Superseded Scoped Completion Checklist

The requested Groups A-E items from the former checklist are admitted under
the scopes below. This table is retained as closure history, not as a claim
that full clean-room reverse engineering is complete:

| Item | Admitted result | Scope |
|---|---|---|
| A1 | Wavelet detail weights: float32 `(-1/192,-1/96,-1/48,-1/24)` = `(-0.0052083334885537624,-0.010416666977107525,-0.02083333395421505,-0.0416666679084301)`. | installed static |
| A2 | Seven-tap Gaussian: `(0.047079380601644516,0.11924773454666138,0.20826762914657593,0.2508104741573334,0.20826762914657593,0.11924773454666138,0.047079380601644516)`. | installed static plus four-focal runtime |
| A3 | `ImageDenoiseBilateralGeneric<5,true>` spatial kernel is uniform `5x5`: `S(dx,dy)=1` for `|dx|,|dy|<=2`, otherwise `0`; range weight is separate. | installed static |
| A4 | NLM public config is `window_size=5`, `patch_size=5`, `step_size=2`; search radius is `2`. | four-focal runtime |
| A5 | Wavelet abs mask is four SIMD lanes of `0x7fffffff`. | installed static |
| B1 | CalibStage `0=factory` at `CapturedImage+0x180`, `1=current` at `+0x12c`; transferred slices are public `intrinsics.k_mat`, `extrinsics.canonical.rotation`, and `.translation`, repacked as K/R/t. | installed static, Unit-1 four focals, Unit-2 exact `28mm` |
| B2 | Cost-volume operands are `Guidance`, `Pixel buf`, `Min cost buf`, and `Line buf`; Guidance is tier-anchor `StereoISP::CreateStereoImage` output `Image<vec4x8ui>`. | installed labels plus four-focal runtime |
| B3 | `ColorCalibration.type`: `0=A`, `1=D50`, `2=D65`, `6=F11`; stored variants are A/D65/F11, the live four-focal pair is A/D65, selected by clamped reciprocal-temperature interpolation. | four focal |
| B4 | The 13-body State machine is `lt::CalibDataProcessor::{runReferenceGroupCams,runHigherGroupCams}` with callbacks returning `CalibDataProcessor::State()`. | installed RTTI plus four focal |
| C1 | After terminal finalization, the exact whole State is retained at `PipelineCache+0x180` and feeds five `0x3f7040 -> PipelineCache+0x258` warp-field records; replacement `State+0x2a8` does not feed that route. | Unit-1 four focal + exact-35mm Unit-2 |
| C2 | SGM tuning is installed/body-independent: `P1=1`, nominal adaptive `P2/P1=500`, guide decay `log2(e)/(18,48,48)`. | installed static plus four focal |
| C3 | Weights are separable half-sample Hann; shaping is orthonormal `I1/I2/I3 -> RGB`; post-square scale is AWB; cache rows are `Vec3<Float16>`; working rows are `vec4x32f`; tested output is `linear_prophoto_rgb` to Radiance `FORMAT=32-bit_rle_rgbe`. | four focal CLI bridge HDR |
| C4 | C6 is cleared at `0x3c90a5`; restoring only its public `is_enabled` reaches the per-key mono-module rejection and writes no image. C6 is terminally excluded from canonical tele bridge-HDR super-resolution contribution. | repeated `70mm`/`150mm`; non-bridge excluded |
| C5 | Canonical `28mm`/`35mm` selects `SparseMirrorAngleOptimizer::CostFunction=1 -> optimize::$_2 -> 0x218940`; guard `0x218bc4` belongs to the distinct CostFunction-`0` / `0x218b30` family. | canonical wide |
| D1 | Exact-focal Unit-2 `28mm` yields ten paired constructor packets, keys `0..9`, joined to public exposure, analog gain, digital gain, and temperature fields. | Unit-2 exact `28mm` |
| E1 | Laplacian clarity uses exact logarithmic plane selection, five-tap reduce/parity expand, negative-detail reconstruction, all five tonal-field envelopes, 8049-sample clarity transfer, adjacent transformed-pyramid interpolation, and `0.75^level` blend. | installed static same mechanism; Unit-1 `28mm` six-plane/levels-`0..4` and tonal-field liveness runtime |

This scoped checklist is complete. The separately tracked distributed
pre-fusion `src1`/`src2` mechanism and final contributor
acceptance/rejection predicate were subsequently closed by explicit ledger
admissions; they were not silently promoted by this checklist. The broader
CNR closure was later corrected by version `3.0.350`; the live guide-source
gap is active even though the earlier selector and matrix gaps were closed.
The live status is the proven/partial tables and current authoritative set
below, not the chronological wording preserved in later addenda.

## Proven Truth

These claims are currently `PROVEN` in the canonical ledger.

| Claim ID | Truth | Zoom status | Readiness |
|---|---|---|---|
| `CLM-INPUT-001` | Raw LRI sensor surfaces are `4160x3120` public `RAW_PACKED_10BPP`, stride `5200`, stored at `32 + slot*0xf7a000`; each ten-byte group is eight consecutive little-endian 10-bit samples, and public Bayer red-site overrides give the per-camera Bayer/mono phase. | exact-focal two-body `28mm/35mm/70mm/150mm = VERIFIED`; runtime corroboration Unit-1 `28mm` | `SPEC_READY` |
| `CLM-LRI-001` | Complete LRIs use public LELR records `LightHeader`, `ViewPreferences`, and `GPSData`; partial preferences merge in file order. All complete local inputs have decoded raw/calibration/preference roles. Public crop and image exposure targets are live; flash calibration is not copied into image state and GPS is metadata-only on the tested HDR route. | `28mm/35mm/70mm/150mm = VERIFIED`; all `9,242` complete local LRIs schema-censused | `SPEC_READY` |
| `CLM-OUTPUT-002` | Final profile-3 placement is formula-closed for every orientation value in complete inputs. The exact legacy Radiance writer is a parity reference; the independent modern contract is top-left contiguous RGB IEEE float32 TIFF with a linear-ProPhoto ICC derived from the installed RGB-to-XYZ matrix. | four-focal normal placement; exact-35mm two-body CW/CCW; focal-independent tagged mapping | `SPEC_READY` |
| `CLM-FIRING-001` | Archive-wide firing topology has two dominant regimes: `5A+5B` for `28mm` and `35mm`, `5B+6C` for `70mm` and `150mm`. No zoom tier's dominant regime is `C-only`. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-COMPAT-002` | Every complete local LRI has exactly one of two full firing sets keyed by public reference camera. Both `28mm`/tele exceptions are runtime-joined to the tele stereo/warp/C6/`C1..C5` IRAMP/crop path; the `74mm`/wide exception is joined to wide MonoFusion/stereo/warp/`B1..B5` IRAMP/crop. Focal alone is never the topology selector. | all `9,242` complete LRIs static; all three exceptions complete runtime, spanning two bodies | `SPEC_READY` |
| `CLM-ZOOM-003` | Focal framing is tiered, not globally `28mm`-anchored. `28mm` and `35mm` use a `28mm` reference tier; `70mm` and `150mm` use a `70mm` reference tier. Internal crop happens before final rasterization. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-DEMOSAIC-001` | Bridge HDR uses `DemosaickLightV1`; the inner kernel at `libcp+0x2eef80` is static SSE2, not JIT. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-SHARPEN-001` | Installed sharpening is Lab-`L*` DoG: `L_out=L+clamp(sharpening*(G_positive(L)-G_negative(L)),-20,20)`. Its direct packet is `(sensor_analog_gain,grain_power,grain_sigma,sharpening,sharpening_scale)`; gain and sharpening select exact piecewise positive/negative sigma curves, scale multiplies both sigmas, and sigma thresholds `1/1.2999999523162842` select 3/5/7 taps. Public vibrance selects only the surrounding helper; all helpers pass the same packet. | installed formula; Unit-1 constructor census `28mm/35mm/70mm/150mm`; complete kernel/sigma replay Unit-1 `28mm` | `SPEC_READY` |
| `CLM-PIPELINE-001` | Installed payload callbacks have a fixed dependency order. Wide Color is public AWB/color scale -> CNR -> adaptive desaturation -> denoise -> Lab-L sharpen -> Laplacian clarity -> conditional linear-ProPhoto materialization. Bayer has the admitted correction order at all four focals; tele BayerFloat adds CNR/adaptive/denoise before sharpen while wide BayerFloat omits them in the observed window. Clarity is fixed index 13; index 15 compares against exact linear-ProPhoto/D50 and matching configs are bit copies, not a nonlinear look curve. The tested profile-3 route selects only that exact-copy branch. | installed exact order/formula; Unit-1 target-set and branch census `28mm/35mm/70mm/150mm`; exact-`28mm` Unit-2 full control; exact-`70mm` Unit-2 scoped discriminator; clarity liveness Unit-1 `28mm`; tele Color zero-hit scoped | `SPEC_READY` |
| `CLM-SHARPEN-002` | Installed Laplacian clarity selects `2..6` total planes logarithmically, reduces with exact float32 `(0.05,0.25,0.4,0.25,0.05)`, expands by exact parity kernels, stores `Expand(G_next)-G`, and reconstructs by subtracting that negative detail. Its 8049-sample transfer, five public tonal-field envelope formulas, adjacent-pyramid interpolation, and `alpha=0.75^level` blend are exact; defaults are `(0,1,1,0.5,-8,0.2,-1)` with samples `[-8,-7.5,...,1]`. | installed/static same mechanism; Unit-1 `28mm = VERIFIED` six-plane and all-field runtime liveness | `SPEC_READY` |
| `CLM-DENOISE-001` | Installed `ImageDenoiseBilateralGeneric<5,true>` uses a uniform 5x5 spatial box, `S(dx,dy)=1` for `|dx|,|dy|<=2` and `0` otherwise. Selected `ImageDenoisePatchNLM<4>` uses public `window_size=5`, `patch_size=5`, and `step_size=2`, but loads exact 4x4 offsets `{-2,-1,0,+1}^2`. It seeds full-frame numerator/denominator with `0.01*source` / `0.01`, phases interior reference centers deterministically through four quadrant passes, samples candidates on a row-parity checkerboard, uses reference-center range scale, locally accumulates and overlap-adds all 16 weighted patch pixels, then normalizes with unrefined `rcpps`; this valid-patch/positive-seed construction is the no-clamp boundary policy. Generated `range_scale` is exact from public reciprocal AWB, public analog gain, installed RGB SensorGainVars, `42/1023`, variance floor `1e-5`, fixed squared-Ohta propagation, and final `(0.0025,0,0,0)` floor. | selected route and generated scale = `28mm/35mm/70mm/150mm VERIFIED`; exact-35mm Unit-2 control; topology installed-static | `SPEC_READY` |
| `CLM-CCM-002` | Public `ColorCalibration.type` maps `0=A`, `1=D50`, `2=D65`, and `6=F11`; each canonical LRI stores 14 records each for A, D65, and F11 and stores no D50 record. The tested bridge-HDR live pair is same-camera A/D65 at all four focal tiers; F11 is stored but not selected. In public `AWB_MODE_AUTO`, the tier-anchor `ViewPreferences.awb_gains` becomes normalized reciprocal neutral RGB; exact `0x350570` fixed-point solution against that camera's public A/D65 matrices, followed by the installed 31-row Robertson temp/tint round trip, reproduces every retained live scene-xy word at all four focal tiers. `0x350bc0 -> 0xab720` then computes clamped float32 reciprocal-temperature interpolation `M_D65 + alpha*(M_A-M_D65)`. | public-origin live xy and pair selection `28mm/35mm/70mm/150mm = VERIFIED`; exact output reconstruction complete-wide/static-same-mechanism tele | `SPEC_READY` |
| `CLM-MERGE-002` | `ImageResolutionAmp` / IRAMP contains a real multi-source weighted accumulator in `libcp`, with the accumulator at `0x369fa1..0x369fa8`; the canonical four-zoom bridge HDR quartet all hit this accumulator surface. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-MERGE-003` | On the tested bridge HDR path, IRAMP receives `src1`, `src2`, `srcs[5]`, `warps[5]`, `scale`, and `roi`; runtime packets directly verify this signature at `28mm`, `35mm`, `70mm`, and `150mm`. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-MERGE-004` | On the corrected canonical bridge HDR quartet, the five direct IRAMP contributor source-vector items are `B1..B5` at `28mm` and `35mm`, and `C1..C5` at `70mm` and `150mm`. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-MERGE-005` | IRAMP converts direct contributors and cropped `src2` from RGB into the exact installed I1/I2/I3 domain before patch preparation; local candidate/sentinel policy, exact score and reconstruction formulas, continuous surviving-candidate weighting, post-IRAMP row/pixel/file policy, and final-file score consequence are closed for canonical profile-3 bridge HDR. | mechanism `28mm/35mm/70mm/150mm = VERIFIED`; direct image-effect intervention `35mm/70mm` | `SPEC_READY` |
| `CLM-MERGE-006` | The selected owner-cache resample route and its final-file dependence on the IRAMP score path are closed by four-focal custody plus representative wide/tele intervention. | custody `28mm/35mm/70mm/150mm = VERIFIED`; direct intervention `35mm/70mm` | `SPEC_READY` |
| `CLM-PREFUSION-001` | Visible `src1` is the one-camera A1-wide/B4-tele `ReferenceImageCache`; visible `src2` is `processLevel1` over A1/A2 MonoFusion mode `0` at profile-3 wide and direct B4 at tele; outer IRAMP gives them distinct guide/reference roles. | `28mm/35mm/70mm/150mm = VERIFIED`; Unit-2 `28mm/70mm` identity discriminators | `SPEC_READY` |
| `CLM-PREFUSION-002` | Canonical profile-3 distributed pre-fusion is formula-closed; MonoFusion mode `1` is reachable only in tested profiles `1` / `2` compatibility scope and is excluded from the canonical target. | `28mm/35mm/70mm/150mm = VERIFIED` | `SPEC_READY` |
| `CLM-ZOOM-002` | Canonical tele public firing topology is `B1..B5 + C1..C6`, not C-only; later C6 clearing remains a distinct stage. | `70mm/150mm = VERIFIED`, public-header corroboration on both calibration bodies | `SPEC_READY` |
| `CLM-WARP-001` | `libcp+0xf540` is an alloc/resize helper, not the writer of the dst-coordinate pair grid. | same mechanism across all four zoom tiers | `SPEC_READY` |
| `CLM-WARP-002` | The dst-coordinate backing store is packed int32 `(x, y)` pairs on an 8-pixel lattice; actual writes occur at `0x366520..0x366523`. | same mechanism across all four zoom tiers | `SPEC_READY` |
| `CLM-WARP-003` | Inside IRAMP, the first pair grid is ROI-derived and a second same-sized transformed pair grid is produced before bbox / clipping handling. | same mechanism across all four zoom tiers | `SPEC_READY` |
| `CLM-CERES-001` | `libcp+0x5c3580` begins with two doubles `(1.0, 1.0)`; the stale four-float decode was a wrong-offset error. | static bundle fact, zoom-irrelevant | `SPEC_READY` |
| `CLM-OUTPUT-001` | The final-compositing queue/drain surface is a hand-rolled intrusive ring/list, not an RB-tree or `std::list`; `0x3bf820 -> 0x3bfc40` inserts records at owner `+0x260`, `0x3c25a0` waits on that container, `0x3bfe60` drains/deletes nodes, and `0x3bca90` filters gathered records before ImagePyramid/Image accessor plus per-tile virtual-dispatch surfaces. Narrowed LLDB proof shows the producer insert edge, insert body, drain body, orchestrator drain edge, and post-gather 0x70-stride filter loop are live across `28mm`, `35mm`, `70mm`, and `150mm`; switch census shows the tested CLI path reaches record types / case targets `1`, `2`, `3`, `11`, and `16` only, with zero hits at case `4` target `0x3bcf20`. Follow-up case-`2` helper proof shows the live case-`2` path reaches helper `0x3bf2f0`, reaches callsites `0x3bf331`, `0x3bf344`, `0x3bf354`, and `0x3bf382`, and records zero hits at alternate/helper callback/completion/error sites under the same tested quartet. Follow-up case-`11` proof shows the case-`11` target and owner `+0x5d0` null test hit with switch-census counts, but owner `+0x5d0 = 0` in every captured sample, so callback callsite `0x3bd47b` and return site `0x3bd47d` record zero hits under the same tested quartet. Follow-up case-`16` cleanup proof shows the case target `0x3bd2f7`, helper call `0x3bd2fe -> 0x3adad0`, and return `0x3bd303` hit once per render; helper `0x3adad0` is entered four times per render overall, every captured helper invocation reaches raw local-count branch `0x3adb16` with `rbp-0x38 = 0`, then cleanup path `0x3adc74 -> 0x3ae490`, while callback/release/error sites `0x3adb6e`, `0x3adb9b`, `0x3adbaa`, `0x3adbb9`, and `0x3adc3f` record zero hits under the same tested quartet. Follow-up case-`1` / case-`3` proof shows case `1` reaches its mutex / flag / condition-broadcast path once per render, changes the captured pointed flag byte from `0` to `1`, and case `3` passes record substructures into helper `0x4182a0`, whose selected normal callsites and normal return hit once per render while selected mismatch/error sites record zero hits under the same tested quartet. | `28mm/35mm/70mm/150mm = VERIFIED` | `REFERENCE_ONLY` |

Additional `CLM-MERGE-005` addendum: installed-bundle extraction pins the wavelet-detail table at `0x5fdb10` to float32 `(-1/192, -1/96, -1/48, -1/24)` after float32 rounding, exact values `(-0.0052083334885537624, -0.010416666977107525, -0.02083333395421505, -0.0416666679084301)`, and pins `0x5a81f0` to four SIMD lanes of `0x7fffffff`, the float32 sign-clearing absolute-value mask. These are static installed-bundle constants, not zoom-dependent runtime claims, and do not close the remaining `CLM-MERGE-005` policy gaps.

Additional `CLM-MERGE-005` addendum: the IRAMP row/cache policy now has exact public identities. Its separable overlap weights are the half-sample Hann window `h_N(i)=sin^2(pi*(i+1/2)/N)`; the fixed three-vector shaping matrix is the orthonormal opponent-color `I1/I2/I3 -> RGB` transform, making `(2,0,0,0)` an intensity-only `I1` correction and accumulated lane 3 the overlap-normalization weight rather than a color channel. Installed RTTI names the post-square channel vector producer `lt::Internal::Pipeline::setWhiteBalance(lt::Internal::PipelineBase::AWB)`, names owner-cache pixels `Vec3<Float16>`, and binds the write/read routes to `ImageConvertPixelType<Vec3<Float16>,vec4x32f>`, `ImageConvertPixelType<vec4x32f,Vec3<Float16>>`, and `TileCache<Vec3<Float16>>::renderROI<vec4x32f>`. Complete `28mm`, `35mm`, `70mm`, and `150mm` runtime reports join that six-byte half-RGB cache to four-lane float working rows with lane 3 set to `1`, then to the final `linear_prophoto_rgb` 16-byte-per-pixel descriptor and Radiance `FORMAT=32-bit_rle_rgbe` writer. This closes public weight/shaping/pixel names and the tested CLI downstream row/file policy; it does not close the separate contributor acceptance/rejection predicate.

Additional `CLM-MERGE-005` addendum: outer IRAMP body `0x3661b0` explicitly converts both color-domain inputs before patch scoring and accumulation. Direct contributors are materialized through `0x366f1c -> 0x374ac0` and transformed in place at `0x366fd0..0x3670a8`; `src2` is materialized through `0x36695a -> 0x374ac0`, cropped, and transformed at `0x368ce0..0x368db8` before `0x3692c6 -> 0x36b920` prepares its reference patch. With exact installed float32 constants `a=0.5773500204086304`, `b=0.7071099877357483`, `c=0.40825000405311584`, and `d=0.8165000081062317`, both loops compute `I1=a(R+G+B)`, `I2=b(R-B)`, and `I3=cR-dG+cB`, preserving lane 3. The inverse tail uses the transpose of this rounded matrix. `src1` remains the distinct byte guide and does not pass through either transform. Installed-body proof plus a Unit-1 `28mm` both-role coefficient capture and prior complete `28/35/70/150mm` IRAMP reports close the application point at four-focal scope. `0x36b920` performs patch/spatial preparation and has no cross-channel lane mixing; the earlier assumption that patches already entered in I-domain there is rejected. The fixed installed arithmetic reads no calibration/body/firmware selector, so no cross-body pixel equality or firmware causation is claimed.

Additional `CLM-WARP-003` addendum: the three selected `state+0x448` node slices transferred into the selector-1/current CalibStage bank now have public calibration names. `node+0x30..+0x53` is composed/focus-evaluated `FactoryModuleCalibration.geometry.per_focus_calibration[].intrinsics.k_mat`; `node+0x60..+0x83` is `extrinsics.canonical.rotation`; and `node+0x54..+0x5f` is `extrinsics.canonical.translation`. They are repacked into current-bank order `K,R,t` at `CapturedImage+0x12c..+0x17f`. Installed static proof plus Unit-1 four-focal runtime and an exact-focal Unit-2 `28mm` discriminator support the mapping. The later values are composed/BA-normalized internal values with those public origins, not direct protobuf wire-byte copies; the only installed CalibStage bank names remain `factory` and `current`.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: installed RTTI publicly identifies the 13-body calibration State machine as `lt::CalibDataProcessor`. Bodies `$_0..$_6` are owned by `CalibDataProcessor::runReferenceGroupCams`, bodies `$_7..$_12` by `CalibDataProcessor::runHigherGroupCams`, and every callback returns `CalibDataProcessor::State()`. Dispatcher `0x22f0f0` carries the installed `"State machine"` label, invokes callback slot `+0x30`, and stores the returned State. Complete `28mm`, `35mm`, `70mm`, and `150mm` runs exercise all 13 RTTI-bound bodies and write HDR. This closes the whole-machine class/method identity, not semantic enum labels for numeric State values and not the separate `src1`/`src2` reducer.

Additional `CLM-MERGE-003` / `CLM-MERGE-005` addendum: follow-up runtime proof now bounds the live `0x3661b0` vector-count use window. At `0x366a50..0x366a65`, the body reads a vector header through `r15+0x18`, computes `(end-begin)/16`, and reaches `0x366a65` with live `rbx = 5` across 16 capped packets per canonical focal tier under `--no-auto-lris`; every accepted packet has vector byte span `80`. This is count-use evidence only. It does not prove complete contributor acceptance, `src1` / `src2` semantics, the full reducer algorithm, or final acceptance/rejection.

Additional `CLM-MERGE-005` addendum: follow-up W5 reproduction proof now verifies representative non-degenerate score and reciprocal magnitudes at the terminal IRAMP arithmetic sites. LLDB core-handled ignore-count / conditional breakpoints capture live `0x36e511 -> 0x36e515` `sqrt(xmm0*xmm1)` score arithmetic on all four canonical focal tiers, and live `0x36a938` non-common `xmm2` denominators whose post-`rcpss` values approximate `1/xmm2` on all four tiers. This admits the arithmetic and representative magnitudes only; it does not admit Opus's exact numeric rows as constants, a full per-pixel distribution, public semantic field names, complete reducer closure, or final acceptance/rejection.

Additional `CLM-MERGE-005` addendum: follow-up branch-target proof now bounds the local `0x36930f` sentinel gate at runtime. On all four canonical focal tiers under `--no-auto-lris`, capped packets reach `0x36931b` with `eax == 0x80000000` and reach `0x369320` with non-sentinel `eax` values whose low table dword at `r12 + rsi * 8` matches `eax`. This admits branch-target behavior only; it does not prove a full sentinel/valid distribution, complete candidate policy, score-threshold policy, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime/static proof now classifies the later `StereoLayer<false>+0x2a8` overwrite that feeds the `0x29ed90` guided-upsample path. Every canonical focal tier reaches `0x26dd40 -> 0x26e120 -> 0x267010 -> 0x26e64a -> 0xf340` for six `StereoLayer<false>` objects with indices `0..5`, mode `8`, and tile sizes `32,16,8,4,2,1`; index `5` is the full `2080 x 1560` descriptor returned through slot `+0x90` at `0x26aa30/0x26aa39` and consumed by `0x29ed90`. Static disassembly classifies `0x267010` as a descriptor builder that allocates a 4-byte-output descriptor from source descriptor dimensions, reads 16-bit source entries, uses the first pointer in `this+0xe0` as a 4-byte lookup table, and writes looked-up values into the destination before `0xf340` moves that stack descriptor into `this+0x2a8`. This narrows the index-5 input to a runtime-built StereoLayer pyramid product, but it does not prove the public physical quantity, public LRI/protobuf field origin, upstream source-descriptor semantics, lookup-vector semantics, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, or acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime proof now verifies the sampled `0x267010` mapping behavior. For all canonical focal tiers and all six `StereoLayer<false>` indices `0..5`, the first 16 sampled source entries are read as `uint16` indices into the `rdx` float lookup vector, and each sampled `lookup[source_u16]` value exactly matches the corresponding 4-byte float in the stack descriptor after `0x267010` returns at `0x26e638`. The source descriptor sizes are the six-level pyramid `65x49`, `130x98`, `260x195`, `520x390`, `1040x780`, and `2080x1560`; lookup-vector counts are `752` for `28mm` / `35mm` and `1472` for `70mm` / `150mm`. This proof establishes sampled internal index-image-to-float-table expansion only; by itself, it does not prove public physical meaning, public LRI/protobuf origin, the immediate producer/custody chain, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime/static proof now bounds the immediate upstream producer/custody chain for the `0x267010` source descriptor. Every canonical focal tier reaches `0x26e4c6 -> 0x299c70` for all six `StereoLayer<false>` indices `0..5`; runtime packets prove the `0x299c70` source object argument is `this+0xf8`, the destination is caller `rbp-0xe0`, `source_object+0x30/+0x34` matches the produced 2-byte descriptor dimensions, the `0x299c70` dispatch callback stores the destination/source pointers at callback `+0x08/+0x10`, the produced descriptor is moved by `0x26e4e0 -> 0xf340` into caller `rbp-0x80`, and that moved descriptor is passed unchanged to `0x267010`; the `0x267010` lookup-vector callsite argument is `this+0xe0`. This closes the immediate internal producer/custody boundary only; it does not prove public field names, LRI/protobuf origin, public calibration semantics, physical meaning, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime/static proof now bounds the sampled internal `0x299c70` callback worker formula for the same `0x267010` source descriptor path. Static extraction shows callback address point `0x6680f0` is invoked by generic executor `0x5440` through slot `+0x30 = 0x29a670`. Worker `0x29a670` writes a `uint16` descriptor by reading per-pixel source-record offsets from `source_object+0x40`, records from `source_object+0x10`, source stride from `source_object+0x38`, selecting the first minimum `uint16` cost in each record's `record+0x08` cost list, and writing `(u16(record+0x00) + u16(record+0x04) * selected_index) & 0xffff`. Runtime probes across `28mm`, `35mm`, `70mm`, and `150mm` validate six dispatches and six sampled worker tiles per focal tier, with `192/192` sampled post-write values matching the reconstructed formula. This closes the sampled internal worker mechanics only; it does not prove public field names, LRI/protobuf origin, source-index physical meaning, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime watchpoint proof now bounds the internal construction/custody path for the tracked index-5 `StereoLayer<false>+0xe0` lookup-vector header and `+0xf8` source object consumed by the proven `0x299c70 -> 0x267010` chain. The live lookup-vector header is populated through the `0xf02d0` path with final observed write at `0xf043e`, using count `752` at `28mm` / `35mm` and count `1472` at `70mm` / `150mm`; the source-object control qword is written at `0x26be62`; and later populated samples at `0x26e4c6`, `0x299c70`, and `0x267010` preserve the same `this+0xf8` / `this+0xe0` argument relationships with source dimensions `2080 x 1560`, stride `2080`. This narrows internal lookup/source-object construction only; it does not prove public field names, public LRI/protobuf origin, public calibration semantics, physical meaning, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime/static verifier now bounds the generated-table mechanics for that tracked index-5 `StereoLayer<false>+0xe0` lookup vector. `0x26c480` builds a stack vector through `0x28fa60` / `0x28f5a0` / `0x28f860`, `0xf02d0` copies it into `this+0xe0`, and later `0x267010` consumes the same bytes unchanged. Runtime packets retain target fields `index=5`, `mode=8`, `this+0x298/+0x29c = [200.0, 640000.0]`, and `2080 x 1560`; the vector exactly matches the installed helper's float32 reciprocal near/far ramp from `640000.0` down to `200.0`, with count `752` at `28mm` / `35mm` and count `1472` at `70mm` / `150mm`. The verifier finds zero full-vector LRI block byte hits, zero public calibration fixed32 full-sequence hits, and zero scalar public calibration fixed32 hits. This admits an internal generated near/far lookup table, not public LRI/protobuf field names, source-index descriptor semantics, final contribution, or acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom runtime/static proof now bounds the endpoint and count producer mechanics for the same generated lookup vector. Static extraction shows the selected endpoint pair comes from binary float tables at `0x609428` / `0x609430`, whose first row is `[200.0, 640000.0]`, propagated through `0x3ff43c -> 0x2681b0 -> 0x26ba90` and stored in `this+0x298/+0x29c`. Runtime packets for the tracked index-5 object prove `this+0x258` is an 840-byte vector of five `0xa8` source records, `this+0x18 = 2.0`, and `this+0xc = 8`; the verifier mirrors `0x28f5a0` float32 math over those records, the first-record scalar, endpoint reciprocal span, clamp `0x1000`, and mode rounding to reproduce lookup counts `752` at `28mm` / `35mm` and `1472` at `70mm` / `150mm`. This closes endpoint/count producer mechanics only; by itself it does not prove public units or naming, source-index descriptor semantics, source-record public names, final contribution, or acceptance/rejection.

Additional `CLM-WARP-003` addendum: deterministic installed-binary proof now joins the selected index-5 endpoint pair to the one-scalar Triangulator reprojection problem. The `0x3f2c40` constructor mode selects `[200.0,640000.0]` for mode `0` or `[70.0,40000.0]` for the nonzero branch, propagates the pair through `state+0x100/+0x104` and Triangulator owner `+0x70/+0x74`, and installs it through imported Ceres lower/upper-bound setters on the scalar already proven to scale ray `(bx,by,1)`. Reused complete runtime reports show all four canonical Unit-1 focal tiers select mode `0`; because the generated index-5 reciprocal vector uses that same `[200.0,640000.0]` endpoint pair, its internal role is now admitted as a reciprocal ray-depth hypothesis grid. Public units, public calibration/LRI/protobuf origin or names, source-index/source-record public semantics, broader runtime solved-value distributions beyond the admitted scoped solve-output runs, final contribution, and acceptance/rejection remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned static proof plus complete Unit-1 four-focal runtime and an exact-focal Unit-2 `28mm` body discriminator now closes the index-5 path's public length units. Exact descriptor-address and data-pointer identity joins the six `StereoLayer<false>` descriptors and exact `UpsampleLayer+0x90` descriptor to the seven depth-cache selections; verified workers perform depth-to-reciprocal, reciprocal-field resize, and reciprocal-to-depth conversion without a length-unit conversion; cache promotion preserves the resulting descriptor into the live provider; and the GDepth writer serializes that provider's exact extrema with `GDepth:Format="RangeInverse"` and `GDepth:Units="mm"`. The admitted dimensional statement is therefore: Triangulator ray-depth scalars, `[200,640000]` bounds, index-5 and `record+0x40` depth-map pixels are `mm`, while the generated reciprocal lookup is `mm^-1`. Public calibration/LRI/protobuf origin and names for the bounds, public source-index names and unrelated whole-record semantics, final contribution, and acceptance/rejection remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: complete installed `__text` reference census now closes the depth-bound origin negatively and deterministically. The bound-selecting constructor `0x3f2c40` has one direct caller through wrapper `0x3f46d0`; that wrapper also has one direct caller, and the sole owner call at `0x3b3004` executes `xor edx,edx` before `0x3b3011 -> 0x3f46d0`. Mode `0` therefore enters the constructor as an installed literal and selects immediate pair `[200.0,640000.0]`; no LRI, calibration object, protobuf field, body identity, focal tier, or runtime option supplies it on this path. Combined with the admitted unit proof, the operational names are installed Triangulator ray-depth lower bound `200 mm` and upper bound `640000 mm`; there is no public calibration/LRI/protobuf carrier or field name for them. The statically present nonzero pair `[70.0,40000.0]` remains unselected and publicly unnamed. Claim status is unchanged.

The installed-origin addendum supersedes earlier `CLM-WARP-003` wording that
listed public calibration/LRI/protobuf origin or names for the mode-0 bounds
as open.

Additional `CLM-WARP-003` addendum: installed debug-label xrefs plus the admitted Unit-1 four-focal and exact-focal Unit-2 `28mm` range-builder reports now close the former generic source-index/source-record names. The pinned `StereoLayer<false>` debug routine exactly labels `+0x2a8` as `Depth map`, `+0x208` as `Skip mask`, and `+0xf8` as `Cost volume`; the cost-volume constructor family independently names its descriptor input `Range map`. Runtime custody joins previous-layer `Depth map` plus `Skip mask` through `0x26d750` to the generated `(lower,count)` Range map, then through `0x29a140` to the Cost volume. The proven `0x299c70` worker selects the first minimum from each variable record's cost list and writes `base_hypothesis_index + hypothesis_index_step * argmin`, so its output is a generated minimum-cost depth-hypothesis index map and the variable records are per-pixel cost-volume records. `Range buf` is a separately labeled `StereoLayer+0x1b8` field and is not equated to the Range map without pointer custody. These runtime-generated products are not direct LRI/protobuf fields. Public names/origins for every cost-volume operand, whole-State record identity, final contribution, and acceptance/rejection remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: the same pinned-label/static verifier and four-focal endpoint/count reports classify the separate five-record `StereoLayer+0x258` family. `StereoLayer+0x240` is exactly labeled `Images`; the producer loop appends one 16-byte Images item, resolves the same camera through `state+0xe0`, finds its same-key `state+0x448` node, composes through `0x264440 -> 0x23faf0`, and appends one `0xa8` record later copied to `+0x258`. All four Unit-1 focal reports contain five Images items and five paired records. `0x28f5a0` forms one three-coordinate value per record from fields `+0x24..+0x50`, computes Euclidean separation from the first record, and uses the maximum geometry spread in the lookup-count formula. The family-level semantic name is therefore per-image composed geometry records. The following addendum closes their whole-field operational identity while retaining that they are derived rather than direct protobuf copies. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned static proof plus completed Unit-1 four-focal runtime and an exact-focal Unit-2 `28mm` discriminator now close the whole-field operational identity of those five `StereoLayer+0x258` items. Each item is a derived per-image, tier-anchor-relative calibrated camera-model record: `+0x00..+0x20` is composed intrinsics with public per-focus `intrinsics.k_mat` ancestry at live `CameraModule.lens_position`; `+0x24..+0x50` is anchor-relative extrinsic translation/rotation sourced from public `extrinsics.canonical`; `+0x54..+0x60` is a derived two-axis offset/scale tuple; `+0x68..+0x78` contains exact same-camera public `Distortion.Polynomial.coeffs`; and `+0x80..+0xa0` is a composed distortion normalization/center matrix derived from public `distortion_center` and `normalization`. Wide ordering is `A1,A5,A2,A3,A4` around anchor `A1`; tele ordering is `B4,B2,B5,B1,B3` around anchor `B4`. `0x28f5a0` computes the maximum separation of their inverse-extrinsic centers, not an anonymous transformed-vector spread. The Unit-2 run preserves the mechanism and ordering with distinct calibration and record bytes. These are derived records, not direct protobuf-message copies. Numeric CalibStage selector names, whole-State identity, remaining Cost-volume operand origins/names, public LRI/protobuf identity for the binary-installed ray-depth bounds, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned shared-control-block RTTI plus same-process pointer custody now identifies the objects selected through `state+0xe0` exactly as `lt::CapturedImage`. In completed Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` renders plus the exact-focal Unit-2 `28mm` discriminator, every selected index-5 object is pointer-identical to an object constructed by `0xf2770` under `std::__1::__shared_ptr_emplace<lt::CapturedImage,...>`; selected keys retain public `CameraModule.id` alignment. This names the selected object type; later addenda name the RawImageFactory lookup container, frame-index key, and numeric CalibStage banks. Fields outside admitted public paths, whole `state+0x448`, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` / `CLM-C6-001` addendum: embedded-schema, two-body raw-wire, pinned constructor-copy, and Unit-1 four-focal runtime proof now names `CapturedImage+0x30` exactly as public `LightHeader.modules[camera].is_enabled`. `0xf2770` copies decoded module input `+0x60` byte-for-byte into `CapturedImage+0x30`; every accepted constructor packet matches the same-key public field. Representative wide/tele LRIs from both physical bodies explicitly store `is_enabled = true` for every listed module. The already-proven C6/key-15 mutation at `0x3c90a5` and downstream `+0x30` gates therefore operate on the runtime `CapturedImage.is_enabled` copy. False-input behavior, C6 terminality, alternate routes, and final image effect remain open. Claim statuses are unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned constructor copies plus `42` Unit-1 four-focal constructor packets now name four more direct public capture fields on the selected `lt::CapturedImage`: `+0x38 = CameraModule.sensor_exposure`, `+0x40 = sensor_analog_gain`, present optional `+0x44 = sensor_digital_gain`, and present optional `+0x104 = sensor_temparature` (the installed descriptor spelling). The runtime/public join is discriminating across `40` exposure values and two raw bit patterns for each gain; exact-wide and exact-tele Unit-2 LRIs independently carry the same public source fields under distinct Unit-2 calibration. The Unit-2 constructor-runtime join remains unproven because the attempted debugger run produced no packet. Lookup-context identity, selector-bank mapping, remaining fields, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` Unit-2 addendum: the failed debugger attempt above is superseded by a complete exact-focal Unit-2 `28mm` run. All ten camera keys `0..9` produce paired `0xf2770` constructor packets and a populated HDR; every packet exactly joins input and `CapturedImage` fields to the same-key Unit-2 public `sensor_exposure`, `sensor_analog_gain`, present `sensor_digital_gain`, and decoded `sensor_temparature`. The packet is discriminating across ten exposures, two analog-gain words, and temperatures `34..43`. This closes the second-body constructor-runtime join; repeating body-independent direct copies at all four Unit-2 focals is not required.

Additional `CLM-WARP-003` addendum: SHA-pinned RTTI, allocation, owner-accessor, constructor-call, and retained-pointer proof now identifies the former anonymous `state+0xe0` lookup context exactly as the raw-pointer word of a retained `shared_ptr<lt::RawImageFactory>`; `state+0xe8` is its control block. The factory retains `shared_ptr<lt::CaptureStack>` built from the capture input stream, and `0x1be970 -> 0xe6ba0` uses that CaptureStack to select the already-proven `lt::CapturedImage` by numeric factory/object key plus public `CameraModule.id`. Later addenda close factory `+0x10` / CapturedImage `+0x64` and numeric `CalibStage` mapping; whole-State identity and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned embedded-schema and generated-parser proof now closes that secondary key. The installed `CameraModule` parser decodes public varint field `15`, exact name `frame_index`, into generated module `+0x54` under has-bit `0x1000`; `0xf2770` copies it into `CapturedImage+0x64`; `0xe6ba0` compares that accessor against `RawImageFactory+0x10` before matching public `CameraModule.id`. The admitted renderer-owner path constructs the factory with selected frame index `0`. Existing completed Unit-1 four-focal reports confirm `42` live zero-valued copies, while discriminating Unit-1 `28mm` and Unit-2 `35mm` burst LRIs each carry all ten camera IDs at frame indices `0..3`; a corpus census finds `9,128` decodable LRIs with `{0}` and `248` with `{0,1,2,3}`. Therefore `CapturedImage+0x64 = CameraModule.frame_index` and factory `+0x10` is its selected-frame lookup key. The following CalibStage addendum closes numeric bank mapping; remaining fields/banks, whole-State identity, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` / `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: complete installed `0xf33d0` code-reference census, four-focal constructor packets, existing State/BA write-back custody, and post-initialization write watches on exact-focal LRIs from both physical calibration bodies now map the installed `CalibStage` names. `CalibStage 0` is `factory` at `CapturedImage+0x180..+0x1d3`; `CalibStage 1` is `current` at `CapturedImage+0x12c..+0x17f`. The constructor copies the same focus-evaluated public `FactoryModuleCalibration` packet into both banks. Selector `0` appears only at the first constructor initialization, while the paired initialization and all nine installed non-initial `0xf33d0` calls use selector `1`; the current bank is selected, transferred, BA-normalized, and written back while the factory bank remains the retained baseline. Both new body watches observe zero live-`libcp` writes to factory; Unit-2 observes a current write at `0xf345e`, while independent Unit-1 evidence already proves current-bank transfer and normalized write-back. This names the banks but does not make each complete 0x54-byte packet a direct protobuf message, name remaining `CapturedImage` / whole-State fields, or prove final image/source effect. Claim statuses are unchanged.

The RawImageFactory, frame-index, and CalibStage addenda supersede earlier
`CLM-WARP-003` wording that listed lookup-context identity, its secondary
numeric key, or numeric selector-bank mapping as open.

The Guidance-related "remain open" clauses in the following chronological
addenda likewise describe their evidence-stage boundaries. Version
`3.0.326` supersedes those clauses with exact final `[Y,U,V,1]` names and
formula.

Additional `CLM-WARP-003` addendum: pinned installed debug labels plus the admitted four-focal `0x276860` operand-source and completed payload-vector reports now name four formerly anonymous Cost-volume worker fields. `StereoLayer+0x288` is exactly `Guidance`; `+0x1e8/+0x200` are `Pixel buf` data/split pointers; `+0x198` is the `Min cost buf` data pointer; and `+0x168` is the `Line buf` data pointer. Static producer custody and one same-object `0x26c633` reuse event per focal tier prove index-5 Guidance reuses the first `Images` descriptor, which the composed-camera order identifies as `A1` at `28mm` / `35mm` and `B4` at `70mm` / `150mm`. Guidance bytes are locally expanded into Pixel buf vectors before the sampled saturating `uint16` Cost-volume recurrence. These are generated runtime image/scratch products, not direct calibration protobuf fields. Complete names for remaining recurrence sources/temporaries/caps/baselines, per-component Guidance semantics, full-map distributions, whole-State/selector identities, bound protobuf identity, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned constructor and SGM-recurrence proof closes target `+0x56/+0x58/+0x60` as body-independent installed algorithm tuning rather than public calibration/LRI inputs. `+0x56 = 1` is the adjacent-hypothesis SGM penalty `P1`; `+0x58 = 500.0` is the nominal guide-adaptive `P2/P1` ceiling scale; and `+0x60` contains three-channel exponential guide-distance decay coefficients exactly equal to `log2(e)/(18,48,48)` with a zero fourth lane. `0x27abb0` builds the source `StereoParams` packet from literals and binary constants, `0x26b750` copies the fields into the layer, auto-sidecar and no-sidecar constructor packets agree, and all four focal-tier worker packets consume the same values. Per-component semantics for the three Guidance lanes and the other recurrence sources/temporaries/caps/baselines remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum: SHA-pinned RTTI and call-chain proof now names the public producer behind first `Images` and reused `Guidance`: tier-anchor `CapturedImage` A1 wide or B4 tele is processed by `lt::StereoISP::CreateStereoImage`, whose first output argument is `Image<vec4x8ui>`. A Unit-1 `28mm` early-terminate watch proves exact 48-byte descriptor equality from the `CreateStereoImage` output through key-`0` cache insertion; static custody then traces cache accessor `0x226410` through `0x3ff43c -> 0x2681b0 -> 0x26ba90` into exact `StereoLayer+0x240` `Images[0]`, which the admitted `0x26c633` path reuses as `+0x288` `Guidance`. Public `CapturedImage`, `CalibData`, and `SoftISP` inputs feed this generated product; it is not a direct calibration protobuf field. Per-component semantics inside `vec4x8ui`, a direct Unit-2 descriptor-equality packet, other recurrence sources/temporaries/caps/baselines, full-map distributions, and final effect remain open. Claim status is unchanged.

Additional `CLM-WARP-003` addendum, corrected by `3.0.277`: SHA-pinned component-route proof plus a Unit-1 `28mm` two-invocation branch packet bounds the key-`0` Guidance components without assigning unsupported color names. Independent cache custody proves key `0` receives producer call `0`; that A1/A1 call copies its public `Image<vec4x32f>` output directly into the byte-pack source and rounds/saturates the four lanes without shuffling. Five spatial samples have independent `C0/C1/C2` color values and exact `C3=1`. A later A5/A1 call takes a separately verified fitted three-channel affine route and is not key `0`. The compared `0/0` and `4/0` operands are source/anchor camera keys, not output color-space selectors. The live SoftISP output-space/configuration and exact `C0..C2` semantics remain open; universal all-pixel/focal/body `C3=1` also remains open. Claim status is unchanged.

Additional `CLM-STEREO-001` addendum: complete Unit-1 `28/35/70/150mm` and exact-focal Unit-2 `28mm` SoftISP property captures select `collapse2`, default hot-pixel removal, native white point, and no configured SoftISP output color-space/color-correction/tone/denoise stage. SHA-pinned all-phase E3 workers normalize Bayer cells to `[R,G1,G2,B]` and emit the exact pre-YUV intermediate `[R,0.5*(G1+G2),B,1]`. Gated Unit-1 wide/tele receipts independently reach GRBG/BGGR workers. The live default hot-pixel stage is nonzero; focused Unit-1 `28mm` proof establishes the installed rank-6 statistic, public analog-gain-to-installed-RGB-LUT selector custody, exact `residual > 4*LUT[candidate]` marker threshold, `0x8000` marker lifecycle, and both spatial-isolation branches over 96 exact replays. Version `3.0.279` closes the LUT generator with a `4096/4096` bit-exact replay. Version `3.0.333` corrects `3.0.280` to one rank residual per rolling source row and a row-varying isolation selector. Version `3.0.335` closes the global edge with the exact six-pixel parity-preserving upper-median halo and complete `12,979,200/12,979,200` output replays for Unit-1 exact-`28mm`, Unit-2 exact-`28mm`, and Unit-1 canonical-`35mm`; wrong-phase controls are nonzero in every run. Version `3.0.326` independently proves the subsequent inlined `StereoISP::ConvertToYUV` stage and exact final `[Y,U,V,1]` byte pack. The selected claim is `PROVEN` / `SPEC_READY`; unselected compatibility arms remain outside scope.

Additional `CLM-STEREO-001` corrective addendum: direct `0x27bff0 -> 0x27adc0` call custody and runtime callback address point `0x659020/+0x30=0x27ce60` bind installed `StereoISP::ConvertToYUV::$_0` between collapse2 and the key-0 byte pack. Embedded schema plus exact-LRI decoding name the inputs as public `LightHeader.sensor_data.type=SENSOR_AR1335(2)` and `ViewPreferences.awb_gains`; the type-2 installed response is `[0.215550005,0.432307005,0.352142990]`. Exact float32 matrix construction, signed fast-`1/2.2` power, `[0,128,128,0]` offset, forced fourth lane one, and nearest-even/saturating pack reproduce every matrix word, float word, and output byte over complete `2080x1560x4` planes for canonical Unit-1 `28mm`, independent Unit-1 `L16_06689`, and exact-focal Unit-2 `28mm`. Existing four-focal producer/G-42 custody supplies merge-critical `28/35/70/150mm` applicability. Final Guidance is `[Y,U,V,1]`; pre-YUV collapse2 remains `[R,0.5*(G1+G2),B,1]`.

Additional `CLM-STEREO-001` / `CLM-CORRECTION-001` addendum: SHA-pinned scalar-vignetting, mono-SoftISP, exposure, and scalar-replication proof now reconstructs the complete wide A2/key-`1` `4160x3120` float plane directly from each LRI's public RAW10, sensor levels, runtime-indexed vignetting calibration, and A1/A2 exposure/analog fields. The exact order is reciprocal-multiply normalization without a black clamp, `(260,260)`-spaced bilinear vignetting with the installed float/double transitions, then the A1/A2 exposure-energy ratio; A2 public `relative_brightness` is bypassed by its admitted `(-1,-1)` Bayer-override sentinel. All `38,937,600` pixels match bit-for-bit across two Unit-1 scenes and exact-focal Unit-2 `28mm`, including negative below-black samples on the latter two, and all subsequent `[mono,mono,mono,1]` words match. Existing Unit-1 `28/35mm` custody supplies canonical wide-tier applicability; tele does not use this branch. This closes A2 public RAW construction, not the still-separate A1/A3/A4/A5 color-camera public-RAW reconstruction or low-parallax G-42 cost discrimination.

Version `3.0.337` adds a scoped `CLM-STEREO-001` / `CLM-CORRECTION-001` selected color-camera public-origin join. SHA-pinned installed workers and complete captured descriptor-tile replays prove stage-3 `f32(u16-black_level) * f32(1/(white_level-black_level))` normalization without clamp and stage-12 public `17x13` vignetting over a fixed `2080x1560` coordinate domain. Exact-`28mm` Unit-1 A1, distinct-calibration Unit-2 A1, and Unit-1 movable key `6` each match all `274,432` captured normalization storage values and all `196,608` captured lens RGB lanes; alpha is bit-preserved. The fixed cameras select distinct one-model public profiles by `lens_position`, while movable key `6` selects/interpolates four models at public `mirror_position=400`, ruling out a fixed-camera coincidence. Existing Unit-1 four-focal stage/correction receipts supply route incidence. This closes the two arithmetic/public-selection boundaries only; it is not a new end-to-end A1/A3/A4/A5 RAW-to-color replay, all-key numerical census, alternate lens-mode proof, or body/firmware attribution.

Additional `CLM-WARP-003` addendum: SHA-pinned allocator/helper/worker proof plus accepted four-focal term and payload-vector packets closes the remaining sampled SGM recurrence roles. `src0` / `src6` and their lane blend are predecessor directional path-cost candidates in `Line buf`; `%xmm1` is `P1`; `%xmm2` is the prior directional minimum from `Min cost buf` and is the normalization baseline; `%xmm3` is that baseline plus guide-adaptive `P2`; and `[r10+2*rdx]` is the per-pixel local matching-cost temporary. The recurrence writes current directional path cost to `Line buf`, accumulates it into the Cost-volume payload, and writes its current minimum to the other `Min cost buf` half. These are generated SGM terms, not additional public calibration/LRI fields. Exact disparity-direction lane convention beyond the already-validated SIMD splice, full-map distributions, final contribution, and acceptance/rejection remain open. Claim status is unchanged.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` correction: SHA-pinned RTTI/control-block proof joined to the admitted four-focal payload packets now exactly names owner `+0x6a8/+0x6b0` as `shared_ptr<lt::ImageCaches>`, visible `src1` vtable `0x65f140` as `lt::ReferenceImageCache`, direct contributor vtable `0x65f490` as `lt::SourceImageCache`, and the visible wrappers as `PipelineCache::initResAmp::$_1/$_2`. The admitted camera keys therefore make visible `src1` the A1 reference cache at `28mm` / `35mm` and the B4 reference cache at `70mm` / `150mm`, while direct contributors are B1..B5 or C1..C5 `SourceImageCache` objects. This supersedes shorthand that left visible `src1` potentially composite-ish or semantically anonymous. The following correction names visible `src2`; complete IRAMP reference/secondary/source use, multi-contributor reduction policy, C6 routing, and final acceptance/rejection remain open. Claim statuses are unchanged.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` refinement: SHA-pinned installed constructor/accessor bodies and all five `ReferenceImageCache` constructor-lambda RTTI records prove that visible `src1` retains exactly one public `lt::CapturedImage::Camera` key. Derived constructor `0x3e27a0`, base constructor `0x3ddd50`, and accessor `0x3ddf30` all use the same key with one `RawImageFactory`; the base stores it at cache `+0x90`. Joined to the admitted canonical constructor packets, that one origin is A1/key `0` at Unit-1 `28mm` / `35mm` and B4/key `8` at Unit-1 `70mm` / `150mm`. Thus `ReferenceImageCache` construction/access is not the hidden N-to-1 reducer. At this evidence stage, outer IRAMP policy was still open; the later v3.0.252 addenda supersede that boundary. The canonical quartet is one calibration body; capture-date or possible camera-firmware differences are not attributed to body.

Additional `CLM-PREFUSION-002` / `CLM-MERGE-005` refinement: SHA-pinned IRAMP operand custody joined to complete canonical four-focal probes now gives the inputs distinct algorithmic roles. `src1` is rendered into the coarse byte-domain registration guide and supplies warp-grid bounds; `src2` is rendered into the full `vec4` reference/baseline patch; each paired `srcs[i] + warps[i]` supplies a warped direct candidate patch. For valid non-sentinel partners, `0x36cde0(reference=src2 patch, candidate=direct patch)` writes tuple scalar `t`; the later body forms multiplier `(t + 2*max(0,t-0.5), t, t, t)`, multiplies the candidate patch, adds `t` to a denominator initialized at `0.2`, reciprocally normalizes, and performs the spatially weighted add. Thus the comparison has direct pixel-contribution consequence and is not debug metadata. Remaining closure is final global acceptance/rejection plus MonoFusion mode-`1` relevance/unreachability. The four canonical files are one calibration body; numerical capture differences are not attributed to body or firmware. Both claims remain blockers.

Additional `CLM-PREFUSION-002` / `CLM-MERGE-005` refinement: installed `0x36cde0` now has a clean-room scalar formula. It L1-normalizes candidate RGB to the prepared reference lane-0 total, computes clamped variance/covariance structural vectors at 256-sample fine and 64-sample coarse scales, applies fixed lifting-transform detail agreement to lane 0 with weights `-1/192` and `-1/96`, reduces each scale with `min4`, and returns `sqrt(coarse_min * fine_min)`. A canonical Unit-1 `35mm` prepared-input replay reproduces live score `0.488706499` (`0x3efa37bd`) bit-for-bit; previously admitted complete `28mm`, `35mm`, `70mm`, and `150mm` probes establish score-site liveness and contribution consequence. SSE reciprocal approximation and float32 operation order are part of bit-exact behavior. This closes the `0x36cde0` formula, not `0x36e530`, exhaustive candidate/sentinel policy, a public tuple-field name, or final acceptance/rejection.

Additional `CLM-PREFUSION-002` / `CLM-MERGE-005` refinement: installed `0x36e530` now has a clean-room formula. It reciprocates five `vec4` normalizers, scales each interleaved 16-by-16 coefficient by `selector(x,y)=min(v2(x),v2(y),4)` with `v2(0)=4`, then runs inverse CDF 9/7 lifting at strides `8,4,2,1`, horizontal before vertical, with symmetric endpoint replication and installed float32 order. All `65,536` one-hot basis outputs match the clean-room formula bit-for-bit. Canonical Unit-1 `35mm` baseline and nonbaseline whole-scratch replays each match every byte, while prior complete four-focal probes establish the same body/output handoff at `28mm`, `35mm`, `70mm`, and `150mm`. This closes the `0x36e530` formula, not exhaustive upstream candidate/sentinel policy, public tuple naming, MonoFusion mode `1`, or final acceptance/rejection.

Additional `CLM-MERGE-005` refinement: the matching IRAMP reference prior is now explicit. SHA-pinned `0x36b920` arithmetic multiplies every one of the 256 forward-spatial-CDF-9/7 `src2` coefficient vectors by exact float32 `0.2f` before storing the numerator tile, and the baseline packet supplies exact float32 `0.2f` to each of the five scale denominator vectors. Therefore reducer initialization is `numerator = 0.2f * forward97(src2)` and `denominator[0..4] = 0.2f` before surviving-candidate additions. Direct replay remains byte-exact, and the baseline-only inverse reconstructs the retained raw `src2` patch with maximum absolute float32 lifting error `1.9073486328125e-06`. Existing complete Unit-1 `28/35/70/150mm` reports join this fixed construction to all canonical focal tiers. The whole 80-byte setup table is not claimed to be all `0.2`, and no cross-body pixel equality or body/firmware causation is asserted.

Additional `CLM-PREFUSION-002` / `CLM-MERGE-005` refinement: exhaustive installed-body census now closes local IRAMP candidate/sentinel policy. Across complete `0x3661b0`, projected pairs are sentinelized only by source-domain or transformed-domain failure; partner records append only with positive source/grid extent, at least one finite projected pair, and strictly positive two-dimensional valid-pair span; exact `INT_MIN` pair entries skip; post-WTA neighborhood-boundary failure rewrites the same pair to sentinel; and every surviving non-sentinel score `t`, including zero, flows through branchless continuous weighting with no score threshold. Prior complete four-focal runtime joins exercise append, sentinel and valid targets, tuple production, and continuous score consumption. This closes local candidate policy, not later global final-output suppression, public internal-field naming, or MonoFusion mode-`1` relevance.

Additional `CLM-MERGE-005` / `CLM-MERGE-006` closure: a return-only LLDB intervention replaces `sqrtss xmm0,xmm0` at `0x36e515`, after all `0x36cde0` body work, with `xorps xmm0,xmm0; nop`; live-process receipts verify the exact bytes and therefore isolate score `t=0`. Completed canonical Unit-1 `35mm` and `70mm` profile-3 Radiance renders separate from repeated controls by `1742.937x` the wide repeat floor and `3.317x` the larger tele within-condition floor, respectively. Joined to complete Unit-1 four-focal score-use and descriptor-to-writer custody, this proves that direct-candidate score influence reaches the final file and that no later per-contributor accept/reject predicate remains after IRAMP composition on the tested CLI route. The final policy is exhaustive local sentinel/record admission followed by continuous score weighting and the admitted image-domain shaping/cache/resample/output chain. Direct differential scope is `35mm` / `70mm`; `28mm` / `150mm` carry joined mechanism/custody scope, not separate interventions. This is one-body route proof, not body/firmware or non-CLI-output universality. Both claims are `PROVEN` / `SPEC_READY`.

Additional `CLM-PREFUSION-002` closure: installed selector/constructor custody proves `MonoFusion+0x00` comes only from `0x40b2b0`, whose exact Demosaicking-config mapping is enum `0->mode0`, `1->mode1`, `2->mode1`, and `3->(byte_4==0)`. A same-LRI Unit-1 `35mm` profile matrix proves profiles `1` / `2` store mode `1` and execute `0x19f790`, while canonical Desktop profile `3` has config `(3,1)`, stores mode `0`, and executes `0x1a3c00`. Existing complete Unit-1 `28mm` / `35mm` and exact-focal Unit-2 `28mm` profile-3 reports confirm wide mode `0`; Unit-1 `70mm` / `150mm` and Unit-2 `70mm` confirm tele constructs no MonoFusion and uses direct B4. Mode `1` is therefore real but formally excluded from the canonical four-focal profile-3 route; at this selector admission its formula was still an unsupported profiles-1/2 compatibility path, never a profile-3 spec stub. Version `3.0.336` subsequently closes that separate mode-1 scalar body under `CLM-COMPAT-001`. Joined to the admitted IRAMP formulas, candidate policy, reconstruction, and final image consequence, the distributed pre-fusion mechanism is formula-closed for canonical profile-3 bridge HDR. `CLM-PREFUSION-002` is `PROVEN` / `SPEC_READY`; capture-date or possible firmware differences are not attributed to body.

Additional `CLM-PREFUSION-001` closure: the parent identity/topology row is reconciled with the stronger admitted evidence that superseded its old "composite-ish shared callable" premise. Exact installed RTTI and constructor/accessor proof name visible `src1` as one-camera `lt::ReferenceImageCache`, A1/key `0` wide and B4/key `8` tele. Visible `src2` is `PipelineCache::processLevel1` over an A1/A2 MonoFusion mode-0 generated descriptor at canonical profile-3 wide and direct B4 at tele. Four-focal IRAMP custody gives the outer roles: `src1` is the coarse registration guide, `src2` the full-vector reference/baseline, and five warped direct sources the candidates. Joined to the exact score/reconstruction formulas, exhaustive local candidate policy, final-file score consequence, and profile-3 mode selector, this parent claim is `PROVEN` / `SPEC_READY` at `28mm`, `35mm`, `70mm`, and `150mm`. Exact-focal Unit-2 `28mm` / `70mm` identity discriminators eliminate a single-body concern without asserting numeric invariance; capture-date or possible firmware differences are not attributed to body. MonoFusion mode `1` remains outside the canonical target as profiles-1/2 compatibility work.

Additional `CLM-ZOOM-002` closure: exact-focal public LRI decoding now gives camera IDs `5..15`, publicly `B1..B5,C1..C6`, at both `70mm` and `150mm` on each of the two physical calibration signatures. Completed canonical Unit-1 `70mm` and `150mm` constructor runs independently create all eleven keys with initial public `CapturedImage.is_enabled = 1` and write `10432x7824` HDR output. Canonical `150mm` firing topology is therefore `5B+6C`, not `6C only`; `70mm` verifies the same tele-tier mechanism. This initial firing claim is separate from the later admitted C6/key-15 clear and exclusion. Cross-body agreement is corroboration only: capture-date or possible firmware differences are not attributed to body.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` correction: SHA-pinned RTTI joined to the admitted four-focal executor packets now names visible `src2` exactly. Wrapper address point `0x65f6e8` is `PipelineCache::initResAmp::$_2`; `0x3ecd80 -> 0x3ebb80` installs callback address point `0x65f7e8`, whose RTTI is the `ImageWarpClamped<ResamplerFilter=2, vec4x32f>` lambda inside `lt::PipelineCache::processLevel1`; and callback slot `+0x30 = 0x3ed2e0` is runtime-observed at `28mm`, `35mm`, `70mm`, and `150mm`. The adjacent direct-contributor wrapper is the distinct `initResAmp::$_3` address point `0x65f768`, slot `+0x30 = 0x3eced0`. Thus visible `src2` is exact PipelineCache level-1 one-generated-descriptor resampling/materialization, not an unnamed reducer. The generated descriptor's tier-dependent camera ancestry is closed by the later `lt::MonoFusion` correction; complete distributed reduction policy and final acceptance/rejection remain open. Claim statuses are unchanged.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` / `CLM-C6-001` correction: SHA-pinned `0xf2770` copy bytes, embedded protobuf descriptors, all `42` admitted Unit-1 four-focal constructor events, and exact-focal Unit-2 public carriers now name item `+0x58/+0x5c` exactly as `CameraModule.sensor_bayer_red_override.{x,y}`, public type `Point2I`. Constructor input `+0x28` holds that optional public message and `0xf2d62..0xf2d71` copies its packed `x/y` into the item. A2/key `1` is the unique wide `(-1,-1)` override and C6/key `15` the unique tele `(-1,-1)` override on both bodies. Thus the `FusionCacheBayer` scan's sign-bit pair has a concrete public source/name. The algorithmic purpose of the selector, optional `FusionCacheBayer+0x20`, complete distributed reduction policy, C6 terminal effect, and final acceptance/rejection remain open. Claim statuses are unchanged.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` correction: SHA-pinned `FusionCacheBayer::0x406a10` source-lookup bytes plus an early-terminate two-body/two-tier runtime matrix identify the visible `src2` target camera. `FusionCacheBayer+0x8 -> 0x1bea00` derives A1/key `0` at wide and B4/key `8` at tele; `0x1be970` returns the same-key active `lt::CapturedImage`, proven by exact shared-control RTTI address point `0x665eb8`. Unit-1 and Unit-2 28mm/70mm agree. The descriptor remains an internal generated image, not a direct protobuf field; the following correction closes its tested tier-dependent camera ancestry. Claim statuses are unchanged.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` correction: pinned installed strings, `MonoFusion::initialize` callback RTTI, constructor/process opcodes, the canonical Unit-1 quartet, and exact-focal Unit-2 28mm/70mm discriminators identify optional `FusionCacheBayer+0x20` as `lt::MonoFusion`. At wide, the target is A1/key `0`, `MonoFusion+0xc0` contains only A2/key `1`, its public eligibility source is `CameraModule.sensor_bayer_red_override=(-1,-1)`, and `0x1b3530` generates a distinct same-shaped descriptor passed to `0x40721b -> 0x31b110`. At tele, MonoFusion has zero activity and the direct B4 route is used. All six renders complete HDR. The outer `PipelineCache::processLevel1` worker resamples one generated descriptor, but wide ancestry is A1 target plus A2 MonoFusion, not one camera. Immediate `0x1b3530` post-worker math is decoded; the following addendum narrows `0x1b37a0`. Distributed reduction and final acceptance/rejection remain open.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: SHA-pinned installed bodies, embedded protobuf schemas, direct LRI decoding, complete Unit-1 `28mm` / `35mm`, and exact-focal Unit-2 `28mm` renders now decode production-profile MonoFusion mode `0`. A2 capture selectors are public `CameraModule.sensor_analog_gain`, `sensor_digital_gain`, and `sensor_exposure`. Corrective constructor proof shows that `int(sensor_analog_gain*100)` selects a row from an installed 28-row `SENSOR_AR1335_MONO` panchromatic table at `0x5ad7c0` (896 bytes, SHA-256 `e0e40ce025012b1df9c96d0ad59d00f45722d521c48a3bc04de806ae3467d878`), not from the LRI's measurably different public type-2 `SensorCharacterization.vst_model[].panchromatic.{a,b}` rows. The initializer observes one mono source and four same-group non-mono records, uses installed response `R=2.3183400630950928`, and stores `alpha=C/(N*R+C)`, `noise_scale=1+C/R`, and installed panchromatic `a,b` divided by `R*C`. Its source normalization is exact float32 `(raw_A2-B)*frame_scale+B`, where `frame_scale=(A1.sensor_exposure*A1.sensor_analog_gain)/(A2.sensor_exposure*A2.sensor_analog_gain*R)`; public `sensor_digital_gain` is not an operand. Mode `0` processes flow-aligned `16x16` patches at step `8` through the SHA-pinned normalized 5/3 lifting forward/inverse pair, an exact installed 16x16 coefficient-weight table, patch-noise variance, coefficient Wiener blending, and separable `0.5*(1-cos(2*pi*(i+0.5)/16))` overlap-add; its final scalar blend is `alpha*target + (1-alpha)/N*accumulated_sources`. Exhaustive installed 256-basis matrices close both transform directions: outer-even/first-detail replication supplies the two boundaries, smooth/detail are stored at even/odd lattice positions, forward recurses at strides `1,2,4,8`, and inverse reverses at `8,4,2,1`. Its secondary map uses `X=sum(1-c_i)` and `Y=sum(c_i^2)` from the Wiener confidences and overlap-adds `(alpha+(1-alpha)*X/N)^2 + ((1-alpha)^2*C/(N^2*R))*Y`; SHA-pinned callback `0x1b33a0` and exact float32 returns are verified at Unit-1 `35mm` and exact-focal Unit-2 `28mm`. Canonical `70mm` / `150mm` remain on the proven direct-B4 route with no MonoFusion. Plain row-major orthonormal DCT-II is refuted. At this evidence stage, mode `1` disposition and outer acceptance were open; the later v3.0.251/v3.0.252 closures supersede both boundaries.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom static/runtime proof now bounds the immediate internal field assembly path for the tracked index-5 `StereoLayer<false>+0xf8` source object. Static extraction shows `0x26be50 -> 0x29a140` produces stack locals, `0x26be5b` writes low `u32` control value `8` from `rbp-0xb0` into `this+0xf8`, `0x26be73 -> 0x28f420` moves a three-qword header from `rbp-0xa8` into `this+0x100`, and `0x26be89 -> 0xf340` moves a descriptor from `rbp-0x90` into `this+0x118`. Runtime probes across `28mm`, `35mm`, `70mm`, and `150mm` validate the control transition `2 -> 8`, the header move, the descriptor move, descriptor dimensions `2080 x 1560`, stride `2080`, and later continuity into `0x26e4c6`, `0x299c70`, and `0x267010`. This narrows internal field custody only; it does not prove public field names, public LRI/protobuf origin, public calibration semantics, physical meaning, remaining full-map distributions beyond the later-admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom static/runtime proof now bounds the immediate `0x29a140` source-local producer body behind that field-assembly edge. Static extraction shows `0x29a140` stores incoming control `ecx = 8` into the output local, zeroes output fields `+0x08..+0x48`, calls `0x299eb0` with the input descriptor, `this+0x208`, and control value, calls `0x28f490` with destination `output+0x08`, `rsi = rax`, and `edx = 0x40`, then calls `0x299fd0` with the output local, input descriptor, and `this+0x208`. Runtime probes across `28mm`, `35mm`, `70mm`, and `150mm` validate the caller/entry arguments, the still-zero sampled header after `0x299eb0`, the populated header after `0x28f490`, the still-zero descriptor before `0x299fd0`, the populated `2080 x 1560`, stride-`2080` descriptor and sampled record-base/offset-table state after `0x299fd0`, exact caller-post local continuity, and later `this+0xf8` / `this+0xe0` continuity into `0x299c70` / `0x267010`. A follow-up validator now proves the full `0x299eb0` returned byte span and the sampled `0x299fd0` offset/record headers from live input and `this+0x208` mask data: `rounded = ceil(input_u16_2 / 8) * 8`, factor `2` for nonzero mask bytes and `3` for zero mask bytes, `record_size = 8 + factor * rounded`, and record header `(input_u16_0, input_u16_2, 1, rounded)`. The specific byte-span and mask-census values recorded in the evidence doc are runtime samples from that admitted run, not stable constants. This narrows immediate internal producer mechanics only; it does not prove public field names, public LRI/protobuf origin, public calibration semantics, physical meaning, stable record constants, exact `0x28f490` helper semantics beyond the observed header-population boundary, final source contribution, anti-ghosting behavior, or final acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom watchpoint proof now bounds the sampled source-record payload writer after `0x299fd0`. Runtime probes arm hardware write-watchpoints on the first 8 payload bytes at `record+0x08` for the first two source-local records only after those bytes are observed as zero. Across `28mm`, `35mm`, `70mm`, and `150mm`, all sampled payload mutations stop at `libcp+0x277a16` inside `0x276860`; static disassembly shows this is immediately after `libcp+0x277a10: movdqu xmmword ptr [r9 + 2*rdx], xmm5`, and register disambiguation proves each watched address matches the `r9 + 2*rdx` destination and not the neighboring `rcx + 2*rdx` store. This narrows sampled internal payload mutation custody only; it does not prove `%xmm5` arithmetic, full-map payload distributions, public field/origin semantics, final source contribution, anti-ghosting behavior, or acceptance/rejection.

Additional `CLM-WARP-003` addendum: follow-up no-auto-LRIS four-zoom vector proof now validates the sampled SIMD increment formula feeding that payload writer inside `0x276860`. For sampled stops at `libcp+0x277a16`, runtime packets capture the live vectors read from `[rsi + 2*rax]`, `[rdi + 2*rdx]`, and `[r10 + 2*rdx]`, the live `%xmm1/%xmm2/%xmm3` operands, and the side/payload destinations. A validator reconstructs the `0x2779b0..0x277a10` unsigned-16 SIMD recurrence: neighbor blend, saturating add/min chain, saturating subtract into `%xmm0`, side-store to `[rcx + 2*rdx]`, and saturating payload add into `%xmm5` / `[r9 + 2*rdx]` for watched lanes with known previous bytes. The stricter rerun also proves sampled internal custody for stable operands/destinations: `rbp-0x1c8` equals the tracked target object; `object+0x108/+0x138/+0x130` match the source-local record base / offset table / stride observed after `0x299fd0`; `r9 == object+0x108 + sampled_record_offset + 8`; `r10 == rbp-0x2e0`; `rbp-0x200 == object+0x168`; `rbp-0x210 == object+0x198`; and `%xmm1` is the unsigned-16 broadcast of `object+0x56`. A follow-up early-terminate packet proof pairs `0x27786b`, `0x27791d`, and `0x277945` on the same target-index-5 context across `28mm`, `35mm`, `70mm`, and `150mm`, proving sampled `%xmm2` is prepared from a `uint16` lookup through `rbp-0x210`, sampled `%xmm3` is prepared from the live post-add `edx`, and both broadcast-ready registers match those paired scalar values. A further step-driven non-degenerate packet proof validates the sampled `%xmm3` pre-add integer term as `trunc_i32(f32(u16[object+0x56]) * f32[object+0x58] * xmm4_low)` and validates the post-add `%xmm3` scalar as that term plus the paired table value on one stepped packet per focal tier. A follow-up `%xmm4` origin proof reconstructs one stepped packet per focal tier through `0x27786f..0x277903`: `%xmm4_low` is formed from `xmm8 - [[rbp-0x208] + rdx]`, `object+0x60`, the observed mask/blend/horizontal-sum/sign/clamp sequence, and local polynomial/exponent-bit assembly; the same verifier finds zero exact full-vector and zero exact nonzero scalar-word LRI payload hits for sampled `object+0x60`. A follow-up operand-source context proof binds sampled `%xmm8` to target-object `+0x200` after local guide-byte conversion from target `+0x288`, binds `[rbp-0x208]` to target `+0x1e8`, and binds `[rbp-0x210]` to target `+0x198`. This proves sampled internal vector arithmetic plus narrow immediate operand/destination custody only; it does not prove public operand meaning/origin, full-map payload distributions, all records/lane positions, final source contribution, anti-ghosting behavior, or acceptance/rejection.

Additional `CLM-OUTPUT-001` addendum: installed-bundle static proof now refutes the stale final-compositing RB-tree / `std::list` anchor for the admitted queue/drain surface, and narrowed four-zoom LLDB proof now verifies runtime liveness for the producer insert edge `0x3bf8bc -> 0x3bfc40`, insert body `0x3bfc40`, drain body `0x3bfe60`, orchestrator drain edge `0x3bcc51 -> 0x3bfe60`, and post-gather 0x70-stride filter loop `0x3bccc0`. Follow-up switch census shows that the tested CLI bridge-HDR path reaches only record types / case targets `1`, `2`, `3`, `11`, and `16`; case `4` target `0x3bcf20`, containing the previously highlighted ImagePyramid/per-tile-dispatch branch, records zero hits under the canonical quartet. The case-4 zero-hit fact is scoped to the tested CLI runs. The proven surface is an intrusive queue and 0x70-stride drain/filter/switch topology only. A later CLI HDR writer-boundary addendum below narrows the file-sink boundary for the tested CLI HDR path; this addendum by itself does not prove byte-level copy-vs-blend behavior, complete or non-CLI file/display sink coverage, final output semantics, anti-ghosting policy, or final merge acceptance/rejection.

Additional `CLM-OUTPUT-001` case-`2` helper addendum: follow-up four-zoom LLDB proof now bounds the live post-gather case-`2` helper path. The canonical CLI bridge-HDR quartet reaches case target `0x3bd308`, helper `0x3bf2f0`, callsites `0x3bf331`, `0x3bf344`, `0x3bf354`, `0x3bf382`, helper return `0x3bf4b8`, and post-helper append callsite `0x3bd31d` once per render. The same runs record zero hits at alternate/helper callback/completion/error sites `0x3bf39a`, `0x3bf3be`, `0x3bf419`, `0x3bf481`, `0x3bf49a`, `0x3bf4c7`, `0x3bf50f`, and `0x3bf55a`. The captured case-`2` record has `field_i32_0x00 = 2`, `field_i32_0x10 = 1`, `field_i32_0x14 = 0`, `field_i32_0x24 = 2`, `field_i32_0x28 = 0`, and focal-specific `field_i32_0x20` values `3912`, `3120`, `3312`, and `1560` for `28mm`, `35mm`, `70mm`, and `150mm`. This is branch/callsite and local field-shape proof only; it does not classify helper bodies, final sink, copy-vs-blend behavior, final output semantics, anti-ghosting policy, or final merge acceptance/rejection.

Additional `CLM-OUTPUT-001` case-`11` callback-gate addendum: follow-up four-zoom LLDB proof now bounds the live post-gather case-`11` callback gate. The canonical CLI bridge-HDR quartet reaches case target `0x3bd453` and owner `+0x5d0` null-test site `0x3bd45d` with counts `7`, `7`, `6`, and `6` for `28mm`, `35mm`, `70mm`, and `150mm`; every captured sample observes owner `+0x5d0 = 0`, and callback callsite `0x3bd47b` plus callback return site `0x3bd47d` record zero hits. This is tested-path gate behavior only; it does not prove case-`11` global terminality, public record semantics, final sink, copy-vs-blend behavior, final output semantics, anti-ghosting policy, or final merge acceptance/rejection.

Additional `CLM-OUTPUT-001` case-`16` cleanup addendum: follow-up four-zoom LLDB proof now bounds the live post-gather case-`16` helper cleanup path. The canonical CLI bridge-HDR quartet reaches case target `0x3bd2f7`, helper callsite `0x3bd2fe -> 0x3adad0`, and helper return site `0x3bd303` once per render. Static disassembly shows case `16` passes `rbp-0x840` to helper `0x3adad0`; runtime packets show `rbp-0x840 == owner+0xd0`, the captured case-`16` record has `field_i32_0x00 = 16`, `field_i32_0x04 = 2`, and captured remaining i32 fields zero in all four admitted runs. Helper `0x3adad0` is entered four times per render overall; every captured helper invocation reaches raw local-count branch `0x3adb16` with `rbp-0x38 = 0`, then cleanup path `0x3adc74 -> 0x3ae490`, local-base cleanup site `0x3adcc3`, and return `0x3adcdf`. Callback site `0x3adb6e`, release sites `0x3adb9b`, `0x3adbaa`, `0x3adbb9`, and bad-function throw path `0x3adc3f` record zero hits under the tested quartet. This is tested-path cleanup behavior only; it does not prove case-`16` global terminality, public field/local/context semantics, helper body semantics, final sink, copy-vs-blend behavior, final output semantics, anti-ghosting policy, or final merge acceptance/rejection.

Additional `CLM-OUTPUT-001` case-`1` / case-`3` boundary addendum: follow-up four-zoom LLDB proof now bounds the remaining live post-gather case-`1` and case-`3` switch targets under the canonical CLI bridge-HDR quartet. Case `1` reaches target `0x3bce77`, mutex lock call `0x3bce7e`, type check `0x3bce83`, flag write `0x3bce92`, condition-broadcast call `0x3bce9c`, mutex unlock call `0x3bcea8`, and return jump `0x3bcead` once per render; captured packets show `field_i32_0x00 = 1` and the pointed flag byte changes from `0` before `0x3bce92` to `1` after `0x3bce92`. Case `3` reaches target `0x3bcee3`, pre-helper callsite `0x3bceeb -> 0x3b07c0`, helper callsite `0x3bcf16 -> 0x4182a0`, and return jump `0x3bcf1b` once per render; captured packets show `field_i32_0x00 = 3` and exact argument custody for `record+0x10`, `record+0x20`, `record+0x50`, `record+0x60`, and `record+0x68` into helper `0x4182a0`. Helper `0x4182a0` reaches selected normal callsites `0x418380`, `0x41847d`, `0x4184b0`, `0x41850b`, `0x418518`, `0x418908`, and normal-return site `0x418bfd` once per render, while case mismatch targets `0x3bea7b` / `0x3beacd` and helper error labels `0x418d38` / `0x418e27` record zero hits under the tested quartet. This is tested-path boundary and operand-custody proof only; it does not prove public field/context semantics, helper body semantics, final sink, copy-vs-blend behavior, final output semantics, anti-ghosting policy, or final merge acceptance/rejection.

Additional `CLM-OUTPUT-001` case-`3` output-configuration addendum: static plus reused runtime proof now bounds the live final-compositing case-`3` output-configuration path. The canonical CLI bridge-HDR quartet passes `10432 x 7824` dimensions and format argument `3` into `0x4182a0`; each run observes color-space selector value `4` at `0x4186a3`, reaches `0x418908 -> 0x41e180` with format argument `3`, returns normally, and records zero hits at error labels `0x418d38` / `0x418e27`. Static disassembly plus live `r12d = 3` proves the tested path uses the format-`3` branch and bypasses the format-`2` compression subpath containing `0x41880f`. The downstream writer receives decoded `.hdr`, row bytes `166912`, and bytes-per-pixel field `16`. This is output-configuration and writer-custody proof only; it does not prove public enum names, pixel correctness, copy-vs-blend behavior, source contribution, anti-ghosting policy, final acceptance/rejection, or non-CLI sinks.

Additional `CLM-OUTPUT-001` CLI HDR writer-boundary addendum: follow-up four-zoom LLDB proof now bounds the tested CLI HDR writer boundary after the live case-`3` helper path. The canonical CLI bridge-HDR quartet reaches helper `0x41e180` once per render with entry dimensions `10432 x 7824` and export-format argument `3`, follows the `.hdr` branch, calls writer helper `0x2326a0` at `0x41e599`, reaches cleanup `0x41ea07`, and reaches normal-return site `0x41f9eb`. The same runs record zero hits at PPM branch target `0x41e953`, PPM writer call `0x41e9ea`, unexpected export-format path `0x41fa93`, invalid export-size path `0x41fad4`, and `0x2326a0` no-data error path `0x232758`. Writer helper `0x2326a0` receives a populated descriptor with width `10432`, height `7824`, stride/count field `10432`, nonzero data pointer, and decoded extension `.hdr`; reaches descriptor data check `0x2326b6`, writer-factory call `0x2326ec`, virtual writer call `0x232731`, after-call site `0x232733`, and normal-return site `0x23274a` once per render; and the virtual writer-call descriptor has row bytes `166912`, bytes-per-pixel field `16`, and the same nonzero data pointer. The emitted files identify as `Radiance HDR image data` under the OS `file` command. This is tested CLI HDR writer-boundary and descriptor-custody proof only; it does not prove pixel correctness, copy-vs-blend behavior, anti-ghosting policy, source contribution, final merge acceptance/rejection, opaque third-argument semantics, or non-CLI/display/preview sinks.

Additional `CLM-C6-001` terminal closure: on canonical tele bridge HDR, C6/key `15` is constructed with public `CapturedImage.is_enabled = 1` and cleared at `0x3c90a5`; all admitted later same-byte observations remain `0`, the direct-payload and stereo candidate gates exclude it, all 58 direct key-getter sites are censused, and the residual ImagePyramid route is full-buffer zero-filled with admitted downstream/data-watch exclusions. A controlled differential now proves the terminal consequence. At both `70mm` and `150mm`, two baseline repeats leave the clear intact, exit `0`, and write populated HDR; two forced-active repeats restore only the same key-15 byte from `0` to `1` after `0x3c90a5`, then deterministically enter the SHA-pinned per-key `SourceImageCache` constructor, reject C6's public `sensor_bayer_red_override=(-1,-1)` with `Super-res does not support mono modules!`, exit `1`, and write zero image bytes. Thus C6 is a fired mono module terminally excluded from successful tele super-resolution image payload construction and must not be admitted as an image contributor on this tested path. Runtime differential scope is canonical Unit-1 tele; the C6 public mono-override identity is independently two-body verified. `CLM-C6-001` is `PROVEN` for canonical tele bridge HDR and `SPEC_READY`; GUI/non-bridge paths remain outside scope.

Additional `CLM-PREFUSION-002` corrective addendum: the previously omitted production mode-0 MonoFusion flow is now formula- and bit-closed. The installed builder consumes five `uint16` A1/A2 pyramid levels (`4160x3120`, `2080x1560`, `520x390`, `130x97`, `32x24`) and runs strict-`<`, `dy`-then-`dx` unsigned-16 SAD searches at `8x8/r8`, `8x8/r4`, `16x16/r8`, `16x16/r4`, then full-resolution overlap `16x16/r2` at spacing 8. Intermediate stages select predictors from a clamped `3x3` prior neighborhood, scale prior vectors by 4, apply the exact installed float32 quadratic fit when its full `3x3` cost neighborhood exists, and preserve the installed nested-add order; the final stage scales its prior by 2, uses integer refinement only, and produces `519x389` vectors. Its strict rejection threshold is `sqrt(selected_public_vignetting_gain)*256*(30+30*clamp((sensor_analog_gain-1)/3,0,1))`, sampled at the pre-local predictor source origin; rejected local vectors return `-1000000` before the wrapper adds predictor displacement. Independent replay matches every one of `215,473` vectors bit-for-bit on each of two physical exact-28mm inputs (`430,946` total), including `73,073` versus `521` body/scene-specific rejection decisions and all 64 captured quadratic fits. Installed formula scope is body/focal independent; runtime numerical scope is exact-28mm on both bodies. Prior admitted route proof supplies canonical four-focal applicability: profile-3 `28mm`/`35mm` use this same mode-0 path, while `70mm`/`150mm` construct no MonoFusion and use direct B4. No 35mm full-vector replay, cross-body numeric invariance, firmware cause, or mode-1 formula is claimed. `CLM-PREFUSION-002` remains `PROVEN` / `SPEC_READY`, now with the live nonzero flow requirement explicit; a zero-residual gather is not equivalent.

Version `3.0.338` closes the previously unstated producer of those captured mode-0 flow operands. SHA-pinned custody binds `0x1b6340 -> 0x1991d0 -> 0x199140 -> 0x189cb0/0x1895d0`. Both reference and source level 0 are reconstructed from public LRI inputs over all `12,979,200` pixels on each exact-`28mm` body; the corrected A2 source join explicitly includes the admitted full-frame hot-pixel stage, which changes `19,586` Unit-1 and `8,404` Unit-2 pixels before vignetting/round-clamp/sqrt-LUT encoding. FastCollapse then uses factors `(2,4,4,4)`, exact symmetric 6- and 10-effective-tap float32 kernels (stored with one terminal zero), vertical-before-horizontal binary32 multiply/add order, phases `1/2`, nearest-edge coordinate clamp, floor dimensions, and final truncation to `uint16`. Complete replay matches all `13,843,912` generated level-1..4 samples across both roles and bodies. Prior route proof supplies profile-3 `28/35mm` applicability and `70/150mm` no-MonoFusion exclusion. No separate 35mm numerical pyramid, profiles-1/2 mode-1 construction, numeric invariance, or body/firmware cause is claimed. `CLM-PREFUSION-002` remains `PROVEN` / `SPEC_READY`; clean-room flow construction may no longer start from captured pyramids.

Version `3.0.339` corrects the earlier cross-talk exclusion. The old census
said generic executor `0x2e20` invokes vtable slot `+0x30`, but breakpointed
the four slot-`+0x38` functions. Installed-byte verification binds the real
callbacks to `0xfebf0`, `0x100680`, `0x103120`, and `0x1054d0`. Completed
Unit-1 `28/35/70/150mm` and exact-`70mm` Unit-2 profile-3 renders all execute
only `RemoveCrossTalkGeneric<float,true>` callback `0x1054d0`. A focused A1
trace records `1,247` callback hits and joins `240/240` stage-6 demosaic input
views to the stage-5 scalar allocation. Therefore versions `3.0.263` and the
cross-talk portion of `3.0.265` are superseded. Public vignetting construction
and sampling remain closed, but `CLM-CORRECTION-001` is `PARTIAL` / `BLOCKER`
until the selected scalar cross-talk matrix/IR interpolation, Bayer-neighbor,
coordinate, boundary, and output arithmetic replay independently.

Version `3.0.340` closes that selected scalar cross-talk path. SHA-pinned
installed custody proves callback `+0x28` is the camera-keyed public
`FactoryModuleCalibration.vignetting.crosstalk` `17x13` 4x4 float32 grid,
while `+0x30` is a generated diagonal IR grid. This public selection is
distinct from vignetting: cross-talk uses public
`FactoryModuleCalibration.camera_id`; the vignetting profile continues to use
calibration-vector ordinal `CapturedImage+0x60`. Exact replay from public RAW
closes Bayer ratio maps, the `17x13` fit, installed A/B/C table selection,
all 20 amount scores and the optional C gate, the generated IR matrix, the
public-AWB similarity transform, matrix-coordinate interpolation,
Bayer-neighbor/reflection recurrence, limiter, and output blend. Unit-1 and
Unit-2 exact-`28mm` A1 packets each match `67,600/67,600` scalar outputs
bit-for-bit; a Unit-1 movable B2 packet independently joins public camera ID
`6` and its distinct matrix/table group. Companion complete renders supply
Unit-1 `28/35/70/150mm` and exact-`70mm` Unit-2 liveness plus demosaic
custody. `CLM-CORRECTION-001` is again `PROVEN` / `SPEC_READY` for selected
profile-3 `float,true`. Other profiles/specializations, a nonzero-limiter
numeric packet, all-camera census, firmware invariance, and body/firmware
cause are not claimed.

Version `3.0.341` closes the remaining public-name custody for the selected
cross-talk A/B/C-table inputs. Embedded-schema and installed-converter proof
bind the sensor selector to public `LightHeader.sensor_data.type`, observed as
`SENSOR_AR1335 (2)`, and bind the former internal `variant_flag` to the public
predicate that at least one `FactoryModuleCalibration.color[].color_matrix`
is present. The amount producer converts the same admitted public-AWB/A-D65
scene chromaticity through installed Robertson helper `0xab2e0`; its captured
CCT reaches the fit bit-for-bit at `4953.66357421875` on Unit-1 exact-`28mm`
and `4175.767578125` on distinct-calibration Unit-2 exact-`28mm`. Both inputs
contain 42 public color-matrix records and produce variant `1`; Unit-1 movable
B2 shares the scene CCT while independently exercising camera group 1. The
installed selector formula is body/focal independent, while exact selector
custody is two-body exact-`28mm` plus movable B2 and the upstream public scene
solve retains its separately admitted Unit-1 four-focal scope. No non-AR1335,
absent-matrix, alternate-profile, firmware-invariance, or body-cause claim is
added. `CLM-CORRECTION-001` remains `PROVEN` / `SPEC_READY`.

Version `3.0.342` closes the portable bit formula for the current-reference
unrefined SSE reciprocal primitive used by admitted demosaic, denoise,
MonoFusion, and IRAMP arithmetic. For every finite normal float32 input, the
top 11 fraction bits select one of 2,048 midpoint-reciprocal bins, the low 12
input bits are ignored, and an integer quotient produces the exact output
fraction and reciprocal exponent; explicit branches cover signed zero,
subnormal, underflow, infinity, and NaN. A signed x86_64 oracle under the same
Apple-Silicon Rosetta environment as the installed probes matches the portable
formula for `6,242,316/6,242,316` cases, with packed `rcpps` lanes identical
to scalar `rcpss`. This removes exact IEEE division as a necessary clean-room
substitute. It does not claim identical approximation bits on every historical
native-Intel microarchitecture, and it does not alter any parent formula's
route, focal, or runtime-packet scope.

Version `3.0.343` closes the selected PatchNLM producer topology and
full-frame boundary policy. The parent seeds numerator and denominator as
`0.01*source` and `0.01`, traverses `[2,width-1)x[2,height-1)` in four
`128x128` quadrant passes, and phases step-2 reference centers with a
deterministic 12,553-pair 48-bit LCG vector. Despite public `patch_size=5`,
the selected `<4>` worker loads offsets `{-2,-1,0,+1}^2`, evaluates a
row-parity checkerboard of candidate centers in a full clipped-and-shifted
five-wide window, uses the reference center's `range_scale`, locally
accumulates 16 weighted source-patch vectors, and overlap-adds them plus the
shared weight sum into the 16 reference-patch output locations. The positive seed
and valid interior patches are the edge policy; there is no clamped-patch
branch. A full-frame pass uses unrefined `rcpps` and restores source alpha.
Installed-static formula scope is body/focal independent, joined to admitted
Unit-1 four-focal and exact-`35mm` Unit-2 route liveness. Concurrent
task-addition order and a full-frame bit replay are not claimed.

Version `3.0.344` corrects and strengthens `CLM-DEMOSAIC-002`. The original
local replay had assigned both directional corrections to chroma sites and
applied the source endpoint clamp to derived planes. Installed row-graph
custody and tiled intermediate captures instead prove red/blue first-stage and
green refined-stage ownership, finite virtual `P/H/A` halos, virtual residual
rows, asymmetric horizontal residual guards, and exact 21-tap addition order.
An independent clean-room implementation matches every one of `51,916,800`
RGBA float32 words on both Unit-1 and distinct-calibration Unit-2 exact-`28mm`
A1 operands. It also matches `66,560/66,560` captured guide/residual words,
including internal tile edges. Installed-static formula scope covers all four
CFA phases and is body/focal independent; public phase-carrier scope remains
two-body `28/35/70/150mm`. Other installed builds and firmware invariance are
not claimed.

Version `3.0.345` closes the immediate mode-0 MonoFusion color wrapper omitted
from the implementation-facing narrative. Installed `0x1b3530` transforms A1
RGB into a deterministic response/opponent basis, replaces only coordinate
zero with `(fused_scalar-black_level)*float32(1/(white_level-black_level))`,
preserves the two opponent coordinates and alpha, then applies the exact
float32 inverse basis. The first basis row is installed AR1335 response
`[0.2155500054,0.4323070049,0.3521429896]`; the other rows are generated by
SHA-pinned helper `0xab830`, and helper `0x9d7e0` generates the inverse. These
two object packs are derived matrices, not independently named protobuf
fields. Public `LightHeader.sensor_data.type=SENSOR_AR1335(2)` selects the
response, while public `SensorCharacterization.black_level=42` and
`white_level=1023` supply normalization. Exact-`28mm` Unit-1 and Unit-2 live
tiles replay all `36` matrix words and `24` sampled output words bit-for-bit.
Prior route proof supplies canonical four-focal scope: profile-3 `28mm/35mm`
use this wrapper and `70mm/150mm` bypass MonoFusion through direct B4. No
separate 35mm numerical replay, scene-pixel invariance, firmware cause, or
other-build claim is added. `CLM-PREFUSION-002` remains `PROVEN` /
`SPEC_READY`; scalar RGB-ratio reinjection is not equivalent.

Version `3.0.346` corrects three implementation-significant mode-0
MonoFusion details with a single SHA-pinned live-packet replay. The patch-noise
scalar `mu` is the row-major binary32 mean of a separate `8x8` view from the
selected public-vignetting auxiliary map, not the target-patch arithmetic
mean; the target patch supplies the harmonic statistic. The complete
`4160x3120` auxiliary map matches all `12,979,200` public-profile-generated
float words and independently regenerates the live mean word. For coefficient
delta `d=S-T`, the exact Wiener update is
`w=rcpps(d*d+lambda)*(d*d); output=w*T+(1-w)*S`; confidence is the grouped
mean of `1-w`. All 256 live forward, Wiener, and inverse words match exactly.
Direct installed checkpoints further prove fused-coarse then row-before-column
inverse order. The mode-0 consumer stores each float-flow component as the
signed 16-bit low word after truncation toward zero; all `403,782` components
match and `146,146` rejected-vector components wrap rather than saturate. All
`272,484` terminal tile cells exactly equal the installed binary32
`alpha*target + (1-alpha)*overlap` schedule. Numerical replay is Unit-1 exact
`28mm`; prior admitted route proof supplies `28/35mm` mode-0 applicability and
`70/150mm` direct-B4 exclusion, while prior exact-focal two-body evidence
supplies the body discriminator. This corrects the old target-mean,
source-weight, and inverse-column-first prose. It does not yet regenerate the
complete overlap tile from every contributing patch. `CLM-PREFUSION-002`
remains `PROVEN` / `SPEC_READY` at its existing selected-profile scope.

Version `3.0.347` removes that final all-patch caveat. A SHA-pinned clean-room
replay regenerates the complete Unit-1 exact-`28mm` `522x522` mode-0
pre-combine overlap image from all 4,489 patch origins. Of those, 3,517 valid
source rectangles use the exact gather, transform, Wiener, inverse, and
overlap-add path; 972 nonintersecting source rectangles bypass coefficient
processing and reuse the spatial target patch directly. The exact fixed
overlap table is recorded as 16 float32 bit words, including its real ULP
asymmetry, and the installed full/clipped multiply orders are explicit. A
direct live `(512,-8)` remainder capture proves all target/source gather and
transform words and closes the edge-noise policy: the auxiliary mean intersects
the full `4160x3120` auxiliary domain while the harmonic target statistic
independently intersects the `522x522` tile domain. This reproduces live
variance `74.05537414550781` (`0x42941c5a`), all 256 remainder Wiener/inverse
words, and finally all `272,484/272,484` overlap words exactly. Prior route
proof supplies profile-3 `28/35mm` applicability and `70/150mm` direct-B4
exclusion; prior exact-focal two-body evidence supplies the body discriminator.
No second-body complete-tile numerical identity, firmware cause, compatibility
mode, other-build, or downstream color-parity claim is added.

Version `3.0.348` replaces the unretained historical Unit-2 tele `53.1%`
range-band statistic with a fresh, same-generation full-map comparison on
`L16_00010`. Two instrumented Lumen draws each replay every captured
`0x298ff0` low/high word across all five transitions under the admitted
asymmetric `{-1,0,1,2}^2` and nonzero-Skip rule: `2,161,250` exact words per
draw, `4,322,500` total. Each draw's next selected index lies inside its own
generated Lumen half-open band in `100%` of controlled cells. A pinned current
Phoenix render through level 3 likewise emits bands exactly equal to the
admitted pool and suffix formula applied to Phoenix's own prior indices.
However, Phoenix already differs at level 0, where both engines search the
complete 1,464-entry lookup and no range builder has run: Phoenix is only
`25.5259%` / `28.1947%` within four of the two Lumen draws, while the two
instrumented Lumen draws are `63.2653%` within four of each other at that
level. Downstream Lumen-winner coverage in Phoenix bands contracts to
`46.2088/19.2170/16.9246%` for draw one and
`49.8587/28.5503/25.5251%` for draw two. Therefore the current range builder
amplifies an upstream winner mismatch but is not its first causal origin. The
next implementation investigation is level-0 selected Guidance/source planes,
composed geometry, G-42 local cost, then G-43 accumulation/argmin. Numerical
scope is this one Unit-2 `70mm` LRI with explicit debugger-perturbed
nondeterminism; no other-scene distribution or G-42-versus-G-43 localization
is claimed. `CLM-STEREO-001` remains `PROVEN` / `SPEC_READY`.

Version `3.0.349` supersedes the remaining causal ambiguity in the preceding
paragraph. The retained noninstrumented Unit-2 `70mm` pair is exactly
`52.878821499%` equal, `94.360761834%` within four, with MAE
`1.1026919995` indices. Its run-to-run variation is rooted in libcp generic-
executor ordering, with a bit-level shared G-43 payload race proven directly
and separate pre-G42 scheduler sensitivity observed at the calibration parent
gate. Ascending sequential `0x2d30` callback execution suppresses the complete
index-5 variation across the stated two-body wide/tele controls. Stock-Lumen
comparisons retain the admitted repeat envelopes; a deterministic clean-room
implementation additionally requires exact self-repeat equality under its
chosen fixed schedule.

## Established But Not Fully Closed

These claims are real and usable, but they remain `PARTIAL` and must keep their stated limits.

The table immediately below contains only claims that remain partial in the
ledger. Prefusion, tele firing, merge policy, and final score consequence have
moved to the proven table above.

The long addenda after that table preserve the evidence sequence at the scope
known when each paragraph was written. Phrases such as "remains open" inside
those chronological addenda do not reopen a claim later promoted by the
ledger. They must be read with the proven/partial tables above and the current
authoritative set below.

| Claim ID | Current truth | Safe scope | Why it is not fully closed |
|---|---|---|---|
| `CLM-MERGE-001` | `FusionCacheBayer` is not the profile-3 bridge HDR multi-camera merge entry point. | four-focal negative architecture exclusion under the exact admitted parent/IRAMP chain | alternate profiles and GUI paths excluded |
| `CLM-ZOOM-001` | Profile-3 `35mm` bridge behavior is public internal crop plus upsample/final rasterization, not "5B + computational synthesis". | proven narrow subset of `CLM-ZOOM-003` | no GUI/export generalization |
| `CLM-CCM-001` | Calibration Block 6 has CCM entries for 14 cameras; A2 and C6 are missing and filtered rather than given fallback records. | A2 wide-MonoFusion and C6 tele-terminal fates are proven for canonical profile 3 | alternate profiles excluded |
| `CLM-DENOISE-002` | Selected CNR RGB/matrix math is closed, and source lane 3 is `guide^2`; the guide comes from the named AWB-stage tile task. | transform/runtime discriminator Unit-1 `70mm`; prior CNR route/math scopes retained | exact guide source, normalization, and four-focal/two-body breadth remain open |

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: four-zoom runtime proof now identifies `PipelineCache+0x8` as level-dimension metadata, not an image/composite pointer. At `28mm` and `35mm`, its five packed `(int32 width, int32 height)` entries are `(10432,7824)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`. At `70mm` and `150mm`, the entries are `(8896,6672)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`. In all four accepted bridge HDR runs, the visible `src1` and `src2` wrapper dimension fields are populated from entry `1` as `4160x3120`, and each wrapper owner stores `PipelineCache*` at owner `+0x28`. This corrects the older scratch-era temptation to read `*(PipelineCache+0x8)` as an image object; it narrows contamination around `src1` / `src2`, but it does not identify semantic `src1` / `src2` contents or close reducer math.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: repo-local installed-bundle proof now replaces the older scratch citation for visible `src2` body `0x3ebb80`. Static proof shows visible wrapper `0x3ecd80` calls `0x3ebb80`, then calls one-image `sqrt(max())` normalization body `0x3edb80`; `0x3ebb80` is bounded to `PipelineCache+0x1e0` state, `PipelineCache+0x1d8` fallback/source-descriptor plumbing, descriptor validation, a 64-entry scalar table, and generic tiled executor dispatch. This bounds the visible `src2` wrapper body as descriptor/state/executor orchestration, not a proven merge/reducer closure. Semantic `src2` contents behind the generic executor dispatch remain open.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: runtime/static proof now binds the accepted visible-`src2` generic executor dispatch at `0x3ebb80 -> 0x3ec462` across the canonical quartet to callback address point `0x65f7e8`, slot `+0x30 = 0x3ed2e0`. Static inspection classifies `0x3ed2e0` as a one-source descriptor resampling/materialization worker over `cache+0x1e0` projection/radial state, a 4096-entry radial scale table, 1/64 fractional coefficient-table indexing, 4x4 SIMD sampling/clamping, and 16-byte vector output. The accepted `28mm` / `35mm` state samples use offsets `(2020.0, 1505.0)` and the `0.991346...` matrix class; accepted `70mm` / `150mm` state samples use offsets `(2075.0, 1590.0)` and the `0.998077...` matrix class. This is four-zoom executor-target closure, not semantic `src2` identity, and not merge/reducer or final acceptance/rejection closure.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up runtime proof now bounds the accepted visible-`src2` executor gate slot across the canonical quartet as `0x65f7e8/+0x30 = 0x3ed2e0`. All four seeds now have accepted gate, accepted dispatch through generic tiler forwarding site `0x5d94`, worker entry at `0x3ed2e0`, and completed `10432x7824` HDR output. `35mm`, `70mm`, and `150mm` use dynamic hardware completion probes that install the `0x5d94` dispatch breakpoint only after the accepted gate, install a dynamic hardware worker breakpoint, continue past the worker stop, and complete output. This still does not prove semantic `src2` contents, multi-source reducer closure, or final merge acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up runtime/static proof now bounds the visible `src2` callback `+0x08` source-descriptor producer across the canonical quartet. Static construction proof ties stack descriptor `rbp-0x2200` to callback `+0x08`; accepted runtime probes show the descriptor is zeroed before the producer call and populated after a virtual call through `PipelineCache+0x1d8`, vtable slot `+0x18`, whose accepted runtime target is `0x406a10` at `28mm`, `35mm`, `70mm`, and `150mm`. This narrows descriptor custody for worker `0x3ed2e0`, but it does not identify public semantic contents, LRI origin, merge/reducer closure, or final acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: complete-render runtime proof now bounds the branch/helper reached inside the accepted visible-`src2` `0x406a10` source-descriptor producer. `28mm` and `35mm` accepted samples have object byte `+0x18 = 1` and reach `0x40721b -> 0x31b110`; `70mm` and `150mm` accepted samples have object byte `+0x18 = 0` and reach `0x407458 -> 0x31acf0`. Prior helper classifications bind `0x31b110` and `0x31acf0` as source adapter / validation-wrapper surfaces, not merge/reducer closure. Public byte semantics, descriptor semantics, LRI origin, and final acceptance/rejection remain open.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up installed-bundle and four-zoom runtime proof now closes the constructor-origin custody of the same `FusionCacheBayer+0x18` selector byte used by the visible-`src2` `0x406a10` branch. The `PipelineCache` constructor path `0x3eab4c -> 0x406960 -> 0x4064c0 -> 0x402d20` initializes the object, `0x402d20` computes byte `+0x18` from an upstream scanned collection with sentinel `0x10`, and the object is stored through the already bounded `PipelineCache+0x1d8` holder. Runtime proof across the canonical quartet shows `28mm` / `35mm` select non-sentinel key `1`, write/read `FusionCacheBayer+0x18 = 1`, and construct optional field `+0x20`; `70mm` / `150mm` leave sentinel `16`, write/read `FusionCacheBayer+0x18 = 0`, and have zero `+0x20` construction-store hits under the tested complete bridge HDR runs. This closes flag-origin custody, not public flag semantics, upstream collection LRI origin, optional `+0x20` semantic name, merge/reducer closure, or final acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up scan-loop runtime proof now bounds the upstream records that feed the `0x402d20` selector predicate. `28mm` / `35mm` scan `10` records with target-normalized keys `0,4,1,2,3`; only key `1` has sign-bit fields `+0x58/+0x5c = (-1,-1)`, so final `r15d = 1` and `FusionCacheBayer+0x18 = 1`. `70mm` / `150mm` scan `11` records with target-normalized keys `6,8,9,5,7`; none has a sign-bit `+0x58/+0x5c` pair, so sentinel `16` remains and `FusionCacheBayer+0x18 = 0`. Tele key `15` has `+0x58/+0x5c = (-1,-1)` and post-mutation `object+0x30 = 0`, but it does not match this predicate's target-normalized bucket, so `0x402d20` does not call `0xf2750` on it in the observed branch. Static follow-up proves `0xf6c60` maps camera IDs `0..4`, `5..9`, and `10..15` to group ordinals `0`, `1`, and `2`; `0x137d70` range-checks camera IDs `0..15`; and constructor path `0xf2770` stores item `+0x60` from input `+0x30` through that range check. It also proves `+0x58/+0x5c` are constructor-assigned two-int fields inside `0xf2770`, with switch defaults, optional input override, and later adjustment logic. Lane B follow-up now names constructor input `+0x30` / item `+0x60` as public `CameraModule.id` and input `+0x28` / item `+0x58/+0x5c` as public `CameraModule.sensor_bayer_red_override.{x,y}`. The `150mm` scan facts are pre-crash instrumentation evidence, not output-completion evidence. Selector purpose, optional `+0x20` meaning, merge/reducer closure, and final acceptance/rejection remain open.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` / `CLM-C6-001` addendum: follow-up constructor-origin proof now runtime-bounds the direct `0xe59a4 -> 0xf2770` callsite across complete four-zoom bridge HDR runs. Wide seeds construct keys `0,4,6,8,9,1,2,3,5,7`; tele seeds construct keys `6,8,9,14,5,7,11,10,12,13,15`; all captured items are initially active at item `+0x30 = 1`; input `+0x30` equals output item `+0x60`; and input `+0x28/+0x18` carries the same two-int pair later observed at item `+0x58/+0x5c`. Hardware write-watchpoint proof on tele key `15` / C6 then captures the active byte changing from `1` to `0` at writer `libcp+0x3c90a5` inside body `0x3c8f90` (watchpoint stop PC `0x3c90a9`) for both `70mm` and `150mm`. Static inspection of that body shows the local gate clears item `+0x30` for key `15` when the grouped context `+0x44` value is not group ordinal `2`. This explains the later direct/stereo candidate-gate `object+0x30 = 0` observations as post-constructor mutated state, but it does not prove C6 is globally unused, terminally filtered, or absent from alternate routes before/outside those tested gates.

Additional `CLM-C6-001` addendum: a focused direct `0xf2720` callsite census over 24 selected C6-adjacent sites completed under the canonical `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled. Both tele seeds produced identical key-15 observations: `0x1bdbab` and `0x1bdbdd` each saw key `15` once with active byte `1` and seven times with active byte `0`; mutation-body sites `0x3c9043` and `0x3c9098` saw key `15` active once; later selected sites `0x3b2143`, `0x402df7`, and `0x40d219` saw key `15` only with active byte `0`; and selected stereo-side getter sites `0x3f30ca` / `0x3f3104` saw no key `15`. Static context for `0x1bdbab` / `0x1bdbdd` is a key-vector membership / append helper, so this proof by itself establishes focused key-query participation while active, not image-buffer contribution, terminal filtering, full direct `0xf2720` callsite coverage, non-`0xf2720` route exclusion, or final C6 acceptance/rejection.

Additional `CLM-C6-001` addendum: a follow-up mutation-identity probe under complete `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled ties the active helper observations to the exact mutation boundary. In each tele run, one tracked key-15 item pointer is observed active at `0x1bdbab` / `0x1bdbdd`, active at mutation-loop sites `0x3c9043` / `0x3c9098`, active immediately before the store at `0x3c90a5`, inactive immediately after the store at `0x3c90a9`, and inactive in the later `0x3b2143` context walk. The same runs show context `+0xa0` is zero before the `0x3c9370` constructor call, populated by the object constructed through `0x1bd270`, and then used by the downstream `0x3c8f90` mutation routine. Static inspection classifies `0x1bdb60` as key-list membership / append bookkeeping and shows it does not inspect pixels, image descriptors, or `item+0x30`; this proves helper-body semantics. A later focused candidate-consumer probe re-hits the constructor/mutation custody path but records zero hits at `0x3c9540`, its internal sites, and `0xe6c30` in both complete tele renders; this excludes only that candidate downstream context route, not all downstream context consumers or final C6 contribution/exclusion.

Additional `CLM-C6-001` addendum: a follow-up post-mutation state-consumer probe under complete `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled proves the immediate caller path after `0x3c8f90` consumes the constructed `ctx+0xa0` object. Both tele seeds hit `0x3b20fe`, `0x3b2103`, `0x3b2111`, `0x3b21d9`, `0x3b21ec`, `0x3b2207`, and `0x3b2213` once; both hit `0x3b2143` eleven times with one key-15 observation. The key-15 / C6 item observed at `0x3b2143` has item `+0x30 = 0`, pair `+0x58/+0x5c = (-1,-1)`, and item `+0x100 = 3` in both tele seeds. The same path writes a derived state object with fields `+0x0 = 3` and `+0x4 = 1`, stores it to context `+0xc8`, and queues context `+0x4b0 = 5`. This proves a live post-mutation state-classification consumer of the constructed context object; it does not prove final image contribution/exclusion, terminality, or alternate-route absence.

Additional `CLM-C6-001` addendum: a follow-up downstream rect-vector probe under complete `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled proves the immediate caller segment after the `context+0xc8` / `context+0x4b0` state writes is live. Both tele seeds reread `context+0xc8` as state fields `+0x0 = 3` and `+0x4 = 1`, receive `0` from `0x40b0e0`, take fallback branch `0x3c8c00`, compute raw/scaled dimension pairs `(4160,3120)` / `(8914,6685)`, reread `context+0x4b0 = 5`, pass that value as `r8d` into `0x3c8d00`, and return a five-entry vector of 16-byte integer tuples. The final tuples are `(16,16,8848,6640)`, `(8,8,4424,3320)`, `(4,4,2212,1660)`, `(2,2,1106,830)`, `(1,1,553,415)` at `70mm`, and `(2368,1776,6528,4896)`, `(1184,888,3264,2448)`, `(592,444,1632,1224)`, `(296,222,816,612)`, `(148,111,408,306)` at `150mm`. This proves an immediate downstream vector-builder path for the proven post-mutation state; by itself it does not prove final image contribution/exclusion, terminality, or alternate-route absence.

Additional `CLM-C6-001` addendum: a four-zoom rect-vector consumer probe proves the five-entry rect-vector route is consumed by the immediate caller across the canonical bridge HDR quartet. The caller derives five `context+0x4c0` delta-dimension pairs from the returned rect tuples and passes those pairs to `0x3982b0`, which builds a five-level `CIAPI::ImagePyramid`; observed ImagePyramid level dimensions match those pairs exactly. The `70mm` pairs are `(8832,6624)`, `(4416,3312)`, `(2208,1656)`, `(1104,828)`, `(552,414)`, and the `150mm` pairs are `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)`, `(260,195)`. The same route is live at `28mm` and `35mm`, with pairs `(10432,7824)`, `(5216,3912)`, `(2608,1956)`, `(1304,978)`, `(652,489)` and `(8320,6240)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` respectively. All four runs store a nonzero ImagePyramid shared pointer at `context+0x538`, report `ImagePyramid::levelCount() = 5`, and install nonzero downstream context object pointers at `+0x678`, `+0x688`, `+0x698`, `+0x6a8`, `+0x6b8`, and `+0x6c8`. This proves vector-consumer identity as ImagePyramid construction, not final C6 image contribution/exclusion, terminality, alternate-route absence, or final merge acceptance/rejection.

Additional `CLM-C6-001` addendum: a follow-up four-zoom ImagePyramid zero-fill probe proves the caller immediately iterates the five `context+0x538` ImagePyramid levels, reads each level image's `width`, `height`, byte `stride`, and `data`, builds a full-image stack descriptor for each level, and invokes direct zero-fill callsite `0x3b2f54 -> 0xf7c0` once per level with bytes-per-pixel argument `4`. All twenty runtime descriptors have `stride_pixels == width`, satisfying the static contiguous zero-fill condition inside `0xf7c0`; the first 32 bytes sampled after return are zero for all twenty descriptors. Three descriptors had nonzero first-32-byte samples immediately before the call and zero samples immediately after return: `35mm` level `2`, `70mm` level `2`, and `150mm` level `1`. This proves an immediate zero-fill consumer of the ImagePyramid route, not final C6 image contribution/exclusion, later writer absence, terminality, alternate-route absence, or final merge acceptance/rejection.

Additional `CLM-C6-001` addendum: a four-zoom downstream-candidate liveness probe re-hits the same zero-fill checkpoints and records zero hits at the selected later static `context+0x538` candidate families under complete canonical bridge HDR renders. The excluded candidate families are histogram-like last-level consumer sites, last-level materializer sites, region/deeper-level consumer sites, direct first-image descriptor sites, and a virtual-consumer path. This is a scoped negative result for those selected VAs only; it does not prove terminality, absence of data-pointer aliases, absence of unprobed generic/indirect consumers, or final C6 contribution/exclusion.

Additional `CLM-C6-001` addendum: a representative four-zoom hardware data-watch probe arms a read/write watchpoint after `0x3b2f59` on the first 8 bytes of one selected zero-filled ImagePyramid level per run: `28mm` level `0`, `35mm` level `2`, `70mm` level `2`, and `150mm` level `1`. All four renders complete with exit status `0`, each watchpoint has zero hits, and each armed descriptor sample is all zero at arming time. This proves no later read/write of those watched byte ranges under those runs; it does not prove whole-buffer terminality, other levels, other byte ranges, or final C6 contribution/exclusion.

Additional `CLM-C6-001` addendum: an expanded tele hardware data-watch grid covers all five zero-filled ImagePyramid levels at `70mm` and `150mm`, with first/middle/last 8-byte ranges per level after `0x3b2f59`. All 30 admitted grid cells complete with exit status `0`; each cell arms one watchpoint; every watched 8-byte range is zero at arming time; and every cell records zero later hardware read/write watchpoint hits before clean render completion. This proves no later read/write of those watched tele byte ranges under those runs; it does not prove whole-buffer terminality, unprobed byte ranges, data-pointer alias absence, or final C6 contribution/exclusion.

Additional `CLM-C6-001` addendum: a remaining-direct `0xf2720` callsite census covers the 34 direct static sites outside the earlier focused 24-site proof under complete canonical `70mm` and `150mm` bridge HDR runs with `.lris` auto-loading disabled. The new key-15-positive sites are identical across both tele seeds: `0xe327e` sees key `15` ten times with active byte `1`; `0xe32f3`, `0xe4063`, `0xe5fd9`, and `0xe6020` each see key `15` once with active byte `1`; and `0xe6be0` sees key `15` seven times with active byte `0`. Static neighborhoods bound the active sites to constructor-adjacent key/container/tree materialization surfaces and the inactive `0xe6be0` site to the `0x1be970 -> 0xe6ba0` shared-object lookup path. The remaining covered sites either hit with no key `15` or had zero hits. No site disabled at cap, no JSON errors occurred, and the focused 24-site plus remaining 34-site sets exactly cover the 58 static direct `call 0xf2720` inventory. This closes admitted runtime census coverage for direct `0xf2720` callsites under the canonical tele bridge HDR path, but it does not prove terminality, non-`0xf2720` route absence, final C6 image contribution/exclusion, or public helper semantics.

Additional `CLM-C6-001` addendum: a post-mutation active-byte read/write watchpoint probe arms one hardware watchpoint on the same tracked key-15 item byte at `item+0x30` after `0x3c90a5` and immediate inactive state at `0x3c90a9`. Complete canonical `70mm` and `150mm` bridge HDR renders both exit with status `0`, write `10432x7824` HDR output, arm one watchpoint, record 18 later watchpoint stops, and have no JSON errors or step-cap truncation. Every stopped sample observes `item+0x30 = 0`, `item+0x60 = 15`, `item+0x58/+0x5c = (-1,-1)`, and `item+0x100 = 3`. The stopped libcp VAs are identical across both tele runs: `0x3f2fbd`, `0x3f30be`, `0x22eeb5`, `0x22f715`, `0x40d23a`, `0x1a8df4`, `0x20b03b`, and `0x3e0406`; the final non-libcp stop is allocator cleanup after the output `Written:` line. This proves that the watched post-mutation active byte remains `0` at every recorded later read/write stop and that later active-byte consumers include sites outside the direct `0xf2720` callsite inventory. It does not prove whole-object terminality, other-field or alias absence, zero-filled ImagePyramid whole-buffer terminality, all non-`0xf2720` route absence, or final C6 contribution/exclusion.

Additional `CLM-C6-001` addendum: a selected-field post-mutation read/write watchpoint probe arms four hardware watchpoints on the same tracked key-15 item after `0x3c90a5` and immediate inactive state at `0x3c90a9`: `item+0x30`, `item+0x58..0x5f`, `item+0x60..0x67`, and `item+0x100..0x107`. Complete canonical `70mm` and `150mm` bridge HDR renders both exit with status `0`, write `10432x7824` HDR output, arm all four watchpoints, and have no JSON errors or step-cap truncation. All pre-output libcp samples observe `item+0x30 = 0`, `item+0x58/+0x5c = (-1,-1)`, `item+0x60 = 15`, and `item+0x100 = 3`. The watched `item+0x60..0x67` range records pre-output stops at `0xf2727` and `0xf3327`; static disassembly identifies `0xf2727` as the return after `movl 0x60(%rdi), %eax` and `0xf3327` as the return after `movl 0x64(%rdi), %eax`, so the second bucket is an adjacent-field read inside the watched range, not a true key read. The watched pair range `item+0x58..0x5f` and type/adjoining range `item+0x100..0x107` record only allocator-cleanup stops after the output `Written:` line. This proves selected-field post-mutation behavior for those watched ranges under the tested tele path; it does not prove whole-object terminality, untested-field/alias absence, final effect of the watched `+0x60..+0x67` reads, or final C6 contribution/exclusion.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: a later first-visible-`src1` gated runtime census extends the earlier first-captured lower producer proof. Under complete bridge HDR runs, the gated branch site `0x3e3279 -> 0x31af30` is observed at all four canonical zooms; `0x3e34e2` and `0x3e3653` have zero hits under that exact gated probe. The lower virtual sites `0x33f3e8` and `0x33f94f` are observed at `28mm`, `35mm`, `70mm`, and `150mm`; `0x33ffd4` is observed at `28mm` and `35mm` and has zero hits at `70mm` and `150mm` under the same complete gated runs. Each nonzero lower virtual site hit the probe cap of `512`, so those counts are lower bounds and the recorded target families are capped-window observations, not exhaustive full-render totals. The earlier `0x65b3c8/+0x30 = 0x341770` target remains proven as the first captured target and one member of the broader capped-window `0x33f3e8` family; it is not the only lower visible-`src1` producer target observed. Installed-bundle static classification bounds the inspected visible bodies in that capped target-family set to thunk / descriptor / region / materialization / cache / executor surfaces. Follow-up runtime/static proof binds the two prior indirect-call gaps under the same first-visible-`src1` gate: `0x342d99` resolves `0x65b948/+0x30 = 0x342b80 -> 0x2eb560`, and `0x3449f0` resolves `0x65c798/+0x30 = 0x345920 -> 0x2f53d0` across `28mm`, `35mm`, `70mm`, and `150mm`. A further gated runtime/static proof bounds the immediate `0x2f53d0` helper chain: `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`, `0x3066d0`, and postbranch `0xab590` are live in capped windows across the canonical quartet, while `0x3048b0` has zero hits under the accepted gated probes; static inspection bounds that chain to validation, descriptor/vector setup, bilateral-kernel-size dispatch, callback-object dispatch through `0x5440`, and one row-executor dispatch through `0x5670`. Follow-up installed-bundle static proof classifies the executor callback bodies under that chain as local descriptor transform / filtering / interpolation / normalization / accumulation surfaces rather than reducer closure. This narrows visible-`src1` source-producer dispatch but still does not identify semantic `src1` / `src2` contents, public helper-field semantics, C6 routing, merge/reducer closure, or final acceptance policy.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up first-visible-`src1` gated runtime proof now bounds the selected `0x2f6420` callback arm under the same live `0x3449f0 -> 0x345920 -> 0x2f53d0` helper path. Complete accepted bridge HDR runs at `28mm`, `35mm`, `70mm`, and `150mm` select the `0x2fb320` arm at `0x2f67e2 -> 0x5440` after the gate; all other tested `0x2f6420 -> 0x5440` arm callsites have zero hits, and the hypothesis-relevant `0x2f78e0` worker entry plus normalize sites `0x2f8584`, `0x2f859f`, and `0x2f85a5` have zero hits under that tested route. This narrows the live `0x2f53d0` helper path and prevents treating `0x2f78e0` as proven live there, but it does not globally refute `0x2f78e0`, identify semantic `src1` contents, or close the exact `src1` / `src2` merge/reduction mechanism.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up first-visible-`src1` gated runtime proof now bounds the selected `0x2fb320` worker mechanics under the same live `0x3449f0 -> 0x345920 -> 0x2f53d0 -> 0x2f6420 -> 0x5440` route. Complete accepted bridge HDR runs at `28mm`, `35mm`, `70mm`, and `150mm` hit capped `0x2fb320` entry and `0x2fbf05` post-store probes with clean exit, and every captured entry sample resolves callback address point `0x65a768` slot `+0x30 = 0x2fb320`. Callback fields `+0x08`, `+0x10`, and `+0x18` decode as readable same-shaped descriptor-like records in every captured entry sample; callback field `+0x20` decodes as a readable `vec4` coefficient pointer with five observed coefficient vectors shared by the captured windows at all four focal lengths. The sampled final store writes destination memory equal to `xmm0`, and `xmm0` is the approximate reciprocal-normalized `xmm4 / xmm3` result produced by the static `rcpps; mulps; movaps` sequence. This bounds the selected worker as local descriptor filtering / normalized weighted `vec4` store work, not proven reducer closure; it does not identify semantic `src1` contents, public field names, C6 routing, final acceptance policy, or the exact `src1` / `src2` merge/reduction mechanism.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: corrected installed-bundle and complete accepted bridge HDR runtime census now proves all thirteen installed `CalibDataProcessor::State ()` `operator()` bodies are live across `28mm`, `35mm`, `70mm`, and `150mm`. The corrected State-family body list is `0x229df0`, `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80`, `0x22bdf0`, `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, and `0x22e1d0`; all four focal runs share the full-render count pattern `(1,1,4,4,4,1,1,1,5,5,5,5,1)`. Captured entry object prefixes point back into the corrected State vtable family, and sampled callers reach the bodies through `0x22f3ff`. Prior wording that treated `0x247390` as `runHigherGroupCams::$_12` is refuted: its vtable typeinfo belongs to an adjacent `SparseLNR::markInliers(..., void(int,int,int))` callback table, not `CalibDataProcessor::State()`. This promotes the corrected family from static-only candidate to live upstream path, but that census is entry-liveness evidence only; it does not assign public State semantics or close the exact `src1` / `src2` merge/reduction mechanism.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: installed-bundle static proof now bounds terminal corrected State body `0x22e1d0` and shared dispatcher `0x22f0f0`. `0x22e1d0` iterates the integer-key vector at `this+0x20`, searches/creates keyed tree nodes under `this+0x28`, calls `0x23c5f0`, `0xe6ba0`, and `0xf33d0`, and returns State value `9`; it does not visibly contain a direct image-width by image-height reducer loop. `0x22f0f0` invokes registered State function objects through slot `+0x30`, stores returned `eax` into the current State slot at `r14+0x6c`, and can notify a callback at `r14+0xe0`. This bounds another State-machine surface away from direct reducer closure, but it does not decode public State semantics, runtime return ordering, or the exact `src1` / `src2` merge/reduction mechanism.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up installed-bundle and four-zoom runtime proof now bounds State helper `0x23c5f0` and selector-gated field-copy helper `0xf33d0`. Static extraction shows `0xf33d0` branches on `r8d`: selector `0` copies two source vector/int records plus a three-int packet into destination offsets `0x180..0x1d0`, selector `1` copies the same shaped inputs into destination offsets `0x12c..0x17c`, and other selector values enter an error path containing string `"wrong CalibStage, must be factory or current"`. Complete accepted no-auto-LRIS bridge HDR runtime proof shows `0x23c5f0` hits four times per render across `28mm`, `35mm`, `70mm`, and `150mm`: twice from return VA `0x22b51e` inside State body `0x22af80` with captured `r8d/r9d = 0/9`, once from `0x22e249` inside `0x22e1d0` with `r8d/r9d = 1/11`, and once from `0x22e288` inside `0x22e1d0` with `r8d/r9d = 1/11`. The static `0x23c5f0 -> 0xf33d0` callsite at `0x23d38d` / return `0x23d392` is live with selector `1` in all four focal tiers, and every captured `0xf33d0` hit uses selector `0` or `1`; total full-render `0xf33d0` hit counts outside the stable `0x1f0ce0` producer edge are run-local liveness evidence rather than admitted algorithm constants. Later evidence maps `0=factory` and `1=current`; public State semantics, complete bank-field meanings, image effect, reducer closure, and final acceptance/rejection remain open.

Additional `CLM-WARP-003` / `CLM-PREFUSION-002` addendum: follow-up Lane B public-meaning audit decodes the public LRI camera/config carriers used as key-space anchors, proves the captured `f2770` constructor-family raw field bridge (`object+0x60 == LightHeader.field_12[camera].field_2`, `object+0x50 == field_4` when present and `0` otherwise, `object+0x54 == field_5`, constructor input `+0x40 == field_8`, and constructor input `+0x48 * 2 == field_10`), names `record+0x40` as the internally depth-labeled `UpsampleLayer+0x90` descriptor return, proves exact public 32,832-byte intrinsics-block fixed32 copies for wide A1-A5 `0xf33d0` K/pose packets, and proves exact public pose copies for B4 plus tele C5. Deterministic embedded-protobuf schema extraction now names those public carriers as `LightHeader.modules`, `CameraModule.id`, `CameraModule.mirror_position`, `CameraModule.lens_position`, `CameraModule.sensor_exposure`, decoded `CameraModule.sensor_temparature`, and `CameraModule.sensor_data_surface.size`; it also names the calibration paths as `FactoryModuleCalibration.geometry`, `GeometricCalibration.per_focus_calibration`, `intrinsics.k_mat`, `focus_hall_code`, and `extrinsics.canonical.rotation/translation`. Representative wide/tele raw-wire checks pass on both physical calibration bodies (`722a6e72...` and `223961c6...`), while the LLDB object-copy observation remains Unit-1-scoped. A follow-up `0x1f0ce0 -> 0xf33d0` producer verifier localizes the B4/C5 K non-match to the constructor-side producer edge: selector `0` and selector `1` receive identical source packets per key, B4/C5 pose packets remain exact-public and stable where observed, and B4/C5 K packets are already zoom-variant non-exact records before downstream State-helper composition. A deeper `0x1f0ce0` K-source trace proves the captured two-record K helper formula: helper entry receives the same camera's two public K records plus public `CalibrationFocusBundle.focus_hall_code` scalars, `0xf3300` supplies runtime `object+0x54 = CameraModule.lens_position`, and helper output copied through `rbp-0x188 -> rbp-0xb8` linearly interpolates/extrapolates K fields `0`, `2`, `4`, and `5` with float32 arithmetic before the identity `0xf3350` scale window. A refreshed `0x23faf0` record-chain verifier adds component-scoped public matches around the pre-call left/right/output records and proves zero exact full 0xa4-byte source-record copies in the checked LRI calibration payload classes. A follow-up `state+0x448` payload probe proves the first visible payload-copy path writes public pose components into payload `+0x00..+0x2c`: `+0x00..+0x20` is `module_calibration[anchor].geometry.per_focus_calibration[2].extrinsics.canonical.rotation` and `+0x24..+0x2c` is the corresponding `.translation`, using anchor `A1` at `28mm` / `35mm` and anchor `B4` at `70mm` / `150mm`, shared across the first-pass inserted keys; tele public-fired `C6` is not inserted by that first visible path, and checked later `+0x30..+0x3c` source slices have zero exact public fixed32-sequence hits. A follow-up later-box formula probe closes formula-level meaning for those later fields: payload `+0x30/+0x34` is uniform float32 scale and payload `+0x38/+0x3c` is float32 box origin from `0x260e40` over the `0x145980(object)` box and `object+0x114/+0x118 = CameraModule.sensor_data_surface.size = [4160,3120]`. A follow-up lookup endpoint/count probe proves the selected `[200.0, 640000.0]` endpoint pair comes from static binary float tables and the lookup count is computed internally from five `0xa8` source records plus `this+0x18`, first-record scalar, endpoint reciprocal span, clamp `0x1000`, and mode `8`. Deterministic depth-bound custody additionally traces that pair into Ceres lower/upper bounds on the one-scalar Triangulator ray-depth reprojection problem; all four canonical Unit-1 focal tiers select mode `0`, admitting the lookup's internal reciprocal ray-depth hypothesis-grid role. Same-process control-block RTTI/pointer proof now identifies the selected `state+0xe0` objects as exact `lt::CapturedImage`; later admitted addenda name the RawImageFactory lookup context and public frame-index key. The audit and producer verifiers still do not find exact public calibration-byte copies for the full CapturedImage stage banks or full `state+0x448` beyond the scoped first-payload pose fields and later box/scale formula slice, and do not close selector-bank names, other B/C packets, tele C6 public-packet origins, public names/origins for remaining Cost-volume operands, public calibration/LRI/protobuf origin and names for the ray-depth bounds, other public semantic names, or final effect for the `StereoLayer<false>` index-5 path.

Additional Lane B producer-verifier detail: the `0x1f0ce0` static byte check now also guards the K stack local, the pose stack local, the three-int stack local, the post-`0xf3350` K-field scale window, the `0xf3300` `object+0x54` accessor, and the installed two-record `0x1f96e0` interpolation windows before both selector-bank copies. This closes the captured focus-dependent K helper formula only; selector-bank names, other packet origins, and the wider Lane B path remain open.

Additional Lane B `state+0x448` public-origin detail: companion static verification and exact raw-word runtime matching on Unit-1 wide and Unit-2 tele renders prove the `object+0x114/+0x118 = [4160,3120]` size pair is `LightHeader.modules[camera].sensor_data_surface.size` and the converted same-camera calibration record consumed by `0x145590 -> 0x145980` comes from `LightHeader.module_calibration[camera].geometry.distortion.polynomial.{distortion_center, normalization, coeffs, fit_cost}`. This closes the public calibration/LRI origin of the box-producing structure only; the computed distortion/undistortion envelope, uniform scale, full `state+0x448` semantics, and wider Lane B path remain derived or open.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up no-auto-LRIS four-zoom runtime proof now bounds `0x23c5f0` post-`0xf33d0` local integer coverage and normal-exit local tree shape. Every run pairs four `0x23c5f0` entries with four normal pre-destroy exits and has no JSON errors, step cap, or tree traversal truncation. The post-`0xf33d0` local `rbp-0x4e0` integer coverage is `{1,2,3,4}` / `{1..9}` at `28mm` and `35mm`, `{5,6,7,9}` / `{5,6,7,9,10..14}` at `70mm`, and `{5,6,9}` / `{5,6,9,10..14}` at `150mm` for the `0x22b51e` versus `0x22e249` / `0x22e288` caller groups. The pre-destroy local tree has `5` nodes for `0x22b51e` and `10` nodes for `0x22e249` / `0x22e288`, with node `i32_0x20` sets `{0,1,2,3,4}` / `{0..9}` at `28mm` / `35mm` and `{0,5,6,7,9}` / `{0,5,6,7,9,10..14}` at `70mm` / `150mm`. This is local helper-field / pre-destroy tree custody proof only, not public field semantics, image effect, reducer closure, or final acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up four-zoom runtime proof now shows the objects populated by the live `0x23c5f0 -> 0xf33d0` selector-`1` copy path are reused by an internal transitive helper path before `0x23c5f0` exits. Each accepted no-auto-LRIS bridge HDR run matches nine prior `0x23d392` destination objects against `204` later `0xf34e0` calls under stack `0xf34e0 <- 0x264270 <- 0x23c5f0`; the matched `0x23c5f0` return VA is `0x23cbab`, after static call `0x23cba6 -> 0x264440`; static `0x264440` sets `edx = 1` and tail-jumps to `0x264270`; and every matched `0xf34e0` call uses selector `1`, selecting `object+0x12c` by the static `0xf34e0` formula. This is internal helper-custody proof only, not post-`0x23c5f0` image effect, source contribution, reducer closure, or final acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-PREFUSION-002` addendum: follow-up four-zoom runtime proof now bounds the next internal `0x23c5f0` record-chain step. In each accepted no-auto-LRIS bridge HDR run, watched sites `0x23cbab`, `0x23cbc1`, `0x23ce5e`, and `0x23d025` each hit `26` times, forming `26` ordered four-site groups with stable local key and source-object pointer. The refreshed probe captures the pre-call `0x23faf0(dst=rbp-0x378, left=rbx+0x20, right=rbp-0x420)` tuple at `after_264440`; the right record is byte-stable across the call, while the `rbp-0x378` record changes across `0x23cbbc -> 0x23faf0`, remains stable afterward, and its mapped `f32_0x00x8` fields are materialized into local tree-node `f64_0x28..0x58` fields in all `104` admitted groups. Node `i32_0x20` equals the sampled `rbp-0x2d0` local key in all groups; node `+0xa0` is first forced to `0` at `0x23ce5e`, then receives the observed final distributions `{0:10, 9:8, 11:8}` at `28mm` / `35mm` and `{0:8, 9:8, 11:10}` at `70mm` / `150mm`. This is internal helper-record-to-local-tree and component-scoped public-origin custody proof only, not public field semantics for the full records, post-`0x23c5f0` image effect, source contribution, reducer closure, or final acceptance/rejection.

Additional `CLM-PREFUSION-001` / `CLM-C6-001` addendum: complete bridge HDR runtime probes with same-name `.lris` auto-loading disabled now bound the keyed helper / vector-builder boundary beneath the visible `src1` source-image topology. Across `28mm`, `35mm`, `70mm`, and `150mm`, `0x1bdc80` and its post-`0xe78e0` count site `0x1bdcfb` are live; every summarized invocation saw count `1`. The stack-mode helper `0x1be750`, both lazy callsites into `0x1be270`, and direct no-gate breakpoints at `0x1be270`, `0x1be291`, `0x1be2fb`, and `0x1be306` have zero hits under these complete runs. Observed helper keys are `0..9` at `28mm`/`35mm` and `5..14` at `70mm`/`150mm`; key `15` / C6 is not observed on this tested helper boundary. This excludes the tested `0x1bdc80` / `0x1be750` / `0x1be270` boundary as a positive C6-routing observation, but it does not identify C6's actual destination or close semantic `src1` / `src2` contents.

Additional `CLM-PREFUSION-001` / `CLM-C6-001` addendum: complete bridge HDR runtime probes with same-name `.lris` auto-loading disabled now also bound the `0x3e42e0` projection field-pack dispatcher boundary. Across `28mm`, `35mm`, `70mm`, and `150mm`, `0x3f6170`, branch decision site `0x3f61b8`, same-category path `0x3f61ca -> 0x3f6200`, and cross-category path `0x3f61e1 -> 0x3f6940` are live. Observed keys are `0,5..9` at `28mm`/`35mm` and `8,10..14` at `70mm`/`150mm`; tele key `15` / C6 is not observed at this tested dispatcher boundary. This excludes `0x3f6170` / `0x3f6200` / `0x3f6940` as a positive C6-routing observation under the canonical tele bridge HDR runs, but it does not identify C6's actual destination or close semantic `src1` / `src2` contents.

Additional `CLM-PREFUSION-001` / `CLM-C6-001` addendum: complete bridge HDR runtime probes with same-name `.lris` auto-loading disabled now bound the direct payload candidate loop immediately upstream of the `0x3e05f5 -> 0x3f6170` dispatcher call. Across `28mm` and `35mm`, the loop visits keys `0..9`; every visited key has `object+0x30 = 1`, keys `0..4` are same-class skipped, and keys `5..9` reach the dispatcher call. Across `70mm` and `150mm`, the loop visits keys `5..15`; keys `5..9` are same-class skipped, keys `10..14` reach the dispatcher call, and key `15` / C6 has post-mutation `object+0x30 = 0`, so it skips before active-pass, class-compare, cross-category, and dispatcher-call sites. This proves a tested C6 filter point under canonical tele bridge HDR, but it does not prove C6 is globally unused or exclude alternate paths outside this direct candidate loop.

Additional `CLM-C6-001` addendum: complete bridge HDR runtime probes with same-name `.lris` auto-loading disabled now also bound the stereo-side keyed-record loop inside the `0x3f2c40` constructor branch. Across `28mm` and `35mm`, the loop visits keys `0..9`; every visited key has `object+0x30 = 1` and reaches both tested `0xf2720` getter callsites at `0x3f30ca` and `0x3f3104`. Across `70mm` and `150mm`, the loop visits keys `5..15`; key `15` / C6 has post-mutation `object+0x30 = 0`, so it skips before the post-gate path and before both getter callsites. This proves a second tested C6 filter point under canonical tele bridge HDR, but it does not prove C6 is globally unused or exclude alternate paths outside the tested direct and stereo-side loops.

Additional `CLM-MERGE-005` / `CLM-MERGE-006` addendum: the destination backing store for the owner `+0xf0` expansion handoff is now bounded. `0x3d4e10` receives a caller-provided context whose `+0x10` field points to the persistent 16-byte destination descriptor, and runtime packets across the canonical four-zoom quartet show local destination descriptor `rbp-0x90` is a clipped view into that context descriptor with matching `qword_28`, in-range data pointer, and 16-byte alignment. The first captured route after that context is bounded too: the active callable branch at `0x3d4842` uses slot `0x3ec960`, `context+0x10` equals the parent `0x3d01b0` caller-provided output descriptor, the caller returns to `0x3d084d` in the selected-cache read/rescale path, and the same temporary descriptor is passed to `0x36f800` at `0x3d08ce` across `28mm`, `35mm`, `70mm`, and `150mm`. A follow-up first-owner census proves sibling direct branch `0x3d4864` is also live for the first captured owner `+0xf0` descriptor at `28mm`, `70mm`, and `150mm`; `35mm` accepted only `0x3d4842` in that census. Every accepted census packet still uses slot `0x3ec960`, returns to caller `0x3d084d`, and preserves the parent/context destination equality checks. A direct-branch post-route proof then shows the first owner-matching direct branch at `28mm`, `70mm`, and `150mm` reaches `0x3d08ce -> 0x36f800` with `rsi` equal to the same temporary descriptor captured as `context+0x10`; `35mm` has no owner-matching direct branch under that first-owner probe. A global branch-site census removes the first-owner gate and proves that complete canonical bridge HDR renders at `28mm`, `35mm`, `70mm`, and `150mm` hit only caller set `{0x3d0732, 0x3d084d, 0x3ecc5a}` and active callable slot set `{0x3ec960, 0x3e4a80}` at `0x3d4842` / `0x3d4864`, with all hits preserving the same parent/context destination equality checks. A post-route family probe then classifies those caller families: `0x3d0732` is exact-size cleanup with no post call, `0x3d084d` reaches `0x3d08ce -> 0x36f800`, and `0x3ecc5a` reaches `0x3ecc74 -> 0x3edb80` visible-`src1` one-image normalization across the canonical quartet. A parent-chain ancestry census then shows `0x3d0732` returns through `0x3b07a9 -> 0x41a8d3 -> 0x3adfce -> 0x280e`, `0x3d084d` returns through `0x3bb822 -> 0x3adfce -> 0x280e`, and visible-`src1` `0x3ecc5a` returns through `0x374cf3 -> 0x3665da -> 0x365f50 -> 0x3ec7df -> 0x3eca4b -> 0x3d4842` with some nested read-context continuations. Static parent-chain body classification now separates callback/iteration glue (`0x280e`, `0x3adfce`) from selected owner-cache/direct-render tile surfaces (`0x3b0740`, `0x41a7d0`, `0x3b9770`, `0xfbda0`, `0x3bb2b0`) and visible-`src1` / IRAMP nested wrapper plus owner `+0xf0` sink surfaces (`0x374ac0`, `0x3661b0`, `0x365960`, `0x3ec770`, `0x3ec960`). Static helper-surface classification then bounds exposed route plumbing around `0x31b110`, `0xfe720`, `0x106cb0`, `0x2e20`, `0xf3570`, `0x3b9660`, `0x3c6ac0`, `0x1bea20`, `0x1bea00`, and `0x1be970` as adapter, rectangle-grid, vignetting-data, callback-dispatch, owner/tile/map/field-copy helpers. Static selected-cache/post-route classification further bounds `0x3d01b0`, `0x3d0650`, `0x3d47d0`, `0x3d4e10`, `0x3d50f0`, `0x3d5290`, `0x2ff00`, `0xc0410`, and `0x3edb80` as level/ROI tile-read, exact-size/read-then-rescale, branch-router, clipped source/destination view, 6-byte-to-vec4 expansion, 16-bit-to-float conversion, and one-image `sqrt(max())` normalization plumbing. A static downstream direct-caller census then bounds direct callers of `0x36f800`, `0x3d01b0`, `0x3edb80`, and `0x3d50f0` in the repo-local static callgraph: `0x36f800` direct callers are selected-cache read/rescale, TileCache-like read/rescale, and IRAMP-internal descriptor resample handoff; `0x3d01b0` direct callers are selected-cache reads, visible-`src1` read, source-adapter caller, and DOFCache render caller; `0x3edb80` direct callers are visible-`src1` and visible-`src2` one-image normalization wrappers; `0x3d50f0` has only the already classified `0x3d4e10` direct caller. A static selected-cache caller census then bounds direct callers of `0x3d0650`: the 14 direct callers fall into source-adapter-style caller windows, small owner-cache selector `0x3b0740`, multi-branch owner/tile-cache surface `0x3bb2b0`, owner `+0xf0` output-sink branch body `0x3ec960`, and later helper/adaptor caller surfaces around `0x42fb40` and `0x42fd30`. A static `0x3e5720` caller census then bounds direct callers of that row-conversion executor setup: active-callable-slot / owner `+0xf0` writer body `0x3e4a80`, owner `+0xf0` output-sink body `0x3ec960`, and DOFCache render body `0x3f0b90`; ancillary `0x432db0` coverage bounds the later selected-cache caller surface `0x42fb40 -> 0x3d0650 -> 0x432db0`. A static `0x3d4e10` caller census then bounds direct callers of the owner `+0xf0` expansion handoff: the two already bounded branch-router post-branch handoffs at `0x3d484a` and `0x3d486c`, plus separate indexed-entry loop caller `0x3d5468`; `0x3d50f0` has only direct caller `0x3d5029` inside `0x3d4e10`, and `0x3d5290` has no direct callers because it is worker-dispatch plumbing. A static/runtime `0x3d5400` executor-route proof then binds that separate loop caller to vtable `0x66a728`: `0x3d01b0` builds the `0x66a728` callback object and dispatches `0x5670`, vtable slot `+0x30` reaches thunk `0x3d53c0`, the thunk jumps to `0x3d5400`, and first-hit runtime probes reach `0x3d5468 -> 0x3d4e10` across the canonical quartet. These static/runtime classifications do not close indirect/vtable callers outside the bounded routes, final file/display sink, final contributor acceptance/rejection, or `src1` / `src2` semantic contents. Exact hot direct-branch and first-hit probe totals are evidence-run counts, not algorithm constants. The first gated `0x36f800` worker path after the selected-cache route is now bounded through callback slot `0x3721d0`, static worker body `0x372210`, runtime worker-entry probe `0x372224`, first weighted `vec4` store at `0x372488`, row-plan/cache setup at `0x372500`, captured 4-tap horizontal row-cache stores inside `0x372760`, and fresh first-dispatch row-plan coverage across all four canonical zooms. A full-render row-cache segment census then proves leading/trailing `0x372760` segments are live at `28mm` and `70mm`, while `35mm` and `150mm` have zero leading/trailing hits under the tested canonical bridge HDR runs. Public offset/scale/pixel-format semantics, downstream row-image/final policy after the classified caller/helper/post-route/direct-caller/selected-cache-caller/`0x3e5720`-caller/`0x3d4e10`-caller/`0x3d5400`-executor-route families, and final acceptance/rejection remain open.

Latest prefusion custody addition: the `0x24c320` / `0x24d610` candidate-scorer output vectors are now bound to shared record-state gate `0x2439b0` by exact output-vector pointer continuity across the canonical four-zoom bridge HDR quartet. This is admitted only as scorer-output custody; it does not close semantic `src1` / `src2` contents, reducer closure, or final acceptance/rejection.

Latest prefusion record-state addition: `0x2439b0` is now bounded as a live record-state gate over those custody-bound scorer-output vectors. The admitted `28mm` / `35mm` family-A runs are unchanged at the before/after boundary; the admitted `70mm` / `150mm` family-B runs promote target-2 records from state `3` to state `4`; and sampled downstream `0x241fd0` / `0x2416d0` / watched-store sites did not match the exact scorer-output vector under this probe. This is admitted only as boundary behavior; public record-state semantics, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion promoted-record addition: selected target-2 records promoted by `0x2439b0` from state `3` to state `4` are now proven to be later consumed by downstream code under clean canonical `70mm` and `150mm` renders. At least one watched promoted record per tele seed advances to state `5` through `0x2416d0`. This is admitted only as watched-record downstream-consumer proof; public state `5` semantics, downstream image contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 selected-index addition: promoted target-2 record indices captured at `0x2439b0` are now proven to enter concrete `0x2416d0` selected-index vectors under clean canonical `70mm` and `150mm` renders. The small promoted sets captured by this probe are observed reaching `(state=5,target=2)` stores. This is admitted only as selected-index/state-relabel proof; public state `5` semantics, downstream image contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 later-watch addition: watched promoted tele records that become `(state=5,target=2)` are now proven to continue downstream into `0x244560` and the already-bounded `0x25d090` candidate block-geometry / active-block helper family under clean canonical `70mm` and `150mm` renders. This is admitted only as later state/candidate/geometry flow; downstream image contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion block-geometry-effect addition: `0x25d090` is now runtime-bounded across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders as block-owned pair-vector growth plus descriptor-build / geometry-predicate / active-byte gating. Active entries reach `0x25d2a0`, accepted entries grow both block pair-vector families and return true, and the only active-byte clears are two `70mm` geometry rejects. This is admitted only as block-state effect proof; downstream image contribution, public state semantics, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion block-decision cascade addition: the `0x244560` / `0x245a40` caller-side decisions after paired `0x25d090` calls are now bounded across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. Every admitted decision join keeps exactly one block active, records abort flag `0`, avoids the watched sentinel-fill path, and reaches `0x2457c0` callsites. This is admitted only as downstream block-decision / coordinate-output custody proof; downstream image contribution, public state semantics, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 coordinate-output addition: `0x2457c0` is now proven live and normally returning across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. Sampled hits at the admitted `0x24593b` store-path site have `record+0x24 == 5`, and every admitted return leaves finite non-sentinel coordinate pairs in `state+0x1e8`. This is admitted only as coordinate-output materialization; downstream image contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 coordinate-consumer addition: representative finite non-sentinel coordinate pairs emitted by `0x2457c0` into `state+0x1e8` are now proven to be read by `0xe8e70` vector-copy work under both State-helper copy-out paths (`0x224d70 -> 0x245a40` and `0x224e50 -> 0x245a20 -> 0x244560`) across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. This is admitted only as coordinate-vector custody / copy-out proof; image-effecting non-copy use of the copied destination, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 coordinate-copy-destination addition: representative finite non-sentinel destination pairs copied out by the State-helper `0xe8e70` path are now proven to be touched again by `0xe8e70` vector-copy work across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. The admitted later caller frames include the State-helper recopy sites and two higher node-vector materialization/copy sites at `0x22a61a -> 0xe8e70 -> 0x22a61f` and `0x22c93a -> 0xe8e70 -> 0x22c93f`. This is admitted only as coordinate-vector custody / propagation proof; image-effecting non-copy use of the propagated destination vectors, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion state-5 coordinate-node-destination addition: representative finite non-sentinel destination pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination are now proven to reach non-copy candidate/index/scoring-selection code under `0x21b2e0` and its `0x21c4f0` callback path across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. The admitted capped window followed at least one finite node-destination pair per run; the sibling node-vector copy site `0x22c93a -> 0x22c93f` had zero observed call/return hits in this proof. This is admitted only as non-copy candidate/index/scoring-selection consumption of a representative node-vector coordinate pair; image effect, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination sentinel-custody addition: one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal tier is now proven to be the same runtime address later rewritten through `0x21b923` / `0x21b92a` into full `(-1.0, -1.0)` at `0x21b930`, then sampled in downstream touches while still sentinel. This links the node-destination consumer, sentinel-write, and sampled downstream-touch boundaries for representative pairs only; all-pairs coverage, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination `0x20b5e0` branch-custody addition: one representative copied node-destination pair per canonical focal tier is now proven to reach `0x20b912` at the same runtime address after sentinelization, still read as full `(-1.0, -1.0)`, step through `0x20b91d -> 0x20ba90` and `0x20baab -> 0x20bafd`, and avoid the local update-write block at `0x20bac0..0x20bac8`. This links copied node-destination identity to one sampled local branch skip only; all-pairs coverage, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination `0x20ca00` source-copy addition: one representative copied node-destination pair per canonical focal tier is now proven to be source-read at the same runtime address by `0xe0ae0` under caller return `0x20d309`, the second local vector copy inside `0x20ca00`, while still full `(-1.0, -1.0)`. This links copied node-destination identity to the `0x20ca00` source-copy surface only; destination-slot identity, local gate selection, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination `0x20ca00` source/gate index addition: for one representative copied node-destination pair per canonical focal tier, every captured `0x20d309` source/gate packet before the watchpoint cap now has readable `source_index` and parent `gate_index` with `source_index != gate_index` (`117`, `117`, `106`, and `106` captured packets respectively). This is capped local non-selection proof for one watched address per tier only; destination-slot terminality, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination selected `0x20ca00` gate-custody addition: prior copied node-destination identity is now carried through sentinelization, the `0x20d309` source copy, computed destination-slot identity, and the `0x20d363 -> 0x20d565` skip branch for one selected `28mm` representative (`source_index == gate_index == 5394`) and one selected `70mm` representative (`source_index == gate_index == 77`). Both copied destinations still read full `(-1.0, -1.0)` at the gate. The selected `35mm` row is a `16384`-stop capped no-match window, and the selected `150mm` index-`240` address has no `0x20d309` source-copy observation during its completed uncapped watch run. This is representative local gate-skip custody only; all-pairs coverage, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination selected cross-unit addition: risk-based Unit-2 validation now observes the same full-sentinel `0x20d363 -> 0x20d565` gate-skip mechanism in one complete `35mm` twin-capture run with `source_index == gate_index == 12`. Unit-2 `28mm` and `70mm` anchor runs have no match before their watch caps, and a targeted Unit-2 `35mm` repeat over the same copied indices `11..14` also has no match before its cap. This admits the local mechanism on both physical units while proving that exact pair index / match incidence is not a stable body or focal-tier constant under these probes. The twin captures differ in scene, calibration, and instrumentation schedule, so body causation, all-pairs terminality, image/source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion `0x20ca00` local-effect addition: deterministic installed-bundle byte/import verification now proves the selected `0x20d363 -> 0x20d565` branch bypasses interval `0x20d369..0x20d560`, including keyed local-node materialization, two coordinate-to-double record-write groups, and imported `ceres::Problem::AddResidualBlock(CostFunction*, LossFunction*, double*)` at `0x20d560`. Joined to the admitted Unit-1 `28mm` / `70mm` and Unit-2 `35mm` branch packets, those selected full-sentinel pair iterations add no residual through this local call and perform none of those skipped writes. The function still constructs a solver summary and calls `ceres::Solve` after the per-pair loop, so shared-solve terminality for those skipped pairs, broader solved-value distributions, downstream image/source contribution, reducer closure, and final acceptance/rejection remain open.

Latest prefusion `0x20ca00` callback-identity addition: installed-bundle vtable/typeinfo bytes and Capstone re-extraction now identify `0x20ca00` exactly as substantive slot `+0x30` of a `void(int,int,int)` lambda inside `lt::Triangulator::refine3dPoints()`. Parent code installs address point `0x657f00`, captures eight pointers at callable `+0x08..+0x40`, and dispatches it through generic executor `0x5670`, whose indirect call uses slot `+0x30`. Historical labels treating `0x20ca00` as the `refine3dPoints()` method entry are coarse; new evidence must call it the Triangulator `refine3dPoints()` lambda callback. This identity proof by itself does not close public names for the three integer arguments, public output meaning, runtime values, downstream image/source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion `0x20ca00` solved-record custody addition: deterministic installed-bundle SHA/Capstone verification now traces the parent owner through callable `+0x08` into callback local `rbp-0x2a8`, binds the callback's post-solve triple to selected fields `+0x08/+0x0c/+0x10` of that owner's `0x14`-stride record vector, and proves the parent immediately reduces positive `record+0x10` values into owner `+0x78/+0x7c`. This closes internal triple ownership and that immediate scalar-range consumer only; by itself it does not prove public triple meaning, runtime solved values, later range consumers, downstream image/source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion `0x20ca00` reprojection-cost addition: deterministic typeinfo/import/SHA/Capstone verification identifies address point `0x667240` as `ceres::AutoDiffCostFunction<lt::Internal::ReProjectionCost,2,1,...>`, correcting the older raw-`ReProjectionCost` vtable label. The callback passes that wrapper, a callable-`+0x28` captured `CauchyLoss` object with double payload `(1.0,1.0)`, and one scalar double to `AddResidualBlock`; the residual-only evaluator scales ray `(bx,by,1)`, applies a 3x4 transform, perspective-divides, and subtracts stored coordinates to produce two residuals. This proves an internal one-scalar ray-depth reprojection objective and names the local residual excluded by admitted sentinel skips; by itself it does not prove public units/LRI origin, runtime solved values, all-pairs terminality, downstream image/source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion `0x20ca00` solve-output addition: one complete Unit-1 `28mm` solve-only render now supplies scoped runtime values and selected-record materialization. Ten callback frames return cleanly with 1,229 unique solve/write groups; `ceres::Solve` changes the bounded ray-depth scalar in 279 groups and leaves it bit-identical in 950, all captured solved values remain within `[200.0,640000.0]`, and every final selected `record+0x10` equals the float32 solved scalar. The immediate second transform leaves the first transformed triple bit-identical in all 1,229 groups under this run. Follow-up discriminator runs show the first post-Solve triple-write materialization is not Unit-1 `28mm`-only: Unit-1 `70mm` captures 3,456 groups with 317 solve-adjusted scalars, and exact-focal Unit-2 `35mm` captures 1,589 groups with 886 solve-adjusted scalars; both have first-write `record+0x10 == f32(solved_scalar)` in every captured group. The Unit-1 `70mm` run refutes generalizing the Unit-1 `28mm` final-z equality because the second transform changes all captured triples and final `record+0x10` exactly matches the solved scalar in `0/3456` groups; Unit-2 `35mm` preserves final-z equality in `1589/1589` groups. A capped Unit-1 `70mm` same-address hardware watch then follows one final `record+0x10` field out to the immediate parent scan, propagation/helper windows, and downstream positive-record gate / transform-score site `0x2189c4` with zero value changes across 64 captured stops. Static + reused-runtime follow-up pins helper `0x218940` and shows that this watched finite positive z reaches `0x2189c4` 37 times and is on the local fallthrough path into the record/transform score body; companion caller proof binds those helper samples to `lt::SparseMirrorAngleOptimizer::optimize(...)::$_2` caller `0x219210`, which immediately stores the helper `xmm0` return into `[r14+0x18][r15]` at `0x219381`. Static + LLDB parent proof then runtime-binds the local consumer for that callback output-vector family: one complete Unit-1 `70mm` packet carries the exact same closure, 1,089-float return-vector header, and begin pointer through 64 sampled post-store callback hits and the matched `0x216f60` parent consumer at `0x217a68`; the parent min-like scan selects index `505` before helper side-output gates and selected 24-byte record materialization for `0xf33d0`. These are not direct branch-step, record-specific score, all-record, public acceptance/rejection, or image/source contribution proofs. This closes scoped runtime solved-value, first-write materialization, representative downstream-custody, representative local score-window admission, representative caller output-vector custody, and one-render same-runtime callback-store to parent-consumer vector custody boundaries only; stable distributions across bodies/focals/renders, public calibration/LRI origins and names, all-candidate behavior, shared-solve terminality, downstream image/source contribution, reducer closure, and final acceptance/rejection remain open.

Latest prefusion `0x216f60` parent-decision addition: SHA-pinned installed code plus complete canonical Unit-1 four-focal runs and one exact-focal Unit-2 `35mm` discriminator now close the local parent gate over the callback score vector, side-output vector, and 24-byte candidate records. The parent selects the minimum score, rejects selected side-output above `0.25`, rejects selected side-output above the center side-output, conditionally rejects selected score above float32 `0.8 * center_score` when `r12d > 0`, and only then materializes the selected record and completes `0x217bbe -> 0xf33d0 -> 0x217bc3` with `r8d = 1`. All 26 captured parent packets agree between arithmetic reconstruction and runtime x86 flags; 12 accepted packets reach `0xf33d0`, while 14 rejected packets do not. These packet counts and selected indices are evidence-run observations, not constants. This closes the captured local score/side-output decision and record custody only; public vector/record names, image/source contribution after `0xf33d0`, distributed reducer closure, and final merge acceptance/rejection remain open.

Latest prefusion accepted-bank custody addition: SHA-pinned selector-1 `0xf33d0` code and hardware read/write watches now carry accepted `0x216f60` winners into destination bank `+0x12c..+0x17f` and later `0x264270` record assembly across the canonical Unit-1 four-focal matrix plus exact-focal Unit-2 `35mm`. Every captured accepted call produces an exact source-to-bank byte copy; the first accepted bank in every run is then read unchanged through both the direct `0xf34e0`-returned bank-copy path and the `0xf3350` accessor-side path before a later `0x23c5f0 -> 0xf33d0` selector-1 overwrite. Selected `0x3f7ec0` materialization callsites record zero hits under these complete no-auto-LRIS runs. This closes accepted-bank-to-State/helper-record-assembly custody and one scoped route exclusion only; public record names, final image/source contribution, distributed reducer closure, and final merge acceptance/rejection remain open.

Latest prefusion `0x264270` output-composer addition: four complete canonical two-phase one-hit hardware-watch runs now carry the exact output record assembled from an accepted selector-1 bank into first consumer `0x23faf0`, then carry the exact composer destination into its first later consumer. SHA-pinned code and runtime address equality prove `0x23faf0` receives the assembly output as `rdx` / `rbx` and copies it into its `rdi` / `r12` destination. The caller and first-use routes split by focal family: `28mm` / `35mm` use `0x239e00 -> 0x239ac0 -> State 0x22d250`, then first read composer fields at `0x23a179` into local score-input state before the `0x23a200` positive-pair scoring loop; `70mm` / `150mm` use `0x20afb0 -> 0x20ada0 -> State 0x22ae60`, then first read the composer destination at `0x20dbef` as scalar input to the static `0x20dbe0` three-row SIMD matrix-composition helper. Every second-phase watch observes unchanged bits. This closes exact assembly-output-to-composer-to-first-transform/score-state custody only; public record semantics, downstream image/source contribution, distributed reducer closure, and final merge acceptance/rejection remain open.

Latest prefusion composer-transform materialization addition: SHA-pinned formulas plus route-gated captures now carry that exact composer destination through its immediate calculation, first durable store, and later hardware-watch boundaries on the canonical quartet. Its first nine floats act as an internal `3x3` transform coefficient block. Wide `0x239e00` applies the block to positive 3D records, perspective-projects, accumulates Euclidean residuals against positive coordinate pairs, divides by the accepted count, and returns a scalar that `0x239ac0` stores bit-exactly in a keyed payload; `0x23a530` next reads the exact scalar unchanged under State `0x22d250`. At `0x22d8f5`, the exact scalar is compared with keyed node `+0x28`. Corrected static/runtime proof establishes a local minimum selector: outcome-targeted `28mm` capture proves `score <= existing` enters candidate materialization and stores the exact candidate at node `+0x28`, while `score > existing` retains the existing keyed node, bypasses new-node allocation, and copies that node's `+0x30`, `+0x60`, and `+0x54` slices byte-exactly through selector-1 `0xf33d0` into the same-key per-camera `state+0xe0` object's CalibStage bank `+0x12c..+0x17f`. On both route effects, the node key equals the object's `+0x60` public `CameraModule.id` carrier. The transferred derived slices are not exact public calibration fixed32 sequences or compact public K/pose components under the checked `35mm` LRI. A post-transfer watch and paired callsite capture now carry the exact selected bank into terminal State `0x22e1d0`'s first `0x23c5f0` call, through selector-1 wrapper `0x264440` and `0x264270`, and into `0x23faf0` as its exact assembled right-record pointer/bytes. The changed `0x23faf0` destination then materializes as eight exact float32-to-float64 fields at the same-key node `+0x28..+0x67`; a gated first-touch watch proves that node is copied byte-exactly into a new `0xa8` keyed-tree node and consumed by `0x1ff460`. Installed strings/xrefs bound that body to internal BA camera-map normalization. A changed normalized field is then read by the same-key caller, converted by `0x23c0f0`, composed by `0x2406a0`, and copied exactly through selector-1 `0xf33d0` into the same `CameraModule.id` object's changed CalibStage bank. In the admitted Unit-1 `35mm` transaction, that complete key-`5` bank remains unchanged through terminal State's second `0x23c5f0` call and is read byte-identically at its `0x23cba6 -> 0x264440` assembly callsite. Complete exact-focal Unit-1 and Unit-2 `35mm` controls share the same two-pass 19-read keyed topology, while their numeric bank changes differ. Tele `0x20dbe0` multiplies the composer `3x3` block by a `3x4` row block, and `0x20afb0` copies the exact 48 result bytes into keyed node `+0x20..+0x4f`; for the tracked first-eight-byte node prefix at each tele tier, no intervening touch occurs and the first later touch is zeroing during recursive tree cleanup after HDR output. Runtime scores and observed keys are evidence-run observations, not constants. This closes internal transform/score materialization, the wide same-public-camera-key `state+0x448 <-> state+0xe0` selected-record boundary, and selected-record custody through terminal BA camera-map normalization, same-key CalibStage write-back, and one exact second-pass calibration-helper read, one wide local minimum decision, and a scoped tele route exclusion only; complete public record/transform names, post-helper image/source effect, tele alias/other-node/other-byte or alternate-route proof, distributed reducer closure, and final merge acceptance/rejection remain open.

Latest post-terminal calibration addition: installed RTTI binds `0x3fe460` to the eighth and final `StereoAsyncAPI::ProcessingState` lambda (`$_7`), which runs the higher-group calibration path, finalizes/replaces an internal calibration sibling through `0x226240 -> 0x239a90`, and returns target state `8`. Complete exact-focal Unit-1 and Unit-2 `35mm` runs both observe owner diagnostic byte `+0x10d = 0`, zero entries to the optional `"src_"` / JPEG / overlay body `0x227b00`, one non-null sibling replacement, and normal completion signalling after the enclosing processing State machine returns. A read/write watch armed on the exact finalized owner slot records no later touch before `0x22e9f0` destruction clears and releases the sibling in both bodies. Complete Capstone-decoded constructor proof shows `0x239a90 -> 0x2399a0` initializes only the replacement's own fields and calls only shared-reference-count helpers, excluding publication of a separate alias by that constructor itself. This excludes that optional diagnostic body, constructor-created publication, and an exact-owner-slot consumer as the production post-terminal route within their stated scopes; later or externally copied aliases, image/source effect, reducer closure, and final acceptance remain open.

Additional `CLM-WARP-003` addendum: sequential canonical `28mm`, `35mm`, `70mm`, and `150mm` runtime joins now distinguish the terminal whole calibration State from that replacement sibling and close its relation to the live warp-field-record vector. The final processing lambda's `r12` is the whole State, its finalizer subobject is exactly `State+0x280`, and the replaced sibling slot is `State+0x2a8`. After terminal finalization, every focal tier records five `initResAmp` joins in which `*(PipelineCache+0x180)` and the `0x3f7040` State argument are pointer-identical to that terminal whole-State root, not to the replacement sibling. Installed custody then carries `state+0xe0/+0x448` through `0x3f7040` into the five `0x50` paired transform/warp-field records stored at `PipelineCache+0x258`. The replacement sibling remains untouched through its exact owner slot until destruction. Thus the whole State has a proven four-zoom downstream warp-record consequence, while the proposed new-sibling-to-`PipelineCache+0x258` feed is refuted for this path. Whole-State public naming, reducer closure, and final merge acceptance/rejection remain open.

Latest prefusion node-destination tele scan/score identity addition: for one representative copied node-destination pair at `70mm` and one at `150mm`, the same runtime address is later sentinelized to full `(-1.0, -1.0)` and then sampled at the same address inside the `0x216f60` scan/count window and at the `0x218bc4` score/materialization guard operand while still full sentinel. This links tele node-destination identity to already-bounded local scan/count and score-guard surfaces only; same-address branch-step, whole-vector terminality, image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node-destination tele `0x218bc4` branch-effect addition: fresh complete `70mm` and `150mm` same-address runs now carry one previously finite copied pair per tier through sentinelization, full `(-1,-1)` bytes at `0x218bc4`, flags proving the x-nonpositive `jae` is taken, and a one-instruction step to `0x218cb8`. Deterministic SHA/Capstone proof shows that target skips pair-y loading, local transform/score formation, score-sum update `xmm1`, over-threshold-count update `r10d`, and positive-pair-count update `r9d`. This closes representative local score/count exclusion for those two watched tele pairs only; all-pairs/alias/alternate-route terminality, public acceptance semantics, shared-solve terminality, downstream image/source contribution, reducer closure, and final acceptance/rejection remain open.

Latest prefusion node sentinel-write addition: the downstream `0x21b2e0` path is now proven to execute coordinate-pair sentinel invalidation writes at `0x21b923` and `0x21b92a` across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. Runtime samples show finite non-sentinel coordinate pairs before the x-lane store and x already changed to `-1.0` before the y-lane store; static disassembly proves both stores write raw bits `0xbf800000` (`-1.0`). This is admitted only as live coordinate invalidation/rejection write proof downstream of the node-destination scoring-selection path; final image effect, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion node sentinel-downstream addition: selected sentinel-marked node-vector coordinate pairs are now proven to be touched later by downstream code across clean canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. The watchpoints were armed only after the full pair read `(-1.0, -1.0)` immediately after `0x21b92a`, and every sampled later touch still observed `(-1.0, -1.0)`. Sampled downstream surfaces include State-family copy/record propagation plus coordinate scan/scoring/materialization windows. This is downstream sentinel-coordinate custody / consumption proof only; final image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion `0x216f60` scan-count addition: the already-admitted downstream watchpoint runs sampled tele stops inside the `0x216f60` scan/count window, and every sampled scan-window stop still read the watched pair as two binary32 `-1.0` lanes. Fresh static disassembly proves the local vector and scalar count paths count only pairs where both lanes are positive, with a threshold of at least eight counted entries before continuing. This proves the sampled tele sentinel pairs are local non-counting inputs to this scan/count window; it does not prove whole-vector terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion sentinel score-guard addition: selected tele sentinel-marked node-vector coordinate pairs that reach the `0x218b30` scoring/materialization guard are now proven to skip the body at `0x218bc4 -> 0x218cb8` under clean canonical `70mm` and `150mm` bridge HDR renders. The first proof recorded `26` watched `70mm` guard samples and `24` watched `150mm` guard samples that still read `(-1.0, -1.0)` and had flags taking `jae 0x218cb8`; follow-up branch-step proof directly single-stepped six watched `70mm` samples and three watched `150mm` samples from `0x218bc4` to `0x218cb8`. Static + runtime local-loop proof now shows that the same admitted branch-step samples bypass the positive-coordinate body containing `xmm1` accumulation, `r10d` update, and `r9d` increment; the helper's later `r14` store is derived after converting `r9d` / `r10d`. Companion `28mm` and `35mm` watchpoint runs completed cleanly but did not observe `0x218bc4` for the first six watched sentinel pairs within the watchpoint cap; count-only wide runs observed `152` completed sentinel pairs at `28mm` and `106` at `35mm`, so the wide sentinel population is much larger than the watched subset. This is sampled tele local non-count / non-score proof plus a scoped wide non-observation/count; wide-tier guard behavior beyond the first six watched pairs, whole-vector terminality, final image effect, source contribution, reducer closure, and final acceptance/rejection remain unproven.

Latest prefusion wide direct-guard addition: complete canonical `28mm` and `35mm` direct-census runs collected the full observed wide sentinel populations (`152` unique completed sentinel pairs at `28mm`, `106` at `35mm`) while also installing a direct breakpoint at `0x218bc4`. That direct guard breakpoint recorded zero hits in both runs, with no guard cap hit. This proves the `0x218b30` / `0x218bc4` scoring/materialization guard site is not live under the admitted wide runs; it does not prove wide sentinel entries are terminal or non-image-effecting.

Latest prefusion wide guard-path closure: installed branch/RTTI proof and complete count-only `28mm` / `35mm` runs now explain that zero-hit result. Parent `0x216f60` selects `SparseMirrorAngleOptimizer::CostFunction == 1`, constructs `optimize(...)::$_2`, and dispatches sibling helper `0x218940`; all CostFunction-`0` construction/dispatch/callback/helper sites are zero-hit. Guard `0x218bc4` exists only in the separate CostFunction-`0` family `optimize(...)::$_1 -> 0x218b30`, the family already observed in tele branch-step packets. Both wide runs reach the parent four times, construct/dispatch only the CostFunction-`1` family four times, and write HDR. This closes why canonical wide does not reach `0x218bc4`; it does not establish global terminality for wide sentinel records outside this optimizer family.

Latest prefusion `0x20b5e0` branch-step addition: follow-up four-zoom runtime branch-step proof now shows that three watched `0x20b912` sentinel reads per canonical focal tier still read `(-1.0, -1.0)`, step through `0x20b91d` with runtime flags taking `jae 0x20ba90`, then step through `0x20baab` with runtime flags taking `jbe 0x20bafd`; no admitted trace reaches the local `0x20bac0..0x20bac8` update-write block. This is direct runtime branch-target proof for sampled sentinel reads, not exhaustive terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion State `0x22ae60` copy/record addition: reused four-zoom downstream-watch packets plus fresh static disassembly now classify the sampled State-family `0xe0ae0` copy callers beneath corrected State body `0x22ae60`. `0x20bd60` / `"point BA"` is keyed record materialization; `0x25e4b0` is the no-map `0x25e0c0` row-producer variant; `0x20dca0` is keyed record storage; `0x20ca00` is selected Ceres setup with positive-coordinate gates; and `0x239ac0` / `0x239e00` are keyed pair-vector propagation surfaces. Follow-up copied-slot gate proof further shows one admitted `70mm` watched sentinel copied by the second `0x20ca00` local vector copy has `source_index == gate_index == 774`, is read at `0x20d363` as `(-1.0, -1.0)`, and skips to `0x20d565`; admitted `28mm`, `35mm`, and `150mm` runs show capped no-match windows for the watched sentinels. This prevents treating those sampled windows as opaque possible reducers, but it does not prove sentinel terminality, image effect, source contribution, reducer closure, or final acceptance/rejection.

Latest prefusion State-machine return addition: accepted no-auto-LRIS canonical bridge HDR runtime proof now captures the dispatcher pre/post path at `0x22f3f6` / `0x22f3ff`. Each of `28mm`, `35mm`, `70mm`, and `150mm` records `38` paired dispatcher calls, exits cleanly, writes `10432x7824` HDR output, and shares the same ordered `(operator, pre-state, returned State)` sequence. The reference-group sequence is `0x229df0 -> 2`, `0x229ec0 -> 3`, `0x22a0e0 -> 3,3,3,6`, `0x22a9b0 -> 6,6,6,4`, `0x22aaf0 -> 4,4,4,7`, `0x22ae60 -> 8`, `0x22af80 -> 9`; the higher-group sequence is `0x22bdf0 -> 1`, `0x22bee0 -> 1,1,1,1,3`, `0x22c350 -> 3,3,3,3,6`, `0x22cd00 -> 6,6,6,6,5`, `0x22d250 -> 5,5,5,5,8`, `0x22e1d0 -> 9`. This proves runtime return ordering for the tested dispatcher path, but it does not assign public State semantics, identify semantic `src1` / `src2` contents, prove reducer closure, or prove final acceptance/rejection.

Latest prefusion State-family exact-body addition: installed-bundle static proof now isolates the exact function body for each corrected State operator. The thirteen State operator bodies contain zero indirect calls; dispatcher `0x22f0f0` contains the expected indirect dispatch calls. The exact State bodies expose direct helper-family surfaces and have zero direct calls to the listed known IRAMP/wrapper/owner-route VAs (`0x365960`, `0x3661b0`, `0x369fa1`, `0x3ecc10`, `0x3ecd80`, `0x3eced0`, `0x3ec960`, `0x3e4a80`, `0x3edb80`, `0x36f800`). This bounds the State shells away from being direct known merge/wrapper entry bodies, but it does not prove helper transitive behavior, public State meanings, semantic `src1` / `src2` contents, image effect, reducer closure, or final acceptance/rejection.

Latest editor mode-1 DOF addition: the installed embedded schema names public `ltpb.Settings.DOF.f_num` and `focus_depth`; `RendererBase::setProperty(ParamFloat(0/1), value)` carries those two floats through the renderer-state snapshot into `DOFCache+0x98/+0x9c`. After the depth-ready gate, mode 1 selects DOFCache exactly when `f_num < (cache+0x88 * cache+0x84 / cache+0x80)`; equality selects PipelineCache. At one Unit-1 `28mm`, profile-3, RenderType-1 five-level treatment, the threshold is exact binary32 `2.0 * 28.0 / 3.680000066757202 = 15.217391014099121`. The no-DOF control selects PipelineCache on all 388 classified mode-1 reads. Setting public `f_num=2.0` and public center-derived `focus_depth=6020.888671875 mm` changes all 388 classified mode-1 reads to DOFCache and changes 659,544 final packed level-4 bytes across 264,514 pixels. Public `MaximumInFocusBlurPixels` is ParamFloat 19, accepted by its setter in `[0.1,10]`, forbidden after mode 1 begins, and constrained more strictly to `0 < value < 10` by the optical helper. This closes public activation, exact local cache predicate, and one final-buffer effect only; the internal `0x3f0b90` optical blur/depth-compositing formula, modes 2/3/4, other bodies/focals, and general edit semantics remain open.

Latest editor DOF optical-math addition: installed camera-family tables now pin physical/equivalent focal pairs, base pixel pitches, and hardware f-numbers. The image-scale term is publicly joined through `LightHeader.modules[].sensor_data_surface.data_scale`; the `CapturedImage` constructor copies it to `+0x124/+0x128`, and the pitch helper computes `base_pitch/data_scale.x`. All 84 module records in the two-body exact-focal corpus carry `[1,1]`. The `0x2c5710` near/far focus-range formula is binary32 replayed for 64 live calls, and `0x2c5590` is closed as an SSE-`rcpss` circle-of-confusion endpoint calculation followed by the exact `log2f`/`ldexp` power-of-two radius bucket; one representative for each observed result `{1,3,6,12,25,51,102}` replays exactly. Runtime formula scope is one Unit-1 `28mm` mode-1 treatment; public scale scope is two bodies by four exact focal tiers. `ImageCircleFilter`, layered/occlusion composition, modes `2/3/4`, and other-focal DOF runtime remain open.

Latest editor DOF circle-filter addition: both installed `ImageCircleFilter<vec4x32f>` and `<float>` specializations are uniform inclusive integer-disk averages. For each `dy in [-r,r]`, horizontal support is `[-floor(sqrt(r^2-dy^2)), +floor(sqrt(r^2-dy^2))]`; normalization is exact binary32 reciprocal of the full lattice-point count. Out-of-bounds coordinates clamp to the nearest edge while retaining the full-disk normalization. SHA-pinned builder/helper/worker bodies and Capstone checks close the incremental add/subtract operation order. The Unit-1 `28mm` treatment observes 2,335 vec4 calls at radii `1..6` and 375 scalar calls at radii `1..7`; those are incidence only. Blur-layer selection and foreground/background composition remain open.

Latest editor DOF layered-compositor addition: installed mode-1 depth compositing is now formula-closed from signed blur coordinates through geometric signed layer bins, exact primary membership, three-neighbor boundary ramps, per-layer blur, and reverse-order premultiplied source-over. Odd layer diameter is `2*ceil(abs(bin.upper))+1` (with the sentinel using the first lower bound). Diameters below the installed type-0 cap `13` use the exact uniform disk plus normalized five-tap Gaussian; larger diameters use `s=max(13/D,min(W,10)/W,min(H,10)/H)`, a downsample/filter/upsample pair, and the exact 64-phase cubic B-spline resampler with truncated signed 16.16 coordinates and per-tap edge clamp. The live five-tap words are `3d5f2f87 3e7a0feb 3ece2434 3e7a0feb 3d5f2f87`. One Unit-1 `28mm` mode-1 treatment records `278` copy, `1435` native-filter, and `900` scaled-large calls, exactly `1800` resamples, and large diameters `{17,33,65,129}`; retained tables, transition pixels, and affine calls replay exactly. All 2,613 filter calls use equal first/second rectangles. Runtime remains one body/focal and depth type `0`; nonempty secondary layers, distinct-rectangle runtime, modes `2/3/4`, other bodies/focals, and general edit semantics remain open.

Latest editor RenderingMode addition: installed Qt metadata names exact public values `0 Normal`, `1 RefocusPoint`, `2 RefocusSlider`, `3 DebugView`, and `4 QuickSelect`; app forwarding preserves each value and the libcp jump table maps them to entries `0x3bb524`, `0x3bb588`, `0x3bb5fa`, `0x3bb718`, and `0x3bb76d`. One Unit-1 `28mm` controlled treatment joins all five routes. Public `ParamInt(20)` supplies the DebugView selector: unset `-1` misses all 388 requests and zero-fills, while eleven unique keys exhaust the live size-11 tree, match 388/388 each, select stable virtual targets, and produce distinct outputs. Explicit key `0x300c` reaches `HigherWarpDebug::renderDebugView` target `0x42c140`, confirming its earlier four-focal bridge-HDR zero-hit result was path-specific. The default QuickSelect image is `5216x3912` and all `20,404,992` bytes are zero on each of 388 reads; installed blending uses `a=float(mask_byte)*0.25` toward magenta `[1,0,1,1]`, so the retained default mode-4 output exactly equals the matching Normal output. Debug-object formulas/public meanings, other bodies/focals, and general edit semantics remain open.

Latest active QuickSelect addition: installed app/libcp proof pins the public packet as `vector<Point<float>>`, normalized radius, Boolean mode, four-int level rectangle, and level index, with at least two points, `0 < radius < 1`, and an in-bounds rectangle. One Unit-1 `28mm` treatment applies points `[(0.49,0.5),(0.51,0.5)]`, radius `0.02`, mode `true`, rectangle `[0,0,5216,3912]`, and level `1`. The accepted mask is exact binary byte data with 32,268 ones. At packed level 4, installed sampling selects `(8*x,8*y)`; exactly 501 output pixels sample one, and exactly those 501 pixels change in the active render, with 1,498 changed RGB bytes, maximum delta 64, and alpha unchanged. This closes one active packet, observed mask range, exact mask-to-output support, and final effect only; internal segmentation, other modes/inputs, Boolean semantics, committed-selection behavior, other bodies/focals, and general editor parity remain open.

Latest RefocusSlider formula addition: installed mode `2` first converts rendered float color to exact Rec.601 scalar `Y=(G*0.587+R*0.299)+B*0.114`. For depth `d` and `DOFCache+0x9c` focus `F`, it sets `q=1/(F*0.075)^2`, evaluates the installed cubic fast-`exp2` approximation at `-((d-F)^2*q)`, and forms `m=0.4*(1-E)`. It then computes `(1-m)*Y + m*[0,0.75,1,1]` and forces alpha to one. At one Unit-1 `28mm`, profile-3, RenderType-1 five-level treatment, clean-room replay exactly matches all 108,720,348 scalar pixels, all 108,720,348 mask pixels, and all 434,881,392 blend lanes. Formula/constants are installed-static scope; route incidence remains one body/focal. DebugView formulas/public meanings, QuickSelect internals/commit semantics, other bodies/focals, and complete editor parity remain open.

Latest RefocusPoint overlay addition: after the admitted mode-1 DOF compositor, installed `0x3bbdc4..0x3bbf12` obtains a scalar depth image and computes the in-focus interval through `0x3f08c0` from the DOF cache plus public ParamFloat(19) `MaximumInFocusBlurPixels`. For live color `c`, it uses strict outside predicate `(d < lower) || (upper < d)`, sets `a=c.a` outside and zero inside, then computes `(1-a)*rgba + a*[c.r,c.g,c.b,1]` in binary32 instruction order. At one Unit-1 `28mm`, profile-3, RenderType-1 five-level treatment, stable `c=[1,0,0,0.25]`, public `f_num=2`, and center-derived focus `6020.888671875 mm`, maximum blur `9.0` places all 108,720,348 pixels inside `[163.2976531982422,79525.2421875]`; maximum blur `0.10000000149011612` produces `[2886.326416015625,16448.662109375]` and 88,002,783 outside pixels. Independent replay matches all 434,881,392 lanes in each treatment exactly. Formula is installed-static scope; runtime incidence remains one body/focal, and this is editor-reference rather than bridge-HDR scope.

Latest alternate-profile MonoFusion addition: Renderer profiles `1/2` share installed mode-1 body `0x19f790`. It applies the exact separable float32 kernel `[0.0219000001,0.228499994,0.499199986,0.228499994,0.0219000001]` vertically then horizontally, splits each aligned source patch into low-pass `L` and residual `H=source-L`, Wiener-fuses transformed `L` through the admitted normalized-5/3 path, and overlap-adds residual `g(c)*H`. The exact confidence gate is zero below `0.5`, equals `c` at exact `0.5`, is `(c-0.5)*2.25` through float32 `0.899999976`, and equals `c` above it. Final scalar output is `alpha*T + ((1-alpha)/N)*sum(F_i) + (1/N)*sum(g(c_i)*H_i)`. Both coordinate axes use nearest-valid-pixel extension; a no-overlap contributor adds the target patch to the filtered accumulator and contributes confidence `c=0`. Profile-1 Unit-1 canonical-`35mm` captures replay `256/256` interior values, one gate packet, one invalid packet, and all `272,484` final tile cells exactly; Unit-1 `35mm` vertical and Unit-2 exact-`28mm` horizontal boundary packets each replay `256/256` cells. Profile `2` has same-body liveness but no separate numeric replay. This closes the common mode-1 scalar formula only; `CLM-COMPAT-001` remains `PARTIAL` / `REFERENCE_ONLY` for remaining alternate-profile and editor semantics. No body/firmware causation or cross-body numeric invariance is claimed.

## Reference-Only Scope Facts

These claims are useful guardrails, but they are not primary drivers of the base merge spec.

| Claim ID | Truth | Use |
|---|---|---|
| `CLM-DEPTH-001` | Tested bridge HDR runs showed no `DepthCache` construction/callback activity under the probed conditions. This must not be generalized into "GUI-only". | scope-bound investigation reference |
| `CLM-DEPTH-002` | `DepthEditor` public surface showed zero hits on the tested `28mm` bridge HDR path. | enough to ignore for base-merge work on that path only |
| `CLM-COMPAT-001` | Initial profile-3 GUI-style pyramid construction reaches the admitted IRAMP topology at `28/35/70/150mm`; one tested Unit-1 `28mm` brush rerender reuses prepared state without rerunning IRAMP/stereo/MonoFusion/calibration. Tested 28mm display output is a five-level packed pyramid; installed policy packs nearest/even saturated `255*float` as conditional normal `GL_BGRA` or fallback `GL_RGBA`. The tested default level-4 route is `lt::PipelineCache ->` exact seven-callback Color pipeline `->` type-13 requestRenderROI record `->` packer; type `4` is public serialization. Pre-pipeline bytes equal the HDR-writer input and post-pipeline bytes equal the editor float image. The complete selected ACRE plus linear-ProPhoto-to-sRGB suffix replays one full `256x256` tile byte for byte; tested lens and contrast stages are exact no-ops. Public capture-normalization fields generate the selected ACRE EV, and `tone_mapping.type=light_v1` selects its exact installed LUT. Selected display index-10 color correction is joined from body-specific public `macbeth_data` through an independently reproduced Ceres/white-normalized endpoint and exact map/matrix interpolation to a zero-byte-difference full-image replay. Public mode-1 DOF activation is joined from `Settings.DOF.f_num/focus_depth` through the exact cache predicate to a changed final packed buffer at one Unit-1 `28mm` treatment. Installed optical constants, public `sensor_data_surface.data_scale` pitch ancestry, exact near/far focus range, exact SSE tile-radius bucketing, both circle filters, signed layer construction, neighbor opacity, large-radius cubic resampling, reverse premultiplied source-over, and the final strict-range red RefocusPoint overlay are formula-closed for mode 1. Public rendering-mode values and top-level dispatch are exact; exact RefocusSlider visualization math, all eleven live DebugView keys/targets, and default plus one active QuickSelect packet/mask/final effect are closed at Unit-1 `28mm`. | editor architecture/route/packing guardrail; exact debug-object formulas/public meanings, internal QuickSelect segmentation and committed-selection semantics, nonempty secondary-layer runtime, distinct-rectangle runtime, other bodies/focals, and complete edit semantics remain reference-only |

## Active Parity Blockers

At version `3.0.313`, no claim-ledger blocker remains for canonical profile-3
processing of a structurally complete supported local LRI through the admitted
modern linear-image output contract. This is scope closure, not a declaration
that every alternate profile, GUI/editing path, display look, or unseen input
variant has been reverse engineered. Any newly demonstrated pixel-changing
gap must be opened and proved through the normal evidence path.

### Current Authoritative Set

Version `3.0.335` closes the selected default hot-pixel worker globally. Its
six-pixel parity-preserving upper-median halo plus admitted rank/LUT/isolation
formula replays all `12,979,200` output words on Unit-1 exact-`28mm`, Unit-2
exact-`28mm`, and Unit-1 canonical-`35mm`. `CLM-STEREO-001` is
`PROVEN` / `SPEC_READY` for selected profile 3.

Version `3.0.334` closes MonoFusion mode-0's A1 flow-reference public origin.
Across complete exact-focal `28mm` captures from both physical calibration
signatures, public A1 RAW10 normalization, direct unity-gain GRBG
`DemosaickLightV1`, installed AR1335 luma projection, reciprocal A1/A2
exposure affine `R/Q`, selected public A1 vignetting, and the installed sqrt
LUT reproduce every one of `12,979,200` level-0 samples exactly per body.
The two bodies have distinct RAW, exposure, calibration, scale, and final
hashes. Prior route proof scopes the formula to profile-3 `28mm`/`35mm` mode
0; `70mm`/`150mm` construct no MonoFusion. This selected A1 route receives
the exact public RAW normalization before demosaic and does not consume the
separate default hot-pixel worker. That worker's historical A2 outer-edge
residual is closed by version `3.0.335` above.

- `CLM-PREFUSION-001` and `CLM-PREFUSION-002` are
  `PROVEN` / `SPEC_READY` for canonical profile 3.
- `CLM-MERGE-005` and `CLM-MERGE-006` are
  `PROVEN` / `SPEC_READY`, including candidate policy and final-file score
  consequence.
- `CLM-ZOOM-002` is `PROVEN` / `SPEC_READY` for the tele firing topology.
- `CLM-COMPAT-002` is `PROVEN` / `SPEC_READY`: both complete `28mm`/tele
  exceptions and the complete `74mm`/wide exception are joined to their public
  reference/firing route, stereo/MonoFusion/C6 behavior, five-warp and direct
  IRAMP contributors, crop/orientation, and completed profile-3 output.
- `CLM-PIPELINE-001` is `PROVEN` / `SPEC_READY`: slot 15 is conditional
  linear-ProPhoto/D50 materialization, not a nonlinear look curve. Complete
  Unit-1 four-focal runtime plus targeted Unit-2 wide/tele controls select only
  the exact-copy branch. Generic unequal-selector formulas remain outside the
  admitted route.

### Historical Narrowing Detail

The bullets below preserve the investigation sequence. Any wording in them
that calls prefusion, C6, tele firing topology, row policy, or final
acceptance open is superseded by the admissions above and the claim ledger.
No "open" or "unproven" sentence in this historical subsection is a current
blocker declaration.

- The exact pre-fusion merge/reduction mechanism behind `src1` / `src2` has not yet been proven. `N-to-1 reducer` is a search shorthand, not an assumption that Lumen must contain one tidy reducer closure. The bounded wrapper, source, selector, scoring, state, and accumulation surfaces do not by themselves close distributed reduction. Public `CameraModule.sensor_bayer_red_override.{x,y}` now names scanned item fields `+0x58/+0x5c`; public source-descriptor identity, selector purpose, optional `FusionCacheBayer+0x20` semantic name, public meanings of the `0x2c` record state/target fields, public State/node-field semantics, and merge/reducer closure remain unproven.
- The visible `src2` executor-target wording is now narrowed: four-zoom gate-slot coverage, accepted dispatch through `0x5d94`, worker entry at `0x3ed2e0`, and completed `10432x7824` HDR output are proven. This correction replaces older shorthand that treated "four-zoom visible-`src2` executor-target coverage" as wholly unproven or output-incomplete.
- The pair-grid path is now bounded to an ROI-derived first lattice plus a second transformed lattice. `PipelineCache+0x258` is proven as the live paired transform / warpfield-record vector feeding that path, the consumer-side second-grid formula is proven, and the producer-side dispatcher / row-map split / final scale-field normalization are proven for the post-wrapper `initResAmp` insertion path. The row producer is further bounded to a 4x4 double matrix chain through `0x25ec70`, `0x25e0c0`, and `0x9db20`: `source_b_product * inverse(source_a_product)`. The immediate source-record constructors are bounded through `state+0x448`, `state+0xe0`, `0x23faf0`, `0x264450`, `0x264270`, `0x264460`, and `0x264980`; `0x23faf0` is bounded as source-record composition, `0x264980` as a two-axis field-shift helper, and `0x264460` as a positive two-axis scale helper. The `state+0xe0` object path is bounded through `0x1be970` / `0xe6ba0` shared `lt::CapturedImage` lookup, and `0x264270`'s object accessors are bounded through `0xf34e0` CalibStage banks, `0xf3350`, and `0xf3360`. The `state+0x448` control-object shape and first insertion gate are bounded: it is initialized as a keyed tree/control object, the first visible population loop resolves `state+0xe0` objects, skips objects with `CapturedImage+0x30 == 0`, inserts/updates by the `0xf2720` integer field, and copies first payload fields `+0x00..+0x2c`; later direct writes to found `state+0x448` payloads are bounded through `+0x80`, with nearby stack-only and separate-record helper calls explicitly excluded. The map pointer provider is now runtime-bound across the canonical quartet for the tracked post-wrapper producer entries: `0x3f7040` takes the cross-category `0x3f72f0` branch, `0x268480` calls the `UpsampleLayer` vtable address point `0x658eb0` slot `+0x90 = 0x26b590`, `0x26b590` returns `UpsampleLayer+0x90`, and that return is written to `record+0x40`. Accepted `28mm`, `35mm`, and `70mm` writer-core probes prove `0x26ac13 -> 0xf340` copies a populated `4160 x 3120`, stride-`4160` descriptor into that `UpsampleLayer+0x90` storage before provider use; accepted `150mm` runtime proves the same provider/storage descriptor boundary without writer-body instrumentation. Four-zoom depth-builder probes further prove `0x26aa10` obtains a previous-layer `+0x90` descriptor shaped `2080 x 1560`, calls `0x29ed90`, receives a `4160 x 3120` descriptor, copies it through `0x2673a0`, and moves it into `UpsampleLayer+0x90`; installed debug-output strings label that `+0x90` descriptor as `depth_... .dp`. Four-zoom worker probes now bind `0x29ed90` to callback vtable `0x668288`, slot `+0x30 = 0x29f5c0`, worker body `0x29f600`, output float store `0x29f9de`, a payload layout of high-res 4-byte guide / low-res float source / `[1.0, 1/3]` coefficient table / `1/288` scale / low-res 4-byte auxiliary guide / high-res float destination, and the static guided 2x upsample arithmetic. Follow-up four-zoom custody proof binds that low-resolution float source descriptor to `StereoLayer<false>` index `5`, mode `8`, tile `1`, size fields `+0x2a0/+0x2a4 = 2080 x 1560`, descriptor `+0x2a8`, and vtable slot `+0x90 = 0x26fb50` returning `this+0x2a8`; it also bounds initial descriptor population through `0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` and later overwrite through `0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab`. A no-LRIS rerun of the canonical `28mm` path proves those captured index-5 depth-custody facts are not dependent on auto-loading the same-name `L16_02130.lris` sidecar. A follow-up no-auto-LRIS four-zoom classification proves the later overwrite path reaches `0x26dd40 -> 0x26e120 -> 0x267010 -> 0x26e64a -> 0xf340` for StereoLayer indices `0..5`, and that index `5` is the `2080 x 1560` runtime-built descriptor returned to `0x29ed90`; static inspection classifies `0x267010` as building a 4-byte descriptor from a source descriptor plus `this+0xe0` lookup/vector state before the `+0x2a8` move. Follow-up no-auto-LRIS proof now bounds that source descriptor's immediate internal producer/custody path as `0x26e4c6 -> 0x299c70`, with source object `this+0xf8`, a 2-byte descriptor built at caller `rbp-0xe0`, moved into `rbp-0x80`, and passed unchanged to `0x267010`; the lookup-vector argument is `this+0xe0`. A follow-up no-auto-LRIS four-zoom worker proof binds callback address point `0x6680f0` through generic executor `0x5440` slot `+0x30` to worker `0x29a670` and validates the sampled source-record min-cost `uint16` write formula across all four focal tiers. A Lane B public-meaning audit decodes the public LRI camera/config carriers, binds `f2770` object `+0x60` to public fired camera IDs, confirms `record+0x40` as the internal `UpsampleLayer+0x90` depth descriptor, proves exact public intrinsics-block fixed32 copies for wide A1-A5 `0xf33d0` K/pose packets, and proves exact public pose copies for B4 plus tele C5; the `0x1f0ce0` producer verifier localizes B4/C5 K as zoom-variant non-exact packets at the producer edge. A deeper `0x1f0ce0` K-source trace plus embedded-schema proof establishes that the producer's first usable K vector is an exact public same-camera `intrinsics.k_mat` record, helper entry receives the same camera's two K records plus public `focus_hall_code` scalars, and `0xf3300` supplies runtime `CapturedImage+0x54 = CameraModule.lens_position`; the captured branch linearly interpolates/extrapolates K fields `0`, `2`, `4`, and `5` with float32 arithmetic, and the tested `0xf3350` scale window is identity before both selector-bank copies. The lookup's internal reciprocal ray-depth hypothesis-grid role is admitted by the shared Triangulator bound pair. The lookup context and secondary key are now named `RawImageFactory` and selected public `CameraModule.frame_index`. Selector banks, other B/C packets, tele C6, remaining unclassified `CapturedImage` fields, full `state+0x448`, public names/origins for remaining Cost-volume operands, public calibration/LRI/protobuf origin and names for the ray-depth bounds, remaining full-map distributions beyond the admitted source-local byte-span/mask census, final source contribution, anti-ghosting behavior, and final acceptance/rejection for the `StereoLayer<false>` index-5 descriptor and other worker inputs remain open.
- A scoped Lane B follow-up now proves first-pass `state+0x448` payload `+0x00..+0x2c` exact public pose-component origins: payload `+0x00..+0x20` is the 32,832-byte intrinsics-block rotation component and payload `+0x24..+0x2c` is the corresponding translation component, with anchor `A1` at `28mm` / `35mm` and anchor `B4` at `70mm` / `150mm`, shared across the first-pass inserted keys. Tele public-fired `C6` is not inserted by that first visible path, and checked later `+0x30..+0x3c` source slices have zero exact public fixed32-sequence hits. A later-box formula proof closes formula-level meaning for those later fields: `+0x30/+0x34` is uniform float32 scale and `+0x38/+0x3c` is float32 box origin from `0x260e40` over the `0x145980(object)` box and `object+0x114/+0x118 = [4160,3120]`. This is component/formula-origin proof only; full `state+0x448` semantics remain open.
- A companion Lane B static/runtime proof closes the public input ancestry of the later `state+0x448` `+0x30..+0x3c` formula: the size term is `LightHeader.modules[camera].sensor_data_surface.size`, and the same-camera record consumed by `0x145590 -> 0x145980` is copied from `LightHeader.module_calibration[camera].geometry.distortion.polynomial.{distortion_center, normalization, coeffs, fit_cost}`. The computed envelope, uniform scale, and whole `state+0x448` payload remain derived rather than direct public fields.
- Full merge topology beyond the now four-zoom-proven accumulator, IRAMP entry-signature, and direct contributor-vector identity surfaces is not yet claim-complete across `28mm`, `35mm`, `70mm`, and `150mm`.
- The local IRAMP partner-vector gate is now bounded: empty partner vectors jump to the accumulator region, while non-empty vectors fall through toward SAD. The first-hit partner-record append/population path is also bounded across the four canonical zooms, including the physical record layout of four int32 scalar fields plus thirteen `0x30` descriptor-like blocks. The non-empty consumer path is bounded through coarse SAD / WTA, local absolute-difference refinement, guarded float refinement, bilinear vec4 resampling, `0x36cde0`, a three-float scratch write, `0x36e530` accumulator-prep source/weight wiring, first downstream tuple-consumer wiring, immediate post-reciprocal weighted-add wiring, immediate post-weighted-add shaping, caller-side post-IRAMP square-copy handoff, caller-side post-square vector-scale handoff, caller-side `0x3e5720` executor setup, row callback `0x38a30` float-channel to binary16 conversion, caller-side owner `+0xf0` output-descriptor sink, first owner `+0xf0` downstream consumer / binary16-to-vec4 expansion family, immediate expansion handoff at `0x3d502e`, the caller-provided destination context backing that local expansion view, the first captured selected-cache read/rescale route through `0x3d084d -> 0x36f800`, first-owner census coverage of sibling branch `0x3d4864` still returning to selected-cache caller `0x3d084d`, first direct-branch post-route handoff to `0x3d08ce -> 0x36f800`, global branch-site caller/slot families `{0x3d0732, 0x3d084d, 0x3ecc5a}` / `{0x3ec960, 0x3e4a80}`, global post-route family classification into exact-size cleanup / owner-cache `0x36f800` rescale / visible-`src1` `0x3edb80` normalization, global parent-chain ancestry for those caller families, static parent-chain body classification, static helper-surface classification, static selected-cache/post-route classification, static downstream direct-caller census for `0x36f800` / `0x3d01b0` / `0x3edb80` / `0x3d50f0`, static selected-cache caller census for `0x3d0650`, static `0x3e5720` caller census, static `0x3d4e10` caller census, static/runtime `0x3d5400` executor-route liveness, that route's first `0x36f800` weighted `vec4` store through `0x3721d0 -> 0x372210` with runtime probe at `0x372224` and store at `0x372488`, row-plan/cache helper setup, captured 4-tap horizontal row-cache stores, fresh first-dispatch row-plan coverage across all four canonical zooms, and full-render leading/trailing row-cache segment reachability at `28mm` and `70mm` with scoped zero-hit results at `35mm` and `150mm`. This does not close public field semantics, public weight/shaping semantics, public row-channel / pixel-format names, downstream row-image/final policy after the classified caller/helper/post-route/direct-caller/selected-cache-caller/`0x3e5720`-caller/`0x3d4e10`-caller/`0x3d5400`-executor-route families, the complete candidate predicate, or final acceptance/rejection.
- Exact tele odd-camera routing, especially C6, remains partially unresolved. The keyed helper / vector-builder boundary at `0x1bdc80` / `0x1be750` / `0x1be270` and projection field-pack dispatcher boundary at `0x3f6170` / `0x3f6200` / `0x3f6940` are excluded as positive C6-routing observations under the canonical bridge HDR runs: tele helper/dispatcher keys omit key `15`. Constructor/watchpoint proof shows key `15` is initially constructed active at item `+0x30 = 1`, then later cleared to `0` at `libcp+0x3c90a5` inside body `0x3c8f90` under the observed local gate. Focused census and identity proof tie the active key-list helper/mutation observations, the mutation store, and later inactive context-walk observation to the same item pointer; static inspection proves helper `0x1bdb60` is key-list bookkeeping. A remaining-direct `0xf2720` census now covers the 34 direct static sites outside that focused set; together the two admitted tele proofs cover all 58 static direct `call 0xf2720` sites, with the newly active key-15 sites bounded to constructor-adjacent key/container/tree materialization surfaces. A same-byte post-mutation active-byte watchpoint then records 18 later stops per canonical tele render, all still observing the watched key-15 `item+0x30` byte as `0`; the stopped libcp sites include active-byte gates outside the direct `0xf2720` callsite inventory, and the final non-libcp stop is allocator cleanup after output write. A selected-field post-mutation watchpoint then bounds watched item ranges `+0x58..+0x5f`, `+0x60..+0x67`, and `+0x100..+0x107`: the `+0x60..+0x67` range is read pre-output at `0xf2727` (`+0x60`) and `0xf3327` (`+0x64`), while watched pair and type/adjoining ranges record only allocator-cleanup stops after output write. The post-mutation caller consumes the constructed `ctx+0xa0` object, writes state to context `+0xc8`, queues `context+0x4b0 = 5`, and then follows a rect-vector route now proven to feed five `context+0x4c0` delta-dimension pairs into `0x3982b0` ImagePyramid construction; a follow-up proves those five ImagePyramid levels are immediately wrapped as full-image descriptors and passed through direct zero-fill callsite `0x3b2f54 -> 0xf7c0`, with after-return first-32-byte samples zero for all twenty level descriptors across the canonical quartet. A downstream-candidate probe re-hit the zero-fill route and recorded zero hits at selected later static `context+0x538` candidate families across complete canonical bridge HDR renders, a representative four-zoom data-watch probe recorded zero later hits at four selected byte ranges, and an expanded tele data-watch grid recorded zero later hits across first/middle/last 8-byte ranges for all five zero-filled ImagePyramid levels at `70mm` and `150mm`. Candidate route `0x3c9540 -> 0xe6c30` is zero-hit under complete canonical tele bridge HDR renders while the constructor/mutation custody sites hit. The direct payload and stereo-side keyed-record loops both visit key `15` at tele tiers but filter it by post-mutation `object+0x30 = 0`. Whether the zero-filled ImagePyramid/geometry route is later written/read outside the watched representative/tele-grid byte ranges or through unprobed helpers/aliases in a final image/merge-effecting way, whether untested C6 fields or object aliases are live, whether the watched `+0x60..+0x67` reads have final image effect, whether the `0x3c90a5` mutation is terminal for canonical bridge HDR, and whether any alternate C6 route has final image effect remains unproven.
- Final merge acceptance / rejection logic beyond the proven accumulator is still unknown.

The authoritative blocker list lives in `docs/canonical/PARITY_BLOCKERS.md`.

## Four-Zoom Validation Rule

All parity validation must work at:

- `28mm`
- `35mm`
- `70mm`
- `150mm`

Canonical seed LRIs:

| Zoom | LRI | Unit signature | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

The wider corpus includes LRIs from two physical L16 devices. Filename alone is not a stable identity because file names can overlap between devices; use full path plus unit/device context for all validation artifacts. The old `Unit A` / `Unit B` seed labels are refuted by per-file calibration-hash proof: all four canonical seeds above are Unit-1. Therefore "four-zoom verified" runtime claims currently mean one physical body across four focal tiers, not cross-unit universality. Unit-2 same-name counterparts exist, but follow-up static verification shows not all same-name counterparts are exact-focal matches; use exact-focal Unit-2 representatives for cross-unit runtime reruns. See [bundle_proof_two_unit_corpus_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_two_unit_corpus_static.md) and [bundle_static_lane_b_crossunit_lri_public_carriers.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_lane_b_crossunit_lri_public_carriers.md).

Correction note: `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri` was formerly listed as the 35mm seed, but direct `LightHeader` decode proves it has `image_focal_length = 98` and a tele-tier `5B+6C` firing set. It must not be cited as 35mm evidence. The corrected true-35mm seed above has `image_focal_length = 35` and a wide-tier `5A+5B` firing set; see [lri_35mm_seed_correction_true35_runtime.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lri_35mm_seed_correction_true35_runtime.md).

Validation is not complete unless all four tiers are checked for:

- fired-camera participation
- framing / crop behavior
- warp / geometry behavior
- merge quality, including ghosting and trailers

## Source Precedence

For new work, use sources in this order:

1. `docs/canonical/CLAIM_LEDGER.md`
2. `docs/TRUTH.md`
3. other files in `docs/canonical/`
4. `docs/evidence/`
5. `docs/quarantine/` and external scratch docs, claim-by-claim only

## What This File Replaced

The older v2 root TRUTH mixed verified findings, partial findings, open questions, and superseded narratives in one long document.

That older narrative is not deleted. It is preserved by git history, and its row-by-row carry-forward decisions are documented in `docs/canonical/TRUTH_RECONCILIATION.md`.
