# C6 post-mutation state consumer probe

This probe checks the caller path immediately after the known C6/key15 mutation
body. It verifies whether the constructed `ctx+0xa0` object is read, whether its
item vector is walked, and whether derived state is written back to the owning
context under the canonical tele bridge HDR profile.

Scope:

- `70mm`: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
- `150mm`: `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`
- `tools/lri_process --profile 3 --export-fmt 3 --no-auto-lris`

Raw outputs belong in ignored `runs/c6_postmutation_state_consumer/`.
