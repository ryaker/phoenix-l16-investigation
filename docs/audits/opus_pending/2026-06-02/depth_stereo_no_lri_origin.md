<!-- provenance: l16-investigator finder (LRI byte-parse + libcp disasm) + orchestrator RTTI/string re-extraction, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine; finder + orchestrator-verified). RESOLVES the "depth/stereo
LRI origin" blank with a decisive negative + a clean-room consequence. Binary `libcp.dylib`; LRIs 70mm
`L16_03434` + 28mm `L16_02130` (both Unit-1).

# Depth/stereo has NO LRI origin — it is RUNTIME stereo-matched across the cameras

## VERDICT (OBSERVED)
The `2080×1560` `StereoLayer<false>` index-5 depth descriptor (debug `depth_*.dp`, guided-upsampled by
`0x29ed90`) is **computed at render time by stereo matching across the multi-camera images**, NOT read from
the LRI. There is no stored depth map, disparity map, or depth config in the capture LRI.

## VERIFIED — libcp (orchestrator re-extracted RTTI + strings)
- **Runtime-only constructors (no proto/LRI arg):**
  `lt::DepthCache::DepthCache(Vec2<i>, vector<Vec2<i>>, shared_ptr<ImageCaches>, shared_ptr<StereoAsyncAPI>)`
  — inputs = output size, camera-grid positions, **ImageCaches** (runtime per-camera buffers), **StereoAsyncAPI**.
  `lt::StereoLayer<false>::StereoLayer(StereoParams)`; `lt::ReferenceImageCache(...,RawImageFactory,...,StereoAsyncAPI)`.
- **Runtime-stereo guard strings (exact VAs):** `0x6325fd` "no lower src cams are enabled. cannot compute
  depth"; `0x63535b` "Cannot init source image caches without a stereo object!"; `0x635543` "Cannot process
  undistortion without Stereo!"; `0x63298b` "Cannot upsample the first layer."; `0x6344fc` "Calling startStereo
  from non-renderer thread!". The depth-compute body `0x226c70` (xref `0x2271b7`) loops over enabled camera
  IDs building per-camera 3D points and throws if the set is empty.
- **The `lt::Stereo`/`StereoState`/`DepthEditorState` protos are EDITOR-STATE serialization, not capture
  data:** RTTI `N4ltpb6StereoE`; build paths `.../stereo/protobuf/stereo_state.pb.cc` and
  `.../libcp/protobuf/depth_editor_state.pb.cc` (the desktop DepthEditor brush/lasso edit state).

## VERIFIED — LRI (deterministic byte-parse; finder)
- `LightHeader.depth_config` (field 13) **ABSENT** in both LRIs (block-0 field nums lack 13).
- Whole-file scan for `Stereo`/`StereoState`/`DepthEditorState`/`disparity`/`depth`/`ltpb`/`DepthConfig` →
  **0 hits** (only coincidental 3-byte `.dp` matches inside raw sensor-plane bodies).

## REFUTED — the "DepthConfig blobs = depth" suspect (and a corroboration of lane-b2)
The earlier undistort probe's "DepthConfig <NNNN bytes>" in LRI Block-2/5/7 was a **parser mislabel**. Those
blocks are **per-camera FACTORY CALIBRATION** (16× camera-indexed 0..15, date-stamped `f7`={Y,M,D,h,m,s}):
- Block 4 (~28.8KB): `f3` ~1.9KB geometric/distortion calib per cam.
- Block 5 (~263KB): `f4` ~15KB per cam (14151B+896B = LSC/vignetting grids).
- Block 7 (~35KB): per-camera color cal.
This CORROBORATES [[lane-b2-lri-calibration-origins]] (Block 4 = lens-shading grid; Block 5 = vignetting;
Block 6 = color/CCM) — same calibration blocks, now also confirmed date-stamped + camera-indexed, and
confirmed NOT depth.

## CLEAN-ROOM CONSEQUENCE (important, new scope)
Phoenix **must reimplement multi-view stereo depth estimation** from the camera images — it CANNOT read depth
from the LRI (none exists). Inputs available to that reimplementation: (a) the raw per-camera sensor planes,
(b) the per-camera factory calibration (Blocks 4/5/7 + intrinsics Block 3) for rectification. This elevates
the still-undecoded **stereo cost math** (`0x2732f0`/`0x275630`, `StereoLayer<false>::runPass`) from
"nice-to-know" to a **required clean-room algorithm** — and it is currently UNKNOWN (bookmarked VAs, no math).

## Connection to the #1 merge blocker (SYNTHESIS / LEAD)
The runtime depth map is not a separate output — committed ledger `CLM-WARP-003` binds the
`UpsampleLayer+0x90` depth map → `record+0x40` consumed by the IRAMP pair-grid/warp transform. ⇒ depth's role
in bridge HDR is as the **warp/registration guide for the pre-fusion merge alignment**. So "does depth
contribute to bridge HDR?" (a prior blank) is likely YES — via the merge warp — even though the DepthCache/
DepthEditor GUI paths show no construction in bridge HDR (`CLM-DEPTH-001/002`). NEEDS_CODEX_VALIDATION.

## Residuals
- Exact stereo-matching algorithm + per-zoom source-camera-pair selection (only "enabled lower src cams" loop
  + anchor `image_reference_camera`=8@70mm/0@28mm observed) — UNKNOWN (the elevated #4 blank).
- Unit-2 not checked; a Light-app re-save with depth edits could embed editor state (not the capture path).
