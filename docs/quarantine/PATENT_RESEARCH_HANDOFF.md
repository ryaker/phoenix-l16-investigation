# Patent Research Handoff - Quarantined Intake Copy

## Quarantine Status

This is a repo-local quarantined intake copy of a user-provided patent research
handoff. It is not canonical evidence and admits zero claims to the project
ledger.

## Provenance

- Source path at intake: `/Users/ryaker/Downloads/PATENT_RESEARCH_HANDOFF.md`
- Source file modified time at intake: `May 22 12:40:31 2026`
- Source file size at intake: `9303 bytes`
- Source SHA-256 at intake:
  `7b0e37c1dc8da79a2218362721a837604bb7c84315b6dee212535bfce78a2222`
- User-stated generation provenance: Google Gemini 3.1 Pro performed patent
  search; Claude Sonnet 4.6 analyzed the research report.

## Admission Rules

- Use this document only for claim discovery, verification planning, or
  contradiction tracking.
- Do not cite this document as proof of Lumen/LRI behavior.
- Any claim discovered here must be independently verified against installed
  binaries, runtime probes, local artifacts, or primary patent/public sources
  before it can enter `docs/canonical/CLAIM_LEDGER.md`.
- Merge-critical claims remain zoom-scoped until independently verified across
  the required 28mm, 35mm, 70mm, and 150mm validation set.

## Source Document Begins

# Patent Research Handoff

**Status**: `HYPOTHESIS`
**Source**: External patent sweep conducted during Codex limit gap (May 2026)
**Admission status**: ZERO claims admitted to `CLAIM_LEDGER.md`
**Purpose**: Two scoped verification tasks for Codex to evaluate on resume

Nothing in this document may be cited as project truth. Everything here
is a structured hypothesis. Admission requires the standard evidence path:
runtime proof or installed-bundle static proof, four-zoom scope where
merge-critical, admitted to `CLAIM_LEDGER.md` with explicit zoom coverage.

---

## Background

A patent sweep of Light Labs Inc. / Light Co filings was conducted while
Codex was at limit. The sweep identified two findings worth structured
verification. All other patent content (Pelican Imaging cross-references,
hypothetical codebase paths, semantic segmentation patents) is background
context only and is explicitly excluded from verification scope.

---

## Finding 1: Ceres Solver Build String

### What Was Found

A public analysis of the Lumen binary identified an embedded Jenkins CI
build path string consistent with Google Ceres Solver v1.12.0:

```text
c:\Users\srv-build\jenkins\workspace\CI-multi-platform-v2\
CI_Projects\CI-WIN\3rdparty\ceres-solver-1.12.0\internal\ceres\
trust_region_preprocessor.cc
```

Ceres Solver is a non-linear least-squares optimization library. The
specific module referenced — `trust_region_preprocessor.cc` — handles
trust-region optimization, which is used in bundle adjustment and camera
pose estimation.

### Why It Matters If True

The warp geometry row producer is already proven as:

```text
source_b_product * inverse(source_a_product)
```

This 4x4 double matrix formula is the kind of output Ceres bundle
adjustment produces when solving camera extrinsics. If Ceres is confirmed
inside `libcp`, it provides a concrete upstream explanation for where those
transform matrices come from and how the per-camera warp records are
computed.

It would not by itself close `CLM-PREFUSION-002` or `CLM-WARP-003`, but
it would narrow the search space for the calibration semantics blocker.

### Verification Task 1

**Scope**: Static binary only. No runtime probe required.

```bash
strings /path/to/libcp | grep -i "ceres\|trust_region\|srv-build\|jenkins"
```

**Accept condition**: The exact string or a recognizable fragment of it
is present in `libcp`.

**Reject condition**: No match. The external analysis was wrong or refers
to a different binary.

**On accept**: Create `docs/evidence/static_libcp_ceres_string.md`.
Record the exact matched string(s), the binary path, and the `strings`
command used. Admit as a static provenance fact only — not as proof of
which code path calls Ceres or when. Do not generalize to merge behavior.

**On reject**: Record as `0 hits` with the tested binary path. Do not
pursue further under this task.

---

## Finding 2: Patent US8913145B2 Claim Correspondence

### What Was Found

Patent US8913145B2 (Rajiv Laroia, assigned to Light Co portfolio) claims
a two-sensor merge architecture. Claim 1 includes:

> "the combining of the first and the second images includes up-sampling
> the first image and down-sampling the second image; and the first image
> is sharpened after the up-sampling"

> "the second image forming a central portion of the single combined
> image and a peripheral portion of the first image forming a peripheral
> portion of the single combined image"

The patent describes asymmetric focal length blending: a wider FOV source
(first image) is up-sampled and sharpened; a narrower FOV telephoto source
(second image) is down-sampled; the telephoto source occupies the center
of the final composite.

### Why It May Be Relevant

Three already-proven surfaces show potential structural correspondence
with this patent's architecture. These are observations, not claims:

**Observation A — `src1` receives a four-level pyramid**

The proven `src1` payload constructor path `0x3dfcc0 -> 0x3e2db0 ->
0x3e27a0` receives level vector:
`(4160,3120), (2080,1560), (1040,780), (520,390)`

