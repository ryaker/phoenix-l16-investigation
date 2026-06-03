# proof_or_disproof_plan — Lane B Unit-2 four-zoom

status: NEEDS_CODEX_VALIDATION. No authority.

## Claim under test (CANDIDATE / LEAD)

On libcp.dylib sha256 b38dc4b3..., the runtime IRAMP accumulator at
`libcp_base+0x369fa4` reads the same Hann-16 coefficient tile (16 floats at
`$rbp-0xa0`) at its FIRST hit for all four Unit-2 four-zoom twin seeds, and that
tile is float32-identical to the Unit-1/28mm reference.

## How Codex can REPRODUCE

1. Confirm libcp.dylib sha256 == b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9.
2. For each Unit-2 seed (28/35/70/150mm paths in manifest.json), run the
   per-zoom `.lldb` (in runs/laneB_unit2_fourzoom/) DIRECTLY:
   `cd /tmp && arch -x86_64 lldb -b -s runs/laneB_unit2_fourzoom/<zoom>.lldb`
   Retry on the intermittent "Cannot open" exit (see README quirk).
3. Read the regenerated `<zoom>_result.json`; compare `coeff16` to the
   `unit1_reference_hann16` array in manifest.json:

```python
import json
u1=json.load(open("manifest.json"))["unit1_reference_hann16"]
for z in ["28mm_L16_02130","35mm_L16_03041","70mm_L16_03434","150mm_L16_02285"]:
    c=json.load(open(f"runs/laneB_unit2_fourzoom/{z}_result.json"))["coeff16"]
    print(z, all(abs(round(c[i],6)-u1[i])<=1e-6 for i in range(16)))
```

Expected: True for all four.

## How this could be DISPROVEN / weakened

- **Different libcp.dylib**: VAs (`0x369fa4`, `0x3eced0`) are binary-specific.
  On any other libcp build the offsets and result may differ. Re-extract base.
- **anchor mismatch**: anchorPassed is already FALSE; if Codex finds the TRUE
  `mulps->maxps->sqrtps` site, that may relocate the intended accumulator and
  the `0x369fa4` capture may be reading a different stage's coefficients than
  the spawn prompt assumed. Codex should locate the real anchor and confirm
  `0x369fa4` is genuinely the IRAMP accumulator referenced.
- **first-hit only**: if later `0x369fa4` hits use different tiles (e.g.
  per-pyramid-level windows), the "uses the same tile" framing is too strong.
  Re-run capturing the first K hits and the distinct tile set.
- **second physical body sanity**: these four are the documented Unit-2 twins.
  If any seed's per-file intrinsics SHA-256 is NOT the Unit-2 hash
  (`223961c6...`), it is mis-labeled and the cross-unit framing is broken;
  Codex should verify each seed's intrinsics hash before trusting "Unit-2."

## Open follow-ups (out of scope here)

- Trace the accumulation loop body from `sym_3661b0` to determine N (source
  frames) and the N->1 store instructions before any reducer/merge language.
- Capture the FULL set of distinct tiles across all hits per zoom.
- Re-run the SAME four-zoom probe on Unit-1 twins in the same session to make
  the cross-unit comparison single-session (this packet relied on the prior
  session's Unit-1 28mm reference only).
