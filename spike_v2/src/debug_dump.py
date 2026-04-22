"""
debug_dump.py — Additive per-cam per-stage instrumentation for Phoenix Spike v2.

Purpose: run the existing ISP stages on each fired cam of an LRI and dump
intermediate arrays (TIFF 16-bit + PNG 8-bit preview) + textual stats to a
single stats file. Does NOT modify any ISP logic. Re-uses per_cam_isp stage
functions directly (does not re-run run_per_cam_isp, which fuses stages).

Outputs, per cam_id cid:
  reference/<cid>_<cam_name>_01_raw.tiff          (uint16, HxW)
  reference/<cid>_<cam_name>_01_raw_preview.png   (uint8, HxW stretched)
  reference/<cid>_<cam_name>_02_undistort.tiff    (uint16)
  reference/<cid>_<cam_name>_03_blc.tiff          (float32 preview uint16 scaled)
  reference/<cid>_<cam_name>_03_blc_preview.png
  reference/<cid>_<cam_name>_04_awb.tiff
  reference/<cid>_<cam_name>_04_awb_preview.png
  reference/<cid>_<cam_name>_05_demosaic.tiff     (uint16 RGB)
  reference/<cid>_<cam_name>_05_demosaic_preview.png
  reference/<cid>_<cam_name>_06_ccm_direct.tiff       (CCM interpretation i)
  reference/<cid>_<cam_name>_06_ccm_rownorm.tiff      (ii)
  reference/<cid>_<cam_name>_06_ccm_inverted.tiff     (iii)
  reference/<cid>_<cam_name>_06_ccm_direct_preview.png
  reference/<cid>_<cam_name>_06_ccm_rownorm_preview.png
  reference/<cid>_<cam_name>_06_ccm_inverted_preview.png
  reference/<cid>_<cam_name>_07_vignette.tiff    (uint16 RGB, final ISP pre-merge)
  reference/<cid>_<cam_name>_07_vignette_preview.png

And a summary text file at logs/verification_stats.txt with per-stage stats
tables, AWB reciprocal verification, CCM neutrality experiment results, and
per-cam final RGB means table.
"""

import os
import sys
import numpy as np
import tifffile
from PIL import Image

# Make src importable when run as script
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

from lri_parser import parse_lri, extract_raw_cam  # noqa: E402
from per_cam_isp import (  # noqa: E402
    blc, awb_bayer, demosaic, vignetting_apply, select_ccm_for_cct,
    lens_undistort_approx, DEFAULT_CCT,
)
from utils import BAYER_LAYOUTS, bayer_pattern_name, apply_ccm_chromaticity  # noqa: E402


CAM_NAMES = {
    0: 'A1', 1: 'A2', 2: 'A3', 3: 'A4', 4: 'A5',
    5: 'B1', 6: 'B2', 7: 'B3', 8: 'B4', 9: 'B5',
    10: 'C1', 11: 'C2', 12: 'C3', 13: 'C4', 14: 'C5', 15: 'C6',
}


def _stretch_u8(arr_2d: np.ndarray, pct_lo=1.0, pct_hi=99.0) -> np.ndarray:
    """Auto-contrast stretch for preview."""
    a = np.asarray(arr_2d, dtype=np.float32)
    if a.size == 0:
        return a.astype(np.uint8)
    lo = np.percentile(a, pct_lo)
    hi = np.percentile(a, pct_hi)
    if hi - lo < 1e-6:
        return np.zeros_like(a, dtype=np.uint8)
    out = (a - lo) / (hi - lo)
    out = np.clip(out, 0.0, 1.0)
    return (out * 255.0 + 0.5).astype(np.uint8)


def _save_preview_png(path: str, arr: np.ndarray, pct_lo=1.0, pct_hi=99.0):
    """Save preview PNG. Handles HxW (grayscale) and HxWx3 (RGB)."""
    if arr.ndim == 2:
        u8 = _stretch_u8(arr, pct_lo, pct_hi)
        Image.fromarray(u8, mode='L').save(path)
    elif arr.ndim == 3 and arr.shape[2] == 3:
        # Per-channel stretch? Use joint percentiles to preserve color.
        a = np.asarray(arr, dtype=np.float32)
        lo = np.percentile(a, pct_lo)
        hi = np.percentile(a, pct_hi)
        if hi - lo < 1e-6:
            u8 = np.zeros_like(a, dtype=np.uint8)
        else:
            out = np.clip((a - lo) / (hi - lo), 0.0, 1.0)
            u8 = (out * 255.0 + 0.5).astype(np.uint8)
        Image.fromarray(u8, mode='RGB').save(path)


