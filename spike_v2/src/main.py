"""
main.py — Phoenix Spike v2 orchestrator.

Usage: python3 main.py <lri_path> <output.tiff>

Orchestrates:
  1. Parse LRI (lri_parser)
  2. Per-camera ISP (per_cam_isp) for all fired cams in parallel
  3. Composite anchor pre-fusion (composite_anchor)
  4. IRAMP N→1 merge (iramp_merge)
  5. Post-IRAMP resample + tone curve (post_merge)
  6. Write TIFF (PIL)

Zoom-tier dispatch per TRUTH §2.1 M4:
  28mm / 35mm: anchor = A1..A5 (composite), contributors = B1..B5
               dispatcher passes cam_ids [0, 5, 6, 7, 8, 9]
  70mm / 150mm: anchor = B1..B5 (composite), contributors = C1..C5
                dispatcher passes cam_ids [8, 10, 11, 12, 13, 14]
"""

import sys
import time
import traceback

import numpy as np
from PIL import Image

from lri_parser import parse_lri, extract_raw_cam
from per_cam_isp import run_per_cam_isp, DEFAULT_CCT
from composite_anchor import build_composite_anchor
from iramp_merge import merge_iramp, FOV_RATIO_28MM_B, FOV_RATIO_70MM_C
from post_merge import post_merge_pipeline, OUT_W, OUT_H
from warp_field import find_dumps, load_aux, load_warps


# Zoom-tier dispatch: (anchor_ids, contributor_ids, fov_ratio)
TIER_WIDE = ([0, 1, 2, 3, 4], [5, 6, 7, 8, 9], FOV_RATIO_28MM_B)      # 28/35mm
TIER_TELE = ([5, 6, 7, 8, 9], [10, 11, 12, 13, 14], FOV_RATIO_70MM_C) # 70/150mm


def zoom_tier(zoom_val: int):
    """Return (anchor_ids, contrib_ids, fov_ratio, anchor_primary_id)."""
    if zoom_val < 70:
        ids = TIER_WIDE
        anchor_primary = 0   # A1 per TRUTH M3
    else:
        ids = TIER_TELE
        anchor_primary = 8   # B4 per TRUTH M3
    return ids[0], ids[1], ids[2], anchor_primary


