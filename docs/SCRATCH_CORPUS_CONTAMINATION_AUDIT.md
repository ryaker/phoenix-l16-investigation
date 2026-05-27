# Scratch Corpus Contamination Audit

**Date:** 2026-04-22
**Corpus:** `/Volumes/Dev/lumen-phoenix-scratch`
**Corpus size:** 136 markdown files
**Purpose:** identify which merge-critical findings were actually proven, which truths were later obscured by stale text, and which topics remain genuinely open.

## Scope

This is a **broad-sweep + targeted-deep-read** audit, not a full line-by-line re-read of all 136 files.

What was done:

- broad grep sweeps across the full scratch corpus for repeated high-conflict topics
- targeted reads of the files carrying the strongest proof, the strongest contradictions, or both
- cross-check against the live installed bundle where the bundle itself could settle the issue

This document is therefore strongest on:

- merge location and merge-path contradictions
- 35mm / 150mm zoom contradictions
- depth / DepthCache / DepthEditor scope overclaims
- `Ceres` / `f_scale`
- IRAMP / warp-grid / anchor-pre-fusion drift

It is **not** a statement that every scratch claim outside those areas has been fully re-audited.

## Classification Rules

This audit uses three labels:

- **FOUND-AND-LOST**: the corpus did reach the correct answer, but older or stale material kept the wrong framing alive afterward.
- **PARTIALLY-FOUND**: some real truth is present, but the full claim was never fully closed; downstream docs must cite only the resolved subparts.
- **NEVER-ACTUALLY-PROVEN**: the corpus contains hypotheses, candidates, or narrative confidence, but never reached strict proof.

## Core Result

The scratch corpus does contain real architectural truth, but it is **not self-stabilizing**. Three contamination patterns recur:

1. A later file proves something, but older files remain easy to quote and keep the old uncertainty alive.
2. A file adds a precision-correction banner, then still contains unrevised absolute wording later in the same file.
3. A negative tested-scope result (`0 hits under these conditions`) gets silently promoted into a global statement (`never`, `GUI-only`, `not in the codepath at all`).

That means the scratch corpus is useful, but **no single document should be treated as authoritative without claim-level filtering**.

## Source Precedence

For future work, the safe precedence order should be:

1. **Live-bundle proof**
   Direct bytes, direct disassembly, direct LLDB from the installed `Lumen.app`.

2. **Late scratch docs with direct evidence and scope discipline**
   Example: [ceres_evaluate_bodies.md](/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md), [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md), [35mm_renderer_mechanism.md](/Volumes/Dev/lumen-phoenix-scratch/35mm_renderer_mechanism.md)

3. **Meta-audits used as contamination maps, not architecture truth**
   Example: [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md), [critique_audit.md](/Volumes/Dev/lumen-phoenix-scratch/critique_audit.md)

4. **Older architecture narratives or hypothesis docs only for traceability**
   These should never outrank later proof.

## Topic Audit

### 1. Ceres `f_scale` at `0x5c3580`

**Classification:** `FOUND-AND-LOST`

**Safe conclusion:**

- `f_scale = 1.0` was actually closed.
- The contrary `(42.0, 1023.0, ...)` interpretation came from a bad file offset, not from the real bytes at `0x5c3580`.

**Winning sources:**

- [ceres_evaluate_bodies.md](/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md): explicit bad-offset diagnosis, correct bytes, LLDB capture of `a_=1.0`, `b_=1.0`
- [va_registry.md](/Volumes/Dev/lumen-phoenix-scratch/va_registry.md): records `0x5c3580` as `a = 1.0`
- [LUMEN_APP_PROOF_ONLY_AUDIT.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/LUMEN_APP_PROOF_ONLY_AUDIT.md): live bundle byte proof from the installed `libcp.dylib`

**Contaminating sources:**

- [ceres_residual_bodies.md](/Volumes/Dev/lumen-phoenix-scratch/ceres_residual_bodies.md): starts with a refutation banner, but still contains the stale wrong-offset narrative in the retained body
- [legacy_doc_audit_round2.md](/Volumes/Dev/lumen-phoenix-scratch/legacy_doc_audit_round2.md): preserves the stale “do not assume `f_scale=1.0`” quote
- [cleanup_actions_log.md](/Volumes/Dev/lumen-phoenix-scratch/cleanup_actions_log.md): records an intermediate “already marked unverified” state that later became false

**Audit verdict:** this is a textbook case where truth was found and then not kept dominant enough.

### 2. `FusionCacheBayer` as the 10-camera merge entry point

**Classification:** `FOUND-AND-LOST`

**Safe conclusion:**

- `FusionCacheBayer` is **not** the 10-camera merge entry point for the bridge HDR path.
- The “FCB is the fusion pipeline” story was explicitly refuted inside the scratch corpus.

