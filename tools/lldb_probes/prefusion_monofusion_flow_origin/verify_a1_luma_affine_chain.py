#!/usr/bin/env python3
"""Bit-exact check of the A1 reference luma + reciprocal-exposure affine chain
against the captured demosaic-output oracle (unit1 28mm). Confirms the installed
AR1335 luma weights and S=R/Q affine, independent of the demosaic kernel.

  luma  = f32( f32(f32(r*wr + b*wb) + f32(g*wg + a*0)) * 981 )
  affine= min( f32(luma * S), 981 )

Run from the reference_operand capture dir. Requires a1_reference_source.f32x4le
(demosaic RGBA) and a1_reference_affine.f32le (oracle affine)."""
import numpy as np
S = np.float32(4.52963924407959)          # reference_scale (0x4090f2ce), = R/Q
wr,wg,wb = (np.float32(0.2155500054359436),
            np.float32(0.43230700492858887),
            np.float32(0.35214298963546753))
src = np.fromfile("a1_reference_source.f32x4le", dtype="<f4").reshape(-1,4)
aff = np.fromfile("a1_reference_affine.f32le", dtype="<f4")
r,g,b,a = src[:,0],src[:,1],src[:,2],src[:,3]
rb   = (r*wr + b*wb).astype(np.float32)
ga   = (g*wg).astype(np.float32)
luma = ((rb+ga).astype(np.float32) * np.float32(981.0)).astype(np.float32)
affine = np.minimum((luma*S).astype(np.float32), np.float32(981.0)).astype(np.float32)
eq = (affine.view("<u4") == aff.view("<u4"))
print(f"a1 luma+affine: {int(eq.sum())}/{eq.size} bit-exact, {int((~eq).sum())} mismatch")
assert eq.all(), "A1 luma/affine chain diverged"
