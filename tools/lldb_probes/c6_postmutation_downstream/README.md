# C6 post-mutation downstream state probe

This probe follows the immediate consumer segment after the proven
post-mutation `context+0xc8` / `context+0x4b0` writes.

It checks whether:

- the state object stored at `context+0xc8` is read again
- `0x40b0e0` returns a branch-controlling code
- `context+0x4b0` is passed into `0x3c8d00`
- `0x3c8d00` builds/updates the output vector used by the same caller path

Scope:

- `70mm`: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
- `150mm`: `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`
- `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

Raw outputs belong in ignored `runs/c6_postmutation_downstream/`.
