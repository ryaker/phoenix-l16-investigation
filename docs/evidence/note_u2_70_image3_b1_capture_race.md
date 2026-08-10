# u2_70_executor_serial image3 (B1) capture race — MEASURED 2026-08-10

`u2_70_executor_serial_r1/image3.rgba8` is NOT valid ground truth for the B1
source plane. Measured facts (see tools/compare_u2_70_level0_boundary.py):

- images 0/1/2/4: byte-identical between r1 and r2 (sha256 equal).
- image3: 73.77% of bytes differ between r1 and r2; r1 has 22.85% exact-zero
  (unwritten) tiles visible as black rectangles; r2 has 0.00%.
- index5_hypothesis_index.u16le is byte-identical across serial2d30 r1/r2/r3.

Conclusion: the interpose's plane read RACED B1's tile materialization in r1.
The plane G-42 actually consumed was complete and deterministic (the index5
map is stable). Use r2's image3 as the B1 reference; treat r1's image3 as a
raced snapshot only.

Cross-check against Phoenix (same LRI, tele tier, proven record order
B4,B2,B5,B1,B3): Phoenix's B1 plane vs r2 image3 Y-correlation +0.976 — the
same level as every other camera pair — confirming the plane identity and
that only the r1 capture timing was at fault.
