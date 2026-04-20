#!/usr/bin/env python3
"""
diag_ccm_bayer.py — CCM direction + bayer phase diagnostic
============================================================
Tests all combinations of CCM variant and bayer phase for cam6 (150mm LRI).
Saves JPEGs to /tmp/ named by variant. Prints channel means for each.

Usage:
    python3 diag_ccm_bayer.py /path/to/L16_00177.lri
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from phoenix_pipeline import parse_lri, load_raw_bayer, blc_awb_normalize, demosaic_ha, apply_tone_curve

LRI = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/L16_Raw/L16_00177.lri"
CAM = 6


def save_jpeg(arr_f32, path, quality=85):
    """Save float32 [0,1] RGB array as JPEG."""
    try:
        import cv2
        u8 = (arr_f32.clip(0, 1) * 255).astype(np.uint8)
        bgr = cv2.cvtColor(u8, cv2.COLOR_RGB2BGR)
        cv2.imwrite(path, bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
        print(f"  saved: {path}")
    except ImportError:
        from PIL import Image
        u8 = (arr_f32.clip(0, 1) * 255).astype(np.uint8)
        Image.fromarray(u8).save(path, quality=quality)
        print(f"  saved: {path}")


def channel_means(rgb):
    return f"R={rgb[:,:,0].mean()*255:.1f} G={rgb[:,:,1].mean()*255:.1f} B={rgb[:,:,2].mean()*255:.1f}"


print(f"Parsing {LRI} ...")
meta = parse_lri(LRI)

print(f"\nAWB gains: {meta['awb_gains']}")
cal = meta['factory_cals'].get(CAM)
if cal is None:
    print(f"ERROR: cam {CAM} not in factory_cals")
    print(f"  Available cameras: {sorted(meta['factory_cals'].keys())}")
    sys.exit(1)

print(f"Cam {CAM} K:\n{cal['K']}")
print(f"Cam {CAM} vignette_grid found: {cal['vignette_grid'] is not None}")
print(f"Cam {CAM} CCM list ({len(cal['ccm_list'])} entries):")
for i, entry in enumerate(cal['ccm_list']):
    print(f"  [{i}] mode={entry['mode']}")
    if entry.get('fwd_ccm') is not None:
        print(f"       fwd_ccm:\n{entry['fwd_ccm']}")
    if entry.get('ccm') is not None:
        print(f"       inv_ccm:\n{entry['ccm']}")

print(f"\nLoading raw bayer for cam {CAM} ...")
raw, lri_bayer_phase = load_raw_bayer(LRI, CAM)
print(f"  raw shape={raw.shape}, min={raw.min():.0f}, max={raw.max():.0f}, mean={raw.mean():.1f}")
print(f"  bayer_phase from LRI surface: {lri_bayer_phase}")

awb = meta['awb_gains']

# Collect CCM variants to test
ccm_variants = {'identity': np.eye(3)}

for i, entry in enumerate(cal['ccm_list']):
    mode = entry['mode']
    if entry.get('fwd_ccm') is not None:
        ccm_variants[f'fwd_mode{mode}'] = entry['fwd_ccm']
        ccm_variants[f'fwd_mode{mode}_T'] = entry['fwd_ccm'].T
        try:
            ccm_variants[f'inv_fwd_mode{mode}'] = np.linalg.inv(entry['fwd_ccm'])
        except np.linalg.LinAlgError:
            pass
    if entry.get('ccm') is not None:
        ccm_variants[f'inv_mode{mode}'] = entry['ccm']
        ccm_variants[f'inv_mode{mode}_T'] = entry['ccm'].T
        try:
            ccm_variants[f'fwd_from_inv_mode{mode}'] = np.linalg.inv(entry['ccm'])
        except np.linalg.LinAlgError:
            pass

# Test all 4 bayer phases × all CCM variants
bayer_phases = [(0,0), (1,0), (0,1), (1,1)]
bayer_names  = {(0,0):'RGGB', (1,0):'GRBG', (0,1):'GBRG', (1,1):'BGGR'}

# First: test all bayer phases with identity CCM to find best demosaic pattern
print("\n=== BAYER PHASE SWEEP (identity CCM, no vignette, no tone) ===")
best_phase = None
best_score = float('inf')

for phase in bayer_phases:
    bayer = blc_awb_normalize(raw, awb['R'], awb['Gr'], awb['Gb'], awb['B'], phase)
    rgb = demosaic_ha(bayer, phase)
    means = channel_means(rgb)
    # Score: penalize large G deviation from neutral and R/B imbalance
    r, g, b = rgb[:,:,0].mean(), rgb[:,:,1].mean(), rgb[:,:,2].mean()
    # Neutral scene: R≈G≈B. Measure imbalance.
    score = abs(r - g) + abs(b - g)
    flag = "  <-- best so far" if score < best_score else ""
    print(f"  {bayer_names[phase]}: {means}  score={score:.3f}{flag}")
    if score < best_score:
        best_score = score
        best_phase = phase

    out = f"/tmp/diag_cam{CAM}_{bayer_names[phase]}_identity.jpg"
    save_jpeg(rgb.clip(0, 1), out)

print(f"\nBest bayer phase (identity CCM): {bayer_names[best_phase]}")

# Second: with best bayer phase, test all CCM variants
print(f"\n=== CCM VARIANT SWEEP (bayer={bayer_names[best_phase]}) ===")
bayer = blc_awb_normalize(raw, awb['R'], awb['Gr'], awb['Gb'], awb['B'], best_phase)
rgb_base = demosaic_ha(bayer, best_phase)

for name, ccm in ccm_variants.items():
    h, w, _ = rgb_base.shape
    out_rgb = (rgb_base.reshape(-1, 3) @ ccm.T).reshape(h, w, 3).clip(0, 1).astype(np.float32)
    toned = apply_tone_curve(out_rgb)
    means = channel_means(toned)
    print(f"  {name}: {means}")
    outpath = f"/tmp/diag_cam{CAM}_{bayer_names[best_phase]}_{name}.jpg"
    save_jpeg(toned, outpath)

# Third: BGGR (default) × best CCM for comparison
print(f"\n=== DEFAULT BGGR × CCM VARIANTS ===")
bayer_bggr = blc_awb_normalize(raw, awb['R'], awb['Gr'], awb['Gb'], awb['B'], (1,1))
rgb_bggr = demosaic_ha(bayer_bggr, (1,1))
for name, ccm in list(ccm_variants.items())[:4]:  # limit to first 4 to avoid spam
    h, w, _ = rgb_bggr.shape
    out_rgb = (rgb_bggr.reshape(-1, 3) @ ccm.T).reshape(h, w, 3).clip(0, 1).astype(np.float32)
    toned = apply_tone_curve(out_rgb)
    means = channel_means(toned)
    print(f"  BGGR+{name}: {means}")

print("\nDone. Check /tmp/diag_cam*.jpg")