**Winning sources:**

- [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md): repeatedly flags the `FusionCacheBayer` interpretation as refuted
- [merge_canvas_writes.md](/Volumes/Dev/lumen-phoenix-scratch/merge_canvas_writes.md): also rejects FCB as the bridge HDR fusion entry point
- [merge_function_reconciliation.md](/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md): correctly rejects FCB as the cross-camera compositor

**Contaminating sources:**

- older inventory/current-state material quoted inside [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md)
- stale references to `ColorFusionBayer` / `FusionCacheBayer` as “the L16 fusion pipeline,” explicitly called out in the audit

**Audit verdict:** the corpus did successfully kill the `FusionCacheBayer` theory, but later readers could still get misled if they quote the old narrative instead of the audit.

### 3. `ImageResolutionAmp` / IRAMP as a real multi-source merge operator

**Classification:** `FOUND-AND-LOST`

**Safe conclusion:**

- `ImageResolutionAmp` / IRAMP is a real multi-source operator inside `libcp`.
- The body at `0x3661b0..0x36ae41` contains a per-source weighted accumulator into an output canvas.
- This is not hypothetical; scratch has direct instruction-level evidence.

**Winning sources:**

- [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md): strongest direct proof, including the accumulator at `0x369fa1..0x369fa8`
- [va_registry.md](/Volumes/Dev/lumen-phoenix-scratch/va_registry.md): records IRAMP body and accumulator
- [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md): explicitly says earlier docs missed `ImageResolutionAmp`

**Contaminating sources:**

- [merge_function_reconciliation.md](/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md): after correctly rejecting FCB, it swings too far and claims the cross-camera merge lives outside `libcp`

**Audit verdict:** the scratch corpus did find a real merge operator in `libcp`, but the overall merge story did not stabilize and later writings reopened the location question in over-broad ways.

### 4. Full merge topology: exact relationship among anchor pre-fusion, IRAMP, and final fusion

**Classification:** `PARTIALLY-FOUND`

**Safe conclusion:**

- IRAMP is real and multi-source.
- `src1` / `src2` are not simple single-camera inputs.
- contributor vectors at 28mm and 70mm were identified.
- several candidate “this exact pre-fusion reducer” sites were refuted.

**Winning resolved subparts:**

- [iramp_camera_identity.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_camera_identity.md): contributor vectors and shared `src1` / `src2` callable behavior
- [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md): accumulator proof
- [composite_producer.md](/Volumes/Dev/lumen-phoenix-scratch/composite_producer.md): refutes one misread of `PipelineCache+0x8`
- [lldb_pipelinecache_level_vector_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_pipelinecache_level_vector_four_zoom.md): repo-local four-zoom proof superseding scratch-only `PipelineCache+0x8` details; `PipelineCache+0x8` is level-vector metadata, not an image/composite pointer
- [runreferencegroupcams_body.md](/Volumes/Dev/lumen-phoenix-scratch/runreferencegroupcams_body.md): refutes one claimed N→1 reducer site

**Unresolved remainder:**

- exact body of the pre-fusion reducer behind `src1` / `src2`
- exact division of labor between anchor pre-fusion and IRAMP for the final “stunning merge”
- whether any additional merge-critical stage outside the proven IRAMP accumulator still affects ghosting-critical output

**Contaminating sources:**

- [anchor_prefusion_and_c6.md](/Volumes/Dev/lumen-phoenix-scratch/anchor_prefusion_and_c6.md): useful mechanically, but over-interprets `[r14+0x8]`
- [merge_function_reconciliation.md](/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md): overstates the “outside libcp” conclusion
- [merge_canvas_writes.md](/Volumes/Dev/lumen-phoenix-scratch/merge_canvas_writes.md): useful for requestRenderROI/canvas observations, but too broad as a sole global fusion model

**Audit verdict:** important pieces are real, but the whole merge topology is still not closed to “ghost-free implementation” standards.

### 5. 35mm behavior

**Classification:** `PARTIALLY-FOUND`

**Safe conclusion:**

- `35mm != "5B + computational synthesis"`
- on the bridge path, 35mm uses an internal crop-plus-upsample mechanism
- the same fired-camera story as 28mm is compatible with the crop being a render-time decision

**Winning sources:**

- [35mm_renderer_mechanism.md](/Volumes/Dev/lumen-phoenix-scratch/35mm_renderer_mechanism.md): strongest bridge trace
- [35mm_crop_math.md](/Volumes/Dev/lumen-phoenix-scratch/35mm_crop_math.md): supportive math, with some explicit unresolved pieces
- [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md): tracks the stale contradictions

**Contaminating sources:**

