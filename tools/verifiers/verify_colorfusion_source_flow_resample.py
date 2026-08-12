#!/usr/bin/env python3
"""Verify the ColorFusion source flow resample is CLOSED (bit-exact).

Ground truth (captured):
  runs/colorfusion_source_planes/u1_28/source_vec4_f16_00.bin  (cam4 half-res
      vec4 f16 plane, 2079x1559) + flow_vec2_f32_00.bin (259x194 per-patch vec2)
  runs/colorfusion_f_runtime/u1_28_transform*/source_before_vec4_f32.bin  (the
      DC-aligned 16x16x vec4 source patch fed to the transform)

Closed formula (0/1024 words differ, this script):
  source_before[j,i,l] = f32( 981.0f * plane_f16[oy+j, ox+i, l] )
  where (ox,oy) = ( floor(px*8 + dx), floor(py*8 + dy) ),  (dx,dy)=flow[py,px],
  scale 981 = white(1023) - black(42).  Integer read; NO sub-pixel interpolation
  (the non-f16-representability of source_before is fully explained by *981).
"""
import struct, sys, pathlib, numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SP = ROOT / "runs/colorfusion_source_planes/u1_28"
FR = ROOT / "runs/colorfusion_f_runtime"

def bits(a): return a.astype(np.float32).view(np.uint32)

def main():
    plane = np.frombuffer((SP/"source_vec4_f16_00.bin").read_bytes(),
                          dtype="<f2").astype(np.float32).reshape(1559, 2079, 4)
    flow = np.frombuffer((SP/"flow_vec2_f32_00.bin").read_bytes(),
                         dtype="<f4").reshape(194, 259, 2)
    ok_all = True
    # The one textured patch whose (px,py) we solved from the flow field:
    for label, patchdir, px, py in [("u1_28_transform", "u1_28_transform", 7, 91)]:
        sb = np.frombuffer((FR/patchdir/"source_before_vec4_f32.bin").read_bytes(),
                           dtype="<f4").reshape(16, 16, 4)
        dx, dy = float(flow[py, px, 0]), float(flow[py, px, 1])
        ox = int(np.floor(px*8 + dx)); oy = int(np.floor(py*8 + dy))
        cand = (np.float32(981.0) * plane[oy:oy+16, ox:ox+16, :]).astype(np.float32)
        diff = int((bits(cand) != bits(sb)).sum())
        print(f"{label}: flow cell ({px},{py})=({dx:.4f},{dy:.4f}) -> origin "
              f"({ox},{oy}); 981*plane vs source_before: {diff}/1024 words differ")
        ok_all &= (diff == 0)
    print("RESULT", "PASS bit-exact" if ok_all else "FAIL")
    return 0 if ok_all else 1

if __name__ == "__main__":
    raise SystemExit(main())