def _float_to_u16(arr: np.ndarray, max_val=None) -> np.ndarray:
    """Scale a float array to uint16 for TIFF output. Uses max_val or array max."""
    a = np.asarray(arr, dtype=np.float32)
    if max_val is None:
        max_val = max(1e-6, float(a.max()))
    scaled = np.clip(a / max_val, 0.0, 1.0)
    return (scaled * 65535.0 + 0.5).astype(np.uint16)


def _bayer_channel_means(bayer_u16_or_f: np.ndarray, pattern: int):
    """Return (R_mean, G1_mean, G2_mean, B_mean) per Bayer phase layout."""
    tl, tr, bl, br = BAYER_LAYOUTS[pattern & 3]
    tiles = {
        tl: bayer_u16_or_f[0::2, 0::2],
        tr: bayer_u16_or_f[0::2, 1::2],
        bl: bayer_u16_or_f[1::2, 0::2],
        br: bayer_u16_or_f[1::2, 1::2],
    }
    # Collect G1 and G2 separately based on position (TL/BR vs TR/BL)
    g_vals = []
    r_mean = None
    b_mean = None
    for pos, ch in [((tl, (0, 0)), tl), ((tr, (0, 1)), tr), ((bl, (1, 0)), bl), ((br, (1, 1)), br)]:
        pass

    # Simpler: iterate positions
    r_pixels = []
    g1_pixels = None
    g2_pixels = None
    b_pixels = []
    pos_to_tile = {
        (0, 0): (tl, bayer_u16_or_f[0::2, 0::2]),
        (0, 1): (tr, bayer_u16_or_f[0::2, 1::2]),
        (1, 0): (bl, bayer_u16_or_f[1::2, 0::2]),
        (1, 1): (br, bayer_u16_or_f[1::2, 1::2]),
    }
    gs = []
    r_tile = None
    b_tile = None
    for pos, (ch, tile) in pos_to_tile.items():
        if ch == 'R':
            r_tile = tile
        elif ch == 'B':
            b_tile = tile
        else:
            gs.append(tile)
    r_m = float(np.mean(r_tile)) if r_tile is not None else float('nan')
    b_m = float(np.mean(b_tile)) if b_tile is not None else float('nan')
    g1_m = float(np.mean(gs[0])) if len(gs) >= 1 else float('nan')
    g2_m = float(np.mean(gs[1])) if len(gs) >= 2 else float('nan')
    return r_m, g1_m, g2_m, b_m