- stale “5B + computational synthesis” story
- stale “35mm canvas center-crop output = 8346×6260 on the bridge” story

**Still not proven:**

- exact Lumen GUI export behavior at 35mm
- whether bridge hard-coded output sizing is the entire reason users see the discrepancy

**Audit verdict:** the corpus found real truth about the bridge render path, but not the whole 35mm user-facing story.

### 6. 150mm firing set

**Classification:** `FOUND-AND-LOST`

**Safe conclusion:**

- the stale `150mm = 6C only` story is not the winning one
- newer scratch material sides with `150mm = 5B + 6C`

**Winning sources:**

- [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md): explicitly documents the contradiction and chooses the newer 11-camera story over the stale 6-camera row

**Contaminating sources:**

- the older `150mm = 6C only` rows quoted inside the audit itself

**Audit verdict:** the right answer existed, but stale rows in the same document family made the wrong answer linger.

### 7. Depth on bridge HDR, `DepthCache`, and “GUI-only”

**Classification:** `PARTIALLY-FOUND`

**Safe conclusion:**

- tested LLDB probes saw **no `DepthCache` construction/callback activity** under the tested bridge HDR conditions
- that is a valid tested-scope result
- it does **not** justify global claims like “bridge HDR does not produce depth” or “DepthCache is GUI-only” without qualification

**Winning sources:**

- [c6_destination_and_depthcache.md](/Volumes/Dev/lumen-phoenix-scratch/c6_destination_and_depthcache.md): the precision-correction banner at the top is the safe part
- [depth_editor_and_iramp_depth.md](/Volumes/Dev/lumen-phoenix-scratch/depth_editor_and_iramp_depth.md): correctly separates IRAMP scratch from renderer-visible depth and says the `DepthCache` populator is not yet traced

**Contaminating sources:**

- the **same** [c6_destination_and_depthcache.md](/Volumes/Dev/lumen-phoenix-scratch/c6_destination_and_depthcache.md), whose lead verdict table later reverts to absolute wording
- the **same** [depth_editor_and_iramp_depth.md](/Volumes/Dev/lumen-phoenix-scratch/depth_editor_and_iramp_depth.md), which includes a careful scope disclaimer and then still says `GUI-ONLY`

**Audit verdict:** this is a classic “precision correction exists, but the doc still re-contaminates itself later” case.

### 8. `DepthEditor`

**Classification:** `PARTIALLY-FOUND`

**Safe conclusion:**

- `DepthEditor` showed zero hits on the tested 28mm bridge HDR run
- that is enough to say Phoenix base-merge work can ignore it for that tested path
- it is **not** enough to say the whole surface is globally GUI-only

**Winning sources:**

- [depth_editor_and_iramp_depth.md](/Volumes/Dev/lumen-phoenix-scratch/depth_editor_and_iramp_depth.md): its tested-scope disclaimer is the safe interpretation

**Contaminating source:**

- the absolute `GUI-ONLY` verdict inside the same document

**Audit verdict:** useful negative result, but not globally closed.

### 9. `0xf540` and the warp dst-coordinate array

**Classification:** `PARTIALLY-FOUND`

**Safe conclusion:**

- the scratch corpus already had the key pieces that `0xf540` is an image resize/alloc helper and that `0x366500..0x366553` initializes the coordinate grid
- the full semantic interpretation of that grid was not closed in scratch

**Winning sources:**

- [va_registry.md](/Volumes/Dev/lumen-phoenix-scratch/va_registry.md): `0xf540` as image resize/alloc
- [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md): identifies `0x366500..0x366553` as coordinate-grid initialization
- [LUMEN_APP_PROOF_ONLY_AUDIT.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/LUMEN_APP_PROOF_ONLY_AUDIT.md): live-bundle proof that `0xf540` prepares storage and the actual pair writes happen later

**Audit verdict:** the corpus had more truth here than later summaries preserved, but it did not finish the semantic decode.

### 10. Exact pre-fusion reducer behind `src1` / `src2`

**Classification:** `NEVER-ACTUALLY-PROVEN`

**Safe conclusion:**

- several candidate sites were investigated and refuted
- `src1` / `src2` are composite-ish wrappers over a shared callable, not simple single-camera objects
- the exact N→1 reducer body was **not** closed

**Evidence trail:**

- [anchor_prefusion_and_c6.md](/Volumes/Dev/lumen-phoenix-scratch/anchor_prefusion_and_c6.md): useful construction-site mechanics, but candidate interpretation overreaches
- [runreferencegroupcams_body.md](/Volumes/Dev/lumen-phoenix-scratch/runreferencegroupcams_body.md): refutes one candidate
- [composite_producer.md](/Volumes/Dev/lumen-phoenix-scratch/composite_producer.md): refutes another candidate and points to the still-unresolved callable path

