# C6 ImagePyramid Data Watch Probe

Purpose: after the proven zero-fill return site `0x3b2f59`, arm a hardware
read/write watchpoint on the actual data pointer for one selected
`context+0x538` ImagePyramid level.

Scope:

- Canonical bridge HDR profile only: `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`.
- This is a data-touch probe, not a callgraph probe.
- Each script watches one level's first `8` bytes only. Zero hits therefore
  means no read/write of that watched byte range under that run, not "the whole
  image buffer was never touched."

Ignored raw outputs belong under:

- `runs/c6_image_pyramid_data_watch/`
