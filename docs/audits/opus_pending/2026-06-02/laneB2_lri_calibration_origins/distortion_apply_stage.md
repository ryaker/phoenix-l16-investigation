<!-- provenance: orchestrator-tasked static finder a16e837c, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, static disasm + RTTI/string xref). Kernel form OBSERVED;
pipeline-order = static call-graph LEAD (no runtime BP).

# Distortion APPLY stage: lt::LensUndistortCRA::operator() @ 0x261940 (per-camera, pre-merge, LUT-based)

## Where & how Block-3 distortion is applied
- **Kernel `0x261940` = `lt::LensUndistortCRA::operator()(int col,int row)->Vec2<float>`** (RTTI: `__func<
  lt::LensUndistortCRA,Vec2<float>(int,int)>` vtable `0x6679d0`, invoke-ptr `0x6679c0`→`0x261940`; typeinfo
  `N2lt16LensUndistortCRAE` `0x5da010`). Object layout: `+0x08/0c`=focal fx/fy, `+0x10`=**LUT base ptr**,
  `+0x28/2c`=principal point, `+0x30..0x50`=intrinsic/homography matrix.
- **Pure LUT-indexed RADIAL undistort** (NOT a runtime polynomial): affine map → homogeneous divide →
  subtract principal point → scale by focal → `r²=x²+y²` → `sqrtss` → `cvttss2si` → **clamp r to [0,0xFFF]
  (4095)** → **`movss (LUT+r*4)`** correction factor → multiply x,y by it → add principal point back. Exactly
  one sqrt, one LUT load, two muls — NO Horner `r(1+k1r²+k2r⁴+k3r⁶)`.
- The 5 Brown-Conrady coeffs `[k1,k2,0,0,k3]` are consumed at **CONFIG time to BUILD the LUT** (builders
  `0xea90` — `cmpq $0x5` requires ≥5 coeffs, loads k3, err "unsupported undistortion coefficients
  configuration!"; `0x145980` — builds/size-validates undistortion vector, err "Distortion and undistortion
  vectors are not the same size"). So poly↔LUT are complementary (poly builds LUT); reconciles laneB2
  `distortion_lut_full_decode.md`.

## Pipeline order (LEAD, static call-graph)
Owned by the per-camera **SourceImageCache** — ctor `lt::SourceImageCache::SourceImageCache(..., 
CapturedImage::Camera, LensUndistortCRA&&)` (string `0x608120`) moves the kernel in as a member; applied via
`lt::Internal::ImageWarpClamped<…ImageLensUndistort<…,LensUndistortCRA>>` (warp `__func` vptr installed at
`0x262164`, right after the kernel). Install sites in the per-camera source-producer region `0x3ec903/
0x3ec924` (adjacent to the merge feeders). ⇒ undistort runs **per-camera, on the source-image producer side,
UPSTREAM of the IRAMP merge** — consistent with the runtime finding that the merge projection `0x3e42e0`
radial is identity (undistort already done here).

## Clean-room implication
Phoenix undistorts **per camera, before merge**, using a radius→correction LUT built from the LRI Block-3
distortion coeffs (or the f3.3.2.5 LUT directly), clamp-indexed over a ~4096-entry radius domain. Standard
reimplementable stage (Rule #0: LUT derived from LRI coeffs / published radial model).

## Open
- Whether the runtime LUT at `this+0x10` is the exact f3.3.2.5 101-entry table upsampled to 4096, or
  re-derived from the 5 coeffs (needs a runtime read of the LUT vs the parsed LRI LUT).
- The poly→LUT build math in `0xea90`/`0x145980` (not decoded in detail).
- Runtime cross-verify of the per-camera→merge ordering (BP `0x261940` + stack walk).
