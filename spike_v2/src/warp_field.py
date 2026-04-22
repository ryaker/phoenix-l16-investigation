"""
warp_field.py — Load WarpField runtime dumps and apply contributor-to-anchor
projection per TRUTH v2.1.4 §2.1 M2.1 + v2.1.5 §2.1 M2.3.

Dumps produced by `/tmp/l16_open_audit/aux_dump/` LLDB probes:
- reference/aux_<LRI>_<zoom>mm.bin  — 4160×3120 f32 aux buffer (52 MB)
- reference/warpfield_<LRI>_<zoom>mm.bin — 5×80 B raw WarpField array
- reference/*.json — decoded metadata

WarpField per-pixel math (TRUTH M2.1):
  sample = aux[dst_y * sy, dst_x * sx]
  out = sample·col2 + col3 + (dst_x·sample)·col0 + (dst_y·sample)·col1
  (src_u, src_v) = round(out[0..1] / out[2])

dst-space is SENSOR-NATIVE (4160×3120). Canvas output (10432×7824) is produced
by post-IRAMP cubic resampling (TRUTH M8 0x3ebb80). This is why col0[0]=col1[1]
≈ 2.5 = canvas/sensor ratio — the 2.5× is baked into the homography.

Clean-room note: this module LOADS runtime captures for spike validation ONLY.
Phoenix production must compute aux + warps from first principles (lens cal,
sensor geometry, camera extrinsics) — see TRUTH §4 OPEN-AUX-WRITER.
"""
import os
import struct
import json
from typing import List, Optional, Tuple
import numpy as np


def find_dumps(reference_dir: str, zoom_mm: int) -> Optional[Tuple[str, str]]:
    """Locate aux + warpfield bin files for a given zoom tier.

    Naming convention: aux_*_<zoom>mm.bin  and  warpfield_*_<zoom>mm.bin.
    Returns (aux_path, wf_path) if both found, else None.
    """
    aux = wf = None
    for name in os.listdir(reference_dir):
        if name.startswith(f'aux_') and name.endswith(f'_{zoom_mm}mm.bin'):
            aux = os.path.join(reference_dir, name)
        elif name.startswith(f'warpfield_') and name.endswith(f'_{zoom_mm}mm.bin'):
            wf = os.path.join(reference_dir, name)
    return (aux, wf) if (aux and wf) else None


def load_aux(bin_path: str, meta_path: Optional[str] = None) -> np.ndarray:
    """Load aux-image as (H, W) float32 array."""
    if meta_path is None:
        meta_path = bin_path.replace('.bin', '.json')
    with open(meta_path) as f:
        meta = json.load(f)
    H, W = meta['height'], meta['width']
    aux = np.fromfile(bin_path, dtype=np.float32, count=H * W).reshape(H, W)
    return aux


def load_warps(bin_path: str, meta_path: Optional[str] = None) -> List[dict]:
    """Load WarpField array as list of decoded dicts.

    Each entry: {col0, col1, col2, col3: (4,) f32 vec; sx, sy: f32; aux_ptr: hex str}
    """
    with open(bin_path, 'rb') as f:
        raw = f.read()
    assert len(raw) % 80 == 0, f"Expected multiple of 80 B, got {len(raw)}"
    warps = []
    for i in range(len(raw) // 80):
        b = raw[i * 80:(i + 1) * 80]
        warps.append({
            'i': i,
            'col0': np.array(struct.unpack('<4f', b[0x00:0x10]), dtype=np.float32),
            'col1': np.array(struct.unpack('<4f', b[0x10:0x20]), dtype=np.float32),
            'col2': np.array(struct.unpack('<4f', b[0x20:0x30]), dtype=np.float32),
            'col3': np.array(struct.unpack('<4f', b[0x30:0x40]), dtype=np.float32),
            'aux_ptr': f'0x{int.from_bytes(b[0x40:0x48], "little"):x}',
            'sx': struct.unpack('<f', b[0x48:0x4c])[0],
            'sy': struct.unpack('<f', b[0x4c:0x50])[0],
        })
    return warps


def apply_warp(contributor_rgb: np.ndarray,
               warp: dict,
               aux: np.ndarray) -> np.ndarray:
    """Vectorized WarpField application.

    Args:
        contributor_rgb: (H, W, 3) f32 contributor camera's post-ISP output
        warp: one entry from load_warps()
        aux:  (H, W) f32 aux buffer (shared across all warps)

    Returns:
        projected: (H, W, 3) f32 — contributor pixels reprojected into anchor
                   coord frame; pixels outside source clipped to edge.
    """
    H, W, _ = contributor_rgb.shape
    assert aux.shape == (H, W), f"aux {aux.shape} vs rgb {(H, W)}"

    col0, col1, col2, col3 = warp['col0'], warp['col1'], warp['col2'], warp['col3']
    sx, sy = np.float32(warp['sx']), np.float32(warp['sy'])

    # Build dst coord grids (sensor-native)
    dst_x = np.arange(W, dtype=np.float32)[None, :]   # (1, W)
    dst_y = np.arange(H, dtype=np.float32)[:, None]   # (H, 1)

    # aux lookup at (dst_x * sx, dst_y * sy) — with sx=sy=1.0 this is identity
    if sx == 1.0 and sy == 1.0:
        sample = aux  # (H, W)
    else:
        ax = np.clip((dst_x * sx).astype(np.int32), 0, W - 1)
        ay = np.clip((dst_y * sy).astype(np.int32), 0, H - 1)
        sample = aux[ay, ax]

    # Projective homography components (only first 3 slots of each col matter;
    # slot 3 is homogeneous/padding with col3[3]=1 per M2.1)
    dx_s = dst_x * sample  # (H, W)
    dy_s = dst_y * sample
    out_0 = sample * col2[0] + col3[0] + dx_s * col0[0] + dy_s * col1[0]
    out_1 = sample * col2[1] + col3[1] + dx_s * col0[1] + dy_s * col1[1]
    out_2 = sample * col2[2] + col3[2] + dx_s * col0[2] + dy_s * col1[2]

    # Perspective divide
    eps = np.float32(1e-6)
    out_2_safe = np.where(np.abs(out_2) < eps, np.sign(out_2) * eps + eps, out_2)
    src_u = np.round(out_0 / out_2_safe).astype(np.int32)
    src_v = np.round(out_1 / out_2_safe).astype(np.int32)

    # Clip to source bounds
    src_u = np.clip(src_u, 0, W - 1)
    src_v = np.clip(src_v, 0, H - 1)

    # Sample contributor
    projected = contributor_rgb[src_v, src_u]
    return projected.astype(np.float32)