A four-level pyramid is consistent with multi-scale up-sampling prep on
a wide-angle source. This is structural correspondence only.

**Observation B — `src2` is a one-source radial resampling worker**

The proven `src2` executor target `0x65f7e8/+0x30 = 0x3ed2e0` is a
one-source descriptor resampling/materialization worker with a 4096-entry
radial scale table. The accepted `28mm` state sample shows:

- Radial scales: `(1.0, 1.0)`
- Offsets: `(2020.0, 1505.0)` — slightly off-center from `4160x3120`
- Matrix: `(0.9913..., 0.0, 17.0; 0.0, 0.9913..., 13.0; 0.0, 0.0, 1.0)`

A radial correction with a near-identity scale (<1% correction) and
small translation offset is consistent with lens distortion correction
applied to a single camera source before it serves as a merge reference.
This is structural correspondence only.

**Observation C — `0x3edb80` is one-image `sqrt(max())` normalization**

The proven `src1` normalization body `0x3edb80` is called directly after
the `src1` wrapper path. A sharpening or normalization step applied to
`src1` after multi-scale construction is consistent with "sharpened after
up-sampling" in the patent claim. This is structural correspondence only.

### What This Does NOT Claim

- This does not identify `src1` as the wide camera or `src2` as the tele
  camera. The L16 is a 16-sensor system; the patent describes a 2-sensor
  system. The architecture may differ significantly.
- This does not close `CLM-PREFUSION-002`. The reducer math remains open.
- The constructor key `0` at wide / `8` at tele does not map to "first
  image / second image" in the patent without further proof.

### Verification Task 2

**Scope**: Scoped static + targeted runtime. Falsifiable against existing
proven surfaces only.

**Step 2a — Static**: Inspect `0x3e27a0` (the `src1` payload constructor
body). Does it contain up-sampling logic, or does it build a descriptor
chain consistent with multi-scale image preparation? Record what it does
without assuming the patent mapping.

**Step 2b — Static**: Re-examine `0x3ed2e0` (the `src2` worker body).
The 4096-entry radial table and `1/64` fractional coefficient indexing
are already proven. Does the output descriptor shape and stride match
what you would expect from a down-sampled or lens-corrected telephoto
source? Record without assuming.

**Step 2c — Runtime (28mm only, gated)**: At the `src1` constructor call
`0x3dfcc0`, capture the key argument and the first entry of the level
vector. At the `src2` executor entry `0x3ed2e0`, capture the output
descriptor dimensions and stride. Do these match a wide/tele relationship
(i.e., is `src1` larger than `src2`, or vice versa)?

**Accept condition for Step 2c**: Output descriptor dimensions from
`src2` at 28mm are consistent with a down-sampled or corrected single
camera source, and `src1` dimensions are consistent with a multi-scale
wide source.

**Reject condition**: Dimensions are equal, or the relationship does not
match the patent architecture. Record as `HYPOTHESIS_NOT_SUPPORTED`.

**On accept of all three steps**: Create
`docs/evidence/patent_us8913145b2_correspondence_28mm.md`. Record exact
dimension captures, static observations, and the specific correspondence
claims — scoped to 28mm only. Do not promote to four-zoom without
separate proof. Do not admit as `CLM-PREFUSION-002` closure.

**On partial accept**: Record what matched and what did not. Update
`BLOCKER_PATHS.md` if the partial result narrows the `src1`/`src2`
semantic search space.

---

## Explicit Exclusions

The following patent research content is **excluded from verification
scope** and must not influence the claim ledger:

- Pelican Imaging Corp. patents (different company, different system)
- US9723272B2 Magna International (vehicle surround-view, not L16)
- US20210264607A1 semantic segmentation (no corresponding surface found)
- All hypothetical codebase paths (`/stabilization/...`, `/stitch/...`,
  `/pipeline/...`, `/effects/...`) — these are fabricated and must not
  be treated as real paths
- The `src1` = wide / `src2` = tele mapping stated as fact in the
  research doc — this is a hypothesis, not an admitted finding
- The asymmetric luminance/chrominance weighting formulas from
  US8199222B2 — no corresponding surface has been located in `libcp`

---

## Source Priority Reminder

This document is subordinate to all canonical project docs.
On any conflict, the following order applies:

1. `CLAIM_LEDGER.md`
2. `PARITY_BLOCKERS.md`
3. `MERGE_CRITICAL_TRUTH.md`
4. `TRUTH.md`
5. This document

---

## Expected Outputs

| Task | Output file | Admission target |
|---|---|---|
| Task 1 (Ceres string) | `docs/evidence/static_libcp_ceres_string.md` | Static provenance fact only |
| Task 2a (src1 constructor) | append to existing `src1` evidence or new file | `CLM-PREFUSION-001` note only |
| Task 2b (src2 worker) | append to existing `src2` evidence or new file | `CLM-PREFUSION-001` note only |
| Task 2c (dimension capture) | `docs/evidence/patent_us8913145b2_correspondence_28mm.md` | `CLM-PREFUSION-001` note only, 28mm scoped |

No task output may be admitted as `CLM-PREFUSION-002` closure.
No task output may be generalized beyond its tested zoom scope.