def run_debug_dumps(lri_path: str, ref_dir: str, stats_path: str,
                    cct: float = DEFAULT_CCT):
    os.makedirs(ref_dir, exist_ok=True)
    os.makedirs(os.path.dirname(stats_path) or '.', exist_ok=True)

    lh, cal, blocks, cam_to_block, fh = parse_lri(lri_path)

    lines = []

    def emit(s=''):
        lines.append(s)
        print(s, file=sys.stderr)

    try:
        emit(f"=== Phoenix Spike v2 debug_dump: {lri_path} ===")
        emit(f"zoom_val = {lh.zoom_val}")
        emit(f"fired cams = {sorted(c.cam_id for c in lh.cams)}")
        emit(f"AWB gains (per-cam, from Block 8): {cal.awb_gains}")
        emit(f"CCM cams parsed: {sorted(cal.ccm_by_cam.keys())}")
        emit(f"Vignetting cams parsed: {sorted(cal.vignetting.keys())}")
        for w in cal.warnings:
            emit(f"WARN: {w}")
        emit()

        # --- AWB reciprocal verification (Check B) ---
        emit("=== B) AWB reciprocal verification ===")
        emit("L16_00007 stored AWB gains (from parser, per-cam):")
        for cid in sorted(cal.awb_gains.keys()):
            R_g, B_g = cal.awb_gains[cid]
            emit(f"  cam {cid:2d} ({CAM_NAMES.get(cid,'?'):>2s}): "
                 f"stored R_gain={R_g:.4f}  stored B_gain={B_g:.4f}  "
                 f"1/R={1.0/R_g:.4f}  1/B={1.0/B_g:.4f}")
        emit("TRUTH §2.3 C1 + C2 claim runtime AWB = 1/stored_gain (reciprocal).")
        emit("For L16_02130 TRUTH cites runtime = (0.5821, 1, 0.6294, 0.3630).")
        emit("For L16_00007 (this LRI) runtime would be R=1/R_gain B=1/B_gain; "
             "parent will cross-check.")
        emit()

        # --- Per-cam per-stage dumps (Checks A, C, D, E) ---
        emit("=== A/D/E) Per-cam per-stage dumps ===")
        header = (f"{'cid':>3} {'name':>4} {'pattern':>6}  "
                  f"{'raw_H':>5} {'raw_W':>5}  "
                  f"{'raw_min':>7} {'raw_max':>7} {'raw_mean':>8} {'raw_med':>7}  "
                  f"{'byR':>7} {'byG1':>7} {'byG2':>7} {'byB':>7}")
        emit(header)

        # Collect post-vignette final RGB means for summary table
        final_means = []   # list of tuples
        ccm_experiment_rows = []   # for section C

        for cam in sorted(lh.cams, key=lambda c: c.cam_id):
            cid = cam.cam_id
            cname = CAM_NAMES.get(cid, f'?{cid}')
            stem = f"{cid:02d}_{cname}"
            pat_name = bayer_pattern_name(cam.bayer_pattern)

            try:
                raw = extract_raw_cam(fh, cam_to_block[cid], cam)
            except Exception as e:
                emit(f"cam {cid} {cname}: EXTRACT FAILED: {e}")
                continue

            # Stage 01: RAW
            raw_path_tiff = os.path.join(ref_dir, f"{stem}_01_raw.tiff")
            raw_path_png = os.path.join(ref_dir, f"{stem}_01_raw_preview.png")
            tifffile.imwrite(raw_path_tiff, raw.astype(np.uint16),
                             compression='lzw')
            _save_preview_png(raw_path_png, raw)
            raw_min = float(raw.min())
            raw_max = float(raw.max())
            raw_mean = float(raw.mean())
            raw_med = float(np.median(raw))
            byR, byG1, byG2, byB = _bayer_channel_means(raw, cam.bayer_pattern)
            emit(f"{cid:>3d} {cname:>4s} {pat_name:>6s}  "
                 f"{raw.shape[0]:>5d} {raw.shape[1]:>5d}  "
                 f"{raw_min:>7.1f} {raw_max:>7.1f} {raw_mean:>8.2f} {raw_med:>7.1f}  "
                 f"{byR:>7.2f} {byG1:>7.2f} {byG2:>7.2f} {byB:>7.2f}")

            # Stage 02: LensUndistort (approx identity)
            undist = lens_undistort_approx(raw)
            tifffile.imwrite(os.path.join(ref_dir, f"{stem}_02_undistort.tiff"),
                             undist.astype(np.uint16), compression='lzw')

            # Stage 03: BLC
            linear = blc(undist)
            blc_u16 = _float_to_u16(linear, max_val=1.1)
            tifffile.imwrite(os.path.join(ref_dir, f"{stem}_03_blc.tiff"),
                             blc_u16, compression='lzw')
            _save_preview_png(os.path.join(ref_dir, f"{stem}_03_blc_preview.png"),
                              linear)

            # Stage 04: AWB (per-Bayer multiply)
            R_gain, B_gain = cal.awb_gains.get(cid, (1.65, 1.80))
            awb_out = awb_bayer(linear, cam.bayer_pattern, R_gain, B_gain)
            awb_u16 = _float_to_u16(awb_out, max_val=1.1)
            tifffile.imwrite(os.path.join(ref_dir, f"{stem}_04_awb.tiff"),
                             awb_u16, compression='lzw')
            _save_preview_png(os.path.join(ref_dir, f"{stem}_04_awb_preview.png"),
                              awb_out)
            aw_r, aw_g1, aw_g2, aw_b = _bayer_channel_means(awb_out, cam.bayer_pattern)

            # Stage 05: Demosaic
            rgb = demosaic(awb_out, cam.bayer_pattern)
            rgb_u16 = _float_to_u16(rgb, max_val=1.1)
            tifffile.imwrite(os.path.join(ref_dir, f"{stem}_05_demosaic.tiff"),
                             rgb_u16, compression='lzw')
            _save_preview_png(os.path.join(ref_dir, f"{stem}_05_demosaic_preview.png"),
                              rgb)
            dm_r = float(rgb[..., 0].mean())
            dm_g = float(rgb[..., 1].mean())
            dm_b = float(rgb[..., 2].mean())

            # Stage 06: CCM — three interpretations
            ccm_illums = cal.ccm_by_cam.get(cid)
            M = select_ccm_for_cct(ccm_illums, cct) if ccm_illums else None

            M_direct = M
            M_rownorm = None
            M_inv = None
            if M is not None:
                rs = M.sum(axis=1, keepdims=True)
                rs_safe = np.where(np.abs(rs) < 1e-4, 1.0, rs)
                M_rownorm = (M / rs_safe).astype(np.float32)
                try:
                    M_inv = np.linalg.inv(M).astype(np.float32)
                except np.linalg.LinAlgError:
                    M_inv = None

            def _apply_direct(img, Mx):
                # TRUTH C3: out = M @ (R/G, 1, B/G); green forced to 1; then
                # rescale so green stays pixel-native: final = (o0*G, G, o2*G).
                G = img[..., 1]
                Gs = np.where(np.abs(G) < 1e-6, 1e-6, G)
                chrom = np.stack([img[..., 0] / Gs,
                                  np.ones_like(G),
                                  img[..., 2] / Gs], axis=-1)
                o = np.einsum('ij,...j->...i', Mx, chrom)
                # Rescale: green back to G, scale R and B by G
                return np.stack([o[..., 0] * G, G, o[..., 2] * G], axis=-1).astype(np.float32)

            ccm_row = {'cid': cid, 'cname': cname,
                       'M': M,
                       'row_sums': None,
                       'neutral_direct': None,
                       'neutral_rownorm': None,
                       'neutral_inv': None}
            if M is not None:
                ccm_row['row_sums'] = tuple(float(x) for x in M.sum(axis=1).tolist())
                # Neutral gray probe (1,1,1)
                neutral = np.array([[[1.0, 1.0, 1.0]]], dtype=np.float32)
                nd = _apply_direct(neutral, M_direct)[0, 0]
                ccm_row['neutral_direct'] = tuple(float(x) for x in nd.tolist())
                if M_rownorm is not None:
                    nn = _apply_direct(neutral, M_rownorm)[0, 0]
                    ccm_row['neutral_rownorm'] = tuple(float(x) for x in nn.tolist())
                if M_inv is not None:
                    ni = _apply_direct(neutral, M_inv)[0, 0]
                    ccm_row['neutral_inv'] = tuple(float(x) for x in ni.tolist())

                # Dump three CCM interpretations as full images
                for tag, Mx in [('direct', M_direct),
                                ('rownorm', M_rownorm),
                                ('inverted', M_inv)]:
                    if Mx is None:
                        continue
                    out = _apply_direct(rgb, Mx)
                    tifffile.imwrite(
                        os.path.join(ref_dir, f"{stem}_06_ccm_{tag}.tiff"),
                        _float_to_u16(out, max_val=1.2),
                        compression='lzw')
                    _save_preview_png(
                        os.path.join(ref_dir, f"{stem}_06_ccm_{tag}_preview.png"),
                        out)

            ccm_experiment_rows.append(ccm_row)

            # Stage 07: Post-vignette (apply on post-demosaic rgb)
            if cid in cal.vignetting:
                vig_rgb = vignetting_apply(rgb, cal.vignetting[cid])
            else:
                vig_rgb = rgb
            vig_u16 = _float_to_u16(vig_rgb, max_val=1.5)
            tifffile.imwrite(os.path.join(ref_dir, f"{stem}_07_vignette.tiff"),
                             vig_u16, compression='lzw')
            _save_preview_png(os.path.join(ref_dir, f"{stem}_07_vignette_preview.png"),
                              vig_rgb)

            fin_r = float(vig_rgb[..., 0].mean())
            fin_g = float(vig_rgb[..., 1].mean())
            fin_b = float(vig_rgb[..., 2].mean())
            final_means.append({
                'cid': cid, 'cname': cname,
                'awb_r': aw_r, 'awb_g1': aw_g1, 'awb_g2': aw_g2, 'awb_b': aw_b,
                'demosaic_r': dm_r, 'demosaic_g': dm_g, 'demosaic_b': dm_b,
                'final_r': fin_r, 'final_g': fin_g, 'final_b': fin_b,
            })

        emit()
        # --- AWB per-cam post-AWB channel mean check ---
        emit("=== Post-AWB Bayer channel means (should show R and B scaled, G unchanged) ===")
        emit(f"{'cid':>3} {'name':>4}  {'awb_R':>9} {'awb_G1':>9} {'awb_G2':>9} {'awb_B':>9}")
        for m in final_means:
            emit(f"{m['cid']:>3d} {m['cname']:>4s}  "
                 f"{m['awb_r']:>9.4f} {m['awb_g1']:>9.4f} {m['awb_g2']:>9.4f} {m['awb_b']:>9.4f}")
        emit()

        # --- Per-cam post-demosaic means ---
        emit("=== Post-demosaic RGB means ===")
        emit(f"{'cid':>3} {'name':>4}  {'dm_R':>9} {'dm_G':>9} {'dm_B':>9} {'R/G':>6} {'B/G':>6}")
        for m in final_means:
            rg = m['demosaic_r'] / m['demosaic_g'] if m['demosaic_g'] > 1e-6 else float('nan')
            bg = m['demosaic_b'] / m['demosaic_g'] if m['demosaic_g'] > 1e-6 else float('nan')
            emit(f"{m['cid']:>3d} {m['cname']:>4s}  "
                 f"{m['demosaic_r']:>9.4f} {m['demosaic_g']:>9.4f} {m['demosaic_b']:>9.4f} "
                 f"{rg:>6.3f} {bg:>6.3f}")
        emit()

        # --- Per-cam final (post-vignette) means ---
        emit("=== D) Per-cam post-vignette FINAL RGB means (pre-merge) ===")
        emit(f"{'cid':>3} {'name':>4}  {'fin_R':>9} {'fin_G':>9} {'fin_B':>9} {'R/G':>6} {'B/G':>6}")
        for m in final_means:
            rg = m['final_r'] / m['final_g'] if m['final_g'] > 1e-6 else float('nan')
            bg = m['final_b'] / m['final_g'] if m['final_g'] > 1e-6 else float('nan')
            emit(f"{m['cid']:>3d} {m['cname']:>4s}  "
                 f"{m['final_r']:>9.4f} {m['final_g']:>9.4f} {m['final_b']:>9.4f} "
                 f"{rg:>6.3f} {bg:>6.3f}")
        emit()

        # --- CCM experiment: neutral (1,1,1) in, three interpretations out ---
        emit("=== C) CCM neutrality experiment (neutral input (1,1,1) -> output) ===")
        emit("Interpretation (i) Direct per TRUTH C3: out = M @ (R/G, 1, B/G)")
        emit("Interpretation (ii) Row-normalized (spike's current default)")
        emit("Interpretation (iii) Inverted: out = inv(M) @ (R/G, 1, B/G)")
        emit(f"{'cid':>3} {'name':>4}  {'row_sums':<32}  "
             f"{'direct_RGB':<30} {'rownorm_RGB':<30} {'inv_RGB':<30}")
        for row in ccm_experiment_rows:
            rs = row['row_sums']
            rs_s = (f"({rs[0]:+.3f},{rs[1]:+.3f},{rs[2]:+.3f})"
                    if rs is not None else 'None')
            def _fmt(t):
                if t is None:
                    return 'None'
                return f"({t[0]:+.3f},{t[1]:+.3f},{t[2]:+.3f})"
            emit(f"{row['cid']:>3d} {row['cname']:>4s}  {rs_s:<32}  "
                 f"{_fmt(row['neutral_direct']):<30} "
                 f"{_fmt(row['neutral_rownorm']):<30} "
                 f"{_fmt(row['neutral_inv']):<30}")
        emit()

        # --- First stored CCM matrix dump for cam 0 (primary anchor) ---
        emit("=== Selected CCM matrices for first 3 cams (at CCT=%.0fK) ===" % cct)
        for row in ccm_experiment_rows[:3]:
            if row['M'] is None:
                emit(f"cam {row['cid']} ({row['cname']}): no CCM")
                continue
            emit(f"cam {row['cid']} ({row['cname']}) M=")
            for r in row['M']:
                emit(f"  [{r[0]:+.5f}, {r[1]:+.5f}, {r[2]:+.5f}]")
        emit()

        # Write stats file
        with open(stats_path, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        emit(f"[debug_dump] wrote stats -> {stats_path}")

    finally:
        fh.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 debug_dump.py <lri_path> [ref_dir] [stats_path]",
              file=sys.stderr)
        sys.exit(1)
    lri = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 else \
        os.path.join(os.path.dirname(_THIS_DIR), 'reference')
    stats = sys.argv[3] if len(sys.argv) > 3 else \
        os.path.join(os.path.dirname(_THIS_DIR), 'logs', 'verification_stats.txt')
    run_debug_dumps(lri, ref, stats)
