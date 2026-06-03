# Lane A5 addendum — guided detail-transfer stage (`0x36abf0`) — WSJF #2

**Status:** `NEEDS_CODEX_VALIDATION`. Small bounded decode. Constants byte-verified (OBSERVED);
buffer roles LEAD. Binary `libcp.dylib` sha256 `b38dc4b3…`.

## What it does (OBSERVED arithmetic, `0x36abf0..0x36ac15`)

Per pixel (vec4), over three buffers A=`(%rdx)`, B=`(%rax)`, C=`(%rcx)`:
```
0x36abf6 d  = A − B
0x36abff w  = C.lane3 (broadcast)            ; per-pixel weight from C's 4th lane
0x36ac03 d *= 2.0                            ; const 0x5a887c = 2.0
0x36ac06 d *= w
0x36ac09 d  = max(d, −0.1)                   ; clamp lo  0x5fdbc0 = −0.1
0x36ac0c d  = min(d, +0.1)                   ; clamp hi  0x5cbf70 = +0.1
0x36ac0f s  = B + C
0x36ac12 s += d
0x36ac15 store s -> (%rax)  (buffer B)
```

So: **`out = (B + C) + clamp( (A − B)·2·C.lane3, −0.1, +0.1 )`** — a **bounded weighted detail/residual
injection**. The high-frequency difference `(A−B)` is amplified ×2, modulated by a per-pixel weight
(`C.lane3`), and **hard-clamped to ±0.1** before being added to the `B+C` base. The ±0.1 cap bounds how
much detail any pixel can gain/lose — a conservative, artifact-limiting sharpen/detail-transfer.

## Constants (byte-verified)
`0x5a887c = 2.0` (gain), `0x5fdbc0 = (−0.1,…)` (clamp lo), `0x5cbf70 = (0.1,…)` (clamp hi).

## Non-claims
- Buffer identities A/B/C (`-0x42c0`/`-0x4270`/`-0x1200` family) and which is the merged result vs a
  blurred/guide version are LEAD — the `(A−B)` "detail" reading assumes A is sharper than B, not proven.
- `C.lane3` as a per-pixel confidence/weight is LEAD (consistent with the A7 lane-3 reciprocal blend).
- This is one stage of the finalization tail; bounded scope.
