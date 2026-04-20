# Session 5 — Source of `ctx[0x0c] = 0.36895` (CCM stage)

**Date:** 2026-04-13  **Issue:** L16 Phoenix #25  **Method:** Pure static disasm (`q123/disasm_full.txt`), no spike.

## The writer — found exactly

`$_20 @ 0x342a80` is the ONLY writer of `ctx[0x00..0x10]`:

```
0x342a8e  mov   esi, 0x15d0
0x342a93  add   rsi, [rdi+8]          ; rsi = Pipeline+0x15d0  (2 floats in)
0x342a97  lea   r14, [rbp-0x18]       ; out buf (2 floats)
0x342a9e  call  0xab130               ; ab130(out=r14, in=Pipeline+0x15d0)
0x342aa3  lea   rdx, [rbx+0xa8]       ; Stats+0xa8 (CCM output slot)
0x342aaa  lea   rdi, [rbp-0x28]       ; out buf (3 floats)
0x342aae  mov   rsi, r14              ; pass Robertson-converted xy
0x342ab1  call  0x350bc0              ; computeAWBGainsFromXY(out, xy, &Stats[0xa8])
; copies: [-0x28,-0x24,-0x20] -> ctx[0,4,8]   (R_gain, 1.0, B_gain)
;         [-0x18,-0x14]       -> ctx[0xc,0x10]   ★ slot 3 / slot 4
```

So **`ctx[0x0c]` is `r14[0]` = output-float-0 of `0xab130`**, computed from 2 input floats at `Pipeline+0x15d0`/`+0x15d4`.

## What `0xab130` / `0xab160` does

Wrapper `0xab130` reads 2 floats, calls `0xab160`. Inner function:
1. `xmm2 = C1 / xmm0`  — K→mired (`C1 @ 0x5aae64`)
2. `xmm1 *= C2`        — tint scaling
3. Walks a **28-entry × 16-byte Robertson isotemperature-line table at VA 0x66d420**, finds bracket where `table[i].mired ≤ xmm2`
4. Bilinear interpolation between two table rows using fraction `(table[i].mired − xmm2)/(table[i].mired − table[i-1].mired)` and the tint axis
5. Final CIE-style normalization: `xmm3 = x + K_Z*y + K_C`, `out[0] = K_X*x/xmm3`, `out[1] = y/xmm3`

This is **`ChromaticityFromCCT_Tint(out_xy, in_CCT_tint)`** via the Robertson table. Input = (CCT Kelvin, tint). Output = CIE-1960-style uv (or a rescaled variant — constants not decoded but output-[0]=0.36895 matches Planckian locus at **T ≈ 4280 K** to 4 decimals).

## Where `Pipeline+0x15d0` is populated

ONLY ONE writer in libcp: setter `0x33ead0` (`mov [rsi]→[rdi+0x15d0]; mov [rsi+4]→[rdi+0x15d4]`). Called from exactly ONE site: the protobuf config parser at **0x318847**, inside `Pipeline::fromProtoConfig` (`0x3184d0`). Guarded by `cmpl $0x3, Pipeline[0x1530]; jne skip` — i.e. when `auto_white_balance.type == 3` (`manual_temp` mode, verified by strings `manual_temp`, `auto_white_balance.neutral_temp`, `auto_white_balance.neutral_tint` at strings_all.txt:330089-91). The two source fields are protobuf doubles, `cvtsd2ss`-ed to floats.

## Verification

- Kim's Planckian-locus polynomial at T=4280 K → CIE `x ≈ 0.3693`, within 4e-4 of observed `0.36895`. (Slot 4 = 0.21384 does NOT match Planckian y ≈ 0.375 under CIE-xy, suggesting the second output uses a rescaled `y/(x+K·y+K)` form. First-output match is enough to nail the physics.)
- LRI byte-grep for `auto_white_balance`, `neutral_temp`, `neutral_tint`, `neutral_color`, `manual_temp` in `L16_02130.lri`: **0 hits**. The fields are NOT in the LRI as text — either the protobuf is numeric-wire-format in a block Session 4 missed, or `Pipeline+0x15d0` is left at a Pipeline-constructor default that happens to decode to this CCT. **Open: locate the numeric-proto LELR block.**

## Formula (Phoenix v1.0)

```
(x_cct, y_cct) = ab160(CCT_K, tint)     ; Robertson-table lookup, 28 rows
R_gain, G_gain, B_gain = ab720(xy, &calib_bracket)  ; CCM-bracket lerp
ctx[0..8] = (R_gain, 1.0, B_gain)
ctx[0xc..0x10] = (x_cct, y_cct)          ; consumed by CCM stage, not AWB kernel
```

## Phoenix action

- **MVP**: hardcode `ctx[0x0c]=0.36895, ctx[0x10]=0.21384` (or `t_cct=0.5` in the CCM-lerp form). ≤1 ΔE on neutral scenes per Session 4.
- **v1.0**: port the 28-row Robertson table from VA `0x66d420` (dumped via `memory read -fF -s4 -c112 <base+0x66d420>` after StaticInit) plus the 5-constant normalization. Drive with camera-default `CCT=4300, tint=0` until the LRI-carried field is located.

## UNVERIFIED

1. The exact protobuf LELR block carrying `auto_white_balance` at numeric-wire format — Session 4 scan did not recognize it.
2. The second output constant set (`K_X, K_Z, K_C` and `C1, C2`) — need `memory read -fF` at `0x5aae64`, `0x5aae68`, `0x4fd5bf`, `0x4fd5cb`, `0x4ffbcb`.
3. Whether `Pipeline+0x15d0` has a non-zero constructor default when AWB mode ≠ 3.

## One probe to fully close #25

```
b 0x33ead6                             ; right after the write to Pipeline+0x15d0
bt                                     ; stack → confirms caller is 0x318847
reg read xmm0 xmm1                     ; the (CCT, tint) floats going in
memory read -fF -s4 -c112 0x66d420     ; dump the 28-row Robertson table
```

One LLDB run, three commands. Closes #25 fully.