**Audit verdict:** this is a genuine open item, not a forgotten closed one.

### 11. Exact C6 destination at 70mm

**Classification:** `NEVER-ACTUALLY-PROVEN`

**Safe conclusion:**

- C6 is absent from the directly observed IRAMP contributor vector at 70mm
- C6 was not directly observed in the tested merge-stage buffers
- exact destination path remains unresolved

**Winning sources:**

- [iramp_camera_identity.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_camera_identity.md)
- [c6_destination_and_depthcache.md](/Volumes/Dev/lumen-phoenix-scratch/c6_destination_and_depthcache.md)

**Audit verdict:** the corpus has strong negative observations, but not a positive destination proof.

## Document-Level Trust Notes

These notes are not about whether a whole file is “good” or “bad.” They are about how to use it safely.

### Safe as claim-level anchors

- [ceres_evaluate_bodies.md](/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md)
  Safe for `f_scale` and the decoded Ceres bodies.

- [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md)
  Safe for “IRAMP is a real multi-source accumulator” and for the specific accumulator/store instructions.

- [35mm_renderer_mechanism.md](/Volumes/Dev/lumen-phoenix-scratch/35mm_renderer_mechanism.md)
  Safe for the tested bridge 35mm crop+upsample behavior.

- [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md)
  Safe as a contamination map. Not a raw architecture source by itself.

- [critique_audit.md](/Volumes/Dev/lumen-phoenix-scratch/critique_audit.md)
  Safe as a contamination map. Not a raw architecture source by itself.

### Use only with claim-level filtering

- [c6_destination_and_depthcache.md](/Volumes/Dev/lumen-phoenix-scratch/c6_destination_and_depthcache.md)
  Use the precision-correction banner. Quarantine the later absolute lead-verdict wording.

- [depth_editor_and_iramp_depth.md](/Volumes/Dev/lumen-phoenix-scratch/depth_editor_and_iramp_depth.md)
  Use the tested-scope findings. Quarantine the global `GUI-ONLY` phrasing.

- [merge_canvas_writes.md](/Volumes/Dev/lumen-phoenix-scratch/merge_canvas_writes.md)
  Useful for requestRenderROI / canvas materialization observations, but too broad as a total fusion theory.

- [anchor_prefusion_and_c6.md](/Volumes/Dev/lumen-phoenix-scratch/anchor_prefusion_and_c6.md)
  Useful mechanically for src1/src2 construction, but not authoritative on what the wrapped object actually is.

### Quarantine for specific over-broad conclusions

- [merge_function_reconciliation.md](/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md)
  Keep its refutations of `0x36f800` and `FusionCacheBayer` as merge sites. Quarantine its stronger “cross-camera merge does not live in libcp” conclusion, because later scratch and live-bundle evidence establish a real multi-source merge operator in `libcp`.

## Control Rules For Future Documentation

If the goal is to stop stale findings from re-contaminating the record, future docs should obey these rules:

1. **No whole-file authority.**
   Cite claims, not documents. Several scratch files contain both winning corrections and stale statements.

2. **Superseded banner wins over retained body text.**
   If a document begins with a superseding note, later retained legacy text in the body cannot outrank it.

3. **A 0-hit LLDB result must always carry tested conditions.**
   If the wording can be read as global, it is too broad.

4. **Merge-critical claims require body proof, not only naming proof.**
   Type names, call chains, or candidate ownership are not enough. For merge truth, require accumulator/store instructions, live hit evidence, or direct byte proof.

5. **Meta-audits do not create architecture truth.**
   Audits are for quarantine and conflict tracking. They do not replace primary proof.

6. **When a topic is only partial, write it as two lines:**
   one line for what is closed, one line for what remains open.
   This prevents “partial closure” from mutating into “fully solved.”

7. **Do not let later summaries outrank narrower proof-only docs.**
   The closest document to the raw evidence should win.

## Practical Next Step

For merge-quality work aimed at a ghost-free modern Lumen replacement, the safest working set is:

- use [LUMEN_APP_PROOF_ONLY_AUDIT.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/LUMEN_APP_PROOF_ONLY_AUDIT.md) for direct bundle-backed corrections
- use [ceres_evaluate_bodies.md](/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md) only for Ceres
- use [iramp_kernel_body.md](/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md) only for IRAMP accumulator truth
- use [35mm_renderer_mechanism.md](/Volumes/Dev/lumen-phoenix-scratch/35mm_renderer_mechanism.md) only for bridge 35mm behavior
- use [backward_audit_2026-04-16.md](/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md) and [critique_audit.md](/Volumes/Dev/lumen-phoenix-scratch/critique_audit.md) only to quarantine stale claims

Everything else should be cited only after claim-level verification.
