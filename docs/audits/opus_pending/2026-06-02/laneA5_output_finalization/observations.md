# Lane A5 — Observations

Source dumps (machine-extracted; reproducible — `commands.txt`):
`runs/laneA5_output_finalization/finalization_369ff2.txt` (`0x369ff2..0x36ae41`, ends at `retq`),
`runs/laneA5_output_finalization/resampler_2b2be0.txt` (`0x2b2be0` head). VA == file offset.

## O1 — Finalization sequence (`0x369ff2..0x36a273`)

```
0x369ff2 movq -0x4388(%rbp),%r15        ; this
0x369ff9 movq 0x8(%r15),%rax            ; output-image object; 0x30(rax)=w, 0x34(rax)=h
0x36a004..0x36a01f                      ; setg (region - w), setg (region - h), orb, cmpl $1; jne 0x36a08f
0x36a021..0x36a059                      ; clamp negatives (cmovsl/cmovnsl); build rect {0,0,w,h} at -0x4258
0x36a05f..0x36a072 callq 0x3750a0(rdi=-0x1730 view, rsi=-0x4258 rect, edx=2)   ; edge-extend view A
0x36a077..0x36a08a callq 0x3750a0(rdi=-0x17d0 view, rsi=-0x4258 rect, edx=2)   ; edge-extend view B
0x36a08f..0x36a0e6                      ; load 0x38(r15)=dst, 0x40(r15)=src, -0x4478=rect; clamp dst∩src (cmovge/cmovg)
0x36a0eb jle 0x36a15b                   ; GATE: if intersection w<=0 -> zero-fill descriptor
0x36a0ef jle 0x36a15b                   ; GATE: if intersection h<=0 -> zero-fill descriptor
0x36a0f1..0x36a159                      ; pack -0x4290 descriptor: corners(psubd), w,h, stride(0x18(rdi)),
                                        ;   -0x4274=0xffffffff (init sentinel), dst ptr (0x20(rdi)+off), 0x28(rdi)
0x36a15b..0x36a16f                      ; (degenerate) pxor + movdqa zero -0x4270/-0x4280/-0x4290
0x36a177..0x36a1dc                      ; scale = 0x30(r15); compute (w*scale - off) as doubles -0x42a0/-0x4298,
                                        ;   scale doubles -0x42b0/-0x42a8
0x36a1e4..0x36a200 callq 0x2b2be0(rdi=-0x4290 desc, rsi=-0x1730 view A, rdx=-0x42a0, rcx=-0x42b0)
0x36a217..0x36a252                      ; build 2nd descriptor -0x42e0 (via 0xf540)
0x36a257..0x36a273 callq 0x36f800(rdi=-0x42e0 desc, rsi=-0x17d0 view B, rdx=-0x42a0, rcx=-0x42b0)
```

OBSERVED-from-disasm: two derived views (`-0x1730`, `-0x17d0`) of the merged output buffer are
edge-padded then cubic-resampled into the destination at `0x38(r15)`. The doubles fed to both
resamplers are the same scale/offset, so the two views are resampled with identical geometry (LEAD:
two planes/levels of the same merged result).

## O2 — `0x3750a0` = border replication (edge-extend) — anchored on assert strings

`0x3750a0` validates `edx>0` (`0x3750f6 testl %edx,%edx; jle` → `"Amount to extend must be positive"`),
ROI bounds (`"ROI must be within image!"`, `"ROI start must be non-negative!"`), then copies interior
border rows/cols outward (top/bottom/left/right halos). edx=2 ⇒ a 2-pixel replicate pad of the merged
buffer before resampling. (Assert strings are deterministic byte facts; the halo-copy interpretation is
LEAD.)

## O3 — `0x2b2be0` / `0x36f800` = cubic-kernel resample into output

`0x2b2be0`: a 64-iteration loop (`cmpq $0x40`) fills a weight table via piecewise polynomial
(`mulss/addss` with `ucomiss`-branched segments = separable cubic kernel LUT), heap-allocates a 0x30-byte
functor (`__Znwm`, vptr `0x6685b8`) bound to {offset doubles, scale doubles, source view, weight table,
dst descriptor}, then calls `0x5440` (recursive spatial-subdivision driver; leaf invoked via
`callq *0x30(rax)`). `0x36f800` is a byte-sibling with different kernel constants (second filter/plane).
Interpretation (cubic / Catmull-Rom-class) is LEAD; the LUT-loop + functor + subdivision structure is
grep-confirmed.

## O4 — Acceptance/rejection at this site = geometric only

The only rejection is the degenerate-rect skip (`0x36a0eb/0x36a0ef jle 0x36a15b`). No score/quality
acceptance gate exists in `0x369ff2..0x36ae41`. (Negative-shaped, scope-bound to this range.)