def run(lri_path: str, output_tiff: str):
    t0 = time.time()
    print(f"[main] Phoenix Spike v2 rendering {lri_path}", file=sys.stderr)
    print(f"[main] Output: {output_tiff} (expected {OUT_W}×{OUT_H})",
          file=sys.stderr)

    # Stage 1: Parse LRI
    print("[main] Stage 1: LRI parse", file=sys.stderr)
    lh, cal, blocks, cam_to_block, fh = parse_lri(lri_path)
    try:
        zoom = lh.zoom_val
        anchor_ids, contrib_ids, fov_ratio, anchor_primary = zoom_tier(zoom)
        print(f"[main] zoom_val={zoom} tier={'WIDE' if zoom<70 else 'TELE'} "
              f"anchor_ids={anchor_ids} contrib_ids={contrib_ids}",
              file=sys.stderr)

        # Stage 2: Per-cam ISP for all fired cams (anchors + contributors)
        print("[main] Stage 2: Per-cam ISP", file=sys.stderr)
        cam_by_id = {c.cam_id: c for c in lh.cams}
        fired_ids = sorted(cam_by_id.keys())
        isp_outputs = {}   # cam_id -> (rgb, ccm)
        for cid in fired_ids:
            cam = cam_by_id[cid]
            print(f"  [isp] cam {cid} ({cam.bytes_per_row} bpr, "
                  f"bayer_pattern={cam.bayer_pattern})", file=sys.stderr)
            raw = extract_raw_cam(fh, cam_to_block[cid], cam)
            rgb, ccm = run_per_cam_isp(raw, cam, cal, DEFAULT_CCT)
            isp_outputs[cid] = (rgb, ccm)
            print(f"    output: {rgb.shape} min={rgb.min():.3f} "
                  f"max={rgb.max():.3f} mean={rgb.mean():.3f} "
                  f"ccm={'yes' if ccm is not None else 'none'}",
                  file=sys.stderr)

        # Stage 3: Composite anchor (A1..A5 or B1..B5)
        #
        # Spike v2.0 known limit: the composite-anchor 4-way weighted SIMD
        # blend kernel (libcp+0x2b3410 per TRUTH M14.1) requires per-cam
        # projection warps to register A1..A5 (each pointing at slightly
        # different scene angles) into a common coordinate frame before the
        # 16-entry LUT weighted blend. WarpField decode (TRUTH M2, 80 B
        # struct) is incomplete. Averaging unregistered A-cam outputs produces
        # disparity ghosts.
        #
        # For the SMOKE TEST we use the primary anchor camera only
        # (A1/cam_id 0 at 28mm; B4/cam_id 8 at 70mm). This validates the
        # per-cam ISP, CCM application, and tone curve without compounding
        # errors from missing registration. Composite pre-fusion is flagged
        # as a spike limitation in the final report.
        print("[main] Stage 3: Composite anchor pre-fusion", file=sys.stderr)
        SPIKE_USE_ANCHOR_PRIMARY_ONLY = True
        if SPIKE_USE_ANCHOR_PRIMARY_ONLY:
            primary_rgb = isp_outputs[anchor_primary][0]
            src1 = primary_rgb.copy()
            src2 = primary_rgb.copy()
            print(f"  [anchor] SPIKE: using primary anchor only "
                  f"(cam {anchor_primary}) — composite pre-fusion deferred",
                  file=sys.stderr)
        else:
            anchor_rgbs = []
            for aid in anchor_ids:
                if aid in isp_outputs:
                    anchor_rgbs.append(isp_outputs[aid][0])
            if not anchor_rgbs:
                raise RuntimeError("No anchor-group cams fired; cannot build composite")
            print(f"  [anchor] using {len(anchor_rgbs)}/{len(anchor_ids)} "
                  f"anchor-group cams", file=sys.stderr)
            src1, src2 = build_composite_anchor(anchor_rgbs)
        print(f"  [anchor] src1 shape={src1.shape} min={src1.min():.3f} "
              f"max={src1.max():.3f} mean={src1.mean():.3f}",
              file=sys.stderr)

        # Anchor CCM: use anchor_primary's CCM (TRUTH M3: single anchor cam)
        anchor_ccm = None
        if anchor_primary in isp_outputs:
            anchor_ccm = isp_outputs[anchor_primary][1]
        # Fallback to any anchor-group cam with CCM
        if anchor_ccm is None:
            for aid in anchor_ids:
                if aid in isp_outputs and isp_outputs[aid][1] is not None:
                    anchor_ccm = isp_outputs[aid][1]
                    break
        print(f"  [anchor] anchor_ccm={'yes' if anchor_ccm is not None else 'NONE'}",
              file=sys.stderr)

        # Stage 4: IRAMP merge
        print("[main] Stage 4: IRAMP merge", file=sys.stderr)
        contrib_rgbs = []
        contrib_ccms = []
        for cid in contrib_ids:
            if cid in isp_outputs:
                rgb, ccm = isp_outputs[cid]
                contrib_rgbs.append(rgb)
                contrib_ccms.append(ccm)
        print(f"  [iramp] using {len(contrib_rgbs)}/{len(contrib_ids)} "
              f"contributor cams", file=sys.stderr)

        # Load runtime aux + WarpField dumps if present (per-zoom-tier);
        # enables vectorized contributor merge. Spec-bound: the dumps are
        # spike reference captures from libcp at render time; Phoenix
        # production must COMPUTE these from first principles (see TRUTH
        # §4 OPEN-AUX-WRITER).
        import os as _os
        ref_dir = _os.path.join(_os.path.dirname(_os.path.dirname(
            _os.path.abspath(__file__))), 'reference')
        aux = warps = None
        dumps = find_dumps(ref_dir, zoom) if _os.path.isdir(ref_dir) else None
        if dumps:
            aux_path, wf_path = dumps
            aux = load_aux(aux_path)
            warps = load_warps(wf_path)
            print(f"  [iramp] loaded aux {aux.shape} + {len(warps)} warps "
                  f"from {ref_dir}", file=sys.stderr)
            merge_on = True
        else:
            print(f"  [iramp] no aux/warpfield dumps for {zoom}mm in {ref_dir} "
                  f"— contributor merge OFF (anchor-only output)",
                  file=sys.stderr)
            merge_on = False
        merged = merge_iramp(src1, contrib_rgbs, contrib_ccms,
                             anchor_ccm, fov_ratio,
                             include_contributors=merge_on,
                             aux=aux, warps=warps)
        print(f"  [iramp] merged shape={merged.shape} min={merged.min():.3f} "
              f"max={merged.max():.3f} mean={merged.mean():.3f}",
              file=sys.stderr)

        # Stage 5: Post-IRAMP resample + tone curve
        print("[main] Stage 5: Post-IRAMP (resample + tone)", file=sys.stderr)
        out_u16 = post_merge_pipeline(merged)
        print(f"  [post] output shape={out_u16.shape} dtype={out_u16.dtype}",
              file=sys.stderr)

        # Stage 6: Write TIFF — PIL's fromarray doesn't directly support
        # uint16 RGB; use tifffile if available, else fall back to 8-bit RGB.
        print("[main] Stage 6: Write TIFF", file=sys.stderr)
        try:
            import tifffile
            tifffile.imwrite(output_tiff, out_u16, compression='lzw', photometric='rgb')
        except ImportError:
            # Fall back to 8-bit RGB (right-shift by 8)
            out_u8 = (out_u16 >> 8).astype(np.uint8)
            im = Image.fromarray(out_u8, mode='RGB')
            im.save(output_tiff, format='TIFF', compression='tiff_lzw')
        import os
        size_mb = os.path.getsize(output_tiff) / 1024 / 1024
        print(f"[main] Wrote {output_tiff} ({size_mb:.1f} MB) "
              f"in {time.time()-t0:.1f}s", file=sys.stderr)

    finally:
        fh.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 main.py <lri_path> <output.tiff>", file=sys.stderr)
        sys.exit(1)
    try:
        run(sys.argv[1], sys.argv[2])
    except Exception:
        traceback.print_exc()
        sys.exit(2)
