# Lane A2 -- NON-CLAIMS (things this packet does NOT establish)

status: NEEDS_CODEX_VALIDATION

1. NOT CLAIMED: that any single function is "the reducer" or "the merge". No N->1 reducer was
   located. The packet bounds where image kernels live, not where (if anywhere) a tidy reducer is.

2. NOT CLAIMED: that the SourceImageCache lambda (0x3ec960 chain / 0x369f80 accumulator) is
   per-camera-only. RTTI shows it takes ONE CapturedImage::Camera + ONE Tile, but I did NOT runtime-
   confirm the camera count, nor exclude that an outer loop calls it once per camera and a later
   stage combines outputs.

3. NOT CLAIMED: that 0x2f78e0 is "denoise and therefore irrelevant to src1/src2". I established its
   RTTI is ImageDenoiseBilateralGeneric<5,true>; its actual position on the src1/src2 path remains
   UNPROVEN (matches the prior committed caveat).

4. NOT CLAIMED: that the 0x23faf0 record family has zero image effect. I only showed it is a
   metadata/record clone and that there is NO DIRECT-CALL path from its 23 host functions to the
   named kernels. Indirect (vtable / std::function / registered-callback) links are NOT excluded and
   are the most likely place such a link would hide, given that 3 of the 6 kernels are themselves
   indirect-only.

5. NOT CLAIMED: completeness of the "6 image kernels" set. The reachability result is only as
   complete as that seed set. Other demosaic/resample/warp kernels not in the seed set were not
   enumerated; a 0x23faf0 host could touch image data via a kernel I did not seed.

6. NOT CLAIMED: anything from rendering or runtime. STATIC ONLY. No render/breakpoint was run
   (another agent may be rendering concurrently).

7. NOT CLAIMED: that 0x365960's two equal-length std::vector<16-byte> args are the src1/src2 pair.
   That is a CANDIDATE only; their semantic identity is unproven.

8. NOT CLAIMED: that the mode-dispatch at 0x3ec960 (+0x18 enum) selects "fusion vs no-fusion". The
   enum's meaning is unknown; only that 0x3ec770->accumulator is one conditional branch of several.
